---
description: BUILD phase — 코디네이터 executes plan.md, dispatching independent tasks to owner agents in parallel, updating state.json and logs until all tasks meet acceptance criteria
argument-hint: "[optional: specific task IDs to run, e.g. T-003 T-004]"
---

Run the harness BUILD phase. Optional task filter: $ARGUMENTS

Respond in Korean.

## Preconditions (hard gate)
Read `.harness/state.json`. Both `approvals.design` and `approvals.plan` must be true — if not, stop and point the user to `/harness:plan` approval. Do not offer to bypass this.

## Execution
Set state.json `phase` = "build".
**병렬/직렬의 유일한 축은 쓰기 트리 공유다.** Write tasks in the SAME working tree are serial — group them into one session that does them in order and commits per task (separate dispatches buy nothing there and each costs a round trip plus a cold context). Write groups in DIFFERENT trees, and every read-only check, run in parallel in one message. Nothing else — not phase, not repo, not "conceptually separate" — justifies serializing.
세션 기본 추론 강도가 높을수록 **호출 1건이 길어진다** — 그 설정에서 빨라지는 유일한 수단은 호출을 **적게·작게** 하는 것이다. 아래 두 값이 그 수단이다.
**브리프 상한 — 값이다**: 디스패치 1건 = 인수조건 **≤8** · 브리프 **≤20줄**. 초과하면 디스패치하지 말고 태스크를 쪼갠다. (실측: 인수조건 45개 세션 50분 vs 축 적은 세션 7~15분.) **인수조건은 GOAL 의 SC·비협상 제약을 면제할 수 없다 — 기계 검사**: 「불요 · 재증명하지 · 생략 · 건너뛴다 · 면제」가 **GOAL 의 SC·제약을 목적어로** 나타나면 그 브리프는 디스패치 금지다. GOAL 을 먼저 개정해 그 커밋 sha 를 인수조건에 인용하거나, 그 항을 지운다(지우면 GOAL 원문이 기본값). 예외는 원장 승계 규칙 하나이며 그때는 면제 대상이 SC 가 아니라 재실행이고 `key` 를 인용한다. (실측 2026-08-25 iter43 T-002 ⑥ → 가드 4건 무판정 삭제 → `a1995c0` 원복, −98줄 소멸.)
**산출 계약도 값이다**: 브리프에 반환 보고 줄 상한·증거 파일 경로를 지정한다 — 미지정이면 `harness-state` §Context budget 8(보고 ≤40줄 · 로그 result ≤20줄 · `d.tokens` 250k 트립)이 계약이다. 코디네이터도 면제되지 않는다: 실행 중 에이전트로 보내는 추가 지시(SendMessage)는 1회 **≤20줄**, 이 상한을 넘는 정정은 지시가 아니라 재브리프다.
**모델 티어링**: 정본은 **`agents/*.md` frontmatter 의 `model:` 하나뿐이다** — 문서·커맨드·기억의 서술은 정본이 아니다. 오버라이드 규칙과 집행은 `harness-ledger` §Dispatch economy.
**특화 스킬 지정 — 유연한 판별 + 선택의 강제 (사용자 정책 2026-08-18)**: 정본은 GOAL 1-B 의 「표면 → 스킬」 표와 design §9. 디스패치마다 **이 태스크가 실제로 만지는 표면**으로 스킬을 정해 브리프에 slug 지정한다 — 태스크 표면이 goal 판별과 다르면(예: Python goal 안의 프롬프트 태스크 → `ai-agent-dev`) **그 태스크만 오버라이드**하고 사유 1줄을 브리프에 남긴다. 들어맞는 스킬이 없으면 「특화 스킬 없음 — 범용 진행」 명기. **§9/1-B 가 비어 있으면 디스패치 금지 — 먼저 채운다.** 무지정(중립) 브리프 금지.
**메인 직접 대역**: 변경 **≤3파일 · ≤40줄 · 판정 0건 · 역편집 복구 가능**이면 코디네이터가 직접 고치고 디스패치하지 않는다 — 대신 그 diff 의 PASS 는 스스로 내지 않는다(reviewer 또는 qa 1인 필수).
**디스패치 프롬프트에 위키·스킬 내용을 재서술하지 않는다**: point the agent at `wiki/INDEX.md` + its own scope and give it the task's criteria. Pasting the rules in yourself bypasses the recall path the wiki exists for — the knowledge stops being retrievable and becomes your copy-paste (2026-08-06: recorded lessons never reached the agents that needed them for exactly this reason).
**가드·lint·측정 스크립트를 신설·수정하는 태스크의 브리프에는 qa scope 의 측정 규율 노드(양성 대조 red 선실증 · 축별 주입)를 slug 로 지정 포함한다** — 내용 재서술 금지, 지정만. 이 규율의 위반 생산자는 검증자가 아니라 빌더인데 qa 노드는 빌더의 기본 읽기 세트 밖이다 (실측 2026-08-07·08-14: 지정 태스크 무결, 미지정 태스크 3건에서 가드 무탐·red 1축 과대 보고로 rework). 판별은 인수조건에 test/lint 파일 신설·수정이 있는지로 한다.

