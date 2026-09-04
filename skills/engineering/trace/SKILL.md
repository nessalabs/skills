---
name: trace
description: "Reconstruct the real runtime call path of a feature from source — every branch, layered like a stack, regenerated every time. Use when the user asks how something flows, what happens when they click/send/call X, for a stack or call trace, or when they invoke /trace."
---

# Trace

Print how a named feature actually runs through the codebase right now: entry
point → each hop → side effects → return. Not an architecture essay. Not a
remembered path from an earlier chat.

This skill is **agent-agnostic**. The same procedure applies in any harness
(CLI, IDE chat, headless). Prefer a smaller explore-style subagent for the
walk when the harness can delegate; otherwise walk the code yourself with the
same rules.

---

## When to use it

- The user names a feature or action and wants the path ("what happens when…",
  "how does send work", "show me the call stack for…").
- They invoke `/trace` (optional flags below).
- You are about to explain a cross-layer flow and a diagram would beat prose.

Do **not** use this for "why did we design it this way" — that is
[`system-architect`](../system-architect/SKILL.md). Do not use it to find a
bug — that is [`method`](../method/SKILL.md). Trace answers *what runs*.

---

## Procedure

1. **Name the feature and the entry point.** One sentence. If several entries
   exist (UI, CLI, RPC), ask which one — or trace each as a separate tree.
2. **Delegate the walk** to a smaller explore subagent when available. Brief it
   with: the feature, the suspected entry, "re-read the repo, follow real call
   edges only, return every branch as a full path, use symbol names from the
   code." Do not accept a prior chat's trace as input.
3. **Always re-read source.** Grep and open the current files. Never paste a
   cached or remembered path as truth.
4. **Follow every branch that can run** for that feature: happy path, early
   returns, auth/connect failures, reject/error handlers, idle/guard exits.
   Each branch is its own tree (Path A, Path B, …). Partial trees are wrong.
5. **Stop at meaningful hops.** Include module boundaries and named functions
   the reader must know. Skip trivial one-line forwards unless they change
   ownership or cross a process/network boundary.
6. **Render** with the rules below. Present the result; do not bury it under
   commentary. A short header is enough.

---

## Render rules

**Default to ASCII.** Use mermaid only when (a) the user asks for it, or (b)
the surface is clearly a rich UI that renders mermaid (e.g. GitHub markdown,
IDE chat known to render it). If unsure → **ASCII only**. Never default to
both.

Flags (when the user passes them): `--ascii`, `--mermaid`, `--both`. Explicit
flags always win.

### ASCII (default)

Layer depth with `|` and `|----->`. Group related hops in a box labeled by
architectural layer (UI, store, client, wire, server, DB, … — use the names
the codebase already uses). `//` notes are for state or UI side effects only.

```text
# Trace: <feature>
Entry: <symbol or UI action>
Source: live from repo (not cached)

## Path A — <label>

|
|  [ <Layer> ]
|     <EntrySymbol>
|-----> <next>
|-----> <next>                      // side effect
|
|  [ <Layer> ]
|-----> <next>
|-----> <boundary crossing>
|
|  [ <Layer> ]
|-----> <handler>
|-----> <return / reply>
|
|  [ <Layer> ]
|-----> <completion>
|         <observable effect>
```

Same feature, other outcomes → `## Path B — …`, full trees, not footnotes.

### Mermaid (when allowed)

Same hops as `flowchart TB` with one subgraph per layer. Prose header first;
diagram second. Keep node labels as code symbols.

See [format](references/format.md) for a worked example and mermaid twin.

---

## Output checklist

- [ ] Header names the feature and entry
- [ ] Every runnable branch has its own full path
- [ ] Symbols match the code (no paraphrased names)
- [ ] Cross-process / network hops are explicit
- [ ] Render is ASCII unless mermaid was justified
- [ ] Trace was regenerated from current source

## Gaps

If the path dies at a stub, a local-only store, or a missing server type, say
so in one line under the tree — do not invent the next hop.
