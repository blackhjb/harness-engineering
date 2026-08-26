---
description: VERIFY phase — qa and code-reviewer run in parallel to check tests and GOAL.md success criteria; produces a PASS/FAIL verdict with evidence, FAIL spawns fix tasks via the 코디네이터
argument-hint: "[optional: specific success criteria or areas to focus on]"
---

Run the harness VERIFY phase. Focus: $ARGUMENTS

Respond in Korean.

## Preconditions
Read `.harness/state.json` and `plan.md`. If build tasks are still `pending`/`in_progress`, warn that verify will likely fail and confirm before proceeding. Set state.json `phase` = "verify".

## Step 1 — Parallel verification (qa fans out per criterion; one code-reviewer per tree)
**qa 는 SC 단위로 팬아웃한다** — one small agent per success criterion (plus one for the regression suite), all launched in a single message. Verification is embarrassingly parallel at the criterion level: each check is 3~8 minutes on its own, and stacking nine of them into one session serializes what could have finished at once (실측 2026-08-06). `code-reviewer` stays ONE per working tree — a diff review needs the whole diff.
Delegate these IN PARALLEL (single message), background 로 — 알림으로 결과를 모으고 그동안 결산 집계·장부 정리를 병행한다(20/45분 집행은 `harness-ledger` §디스패치 계약의 비동기 루프와 동일). Both RETURN structured reports and append log entries; neither edits plan.md or state.json — only the 코디네이터 (Step 3) converts findings into fix tasks.
**Multi-repo goals split by working tree, and a tree's pair starts as soon as THAT tree is frozen** — its tasks are `done` and no further commits are planned — without waiting for another tree's build. State the tree and its `git log <base>..HEAD` range in each brief; if commits later land in that tree, re-review only the delta. Review scope is per-tree, so a sibling repo still building never justifies idling (로그 2026-08-06).
**측정 승계는 원장으로 집행한다** — 조회 패턴·재실행 의무 4종은 `harness-state` §측정 원장이 정본이다(여기서 다시 적지 않는다; 한쪽만 고쳐지면 조용히 갈라진다). 검증자 고유 의무는 하나: 재측정해 **다른 값이 나오거나 결함을 실증하면 `refutes` 필드에 앞선 레코드 id 를 채워 원장에 append** — 이것이 M1(자기보고 정확도)의 유일한 입력이다. CPU 바운드 검증은 트리당 1세션.

- `qa` brief: read `.harness/GOAL.md`, `wiki/INDEX.md` (open qa + global/workflow nodes), `plan.md`, `design.md`. Check EVERY success criterion SC-n in GOAL.md and every task's 인수 조건 with an actual command, an inspection, or an audit of logged evidence per the scope rule above — none by assumption. **인수조건에 GOAL SC 표에 없는 수치를 넣을 때는 출처를 값으로 병기하고, 출처가 GOAL 의 「범위 제외」 절·배경 통계·상금표면 그 수치를 인수조건으로 쓰지 않는다** — 쓰려면 같은 턴에 ①그 집합이 라운드 간 **고정**임을 실측(2라운드 분모 값 병기) ②그 분기의 **판별력**(진입 계수 + `git grep -l … -- tests` 파일 수)을 값으로 낸다. 둘 중 하나라도 미충족이면 그것은 **기준 결함(blocks-task, 소유자 = 인수조건 작성자)**이고 verify 결과가 아니다 (2026-08-20 V-C D-1: 「multi 12/12 보존」 → 실측 분모 14/13/16 으로 12 고정 집합 부재, 지목 분기 Golden 진입 0 + 단위 테스트 0파일 → 기준 철회). **Additionally map EVERY plan.md task to exactly one of: commit sha / log result entry / explicit `deferred` with reason. One or more unmapped tasks = FAIL** — SC-level checks cannot see commit-less tasks, so "all SC met" and "a planned task never ran" can both be true (로그 참조). RETURN a table: 기준 / 검증 방법(실행한 명령) / 결과 / 증거, plus the task↔artifact map. Append full evidence (command output excerpts) to today's log.
- `code-reviewer` brief: same context. Review all code changed during this goal's build (diff against state.json `base_ref` where set) for correctness, design.md conformance, security, test adequacy. RETURN a table: 심각도(BLOCKER/MAJOR/MINOR/NIT) / 파일:라인 / 문제 / 권고. Append to today's log.

