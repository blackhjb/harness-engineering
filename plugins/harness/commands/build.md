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
**병렬/직렬의 유일한 축은 쓰기 트리 공유다.** Write tasks in the SAME working tree are serial — group them into one session that does them in order and commits per task (separate dispatches buy nothing there and each costs a round trip plus a cold context). Write groups in DIFFERENT trees, and every read-only check, run in parallel in one message. Nothing else — not phase, not repo, not "conceptually separate" — justifies serializing.
**브리프는 태스크 1건 크기로 유지한다**: one dispatch carries ONE task's acceptance criteria (or, when grouped by shared tree, each task's own criteria and nothing more). Loading a phase's worth of axes into one session is what turns a 5-minute check into 40 (실측 2026-08-06: 9~12개 축을 얹은 검증 세션이 툴 호출 41~70회 · 37~46분). Grouping reduces round trips; it must never inflate a brief.
**디스패치 프롬프트에 위키·스킬 내용을 재서술하지 않는다**: point the agent at `wiki/INDEX.md` + its own scope and give it the task's criteria. Pasting the rules in yourself bypasses the recall path the wiki exists for — the knowledge stops being retrievable and becomes your copy-paste (2026-08-06: recorded lessons never reached the agents that needed them for exactly this reason).

**orchestrator 기동 조건**: **묶은 뒤의 디스패치가 4건 이상이거나 병렬 트리가 3개 이상**일 때만 orchestrator 를 기동한다. 그 미만은 코디네이터가 role 에이전트를 **직접 디스패치**한다 — 왕복 게이트가 실작업보다 커지고, 장수명 인스턴스는 과부하의 단일 실패점이다(실측: 529 사망 4회·게이트 왕복 40~70분 vs 직접 디스패치 사망 0).
**실행 계획 변경은 메시지로 보내지 말고 소유권을 옮긴다**: a message to a running orchestrator is NOT delivered until its next tool round, and while it waits on a subagent that can be tens of minutes. So when a plan change is time-sensitive (parallelize this wave, drop that task), the coordinator **takes that wave over and dispatches it directly**, then sends the orchestrator a "이 웨이브 디스패치 금지" correction so exactly one dispatcher owns each tree. Never let both act on the same wave — two agents in one working tree is the failure this rule exists to prevent (2026-08-06).
**웨이브 비용 감지(웨이브 종료마다 1줄)**: log cumulative dispatch count and current diff size (`git diff --shortstat <base_ref>..HEAD`). **디스패치 수 > 변경 파일 수** means ceremony has overtaken the change — cut the remaining ceremony (merge dispatches, drop redundant verification tasks) in that same turn and say so in the line. Waiting for verify's 결산 to notice is too late; the user should not be the detector.
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
