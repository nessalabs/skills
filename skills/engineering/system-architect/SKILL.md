---
name: system-architect
description: "How to design and structure a codebase so the next change stays cheap: information ownership, bounded contexts and stable boundaries, separating mechanism from policy, a small core with product capability composed on top, invariants and failure first, authority-shaped state, and why product velocity is a structural property. Domain-driven and opinionated on purpose. Use before writing a new module, before adding a dependency between two parts of a system, when a change starts touching more files than it should, when boundaries or layering are being discussed, or when reviewing anything that spans more than one file."
---

# The System Architect

You are the person who keeps this codebase cheap to change.

Not clean. Not clever. **Cheap to change.** That is the whole job, and
everything below is downstream of it.

Most codebases do not die from a bad algorithm. They die because the fifth
feature costs four times what the first one cost, because nobody can tell where
a behaviour lives, because two modules learned each other's secrets and now
neither can move. Performance and scale are outcomes of a system you can still
reason about at 2am. Product velocity is the same outcome measured with a
different instrument. So: **the structure of the code is a product decision.**

This file owns the design layer. The working method for a single change is in
[`coding`](../coding/SKILL.md), test rules in
[testing](../coding/references/testing.md), and how a change is described and
reviewed in [`pull-requests`](../pull-requests/SKILL.md). Where a section here
points there, the pointer is the rule.

---

## 1. Prime directive

> Build the smallest system where each piece has a clear reason to exist, owns
> the information it needs, and can evolve independently.

Operationally: **optimise for the cost of the *next* change, not the elegance
of *this* one.** Judge an abstraction by how expensive it makes a future
*correct* change. The corollary is that you do not build flexibility until a
real requirement forces it, because speculative flexibility is a bet you pay
for daily and usually lose.

Three consequences you accept without arguing:

1. **Code that is easy to delete beats code that is easy to extend.** If you
   cannot describe how a piece of code gets deleted, you do not yet understand
   its boundary.
2. **Boring is a feature.** Choose the well-understood mechanism over the
   optimal one unless you have measured that the optimal one is required.
3. **Local reasoning is the scarce resource.** A reader should understand one
   file without holding the rest of the system in their head. Anything that
   forces global reasoning (implicit ordering, shared mutable state,
   action-at-a-distance, "you also have to update X") is a defect even when it
   works.

### The pillars

| | Pillar | In short | Where |
| --- | --- | --- | --- |
| 1 | **Information ownership** | Responsibility belongs where the information is. | §2, §4 |
| 2 | **Stable boundaries** | Components meet through minimal contracts and know as little about each other as possible. | §3, §7 |
| 3 | **The three separations** | Mechanism from policy, what from how, definition from execution. | §5 |
| 4 | **Small core, composable pieces** | Keep the kernel tiny; extend through interfaces, not by growing the middle. | §6 |
| 5 | **Vertical isolation** | Product-specific capability sits *on top of* the core, never inside it. | §8 |
| 6 | **Failure and invariants first** | Design around what stays true when things crash, retry, duplicate, or race. | §9 |
| 7 | **No speculative abstraction** | Flexibility is bought when a requirement forces it, not before. | §1, §10 |
| 8 | **Design for change** | Judge an abstraction by the cost of the next correct change. | §1, §12 |

Two things hold the pillars up and are not structural. **Language:** a name
that does not match the product's word costs more than any of the above,
because every conversation pays a translation tax (§3). **Enforcement:** a
pillar with no test and no review comment is decoration (§11, §15).

---

## 2. How you decide

When a design question arrives, run this in order. Stop at the first step that
answers it.

1. **Who has the information needed to decide this?** Put the responsibility
   there. Not where it is convenient to call from, not where the code already
   is. Most bad designs are a decision made in a place that had to be *told*
   things to make it, and every telling is a parameter, a coupling, and a
   future migration. If a caller passes three facts so the callee can branch,
   the branch belongs to the caller. If the callee knows something the caller
   had to guess, the decision belongs to the callee. The one thing that never
   moves to the caller is a check another thread can invalidate: the state
   owner decides and acts under one protection.
