---
id: "skill-trace"
title: "Follow calls without mistaking candidates for proof"
kind: "statechart"
status: "implemented"
summary: "Trace helps you answer “what runs when this happens?” Start with an
  actual entry point and a fixed source revision. The helper returns candidate
  calls and locations; the agent must still read conditions and confirm which
  implementation runs."
parent: "skills"
sources:
  [
    "skills/engineering/trace/SKILL.md",
    "skills/engineering/trace/scripts/expand.py",
    "skills/engineering/trace/references/format.md"
  ]
sourceRevision: "1ae753c25b29967c0a8672c275d3d1d40f0de865"
diagramLinks: {}
model: { "spec": "tla/TraceTraversal.tla", "config": "tla/TraceTraversal.cfg" }
diagramDetails:
  [
    {
        "diagram": 0,
        "node": "Gap",
        "section": "What the implementation actually selects"
      },
    {
        "diagram": 0,
        "node": "Emit",
        "section": "What the implementation actually selects"
      }
  ]
modelCheck:
  sourceRevision: "1ae753c25b29967c0a8672c275d3d1d40f0de865"
  checker: tlc-1.7.4
  date: 2026-11-03T09:02:35.058Z
  config: tla/TraceTraversal.cfg
  modelDigest: f31e3ace3bcb7743ceffdd547a0862361a5bdc1df23734c2c003d405720ae316
  states: 10
  held:
    - UniqueEmission
    - DepthBound
  broke: []
  unchecked: []
---
# Follow calls without mistaking candidates for proof

Trace helps you answer “what runs when this happens?” Start with an actual entry point and a fixed source revision. The helper returns candidate calls and locations; the agent must still read conditions and confirm which implementation runs.

For example, a name tagged as a lock may not acquire any lock at all. Tags come from name patterns. A missing definition may be an external call, dynamic dispatch, unsupported syntax or a parser failure. None of those results proves that no work occurs.

```mermaid
stateDiagram-v2
  [*] --> Locate
  Locate --> Gap: No matching definition returned
  Locate --> Seen: File and start line already visited
  Locate --> Inspect: New definition
  Inspect --> Emit: Collect calls marks and candidate locations
  Emit --> Locate: Depth permits a recursive callee
  Emit --> Done: No more selected callees
```

## Use the result

The [Trace procedure](../../skills/engineering/trace/SKILL.md) distinguishes understanding mode from debugging. Understanding follows required branches and ends with gaps. Debugging starts with observable symptoms and candidate mechanisms, follows relevant branches and ends with suspects, probes, invariants and a test location. A source trace does not itself reproduce a bug.

Run the helper from its skill directory with Python and an available ast-grep:

```sh
python3 scripts/expand.py main --root /absolute/project --lang python --depth 2 --json
```

The root must be the codebase you intend to read. `--in` narrows the starting definition. Positive depth counts the root as the first level: `--depth 2` inspects the root and one level of selected callees. Without a language, extension counts select one; generated/dynamic code and unsupported syntax require manual follow-up. If no installed ast-grep/sg is detected, the helper can invoke npx to obtain it. That external installation and parser are separate from the source being traced.

## What the implementation actually selects

Definitions are deduplicated by file and starting line. Calls are deduplicated by callee text within one definition; source order is retained. Resolution sorts same-file and same-directory candidates first and retains up to five. Recursive expansion takes the first candidate's file, then looks up the bare name again in that file. All matching definitions there can be inspected, including same-named methods on different types. Qualified lookup falls back to the bare name when no qualified hit exists. Confirm ambiguity instead of treating the first candidate as type resolution.

The current script recurses depth-first, despite its docstring/skill describing the expansion as breadth-first. It scans whole files for matches and filters the definition's line range, despite “only the body parsed” wording. `--depth` controls recursive expansion, not an exhaustive call graph; zero or negative values still inspect the root. These are source-observed documentation discrepancies, not fixed behavior in this atlas.

Parser failures can be printed on stderr and returned as an empty result. The helper therefore cannot distinguish every parser error from a genuine empty match using its JSON alone. Preserve stderr and investigate unexpected gaps. The parser smoke tests here cover a small Python fixture, not every language, overload or generated call.

## Model scope

The bounded model represents four already-resolved definitions, a stack and visited identities, at depth two or three. It checks that a definition is emitted at most once and recursive emissions stay within the requested positive depth. It assumes candidate resolution and depth inputs are valid. It does not prove complete call-graph discovery, parse correctness, type dispatch or breadth-first order. Controls remove visited suppression and the depth guard. Actual traversal tests separately exercise the production Python helper.
