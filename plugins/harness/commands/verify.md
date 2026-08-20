---
description: VERIFY phase — qa and code-reviewer run in parallel to check tests and GOAL.md success criteria; produces a PASS/FAIL verdict with evidence, FAIL spawns fix tasks via the 코디네이터
argument-hint: "[optional: specific success criteria or areas to focus on]"
---

Run the harness VERIFY phase. Focus: $ARGUMENTS

Respond in Korean.

## Preconditions
Read `.harness/state.json` and `plan.md`. If build tasks are still `pending`/`in_progress`, warn that verify will likely fail and confirm before proceeding. Set state.json `phase` = "verify".

## Step 1 — Parallel verification (qa fans out per criterion; one code-reviewer per tree)
**qa 는 SC 단위로 팬아웃한다** — one small agent per success criterion (plus one for the regression suite), all launched in a single message. Verification is embarrassingly parallel at the criterion level: each check is 3~8 minutes on its own, and stacking nine of them into one session serializes what could have finished at once (실측 2026-08-06). `code-reviewer` stays ONE per working tree — a diff review needs the whole diff.
Delegate these IN PARALLEL (single message), background 로 — 알림으로 결과를 모으고 그동안 결산 집계·장부 정리를 병행한다(20/45분 집행은 `harness-ledger` §디스패치 계약의 비동기 루프와 동일). Both RETURN structured reports and append log entries; neither edits plan.md or state.json — only the 코디네이터 (Step 3) converts findings into fix tasks.
**Multi-repo goals split by working tree, and a tree's pair starts as soon as THAT tree is frozen** — its tasks are `done` and no further commits are planned — without waiting for another tree's build. State the tree and its `git log <base>..HEAD` range in each brief; if commits later land in that tree, re-review only the delta. Review scope is per-tree, so a sibling repo still building never justifies idling (로그 2026-08-06).
**측정 승계는 원장으로 집행한다** (`harness-state` §측정 원장): 검증자는 측정 전 `grep -F '"key":"<명령>@<sha7>"' .harness/measurements.jsonl` 을 **먼저** 돌리고, 히트가 있고 이후 커밋이 없으면 재실행하지 않고 그 값을 인용한다. 재실행 의무는 셋뿐 — ①히트 없음 ②이후 커밋 존재 ③red 이력 없는 회귀 pin(goal 당 표본 1건만 격리 worktree 재현). 재측정해 **다른 값이 나오거나 결함을 실증하면 `refutes` 필드에 앞선 레코드 id 를 채워 원장에 append** — 이것이 M1(자기보고 정확도)의 유일한 입력이다. CPU 바운드 검증은 트리당 1세션.

- `qa` brief: read `.harness/GOAL.md`, `wiki/INDEX.md` (open qa + global/workflow nodes), `plan.md`, `design.md`. Check EVERY success criterion SC-n in GOAL.md and every task's 인수 조건 with an actual command, an inspection, or an audit of logged evidence per the scope rule above — none by assumption. **Additionally map EVERY plan.md task to exactly one of: commit sha / log result entry / explicit `deferred` with reason. One or more unmapped tasks = FAIL** — SC-level checks cannot see commit-less tasks, so "all SC met" and "a planned task never ran" can both be true (로그 참조). RETURN a table: 기준 / 검증 방법(실행한 명령) / 결과 / 증거, plus the task↔artifact map. Append full evidence (command output excerpts) to today's log.
- `code-reviewer` brief: same context. Review all code changed during this goal's build (diff against state.json `base_ref` where set) for correctness, design.md conformance, security, test adequacy. RETURN a table: 심각도(BLOCKER/MAJOR/MINOR/NIT) / 파일:라인 / 문제 / 권고. Append to today's log.

