---
description: Set or reset the harness goal — brief interview, then scaffold .harness/ and write GOAL.md with measurable success criteria
argument-hint: "<one-line goal>"
---

The user wants to set a harness goal: $ARGUMENTS

Respond in Korean; write all .harness/ files in Korean (code identifiers, file paths, technical terms as-is). Consult the harness-state skill; scaffold files directly from its canonical section lists.

## 1. Interview (one message, short)
Ask in Korean, in a single message, only what "$ARGUMENTS" does not already answer (max 5):
1. 성공 기준 — how will we MEASURE done? Push for verifiable checks ("p95 < 200ms", "이 3개 API가 통합 테스트 통과"), not feelings.
2. 제약 — tech stack constraints, must-not-change, infra/budget limits.
3. 기한 — deadline or time budget.
4. 범위 제외 — explicitly OUT of scope.
5. 참고 컨텍스트 — existing code/docs to look at first (optional).
Wait for the answers before writing anything. If a success criterion comes back vague, restate it measurably once ("이렇게 바꾸면 측정 가능합니다: ... 맞습니까?") and proceed on confirmation.

## 2. Handle an existing .harness/
- No `.harness/`: create the full structure below.
- `.harness/` exists: NEW GOAL ITERATION. Preserve `playbook.md`, `retro/`, and `logs/` — accumulated learning. Read the old state.json, increment `iteration`, and overwrite GOAL.md / analysis.md / prd.md / design.md / plan.md with fresh scaffolds. If the previous goal's phase is not `done` or `retro`, warn the user it is unfinished and get explicit confirmation before overwriting.

## 3. Create files (from the harness-state skill's canonical section lists)
Every section present, empty ones marked "해당 없음".
- `.harness/GOAL.md` — filled from the interview.
- `analysis.md`, `prd.md`, `design.md`, `plan.md` — headers only, sections per the skill's lists.
- `state.json` — per the skill's schema: `goal_id` = `<yyyymmdd>-<short-slug>`, `base_ref` = current commit SHA from `git rev-parse HEAD` (null if not a git repo), `phase` = "goal", `iteration` (1 or incremented), `updated_at` = now, `approvals` all false, `verify` = {"verdict": null, "date": null}, `tasks` = [].
- `playbook.md` — create with header + format comment ONLY if missing; never overwrite an existing playbook.
- `retro/inbox.md` and `logs/` — create if missing.
- Append a goal-set entry to today's daily log (who, what goal, iteration).

## 4. Confirm and hand off
Show the user in Korean: the success criteria table, 제약, 범위 제외; ask them to confirm GOAL.md or request edits. Once confirmed, the next step is `/harness:analyze`.

## Question rules (co-creation)
All user questions in this phase follow the `co-creation` skill (key branch points only, batched options with a recommended default, decisions recorded in the owning document and never re-asked); exception — the initial interview may ask short open-ended questions for basic facts (기한, 제약 등).
