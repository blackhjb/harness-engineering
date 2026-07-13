#!/usr/bin/env bash
# Hunter Harness 오프라인 설치 스크립트 (대체 수단)
#
# 권장 경로는 README의 방법 1 — 플러그인 마켓플레이스:
#   /plugin marketplace add <repo>  →  /plugin install harness@hunter-harness
# 이 스크립트는 마켓플레이스를 쓸 수 없는 환경을 위한 오프라인 폴백이다.
#
# 동작: 플러그인 내용을 Claude Code가 자동 로드하는 문서화된 경로에 복사한다.
#   agents/*   → .claude/agents/
#   skills/*   → .claude/skills/
#   commands/* → .claude/commands/  (harness- 접두사로 리네임: goal.md → harness-goal.md)
# 따라서 이 방식으로 설치하면 커맨드는 /harness:goal 이 아니라 /harness-goal 형태다.
#
# 주의: <project>/.claude/plugins/ 는 문서화된 플러그인 자동 로드 경로가 아니고,
#       ~/.claude/plugins/ 수동 복사는 플러그인 매니저와 충돌할 수 있어 사용하지 않는다.
#
# 사용법:
#   ./install.sh /path/to/project   # 프로젝트 로컬 설치 (<project>/.claude/)
#   ./install.sh --user             # 사용자 전역 설치 (~/.claude/)
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/plugins/harness"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "오류: $SRC_DIR 를 찾을 수 없습니다. repo 루트에서 실행하세요." >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "사용법: $0 </path/to/project | --user>" >&2
  exit 1
fi

if [[ "$1" == "--user" ]]; then
  CLAUDE_DIR="$HOME/.claude"
else
  PROJECT_DIR="$1"
  if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "오류: 프로젝트 디렉토리가 없습니다: $PROJECT_DIR" >&2
    exit 1
  fi
  CLAUDE_DIR="$PROJECT_DIR/.claude"
fi

STAMP="$(date +%Y%m%d%H%M%S)"

# 덮어쓰게 될 기존 파일/디렉토리는 타임스탬프 백업으로 보존한다.
backup_if_exists() {
  local dest="$1"
  if [[ -e "$dest" ]]; then
    local backup="${dest}.bak.${STAMP}"
    echo "  기존 항목 백업: $backup"
    mv "$dest" "$backup"
  fi
}

# --- agents ---
echo "에이전트 복사 → $CLAUDE_DIR/agents/"
mkdir -p "$CLAUDE_DIR/agents"
for f in "$SRC_DIR"/agents/*.md; do
  base="$(basename "$f")"
  backup_if_exists "$CLAUDE_DIR/agents/$base"
  cp "$f" "$CLAUDE_DIR/agents/$base"
done

# --- skills ---
echo "스킬 복사 → $CLAUDE_DIR/skills/"
mkdir -p "$CLAUDE_DIR/skills"
for d in "$SRC_DIR"/skills/*/; do
  name="$(basename "$d")"
  backup_if_exists "$CLAUDE_DIR/skills/$name"
  cp -R "$d" "$CLAUDE_DIR/skills/$name"
done

# --- commands (harness- 접두사로 리네임) ---
echo "커맨드 복사 → $CLAUDE_DIR/commands/ (harness- 접두사)"
mkdir -p "$CLAUDE_DIR/commands"
for f in "$SRC_DIR"/commands/*.md; do
  base="$(basename "$f")"
  new="harness-${base}"
  backup_if_exists "$CLAUDE_DIR/commands/$new"
  cp "$f" "$CLAUDE_DIR/commands/$new"
  echo "  ${base} → ${new}   (/harness-${base%.md})"
done

echo ""
echo "설치 완료: $CLAUDE_DIR"
echo ""
echo "안내:"
echo "  - 이 설치 방식에서 커맨드는 /harness-goal, /harness-quick 처럼 하이픈 형태입니다."
echo "    (/harness:goal 콜론 형태는 플러그인 설치일 때만)"
echo "  - 권장 경로는 README 방법 1(플러그인 마켓플레이스)입니다. 이 스크립트는"
echo "    오프라인 폴백이며, 업데이트·삭제를 직접 관리해야 합니다."
echo "  - Claude Code를 재시작한 뒤 /harness-goal 로 시작하세요."
