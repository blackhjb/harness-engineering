---
name: testing-qa
description: Cross-stack verification playbook — deriving test cases from acceptance criteria, test matrix and defect report templates, evidence format for .harness/logs/, per-stack commands (Gradle/pytest/npm), flaky-test policy, and dry-run vs full-integration guidance. Use for ANY verification, test-writing, test-design, or QA work in the harness.
---
# Testing & QA Playbook

A claim without evidence is an opinion; a verdict without a matrix is a guess.

## 1. Deriving test cases from acceptance criteria

For EACH acceptance criterion in plan.md (and each touched success criterion in GOAL.md):

1. **Restate as an observable outcome.** "API works" is not testable; "POST /api/v1/orders with valid body returns 201 and the order is retrievable by the Location header" is. Not restatable observably → the criterion is defective; file a plan defect before testing.
2. **Extract the variables** — inputs, states, environments it depends on (payload fields, auth state, existing data, dependency availability).
3. **Enumerate per variable**: valid, boundaries (0, 1, max, max+1, empty string, null, unicode/emoji, very long), invalid type, missing.
4. **Add failure injection**: dependency down/slow/timeout, duplicate submission (idempotency), concurrent execution, partially-written prior state.
5. **Add regression**: what shares code paths? Minimum: full existing suite; risky changes: re-exercise neighboring endpoints manually.

Rule of thumb: one criterion → 1-2 happy, 3-6 edge, 1-3 failure cases. A happy-path-only matrix means design isn't done.

## 2. Test matrix template (paste into the verification log)

```markdown
## 테스트 매트릭스 — <task-id>: <task title>
| # | 유형 | 케이스 | 입력/조건 | 기대 결과 (근거: design.md/plan.md 인용) | 결과 | 증거 |
|---|------|--------|-----------|------------------------------------------|------|------|
| 1 | happy | 정상 주문 생성 | 유효 payload | 201 + Location 헤더 | PASS | cmd#3 |
| 2 | edge | quantity=0 | 경계값 | 400, errors[].field=quantity | PASS | cmd#4 |
| 3 | failure | DB 커넥션 차단 | 컨테이너 중지 | 503 ProblemDetail, 재시도 후 복구 | FAIL | cmd#7 |
| 4 | regression | 기존 조회 API | 전체 스위트 | 전부 green | PASS | cmd#1 |
```

Types: `happy` / `edge` / `failure` / `regression`. Every row's expected result cites its source.

## 3. Commands per stack (run these, paste real output)

**Java / Spring Boot (Gradle)**
```bash
./gradlew test                                   # full suite — always the baseline
./gradlew test --tests 'OrderServiceTest'        # focused repro
./gradlew build                                  # when config/deps/build files changed
./gradlew test --rerun-tasks                     # bypass cached results when suspicious
```
Reports: `build/reports/tests/test/index.html`, `build/test-results/test/*.xml`.

**Python worker (uv)**
```bash
uv run pytest -q                                 # full suite
uv run pytest -q tests/test_worker.py -k "retry" # focused
uv run pytest -q -x --lf                         # rerun last failures, stop at first
uv run ruff check . && uv run ruff format --check .   # lint gate
uv run pytest -q -m dry_run                      # dry-run fixture suite (no external calls)
```

**Node (if present)**
```bash
npm test -- --run                                # CI mode, no watch
npm run lint
```

**Behavioral checks against a running app**
```bash
curl -si -X POST localhost:8080/api/v1/orders -H 'Content-Type: application/json' -d @case2.json
```
Capture full status line + body. A 200 with the wrong body is a FAIL.

## 4. Verification evidence format for .harness/logs/

Append to today's daily log `.harness/logs/YYYY-MM-DD.md` under the header `## HH:MM [qa] verify`, in Korean. Required content:

