---
description: Read .harness/ state and render a concise Korean status report — phase, task progress, blockers, and next actions
argument-hint: ""
---

Render the current harness status. READ-ONLY — do not modify any .harness/ file, do not dispatch agents.

If `.harness/` or `.harness/state.json` does not exist, tell the user (Korean) that no harness goal is set and to run `/harness:goal`.

## Gather
1. `.harness/state.json` — goal_id, phase, iteration, approvals, verify verdict, tasks.
2. `.harness/GOAL.md` — one-line goal, success criteria IDs.
3. `.harness/plan.md` (if present) — task table.
4. Today's daily log — or, if absent, the most recent one directly under `logs/` (NEVER `logs/archive/`) — scan the last entries for failures, escalations, open decisions.
5. `.harness/retro/inbox.md` — unprocessed insight count.
Cross-check: if state.json and plan.md disagree on a task status, report BOTH values and flag it — do not fix it here.

## Render (Korean, compact — under 30 lines)
```
## 하네스 상태: <goal 한 줄> (iteration N)
- 단계: <phase> | 마지막 업데이트: <updated_at>
- 승인: design <✅/❌> · plan <✅/❌> | 검증: <PASS/FAIL/미실행>

### 작업 진행 (done/전체)
| ID | 작업 | 담당 | 상태 |
(in_progress / blocked / failed 작업만 행으로; done은 개수로 요약)

### 차단 요인
- (최근 로그의 escalation·failure·미해결 결정. 없으면 "없음")

### 다음 액션
1. <현재 단계와 게이트 기준으로 실행할 커맨드 — 예: 설계 미승인이면 /harness:plan 승인부터>
```

Next-action logic: phase goal → `/harness:analyze`; analyze → `/harness:plan`; plan/design without approvals → get approval in `/harness:plan`; approved but tasks pending → `/harness:build`; all tasks done, no verdict → `/harness:verify`; verify FAIL → fix tasks via `/harness:build`; verify PASS → `/harness:retro`; retro done → new `/harness:goal`. An open escalation in the logs is ALWAYS next action #1.