**(조건부, 트리당 1회) 이질 모델 적대적 리뷰 — code-reviewer 의 보조 입력:** 하네스 에이전트 전원이 Claude(opus 9 + fable 1)이므로 code-reviewer 는 동일 모델 계열의 공통 맹점을 자기 힘으로 볼 수 없다 — solo dev 라 다른 사람이 잡아줄 리뷰도 없다. 다음 **논리곱이 참일 때만** 사용자가 직접 `/codex:adversarial-review --background --base <state.json base_ref> -m gpt-5.6-terra` 를 실행하고 그 JSON 산출물을 code-reviewer 브리프에 첨부한다: ①diff 가 **비가역 경계**를 건드림(마이그레이션 · 삭제/덮어쓰기 · 부분 실패가 남는 배치 · 인증/권한/테넌트 격리 · PII 경로) **AND** ②`git diff --name-only <base_ref>..HEAD -- src | wc -l` ≥ 5. 하나라도 거짓이면 부르지 않는다 — 1~2파일 국소 수정과 문서·프롬프트 전용 변경에서 기대 수확은 호출 비용을 넘지 않는다. 실행 증거가 필요한 판정(red 증명 가드 · A/A 기구 검정 · p95)에는 **대체재가 아니다**: 정적 추론 리뷰는 명령도 출력도 만들지 않는다.
- **qa 팬아웃에 넣지 않는다** — qa 는 SC 1건당 1세션이라 같은 diff 를 SC 수만큼 중복 리뷰하게 되고, 산출물 형태(심각도/파일:라인/권고)는 code-reviewer 리턴 표와 동형이지 qa 의 「기준/검증 명령/결과/증거」 표와 이형이다.
- **Codex 경로(`.codex/agents/`)로 이 워크플로를 돌릴 때는 호출하지 않는다** — 리뷰어가 이미 GPT라 이질성 이점이 0 이다. 이 슬롯은 Claude 경로 전용 보완재다.
- **모델은 terra 고정 — `-m gpt-5.6-terra` 를 빼지 않는다.** 이 슬롯은 code-reviewer 의 *보조 입력*이지 판정자가 아니고(승격 바는 Step 2), 프런티어 티어를 태울 자리가 아니다. `~/.codex/config.toml` 의 전역 기본은 `gpt-5.6-sol` + `model_reasoning_effort = "ultra"` 이므로 플래그를 빼면 sol/ultra 로 돈다. **추론 강도는 이 커맨드로 낮출 수 없다** — review 경로는 `--effort` 를 파싱하지 않고(`valueOptions: ["base","scope","model","cwd"]`), `runAppServerTurn` 이 `effort: null` 로 보내 서버가 config 기본값을 쓴다. 즉 모델만 내려도 ultra 항은 남는다; 더 줄이려면 codex 전역 설정을 바꿔야 하고 그건 하네스 밖의 결정이다.
- 모델은 이 커맨드를 자동 호출할 수 없다(`disable-model-invocation: true`). 플러그인 캐시 경로(버전 포함)를 하드코딩해 `codex-companion.mjs` 를 Bash 로 직접 때리는 우회는 **금지** — 버전 승급 때 조용히 깨진다. 사용자 실행이 정본이고, 그 대기는 `--background` 로 흡수한다.

## Step 2 — Verdict
Compute the verdict yourself from both reports. Severity mapping: qa uses blocks-goal / blocks-task / minor; the reviewer uses BLOCKER / MAJOR / MINOR / NIT.
- PASS: every SC-n verified met AND zero qa blocks-goal/blocks-task findings AND zero reviewer BLOCKER findings.
- FAIL: anything else. Reviewer MAJOR findings become fix tasks and the verdict is FAIL. (qa minor and reviewer MINOR/NIT do not block PASS — list them.) Partial success is FAIL with an itemized gap list.
**외부 적대적 리뷰의 승격 바 (첨부됐을 때만 적용):** codex finding 은 정적 추론이고, 그 프롬프트 자체가 「추론에 의존하면 명시하고 confidence 를 정직하게」라고 지시받는다 — 그래서 **verdict 를 직접 움직이지 않는다.** `confidence ≥ 0.7` **AND** code-reviewer 가 그 file:line 을 자기 눈으로 재확인한 것만 BLOCKER/MAJOR 로 승격해 fix 태스크가 된다(= 「red 증명으로만 가드」·「재현 2회」와 동일한 바, 새 원리 아님). 재확인되지 않은 것은 전부 candidate wiki node 로만 남기고, **승격/기각 건수를 verdict 항목에 값으로 병기**한다(예: `외부 적대 리뷰 7건 → 승격 2 · 기각 5`). 병기 없는 첨부는 리뷰를 돌렸다는 주장만 남기고 판별력을 남기지 않는다.
Record in state.json: `verify` = {"verdict": "PASS"|"FAIL", "date": now}. Append a verdict entry with evidence summary to today's log. Exactly two verdicts exist — a PASS with caveats, named risks, or conditions does not; anything short of full PASS is FAIL.

