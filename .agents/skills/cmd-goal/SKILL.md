---
name: cmd-goal
description: "Set or reset the harness goal — brief interview, then scaffold .harness/ and write GOAL.md with measurable success criteria (mirrors /harness:goal)"
---

This skill mirrors the Claude Code command `/harness:goal`. Read the full workflow definition at `plugins/harness/commands/goal.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
