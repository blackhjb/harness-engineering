---
name: harness-ledger
description: 장부(state.json·plan.md)·문서 정본 섹션·디스패치 계약 — 코디네이터(커맨드 실행 주체)·improver 전용. dev·qa·review 는 열 필요 없다.
---

# harness-ledger: 장부와 문서 계약

`harness-state` 가 공용 계약(디렉터리·위키·로그·컨텍스트 예산)을 정의하고, 이 스킬은 **장부를 쓰는 주체**만 필요한 세부를 담는다. 읽는 주체: 코디네이터(`/harness:*` 커맨드 실행 주체), `harness-improver`.

## state.json schema

```json
{
  "goal_id": "string — <yyyymmdd>-<short-slug>",
  "base_ref": "string|null — git commit SHA at goal start (set by /harness:goal via git rev-parse HEAD); diff base for code review",
  "phase": "goal | analyze | plan | design | build | verify | retro | done",
  "iteration": "integer ≥ 1 — increments on each /harness:goal over an existing .harness/",
  "updated_at": "ISO-8601 — refreshed on EVERY write",
  "approvals": { "design": "boolean", "plan": "boolean" },
  "verify": { "verdict": "\"PASS\" | \"FAIL\" | null", "date": "ISO-8601 | null" },
  "tasks": [
    {
      "id": "T-NNN — matches plan.md",
      "owner": "backend-dev | frontend-dev | ai-agent-dev | qa | code-reviewer | planner | analyst | architect | product-designer",
      "status": "pending | in_progress | blocked | review | done | failed | deferred",
      "artifacts": ["file paths this task created/modified"]
    }
  ]
}
```

Rules:
- The `owner` 10-role list = the SINGLE agent-role enum source; other files reference it, never restate it.
- `tasks[]` mirrors plan.md's table; on disagreement fix both, log it.
- plan.md and `tasks[]`: 코디네이터 전용. Commands may set `phase`/`approvals`/`verify`. Every other agent REPORTs to its dispatcher, never edits plan.md/state.json — qa and code-reviewer return structured defect reports + log entries; only the 코디네이터 turns findings into fix tasks.
- `approvals.design`/`approvals.plan`: set ONLY on an explicit user yes; they gate all build dispatches. `verify.verdict`: set only by the verify command.
- Write the whole file atomically (read, modify, write back complete JSON).
- `deferred` ≠ `pending`: a deferral is a DECISION (reason + where it is re-planned), never a leftover. NEVER park deferred work as `pending` — an unexecuted task and a deferred task must be distinguishable from status alone (로그 참조).
- state.json MUST be git-tracked: at scaffold time, if the repo's `.gitignore` excludes it (e.g. `*.json`), add a `!.harness/state.json` exception. An untracked state file cannot be recovered after a destructive git operation (dangling-blob recovery only works for staged files). EXCEPTION: a project may deliberately keep ALL of `.harness/` local-only (gitignored) — that is a recorded human decision (GOAL 제약 or a `decision` log entry), never an agent's. In such a repo the destructive-git ban above is the ledger's ONLY protection; treat `.harness/` as unrecoverable and never propose re-tracking it.

## Lifecycle rules

1. `/harness:goal` scaffolds everything; preserves wiki/, retro/, logs/ (accumulated learning) across iterations.
2. Phases move only forward except: verify FAIL → build, and any phase → goal (new iteration). The transition's writer updates state.json in the same turn.
3. Document ownership is exclusive per phase (table above); others read but do not edit — log disagreements and escalate.
4. Task status flow (English values only): `pending → in_progress → (review) → done`, branches `blocked`/`failed`. Only evidence-backed transitions to `done`.
5. Gates: design approval before build, verify PASS before done, human approval before applying harness edit proposals.
6. User decisions: PRIMARY record = the owning document (architecture → design.md ADR, scope/priority → prd.md, goal-level → GOAL.md); the `decision` log entry is secondary — "never re-ask" is enforced via the documents, not logs.
7. **Backward propagation**: when build/verify work REFUTES a premise recorded upstream (a GOAL measurement, an analysis F-NNN fact, a design assumption), 코디네이터 corrects the owning document IN THE SAME TURN — a one-line 정정 with the refuting evidence, never a silent divergence. Stale premises left in documents poison every later read (로그 참조).
8. **Quick route (규모 비례)**: a goal that `/harness:goal` triages as quick 경로 (no contract/architecture impact, mechanical diff, command-checkable SCs) **does not create analysis.md/prd.md/design.md/plan.md at all** (goal.md §4) and runs as `/harness:quick` batches; phase closes goal → done directly. What is NOT waived: every SC still gets its measurement command + value in a `verify` log entry, state.json `verify.verdict` is still set, and guard changes still require a positive control. Ceremony scales with the change; evidence does not (로그 참조).

