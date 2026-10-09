# Architecture decision records

One record per decision that is expensive to reverse. Keep the decision and
its reasons as history: when the decision changes, write a new record that
supersedes it. Follow the repository's identity and lifecycle convention.
Track current delivery status and evidence separately, and update them using
the repository's convention. Label and date them. The history tells you whether
the original constraints still hold, while current evidence tells you what has
shipped.

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

Keep the decision short. Put detailed mechanics and evidence in linked design
documents; split the record when it contains independent decisions.

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

## Reconciling records with the system

**Compare the decided scope, the shipped slices, and their evidence separately.**
Accepted is not implemented, and implemented is not verified on every platform.
For each promised slice, name the owner, current implementation and evidence,
with the remaining gates. A schema can exist before its consumer renders,
executes or authorizes it. Rejected alternatives and deferred improvements are
not unfinished requirements unless the decision included them.

**Repair the contradiction wherever readers encounter it.** Check the header,
current-state prose, delivery tables, checklists, index, linked README and
tracking issue. A corrected header does not repair a stale body. Describe the
exact claim that disagrees with current evidence and the bounded correction;
do not rewrite an accepted decision to make a code defect look intentional.

**Check the inventory as a structure.** Records need unique identities and
placement consistent with the repository's inventory convention. Keep decision
acceptance separate from delivery completion when choosing a lifecycle section.
A stray link elsewhere is not index coverage. A move preserves supersession
history and incoming references. Keep shared-index edits narrow, reread after combining changes,
and check the resulting tree rather than each patch in isolation.

Before filing a finding, compare existing issue ownership and the exact sections
changed by open pull requests. Touching the same document does not prove the
contradiction is fixed. Pin the inspected revision and distinguish inspected
code, reported checks, checks you ran and unknown coverage, following
[method](../../method/SKILL.md#2-verifying).