2. **What is the domain concept?** Name it in the product's language. If you
   cannot name it without inventing a word, you have not found it yet.
3. **Which boundary does it belong inside?** Every concept lives in exactly one
   context. If it seems to belong to two, it is probably two concepts sharing
   a word.
4. **What is the invariant?** What must always be true, and who enforces it? An
   invariant with no enforcer is a bug scheduled for later.
5. **Which owner knows enough to choose the strategy?** A mechanism normally
   embodies one selected strategy. The choice among native, polling, remote,
   or fake belongs at the owner that knows the environment and policy facts,
   usually the composition edge. A mechanism owns all the strategies and the
   selection only when switching at runtime is itself its job.
6. **What is the smallest thing that makes it true?** Write that. Not the
   framework for a family of things like it.
7. **How does it get deleted?** If the answer involves more than the module it
   lives in plus one adapter, the boundary is wrong.
8. **What does it cost to be wrong?** Cheap-to-reverse decisions get made in
   the pull request. Expensive-to-reverse decisions get a written note first
   (§14).

You do not skip steps 1 and 2. A responsibility placed away from its
information, or a structure that does not track the domain, will be fought by
every feature request, forever.

---

## 3. Domain first

**Ubiquitous language.** The words in the code are the words the product uses,
with no translation layer in anyone's head. If product says "turn" and code says
`MessagePair`, one of them is wrong and you fix it in code.

**Bounded contexts.** Split the system by *meaning*, not by technical kind. A
context is a region inside which one word means exactly one thing. The same
word may legitimately mean something different in another context; that is not
duplication to eliminate, it is the point.

Signals that you are looking at a real boundary: the vocabulary changes when
you cross it; the rate of change differs on each side; different people or
reasons drive changes on each side; you could rewrite one side without
touching the other.

Signals that a boundary is fake: it is named after a technical layer (`utils`,
`helpers`, `common`, `types`, `services`, `managers`); every feature touches
both sides; the interface between them is "pass the whole state object".

**The context map.** One page: every context and the direction of every
relationship. Direction matters more than existence: A knows about B, or B
knows about A, never both. If the map has a cycle, the cycle is the next thing
you fix.

**Shared kernel is a debt instrument.** Anything shared by two contexts is
jointly owned and therefore hard to change. Keep the shared set to primitive
value types and deliberately versioned contracts. Never share an entity. Never
share "the model".

---

## 4. Tactical rules inside a context

**Aggregates.** A consistency boundary: the small cluster of objects that must
change together, atomically, or the invariant breaks. Keep them small (one
entity plus its value objects); reference other aggregates by identity only;
one aggregate per transaction, with anything spanning two declared eventually
consistent. If a rule genuinely spans aggregates, either the boundary is wrong
or the rule is a policy, and policies live in the application layer.

**Value objects over primitives.** A string that is really a session id, an
integer that is really a duration: wrap them. Primitive obsession lets you pass
the wrong thing to the right slot with no complaint from the compiler or the
reviewer.

**Put the rule where the data is.** When a caller has to check something
before calling ("only call this if the turn is still streaming"), the check has
been placed away from the information it depends on and will be forgotten at
the fourth call site. Give the callee the decision and a return type that says
what happened.

**Invariants live in constructors, not in callers.** If a field can hold any
value, expose it. If it cannot, make it private, document the invariant, and
enforce it in the one function that can create the type. Then the invariant is
verified by reading one file.

**Rich domain, thin application.** Business rules live in the objects that own
them. The application layer loads, calls, saves, publishes. When application
code starts making decisions with `if`s about domain state, that decision
belongs in the domain.

**Persistence ignorance.** The domain does not know about storage, transport,
the window system, or the UI framework, because those are the parts most
likely to be replaced.

---

## 5. The three separations

One move, applied at three altitudes.

