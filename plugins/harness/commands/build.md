---
description: BUILD phase — the orchestrator executes plan.md, dispatching independent tasks to owner agents in parallel, updating state.json and logs until all tasks meet acceptance criteria
argument-hint: "[optional: specific task IDs to run, e.g. T-003 T-004]"
---

Run the harness BUILD phase. Optional task filter: $ARGUMENTS

Respond in Korean.

## Preconditions (hard gate)
Read `.harness/state.json`. Both `approvals.design` and `approvals.plan` must be true — if not, stop and point the user to `/harness:plan` approval. Do not offer to bypass this.

## Execution
Set state.json `phase` = "build", then delegate the entire build to the `orchestrator` with this brief:
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
