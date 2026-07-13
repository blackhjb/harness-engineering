---
name: cmd-plan
description: "PLAN + DESIGN phases — planner writes prd.md, architect (plus product-designer for user-facing work) writes design.md, orchestrator breaks it into plan.md tasks; ends at a user approval gate before build (mirrors /harness:plan)"
---

This skill mirrors the Claude Code command `/harness:plan`. Read the full workflow definition at `plugins/harness/commands/plan.md` (repo root relative) and execute it exactly as written. Where the workflow says to delegate to a named agent, spawn the Codex subagent of the same name (defined in `.codex/agents/`). All `.harness/` state conventions are defined in the `harness-state` skill.
