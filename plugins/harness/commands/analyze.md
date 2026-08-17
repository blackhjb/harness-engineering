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
0. **표면 ≤3파일이면 analyst 를 부르지 않는다** — 코디네이터가 직접 grep 으로 사실을 세우고 `analysis.md` 에 F-NNN 만 적는다. 디스패치 1건이 통째로 빠지고, 이 규모에서 analyst 가 새로 알아내는 것은 실측상 없다.
1. Set state.json `phase` = "analyze", refresh `updated_at`.
2. Delegate to the `analyst` agent with this brief. 브리프에는 조사 대상 서비스 유형에 맞는 **도메인 특화 스킬 slug**(예: LLM 에이전트=ai-agent-dev · Python 서비스=python-service)를 지정한다 — 중립 브리프 금지 (사용자 정책 2026-08-18). **When the goal has two or more independent investigation fronts, dispatch one analyst per front IN PARALLEL (single message)** — each writes its own `/tmp/agent-analyst-<front>-<date>.md` and appends its own log entry, and the coordinator merges the fronts into `.harness/analysis.md` itself (the merge is a compression pass, not a third dispatch; note the merge in the log). Serializing independent fronts, or spending an extra agent on the merge, is the avoidable cost here.
   - Read `.harness/GOAL.md` and `.harness/wiki/INDEX.md` (open analysis + global/workflow nodes) first.
   - **탐색 경계**: 브리프에 코디네이터가 이미 잰 **시작 파일 목록**(grep 실측)을 싣고 "여기서 출발, 재검증 말 것"을 명시한다. 그 밖으로 넓히려면 답이 안 나온 질문을 1줄로 적고 넓힌다 — 열린 탐색이 analyst 세션을 12분으로 만든 원인이다.
   - **질문 ≤5개, 그리고 질문 1개 = 명령 몇 줄로 답이 나오는 크기.** 전수표·런타임 전개·git 이력 조사·임계 스윕을 한 질문에 묶으면 개수 상한을 지킨 채 세션이 시간 단위가 된다 (로그 2026-08-07). 그 크기면 질문이 아니라 태스크다 — 분해하거나 답을 build 로 미룬다.
   - **증명 규율을 브리프에 넣지 않는다.** 양성 대조군 주입·임계 하향 대조·red 선실측은 build/verify 소관이다. 위키 `qa` 노드도 **판정 규율**(계수 경계, prod/테스트 분리, 런타임 도달)만 싣고 **증명 절차**(대조군·주입·스윕)는 싣지 않는다.
   - Write `.harness/analysis.md` (**≤80줄**, 초과 시 압축이 핸드오프 조건) in Korean per the `harness-ledger` skill's canonical analysis sections; each unknown needs a 확인 방법 and whether it BLOCKS planning; risks with 조기 신호 and 대응.
   - Append a result entry with key evidence to today's log (`.harness/logs/YYYY-MM-DD.md`).
3. When the analyst returns, read `.harness/analysis.md` yourself: it must name concrete files/versions/commands, not generic statements. If shallow, send the analyst back exactly once, naming the specific gaps.
4. Refresh state.json `updated_at`.

## Report to the user (Korean)
- 핵심 발견 3-5개 (파일 경로 포함)
- 가장 위험한 리스크 2-3개
- 계획을 차단하는 항목 (알아내야 하는 것 U-n 중 차단 여부 "예") — if any exist, ask the user to resolve them NOW
- 다음 단계 (차단 항목이 없을 때): analysis.md 의 권고가 정한 경로 — 남은 작업이 quick 경로 기준(goal 커맨드 §2: 계약·아키텍처 결정 0 + 기계적 소규모 diff + 명령 판정 가능 SC)을 충족하면 `/harness:quick`, 아니면 `/harness:plan`. 권고는 반드시 어느 쪽인지 명시한다 — 규모 판정 없이 기본값으로 plan 에 넘기지 말 것

## Question rules
질문은 `co-creation` 스킬을 따른다; 기록된 결정은 재질의하지 않는다.
