---
description: BUILD phase — the orchestrator executes plan.md, dispatching independent tasks to owner agents in parallel, updating state.json and logs until all tasks meet acceptance criteria
argument-hint: "[optional: specific task IDs to run, e.g. T-003 T-004]"
---

Run the harness BUILD phase. Optional task filter: $ARGUMENTS

Respond in Korean.

## Preconditions (hard gate)
Read `.harness/state.json`. Both `approvals.design` and `approvals.plan` must be true — if not, stop and point the user to `/harness:plan` approval. Do not offer to bypass this.

## Execution
Set state.json `phase` = "build".
**orchestrator 기동 조건**: plan.md 태스크가 **6건 이상이거나 웨이브가 2개 이상**일 때만 orchestrator 를 기동한다. 그 미만은 코디네이터가 role 에이전트를 **직접 디스패치**한다 — 왕복 게이트가 실작업보다 커지고, 장수명 인스턴스는 인프라 과부하의 단일 실패점이다(실측: 소규모에서 529 사망 4회·게이트 왕복 40~70분 vs 직접 디스패치 사망 0).
**우회 시 책무 승계(필수)**: orchestrator 없이 진행하면 그 startup protocol 3종을 코디네이터가 명시적으로 승계한다 — ①`wiki/INDEX.md` + 해당 scope 노드 읽기 ②태스크↔산출물 사상 장부 유지 ③증거 없는 done 금지(값으로만 판정). 승계 사실을 dispatch 로그 항목에 한 줄로 남긴다.

기동하는 경우 전체 build 를 `orchestrator` 에 위임한다:
- Read `.harness/GOAL.md`, `wiki/INDEX.md` (+ workflow/global nodes), `plan.md`, `design.md`, `state.json` first (your startup protocol).
- Execute plan.md wave by wave **and run ALL waves continuously — finishing one wave is not a stopping point**; stop only on your loop's four stop conditions (all done / blocked with nothing independent / escalation / context-limit handoff). Read-only tasks in parallel; commit-producing tasks strictly serial (shared working tree).
- Task IDs passed ("$ARGUMENTS") → run only those and their unmet dependencies.
- Each dispatch follows your dispatch contract (task ID, verbatim acceptance criteria, read-first paths, exact artifact paths, log + wiki-node instructions).
- `done` only when acceptance criteria are demonstrably met with evidence in today's log. Failures: your retry policy — one amended retry, then fix-task or human escalation.
- Keep plan.md statuses and state.json `tasks[]` current after every transition; logs append-only.
- Escalate mid-build per your escalation rules (ambiguity, destructive ops, tradeoffs, double failure) — pause the affected chain, keep independent work running.
- If the orchestrator instance dies TWICE to an infrastructure error (API 5xx/overload, stream abort), stop re-dispatching the same brief. Verify nothing partial landed (`git log <base_ref>..HEAD`, `git status --short`, state.json status counts), then relaunch it scoped to ONE wave or batch per instance until the window passes — short-lived instances survive overload windows that long-lived ones do not, and dispatched task agents (short-lived by construction) kept succeeding throughout.

## Report to the user (Korean)
완료/실패/차단 task counts with IDs, key artifacts (file paths), open escalations needing a decision, next step — `/harness:verify` when all tasks are done, or the specific unblock action. Do not declare the goal met here; only verify can.

## Retro nudge (always evaluate)
Count `(candidate)` lines in `.harness/wiki/INDEX.md`. If ≥5 candidate nodes, OR any `failure` event was logged during this build (including failures recovered by retry), OR a human escalation occurred, append to the report: "⚠️ 학습 루프 권장: 위키에 candidate 노드 N건 — 다음 build 전에 `/harness:retro` 실행을 권장합니다 (같은 실수 반복 방지)." One line only; do not run retro automatically.
