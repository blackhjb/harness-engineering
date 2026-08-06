---
description: Set or reset the harness goal — brief interview, then scaffold .harness/ and write GOAL.md with measurable success criteria
argument-hint: "<one-line goal>"
---

The user wants to set a harness goal: $ARGUMENTS

Respond in Korean; write all .harness/ files in Korean (code identifiers, file paths, technical terms as-is). Consult the harness-state skill; scaffold files directly from its canonical section lists.

## 1. Interview (one message, short)
Ask in Korean, in a single message, only what "$ARGUMENTS" does not already answer (max 5):
1. 성공 기준 — how will we MEASURE done? Push for verifiable checks ("p95 < 200ms", "이 3개 API가 통합 테스트 통과"), not feelings.
   각 기준은 **판별력 2문항**을 통과해야 GOAL 에 들어간다: (a) **이 기준은 지금(수정 전) 거짓인가** — 참이면 vacuous 이므로 교체한다. 로그 레벨·문자열·상수를 인용하는 기준은 그 원문 줄을 열어 확인한다(예: "WARNING 0건"이라 썼는데 실제 호출이 `logger.info` 면 수정 전에도 통과한다). (b) **이 측정이 대상 기전을 실제로 통과하는가** — 같은 값이 다른 경로로도 나올 수 있으면(고정 문구·캐시·조기 반환) 경로 식별 증거를 기준에 함께 적는다.
   (a) 를 착수 시점에 확정할 수 없으면 기준 문장에 "**수정 전 red 실측을 같은 태스크에 포함**"을 명시한다 — build 단계의 양성 대조 의무와 같은 규율을 기준 자신에게도 건다.
2. 제약 — tech stack constraints, must-not-change, infra/budget limits.
3. 기한 — deadline or time budget.
4. 범위 제외 — explicitly OUT of scope.
5. 참고 컨텍스트 — existing code/docs to look at first (optional).
Wait for the answers before writing anything. If a success criterion comes back vague, restate it measurably once ("이렇게 바꾸면 측정 가능합니다: ... 맞습니까?") and proceed on confirmation.

## 2. Size triage (규모 비례 라우팅 — do not skip)
Classify the goal's size BEFORE scaffolding. **The change surface MUST be grep-measured first — routing on document reasoning alone is forbidden**: locate the files that actually change (the constant, the route, the component), count them, and write that count into GOAL.md 승인 섹션 next to the route. Ceremony scales with the measured change, never with the goal's importance — and unmeasured routing is this triage's most expensive error (실측: 5-file additive-field goal misrouted to the full loop → ~55 min of documents and wave management; ~300-line batch → ~1.4M subagent tokens, where every defect was caught by verification and none by ceremony).

- **quick 경로** — ALL of: **no compatibility-breaking contract change** · no architecture decision (no new module boundary, no tech choice) · measured diff localized and mechanical (guards, re-exports, test fixes, config/doc tweaks — roughly ≤8 files / ≤150 lines) · every success criterion directly checkable by a command.
  - "Contract change" here means **breaking**: a removed/renamed field, a changed type or meaning, a new required request field, a new required argument. An **additive, backward-compatible** change — a new response field, an optional/keyword-only parameter with a default, a new enum member old consumers ignore — does NOT disqualify quick when old clients and existing call sites keep working unchanged. State which of the two it is, with the evidence (old-consumer behavior), rather than treating "the contract is touched" as automatic disqualification.
  → Still scaffold per section 4, but leave analysis.md/prd.md/design.md/plan.md as stubs marked "해당 없음 — quick 경로", record the route + one-line rationale in GOAL.md (승인 섹션) and the daily log, and hand off to `/harness:quick` (one batch, or one invocation per SC cluster) instead of `/harness:analyze`. Verification rigor is NOT reduced — quick's proportional-verify rules still apply in full.
