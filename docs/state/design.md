---
id: "skill-design"
title: "Choose boundaries that keep decisions local"
kind: "guide"
status: "reference"
summary: "Put a decision where the information needed to make it already lives. A caller should use that owner's result rather than maintain a second guessed answer."
parent: "skills"
sources:
  [
    "skills/engineering/system-architect/SKILL.md",
    "skills/engineering/system-architect/references/structure.md",
    "skills/engineering/system-architect/references/patterns.md",
    "skills/engineering/system-architect/references/adr.md",
    "skills/engineering/system-architect/references/velocity.md",
  ]
sourceRevision: "1ae753c25b29967c0a8672c275d3d1d40f0de865"
diagramLinks: {}
---

# Choose boundaries that keep decisions local

Put a decision where the information needed to make it already lives. A caller should use that owner's result rather than maintain a second guessed answer.

For example, if two parts separately decide whether a request is still current, they can disagree after a delayed reply. Find the owner of the request identity and make the decision there. Then ask whether that answer still applies to the same request, moment and conditions when it is used.

The [system-architect skill](../../skills/engineering/system-architect/SKILL.md) owns these two core rules and their applications to boundaries, failure and concurrency. It distinguishes mechanism from policy, description from execution, and a small reusable core from product-specific capability. These are design questions, not a prescribed folder template.

| Decision you are making                                  | Owning reference                                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Module/process layout and dependency absence             | [Structure](../../skills/engineering/system-architect/references/structure.md)  |
| A concrete concurrency, publication or caching technique | [Patterns](../../skills/engineering/system-architect/references/patterns.md)    |
| Why a decision was made and what remains                 | [Decision records](../../skills/engineering/system-architect/references/adr.md) |
| Why ordinary changes require excessive coordination      | [Velocity](../../skills/engineering/system-architect/references/velocity.md)    |

Avoid turning an example pattern into a universal requirement. The source asks whether the extra abstraction solves a real coupling or future-change problem. The resulting design still needs verification in its target repository; the instruction text alone enforces no imports or runtime invariant.
