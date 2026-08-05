---
description: Lightweight path for S/M-size mechanical work (bugfix, config change, guard/test additions, small refactor batch) — minimal ceremony, full verification rigor; refuses anything that needs the full loop
argument-hint: "<one-line task, e.g. 'fix NPE in OrderService.cancel'>"
---

Run a harness QUICK task: $ARGUMENTS

Respond in Korean. This path skips analyze/plan/design ceremony for genuinely small work — it does NOT skip the harness's memory discipline, and it NEVER skips verification rigor (경량화는 문서·오케스트레이션에만 적용되고 검증 증거에는 적용되지 않는다).

## 1. Preconditions
`.harness/` and `.harness/state.json` must exist. If not, stop and point to `/harness:goal` — quick tasks still need GOAL.md and the wiki as context.

## 2. Classify (hard gate)
Quick covers S-size work (single-file bugfix, config change, small localized refactor) AND M-size mechanical batches (several small localized edits — guards, re-exports, test fixes, doc/config tweaks — with zero contract or architecture impact; roughly ≤8 files / ≤150 lines expected diff). REFUSE and redirect to the full loop (`/harness:analyze` → `/harness:plan`) if the task:
- creates or changes an API/data contract (new endpoint, schema/migration, message shape), or
- requires an architecture decision (new module boundary, tech choice, non-mechanical coupling change that propagates behavior across modules), or
- changes data models, or
- is ambiguous enough that a wrong guess is expensive.
When refusing, say why in one line and name the command to run instead. Do not offer to bypass this gate.

## 3. Execute
1. Append a quick-task entry to today's daily log (`## HH:MM [quick] dispatch`, task one-liner, why it qualifies as quick).
2. Do the work — one of:
   - **Coordinator-direct** for tiny unambiguous edits (a few lines, no judgment calls): edit in the main loop and log it as such; or
   - **Dispatch ONE dev agent** — backend-dev, frontend-dev, or ai-agent-dev — with this brief:
     - Read `.harness/GOAL.md` and `wiki/INDEX.md` (open own-scope + global/workflow nodes) FIRST (mandatory), plus the design.md sections relevant to the touched area (API 계약 / 데이터 모델 / 에러 전략 as applicable).
     - No plan.md task exists for quick mode — this brief IS your task assignment and acceptance criteria; the "work only your plan.md task" rule is waived.
     - Make the change; run focused tests for the touched code.
     - Append a result entry with evidence to today's log; insights as wiki nodes (create/reinforce/promote per the `harness-state` skill).
3. **Proportional verification (mandatory, not reducible):**
   - Always: run the project's test suite (or dispatch `qa` for a focused check if the suite is heavy); confirm green with real output, plus the project's import/boot smoke if one is established. Exception — documentation-only changes: skip the suite; a reviewer glance (or self-check of rendered content and links) suffices, and the report states this exception was used.
   - If the change adds or modifies a guard/lint/test-that-must-catch: a **positive control is mandatory** — inject a known violation → red (exit code) → revert → green, logged with the actual commands and outputs. A guard merged without a red reproduction is not done ("초록불 lint 는 없는 lint 보다 나쁘다").
   - For a multi-file batch: ONE `code-reviewer` pass over the final diff before calling it done (single file, a NIT-level tweak: reviewer optional).
4. If this quick run completes a quick-routed GOAL (state.json goal whose route was set to quick by `/harness:goal`): measure EVERY SC in GOAL.md with its stated command, append a `verify` log entry with the values **plus the goal 결산** (`git diff --shortstat <base_ref>..HEAD`, commit count, dispatch count, observed subagent tokens — same fields as the full loop's verdict entry; retro mines these for ceremony-vs-diff disproportion), set state.json `verify` = {verdict, date} and `phase` = "done" on PASS. This closure is the command/coordinator's job — never the dev agent's.

## 4. Report (Korean)
What changed (file paths), test + positive-control evidence (actual values/exit codes), reviewer verdict if dispatched, wiki insights added. Append a final result entry to today's log.

State discipline: quick tasks leave a log trail only — do NOT add rows to plan.md, do NOT touch state.json `phase` or `tasks[]` (the goal-closure step in 3.4 is the one exception, and it belongs to the command, not the dev agent). If the "quick" task turns out bigger mid-flight, stop, log it, redirect to the full loop.