**Goal 결산 (same verdict entry):** `git diff --shortstat <base_ref>..HEAD` + 커밋 수 + 디스패치 수, 그리고 **품질 지표 M1·M2·M5 를 측정 원장에서 계수해 값으로 기재**한다(계수식은 `harness-state` §측정 원장; 목표치는 하네스 `docs/GOAL.md`). **계수 전에 이 goal 의 디스패치 수 ↔ 원장 `d` 레코드 수를 대조해 차이(누락 에이전트·tokens 미기재)를 값으로 병기한다** — 대조 없는 M2·M5 는 분모 불명이다.

**같은 자리에서 이 goal 구간의 원장 행을 스키마로 대조해 값으로 병기한다**: ①`t` 필드 없는 행 수 ②`key` 에 `@<sha7>` 이 없는 `m` 행 수 ③`refutes` 아닌 이름으로 반증을 적은 행 수(`supersedes` 등) ④`tokens` 가 null·0 인 **위임** `d` 행 수 ⑤`agent` 표기 변형 수. 다섯 값이 전부 0 이 아니면 M1·M2·M5 는 **그 결손을 병기한 조건부 값**으로 적는다. **코디네이터 직접 집행도 `d` 레코드를 남긴다** — 없으면 승계·M1·노드 효과 계수 세 지표에서 동시에 빠진다 (로그 2026-08-26).
원장은 append-only 이므로 누락 소급 기재는 금지, 차이 병기만 한다. **외부 모델 호출(적대적 리뷰 등)은 tokens 를 원장에 기재할 수 없으므로 이 대조에서 반드시 차이로 잡힌다** — 「외부 호출 n건, tokens 미기재」로 병기하고, 그 n 을 M5 분자에 추정치로 채워 넣지 않는다(추정 tokens 를 섞으면 M5 는 측정이 아니라 의견이 된다). 원장이 비었으면 「미측정」이라 적는다 — 100% 가 아니다. M3(상류 사실 정확도)·M4(요청 충족·과잉)는 아직 수기: 반증된 상류 사실 건수와 SC 중 출처 `제안` 행 수를 세어 적는다. 결산 없는 goal 은 retro 의 채굴 루프에 보이지 않는다.
**프로덕션 순삭제 헤드라인은 `git diff --numstat <base_ref>..HEAD -- src` 의 (added−deleted) 합 한 값으로만 적고 그 명령을 병기한다** — 웨이브·커밋 구간 부분합의 deletions 총계는 헤드라인이 될 수 없고, 같은 goal 이 부착했다 원복한 계측은 base..HEAD 에서 자동 상계되므로 실적 0 이다 (실측 2026-08-20: 구간 총계 −94 보고 vs base..HEAD 실순 −24, 차액 ~70줄이 자기 부착 원복). 테스트·스크립트 델타는 별항.

**백그라운드 잔여 스캔 (same verdict entry):** verdict 를 적기 전에 이 세션이 background 로 띄운 디스패치 전건의 생존을 확인한다 — "running" 표시는 생존 증거가 아니다(세션이 유휴로 넘어가면 통지는 영원히 오지 않는다, wiki `workflow--liveness-by-notification-not-inference`). 진행 중 항목은 ①재개 메시지로 결과 회수 ②kill 후 동기 재실행 ③명시 이월(로그에 소유자·재개 방법 기재) 중 하나로 처분하고, 처분 없이 세션을 넘기지 않는다.

## Step 3 — On FAIL, route fixes
코디네이터가 직접 (the ONLY writer of plan.md and state.json `tasks[]`): for each unmet criterion, qa blocks-goal/blocks-task finding, and reviewer BLOCKER/MAJOR finding, add a fix task to plan.md (new T-NNN, owner, dependencies, acceptance criteria = the exact failed check), mirror into `tasks[]`, set phase back to "build". Point the user to `/harness:build`, then `/harness:verify` again.

## Report to the user (Korean)
Verdict up front (PASS/FAIL), criteria table, qa blocks-goal/blocks-task and reviewer BLOCKER/MAJOR findings, next step:
- PASS → `/harness:retro` (goal 마무리 회고).
- FAIL → fix-task list and `/harness:build`. If the same class of failure appears ≥2 times in the findings, or `wiki/INDEX.md` has ≥5 `(candidate)` nodes, recommend `/harness:retro` BEFORE `/harness:build`: "⚠️ 반복 실패 패턴 감지 — 수정 전에 `/harness:retro`로 위키에 등재하면 fix 작업이 같은 함정을 피합니다."