```markdown
### 검증 — <task-id>
- 일시 / 검증자: qa
- 대상 커밋: <git rev-parse --short HEAD>
- 참조: plan.md <task-id> 수용 기준, GOAL.md 성공 기준 <n번>

#### 실행한 명령 (번호 붙여 참조)
cmd#1: ./gradlew test
  → BUILD SUCCESSFUL, 142 tests, 0 failed (출력 마지막 10줄 원문 붙여넣기)

#### 테스트 매트릭스
(2절 템플릿)

#### 수용 기준별 판정
- AC-1 "...": PASS (cmd#3, matrix #1-2)
- AC-2 "...": FAIL (matrix #3, 결함 DEF-01 보고)

#### 종합 판정: PASS | FAIL
#### 미검증 잔여 리스크: (명시적으로, 없으면 "없음")
```

Evidence = the actual command plus the actual output excerpt.

## 5. Defect report template (RETURN to your dispatcher — qa never writes plan.md)

qa returns defect reports in this format; only the orchestrator converts them into plan.md fix tasks (plan.md and state.json `tasks[]` are orchestrator-only per the harness-state skill).

```markdown
### DEF-<nn>: <one-line symptom>
- 심각도: blocks-goal | blocks-task | minor
- 담당(owner): backend-dev   의존성: <original-task-id> 완료를 차단
- 재현 절차 (최소화):
  1. <exact command or request — minimal payload that still reproduces>
  2. ...
- 기대: <quote design.md/plan.md line>  실제: <observed, verbatim>
- 추정 원인: <file:line 가설임을 명시>
- 증거: 검증 로그 cmd#<n>
- 수용 기준: 재현 절차 수행 시 기대 결과 반환 + 회귀 스위트 green
```

Reproduce twice before filing. Minimize first: strip payload fields, drop steps, shrink data until removing anything makes the bug vanish — that boundary is your suspected cause.

## 6. Flaky-test policy

1. A test failed → rerun the FOCUSED test once, then once more (max 2 reruns).
2. Fails every time → real defect. File it.
3. Intermittent → mark **FLAKY**: never counted as PASS, never rerun-until-green. Report as a separate defect ("FLAKY: <test name>", suggested owner backend-dev) with observed failure rate and both outputs — the orchestrator turns it into a task. Causes to name: time/`now()` dependence, test-order coupling, shared mutable state, real-network calls, sleeps instead of awaits.
4. Flaky on the change's critical path → blocks PASS for that criterion. Off-path flakiness = residual risk, listed explicitly.
5. Repeated offenders go to playbook.md via retro — flakiness is a defect class, not weather.

## 7. Dry-run vs full integration — when to demand which

**Dry-run / fixture level suffices** for pure logic, parsing/mapping, prompt construction, or config wiring — anything fully expressible in recorded fixtures. The Python AI worker's dry-run mode is the default gate for its logic changes: `uv run pytest -q -m dry_run`.

**Demand full integration (real DB via Testcontainers / staged environment / real deploy with `--no-traffic`)** when the change touches:
- SQL/JPA queries, migrations, transaction or locking behavior (H2/mocks lie here)
- Serialization boundaries with external systems (Vertex AI request/response shapes, webhook payloads)
- Auth, IAM, Secret Manager wiring, Cloud Run/Scheduler config — config only fails for real
- Concurrency, retries, timeouts, idempotency
- Anything where a fixture would be written by the same assumption that would contain the bug

Rule: mocks verify YOUR logic; integration verifies YOUR ASSUMPTIONS about others. A criterion about external behavior can never be PASSed on mocks alone — if integration was impossible, say so in residual risks and mark that criterion FAIL. There are only two verdicts, PASS and FAIL; a pass with named risks or conditions attached does not exist.

## 8. Verifier's checklist before writing PASS

- [ ] Full suite ran (not just focused tests) and output tail is in the log
- [ ] Every acceptance criterion has a matrix row and a per-criterion verdict
- [ ] At least one edge and one failure case per criterion actually executed
- [ ] Builder's new tests spot-read: they assert the criterion, not mock it away
- [ ] Regression: neighboring behavior re-checked
- [ ] Residual risks written down, even (especially) when everything passed
