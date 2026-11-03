---
id: "skills"
title: "Choose an engineering or Nessa skill"
kind: "system"
status: "implemented"
summary: "This repository gives an agent written procedures for engineering work and Nessa setup. It does not run an agent service. Most files are instructions the host reads; the trace helper is the only executable tool shipped here."
parent: null
sources:
  [
    "README.md",
    ".claude-plugin/plugin.json",
    "skills/engineering/README.md",
    "skills/nessa/README.md",
  ]
sourceRevision: "1ae753c25b29967c0a8672c275d3d1d40f0de865"
diagramLinks:
  {
    "Engineering": "skill-ownership",
    "Nessa": "skill-authoring",
    "Rules": "skill-ownership",
    "Trace": "skill-trace",
  }
---

# Choose an engineering or Nessa skill

This repository gives an agent written procedures for engineering work and Nessa setup. It does not run an agent service. Most files are instructions the host reads; the trace helper is the only executable tool shipped here.

For example, when a message goes missing, use Trace to locate the path, Method to investigate the cause, Coding to make a supported change, and Pull requests to explain the result. These are cooperating procedures, not automatic stages enforced by a scheduler.

| Your task                              | Start here                                          |
| -------------------------------------- | --------------------------------------------------- |
| Install the set or understand updates  | [Installation](installation.md)                     |
| Find the one file that owns a rule     | [Ownership and inventory](ownership.md)             |
| Change code or choose tests            | [Coding and tests](coding.md)                       |
| Decide module boundaries               | [System design](design.md)                          |
| Investigate a bug or performance claim | [Evidence and plain explanations](investigation.md) |
| Follow a runtime path                  | [Trace and its helper](trace.md)                    |
| Add coverage for recent fixes          | [Test-gap review](test-gaps.md)                     |
| Write or review a PR                   | [Pull requests](pull-requests.md)                   |
| Connect another computer to Nessa      | [Computer setup](connect.md)                        |
| Author a state atlas                   | [Nessa Docs procedure](authoring.md)                |
| See what was checked here              | [Verification and limits](verification.md)          |

```mermaid
flowchart TD
  Host[Agent host reads a skill] --> Engineering[Engineering procedures]
  Host --> Nessa[Nessa setup and documentation]
  Engineering --> Rules[One owner for each lesson]
  Engineering --> Trace[Optional syntax-tree helper]
  Trace --> Parser[External ast-grep parser]
  Nessa --> Products[External Nessa gateway and renderer]
```

The checked-in plugin manifest lists nine skills: seven engineering and two Nessa skills. The README's “all seven” sentence describes the engineering group; it is not the whole plugin count. The source checkpoint is this repository's revision. A target project, agent host, Tailscale installation or Nessa binary has its own version and evidence boundary.
