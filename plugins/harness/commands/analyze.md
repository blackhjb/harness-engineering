---
description: ANALYZE phase — delegate to the analyst agent to investigate the codebase and context, producing .harness/analysis.md
argument-hint: "[optional focus area]"
---

Run the harness ANALYZE phase. Focus hint from the user: $ARGUMENTS

Respond in Korean.

## Preconditions
- `.harness/GOAL.md` must exist; if not, stop and point to `/harness:goal`.
- Read `.harness/state.json`. If phase is past `analyze` (plan/design/build/verify), warn that re-analysis will feed a plan revision, but proceed if the user asked for it.

## Steps
1. Set state.json `phase` = "analyze", refresh `updated_at`.
2. Delegate to the `analyst` agent with this brief:
   - Read `.harness/GOAL.md` and `.harness/wiki/INDEX.md` (open analysis + global/workflow nodes) first.
   - Investigate the codebase and context relevant to the goal — structure, key modules, dependencies, existing tests, build/deploy setup — plus the focus hint "$ARGUMENTS".
   - Write `.harness/analysis.md` in Korean per the harness-state skill's canonical analysis sections; each unknown needs a 확인 방법 and whether it BLOCKS planning; risks with 조기 신호 and 대응.
   - Append a result entry with key evidence to today's log (`.harness/logs/YYYY-MM-DD.md`).
3. When the analyst returns, read `.harness/analysis.md` yourself: it must name concrete files/versions/commands, not generic statements. If shallow, send the analyst back exactly once, naming the specific gaps.
4. Refresh state.json `updated_at`.

## Report to the user (Korean)
- 핵심 발견 3-5개 (파일 경로 포함)
- 가장 위험한 리스크 2-3개
- 계획을 차단하는 항목 (알아내야 하는 것 U-n 중 차단 여부 "예") — if any exist, ask the user to resolve them NOW
- 다음 단계 (차단 항목이 없을 때): analysis.md 의 권고가 정한 경로 — 남은 작업이 quick 경로 기준(goal 커맨드 §2: 계약·아키텍처 결정 0 + 기계적 소규모 diff + 명령 판정 가능 SC)을 충족하면 `/harness:quick`, 아니면 `/harness:plan`. 권고는 반드시 어느 쪽인지 명시한다 — 규모 판정 없이 기본값으로 plan 에 넘기지 말 것

## Question rules (co-creation)
All user questions in this phase follow the `co-creation` skill (key branch points only, batched options with a recommended default, decisions recorded in the owning document and never re-asked).
