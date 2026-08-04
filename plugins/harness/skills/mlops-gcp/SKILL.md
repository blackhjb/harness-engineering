---
name: mlops-gcp
description: GCP MLOps playbook — Vertex AI model/region/quota gotchas, service accounts and least-privilege IAM, Secret Manager migration from .env, Cloud Run services vs jobs decision table, Dockerfiles for python-uv apps, GitHub Actions deploy pipelines with approval gates, structured logging and Google Chat alerting, rollback, and monthly cost review. Use when deploying or operating AI or backend workloads on GCP.
---

# GCP MLOps Playbook

## 1. Vertex AI usage
- **Model selection**: pin exact model IDs in one config (ai-agent-dev 2-tier routing). No floating aliases like `-latest` in production — a silent model swap invalidates evals.
- **Region gotchas**: newer Gemini models are often ONLY on `location="global"` before regional rollout; `asia-northeast3` lags. Check per model; note `global` use in design.md (data leaves the region — healthcare data needs an explicit ruling first).
- **Quotas**: per project × region × model (requests/min, tokens/min); new-project defaults can be tiny — check `IAM & Admin → Quotas` (`aiplatform.googleapis.com`) BEFORE the first scheduled run. Handle 429 with exponential backoff + jitter; a batch job slows down, not fails.
- **Cost monitoring**: budget alert on the project (§9); per-call token logging (ai-agent-dev §9) is the real cost meter — billing lags ~1 day.

## 2. Service accounts + IAM least privilege
One dedicated SA per workload; never the default compute SA.

```
hermes-collector@PROJECT.iam.gserviceaccount.com
  roles/aiplatform.user            # Vertex calls
  roles/secretmanager.secretAccessor   # only on the specific secrets, not project-wide
  roles/logging.logWriter
```

- Grant `secretAccessor` at the secret resource level (`gcloud secrets add-iam-policy-binding notion-token --member=… --role=…`), not project level.
- GitHub Actions authenticates via **Workload Identity Federation**, never exported JSON keys. A JSON key anywhere is a finding: rotate and delete.
- Quarterly: `gcloud projects get-iam-policy PROJECT`; delete anything you can't explain in one sentence.

## 3. Secret Manager migration from .env
Preferred pattern — no code change: mount secrets as env vars on Cloud Run, keep reading `os.environ`.

```bash
printf '%s' "$NOTION_TOKEN" | gcloud secrets create notion-token --data-file=-
gcloud run jobs update hermes-collector \
  --set-secrets=NOTION_TOKEN=notion-token:latest,GCHAT_WEBHOOK=gchat-webhook:latest
```

Client library only when a secret must rotate without redeploy:

```python
from google.cloud import secretmanager

def get_secret(name: str, project: str, version: str = "latest") -> str:
    client = secretmanager.SecretManagerServiceClient()
    path = f"projects/{project}/secrets/{name}/versions/{version}"
    return client.access_secret_version(name=path).payload.data.decode()
```

Migration checklist: create secrets → grant per-secret accessor to the workload SA → `--set-secrets` on the job/service → verify a run → remove values from `.env`/CI variables → keep `.env.example` with names only.

## 4. Cloud Run: services vs jobs
| Criterion | **Service** | **Job** |
|---|---|---|
| Trigger | HTTP request (webhook, API, Chat app) | `gcloud run jobs execute` / Cloud Scheduler |
| Lifetime | Always deployable, scales 0→N per request | Runs to completion, exits |
| Timeout | ≤ 60 min per request | ≤ 24 h per task |
| Retry | Caller's problem | Built-in `--max-retries` |
| Fits | Chat-command bot, ingestion webhook, internal API | Nightly collect/analyze/publish, backfills, batch evals |
| Anti-pattern | Batch work behind an HTTP handler pinged by a scheduler (timeout + double-run bugs) | Long-lived pollers (use a service or scheduler) |

Default for AIX pipeline work: **Jobs**. Choose a Service only when something external must call you.

