---
description: Lightweight path for S-size tasks (single-file bugfix, config change, small refactor) — one dev agent, tests, log trail; refuses anything that needs the full loop
argument-hint: "<one-line task, e.g. 'fix NPE in OrderService.cancel'>"
---

Run a harness QUICK task: $ARGUMENTS

Respond in Korean. This path skips analyze/plan/design for genuinely small work — it does NOT skip the harness's memory discipline.

## 1. Preconditions
`.harness/` and `.harness/state.json` must exist. If not, stop and point to `/harness:goal` — quick tasks still need GOAL.md and the wiki as context.

## 2. Classify (hard gate)
Quick is ONLY for S-size work: single-file bugfix, config change, small localized refactor. REFUSE and redirect to the full loop (`/harness:analyze` → `/harness:plan`) if the task:
- creates or changes an API/data contract (new endpoint, schema/migration, message shape), or
- spans multiple modules/components, or
- changes data models, or
- is ambiguous enough that a wrong guess is expensive.
When refusing, say why in one line and name the command to run instead. Do not offer to bypass this gate.

## 3. Execute
1. Append a quick-task entry to today's daily log (`## HH:MM [quick] dispatch`, task one-liner, why it qualifies as quick).
2. Dispatch ONE dev agent — backend-dev, frontend-dev, or ai-agent-dev — with this brief:
   - Read `.harness/GOAL.md` and `wiki/INDEX.md` (open own-scope + global/workflow nodes) FIRST (mandatory), plus the design.md sections relevant to the touched area (API 계약 / 데이터 모델 / 에러 전략 as applicable).
   - No plan.md task exists for quick mode — this brief IS your task assignment and acceptance criteria; the "work only your plan.md task" rule is waived.
   - Make the change; run focused tests for the touched code.
   - Append a result entry with evidence to today's log; insights as wiki nodes (create/reinforce/promote per the `harness-state` skill).
3. On return, run the project's test suite (or dispatch `qa` for a focused check if the suite is heavy); confirm green with real output. Exception — documentation-only changes: skip the suite; a reviewer glance (or self-check of rendered content and links) suffices, and the report states this exception was used.

## 4. Report (Korean)
What changed (file paths), test evidence, wiki insights added. Append a final result entry to today's log.

State discipline: quick tasks leave a log trail only — do NOT add rows to plan.md, do NOT touch state.json `phase` or `tasks[]`. If the "quick" task turns out bigger mid-flight, stop, log it, redirect to the full loop.
