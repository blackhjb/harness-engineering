---
description: Set or reset the harness goal — brief interview, then scaffold .harness/ and write GOAL.md with measurable success criteria
argument-hint: "<one-line goal>"
---

사용자가 하네스 goal 을 설정하려 한다: $ARGUMENTS

한국어로 응답하고 모든 `.harness/` 파일을 한국어로 쓴다(코드 식별자·경로·기술 용어는 원문). 문서 스캐폴드는 `harness-ledger` 스킬의 정본 섹션 목록에서 직접 생성한다.

## 1. 인터뷰 (한 메시지, 짧게)
한 메시지로 묻는다. **quick 후보면 2문항만**(성공 기준 · 범위 제외); 표준 루프면 최대 4문항(+ 제약 · 기한). 이미 "$ARGUMENTS" 가 답한 것은 묻지 않는다. 성공 기준이 모호하게 오면 측정 가능하게 한 번 재진술하고("이렇게 바꾸면 측정 가능합니다: ... 맞습니까?") 확인 후 진행한다.

**SC 표 확정 체크리스트 — 행마다 5축 전부.** 범위 팽창과 vacuous SC 는 실행이 아니라 이 표를 쓰는 순간 태어난다 (로그 2026-08-07):
1. **측정** — 검증 가능한 값("p95 < 200ms"), 느낌 금지.
2. **수정 전 거짓** — 참이면 vacuous; 인용한 로그 레벨·문자열·상수는 원문 줄을 열어 확인. grep·명령 1회로 1분 안에 확인되면 **지금 돌린다** — "수정 전 red 실측을 태스크에 포함" 유예는 확인이 실제로 비쌀 때만.
3. **경로 식별** — 같은 값이 다른 경로로도 나올 수 있으면 경로 식별 증거를 함께 적는다.
4. **출처** — 행마다 한 단어: `사용자` / `파생`(사용자 SC 달성에 필연) / `제안`(내 판단). `제안` 이 1건이라도 있으면 착수 전에 그 행만 사용자에게 별도 확인한다 — 검증 요청에 리팩터 SC 를 얹는 것이 최대 비용 경로다.
5. **달성 가능성** — §범위 제외와 나란히 읽는다. 제외된 수단 없이는 도달 불가한 SC 는 모순: 목표치를 「판정·사유 등록으로 닫는다」로 낮추거나 그 제외를 푼다.

## 2. 규모 분류 (규모 비례 라우팅 — 생략 금지)
**먼저 `.harness/wiki/INDEX.md` 를 열고 `cost`/`workflow`/`global` 노드를 읽는다** — 아래 임계값은 그 노드가 이기는 기본값이다.
스캐폴드 **전에** 규모를 분류한다. **변경 표면은 grep 실측이 선행 — 문서 추론만으로 라우팅 금지**: 실제로 바뀌는 파일(상수·라우트·컴포넌트)을 찾아 세고, 그 수를 라우팅과 함께 GOAL.md 승인 섹션에 적되 `change-surface`(바뀔 파일)인지 `read-surface`(읽을 파일)인지 **한 단어로 병기**한다. 감사·검증형 goal 은 바뀔 파일을 미리 알 수 없어 read-surface 를 세기 쉽다 — read-surface 는 곧 「규모 미상」이므로 아래 판단-불가 규칙을 탄다. 세리머니는 목표의 중요도가 아니라 실측된 변경 크기에 비례한다.

- **quick 경로** — 전건 충족: **호환성을 깨는 계약 변경 없음** · 아키텍처 결정 0(새 모듈 경계·기술 선택 없음) · 실측 diff 가 국소적·기계적(가드, re-export, 테스트 수정, config/문서 — 대략 ≤8파일 / ≤150줄) · SC 전건이 명령으로 판정 가능.
  - breaking = 필드 제거·rename·타입/의미 변경·필수 요청 필드/인자 추가. **추가형**(새 응답 필드 · 기본값 있는 kwarg · 구 소비자가 무시하는 enum 값)은 quick 을 탈락시키지 않는다 — 어느 쪽인지 구 소비자 동작 근거와 함께 1줄로 명시.
  → §4 대로 스캐폴드하되 analysis/prd/design/plan 은 만들지 않고, 라우팅 + 1줄 근거를 GOAL.md 승인 섹션과 일간 로그에 기록한 뒤 `/harness:analyze` 대신 `/harness:quick`(한 배치, 또는 SC 클러스터당 1회)으로 넘긴다. **검증 엄격도는 경감되지 않는다.**
