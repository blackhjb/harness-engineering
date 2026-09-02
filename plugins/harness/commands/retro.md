---
description: RETRO phase — delegate to harness-improver to mine failures from logs and candidate wiki nodes, curate the wiki ACE-style, and propose bounded harness edits for user approval
argument-hint: "[optional: specific incident or theme to focus on]"
---

Run the harness RETRO (회고) phase. Focus: $ARGUMENTS

Respond in Korean.

## Preconditions
Proceed if `.harness/logs/` contains at least one daily log (excluding `logs/archive/`) OR `.harness/wiki/INDEX.md` lists candidate nodes. If neither holds, tell the user there is nothing to retro yet and stop.

## Step 1 — Delegate to harness-improver
Brief:
- Your startup protocol: read GOAL.md, wiki/INDEX.md and every candidate node, find the last retro report, mine all `logs/` entries since then. Apply the user's focus if given: "$ARGUMENTS".
- Cluster failures into patterns (surface error vs causal mechanism); only patterns with ≥2 occurrences or one high-severity event yield proposals.
- Write the full report to `.harness/retro/YYYY-MM-DD.md` per your output contract (실행 요약 / 패턴 분석 / 위키 큐레이션 / 하네스 수정 제안 / 관찰 항목).
- Apply wiki curation (promote/merge/retire/create nodes + INDEX hygiene) directly to `.harness/wiki/`.
- Do NOT apply agent-prompt or workflow-gate edits — return them as diffs for human approval.
- Log completion. Do NOT write state.json — the command handles the phase change.

## Step 2 — Present for approval (Korean)
On return, first set state.json `phase` = "retro", refresh `updated_at` (commands may set phase; the improver may not). Then:
1. Pattern table (패턴 / 횟수 / 심각도 / 인과 메커니즘).
2. Wiki curation already applied (created/promoted/merged/retired node slugs and their rules).
3. Each harness edit proposal as a diff with 증거 / 기대 효과 / 회귀 리스크. **적용은 전건 사용자 승인 후다** (docs/GOAL.md 범위 외 · harness-improver Boundaries). 위키 노드 큐레이션만이 승인 없이 도는 채널이다.
   **「적용 완료」의 정의 — 장치 6단계. 여섯을 다 하지 않은 수정은 적용이 아니라 임시 편집이다.** 각 단계는 보고에 적을 **값**을 낳는다.

   | # | 단계 | 보고 값 | 안 하면 |
   |---|---|---|---|
   | ① | 소스(`plugins/harness/…`) 편집 | — | — |
   | ② | `bash tools/sync-codex.sh` | `sync <n>/<n>` + `copied as fallback` 수 | 미러가 뒤처져 Codex 가 **다른 규칙**으로 돈다. 폴백 >0 이면 심링크가 끊겨 편집이 전파되지 않는다 |
   | ③ | `version` 범프 — `plugin.json` **과** `marketplace.json` **양쪽** | `범프 <구>→<신>` | 번호가 같으면 `claude plugin update` 가 공개본으로 캐시를 덮어 수정이 전량 소실. 한쪽만 올리면 두 매니페스트가 갈린다 (2026-09-02: 1.29.1/1.29.2) |
   | ④ | 소스 커밋 1건 — `agents/*.md` 가 있으면 같은 이름 `.codex/agents/<name>.toml` 동반 | `커밋 <sha7>` | 미러 없는 커밋이 drift 의 발생 지점이다 |
   | ⑤ | 런타임 캐시 동기 + 푸시 | `동기 <n>/<n> IDENTICAL` · `ahead 0` | 캐시만 맞추고 origin 을 안 올리면 다음 update 가 옛 공개본으로 되돌린다 |
   | ⑥ | `python3 tools/check-canon.py` | `정합성 FAIL 0 / WARN <n>` | 위 다섯의 누락이 아무데서도 안 잡힌다 |

   캐시만 편집한 상태로 세션을 넘기지 않는다 (실측 2026-08-24). ②·④ 는 `tools/hooks/pre-commit` 이 커밋 시점에도 막지만 `--no-verify` 로 우회되므로 ⑥ 이 이중 가드다. Apply approved diffs to the named agent/command files; record each decision (approved/rejected + reason) in the retro report.
4. **역재생 검증 (every applied edit, no exceptions)**: replay the incident that motivated the edit against the NEW text — feed the same inputs the failing agent had and state whether the new rule yields a different decision. Record 판정: **장치**(the rule produces a value or a mechanical trigger that forces the different outcome) or **문장**(it asks for better judgment on the same call that already failed). A 문장 verdict means the edit does not close the failure — either convert it into a measurement/gate the agent must write down, or drop it. This is the harness's own positive control: an edit shipped without it is the harness-edit equivalent of a guard with no red run (로그 2026-08-06).
5. **산문 예산**: a rules section that keeps accreting loses per-line attention. When adding lines to a section that already exceeds ~12 lines, compress or delete equivalent lines in it (merge older incident narratives into a single clause) so the section does not grow monotonically. Report the section's before/after line count in the retro.
6. Never apply a rejected or unreviewed proposal; never let the improver touch permission or safety rules.

## Step 3 — Close the loop
If the verify verdict is PASS and no fix work remains, offer to set phase to "done". Suggest next: a new `/harness:goal`, or nothing.
