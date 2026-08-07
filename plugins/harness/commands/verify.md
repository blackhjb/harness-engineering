---
description: VERIFY phase — qa and code-reviewer run in parallel to check tests and GOAL.md success criteria; produces a PASS/FAIL verdict with evidence, FAIL spawns fix tasks via the orchestrator
argument-hint: "[optional: specific success criteria or areas to focus on]"
---

Run the harness VERIFY phase. Focus: $ARGUMENTS

Respond in Korean.

## Preconditions
Read `.harness/state.json` and `plan.md`. If build tasks are still `pending`/`in_progress`, warn that verify will likely fail and confirm before proceeding. Set state.json `phase` = "verify".

## Step 1 — Parallel verification (qa fans out per criterion; one code-reviewer per tree)
**qa 는 SC 단위로 팬아웃한다** — one small agent per success criterion (plus one for the regression suite), all launched in a single message. Verification is embarrassingly parallel at the criterion level: each check is 3~8 minutes on its own, and stacking nine of them into one session serializes what could have finished at once (실측 2026-08-06). `code-reviewer` stays ONE per working tree — a diff review needs the whole diff.
Delegate these IN PARALLEL (single message). Both RETURN structured reports and append log entries; neither edits plan.md or state.json — only the orchestrator (Step 3) converts findings into fix tasks.
**Multi-repo goals split by working tree, and a tree's pair starts as soon as THAT tree is frozen** — its tasks are `done` and no further commits are planned — without waiting for another tree's build. State the tree and its `git log <base>..HEAD` range in each brief; if commits later land in that tree, re-review only the delta. Review scope is per-tree, so a sibling repo still building never justifies idling (incident 2026-08-06: generalizing "a later commit would fall outside review scope" across repos idled the frozen backend behind an in-flight frontend task).
**측정 승계 — 같은 값을 두 번 만들지 않는다**: 측정 키 = `(명령 문자열, sha)`. 키가 같고 그 트리에 이후 커밋이 없으면 **로그의 값을 인용하고 재실행하지 않는다**. 재실행 의무는 셋뿐 — ①키·값이 로그에 없음 ②그 트리에 이후 커밋 존재 ③**red 이력이 없는 회귀 pin**(수정 전후 모두 green)은 goal 당 **표본 1건**을 검증자가 격리 worktree 에서 직접 주입해 재현하고 로그값과 대조한다. 그 일치가 나머지 대조군을 신뢰할 근거다. CPU 바운드 검증은 트리당 1세션.

- `qa` brief: read `.harness/GOAL.md`, `wiki/INDEX.md` (open qa + global/workflow nodes), `plan.md`, `design.md`. Check EVERY success criterion SC-n in GOAL.md and every task's 인수 조건 with an actual command, an inspection, or an audit of logged evidence per the scope rule above — none by assumption. **Additionally map EVERY plan.md task to exactly one of: commit sha / log result entry / explicit `deferred` with reason. One or more unmapped tasks = FAIL** — SC-level checks cannot see commit-less tasks, so "all SC met" and "a planned task never ran" can both be true (incident: an unexecuted guard-extension task passed verify). RETURN a table: 기준 / 검증 방법(실행한 명령) / 결과 / 증거, plus the task↔artifact map. Append full evidence (command output excerpts) to today's log.
- `code-reviewer` brief: same context. Review all code changed during this goal's build (diff against state.json `base_ref` where set) for correctness, design.md conformance, security, test adequacy. RETURN a table: 심각도(BLOCKER/MAJOR/MINOR/NIT) / 파일:라인 / 문제 / 권고. Append to today's log.

## Step 2 — Verdict
Compute the verdict yourself from both reports. Severity mapping: qa uses blocks-goal / blocks-task / minor; the reviewer uses BLOCKER / MAJOR / MINOR / NIT.
- PASS: every SC-n verified met AND zero qa blocks-goal/blocks-task findings AND zero reviewer BLOCKER findings.
- FAIL: anything else. Reviewer MAJOR findings become fix tasks and the verdict is FAIL. (qa minor and reviewer MINOR/NIT do not block PASS — list them.) Partial success is FAIL with an itemized gap list.
Record in state.json: `verify` = {"verdict": "PASS"|"FAIL", "date": now}. Append a verdict entry with evidence summary to today's log. Exactly two verdicts exist — a PASS with caveats, named risks, or conditions does not; anything short of full PASS is FAIL.

**Goal 결산 (same verdict entry):** aggregate the per-wave cost lines build already logged (dispatch count, diff size) into a final `git diff --shortstat <base_ref>..HEAD` + commit count + dispatch count, plus subagent token totals where observed. Retro mines these for ceremony-vs-diff disproportion — a goal with no 결산 is invisible to that loop.

## Step 3 — On FAIL, route fixes
Delegate to the `orchestrator` (the ONLY writer of plan.md and state.json `tasks[]`): for each unmet criterion, qa blocks-goal/blocks-task finding, and reviewer BLOCKER/MAJOR finding, add a fix task to plan.md (new T-NNN, owner, dependencies, acceptance criteria = the exact failed check), mirror into `tasks[]`, set phase back to "build". Point the user to `/harness:build`, then `/harness:verify` again.

## Report to the user (Korean)
Verdict up front (PASS/FAIL), criteria table, qa blocks-goal/blocks-task and reviewer BLOCKER/MAJOR findings, next step:
- PASS → `/harness:retro` (goal 마무리 회고).
- FAIL → fix-task list and `/harness:build`. If the same class of failure appears ≥2 times in the findings, or `wiki/INDEX.md` has ≥5 `(candidate)` nodes, recommend `/harness:retro` BEFORE `/harness:build`: "⚠️ 반복 실패 패턴 감지 — 수정 전에 `/harness:retro`로 위키에 등재하면 fix 작업이 같은 함정을 피합니다."