## Canonical required sections per document

Scaffold directly from these lists; keep every section even if empty, marked "해당 없음":

- **GOAL.md**: 한 줄 목표 · 배경 · 성공 기준 표(SC-n / 기준 / 측정 방법 / 목표치) · 제약 · 기한 · 범위 제외 · 승인
- **analysis.md**: 요약 · 현재 상태(파일 경로 근거) · 아는 것(**each fact gets an ID `F-NNN` + file:line evidence** — downstream documents REFERENCE `F-NNN`, never copy the fact's prose; a refuted fact is corrected HERE first, then every referencing doc gets a one-line 정정 note in the same turn) · 알아내야 하는 것(U-n · 확인 방법 · 차단 여부) · 가정([확인]/[추정]/[불명] + 신뢰도) · 리스크 표(R-n · 가능성 상/중/하 · 영향 상/중/하 · 조기 신호 · 대응) · 권고
- **prd.md**: 문제 정의 · 타겟 사용자 · 사용자 스토리 표(US-n · 우선순위 P0-P2 · Given/When/Then 인수 조건) · 기능 요구사항(FR-n) · 비기능 요구사항(NFR-n — 정량 수치) · 스코프 컷·범위 제외 · 릴리스 슬라이스 · 규제·개인정보 체크 · 미해결 질문. Priorities: P0/P1/P2 only (P0 = must-ship); no other scale in artifacts.
- **design.md** (numbered, in order): 1 시스템 컨텍스트 · 2 품질 속성 우선순위 · 3 아키텍처 스타일 · 4 컴포넌트/모듈 책임 · 5 API 계약 · 6 데이터 모델 · 7 에러/장애 전략 · 8 UX 설계 (사용자 대상 기능일 때 — product-designer 작성; the ONLY UX section name) · 9 기술 선택 · 10 NFR 예산 · 11 설계 결정 (ADR) · 12 승인 (BUILD 게이트 체크박스 → state.json approvals.design)
- **plan.md**: 작업 표(T-NNN / 작업 / 담당 / 의존성 / 인수 조건 / 상태 / **증거**) · 병렬 실행 웨이브 · 커버리지 확인 · 리스크와 대비책. Status = the English enum above; 담당 = the state.json role list. 증거 column: `done` = commit sha or log entry ref · `deferred` = 사유 + 재편성 위치 · `blocked` = 차단 원인. A row whose status can't be justified by its 증거 cell is treated as NOT done.

Initial content (fresh scaffold): `wiki/INDEX.md` = header `# Wiki Index` + one format comment (`<!-- 형식: - [scope] [[slug]] — 한 줄 훅 (candidate) · 노드 파일은 <scope>--<slug>.md -->`).


## 위키 큐레이션 계수 (harness-improver 전용)

노드 형식·수명주기·상한은 `harness-state` 가 정본이다. 은퇴 대상을 **고르는** 계수만 여기 있다.

**은퇴 순서는 추측이 아니라 측정으로 정한다** — 「저가치」는 판단이라 오래된 노드가 남고 새 학습이 막힌다 (로그 2026-08-07). 은퇴 후보 순서:
1. **효과 반증** — 열린 상태에서 그 scope 의 `refutes` 가 발생한 노드(원장으로 계수). 노드가 있었는데 막지 못했다는 뜻이다.
2. **효과 미관측** — 5회 이상 열렸으나 그 scope 에서 `refutes` 도 예방 기록도 없는 노드.
3. 그 외 개선자 판단.
**효과가 확인된 노드(열린 goal 에서 그 부류 실패 0)는 은퇴시키지 않는다.** 자리가 없으면 1·2 를 먼저 비운다.

**동반실패 100% 인 노드는 은퇴 전에 먼저 본문 길이를 잰다** — 상한(`harness-state`: 10줄·날짜 ≤2) 초과면 실패 원인은 규칙이 틀린 게 아니라 **술어가 서사에 묻힌 것**이다. 그런 노드는 은퇴가 아니라 **압축**이 처분이고, 압축 후 다음 goal 의 계수로 재판정한다. 상한 안인데도 100% 면 그때 은퇴시킨다.

### 노드 효과 계수

디스패치 종료 시 원장 `d` 레코드에 **그 세션이 실제로 연 노드 slug 를 적는다**: `"nodes":["qa--x","global--y"]`. 개선자는 이것으로 센다 —
```
열림   = nodes 에 그 slug 를 가진 d 레코드 수
동반실패 = 그중 rework:true 인 d 레코드 수
```
「읽었다」가 아니라 **「열려 있었는데도 실패했는가」**를 센다. 노드가 조언인지 장치인지는 이 비율로만 판별된다.

**이 수치는 지목이지 판결이 아니다** — 귀속이 디스패치 단위라 한 세션에서 여러 노드가 열렸으면 책임이 나뉘지 않는다. 개선자는 이 표로 **조사 순서만** 정하고, 은퇴·수정은 기전을 확인한 뒤에 한다. 근거 goal 이 1개뿐인 노드는 아직 데이터가 아니다.

## 품질 지표 계수 (결산 주체 = 코디네이터)

**품질 지표 자동 계수**(하네스 `docs/GOAL.md` M1·M2·M5·M6) — goal 종결 시 결산에 값으로 기재:
```
M1 자기보고 정확도 = 1 − (refutes 필드를 가진 m 레코드 수 ÷ 전체 m 레코드 수)
M2 역할 에이전트   = (rework:false 인 d 중 agent≠코디네이터) ÷ (agent≠코디네이터 인 d 전체)
M6 브리프 정확도   = (rework:false 인 **위임** d) ÷ (**위임** d 전체)
  분모는 **브리프를 받은 디스패치**다 — 코디네이터 직접 집행 배치는 브리프가 없으므로 분모에서 뺀다(그 배치의 품질은 M1 이 잡는다).
  **`rework` 는 결산 시점에 재계상한다**: 디스패치 종료 시 자기신고는 verify 가 뒤집기 **전에** 확정된다. 결산은 그 goal 의 `refutes` 를 가진 m 레코드가 지목하는 원 측정의 디스패치를 `rework:true`/`cause:brief` 로 세고(원장은 append-only — 과거 행을 고치지 않는다), **그 재계상 결과를 산문뿐 아니라 원장에 한 줄로 append 한다**: `{"t":"m","id":"m-<HHMM>-coord-rework","agent":"coordinator","key":"결산 rework 재계상@<sha7>","value":{"<d-id>":"brief","<d-id>":"agent"}}`. 산문에만 적으면 다음 회고가 원장에서 얻는 `rework` 신호가 **0건**이 되어 M2·M6 미달 지점을 기계로 찾지 못한다(실측 2026-08-27: iter50 `d` 10건 전건 `rework:false` 인데 결산 M6 은 55.6%). 실측 2026-08-25 iter43: `d-1310` 은 `rework:false` 인데 그 산출 W2 −98줄은 전건 원복됐다.
M5 비용 비례       = (d 레코드 tokens 합) ÷ (변경 소스 파일 수, 테스트·픽스처·문서 제외)
```
**M2 와 M6 을 합산하지 않는다** — 합치면 어느 쪽을 고쳐야 하는지 가려진다. 실측 2026-08-25: 합산 68% 안에 에이전트 100% 와 브리프 45% 가 섞여 있었다.
**M6 이 M2 보다 낮으면 고칠 곳은 에이전트가 아니라 브리프다** — 그 goal 의 회고는 실패한 브리프의 `cause` 분포부터 연다.
원장이 비어 있으면 그 goal 의 지표는 **미측정**이지 100% 가 아니다 — 결산에 그렇게 적는다.

## 디스패치 계약 (코디네이터 = 유일 디스패처)

코디네이터는 조정만 하고 구현하지 않는다(유일 예외: 사용자가 명시 요청한 1줄 fixup). 유일 지표: 루프가 GOAL.md 성공 기준에 디스크 증거와 함께 수렴하는가.

### Startup protocol (every invocation)
1. Read `.harness/GOAL.md`, `wiki/INDEX.md` (open workflow/global nodes), `state.json`, `design.md`, `plan.md` (skip missing design/plan; schemas above). No GOAL.md → stop; tell the user to run `/harness:goal`.
2. Reconcile state.json with reality: `in_progress` with no artifacts changed on disk = `failed`, re-planned; log every discrepancy — never trust stale state silently.
3. Open (or create) today's shared log `.harness/logs/YYYY-MM-DD.md` (ONE append-only file for all agents; format per the `harness-state` skill); append a session-start entry.

## The loop
Repeat until every GOAL.md success criterion is met or an escalation fires:
1. PLAN — next wave: all plan.md tasks with dependencies `done` and status `pending`. **의존 엣지는 존중하기 전에 재확인한다** — 빌드 의존은 「같은 트리 + 둘 다 커밋」이거나 「뒤가 앞의 산출물을 소비」할 때만 성립한다(정본 규칙·근거는 `commands/plan.md` Stage 3). 배포 순서 제약이면 plan.md 에서 그 엣지를 정정하고 로그 1줄을 남긴 뒤 대기하지 않는다.
2. DELEGATE — **group before dispatching**: tasks with the same owner in the same working tree go into ONE session (ordered, one commit per task) — they serialize anyway, so extra dispatches buy only round trips and cold contexts. Then dispatch each group to its owner. Groups in **different** working trees, and read-only tasks (qa, review, investigation), run IN PARALLEL in a single message; **commit-producing groups sharing one tree run STRICTLY SERIAL** — **이 규율의 주어에는 디스패처 자신이 포함된다**: 커밋 산출 디스패치가 열려 있는 동안 코디네이터는 같은 트리에서 **어떤 커밋도 만들지 않는다**(문서·장부 포함). 장부는 커밋 없이 파일 편집으로 갱신한다.
  **코디네이터의 커밋도 pathspec 이다 — `git commit -m ... -- <파일 열거>` 로 쓰고 직후 `git show --stat` 으로 재확인한다. `git add -A -- <경로>` 는 pathspec 을 붙였는데도 **인덱스 전체**가 나가므로 금지다** — 「pathspec 을 썼다」는 자기점검을 통과해 버리는 형태다(실측 2026-08-28: 코디네이터가 `git add -A -- src .harness docs` 를 써 타 세션 문서 **+644줄**을 흡수했고, `git show --stat` 이 1482 insertions 를 내 그 goal 의 실적 −3줄을 가렸다. 위키 `workflow--shared-worktree-discipline` 이 열린 상태였으나 그 노드도 이 형태를 예시로 들지 않아 못 막았다).

**집행**: 커밋 전 `state.json` 에 `in_progress` 태스크가 1건이라도 있으면 커밋하지 말고 로그에 「커밋 보류: T-NNN in_progress」 1줄을 남긴다 (로그 2026-08-26 — 코디네이터 커밋이 남의 스테이징된 `git rm` 을 삼켰다). — agents share one working tree and git index, so parallel commits interleave staging even when files don't overlap (로그 참조). One task = one dispatch path; never let a second dispatcher (including yourself acting manually) pick up a task already dispatched.
3. OBSERVE — check each report against acceptance criteria; confirm claimed artifacts exist on disk.
4. WAVE GATE — before the next wave, confirm EVERY task of the finished wave has a log entry: commit-producing tasks via sha, **commit-less tasks (gates, investigations, doc checks) via their log entry — these leave no diff and are the ones that get silently skipped** (로그 참조). `done` only with evidence; "the agent said so" is not evidence. **그 항목이 인용한 원장 id 는 표본이 아니라 전수 대조하고 게이트 줄에 「인용 <n>건 · 미실재 <m>건」을 값으로 적는다** — `for id in <인용 목록>; do grep -c -F "\"$id\"" .harness/measurements.jsonl; done`. 미실재 >0 이면 그 태스크의 M1·M5 는 조인 불가이므로 `done` 전에 집행자에게 정정 항목을 요구한다(실측 2026-08-27: 표본 1/8 확인이 8건 전건 오기를 통과시켰고, 같은 goal 에서 두 번째 9건 오기는 게이트가 아예 못 잡았다).
5. ITERATE — update plan.md (status + 증거 column) + state.json; re-read `git log -1` before writing state (a sibling may have committed or amended — never identify an artifact by a sha you remember rather than re-check). Then next wave.

**You run ALL waves continuously. Finishing one wave is not a stopping point.** Stop ONLY on: (1) every task done → hand to verify, (2) blocked with no independent work remaining, (3) an escalation rule fires, (4) context limit approaching → write a handoff (per-task next action, current wave, plan/state accuracy) and end. After the final wave the goal is NOT met until a verify phase (qa + code-reviewer) returns PASS.

## Dispatch contract — every task prompt contains, and NOTHING more
Task ID + acceptance criteria verbatim from plan.md · read-first = GOAL.md + wiki/INDEX.md (own-scope nodes) + **the agent's own plan.md task row + only the design/prd SECTIONS that row cites** (never "read design.md/analysis.md" wholesale — the fixed read-set in the `harness-state` skill is the contract) · exact artifact paths · **시간 상한·착수 증거는 아래 §비동기 루프가 정본** · **착수 증거: 착수 5분 내에 지정 산출물 파일에 헤더(제목 + 착수 시각 + 읽기 목록)만이라도 기록** — 디스패처는 그 파일의 존재·mtime 으로 생존을 값으로 확인한다(파일 부재 = 정지, 추론 불필요) · the instruction to log its result (with evidence) to the shared daily log, record insights as wiki nodes (create/reinforce/promote per the `harness-state` skill), and REPORT status/defects/blockers in its reply — role agents never edit plan.md or state.json.

## Dispatch economy — 디스패치 단가는 작업 크기가 아니라 컨텍스트 재구축이 정한다
실측(2026-08-06): 14 디스패치 평균 **107k 토큰**, 최소 64k — 작업 크기와 거의 무관했다. 토큰 대부분은 에이전트가 GOAL·위키·코드베이스를 **처음부터 다시 파악**하는 데 쓰인다. 같은 파일을 두 에이전트가 각자 파악하면 그 비용은 두 번 든다.
- **앵커 우선**: 이미 확인된 사실은 `file:line` 과 함께 브리프에 싣고 "재검증하지 말고 여기서 출발"이라고 명시한다. 실측상 이 문장이 있는 배치가 눈에 띄게 짧았다(64k·72k). 단, **전제가 틀릴 수 있음**을 함께 적어라 — 아래 전제 게이트가 그 안전장치다.
- **전제 게이트**: 브리프의 전제가 검증에서 깨지면 **구현하지 말고 즉시 중단·보고**하게 하라. 억지 구현 금지. (로그 참조)
- **재사용 > 신규 스폰**: 직전 에이전트와 레포·파일 영역이 겹치면 새로 스폰하지 말고 그 에이전트를 이어서 쓴다(컨텍스트 재구축 1회가 통째로 빠진다). 겹치지 않을 때만 새로 스폰한다.
- **모델 티어링 — 정본은 `agents/*.md` frontmatter 의 `model:` 하나뿐이다.** 지시·문서·기억은 정본이 아니다: 사용자가 티어 정책을 바꾸면 **같은 턴에 frontmatter 를 편집한다** (로그 2026-08-20 — 지시만 있고 frontmatter 가 옛 값이라 디스패치 2건 전손). 집행: 디스패치 로그 항목에 `model=<값>` 을 **값으로 적는다**(적으려면 frontmatter 를 실제로 읽어야 한다 — 값 없는 항목 = 계약 위반). 하향은 **기계적 · 되돌리기 쉬움 · 판정 없음** 3조건을 **전건** 충족하는 배치만(문구 교체·주석 정정·픽스처 정리). 코드 편집이 1줄이라도 있으면 하향 금지 — 삭제도 호출부 패치 판단을 남긴다. `code-reviewer` · `analyst` · verify 판정 · 보안/계약 표면은 **절대 하향 금지**.

## 비동기 루프 — 디스패치의 기본 실행 형태 (코디네이터 직접 디스패치에도 동일 적용)
- **예상 10분+ 디스패치는 background 로 띄우고, 완료 알림이 루프를 전진시킨다.** 디스패처는 대기하지 않는다 — 다른 트리 디스패치·장부 갱신·다음 웨이브 준비·독립 조사를 병행한다. 알림 전 결과를 추정하거나 선반영하는 것은 금지다.
- **시간 상한의 집행(장치)**: 20분 무보고 → 그 에이전트의 output 파일을 **1회** 열어 중간 상태를 실측한다(mtime·경과 시간으로 사망 판정 금지 — liveness 는 알림 또는 output 실측으로만). 45분 → TaskStop 후 **남은 범위만** 델타 재브리프. 그 사이 반복 폴링 금지 — 확인은 상한 시점 1회씩이다. 환경이 background 실행을 지원하지 않으면 동기 실행으로 강등하되 시간 상한 집행은 동일하다.

- **인과 가설·해법 지정 브리프의 선행 조건(장치)**: 브리프가 「X 때문에 Y」(원인) 또는 「X 를 이렇게 고쳐라」(해법)를 실으면, 그 문장에 **`[가설]` 표식**을 붙이고 착수 **첫 단계**로 **반사실 1회**를 요구한다 — 원인형은 X 를 넣고/빼서 Y 가 실제로 바뀌는지, 해법형은 그 착지점에서 **기존 성공 케이스 상실 0** 인지. 바뀌지 않으면(=no-op) 집행하지 말고 blocked 로 닫고 진짜 기전을 값으로 보고하게 하라. 심볼 생존 표는 「그것이 있는가」만 답하므로 이 축을 덮지 못한다. 표식은 **실측 근거가 없는 문장에만** 붙인다 — 남용하면 앵커 우선의 토큰 절감이 무너진다. 반사실 준비가 태스크만큼 비싼 표면(외부 API·비결정 LLM)에서는 「가설이 반증되면 blocked 가 정답」을 브리프에 1줄 명시하는 것으로 갈음한다 (로그 2026-08-19: 통로 부재로 디스패치 1건 전량 폐기, 지정 해법 1건은 기존 차단 2건 상실로 기각).
- **삭제·제거형 브리프의 선행 조건(장치)**: 브리프가 지울 심볼·상수를 나열하면, 착수 **첫 단계**로 그 목록의 **현 HEAD 정의부 grep 생존 표**(심볼 → 정의 hit 수)를 요구한다. 0 hit 는 dead 가 아니라 「이미 집행됐거나 이름이 틀림」이고, 좌표와 이름이 어긋나면 **이름이 정본**이다. 생존 0 항목은 집행 목록에서 빼고, 그 사실을 인용한 상류 문서의 정정으로 되먹인다 (로그 2026-08-18).
- **수렴·값-동등형 브리프의 선행 조건(장치)**: 브리프가 「N벌을 1벌로」·「값-동등이니 치환하라」를 요구하면 **가드 차집합 표**(벌 → 가드 집합 → 차집합 원소)를 싣고 **차등 형태를 열거하지 않는다** — 형태는 그 차집합에서 집행자가 역산한다. 예시를 함께 실으면 같은 줄에 **「이 목록은 하한 — 차집합으로 재도출해 개수가 다르면 큰 쪽이 정본」**을 적는다. **주입 red 는 지목 축마다 1건**이고 **축 수 ≠ 주입 수면 인수조건 미충족**이다.
  **집행(값 트리거)**: 브리프에 표적 개수를 나타내는 **정수**(「사본 3벌」·「형태 4개」·「사이트 8곳」)가 나오면 **그 줄에 그 정수를 만든 계수 명령**이 있어야 한다 — 없는 정수는 측정값이 아니라 승계 사실이므로 「<명령> 으로 세라」로 바꾼다. 사본 계수는 **이름 grep + 본문 표현식 grep 2축**이다(이름 grep 만 쓰면 함수로 안 뽑힌 인라인 사본이 분모에서 빠진다 — 2026-08-26: 형태 열거로 `hasattr` 축이 브리프 단계에서 누락돼 MAJOR 1건이 리뷰까지 흘렀고 「3벌」이 실제 4벌, 재디스패치 1회·M6 33.3%).

**Do NOT restate wiki nodes, skill content, or past-incident lore in dispatches.** Agents read the wiki themselves (universal rule #1); duplicating it bloats every prompt and rots when the wiki is curated. A dispatch over ~20 lines means acceptance criteria belong in plan.md or the lesson belongs in a wiki node — move it, don't inline it.

By task type: `backend-dev` Java/Spring · `frontend-dev` React UI · `ai-agent-dev` Python/LLM · `qa` verification · `code-reviewer` review · `planner` requirements · `analyst` investigation · `architect` design · `product-designer` UX 설계.

## Gates — hard rules, regardless of who asks
- No BUILD dispatch unless `design.md` exists and `approvals.design == true`; no BUILD wave unless `approvals.plan == true` (the user saw and approved plan.md).
- No task `done` without criteria demonstrably met + evidence logged; phase never `done` without a verify PASS verdict in state.json and logs.
- You are the sole writer of `plan.md` and state.json `tasks[]`/statuses (commands may set `phase`/`approvals`/`verify` per §state.json schema); apply reported statuses with the enum pending / in_progress / blocked / review / done / failed (English enum only in files). Never implement changes yourself — edit only `.harness/` bookkeeping files; every code change goes through a role agent (sole exception: a one-line fixup explicitly requested by the user).

## Failure handling
- 1st failure: **원 브리프를 다시 쓰지 말고** 같은 담당에게 델타만 보낸다 — 실패한 인수조건 1건 + 실패 증거 + 원 브리프 참조. 브리프 재작성이 그 자체로 새 오류원이다(재실행 실수의 실측 원인).
- 2nd failure: stop retrying — fix task with a different approach or owner, or escalate to the human.
- Every failure: log entry + one candidate wiki node (or a reinforcement of the matching existing node) — pattern, not blame.

## Escalate to the human — stop the loop when
- Ambiguity lets two reasonable implementations diverge
- Destructive/hard-to-reverse action: data migration, deletion, force-push, prod deploy, spending money
- A tradeoff would change scope, deadline, or any GOAL.md success criterion
- The same task failed twice, or two agents produced contradictory artifacts

## State discipline
- Update state.json after every status change and phase transition; always refresh `updated_at` (ISO-8601).
- The shared daily log holds all evidence; minimum events: dispatch, result with evidence, gate decision, escalation + resolution.
- plan.md's status column is the human-readable source of task truth; state.json `tasks[]` mirrors it; disagreement → fix both, log the correction.

## Anti-patterns you never commit
Dispatching dependent tasks in parallel. Parallelizing commit-producing tasks.
**Committing anything yourself while a commit-producing dispatch is open in the same tree.**
 Marking work done to "keep momentum". Editing source yourself for speed. Silently narrowing the goal so verify passes. Chat as the only record of a decision. A third re-run of a failed task with the same prompt. **Completing after a single wave when pending tasks remain** (the loop's four stop conditions are exhaustive). **Restating wiki-node/skill content inside dispatch prompts.** **Leaving a refuted upstream premise uncorrected** (backward propagation per §Lifecycle rules 7). Appending task findings to phase documents instead of the log. **Declaring a dispatched agent dead from file mtime, tree state, or elapsed time and then editing its files yourself** — liveness comes only from the task notification or an explicit stop; guessing wrong puts two writers on one file.

질문은 `co-creation` 스킬을 따른다; 기록된 결정은 재질의하지 않는다.
