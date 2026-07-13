---
description: VERIFY phase — qa and code-reviewer run in parallel to check tests and GOAL.md success criteria; produces a PASS/FAIL verdict with evidence, FAIL spawns fix tasks via the orchestrator
argument-hint: "[optional: specific success criteria or areas to focus on]"
---

Run the harness VERIFY phase. Focus: $ARGUMENTS

Respond in Korean.

## Preconditions
Read `.harness/state.json` and `plan.md`. If build tasks are still `pending`/`in_progress`, warn that verify will likely fail and confirm before proceeding. Set state.json `phase` = "verify".

## Step 1 — Parallel verification (single message, two Task calls)
Delegate to `qa` and `code-reviewer` IN PARALLEL. Both RETURN structured reports and append log entries; neither edits plan.md or state.json — only the orchestrator (Step 3) converts findings into fix tasks.
- `qa` brief: read `.harness/GOAL.md`, `playbook.md`, `plan.md`, `design.md`. Run the test suites and check EVERY success criterion SC-n in GOAL.md and every task's 인수 조건 with an actual command or inspection — none by assumption. RETURN a table: 기준 / 검증 방법(실행한 명령) / 결과 / 증거. Append full evidence (command output excerpts) to today's log.
- `code-reviewer` brief: same context. Review all code changed during this goal's build (diff against state.json `base_ref` where set) for correctness, design.md conformance, security, test adequacy. RETURN a table: 심각도(BLOCKER/MAJOR/MINOR/NIT) / 파일:라인 / 문제 / 권고. Append to today's log.

## Step 2 — Verdict
Compute the verdict yourself from both reports. Severity mapping: qa uses blocks-goal / blocks-task / minor; the reviewer uses BLOCKER / MAJOR / MINOR / NIT.
- PASS: every SC-n verified met AND zero qa blocks-goal/blocks-task findings AND zero reviewer BLOCKER findings.
- FAIL: anything else. Reviewer MAJOR findings become fix tasks and the verdict is FAIL. (qa minor and reviewer MINOR/NIT do not block PASS — list them.) Partial success is FAIL with an itemized gap list.
Record in state.json: `verify` = {"verdict": "PASS"|"FAIL", "date": now}. Append a verdict entry with evidence summary to today's log. Exactly two verdicts exist — a PASS with caveats, named risks, or conditions does not; anything short of full PASS is FAIL.

## Step 3 — On FAIL, route fixes
Delegate to the `orchestrator` (the ONLY writer of plan.md and state.json `tasks[]`): for each unmet criterion, qa blocks-goal/blocks-task finding, and reviewer BLOCKER/MAJOR finding, add a fix task to plan.md (new T-NNN, owner, dependencies, acceptance criteria = the exact failed check), mirror into `tasks[]`, set phase back to "build". Point the user to `/harness:build`, then `/harness:verify` again.

## Report to the user (Korean)
Verdict up front (PASS/FAIL), criteria table, qa blocks-goal/blocks-task and reviewer BLOCKER/MAJOR findings, next step:
- PASS → `/harness:retro` (goal 마무리 회고).
- FAIL → fix-task list and `/harness:build`. If the same class of failure appears ≥2 times in the findings, or `retro/inbox.md` has ≥5 unprocessed insights, recommend `/harness:retro` BEFORE `/harness:build`: "⚠️ 반복 실패 패턴 감지 — 수정 전에 `/harness:retro`로 플레이북에 등재하면 fix 작업이 같은 함정을 피합니다."
