# 지침 정합성 검사기 `tools/check-canon.py` — 설계와 실측

> 계기: v1.19.0 전수 정독 감사가 모순 4건·드리프트 14곳을 찾았다. **그 감사를 사람이 해야 했다는 것이 결함이다.**
> 회고는 로그(사건)에서 채굴하는데, 「지침 두 곳이 반대로 말한다」는 사건으로 나타나지 않는다 — 에이전트는 둘 중 하나를 따르고 정상 종료한다.
> 승계 grep 이 v1.18.2 부터 v1.19.0 까지 죽어 있었던 것이 그 증거다.

## 0. 설계 원리

**① 낱말이 아니라 「해석 가능한 참조」를 검사한다.**
`grep orchestrator` 는 ARCHITECTURE 의 은퇴 기록(정당한 역사 서술)을 오탐한다. 대신 백틱 포인터(`` `skill` ``·`` `agents/x.md` ``·`§섹션`)만 뽑아 **실재하는지 해석**한다. 실측: 낱말 검색 4건 전부 오탐 · 참조 해석 오탐 0.

**② 모순을 찾지 말고, 중복을 금지한다.**
자연어 모순은 grep 으로 검출 불가다. 그래서 문제를 뒤집는다 — **정본을 선언하고 「정본 밖에서 값으로 다시 쓰였는가」를 잡는다.** 중복이 0이면 모순은 발생할 수 없다. 이것이 v1.19.0 이 각 사안을 「정본 1곳 + 나머지는 포인터」로 바꾼 것의 기계적 집행이다.

**③ 검사기 자신도 red 증명을 가진다.**
하네스 규칙 「가드는 red 증명으로만」은 검사기에도 적용된다. `--against <sha>` 로 **v1.19.0 이전 트리(68ff0ef)에 돌려 알려진 결함을 여전히 잡는지** 확인한다. 실패하면 검사기가 퇴화한 것이다.

## 1. Tier 1 — 파생 검사 (설정 불필요, 트리에서 사실을 유도)

| ID | 검사 | 기대값의 출처 | 68ff0ef red |
|----|------|---------------|-------------|
| `VERSION` | `plugin.json.version` == `marketplace.json.plugins[0].version` | 상호 | **✓ 1.18.3 vs 1.12.0 검출** |
| `ROSTER` | description 의 `N role agents`·`N workflow commands`·`N skills` == 실제 파일 수 | 파일 수 | **✓ `12 role agents` vs 실제 10 검출** |
| `MIRROR` | `sync-codex.sh` 재생성 후 `git diff --exit-code` 청결 | 생성기 | (현재 CLEAN) |
| `DANGLING` | 백틱 포인터가 실재하는 스킬·에이전트·파일·§섹션을 가리키는가 | 트리 | 현재·이전 모두 0 |
| `SELFREF` | 스킬 파일이 자기 이름을 스킬 포인터로 씀 (= 자기 §섹션을 가리켜야 함) | 파일명 | **✓ harness-ledger 2건 검출** |
| `PORTABILITY` | 범용 프롬프트에 프로젝트 고유 `*.py:NNN`·사건 서사 초과 | 정규식 | **✓ qa 1 + analyst 2 검출** |
| `BUDGET` | 역할별 읽기 조합 단어수 vs 상한 | `budget.yaml` 조합표 | (측정·보고만, FAIL 아님) |

**Tier 1 은 v1.19.0 이 고친 15건 중 7건을 잡는다.** 설정 파일 없이, 오탐 0으로.

## 2. Tier 2 — 정본 레지스트리 (`tools/canon.yaml`)

Tier 1 이 못 잡는 8건(스킬 오지정 4 + 모순 4)은 **규칙의 정체**를 알아야 판정된다. 선언한다:

```yaml
- id: ledger-succession-grep
  정본: skills/harness-state/SKILL.md#측정 원장
  값: "grep -F '<명령>@<sha7>@<env>'"
  금지: '"key":"'                       # 반대형 — 트리 어디에도 없어야 한다
  포인터_허용: [commands/verify.md, skills/harness-ledger/SKILL.md]
  범위: plugins          # 금지 검사를 배포 프롬프트로 한정 (레포 자체 문서 제외)

- id: rerun-obligations
  정본: skills/harness-state/SKILL.md#측정 원장
  값: "재실행 의무는 넷"
  금지: "재실행 의무는 (셋|둘|다섯)"

- id: harness-edit-approval
  정본: agents/harness-improver.md#Boundaries
  값: "전건 사용자 승인"
  금지: "(저위험).{0,20}자동 적용"

- id: model-tiering
  정본: FRONTMATTER                     # 특수값: agents/*.md 의 model: 이 정본
  금지: "(설계·분석|빌드·검증)\\s*=\\s*(fable|opus|sonnet)"
```

항목당 3개 단언:
- **(a) 정본 실재** — `값` 이 선언 위치에 있는가. **없으면 정본이 증발한 것** ← v1.18.2 가 설명만 고치고 코드블록을 놓친 그 사건을 잡는 항.
- **(b) 반대형 부재** — `금지` 패턴이 트리 어디에도 없는가. ← 승계 grep 버그를 잡는 항. 가장 싸고 가장 정밀하다.
- **(c) 단일 정본** — `값` 이 정본 밖 파일에 나타나면 위반. `포인터_허용` 은 **슬러그 언급만** 허용하고 값 재서술은 금지한다.