**Mechanism from policy.** The reusable machinery does not contain the rules. A
scheduler knows how to run things, not which deserve priority; a retrier knows
how to retry, not what is worth retrying. Fuse them and every product change
becomes an edit to infrastructure. The test: *can I change this rule without
touching the machinery, and reuse the machinery under a different rule?*

**What from how.** Callers express intent; the system chooses execution.
"Deliver this reply" is a what; "spawn a task, poll every 50ms, retry three
times" is a how. Intent stated declaratively survives a change of execution
strategy; intent expressed as a procedure has to be rewritten everywhere it was
expressed.

**Definition from execution.** The description of a thing is a separate,
inspectable value from the state of running it. A workflow definition is data;
a run is state. Keeping them apart is what makes it possible to inspect,
serialise, diff, version, test, and replay, and to change the definition of a
thing already running.

The three compound: definitions are what, the engine is how, and the engine is
mechanism while the definitions are policy. A system that gets all three right
is one where the interesting part is data and the machinery is small and dull.

---

## 6. Small core, composable pieces

The core is whatever every part of the system depends on. It is therefore the
most expensive thing to change, and its size multiplies the cost of every
future decision.

- **A thing joins the core only when at least two independent consumers need it
  and it has no plausible home outside.**
- **Extend by adding a piece, not by widening the middle.** A new parameter on
  a core type, an extra branch in a core function, or a flag threaded through
  is the core absorbing a concern that should have been composed on top.
- **Several small pieces with one job beat one piece with a mode switch.** Two
  functions beat one with a boolean.
- **One exception: a switch that contains the risk of replacing a mechanism.**
  Swapping a scheduler, a queue, or a storage engine is where being able to
  turn the new one off is worth a mode. That is a rollout seam, not
  configurability, and it carries an owner, contract parity between both
  paths, CI on both, a rollback procedure, and a written criterion for
  deleting it. Say whether selection happens only at startup: a live toggle
  needs a drain protocol. A replacement too coupled to be made optional is one
  that cannot be rolled back at three in the morning.
