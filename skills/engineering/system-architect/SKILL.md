---
name: system-architect
description: "How to design and structure a codebase so the next change stays cheap: one authority per fact, information ownership, clear boundaries, separating mechanism from policy, a small core with product capability composed on top, invariants and failure first, owner-keyed state, and why product velocity depends on structure. Use before writing a new module, before adding a dependency between two parts of a system, when a change starts touching more files than it should, when boundaries or layering are being discussed, or when reviewing anything that spans more than one file."
---

# The System Architect

Keep the codebase cheap to change. Codebases slow down when nobody knows where
a rule lives, or when two modules rely on each other's internals and neither
can move. Performance, reliability, and product speed all come from a system a
person can understand one piece at a time.

This skill owns the design layer. Single-change workflow lives in
[`coding`](../coding/SKILL.md), test rules in
[testing](../coding/references/testing.md), and change descriptions and reviews
in [`pull-requests`](../pull-requests/SKILL.md).

## 1. Prime directive

Build the smallest system where each piece has one clear job, owns the
information it needs, and can change on its own. Judge every design by the cost
of the *next* real change, and add flexibility only when a real need asks for it.

- **Easy to delete beats easy to extend.** If you cannot explain how to remove
  a module cleanly, its boundary is tangled.
- **Boring is a feature.** Pick the well-understood mechanism unless
  measurements prove you need a complex one.
- **Protect local reasoning.** A reader should understand one file without
  holding the whole system in mind. Implicit ordering, shared mutable state,
  and "remember to also update X" are defects even when they work.

### Core rule 1: every fact has one authority

Every fact the system relies on has one place in charge of it: that place
creates, decides, changes, checks, and ends it. Everything else asks that place
or uses what it handed out. Bugs start when a second place guesses, keeps a
copy, re-checks the rule, or patches the value downstream, and the two disagree.

For every fact your change touches, ask:
1. **Who makes it?** Make values valid at creation; downstream repair is guessing.
2. **Who decides it?** One function decides; callers use its answer.
3. **Where does every path pass?** Put the rule at the one gateway nobody can bypass.
4. **Who ends it?** Close, cancel, cleanup, and once-only claims move with ownership.
5. **Where is the promise made?** Test the guarantee where consumers rely on it.
6. **Fact or proxy?** Ask the authority directly rather than inferring from a handle, flush, or env var.