**성과의 정의 — 브리프에 값으로 박는다 (사용자 정책 2026-08-20).** 삭제형·구조형 goal 의 헤드라인은 **프로덕션 순삭제 줄수 + 분기 델타**다. 다음 셋은 성과가 아니므로 목표치·헤드라인으로 쓰지 말고, 브리프에 금지로 명시한다: ①**계측기·게이트·측정 인프라 신설** — 그건 비용이고, 소비(삭제)가 같은 배치에 없으면 빚만 남는다 ②**테스트 파일·테스트 줄수 삭제** — 언제든 지울 수 있어 진척을 나타내지 않는다(prod/test 분리 보고 필수) ③**이관·개명·재수출** — 위치만 바뀐다. 판정 질문: 이 커밋이 `src/` 프로덕션 줄수와 분기 계수를 줄였는가.

**Ablation 우선 — 계측은 ablation 이 불가능할 때만 (사용자 정책 2026-08-20).** 「죽은 것 같은 코드」의 기본 처분은 **지우고 정답률로 판정**이다. 계측→수집→판정→삭제 4단계는 ablation 이 구조적으로 불가능한 경우(외부 상태 의존·측정 자체가 목적)에만 쓴다. 계측 경로를 택하면 **왜 ablation 이 불가능한지 1줄**을 브리프에 남긴다 — 남기지 못하면 ablation 으로 간다. (실측 2026-08-19~20: 계측 전담 iteration 이 게이트 20종을 낳고 상수 2~12종 처분에 그쳐 원복으로 닫혔다.)

**선언과 디스패치는 같은 턴이다.** 「다음은 X 를 디스패치한다」를 사용자에게 보고했으면 **그 턴 안에서 실제로 Agent 를 호출**한다. 보고만 하고 턴을 끝내면 루프가 조용히 정지한다 — 웨이브 착지 처리는 「장부 갱신 → **디스패치**」를 한 턴에 붙여서 하고, 디스패치 없이 턴을 닫을 때는 정지 조건 4종 중 어느 것인지 로그에 남긴다. (실측 2026-08-19: 선언 후 미호출로 19시간 유휴.)

**장수 측정의 수확 주체는 코디네이터다.** 측정 에이전트가 Golden·벤치를 백그라운드로 띄우고 세션을 끝내면 프로세스는 살아도(nohup·PPID 1) **결과를 수확할 주체가 사라진다**. 측정 디스패치 브리프에는 「이 세션 안에서 완주」를 요구하고, 그래도 조기 종료하면 코디네이터가 러너 종료를 기다려 직접 수확한다(추가 디스패치 금지 — 왕복만 늘어난다).

**디스패처는 코디네이터 1인이다** — 대형 웨이브도 코디네이터가 `harness-ledger` §디스패치 계약을 그대로 집행한다.
**한 트리의 디스패처는 항상 1인이다** — 실행 중인 장수명 에이전트에 시간 민감한 계획 변경을 메시지로 보내지 않는다(다음 툴 라운드까지 미배달; 기전·실측은 wiki `workflow--liveness-by-notification-not-inference`).
**웨이브 비용 감지 — 웨이브 종료마다 로그에 1줄.** 이 1줄 없이는 다음 웨이브를 열지 않는다(WAVE GATE 항목).