## Step 2 — Verdict
Compute the verdict yourself from both reports. Severity mapping: qa uses blocks-goal / blocks-task / minor; the reviewer uses BLOCKER / MAJOR / MINOR / NIT.
- PASS: every SC-n verified met AND zero qa blocks-goal/blocks-task findings AND zero reviewer BLOCKER findings.
- FAIL: anything else. Reviewer MAJOR findings become fix tasks and the verdict is FAIL. (qa minor and reviewer MINOR/NIT do not block PASS — list them.) Partial success is FAIL with an itemized gap list.
Record in state.json: `verify` = {"verdict": "PASS"|"FAIL", "date": now}. Append a verdict entry with evidence summary to today's log. Exactly two verdicts exist — a PASS with caveats, named risks, or conditions does not; anything short of full PASS is FAIL.

**Goal 결산 (same verdict entry):** `git diff --shortstat <base_ref>..HEAD` + 커밋 수 + 디스패치 수, 그리고 **품질 지표 M1·M2·M5 를 측정 원장에서 계수해 값으로 기재**한다(계수식은 `harness-state` §측정 원장; 목표치는 하네스 `docs/GOAL.md`). **계수 전에 이 goal 의 디스패치 수 ↔ 원장 `d` 레코드 수를 대조해 차이(누락 에이전트·tokens 미기재)를 값으로 병기한다** — 대조 없는 M2·M5 는 분모 불명이다. 원장은 append-only 이므로 누락 소급 기재는 금지, 차이 병기만 한다. 원장이 비었으면 「미측정」이라 적는다 — 100% 가 아니다. M3(상류 사실 정확도)·M4(요청 충족·과잉)는 아직 수기: 반증된 상류 사실 건수와 SC 중 출처 `제안` 행 수를 세어 적는다. 결산 없는 goal 은 retro 의 채굴 루프에 보이지 않는다.
**프로덕션 순삭제 헤드라인은 `git diff --numstat <base_ref>..HEAD -- src` 의 (added−deleted) 합 한 값으로만 적고 그 명령을 병기한다** — 웨이브·커밋 구간 부분합의 deletions 총계는 헤드라인이 될 수 없고, 같은 goal 이 부착했다 원복한 계측은 base..HEAD 에서 자동 상계되므로 실적 0 이다 (실측 2026-08-20: 구간 총계 −94 보고 vs base..HEAD 실순 −24, 차액 ~70줄이 자기 부착 원복). 테스트·스크립트 델타는 별항.

**백그라운드 잔여 스캔 (same verdict entry):** verdict 를 적기 전에 이 세션이 background 로 띄운 디스패치 전건의 생존을 확인한다 — "running" 표시는 생존 증거가 아니다(세션이 유휴로 넘어가면 통지는 영원히 오지 않는다, wiki `workflow--liveness-by-notification-not-inference`). 진행 중 항목은 ①재개 메시지로 결과 회수 ②kill 후 동기 재실행 ③명시 이월(로그에 소유자·재개 방법 기재) 중 하나로 처분하고, 처분 없이 세션을 넘기지 않는다.

## Step 3 — On FAIL, route fixes
코디네이터가 직접 (the ONLY writer of plan.md and state.json `tasks[]`): for each unmet criterion, qa blocks-goal/blocks-task finding, and reviewer BLOCKER/MAJOR finding, add a fix task to plan.md (new T-NNN, owner, dependencies, acceptance criteria = the exact failed check), mirror into `tasks[]`, set phase back to "build". Point the user to `/harness:build`, then `/harness:verify` again.

## Report to the user (Korean)
Verdict up front (PASS/FAIL), criteria table, qa blocks-goal/blocks-task and reviewer BLOCKER/MAJOR findings, next step:
- PASS → `/harness:retro` (goal 마무리 회고).
- FAIL → fix-task list and `/harness:build`. If the same class of failure appears ≥2 times in the findings, or `wiki/INDEX.md` has ≥5 `(candidate)` nodes, recommend `/harness:retro` BEFORE `/harness:build`: "⚠️ 반복 실패 패턴 감지 — 수정 전에 `/harness:retro`로 위키에 등재하면 fix 작업이 같은 함정을 피합니다."