Examples (full 31-row index in [core-rule-examples](references/core-rule-examples.md#core-rule-1-every-fact-has-one-authority)):

| What went wrong | Who should be in charge | Rule |
| --- | --- | --- |
| One caller checks "rebuild needed", another skips it, showing stale data | The one gateway every request passes | [Put a rule where every path has to pass](../coding/SKILL.md#3-failure-first) |
| Code checks "has a terminal handle" when it means "owns the process" | The fact itself, stored directly | [Store the real fact](#4-tactical-rules-inside-a-context) |
| Dropping a handle is expected to stop a background task, and it keeps running | Whoever holds the resource now | [Hand off the off switch too](#9-failure-and-invariants-first) |

### Core rule 2: a check only holds for what it looked at

A check, promise, or stored fact is valid only for the exact thing, moment, and
conditions it inspected. Bugs start when a "yes" travels across a lookup,
redirect, queue, `await`, different machine rules, or another request's context.

For every check or stored fact you rely on, ask:
1. **Same thing?** Is what you checked the exact value you use after lookups or conversions?
2. **Same moment?** Could it have changed across a delay, queue, `await`, or re-entry?
3. **Same rules?** Does the consumer share the same machine, ordering, units, and phase?
4. **Same scope?** Does it belong to this copy, request, or user without leaking?
5. **Still justified?** Re-verify locks, caches, and shortcuts whenever sharing changes.

If any answer is no, check again at use or take the slower safe path. Examples
(full 18-row index in [core-rule-examples](references/core-rule-examples.md#core-rule-2-a-check-only-holds-for-what-it-looked-at)):

| What went wrong | What the check should have covered | Rule |
| --- | --- | --- |
| A queued update runs after its target was deleted and crashes | The target when work runs, not when queued | [What you saw is a clue](../coding/SKILL.md#3-failure-first) |
| A host name passes a permission check, then resolves to a blocked IP | The resolved address at the step that uses it | [Check the thing you will use](../coding/SKILL.md#3-failure-first) |
| First request fills a shared cache with its own base path, breaking later ones | Only request-independent data; each request brings its context | [A cache key must include everything that changes the result](references/patterns.md#derived-state-and-accelerators) |

When a bug teaches a new lesson, map it to Core rule 1 or 2 and add a row to
[core-rule-examples](references/core-rule-examples.md) before adding a new rule.

## 2. How you decide

Run these in order and stop at the first step that settles it; never skip 1 or 2:

1. **Who has the information?** Put the logic there. If a caller passes facts
   so a callee can branch, move the branch to the caller; if the callee knows
   what the caller guessed, move it to the callee. Exception: a check another
   thread can invalidate stays with the state owner under one lock.
2. **What is the product concept?** Name it in the product's own words.
3. **Which area owns it?** One concept lives in one area; two areas usually
   mean two concepts sharing a word.
4. **What must stay true, and who enforces it?** Name the enforcer.
5. **Who picks the strategy?** The wiring edge picks native, polling, remote,
   or fake; a mechanism owns multiple strategies only if runtime switching is
   its job.
6. **What is the smallest thing that works?** Build that, not a framework.
7. **How does it get deleted?** Removing it should touch its module and one adapter.
8. **What does it cost to be wrong?** Reversible choices go in the PR;
   expensive ones get a written note first (§14).

## 3. Domain first

- **Use the product's words.** If product says "turn" and code says
  `MessagePair`, rename the code so nobody translates in their head.
- **Split by meaning, not technical layers.** A real boundary has different
  vocabulary, rate of change, and reasons to change on each side, and you can
  rewrite one side alone. A fake boundary is named `utils`, `helpers`, `common`,
  `types`, `services`, or `managers`, gets edited on both sides by every
  feature, or passes the whole state object across.
- **Keep dependencies one-way.** Map every area and arrow on one page: A knows
  B or B knows A, never both. Fix cycles first.
- **Keep shared code tiny.** Anything shared across areas is jointly owned and
  hard to change. Limit it to small value types and versioned contracts; keep
  mutable ownership local. A remote mirror may keep foreign IDs only under a
  versioned contract with explicit generation and reconnect rules.

## 4. Tactical rules inside a context

- **Group things that must change together.** Keep each consistency group
  (aggregate) small — one main record plus its owned helper values. Reference
  other groups by id only, update one group per transaction, and treat
  cross-group rules as eventually consistent or as application-layer policies.
- **Wrap raw primitives with meaning.** Give session ids and durations their
  own types so the compiler catches mix-ups.
- **Put the rule where the data is.** Move caller preconditions ("only call
  while streaming") into the callee and return what happened. Handle the empty
  case cheaply inside the owner instead of making callers check `Option`.
- **Store the real fact.** Store "owns process" or "can be focused" directly
  rather than inferring it from a terminal handle or tab order.
- **Keep tags with the fact.** Origin, visibility, and certainty are part of
  the value; deduplication and caches must keep them with an explicit merge
  rule ("visible if either is visible").
- **Enforce invariants in the owner.** Make constrained fields private,
  document the rule, and enforce it across every constructor and mutator in the
  public API (e.g., queries must handle elapsed time past a shortened timer).
- **Keep business rules in domain objects and orchestration thin.** Application
  code loads, calls, saves, and publishes; domain branching stays in domain
  objects. Keep storage, transport, and UI out of business rules.

## 5. The three separations

- **Mechanism from policy.** Reusable machinery holds no product rules (a
  scheduler runs work; policy picks priority). Change a rule without editing
  machinery, and let two operations on one pool follow different rules (flush
  output at shutdown vs wait for input).
- **What from how.** Callers state intent ("deliver this reply"), and the
  system picks execution (task, polling, retries) so execution can change
  without rewriting callers.
- **Description from running state.** Keep a workflow or job definition as
  inspectable data separate from live run state so you can diff, version,
  serialize, test, replay, and update definitions independently.

## 6. Small core, composable pieces

Everything depends on the core, so measure it by how much someone must learn
before writing anything.

- Add to the core only when at least two independent consumers need it and it
  has no good home outside.
- Extend by adding a piece rather than adding parameters, branches, or flags to
  core types; prefer small single-job pieces over one piece with a mode switch.
- The one valid mode switch is a temporary rollout seam for replacing a core
  mechanism (scheduler, queue, storage engine); its parity, drain-protocol, and
  removal rules live in [patterns](references/patterns.md#seams).
- Wire concrete pieces at the edge so pieces stay unaware of each other; to
  pull a leaked choice back to the edge, see [patterns](references/patterns.md#structure).

## 7. Structure

- **Stay flat by default.** Use one level of modules named after what they do.
  Add a second level only for named variants (like input kinds) with shared
  helpers in the parent; never split directories just to shorten files. Naming
  and re-exports live in [structure](references/structure.md#naming).
- **Dependencies point inward.** Adapters depend on application, which depends
  on domain. Application defines ports and adapters implement them.
- **Areas talk through contracts.** Prefer domain events; for direct calls, go
  through a caller-defined port.
- **Test architectural absences** (no domain import from adapters, no cycles,
  no `utils`, no ambient singletons) and **apply cross-cutting concerns once at
  the boundary**. Full layout and process boundaries live in
  [structure](references/structure.md).

## 8. Vertical isolation

Product features sit on top of the core, never inside it. Even when a one-line
core hack takes an hour and composing on top takes a day, take the day so the
core does not learn about individual features.

- Keep product `if` branches, feature-named variants, and single-surface fields
  out of the core; features depend on the core, never the reverse.
- When a feature needs a new capability, add a general hook or port in the
  core's own vocabulary. If you cannot describe it without naming the feature,
  it is not general enough.
- Quick test: could the core serve a product without this feature? Apply the
  same rule to shared app surfaces: never special-case one caller.

## 9. Failure and invariants first

Design for crashes, retries, duplicates, and races before the happy path:
- **Stops halfway?** Make the transition atomic, or partial state detectable and repairable.
- **Runs twice?** Make it safe to repeat, or detect repeats by identity.
- **Two run at once?** Impossible by construction, serialized by one owner, or
  a documented benign race. "Unlikely" is not an answer.

Operational rules live in [`coding`](../coding/SKILL.md#3-failure-first).
Structural rules:
- **Make broken states unrepresentable** with types, **name the enforcer** for
  every invariant, and **restructure until you can argue the guarantee in a
  paragraph** (state and test unstated guarantees so refactors keep them).
- **Key owned state by its owner first.** Put the principal (tenant, session,
  window, user, plugin) before the local id in the key, or type state by owner,
  so a guessed id cannot reach someone else's data. For capability tokens
  combining identity and authority, see
  [patterns](references/patterns.md#feature-and-capability-gating).
- **Hand off the off switch too.** Give background tasks and child processes an
  explicit cancel, close, or reset path and follow it to the promised external
  effect or resource release; dropping a local handle proves neither.
- **Treat migrations as a semantic dependency graph** and **track escape-hatch
  flags as debt** (distinct from rollout seams); see
  [patterns](references/patterns.md#evolving-the-core).

## 10. What you refuse to build

- Single-use abstractions (wait for the second real use of the same idea).
- Unrequested flags, generic frameworks for specific problems, or pass-through
  layers that neither hold a rule nor flip a dependency direction.
- Hidden control flow (silently no-oping on global state), unmeasured
  performance work, unexamined dependencies (check if one was removed before),
  or shortcuts reaching into another module's internals.

## 11. Tests are a design instrument

Hard-to-test code is badly coupled. Match each test to its risk: fast unit
tests on real domain objects, integration tests against real dependencies for
use cases, consumer-owned contract tests at module boundaries, module-graph
tests for absences, and deterministic seams for concurrency or time. Route
time, randomness, filesystem, network, and concurrency through one internal
module each, and fake the lowest external mechanism rather than your own
orchestration. Full test rules live in [testing](../coding/references/testing.md).

## 12. Velocity is a structural property

Product speed is how many changes can land independently without coordination:
merge small changes fast, keep main shippable, aim for common changes to touch
one file (counting *decisions* after subtracting moves, generated files, and
formatting), and evolve seams additively before removing old paths. See
[`pull-requests`](../pull-requests/SKILL.md#size-and-shape) and
[velocity](references/velocity.md).

## 13. Performance and scale, when they matter

Performance method lives in [`coding`](../coding/SKILL.md#5-performance).
Structurally: mark and measure hot paths; pass expensive resources explicitly;
batch at boundaries without widening payloads; bound every queue at its owner
with defined full-queue behavior; keep accelerators (caches, indexes, bloom
filters) behind their own boundary with stated error direction
([patterns](references/patterns.md#derived-state-and-accelerators)); treat
benchmarks as regression tests rather than proof; and add observability before
regressions happen.

## 14. Write the decisions down

Code shows *what*, not *why* or what you rejected. Keep a one-page architecture
map updated with each structural change
([structure](references/structure.md#an-architecture-map)), record non-trivial
choices in [adr](references/adr.md), and write the design note and what you
chose not to do before large or hard-to-reverse work
([`pull-requests`](../pull-requests/SKILL.md#say-what-you-deliberately-did-not-do)).

## 15. Review, checklist, and smells

Use [review-and-smells](references/review-and-smells.md) for the architect's
review questions, pre-write checklist, and 15 boundary smells. General review
standards live in [`pull-requests`](../pull-requests/SKILL.md#reviewing);
pre-PR checks live in [`coding`](../coding/SKILL.md#8-finishing-and-reporting).

## Where the rest of this lives

- [core-rule-examples](references/core-rule-examples.md): full bug-to-rule index for Core rules 1 and 2.
- [structure](references/structure.md): layout, absences, process boundaries, growing a module, architecture map.
- [patterns](references/patterns.md): structure, seams and rollout seams, capability gating and tokens, derived state, concurrency, migrations, escape hatches, evolving the core.
- [velocity](references/velocity.md): diagnostics for structural health.
- [adr](references/adr.md): when to write a decision record, template, and reconciliation.
- [review-and-smells](references/review-and-smells.md): architect review questions, pre-write checklist, and boundary smells.
- [`coding`](../coding/SKILL.md), [`pull-requests`](../pull-requests/SKILL.md), [`method`](../method/SKILL.md): the change, its description, and the proof.