| 값 | 명령·정의 | 판정 |
|---|---|---|
| 누적 디스패치 수 | 이 goal 에서 지금까지 띄운 건수 | — |
| 변경 소스 파일 수 | `git diff --shortstat <base_ref>..HEAD` 에서 **테스트·픽스처·문서 제외** — 회귀 가드를 성실히 쓸수록 분모가 부풀어 초과가 가려진다 | — |
| **초과 여부** | 디스패치 수 **>** 변경 소스 파일 수 | 참이면 세리머니가 변경을 추월했다 |
| 실패·재디스패치분 | 모델 한도·무성 정지·브리프 결함 기인 재측정을 **분리 계상** | 실패는 분자에만 남고 분모를 늘리지 않는다 |

**초과가 참이면 그 턴에** ①남은 세리머니를 실제로 잘라내거나 ②goal 을 축소 종결하거나 ③사용자에게 표적 교체를 제안한다 — 셋 중 하나를 로그에 값으로 적는다. **절단 대상을 고르기 전에 초과분을 분해한다**: 분해 없이 자르면 실패의 벌을 멀쩡한 검증 단계가 받는다(2026-08-20: 초과분 3 = 한도 2 + 정지 1 이었는데 verify 의 SC 팬아웃을 7→2 로 축약했다). **검증 엄격도는 절단 대상이 아니다** — 실패분이 초과를 설명하면 세리머니가 아니라 실패를 보고한다. verify 의 결산을 기다리는 것은 늦다; 사용자가 탐지자가 되어서는 안 된다. **감지만 하고 계속 도는 것은 위반이다**(실측 2026-08-20: 디스패치 11 > 변경 소스 9 로 트리거를 충족했는데 비용 줄이 1회만 기록돼 루프가 그대로 진행됐다).
같은 1줄에 **장부 대조 2값**을 붙인다: ①`plan.md` 상태열과 `state.json tasks[]` 의 **불일치 행 수**(0 이 아니면 다음 웨이브 전에 둘 다 고친다) ②**누적 디스패치 수 − 원장 `d` 행 수**(0 이 아니면 그 차이가 코디네이터 직접 집행분이므로 그 구간 `d` 1행을 그 턴에 append). 웨이브 게이트는 매 웨이브 도므로 이 두 값은 **verify 가 아니라 build 중에** stale 을 잡는다(2026-08-27 iter52: 7/7 행 stale 이 goal 내내 지속돼 verify 에서 blocks-goal 로 검출).
**코디네이터 상시 책무**: ①`wiki/INDEX.md` + 해당 scope 노드 읽기 ②태스크↔산출물 사상 장부 유지 ③증거 없는 done 금지(값으로만 판정) — `harness-ledger` §디스패치 계약이 정본.
**실행 형태**: 10분+ 디스패치는 `harness-ledger` §디스패치 계약의 「비동기 루프」 그대로 — background + 알림 전진 + 병행 작업 + 20/45분 집행. 동기 대기는 10분 미만 단건에만.

코디네이터는 plan.md 를 웨이브 단위로 연속 집행한다 — 한 웨이브 종료는 정지점이 아니다(정지 조건 4종·디스패치 계약·재시도 정책은 `harness-ledger` §디스패치 계약). `done` 은 인수 조건 충족 증거가 오늘 로그에 있을 때만.

## Report to the user (Korean)
완료/실패/차단 task counts with IDs, key artifacts (file paths), open escalations needing a decision, next step — `/harness:verify` when all tasks are done, or the specific unblock action. Do not declare the goal met here; only verify can.

## Retro nudge (always evaluate)
Count `(candidate)` lines in `.harness/wiki/INDEX.md`. If ≥5 candidate nodes, OR any `failure` event was logged during this build (including failures recovered by retry), OR a human escalation occurred, append to the report: "⚠️ 학습 루프 권장: 위키에 candidate 노드 N건 — 다음 build 전에 `/harness:retro` 실행을 권장합니다 (같은 실수 반복 방지)." One line only; do not run retro automatically.
