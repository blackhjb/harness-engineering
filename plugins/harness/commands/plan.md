---
description: PLAN + DESIGN phases — planner writes prd.md, architect (plus product-designer for user-facing work) writes design.md, orchestrator breaks it into plan.md tasks; ends at a user approval gate before build
argument-hint: "[optional notes or emphasis]"
---

Run the harness PLAN (기획) and DESIGN (설계) phases. User notes: $ARGUMENTS

Respond in Korean. All artifacts in Korean per the harness-state skill.

## Preconditions
`.harness/GOAL.md` and `.harness/analysis.md` must exist and be filled in (not empty scaffolds); otherwise stop and point to `/harness:goal` or `/harness:analyze`. If analysis.md lists a blocking item in 알아내야 하는 것 (차단 여부 "예"), surface it to the user before proceeding.

## Stage 1 — PRD (planner)
Set state.json `phase` = "plan". Delegate to `planner`: read GOAL.md, playbook.md, analysis.md; write `.harness/prd.md` per the harness-state skill's canonical PRD sections (P0 = must-ship). Every P0 story must trace to a success criterion (SC-n) in GOAL.md.

## Stage 2 — Design (architect, + product-designer when user-facing)
Set state.json `phase` = "design". Determine from prd.md whether the work has user-facing UI.
- Delegate to `architect`: read GOAL/playbook/analysis/prd; write `.harness/design.md` per the harness-state skill's canonical 12 sections — all except `8. UX 설계`.
- If user-facing: delegate to `product-designer` IN PARALLEL (same message) to write the `8. UX 설계` section (screens, flows, states, error/empty/loading cases) — architect owns the file merge; product-designer returns its section and architect integrates it, or dispatch product-designer after architect if they would collide on the same file.
Check design.md answers every P0 story; if a P0 lacks design coverage, send the gap back to the architect once.

## Stage 3 — Task breakdown (orchestrator)
Delegate to `orchestrator`: read all of the above; write `.harness/plan.md` — task table (T-NNN, 작업, 담당, 의존성, 인수 조건, 상태=pending), parallel wave grouping, risks. Rules to pass along: every task sized for one agent session; acceptance criteria checkable by a command or file inspection; owners from the harness-state state.json role list; every P0 requirement covered by at least one task; qa tasks included, not implied. Orchestrator mirrors tasks into state.json `tasks[]` (plan.md and `tasks[]` are orchestrator-only).

## Stage 4 — Approval gate (do not skip)
Present in Korean: prd.md priorities summary, design.md key decisions and tradeoffs, and the full plan.md task table with waves. Ask explicitly: "이 설계와 계획을 승인하시겠습니까? 수정할 부분이 있으면 알려주세요."
- On approval: set state.json `approvals.design` = true and `approvals.plan` = true, refresh `updated_at`, log the approval, and point to `/harness:build`.
- On change requests: route each to the owning agent (planner/architect/product-designer/orchestrator), then re-present. Never set approvals without an explicit yes.

## Question rules (co-creation)
All user questions in this phase follow the `co-creation` skill (key branch points only, batched options with a recommended default, decisions recorded in the owning document and never re-asked).
