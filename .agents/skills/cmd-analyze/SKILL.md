---
name: cmd-analyze
description: "ANALYZE phase — delegate to the analyst agent to investigate the codebase and context, producing .harness/analysis.md (mirrors /harness:analyze)"
---

This skill mirrors the Claude Code command `/harness:analyze`. Read the full workflow definition at `plugins/harness/commands/analyze.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