## 2-b. 구현 결과 (2026-08-25 실측)

```
python3 tools/check-canon.py                  → PASS  위반 0 · 경고 13   exit 0
python3 tools/check-canon.py --against 68ff0ef → FAIL  위반 14 · 경고 16  exit 0
python3 tools/check-canon.py --against HEAD    →                          exit 1  (검사기 퇴화 신호)
```

**68ff0ef(v1.19.0 직전)에서 검출한 14건** — v1.19.0 이 사람 정독으로 고친 것들이다:

| 검사 | 건수 | 내용 |
|------|-----|------|
| `CANON/succession-grep-pattern` | 3 | **정본에서 값 증발** + 반대형 2곳(harness-state:134 · verify.md:17) |
| `CANON/rerun-obligations` | 1 | verify.md 「재실행 의무는 셋」 |
| `CANON/harness-edit-approval` | 1 | retro.md 「저위험 … 자동 적용」 |
| `CANON/portability-project-slugs` | 2 | analyst · qa |
| `PORTABILITY` | 3 | `candidate_matching.py:189` · `faq_handler.py:99` · `eval_golden_app_dev_parallel.py:1304` |
| `SELFREF` | 2 | harness-ledger:74 · :114 자기참조 |
| `ROSTER` | 1 | marketplace.json `12 role agents` vs 실제 10 |
| `VERSION` | 1 | marketplace 1.12.0 vs plugin 1.18.3 |

가장 중요한 항: **승계 grep 을 세 방향으로 잡는다** — 정본에 값이 없음(a) + 반대형 존재(b) 두 단언이 동시에 발화한다. v1.18.2 가 설명만 고치고 코드블록을 놓쳤을 때 (a)가, verify.md 가 틀린 쪽을 복제했을 때 (b)가 걸린다.

### 구현 중 발견 — 읽기 예산이 로케일 의존 측정이었다

같은 `qa.md` 를 `LC_ALL=en_US.UTF-8 wc -w` 는 **665단어**, `LC_ALL=C wc -w`(= python `.split()`)는 **583단어**로 센다. UTF-8 로케일의 `wc` 가 CJK 구두점(`·` `—` `「」`)에서도 쪼개기 때문이다.

기존에 보고된 수치(harness-state 2,557→2,149 등)는 전부 UTF-8 쪽이다. **같은 명령·같은 파일인데 환경이 다르면 값이 다르다** — 원장 키에 `<env>` 를 결박한 것과 정확히 같은 결함이다. 검사기는 결정적인 공백 분할로 고정했으므로 출력값이 과거 보고보다 ~12% 낮다.

→ **3,500 상한은 어느 단위인가를 사용자가 결정해야 한다.** v1.19.0 이 이미 「목표치 재설정은 사용자 결정」으로 남긴 항목이고, 그래서 `BUDGET` 은 WARN 이지 FAIL 이 아니다.

## 3. 정직한 한계

**이 검사기는 새 모순을 발견하지 못한다.** 선언한 것만 지킨다.
그러므로 이것은 탐지기가 아니라 **회귀 가드**다 — 「한 번 발견한 모순은 두 번 다시 못 들어온다」. 테스트 스위트와 같은 성격이고, 같은 규율이 필요하다: **회고가 새 모순을 찾으면 그 자리에서 레지스트리 항목을 추가**한다(버그 수정에 회귀 테스트를 붙이는 것과 동일).

전수 정독은 여전히 주기적으로 필요하다. 다만 매번 **같은 것을 다시 찾지는 않게** 된다.

## 4. 집행 지점 — 장치화

지금 `retro.md` 의 「적용 완료 4단계」(편집 · 범프 · 커밋 · 캐시동기) **앞에 ⓪을 넣는다**:

```
⓪ tools/check-canon.py 통과 (PASS)  ← 신설
① plugins/harness/ 소스 편집
② plugin.json version 범프
③ 소스 커밋 1건
④ 런타임 캐시 동기 diff 전건 IDENTICAL
```

보고에 값으로 적는다: `정합성 <n>검사 PASS` · `범프 <구>→<신>` · `커밋 <sha7>` · `동기 <n>/<n> IDENTICAL`.

「⓪ 없이 ①~④ 를 한 수정은 적용이 아니다」 — 4단계 규칙과 같은 형태의 **장치**(판단이 아니라 값)로 만든다.

**정밀도 교훈 — `값` 은 distinctive 해야 한다.** 초안의 `harness-edit-approval` 은 값을 「사용자 승인」으로 잡아 retro.md 의 정당한 포인터 문장을 오탐했다. 세 곳의 서술이 이미 일치하므로 실제 가드는 반대형 금지 하나다 → `종류: 금지` 로 내렸다. **짧고 흔한 문자열을 정본 값으로 쓰지 않는다.**

## 5. 구현 제약

- python3 stdlib 전용, 의존성 0 (`sync-codex.sh` 와 동일 규율 — 지루한 기술·최소 가동부)
- 단일 파일 `tools/check-canon.py` + 설정 `tools/canon.yaml`
- 출력 = 값: 위반 표(검사 / 파일:라인 / 기대 / 실제) + `exit 0|1`
- `--against <sha>` = 자기 대조 모드(격리 worktree 사용 후 제거; 파괴적 git 금지 준수)
