# GOAL — Hunter Harness 구축

> 이 문서는 하네스 자신의 GOAL이다. 하네스가 관리하는 프로젝트의 GOAL.md와 같은 형식을 따른다.
> 참조: Lilian Weng, "Harness Engineering for Self-Improvement" (2026-07)

## 목표

1인 개발자(백엔드·프론트·AI 에이전트·기획·운영 전담)가 어떤 프로젝트, 어떤 PC에서든
한 줄 설치로 이식해 쓸 수 있는 **목표 지향(goal-driven) 멀티 에이전트 개발 하네스**를 만든다.

## 성공 기준 (측정 가능)

| ID | 기준 | 검증 방법 |
|----|------|-----------|
| SC-1 | `/plugin marketplace add <repo>` + `/plugin install harness` 만으로 새 환경에 설치된다 | 신규 프로젝트에서 설치 후 `/harness:goal` 실행 |
| SC-2 | 요청 역할 6종(개발자·설계자·분석자·QA·기획자·상품설계자) + 확장 4종(오케스트레이터·코드리뷰어·SRE·하네스개선자)이 모두 에이전트로 존재한다 | `agents/` 파일 12개, frontmatter 유효 |
| SC-3 | GOAL→분석→기획→설계→구현→검증→회고 전 단계가 커맨드로 실행 가능하다 | 8개 커맨드 동작 (goal·analyze·plan·build·verify·retro·status + 경량 경로 quick) |
| SC-4 | 모든 작업 상태가 `.harness/` 파일로 영속화되어 세션이 끊겨도 복구된다 | state.json + 산출물 파일 스키마 존재 |
| SC-5 | 스택별 스킬(Spring Boot, React/TS, LLM 에이전트, 데이터 파이프라인, GCP MLOps, QA, 기획문서) + 공동 제작 프로토콜이 존재한다 | `skills/` 9종 |
| SC-6 | 하네스가 자기 실패를 회고해 스스로 개선안을 내는 루프가 있다 | `/harness:retro` + harness-improver 에이전트 |

## 제약

- 프롬프트는 영어(모델 성능 최적), 사용자 응답·산출물은 한국어.
- 하네스 개선(회고) 루프는 제한된 편집면만 허용: 플레이북·프롬프트·게이트. 권한/안전 규칙은 편집 금지, 적용은 사람 승인 후.
- 파괴적 작업(운영 배포, 리소스 삭제)은 항상 사람 승인 게이트.
- 1인 유지보수 전제: 지루한 기술(boring tech), 최소 가동부.

## 범위 외

- 모델 가중치 학습/튜닝 (기사에서 말하는 joint optimization은 범위 외)
- 자동 하네스 편집 적용 (제안까지만, 적용은 사람이)
- CI 서버 등 외부 인프라 구축
