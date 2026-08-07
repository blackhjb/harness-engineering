---
name: ai-agent-dev
description: LLM·에이전트 파이프라인을 만들거나 고칠 때 연다 — 프롬프트 버전·구조화 출력·모델 라우팅·eval. 순수 라우트/DB 작업은 python-service, 배포는 mlops-gcp.
---

# LLM/Agent Engineering Playbook

## 0. AI architecture is decisions, not model calls

The model call is an implementation detail; these eight decisions are the architecture. Walk them BEFORE building any LLM feature; every deviation from a default = an ADR in design.md (`D-NNN`). Quality-attribute priorities and NFR budgets live in design.md sections 2 and 10 — this section decides, those record.

1. **LLM 필요 여부** — can rules/regex/SQL do it? LLM only where fuzzy language understanding/generation is the actual requirement. Extraction default: hybrid — rules first, LLM for the residual.
2. **Workflow vs Agent** — fixed-step pipeline (LLM inside steps) vs agent (LLM picks next action). Default: workflow; agent loop only for genuinely dynamic tool choice or unbounded steps (§11) — agents cost more, test worse, fail less predictably.
3. **모델 티어 라우팅** — cheap model for extraction/classification, reasoning model for judgment/synthesis. Route per call, never one-model-for-everything; budgets in design.md NFRs (§4, §8).
4. **RAG vs 롱컨텍스트 vs 파인튜닝** — default: stuff-the-context for small corpora (< a few hundred KB). RAG for large/changing corpora — chunking + citation mandatory (§10). Fine-tuning: last resort (needs eval set + drift ops), always an ADR.
5. **동기 vs 배치** — user-facing sync: p95 latency budget + fallback path. Pipeline default: overnight batch (Cloud Run Jobs); choosing batch = designing retry/backfill now, not later.
6. **구조화 출력 강제** — pydantic schema first (§2); free-text LLM output crossing a component boundary is a design smell. Repair-retry policy per call (§3).
7. **평가 먼저** — golden set + regression run on every prompt change + explicit quality bar (§6). "데모에서 잘 나왔다" is not an eval.
8. **실패 시 동작** — every call declares malformed/timeout/quota behavior: skip+record? default value? fail the pipeline? Silent degradation is banned.

## 1. Pipeline architecture pattern
Every LLM batch pipeline: five stages, each with file-persisted output so any stage re-runs alone:

```
ingest → normalize → extract(LLM, cheap tier) → aggregate(LLM, reasoning tier) → publish
```

- **ingest**: pull raw data → immutable raw files (`data/raw/<date>/<source>/…`). No transformation.
- **normalize**: raw → common pydantic record. Pure Python, no LLM — most "LLM errors" die here free.
- **extract**: per-document LLM calls, cheap tier, structured output only, failure-isolated per document.
- **aggregate**: one (or few) reasoning-tier calls over extracted records: synthesis, ranking, report.
- **publish**: deliver (Google Chat / KB repo commit). Never call the LLM here — a retry must not re-spend tokens.

Rule: LLM stages read files and write files — makes dry-run, backfill, stage-level retry trivial.

## 2. Schema-first prompting
Define the pydantic schema BEFORE the prompt. The schema is the contract; the prompt motivates it.

```python
from pydantic import BaseModel, Field

class IssueInsight(BaseModel):
    summary: str = Field(description="핵심 요약, 2문장 이내, 한국어")
    category: Literal["bug", "feature", "ops", "question"]
    source_ref: str = Field(description="근거가 된 원문 ID/URL — 필수")
    evidence: str = Field(description="원문에서 그대로 가져온 근거 문장")
    confidence: Literal["high", "medium", "low"]
```

- `source_ref` / `evidence` / `confidence` required on every extraction schema — no-fabrication enforced structurally.
- 1-3 few-shot `입력 → 올바른 JSON` pairs: one normal, one "정보 없음" case (teach "not in source" over inventing).
- Prompt states the policy: "원문에 없는 사실은 절대 생성하지 마라. 정보가 없으면 confidence를 low로 하고 evidence를 비워라."

## 3. Retry/repair for malformed output

```python
from pydantic import ValidationError

def call_structured[T: BaseModel](client, model: str, prompt: str, schema: type[T], max_repair: int = 2) -> T:
    resp = client.models.generate_content(
        model=model, contents=prompt,
        config={"response_mime_type": "application/json",
                "response_schema": schema, "temperature": 0.1},
    )
    for attempt in range(max_repair + 1):
        try:
            return schema.model_validate_json(resp.text)
        except ValidationError as e:
            if attempt == max_repair:
                raise LLMOutputError(model=model, errors=e.errors()) from e
            repair = (f"이전 출력이 스키마 검증에 실패했다.\n오류: {e}\n"
                      f"이전 출력: {resp.text}\n"
                      "수정된 JSON만 출력하라. 설명 금지.")
            resp = client.models.generate_content(model=model, contents=repair,
                config={"response_mime_type": "application/json", "response_schema": schema})
```

Rules: temperature ≤ 0.2 for extraction; max 2 repairs (past that the input is bad, not the format); `LLMOutputError` is caught at the per-document boundary, logged, counted in the partial-success report — never crashes the batch.

