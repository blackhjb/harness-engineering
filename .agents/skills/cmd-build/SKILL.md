---
name: cmd-build
description: "BUILD phase — 코디네이터 executes plan.md, dispatching independent tasks to owner agents in parallel, updating state.json and logs until all tasks meet acceptance criteria (mirrors /harness:build)"
---

This skill mirrors the Claude Code command `/harness:build`. Read the full workflow definition at `plugins/harness/commands/build.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
