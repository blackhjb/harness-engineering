---
description: RETRO phase — delegate to harness-improver to mine failures from logs and candidate wiki nodes, curate the wiki ACE-style, and propose bounded harness edits for user approval
argument-hint: "[optional: specific incident or theme to focus on]"
---

Run the harness RETRO (회고) phase. Focus: $ARGUMENTS

Respond in Korean.

## Preconditions
Proceed if `.harness/logs/` contains at least one daily log (excluding `logs/archive/`) OR `.harness/wiki/INDEX.md` lists candidate nodes OR a legacy `playbook.md`/`retro/inbox.md` awaits migration. If none holds, tell the user there is nothing to retro yet and stop.

## Step 1 — Delegate to harness-improver
Brief:
- Your startup protocol: read GOAL.md, wiki/INDEX.md and every candidate node, find the last retro report, mine all `logs/` entries since then. Apply the user's focus if given: "$ARGUMENTS". A legacy `playbook.md`/`retro/inbox.md` present → run the one-time wiki migration per the harness-state skill first.
- Cluster failures into patterns (surface error vs causal mechanism); only patterns with ≥2 occurrences or one high-severity event yield proposals.
- Write the full report to `.harness/retro/YYYY-MM-DD.md` per your output contract (실행 요약 / 패턴 분석 / 위키 큐레이션 / 하네스 수정 제안 / 관찰 항목).
- Apply wiki curation (promote/merge/retire/create nodes + INDEX hygiene) directly to `.harness/wiki/`.
- Do NOT apply agent-prompt or workflow-gate edits — return them as diffs for human approval.
- Log completion. Do NOT write state.json — the command handles the phase change.

## Step 2 — Present for approval (Korean)
On return, first set state.json `phase` = "retro", refresh `updated_at` (commands may set phase; the improver may not). Then:
1. Pattern table (패턴 / 횟수 / 심각도 / 인과 메커니즘).
2. Wiki curation already applied (created/promoted/merged/retired node slugs and their rules).
3. Each harness edit proposal as a diff with 증거 / 기대 효과 / 회귀 리스크, **위험도 분류 동반**. **저위험**(additive 문구·체크리스트·기록 의무 — 게이트·권한·검증 엄격도를 바꾸지 않음)은 자동 적용 후 사후 통보만 한다; **고위험**(승인 게이트·권한·검증 엄격도·안전 규칙 변경)만 사용자가 건별 승인한다.
   **「적용 완료」의 정의(장치 4단계) — 넷을 다 하지 않은 수정은 적용이 아니라 임시 편집이다**: ①소스(`plugins/harness/…`) 편집 ②`.claude-plugin/plugin.json` **`version` 범프**(번호를 올리지 않으면 `claude plugin update` 가 같은 번호의 공개본으로 캐시를 덮어 수정이 전량 소실된다) ③소스 커밋 1건 ④런타임 캐시 동기 — 파일별 `diff -q <소스> <캐시>` **전건 동일**을 값으로 기재. 보고에 4단계 값을 적는다: `범프 <구>→<신>` · `커밋 <sha7>` · `동기 <n>/<n> IDENTICAL`. 캐시만 편집한 상태로 세션을 넘기지 않는다 (실측 2026-08-24: 수정 7건이 소스 미커밋 + 미범프 + 캐시 직접 편집 상태로 남아 update 1회 소실 위험) (사용자 결정 2026-08-14 — "사람이 볼 필요 있나"). Apply approved/auto-applied diffs to the named agent/command files; record each decision (auto-applied/approved/rejected + reason) in the retro report.
4. **역재생 검증 (every applied edit, no exceptions)**: replay the incident that motivated the edit against the NEW text — feed the same inputs the failing agent had and state whether the new rule yields a different decision. Record 판정: **장치**(the rule produces a value or a mechanical trigger that forces the different outcome) or **문장**(it asks for better judgment on the same call that already failed). A 문장 verdict means the edit does not close the failure — either convert it into a measurement/gate the agent must write down, or drop it. This is the harness's own positive control: an edit shipped without it is the harness-edit equivalent of a guard with no red run (로그 2026-08-06).
5. **산문 예산**: a rules section that keeps accreting loses per-line attention. When adding lines to a section that already exceeds ~12 lines, compress or delete equivalent lines in it (merge older incident narratives into a single clause) so the section does not grow monotonically. Report the section's before/after line count in the retro.
6. Never apply a rejected or unreviewed proposal; never let the improver touch permission or safety rules.

## Step 3 — Close the loop
If the verify verdict is PASS and no fix work remains, offer to set phase to "done". Suggest next: a new `/harness:goal`, or nothing.
