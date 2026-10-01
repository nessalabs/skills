# Patterns worth stealing

Concrete techniques observed in long-lived, high-performance systems: runtimes,
HTTP stacks, search engines, editors, application frameworks. These are the
implementation-level moves behind the principles in [../SKILL.md](../SKILL.md).
Each is the general idea, not the case it came from; each is cheap to adopt and
has a clear reason to exist.

Rules about testing live in [testing](../../coding/references/testing.md), about
describing and reviewing a change in
[`pull-requests`](../../pull-requests/SKILL.md), and about performance method in
[`coding`](../../coding/SKILL.md#5-performance). Nothing here repeats them.

---

## Structure

**The dependency graph is a strict DAG of libraries with the product at the
top.** The most maintainable large codebases are a set of independent libraries
plus a thin binary that composes them. The binary depends on everything.
*Nothing depends on the binary.* If you cannot draw that picture, the product
has leaked into the libraries.

**The abstraction module depends on nothing.** A small module in the middle
defines only the port and has zero internal dependencies. Implementations
depend on it; consumers depend on it; neither knows about the other. This is
what makes two competing implementations pluggable without either knowing it
has a rival.

**Runtime-agnostic by defining ports, not by abstracting late.** A library
defines the traits it needs from the outside world (how to spawn, sleep, read,
write) and ships the adapters for a specific environment in a separate
package. The core has no opinion about its host; the opinion lives in one
place.

**Moving a leaked choice back to the edge.** When an implementation choice has
leaked into the core as a generic parameter or a core feature flag, the
migration is: selection moves to the composition edge; implementation-specific
API moves to extension traits on the adapter; the consumer-facing handle stays
stable, by type erasure if selection must happen at runtime, with a
static-dispatch path kept where code size or specialisation matters. Then
enumerate every *other* place the choice was represented: dependencies,
feature flags, config schema, build detection, bundler behaviour, CLI
templates, examples, docs, tests, rollback. A mechanism is not decoupled while
the operational tooling still hard-codes the old choice.

**One canonical extension mechanism per system.** When a type must support
many representations, pick one mechanism (one function table, one trait) and
route everything through it. Adding a representation is then additive and
touches nothing existing.

**A small core that almost never breaks, orbited by packages that churn.** You
can read the discipline off the version numbers: the core on a long-lived minor
version while the satellites have had several breaking releases. That gap is
the design working.

---

## Seams

**A shim module that swaps implementations under test.** High-assurance code
imports its concurrency primitives from an internal module that re-exports
either the real ones or instrumented ones, chosen by a build flag. One switch
turns the whole program into something a model checker can explore.

The transferable form: **route every dependency on the unpredictable through
one internal module, so a single flag replaces all of it at once.** Time,
randomness, the filesystem, the network, the OS.

**Shrink the constants under test.** The queue that has 256 slots in production
has 4 under the model checker, because exhaustive exploration of 256 does not
finish.

**Selection at the owner, mechanics in the adapter.** When a subsystem has
several strategies (a native watcher, polling, a remote proxy, a fake), the
owner that knows the environment picks one and hands it down. The fake replaces
the lowest external mechanism only; production's ordering, deduplication, and
lifecycle logic runs unchanged in tests. Process-global state for such a
subsystem is what makes this impossible, so the first move is usually giving it
an owner.

---

## Feature and capability gating

**Never write a raw conditional-compilation attribute at a call site.** Define
a named macro per capability in one file; every call site uses the name. The
answer to "what does this feature actually enable" is then a file you read.
This is mechanism-versus-policy at the build level.

**Complementary conditions are syntactically recognisable as complements.** One
is written as exactly `not(...)` around what the other writes; no boolean
algebra. Two conditions a reader must transform to compare are two conditions
that will drift.

**Gates and documentation are provably in sync.** When the docs claim three
things are unsupported and only two have a guard, the demand is "make them
match and keep them matching", not "fix the docs".

**New public surface enters behind an instability gate.** The promise of
stability is made later, deliberately, as its own decision. Otherwise every
merged feature is an accidental permanent commitment.

**Both sides of a gate are tested, or the gate is a lie.** The build everyone
runs must be unable to reach the experimental path, and a dedicated CI job
must build and test it enabled, from the change that introduces the gate. That
is what makes developing a large feature on the main branch cheaper than a
long-lived branch. Give the gate a stabilisation or removal criterion when you
add it.

---

## Derived state and accelerators

For anything whose job is to avoid authoritative work: a cache, a search index,
a bloom filter, a precomputed candidate set, a routing summary, a second
execution engine.

**Put the accelerator behind its own boundary before wiring it in.** A separate
module with its own versioning keeps "we made search faster" from becoming
"search and indexing are now one thing", and keeps deleting the experiment
cheap, which is the outcome most such experiments deserve.

**Write down which way the error may run, before anything depends on it.** The
useful shape for a candidate filter: *it never claims a match; it returns what
it cannot rule out; the authoritative path verifies; false positives cost time,
false negatives are a bug.* Let an accelerator answer rather than narrow and
every corruption becomes a wrong answer instead of a slow one. Watch any
shortcut fact that lets you skip the real check, like "this list is complete"
or "nothing changed since". It has to stay true when results are combined
(merged, either-or, joined, cut short) and when writers arrive out of order.
If one branch of a merge cannot promise it, the merged result cannot either.
When you are not sure, promise less.

**A shortcut may change speed, never the answer.** A hidden fast path does the
same thing as the normal path by default; overriding it may only make it
cheaper. The caller calls one method and never checks which type it got.
Also, the fast path's needs are not the caller's problem: if it needs sorted
input, do not sort the user's meaningful data to suit it. Have it start over
when input goes backwards, and keep the strict version for callers who already
promise the order.

**Only reorder steps when you can say why it is safe.** Moving a filter before
another step is fine only if you can say why the result is the same.
"Its inputs still exist there" is not a reason. Anything that depends on order,
on neighbouring rows, or on a running total blocks the move until you can show
why it is safe. For plugin code you cannot see inside, the plugin must declare
the properties the optimiser relies on (same input gives same output, no side
effects, works row by row), and those flags are saved along with it.

**A cache key must include everything that changes the result.** Work the key
out from the finished output itself where you can, rather than from a list of
fields someone has to keep up to date. Leave out things that only say *where*
it is (file paths, file names). Any mode that changes what gets built (coverage,
debug, instrumentation) must be part of the key, checked by the cache itself,
not left to callers to remember. Test both ways: changes that must give a new
key, and changes that must not.

**When the source changes, everything built from it changes too.** An index or
lookup table into some content is thrown away in the same step that replaces
that content, and a cache entry is removed when its source is deleted. A weak
reference does not clean up leftover entries. Things the user set on top, like
a filter or sort order, are kept only if they still make sense for the new
content.

**A value picked from several sources is worked out, not stored.** When an
override, a setting, and a default compete, keep each one where it is. One
function picks the winner, and everyone asks that function. Never copy the
fallback into the main value's storage, or it goes stale.

**Derived means rebuildable, which is a separate question from available.** Say
what happens when it is absent, stale, locked, corrupt, or written by an older
version: fall back, rebuild in the background, rebuild on demand, or refuse.
An optional speed-up being built in does not mean it is available when the
program runs. Check for it in a way that cannot crash, and use the normal path
if it is missing.
Measure the fallback before calling the system resilient. Failing closed is a
legitimate choice to write down at the selection boundary, not a default to
drift into.

**A new engine starts compatible with nothing.** When an established feature
gains a second execution path, classify every existing option combination:
proven equivalent, falls back, explicitly refused, or deliberately different.
Start paranoid and widen with tests. The worst outcome is the unsupported
combination that returns plausible output, because nobody finds out.

**A capability keeps its applicability predicate.** When whether a provider
applies depends on a selector, a scope, a version, or a tenant, the predicate
is part of the capability. Do not collapse conditional registrations into a
global boolean, and do not conflate static capability data with a mutable
aggregate. A metadata-only change must invalidate the cache; a multi-phase
operation (prepare, then apply) must resolve to the same provider in both
phases.

**Untrusted inputs cannot write a shared cache.** Trusted runs write the
measurement or scheduling record; untrusted runs read it. A cache anything can
write is an injection point.

**Watch the measurement that drives a heuristic.** When work is scheduled by
measured cost, write the measurement fresh each run so retired work drops out,
and log the diff against the previous run so the team notices when variance
has grown enough that the heuristic has stopped working.

---

## Concurrency and failure

**The module doc *is* the safety protocol.** The best concurrent code opens
with a comment that enumerates every kind of reference to the object, what the
state bits mean, and, field by field, who may access it, when, and under what
condition. Rules are numbered so review can cite them. It is the only place the
invariant exists, because the compiler cannot express it. Adopt the format for
modest state too: one line per field, who writes it and who reads it.

**Splitting a lock is a protocol change, not a storage change.** Before
replacing one shared lock with shards or separate components, write the old and
new ownership maps side by side: per field, who writes it, under what
protection, who reads it to decide something, and when that decision goes
stale. Then list the orderings the single lock gave you for free (admission
against shutdown, publication against sleeping, the last worker exiting
against new work arriving). Proving each shard thread-safe says nothing about
those. Test at low worker counts and small capacities as well as high, race
submission against shutdown, and assert progress, not merely absence of
corruption.

**A callback under a held lock is a protocol, or a bug.** Dispatching to
listeners while holding the registry lock works until a listener removes
itself, adds a peer, or emits again. Either snapshot the registry and release
before dispatching, or queue mutations made during dispatch and replay them
after, and test add, remove, self-removal, and nested emission. Holding across
the call is acceptable only when re-entry is impossible by a local, durable
guarantee, not by convention.

**Only queue what has to wait.** A one-at-a-time queue says "this depends on
what came before". Keep something in it only if that is true. Reading a fixed
item by its id can skip the queue; asking "what is the current state?" must
wait its turn. Anything that skips the queue still counts against the shared
limit.

**Encode the concurrency contract in type names.** A single shared buffer
exposed as two types (producer handle, single thread; consumer handle, any
thread) makes the rule impossible to violate by accident.

**Fallible operations are marked, tested, and documented as a set.** Where a
function can abort, annotate it so the failure is attributed to the caller,
document the exact condition, and collect the tests asserting it in one file.
Failure behaviour is public API with its own suite.

**Cleanup has an owner on each side of a boundary.** When an aborted operation
must clean up, say which side removes what: the writer removes its own
unfinalised output; the transaction removes the finalised output. Stated
explicitly, or both sides assume the other did it.

**Cite the issue that caused the design.** "Wider integers here to mitigate a
wraparound race; see issue NNNN." The history of why the obvious version was
wrong is the most valuable thing to leave behind, and the cheapest place is
next to the code.

**Fix it upstream.** Working around a bug in a layer you depend on is a
permanent local cost to avoid a one-time external one.

---

## Evolving the core

Steady state is the easy part. These are the moves that keep a system fast and
correct while it keeps changing; the mechanics of landing a change are in
[`pull-requests`](../../pull-requests/SKILL.md#size-and-shape).

**Weigh the fix against the interface.** *"The alternative was returning an
error, but that is an interface change, which I would like to avoid."*
Choosing the smaller fix because the larger one breaks a promise, and saying
so, is the routine case.

**Promise as little as people need.** Every promise is something you can never
change again. When users want to rely on something that happens to be true
today (a memory layout, an alignment, an order), either say clearly that it is
not promised, or promise only the part they need: "aligned to at least 8
bytes", not "laid out exactly like this".

**A dependency is a policy decision with a memory.** A change reverted with
"we removed this dependency before when it raised its minimum compiler version
and broke ours" is institutional memory applied as a rule. The re-landed
version using the in-house equivalent was smaller.

**Reason forward to the unbuilt feature.** When a refactor lands ahead of the
capability that motivates it, the reviewer's job is to ask whether it will
still be correct once that capability exists: *"will this hold if we revert an
append after the object was replaced?"*

**Encapsulate into the owner where possible; where the core cannot, because
extensions need it, introduce an explicit handle.** The reason encapsulation
fails is exactly vertical isolation: the core cannot write the functions in
advance because it does not know what product-specific code will do.

**A mechanical mega-change is justified by the test suite, not by review.**
Replacing a hand-written layer with a specification plus generation, tens of
thousands of lines, is reviewed with one honest argument: the existing tests
will catch any divergence. It is only available to a codebase that earned the
tests first, and it is the strongest argument for generating repetitive code
from a spec.

**Revert rather than patch a regression.** The instructive sequence, seen more
than once: a structural fix replaces an escape hatch; ships with benchmarks;
production reports a regression on a workload the benchmarks did not model,
diagnosed through metrics built before they were needed; the obvious narrow
fix turns out to reintroduce the original defect, and the author says so; the
change is reverted. Every step of that is correct. Benchmarks model what you
thought of; observability is what makes the rest diagnosable; a fix that
reintroduces the defect is not a fix; reverting is a normal move.