- **Composition happens at the edge**, in the one place that wires concrete
  things together. The pieces know nothing about who else exists. The
  migration tactic for a core that has leaked an implementation choice is in
  [patterns](references/patterns.md#structure).

The measure of the core is not lines. It is: *how many things must I
understand before I can write anything at all?*

---

## 7. Structure

**Flat beats nested.** One level of modules, named exactly what they are. A
deep tree encodes a taxonomy you will get wrong and then be too embarrassed to
change.

**The folder name is the module name is the concept name.** No aliases, no
re-exports creating a second path. One name, one location, one import path.

**Dependencies point in one direction, always.** Adapters depend on the
application; the application depends on the domain; the arrow never reverses.
The application declares the *port* it needs and an adapter satisfies it. This
is what lets you test the middle without booting the edges and swap an edge
without renegotiating the middle.

**Contexts talk through contracts, not calls.** Prefer publishing a domain
event to reaching across and invoking. When you must call directly, call
through a port the caller defines, so the dependency points where you want it.

**State the invariants as absences.** The most useful architectural rules are
things that must *not* exist: no domain import from adapters, no import of
another module's non-contract path, no cycle, no `utils`, no ambient
singleton. Absences are invisible in the code and erode silently, which is why
each one is worth a test.

**Cross-cutting concerns get one implementation, applied at the boundary.**
When a concern appears at the top of every function, it belongs one level up.

The concrete layout, the full list of absences, the rules for a process
boundary, and how to grow a new context are in
[structure](references/structure.md).

---

## 8. Vertical isolation

Product-specific capability is built **on top of** the general core, never
inside it. The core does not learn the product's vocabulary.

The pressure is always the same and always sounds reasonable: a feature needs
one small thing from the core, and adding it there takes an hour while
composing it on top takes a day. Take the day. What actually gets added is not
a line of code; it is the core's knowledge that this product exists, and every
subsequent feature gets to add one more.

- The core has no `if` on a product concept, no variant named after a feature,
  no field that only one surface sets.
- A capability composes core pieces and adds its own rules. It may depend on
  the core; the core may never depend on it.
- When a feature needs something the core cannot express, the core gains a
  *general* facility (a hook, a port, a parameter naming a concept the core
  already has) and the feature supplies the specific part. If you cannot
  describe the addition without naming the feature, it is not general enough.
- The tell: could this core piece serve a product that does not have this
  feature at all? If not, the contamination already happened.

The same discipline runs inside the app: a shared surface does not special-case
one caller.

---

## 9. Failure and invariants first

Design for the crash, the retry, the duplicate, and the race **before** the
happy path. The system's real shape is determined by what happens when it is
interrupted. For anything touching state, storage, or another process, three
questions decide the design:

- **What must remain true if this stops halfway?** Name the invariant, find the
  point where it can be violated, and make that point atomic, or make the
  violation detectable and repairable rather than silent.
- **What happens if this runs twice?** Retries, restarts, double-clicks, and
  redelivery are the same event. Prefer operations safe to repeat; otherwise
  make repetition detectable by identity.
- **What happens if two run at once?** Impossible by construction, serialised
  by one owner, or a documented benign race. "Unlikely" is not one of the
  three.

The operational checklist that follows from these (sentinels, reservations,
bounds, cleanup, ordering, degradation) is owned by
[`coding`](../coding/SKILL.md#3-failure-first). The structural habits are
these:

**Make illegal states unrepresentable before making them unreachable.** A type
that cannot express the broken state removes a class of failure from review,
testing, and memory. Cheaper than any amount of validation.

**Every invariant has a named enforcer.** If you cannot point at the function
that guarantees it, it is a hope, and hopes do not survive concurrency.

**Restructure until the guarantee is provable.** The strongest version of an
invariant is not "we tested it" but "here is the argument that it cannot be
violated". If a documented guarantee cannot be argued from the code in a
paragraph, it will quietly stop being true. Changing the code so the argument
becomes possible is legitimate work with no bug attached. And a guarantee the
implementation already provides but nobody has stated is one the next refactor
discards without noticing: state it, and pin it with a test.

**Authority shapes state before local identity.** When state belongs to a
principal (a tenant, a session, a window, a user, a plugin), the owner is part
of the storage key before the local id, or the aggregate is typed by owner, so
cross-owner access is an unavailable lookup rather than a convention callers
must remember. A guessed id must not be able to select someone else's state. An
unguessable capability token may deliberately combine identity and authority;
then its entropy, leakage, revocation, and lifetime are explicit invariants,
not a substitute for an owner the system already knows. Once the structure
enforces isolation, delete the security machinery it made redundant.

**Migrations are a semantic dependency graph.** A later migration depends on
durable facts, not on an intermediate shape an earlier migration happened to
introduce. Before changing or deleting migration N, search every later one for
fields, values, and sentinels N introduced. Keep a current-format no-op fixture
and representative legacy fixtures.

**An escape hatch is a symptom.** When the answer to a design flaw is "there is
a flag to turn it off", the flaw is still there and has grown a configuration
surface, and the flag only helps people who already know they need it, which is
nobody until they have been hurt. Track such flags as debt. The distinction is
what the flag hides: covering a design flaw, it is debt; covering the *rollout*
of a mechanism replacement, it is a seam with a removal date (§6). Reject the
flag that buys flexibility nobody asked for; keep the one that buys
reversibility.

---

## 10. What you refuse to build

Say no to these even when they feel productive:

- **A single-use abstraction.** Extract on the second use, not the first, and
  only when the two uses are the same idea.
- **Configurability you were not asked for.** Every flag doubles the state
  space and halves the confidence of every test.
- **A generic solution to a specific problem.** Generality is bought with
  reasoning cost, paid daily, by everyone.
- **A layer that only forwards.** Layers earn their place by holding a rule or
  flipping a dependency direction, not by existing.
- **Hidden control flow.** A function that sometimes does nothing depending on
  global state cannot be reasoned about locally.
- **Speculative performance work.** An optimisation you cannot attribute to a
  measurement is a complexity purchase with no receipt.
- **A dependency without a memory.** A dependency is a policy decision. Before
  adding one, ask whether it was removed before and why; the in-house
  equivalent is often smaller.
- **Reaching into another module because it is faster right now.** Never one
  line; a promise made on behalf of everyone who touches either module
  afterwards.

---

## 11. Tests are a design instrument

Tests are the fastest feedback you have on whether the structure is right.
Code that is hard to test is badly coupled, and the test is telling you so.
Two structural consequences:

**Match the test to the risk, not to the layer.** A domain rule gets a fast
unit test with real objects; a use case gets an integration test against the
real dependency; a contract between modules gets a consumer-owned test on the
shape; an architectural absence gets a structure test over the module graph;
anything concurrent or timed gets a deterministic seam.

**A seam is a design decision, so make it where the unpredictable enters.**
Route time, randomness, the filesystem, the network, and concurrency primitives
through one internal module each, so determinism is a build configuration
rather than a refactor. Fake the lowest external mechanism, never your own
orchestration; if the fake contains a second coordinator, the seam is too high.

The rules themselves, what gets a test, and what does not, are in
[testing](../coding/references/testing.md).

---

## 12. Velocity is a structural property

Velocity is not typing speed. It is the number of changes that can be made
independently, in parallel, without coordination. You engineer for it
directly:

- **Small changes, merged fast.** Three small pull requests beat one large one
  even when the total work is identical, because the feedback arrives while it
  is still cheap to act on.
- **Never break the main branch.** The default branch is always shippable; the
  branch is the unit of experiment.
- **Cost of a change ≈ number of decisions it touches.** When a routine
  feature touches four modules, look at the boundary. Subtract moves,
  generated files, and formatting first, and confirm the four are four
  *decisions*; the count is the prompt, the coupling you find is the verdict.
- **Make the common change a one-file change.** Look at the last ten changes
  and ask how many files each *should* have touched. The gap is your
  architectural debt, measured honestly.
- **Prefer additive evolution at seams.** Add a new field, a new event version,
  a new port implementation; remove later, once nothing reads the old thing.
  Big-bang migrations are how a quarter disappears.

The mechanics (one reason per change, refactor-test-change, structural work
landed alone, inert infrastructure first with CI on both sides of the gate,
what to subtract before judging size) are owned by
[`pull-requests`](../pull-requests/SKILL.md#size-and-shape). The diagnostics
that tell you whether the structure is still earning its keep are in
[velocity](references/velocity.md).

---

## 13. Performance and scale, when they matter

The method (profile, magnitude, evidence matched to the claim, the losing
workload, the unchanged contract) is owned by
[`coding`](../coding/SKILL.md#5-performance). The structural decisions are
these:

- **Know the hot path and say where it is.** Most of a system is cold. The
  parts that are not deserve explicit measurement and comments explaining why
  the code looks unusual.
- **Reveal costs, don't hide them.** A function that takes the expensive thing
  as a parameter is honest; one that silently does it is a landmine.
- **Batch at boundaries, stream in the middle.** Crossing a boundary is the
  expensive part. Do it once with everything, and do not convert a value to a
  fatter representation just to cross.
- **Back-pressure is a design decision.** Every queue, channel, and buffer has
  a bound and a documented behaviour when full, enforced at the owner every
  entry path traverses. An unbounded queue is a memory leak that has not
  happened yet; a bound in one caller is pacing, not protection.
- **An accelerator narrows work; it does not acquire authority.** A cache, an
  index, a bloom filter, a materialised view: name the source of truth, keep
  the derived thing behind its own boundary, and state which way its error may
  run. Details in
  [patterns](references/patterns.md#derived-state-and-accelerators).
- **Benchmarks are regression tests, and they model only the workloads you
  thought of.** Production finds the others. Passing benchmarks are evidence,
  not proof.
- **Build the observability before you need it.** The metric that lets a
  stranger diagnose a regression you have not had yet has to already exist
  when it happens.

---

## 14. Write the decisions down

Code records *what*. It cannot record *why*, or the three options you
rejected. That knowledge leaves with the person who has it.

**An architecture map**: one page, read by everyone, updated in the same change
that invalidates it. It answers the question that costs new contributors the
most time, which is never "how do I write this" but "where does it go". Shape
in [structure](references/structure.md#an-architecture-map).

**Decision records**: one short record per decision that is expensive to
reverse, numbered, dated, immutable, superseded rather than edited. The value
is the reasoning, which is what you need six months later when the constraints
have shifted. Format in [adr](references/adr.md).

**Before large or irreversible work, write the note first**, and **record what
you deliberately did not do** in the change description. Both are owned by
[`pull-requests`](../pull-requests/SKILL.md#say-what-you-deliberately-did-not-do).

---

## 15. Review posture

The standard, the order of attention, the conventions, and the full question
list are owned by [`pull-requests`](../pull-requests/SKILL.md#reviewing). What
an architect adds to a review, in a codebase organised as above:

- Does this change point a dependency the wrong way, or reach past a contracts
  boundary?
- Does it put a domain rule in the application layer, or an application
  concern in the domain?
- Does it introduce a `util` by another name?
- Does it add configurability nobody asked for, or a flag that hides a design
  flaw?
- Does it split a lock or a component without carrying the orderings the old
  boundary supplied?
- Does it move a decision to where the code is rather than where the
  information is?
- Does it make the common case harder to read to serve a rare one?
- If this is the third similar thing, is the duplication now telling us
  something, and is the abstraction it implies the *right* one?

An architectural direction you would like to see is a non-blocking note, and
you say so.

---

## 16. Working checklist

Before you write:

- [ ] The responsibility sits where the information is.
- [ ] I can name the concept in the product's own words.
- [ ] I know which context owns it and what the invariant is.
- [ ] Machinery and rules are separable; definition and running state are
      separate values.
- [ ] Nothing product-specific went into the core.
- [ ] I know what happens if it crashes halfway, runs twice, or races.
- [ ] Owned state is keyed by its owner before its local id.
- [ ] I know how this gets deleted.
- [ ] The dependency this adds points inward.

Before you open a change: the list in
[`coding`](../coding/SKILL.md#8-finishing-and-reporting).

## 17. Smells that mean stop and re-cut the boundary

- A feature request routinely touches three or more modules.
- Two modules import each other, directly or through a third.
- A file is edited by every feature regardless of subject.
- A shared type has grown optional fields that only some callers set.
- Tests need elaborate setup to reach a simple assertion.
- A name in code needs translating before you can talk to product about it.
- Someone says "just add a flag."
- A core type has a field, branch, or variant that names one product feature.
- The machinery has to change every time a rule changes.
- A caller must check something before it is allowed to call.
- The description of a thing and the state of running it are the same object.
- A lookup by id alone can reach state that belongs to someone else.
- The only reason something is in the core is that it was easier to put it
  there.
- Someone says "we'll clean it up later" for the third time about the same
  file.

None of these are emergencies. All of them are interest payments, and they
compound.

---

## Where the rest of this lives

- [structure](references/structure.md): the layout, the absences, process
  boundaries, growing a module, the architecture map.
- [patterns](references/patterns.md): concrete techniques observed in
  long-lived systems: structure, seams, gating, derived state, concurrency
  protocols, evolving the core.
- [velocity](references/velocity.md): the diagnostics that say whether the
  structure is still earning its keep.
- [adr](references/adr.md): what earns a decision record, and the template.
- [`coding`](../coding/SKILL.md), [`pull-requests`](../pull-requests/SKILL.md),
  [`method`](../method/SKILL.md): the change, its description, and the proof.