- **표준 루프** — 그 외 전부, 또는 오판이 비쌀 만한 의심이 있으면 → `/harness:analyze`.
- **판단 불가** — `/harness:analyze` 를 먼저 돌린다. 그 analyze 는 **규모를 재는 패스**이지 증명하는 패스가 아니다(analyze 커맨드의 질문 크기 상한 적용); analysis.md 권고가 경로(quick vs plan)를 명시하고 그대로 진행한다.

임계값(≤8파일/≤150줄)은 retro 가 조정하는 기본값이다 — 프로젝트에 `cost` scope 위키 노드가 있으면 그것이 이긴다. 선택한 경로와 근거를 §5 확인 메시지에 밝힌다.

**문안 확정 게이트**: 산출물이 사용자 눈에 보이는 문자열(문구·라벨·에러·화면 상태)을 포함하면, 착수 전에 **리터럴 3안 이내로 1회 확정**받고 그 문안을 GOAL.md 목표치 칸(또는 design.md §8)에 그 턴에 적는다. 미기재 문안으로는 디스패치하지 않는다 — 문구는 취향이라 착수 후 바뀌면 배선까지 되돌아간다 (로그 참조).

## 2-B. 사실 명제에는 근거를 붙인다 (재작업의 최대 원인)
GOAL 배경·전제의 **사실 명제**(도입 시점·인과 순서·부재 주장·값의 형태·직전 iteration 의 결론)는 각각 `file:line`·커밋 sha·명령 출력 중 하나를 같은 줄에 병기한다. 근거를 댈 수 없으면 `[미검증]` 으로 표시하고 analyze 의 확인 대상으로 넘긴다. 직전 iteration 의 verify 로그·사용자 보고를 그대로 승격하는 것이 가장 흔한 오염 경로다 (로그 참조).

## 3. 기존 .harness/ 처리
- **위키 상한 위반이면 새 goal 전에 `/harness:retro` 먼저** (candidate ≤15, active ≤8 per scope, INDEX ≤80줄) — 큐레이션은 다음 goal 의 선행 조건이다 (로그 참조).
- **장부가 실제와 어긋나면 먼저 맞춘다**: 마지막 verdict 이후 코드가 바뀌었는데 state.json 이 여전히 `done`/PASS 면 그 후속 작업은 미등록 iteration 이다 — `iteration` 증가 + `verify` 리셋으로 등록부터.
- `.harness/` 없음: 아래 전체 구조 생성.
- `.harness/` 있음: 새 goal iteration. `wiki/`·`retro/`·`logs/` 는 보존(축적 학습; legacy `playbook.md`/`retro/inbox.md` 도 보존 — 다음 retro 가 이관). 구 state.json 을 읽어 `iteration` 증가, GOAL/analysis/prd/design/plan 은 새 스캐폴드로 덮는다. 직전 goal 의 phase 가 `done`/`retro` 가 아니면 미완임을 경고하고 명시 확인 후 덮는다.

## 4. 파일 생성 (`harness-ledger` 스킬의 정본 섹션 목록에서)
모든 섹션 존재, 빈 섹션은 "해당 없음".
- `GOAL.md` — 인터뷰 내용으로 채움.
- `analysis.md`·`prd.md`·`design.md`·`plan.md` — **표준 루프만** 생성(헤더만). **quick 경로는 이 4개를 만들지 않는다** — quick 의 장부는 GOAL.md + state.json + 로그다.
- `state.json` — 스킬 스키마대로: `goal_id` = `<yyyymmdd>-<short-slug>`, `base_ref` = `git rev-parse HEAD`(git 아니면 null), `phase` = "goal", `iteration`(1 또는 증가), `updated_at` = now, `approvals` 전부 false, `verify` = {"verdict": null, "date": null}, `tasks` = [].
- `wiki/INDEX.md` — 없을 때만 헤더 + 형식 주석으로 생성; 기존 위키는 절대 덮지 않는다.
- `retro/`·`logs/` — 없으면 생성.
- 오늘 일간 로그에 goal-set 항목 append (누가, 무슨 goal, iteration).

## 5. 확인과 핸드오프
사용자에게 한국어로: 성공 기준 표 · 제약 · 범위 제외 · §2 라우팅 결정과 근거를 보여주고 GOAL.md 확정 또는 수정 요청을 받는다. 확정되면 다음 단계는 라우팅된 커맨드다 — quick 경로면 `/harness:quick`, 아니면 `/harness:analyze`. **라우팅이 사용자에게 수동 단계를 추가해서는 안 된다**: 자율 진행 권한("알아서 진행")이 있으면 코디네이터가 같은 세션에서 라우팅된 커맨드를 직접 호출한다.

## Question rules
질문은 `co-creation` 스킬을 따른다; 기록된 결정은 재질의하지 않는다. 예외 — 최초 인터뷰는 기본 사실(기한, 제약 등)을 짧은 개방형으로 물어도 된다.
