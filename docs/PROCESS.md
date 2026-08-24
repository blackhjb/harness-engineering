# PROCESS — 하네스 사용 프로세스

## 전체 루프

```
/harness:goal ──▶ /harness:analyze ──▶ /harness:plan ──▶ /harness:build ──▶ /harness:verify ──▶ /harness:retro
   (목표)            (분석)            (기획+설계+계획)        (병렬 구현)          (검증)             (회고/자기개선)
                                        │ 사람 승인 게이트                          │ FAIL → fix 태스크 → build 반복
```

언제든 `/harness:status` 로 현재 단계·진행률·블로커 확인.
작은 작업(단일 파일 수정 등, 새 계약 없음)은 `/harness:quick` 으로 전체 루프 생략 — 에이전트 1명 디스패치.

## 단계별 상세

### 1. `/harness:goal <한 줄 목표>`
- 짧은 인터뷰(최대 5문항)로 측정 가능한 성공 기준·제약·범위 외 확정
- `.harness/` 생성, GOAL.md 작성, state.json phase="goal"
- 기존 goal이 있으면 새 iteration으로 전환 (wiki/logs는 보존)

### 2. `/harness:analyze`
- analyst가 코드베이스·데이터·연동·제약 조사 → analysis.md
- `[확인]/[추정]/[불명]` 태그로 근거 수준 구분, 막히는 unknown은 사람에게 질문

### 3. `/harness:plan`
- planner → prd.md (유저스토리·우선순위·최소 슬라이스)
- architect(+UI 작업 시 product-designer 병렬) → design.md (계약·데이터모델·UX 상태 인벤토리)
- 코디네이터 → plan.md (태스크 표: 담당 에이전트/의존성/수용 기준/웨이브)
- **사람 승인 후에만 build 가능** (state.json approvals)

### 4. `/harness:build`
- 코디네이터가 의존성 없는 태스크를 담당 에이전트에게 **병렬 디스패치**
- 각 개발 에이전트: wiki INDEX + 자기 scope 노드 필독 → TDD 구현 → 수용 기준 충족 → logs/ 기록 → 배운 점을 위키 노드로 적재(생성/강화/승격)
- 설계 공백 발견 시 즉시 architect에게 보고 (무단 변경 금지)

### 5. `/harness:verify`
- qa + code-reviewer 병렬 실행
- qa: GOAL 성공 기준 대비 동작 검증 (PASS/FAIL + 증거)
- code-reviewer: diff 리뷰 (BLOCKER/MAJOR → CHANGES_REQUESTED)
- FAIL이면 fix 태스크 생성 → build로 복귀. "조건부 통과" 없음

### 6. `/harness:retro`
- harness-improver가 logs/ + candidate 노드 마이닝 → 실패 패턴 클러스터링
- 산출: 위키 큐레이션(승격/병합/은퇴 — 자동 적용) + 프롬프트/게이트 수정안(diff 단위 사람 승인)
- 이것이 하네스를 쓸수록 똑똑해지게 만드는 루프

## 실전 예시 (첫 세션)

```
/harness:goal 아침 브리핑에 사람별 wiki 링크를 붙여 개인 멘션으로 전송
→ 인터뷰 답변 → GOAL.md 확정
/harness:analyze   # hermes-worker 구조·Chat API 제약 분석
/harness:plan      # PRD·설계·태스크 승인
/harness:build     # ai-agent-dev + qa 병렬 작업
/harness:verify    # dry-run + 골든 픽스처 검증
/harness:retro     # "Chat API 멘션은 space 멤버만 가능" → wiki 노드 등재
```

## 규율 (짧은 버전)

- 파일이 진실이다: 채팅에만 있는 결정은 없는 결정
- 질문은 핵심 분기점에서만: 선택지+추천안+트레이드오프로 묻고, 답은 기록해 다시 묻지 않는다
- 게이트는 우회하지 않는다: 승인 없는 build, 증거 없는 done 금지
- 실패는 자산이다: 실패 로그를 지우지 말고 retro로 보낸다
- 사람은 스택 위로: 매 단계 실행이 아니라 승인 지점에서 개입
