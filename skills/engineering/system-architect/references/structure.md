# Structuring a codebase

The persona's rules in [../SKILL.md](../SKILL.md) turned into concrete layout.
Language-agnostic: the names below are roles, not directory names you must use.

## When to apply this

A five-file module does not need a four-layer split, and imposing one early is
its own kind of damage. The trigger for applying the structure below is a
concept acquiring **an invariant** (something that must always be true), **a
second consumer**, or **its own persistence**. Until then, one well-named file
is correct.

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
because it is the one that stops a change to one feature from becoming a change
to five.

## Dependency direction

```
adapters  ──────►  application  ──────►  domain
(storage, UI,      (use cases,           (rules,
 OS, network)       orchestration)        invariants)
```

The arrow never reverses. The domain does not import the application. The
application does not import an adapter — it declares the **port** it needs, and
an adapter satisfies it. This is not ceremony: it is what lets you test the
middle of the system without booting the edges, and swap an edge without
renegotiating the middle.

If an import in a diff crosses these arrows the wrong way, that is the review
comment — before correctness, before style.

## Naming

- Folder name == module name == the domain concept, in the product's words.
- No `utils`, `helpers`, `common`, `shared`, `core`, `types`, `misc`. If you
  cannot name a module after what it *is*, you have not found the concept.
- One canonical import path per item. No re-exports creating a second route.
- Flat beats nested. One level of well-named modules is scannable; a four-level
  tree encodes a taxonomy you will get wrong and then be too embarrassed to
  change.

## The absences

The most valuable architectural rules are things that must *not* exist. They are
invisible in the code, which is exactly why they erode. Write them down, then
make them a test.

1. The domain layer imports nothing from adapters — no transport types, no
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

Once the codebase is large enough for these to be worth automating, they become
a structure test over the module graph. That converts a recurring review comment
into a red build, which is the trade you want: reviewers spend attention on
design, machines spend it on rules.

## Cross-context communication

Prefer publishing a fact over issuing an instruction. When one context needs
another to act, it publishes what happened ("reply completed") rather than
telling the other what to do ("update the transcript"). The publisher then has
no knowledge of who reacts, and the set of reactors can change without touching
it.

Direct calls are acceptable when the relationship is genuinely a dependency
rather than a collaboration — but **the caller defines the interface and the
callee implements it**, so the arrow points where the design wants it, not where
the file happens to live.

## The core and what sits on it

A system that lasts has a general core and product-specific capability built
**on top of** it. The core does not learn the product's vocabulary.

- The core has no conditional on a product concept, no variant named after a
  feature, no field that only one surface sets.
- A capability composes core pieces and adds its own rules. It may depend on the
  core; the core may never depend on it.
- When a capability needs something the core cannot express, the core gains a
  *general* facility — a port, an event, a parameter naming a concept the core
  already has — and the capability supplies the specific part. If you cannot
  describe the addition without naming the feature, it is not general enough.
- The test: could this core piece serve a product that does not have this
  feature at all? If no, the contamination already happened.

The pressure is always the same and always sounds reasonable: a feature needs
one small thing from the core, and adding it there takes an hour while composing
it on top takes a day. Take the day. What actually gets added is not a line of
code — it is the core's knowledge that this product exists, and every subsequent
feature gets to add one more.

## Rules for a process or bundle boundary

Any seam between two runtimes — a host and a UI, a server and a client, a worker
and a page — rots silently unless these hold.

- **One definition of every payload shape, imported by both sides.** Never
  redeclare the shape on the receiving side: the two compile happily and drift
  until runtime. Generate one side from the other, or hand-write one declaration
  both import.
- **Everything crossing the seam is an explicit message**, never shared state.
- **Guard the seam so the far side can run without the near one**, if that is a
  supported mode. It is worth a build-matrix job, because it breaks quietly.
- **Validate at the boundary, then trust inwards.** Parse untrusted input into a
  domain type once, at the edge. Downstream code receives the type, not the raw
  payload plus a promise that someone checked it.
- **Pass the first payload in.** State the far side needs to do its first useful
  work should arrive with it, not as a round trip afterwards.

## Failure-first checklist

Before writing anything that touches state, storage, the OS, or another process:

- What must stay true if it stops halfway? Which function guarantees it?
- What if it runs twice — a retry, a restart, a double input, a redelivery?
- What if two of them run at once? Impossible by construction, serialised by one
  owner, or a documented benign race — pick one. "Unlikely" is not one of the
  three.
- Is the durable write ordered before the announcement?
- What is the bound on every queue, channel, and retry?
- Is this failure fatal or survivable, and is that consistent with the code
  around it? A surface that opens degraded beats a surface that does not open.

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
- A **code map** naming each module and what it owns — coarse-grained, a country
  map not a street atlas.
- The **invariants**, especially the absences above.
- The **boundaries** and what crosses them.
- The **cross-cutting concerns** and where each is implemented once.
- A **"where do I make this change"** table. This answers the question that costs
  new contributors the most time, which is never "how do I write this" but
  "where does it go".

Name files and types without linking to line numbers, so it does not rot. Update
it in the same change that invalidates it, or not at all — a stale map is worse
than no map, because people trust it.
