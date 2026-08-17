---
description: Lightweight path for S/M-size mechanical work (bugfix, config change, guard/test additions, small refactor batch) — minimal ceremony, full verification rigor; refuses anything that needs the full loop
argument-hint: "<one-line task, e.g. 'fix NPE in OrderService.cancel'>"
---

Run a harness QUICK task: $ARGUMENTS

한국어로 응답한다.

**quick 이 표준 루프와 다른 점은 정확히 셋뿐이다** — ①`/harness:plan` Stage 4 **승인 게이트를 거치지 않는다**(기계적 변경이라 승인할 설계가 없다) ②분해가 배치 1건이라 웨이브·orchestrator 가 없다 ③verify 커맨드 대신 **코디네이터가 종결한다**. 그 외 전부 — 위키 선독, 디스패치 단가, 검증 엄격도, 장부 형식 — 는 표준 루프와 **같은 규칙, 같은 소유자**다. 여기서 다시 정의하지 않는다. 이 파일에 규칙을 복제하면 한쪽만 고쳐질 때 조용히 갈라진다(실측 2026-08-10: 측정 원장 도입 시 verify·quick 을 따로 고쳐야 했다).

## 1. Preconditions
`.harness/` 와 `state.json` 이 있어야 한다. 없으면 중단하고 `/harness:goal` 로 안내 — quick 도 GOAL.md 와 위키가 컨텍스트다.
**코디네이터 자신도 위키를 읽는다**(`harness-state` 규칙 4①) — §3 의 Coordinator-direct 경로는 서브에이전트를 거치지 않으므로, 코디네이터가 직접 읽지 않으면 위키가 그 편집에 **구조적으로 도달하지 못한다**.

## 2. Classify (hard gate)
Quick 대역의 정본은 `goal.md` §2 다. 그 조건을 하나라도 벗어나면 **거부하고** 전체 루프(`/harness:analyze` → `/harness:plan`)로 돌린다: 계약 변경 · 아키텍처 결정 · 데이터 모델 변경 · 오판이 비싼 모호함. 거부할 때는 사유 1줄과 실행할 커맨드 이름을 말한다. 게이트 우회를 제안하지 않는다.

## 3. Execute
1. 오늘 일간 로그에 quick 항목 append (`## HH:MM [quick] dispatch`, 작업 한 줄, quick 자격 근거).
2. 작업 — 둘 중 하나:
   - **Coordinator-direct** — `build.md` 의 메인 직접 대역(≤3파일·≤40줄·판정 0건·역편집 복구 가능)에 들면 직접 고치고 그렇게 로그한다.
   - **dev 에이전트 1명 디스패치** — backend-dev / frontend-dev / ai-agent-dev. 브리프를 쓰기 전에 **`agents/orchestrator.md` 의 `## Dispatch contract` · `## Dispatch economy` · `## 비동기 루프` 세 절을 열어 그대로 승계한다**(orchestrator 를 기동하지 않으므로 코디네이터가 그 책무를 진다 — `build.md` §우회 시 책무 승계와 같은 구조). quick 고유 조항은 하나뿐: **plan.md 태스크가 없으므로 이 브리프가 곧 과제이자 인수 조건**이며 "자기 plan.md 태스크만" 규칙은 면제된다.
3. **Proportional verification (경감 불가):**
   - 항상: 프로젝트 전건 스위트(무거우면 `qa` 에 위임) — 실제 출력으로 green 확인 + 확립된 import/boot smoke. 예외는 **문서 전용 변경**뿐(스위트 생략, 리뷰어 일별 또는 렌더 자체 점검으로 갈음하고 그 예외를 썼다고 보고에 적는다).
   - 가드·lint·반드시 잡아야 하는 테스트를 추가·수정했으면 **양성 대조 필수** — 절차와 함정은 `testing-qa` §8(생산자별 주입). 대조군은 **사용자 관측 행동을 지키는 가드에만** 붙이고, 생략했으면 판단 근거를 로그에 1줄.
   - 다중 파일 배치는 최종 diff에 **`code-reviewer` 1회가 게이트다** — 미실행 상태로 done·PASS 선언 금지(단일 파일 NIT 수준이면 선택). 실행하지 않았으면 사유를 종결 항목에 적고 verdict 를 보류한다.
4. **종결** — quick 으로 라우팅된 GOAL 을 이 실행이 완료하면, verify 커맨드 대신 코디네이터가 종결한다. GOAL.md 의 **모든 SC 를 그 SC 가 적은 명령으로 측정**하고(측정 전 원장 조회 · 새 측정은 원장 append), `verify` 로그 항목에 값 + **결산**을 적은 뒤 state.json `verify` = {verdict, date}, PASS 면 `phase` = "done". 결산 필드와 M1·M2·M5 계수식은 `verify.md` §Goal 결산과 동일하다 — 여기서 다시 적지 않는다.
   **종결 체크리스트(전건 기재)**: SC 전건 측정값 · 결산 · **배치↔산출물 사상**(배치마다 원장 `d` 레코드 1건, 각 레코드가 커밋 sha 또는 `deferred`+사유에 사상 — 미사상 1건이라도 있으면 종결 금지) · **code-reviewer verdict 또는 미실행 사유** · **독립성**(코드를 직접 수정한 주체는 그 diff 의 PASS 를 스스로 내지 않는다 — 직접 수정이 있었으면 `code-reviewer` 또는 `qa` 1인 필수).

## 4. Report (한국어)
바뀐 것(파일 경로) · 테스트와 양성 대조 증거(실제 값·exit code) · 리뷰어 verdict · 추가한 위키 통찰. 오늘 로그에 최종 result 항목 append.

**장부 규율**: quick 은 `plan.md` 를 만들지 않는다 — 배치↔산출물 사상은 **원장 `d` 레코드**가 지고, `state.json.tasks[]` 는 비워 둔다(표준 루프의 plan.md/tasks[] 와 역할이 겹치지 않게). `phase`·`verify` 는 §3.4 종결에서만 커맨드가 쓴다. 진행 중 quick 대역을 벗어나면 **멈추고 로그에 적고 전체 루프로 돌린다**.
