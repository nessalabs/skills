# Architecture decision records

One record per decision that is expensive to reverse. Numbered, dated, and
immutable — when a decision changes, write a new record that supersedes the old
one rather than editing it. The history *is* the value: it is what tells you, a
year later, whether the constraints that produced a decision still hold.

## What earns a record

- A boundary: what a context owns, and what it does not.
- A dependency direction, especially where the obvious direction was rejected.
- Anything costly to undo: a storage format, a wire contract, a concurrency
  model, a persistence choice, a third-party dependency at the core.
- A deliberate exception to a structural rule.

## What does not

- Anything reversible in an afternoon. Decide it in the pull request.
- Style, naming conventions, formatting.
- Restating a rule that already exists elsewhere.

## Template

Keep it to one page. If it needs more, it is probably two decisions.

```markdown
# NNNN. <short decision, as a statement>

- **Date:** YYYY-MM-DD
- **Status:** proposed | accepted | superseded by [NNNN](NNNN-....md)

## Context

What forces are at play — technical, product, team. What made this a decision
rather than an obvious step. State the constraint that actually binds; if there
isn't one, this may not need a record.

## Decision

What we are doing, in the active voice. One paragraph.

## Alternatives considered

Each one with the reason it lost. This is the section future readers come for,
because their question is rarely "what did we do" and almost always "did you
consider X".

## Consequences

What becomes easier. What becomes harder — say this plainly, including the work
we are accepting as a cost. What we would watch for to know this decision has
stopped being right.
```
