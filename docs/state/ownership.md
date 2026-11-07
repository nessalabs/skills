---
id: "skill-ownership"
title: "Find the owner of a rule"
kind: "guide"
status: "reference"
summary: "Each lesson has one owning skill or reference. Use this map to find that owner before changing instructions; this atlas summarizes the routes without becoming a second rulebook."
parent: "skills"
sources:
  ["AGENTS.md", "skills/engineering/README.md", ".claude-plugin/plugin.json"]
sourceRevision: "1ae753c25b29967c0a8672c275d3d1d40f0de865"
diagramLinks: {}
---

# Find the owner of a rule

Each lesson has one owning skill or reference. Use this map to find that owner before changing instructions; this atlas summarizes the routes without becoming a second rulebook.

| Skill                | Owns                                              | Supporting material                                          |
| -------------------- | ------------------------------------------------- | ------------------------------------------------------------ |
| `coding`             | How to make a change and report it                | Rust, React/TypeScript and testing references                |
| `system-architect`   | Ownership, boundaries and design decisions        | Structure, patterns, velocity and decision-record references |
| `method`             | Finding, verifying and retaining evidence         | Investigation stages in its SKILL.md                         |
| `trace`              | Source-path reconstruction                        | Output format and Python expand helper                       |
| `test-gaps`          | Reviewing recent fixes for missing conditions     | Uses testing and PR owners rather than copying their rules   |
| `pull-requests`      | PR descriptions, evidence and review              | Description template and diagram conventions                 |
| `wdym`               | Plain-language explanation                        | Examples in its SKILL.md                                     |
| `connect-a-computer` | Tailnet reachability, pairing, grants and serving | External Nessa and Tailscale commands                        |
| `nessa-docs`         | Repository state maps and optional rule checks    | Markdown/model format                                        |

The [engineering owner table](../../skills/engineering/README.md#how-the-set-is-organised) is the authoritative lesson routing. The [Nessa index](../../skills/nessa/README.md) owns the product skill routes. Plugin and package metadata describe distribution, not a lifecycle. Agent labels describe discovery, not execution evidence.

For a new lesson, first ask whether an existing ownership or check-scope rule already explains it. Put the change with that owner and link to it elsewhere. The source instructions require version updates for broad skill changes; this atlas itself adds no new instructional policy. Unrelated codebases remain governed by their own working instructions.