## 5. Dockerfile for python-uv apps
```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.7 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app
# Layer 1: deps only — cached until lockfile changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
# Layer 2: source
COPY src/ src/ prompts/ prompts/
RUN uv sync --frozen --no-dev
ENTRYPOINT ["uv", "run", "python", "-m", "app.main"]
```
Rules: `uv.lock` committed and `--frozen` always (a build must not resolve versions); deps layer before source; pin the uv version; `.dockerignore` excludes `data/`, `evals/golden/`, `.venv`, `.harness/`; ship `prompts/` in the image — they are code.

## 6. GitHub Actions deploy pipeline
```yaml
jobs:
  test:      # every push/PR
    steps: [uv sync, ruff check ., ruff format --check ., uv run pytest]  # pytest = fixtures/dry-run only
  build:     # main only, needs: test
    steps: [auth via workload-identity, docker build, push to Artifact Registry as $GITHUB_SHA]
  deploy:
    needs: build
    environment: production        # GitHub environment with required reviewer = the approval gate
    steps:
      - gcloud run jobs update hermes-collector --image "$REGION-docker.pkg.dev/$PROJECT/app/hermes:$GITHUB_SHA"
```
- Tag images with the git SHA, never only `latest` — rollback depends on it.
- `environment: production` with required reviewer = one-click approval gate; even solo, it prevents "merged at 23:50, broke the 02:00 run".
- Post-deploy smoke: `gcloud run jobs execute hermes-collector --args="--dry-run" --wait` — verifies image, secrets, IAM without spending tokens or touching data.

## 7. Structured logging + Google Chat alerting
- JSON lines to stdout; Cloud Run ingests them queryable in Logs Explorer. Include `severity`, `job`, `date_param`, event fields; `severity=ERROR` only for events a human must see.
- Alert path A (in-process, immediate):
```python
import httpx
def alert(text: str) -> None:
    try:
        httpx.post(WEBHOOK_URL, json={"text": f"🔴 {JOB_NAME}: {text}"}, timeout=10)
    except Exception:
        logging.exception("alert delivery failed")  # alerting must never crash the job
```
Call from the top-level exception handler and the partial-success reporter.
- Alert path B (catches container-level death A can't): logs-based alert on `resource.type="cloud_run_job" AND severity>=ERROR` plus Cloud Run Job execution-failed events → notification channel. Path B is the safety net for OOM kills and image-start failures.
- Alert content standard: job name, `--date` param, error head (≤300 chars), exact rerun command. An alert you can't act on from your phone is noise.

## 8. Rollback strategy
- **Job code**: redeploy previous SHA — `gcloud run jobs update hermes-collector --image …/hermes:<prev-sha>`. Under 2 minutes; practice it once.
- **Service code**: `gcloud run services update-traffic hermes-bot --to-revisions=<prev-revision>=100` — instant, no rebuild.
- **Prompts / model IDs**: ship in the image, so image rollback reverts them atomically with code — keep it that way.
- **Data**: processed is regenerable from immutable raw (data-pipeline §2) — rollback = re-run with fixed code for affected dates. Raw is never rolled back.
- Precondition: forward-only migrations and idempotent jobs. If a rollback would corrupt state, the design was wrong — file it with the architect.

## 9. Monthly cost review checklist (15 minutes, first business day)
- [ ] Billing → Reports, group by service: Vertex AI, Cloud Run, Artifact Registry, Logging. Compare vs last month; explain any ±30% swing.
- [ ] Vertex token spend vs the per-call logs' estimate — a gap means an unlogged caller; find it.
- [ ] Budget alert at expected monthly × 1.5 with email + webhook channel (create once, verify it still fires).
- [ ] Artifact Registry: cleanup policy keeps last ~10 images; untagged digests deleted.
- [ ] Log retention: default 30 days is right for jobs; no accidental sink to expensive storage.
- [ ] Idle leftovers: unused Scheduler jobs, stale Cloud Run revisions/services from PoCs — delete.
- [ ] Record numbers in a wiki node (scope: cost) if any lesson emerged.
