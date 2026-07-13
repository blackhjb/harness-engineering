---
name: data-pipeline
description: Data pipeline playbook — idempotent batch job design, date parameterization and backfill, KST timezone handling, raw/processed layering, incremental vs full sync, failure isolation with partial-success reporting, data quality checks, repo-as-knowledge-base storage, and Cloud Scheduler + Cloud Run Jobs scheduling. Use for ANY data collection, ETL, batch pipeline, or scheduled job work.
---

# Data Pipeline Playbook

## 1. Batch job design: idempotent, date-parameterized, re-runnable
Every batch job takes an explicit logical date and produces the same output when re-run:

```python
@click.command()
@click.option("--date", "date_str", default=None, help="논리 처리일 YYYY-MM-DD (KST). 기본: 어제")
@click.option("--dry-run", is_flag=True)
def main(date_str: str | None, dry_run: bool):
    kst = ZoneInfo("Asia/Seoul")
    target = date.fromisoformat(date_str) if date_str else (datetime.now(kst) - timedelta(days=1)).date()
```

- Idempotency = deterministic output paths keyed by date (`data/processed/2026-07-10/…`) + overwrite-on-rerun (or temp-then-rename). Never append blindly; a re-run must not duplicate rows.
- Upstream writes carry an idempotency key (`<source>:<doc_id>:<date>`) — a retried job must not double-post to Chat or double-commit to the KB.
- Backfill is then free: `for d in 2026-07-01..2026-07-09: run --date $d`. A job that can't backfill isn't parameterized correctly — fix that first.

### KST timezone gotchas (recurring bug source)
- Containers run in UTC. `datetime.now()` without tz is a bug; always `datetime.now(ZoneInfo("Asia/Seoul"))`.
- "어제 데이터" at a 07:00 KST run = 22:00 UTC two days back → 22:00 UTC yesterday — compute boundaries in KST, convert to UTC for API params.
- Cloud Scheduler: always `--time-zone="Asia/Seoul"`.
- Source APIs return UTC/offset timestamps — normalize to aware datetimes at ingest, store ISO-8601 with offset, convert to KST only for display.

## 2. Raw/processed layering
```
data/
  raw/<YYYY-MM-DD>/<source>/…       # immutable: exactly what the API returned, incl. failures manifest
  processed/<YYYY-MM-DD>/…          # derived, always regenerable from raw
```
- Raw is append-only, never edited. Extraction logic changed → re-derive processed from raw; no re-fetching.
- Every derived file must be reproducible by `run --date D` from raw alone; otherwise the pipeline has hidden state.
- `manifest.json` per raw date-partition: what was fetched, counts, fetch time, failures — what freshness checks read.

## 3. Incremental vs full sync
| Choose | When | Cost |
|---|---|---|
| Full sync | Small source (<~5k items), cheap API, correctness paramount | Simple, no cursor bugs; wasteful at scale |
| Incremental (updated_since cursor) | Large source, rate-limited API | Cursor storage + missed-update risk (deleted/moved items) |
| Hybrid | Default recommendation | Incremental daily + full sync weekly to self-heal drift |

Cursor in a state file (`state/cursor_<source>.json`), written only after a fully successful run — a half-failed run must not advance the cursor.

## 4. Failure isolation + partial-success reporting
One bad document must never kill the night's pipeline.

```python
results, failures = [], []
for doc in docs:
    try:
        results.append(process(doc))
    except Exception as e:  # unit boundary — classify, record, continue
        failures.append({"id": doc.id, "source": doc.source, "error": type(e).__name__, "msg": str(e)[:300]})
```

- Isolation boundary = one source AND one document. A whole source failing (auth expired) = source-level failure; other sources proceed.
- Exit contract: 0 = all ok; still 0 with a partial-success report if some units failed but output was produced; nonzero only when the run produced nothing usable (so Cloud Run retry fires appropriately).
- Partial-success report (Google Chat + run log): `성공 42 / 실패 3 (notion:2 jira:1)`, failed IDs, retryable or not. Silent partial data is worse than a loud crash.

## 5. Data quality checks (run before publish)
- **Schema**: every processed record validates against its pydantic model — free if schema-first.
- **Freshness**: raw manifest for the target date exists and is < N hours old; else abort publish and alert.
- **Volume anomaly**: today's count vs trailing 7-day median; alert if < 50% or > 300% (thresholds in config). Catches silently-broken auth and pagination bugs.
- **Referential**: aggregate output cites only doc IDs present in processed data (pairs with the LLM no-fabrication check).
- Failing DQ check ⇒ block publish, alert with the numbers, leave raw/processed intact. Never publish suspect data to save the morning send.

## 6. Storage: repo-as-knowledge-base, and when to graduate
Default (hermes-kb pattern): a GitHub repo of markdown/JSON, partitioned by date/topic, committed by the pipeline — versioned, diffable, greppable, zero infra, readable by humans and LLM agents.
- Practices: deterministic file paths (re-run = clean diff, not duplicates), one logical record per file or per date-file, commit message `data: <source> <date> (+N/-M)`, pipeline pushes via a bot token scoped to that repo only.
- Graduate to SQLite → Postgres/BigQuery only when one of these holds (record as an ADR with numbers): cross-partition queries dominate, concurrent writers appear, repo size makes clones painful (>~1GB), or you need sub-second lookup from a service. "A DB would be cleaner" is not a reason; a failing measurement is.

## 7. Scheduling: Cloud Scheduler + Cloud Run Jobs
Pattern (hermes-worker): separate **collect/analyze** from **publish**, so a failed analysis can be retried before the morning send instead of skipping a day.

```
02:00 KST  scheduler → run-job collect   (ingest→normalize→extract→aggregate, writes processed + report draft)
07:30 KST  scheduler → run-job publish   (reads latest draft, DQ-checks freshness, sends to Google Chat)
```

- Two Scheduler jobs, two Cloud Run Jobs (or one image, two commands). The gap = manual-retry window: collect fails at 02:00 → rerun at 07:00 → publish still on time.
- Config: `--max-retries=2` for collect (transient API errors); `--max-retries=0` or 1 for publish (double-send is worse than late; idempotency key if >0); `--task-timeout` = 2-3× p95 runtime, never the default.
- Scheduler retry OFF for jobs with their own retries — stacked retries cause 3× duplicate runs. One retry layer, chosen deliberately.
- Publish reads "latest successful draft for date D", not "whatever collect just wrote" — file decoupling makes the retry window real.
- Every job start/end/failure emits a structured log line; failures also fire the Google Chat webhook with job name, date param, error head.

## 8. Pipeline review checklist
- [ ] `--date` and `--dry-run` flags exist; backfill for an arbitrary past date works.
- [ ] All datetime handling timezone-aware; boundaries computed in KST.
- [ ] Raw immutable and sufficient to regenerate all processed output.
- [ ] Re-run produces no duplicates (idempotent writes + idempotency keys on side effects).
- [ ] Per-document and per-source failure isolation; partial-success report wired to Chat.
- [ ] DQ checks (schema/freshness/volume) gate the publish step.
- [ ] Collect and publish separately schedulable and separately retryable.
- [ ] Cursor/state files advance only on full success.
