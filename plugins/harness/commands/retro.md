---
description: RETRO phase — delegate to harness-improver to mine failures from logs and retro inbox, update the playbook ACE-style, and propose bounded harness edits for user approval
argument-hint: "[optional: specific incident or theme to focus on]"
---

Run the harness RETRO (회고) phase. Focus: $ARGUMENTS

Respond in Korean.

## Preconditions
Proceed if `.harness/logs/` contains at least one daily log (excluding `logs/archive/`) OR `.harness/retro/inbox.md` has unchecked items. If neither holds, tell the user there is nothing to retro yet and stop.

## Step 1 — Delegate to harness-improver
Brief:
- Your startup protocol: read GOAL.md and playbook.md, find the last retro report, mine `retro/inbox.md` plus all `logs/` entries since then. Apply the user's focus if given: "$ARGUMENTS".
- Cluster failures into patterns (surface error vs causal mechanism); only patterns with ≥2 occurrences or one high-severity event yield proposals.
- Write the full report to `.harness/retro/YYYY-MM-DD.md` per your output contract (실행 요약 / 패턴 분석 / 플레이북 변경 / 하네스 수정 제안 / 관찰 항목).
- Apply playbook changes (add/merge/retire bullets) directly to `.harness/playbook.md`.
- Do NOT apply agent-prompt or workflow-gate edits — return them as diffs for human approval.
- Clean promoted/retired items out of retro/inbox.md per your inbox rules (below-threshold lines stay), log completion. Do NOT write state.json — the command handles the phase change.

## Step 2 — Present for approval (Korean)
On return, first set state.json `phase` = "retro", refresh `updated_at` (commands may set phase; the improver may not). Then:
1. Pattern table (패턴 / 횟수 / 심각도 / 인과 메커니즘).
2. Playbook changes already applied (added/merged/retired bullet IDs and text).
3. Each harness edit proposal as a diff with 증거 / 기대 효과 / 회귀 리스크; the user approves or rejects EACH ONE individually. Apply only approved diffs to the named agent/command files; record each decision (approved/rejected + reason) in the retro report.
4. Never apply a rejected or unreviewed proposal; never let the improver touch permission or safety rules.

## Step 3 — Close the loop
If the verify verdict is PASS and no fix work remains, offer to set phase to "done". Suggest next: a new `/harness:goal`, or nothing.