## 4. 2-tier Vertex AI Gemini routing
One config mapping, no scattered model strings:

```python
from google import genai

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

MODEL_TIERS = {
    "extract": "gemini-2.5-flash",  # high-volume: extraction, classification, normalization
    "reason":  "gemini-2.5-pro",    # low-volume: judgment, synthesis, ranking, final report
}

def llm(tier: Literal["extract", "reason"], prompt: str, schema: type[BaseModel]):
    return call_structured(client, MODEL_TIERS[tier], prompt, schema)
```

Routing rule: "read one document, fill one schema" → extract; cross-document judgment, prioritization, or prose quality → reason. Unsure → eval on the cheap tier first, upgrade only if it fails. Typical split: 90%+ extract, <10% reason.

## 5. Prompt versioning layout
Prompts are files in the repo, loaded at runtime — never inline strings.

```
prompts/
  extract_issue.md      # v3 — header: version, changelog, target model tier, schema name
  aggregate_daily.md
  repair.md
```

Header convention (top of each file):
```
<!-- version: 3 | tier: extract | schema: IssueInsight
     v3: few-shot에 '정보 없음' 케이스 추가 (eval 87→94%)
     v2: 카테고리 정의 명시 -->
```
Changing a prompt file = a diff in code review + a mandatory eval re-run.

## 6. Eval harness design
Every LLM task gets `evals/<task>/`:

```
evals/extract_issue/
  golden/            # 10+ real inputs incl. edge cases (empty doc, mixed language, huge doc)
  expected/          # expected outputs or assertion specs per case
  run_eval.py        # runs task on golden set, scores, prints table, exits nonzero on regression
  baseline.json      # last accepted score, committed
```

- Assertions, strongest first: (1) schema-valid, (2) required fields non-empty, (3) no-fabrication: every `evidence` string appears in the source (substring/fuzzy), (4) task correctness (category match, key facts), (5) Korean output check.
- Run on every prompt/model change; compare with `baseline.json`; regression blocks merge.
- LLM-as-judge: only for subjective quality (tone, usefulness); pin the judge model version; fixed rubric, anchored 1-5 examples; never the sole gate — always alongside hard assertions; beware self-preference when judge and generator share a family.

## 7. Dry-run / fixture strategy
- Global `--dry-run` flag: LLM client swapped for a `FixtureClient` returning recorded responses from `tests/fixtures/llm/<task>/<case>.json`, keyed by task + input hash.
- Record fixtures once from real runs (`--record`), commit. CI and pytest run entirely on fixtures: fast, free, deterministic.
- Dry-run must exercise the FULL pipeline incl. publish formatting (publish targets a local file). If dry-run can't run end-to-end, the pipeline is not testable — fix that first.

## 8. Cost control checklist
- [ ] Per-call budget estimated (tokens in/out × price) before implementation; per-run and monthly ceilings in design.md NFRs.
- [ ] Cheap tier by default; reasoning tier requires justification.
- [ ] Inputs trimmed: only needed fields; cap document length with an explicit `max_input_chars`.
- [ ] `max_output_tokens` set on every call.
- [ ] Batch/dedupe: skip already-processed documents (idempotency key), don't re-extract unchanged inputs.
- [ ] Dry-run for all development iterations — burning tokens to debug parsing is a smell.
- [ ] Measured cost per run logged and compared to budget in the run log.

## 9. Observability
One structured line per LLM call (JSON to stdout — Cloud Run picks it up):

```python
log.info("llm_call", extra={"task": task, "model": model, "tokens_in": u.prompt_token_count,
    "tokens_out": u.candidates_token_count, "latency_ms": ms,
    "outcome": "ok|repair_1|repair_2|failed", "doc_id": doc_id})
```

End of run: summary line — total calls, tokens, estimated cost, failure count, failed doc IDs — feeds the Google Chat report and the `.harness/logs/` entry.

## 10. RAG basics (only when retrieval is actually needed)
- Chunking: split on document structure (headings/sections), ~500-1000 tokens, 10-15% overlap; keep metadata (source, title, date, URL) per chunk.
- Index: dumbest thing that works — at repo-as-KB scale (<10k chunks), grep/BM25 or an in-memory embedding matrix; a vector DB is an ADR-level decision, not a default.
- Answering: retrieved chunks enter the prompt WITH source IDs; the answer schema requires citations per claim; a claim without a retrievable citation is dropped, not published.
- Eval retrieval separately from generation: recall@k on a small labeled set before blaming the prompt.

## 11. Agent-loop design
Keep the loop boring and inspectable:
- Explicit tool registry: tool = name + pydantic args schema + pure function. Model selects via structured output, code executes.
- State in files, not the context window: the loop writes `state.json` (step, findings, pending) each iteration; resumable after a crash.
- Stop conditions, all three, always: (1) goal predicate satisfied, (2) max iterations (start at 10), (3) budget exhausted (tokens or wall-clock). Log which fired.
- Every iteration appends to a trace log (tool, args, result summary) — the trace is your debugger.
- Prefer a fixed pipeline whenever steps are known in advance; agents are for genuinely dynamic control flow only.
