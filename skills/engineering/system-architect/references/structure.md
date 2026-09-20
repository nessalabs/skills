# Structuring a codebase

The rules in [../SKILL.md](../SKILL.md) turned into concrete layout.
Language-agnostic: the names below are roles, not directory names you must
use.

## When to apply this

A five-file module does not need a four-layer split, and imposing one early is
its own kind of damage. The trigger for the structure below is a concept
acquiring **an invariant**, **a second consumer**, or **its own persistence**.
Until then, one well-named file is correct.

## Shape

```
<context>/
  domain/         rules, entities, value objects, events. Imports nothing outward.
  application/    use cases and the ports (interfaces) they need. Imports domain only.
  adapters/       implementations of those ports: storage, transport, OS, UI, network.
  contracts/      what other contexts may see. The only public path.
```

Everything except `contracts/` is private to the module. Other modules import
`contracts/` and nothing else. This is the single most valuable rule here,
because it is the one that stops a change to one feature from becoming a
change to five.

## Dependency direction

```
adapters  ──────►  application  ──────►  domain
(storage, UI,      (use cases,           (rules,
 OS, network)       orchestration)        invariants)
```

The arrow never reverses. The domain does not import the application. The
application does not import an adapter; it declares the **port** it needs, and
an adapter satisfies it. If an import in a diff crosses these arrows the wrong
way, that is the review comment, before correctness, before style.

## Naming

- Folder name == module name == the domain concept, in the product's words.
- No `utils`, `helpers`, `common`, `shared`, `core`, `types`, `misc`. If you
  cannot name a module after what it *is*, you have not found the concept.
- One canonical import path per item. No re-exports creating a second route.
- Flat beats nested.

## The absences

The most valuable architectural rules are things that must *not* exist. They
are invisible in the code, which is exactly why they erode. Write them down,
then make them a test.

1. The domain layer imports nothing from adapters: no transport types, no
   framework types, no filesystem, no runtime.
2. No module imports another module's non-`contracts` path.
3. The module graph is acyclic.
4. No global mutable state, service locator, or ambient singleton. Dependencies
   arrive as parameters, first position.
5. No test-only constructor or test-only visibility that builds a state
   production cannot.
6. No unbounded queue, channel, buffer, or retry loop. Each has a bound and a
   documented behaviour at the bound.
7. Nothing outside an adapter knows the shape of a stored record, a wire
   message, or a UI framework type.
8. No lookup by a bare local id into state that belongs to a principal. The
   owner is part of the key.

Once the codebase is large enough for these to be worth automating, they
become a structure test over the module graph (see
[testing](../../coding/references/testing.md#structure-and-placement)). That
converts a recurring review comment into a red build: reviewers spend attention
on design, machines spend it on rules.

## Cross-context communication

Prefer publishing a fact over issuing an instruction. When one context needs
another to act, it publishes what happened ("reply completed") rather than
telling the other what to do ("update the transcript"). The publisher has no
knowledge of who reacts, and the set of reactors can change without touching
it.

Direct calls are acceptable when the relationship is genuinely a dependency
rather than a collaboration, but **the caller defines the interface and the
callee implements it**, so the arrow points where the design wants it, not
where the file happens to live.

## Rules for a process or bundle boundary

Any seam between two runtimes (a host and a UI, a server and a client, a
worker and a page) rots silently unless these hold.

- **One definition of every payload shape, imported by both sides.** Never
  redeclare the shape on the receiving side: the two compile happily and drift
  until runtime. Generate one side from the other, or hand-write one
  declaration both import.
- **Everything crossing the seam is an explicit message**, never shared state.
- **Preserve the natural representation.** Bytes that are already bytes do not
  become text and back because the convenient channel takes text. Text may be
  the correct stable contract; accidental amplification is what to avoid.
- **Guard the seam so the far side can run without the near one**, if that is
  a supported mode. It is worth a build-matrix job, because it breaks quietly.
- **Validate at the boundary, then trust inwards.** Parse untrusted input into
  a domain type once, at the edge.
- **Pass the first payload in.** State the far side needs to do its first
  useful work arrives with it, not as a round trip afterwards.
- **Authority travels with the message, not with a guessable id.** A response
  queue, a session table, or a resource map shared across principals is keyed
  by the principal first.

## Growing a new context

1. Write the name and its one-sentence purpose in the architecture map first.
   If it is hard to write, stop.
2. Create the domain with the invariant enforced in a constructor, and a test.
3. Add the use case, with an interface for anything it needs from outside.
4. Implement that interface in an adapter.
5. Expose the minimum in `contracts/`.
6. Wire it in **exactly one composition point**.

Step 6 matters most: there is one place where concrete adapters are chosen and
handed to use cases. Everything else receives what it needs. That single place
is what makes the system testable and what makes swapping an edge a one-file
change.

## An architecture map

Keep a one-page document, read by everyone, updated rarely, containing:

- The bird's-eye view of the problem.
- A **code map** naming each module and what it owns: a country map, not a
  street atlas.
- The **invariants**, especially the absences above.
- The **boundaries** and what crosses them.
- The **cross-cutting concerns** and where each is implemented once.
- A **"where do I make this change"** table. This answers the question that
  costs new contributors the most time, which is never "how do I write this"
  but "where does it go".

Name files and types without linking to line numbers, so it does not rot.
Update it in the same change that invalidates it, or not at all: a stale map
is worse than no map, because people trust it.