- **표준 루프** — anything else, or any doubt that a wrong guess is expensive → `/harness:analyze` as usual.
- **판단 불가** — run `/harness:analyze` first; analysis.md's 권고 MUST then name the route (quick vs plan) explicitly, and the goal proceeds on that recommendation.

The numeric thresholds above (≤8 files / ≤150 lines) are **retro-tunable defaults, not constants**: retro mines each goal's 결산 (diff vs orchestration cost, logged by verify/quick closure) and proposes threshold adjustments through the bounded harness-edit channel; a project may also carry a sharper local rule as a `cost`-scope wiki node — when one exists, it wins over these defaults.

State the chosen route and its rationale in the confirmation message (section 5).

## 2-B. 사실 명제에는 근거를 붙인다 (재작업의 최대 원인)
GOAL 배경·전제에 쓰는 **사실 명제**(도입 시점·인과 순서·"~가 없다"는 부재 주장·값의 형태·직전 iteration 의 결론)는 각각 `file:line`·커밋 sha·명령 출력 중 하나를 **같은 줄에 병기**한다. 근거를 댈 수 없으면 `[미검증]` 으로 표시하고 analyze 의 확인 대상으로 넘긴다 — 확신도를 섞어 쓰지 않는다.
직전 iteration 의 verify 로그·사용자 보고를 그대로 승격하는 것이 **가장 흔한 오염 경로**다(실측: 한 iteration 의 전제 5건이 analyze 에서 전건 반증됐고, 그 교정에만 analyst 2인 212k 토큰이 쓰였다). 틀린 전제로 시작하면 그 뒤 모든 디스패치가 재작업이 된다 — 토큰을 가장 많이 태우는 지점은 작업이 아니라 **잘못된 출발**이다.

## 3. Handle an existing .harness/
- No `.harness/`: create the full structure below.
- `.harness/` exists: NEW GOAL ITERATION. Preserve `wiki/`, `retro/`, and `logs/` — accumulated learning. (A legacy `playbook.md`/`retro/inbox.md` is also preserved untouched; note to the user that the next `/harness:retro` migrates it into wiki nodes per the harness-state skill.) Read the old state.json, increment `iteration`, and overwrite GOAL.md / analysis.md / prd.md / design.md / plan.md with fresh scaffolds. If the previous goal's phase is not `done` or `retro`, warn the user it is unfinished and get explicit confirmation before overwriting.

## 4. Create files (from the harness-state skill's canonical section lists)
Every section present, empty ones marked "해당 없음".
- `.harness/GOAL.md` — filled from the interview.
- `analysis.md`, `prd.md`, `design.md`, `plan.md` — headers only, sections per the skill's lists.
- `state.json` — per the skill's schema: `goal_id` = `<yyyymmdd>-<short-slug>`, `base_ref` = current commit SHA from `git rev-parse HEAD` (null if not a git repo), `phase` = "goal", `iteration` (1 or incremented), `updated_at` = now, `approvals` all false, `verify` = {"verdict": null, "date": null}, `tasks` = [].
- `wiki/INDEX.md` — create with header + format comment ONLY if missing; never overwrite an existing wiki.
- `retro/` and `logs/` — create if missing.
- Append a goal-set entry to today's daily log (who, what goal, iteration).

## 5. Confirm and hand off
Show the user in Korean: the success criteria table, 제약, 범위 제외, and the section-2 route decision with its rationale; ask them to confirm GOAL.md or request edits. Once confirmed, the next step is the routed command — `/harness:quick` for the quick 경로, `/harness:analyze` otherwise. **Routing must never add a manual step for the user**: when the user has granted standing autonomous progression (e.g., "알아서 진행"), the coordinator invokes the routed command itself in the same session — the route decides WHICH path runs, the user is never asked to type it.

## Question rules (co-creation)
All user questions in this phase follow the `co-creation` skill (key branch points only, batched options with a recommended default, decisions recorded in the owning document and never re-asked); exception — the initial interview may ask short open-ended questions for basic facts (기한, 제약 등).
