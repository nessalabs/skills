# Rust

How to think in Rust, then what to do. Distilled from correctness and
performance work in long-lived Rust systems: async runtimes, search engines,
editors, application frameworks. Every entry is the general idea, not the case
it came from. The working method is in [`coding`](../SKILL.md); the design
layer is in [`system-architect`](../../system-architect/SKILL.md); test rules
are in [testing](testing.md). This file holds only what is specific to Rust.

## How to think in Rust

**The compiler is a design reviewer, and it reviews coupling.** When the borrow
checker fights you, it has usually found two owners for one piece of state, or
a lifetime that crosses a boundary it should not. Reshape the ownership before
reaching for `Rc<RefCell<_>>`, `clone()`, or `unsafe`. Those are all ways of
telling the reviewer to be quiet.

**Whoever owns the value decides who may change it.** Ownership is the
mechanism for "responsibility goes where the information is". A `&mut`
parameter is a statement about who is allowed to decide; a shared reference is a
promise not to. Design the ownership graph first and the API follows.

**Costs are visible, so put each one where the caller can see it.** Allocation,
cloning, locking, blocking, and dynamic dispatch all show in the signature or
at the call site if you let them. The job is to make sure they do.

**Make the illegal state unrepresentable, then make the invariant local.** A
type that cannot express the broken state removes a class of failure from
review and memory. Where the type system cannot express a rule (who may touch a
field from which thread, when an `unsafe` precondition holds), the rule lives
in a comment at the declaration, numbered so review can cite it.

**Every `await` is a place your function can stop existing.** Cancellation is
not an error path; it is a normal exit that runs no code after the current
await. Every async function is designed for being dropped there.

**A promise made with `unsafe` is a proof over the whole safe API.** Marking
something `Send`, `Sync`, or sound is a claim about every safe operation
reachable from that type, now and after the next refactor, not about the fields
at the impl site.

---

## API shape

**Take the most general thing, return the most specific.** `&str` over
`&String`, `&[T]` over `&Vec<T>`, `impl IntoIterator` over a concrete
collection. Return concrete types so callers keep their options. Generality in
the parameter position costs nothing; in the return position it leaks your
implementation.

**Let the caller allocate.** A function that writes into `&mut String` or
`&mut Vec<T>` lets a caller reuse a buffer across a loop; one that returns a
fresh value forces an allocation and hides it. Provide the writing form and
build the allocating form on top, never the reverse.

**Pass context first.** A handle, a config, a clock threaded through a call
chain goes in the first position. It reads as "in this context, do this", and
adding or removing context does not churn the interesting arguments.

**Push conditionals up, loops down.** A function that sometimes does nothing
based on state it reads itself cannot be reasoned about locally; hoist the
condition. A function called in a loop should usually take the batch. The
exception is a check another thread can invalidate: that stays with the state
owner, as one operation that decides and acts under the same lock and returns
what happened.

**Minimise what is `pub`.** Everything public is a promise. Prefer
`pub(crate)`; make a thing public when something outside needs it, not because
it seems generally useful.

**When an API takes ownership, hand it storage rather than copying into it.**
Search a consuming call for `clone`, `to_vec`, `to_owned`, and `collect` that
could have been a move. `Cow::into_owned` still allocates for borrowed input,
so the honest claim is "reuses owned storage when there is some", not "zero
copy".

## Types and invariants

**A field with an invariant is private and enforced in the constructor.** If
any value is legal, make it public. If not, document the rule, make it private,
and enforce it in the one function that can build the type. The invariant is
then verified by reading one file.

**Do not invent a postcondition the producer never promised.** A range handed
into a matcher or decoder is not a bound on what comes back; with look-around
or multiline modes a match can legally end past the slice. Handle the wider
case, or get the bound stated and tested on the producer's side.

**Newtype anything with a unit or a meaning.** `SessionId(String)`,
`Millis(u64)`. The compiler cannot tell you that you passed a width where a
height belonged unless you let it.

**Encode roles in distinct types.** When one structure has two access
disciplines, such as a producer half for one thread and a consumer half for
many, give them two names. The rule then appears at every use site and cannot
be violated by accident.

**Exploit forbidden values.** If zero or empty is not a legal value, encode
that with `NonZero*` or an offset representation. `Option<T>` becomes free and
an illegal state becomes impossible.

**Do not let a rare case fatten a shared type.** A large, rarely used variant
or field is paid for by every instance. Box it, or move it to a structure only
the rare path carries.

**Size matters when the count is large.** For a type with millions of
instances, its byte size *is* the memory profile. Count the bytes, pack where
the win is real, and document the layout at the declaration.

## Allocation

**Reserve exactly what you write.** A capacity hint that does not match the
write either wastes memory or triggers the reallocation it was meant to
prevent.

**Reuse the buffer rather than freeing it.** Clear and refill keeps the
allocation; drop and recreate does not. Hold the buffer at the outer scope of
any loop.

**Watch for the defensive copy inside a loop.** The most common accidental
quadratic in Rust is a `clone()` made for a good local reason, ownership or a
borrow conflict, sitting in a loop over something that grows. The fix is
usually a small index or handle type rather than the value.

**Construct errors lazily.** `ok_or_else`, not `ok_or`; build the message in
the closure. An error path that allocates on every success taxes the common
case.

**Lazy and memoised beats eager global beats recomputed.** Initialise expensive
state on first use, especially behind a strategy selector where most
alternatives are never used.

## Generics, monomorphisation, code size

**Outline the non-generic body of a generic function.** A generic function is
copied per instantiation; move the part that does not depend on the type
parameter into a private non-generic function behind a thin shim. Binary size
and instruction cache improve. Compile time usually does but not always, so
report build wall and CPU time alongside the size win rather than assuming.

**Make helper types generic over the minimum.** A combinator generic over the
*input* type rather than the *item* type it handles multiplies across every
combination.

**Type erasure is a trade, not an upgrade.** A `dyn` boundary buys a stable,
non-generic handle and runtime selection; it costs dynamic dispatch, downcast
paths, and a runtime-mismatch error that did not exist before. Do the cheap
concrete work before erasing, keep a static-dispatch path where specialisation
or code size matters, and never erase merely to avoid writing a type parameter.

**Mark cold paths cold.** `#[cold]` and `#[inline(never)]` on error
construction, slow-path refills, and panics keep them out of every call site.

**`#[inline]` on small leaf implementations that cross a crate boundary.**
Without it a downstream crate cannot inline them and loses bounds-check elision
at every call site. Do not scatter it elsewhere.

## Concurrency

**State the access rules per field.** For any structure touched by more than
one thread, a comment at the declaration says, per field, who may read, who may
write, under what condition. Number the rules so review can cite them. It is
the only place that information can exist.

**Do not call out while holding a lock.** A user-supplied callback, a `Drop`, a
`Clone`, a `Display` run under a non-reentrant lock can re-enter you, block on
you, or panic mid-transition. Before dispatching, draw the cycle: held resource
→ callback → public APIs it can reach → resources they acquire, including your
own wrappers such as a one-shot listener that removes itself. Snapshot the
registry and release, or queue mutations and replay after. Holding across the
call is acceptable only when re-entry is impossible by a local, durable
guarantee. Where an operation must happen under the lock, check the actual
mutex wrapper's behaviour on panic, and drop the replaced value after
unlocking.

**A manual `unsafe impl Send` or `Sync` is a transitive proof.** Enumerate every
way the inner state can escape through safe code: `Clone`, public fields and
getters, `Arc` extraction, closure capture, trait-object conversion, child
handles, destructuring. Put the assertion on the narrowest outer type whose API
actually enforces the invariant, keep the inner types non-`Send`, and pin it
with a compile-fail test and a run under Miri or a race detector.

**Move the shared counter from the frequent event to the rare transition.** If
every unit of work touches one atomic, that atomic is the bottleneck. A count
of *active workers* updated on sleep and wake often answers the same question.

**Measure wake-ups, not just throughput.** When a scheduling change alters who
gets notified, track unsuccessful wake-ups and useful work per wake alongside
latency. Fewer notifications is not a win if progress stalls; more is not a win
if CPU per completed operation rises.

**Releasing the resource is half the obligation; waking the waiter is the
other half.** Returning a permit through the raw primitive instead of the normal
release path leaves a closed receiver asleep forever. For every exit, name the
owner that returns the resource and the transition that makes the waiter
runnable. In a manually polled test, assert the future was *woken* before
polling it again; a forced poll hides exactly this bug.

**Construct the whole worker set before starting any of it.** A factory that
panics partway leaves an active count including participants that never
existed. Test the panic at the first, middle, and last position.

**A fixed pool or cache capacity is a concurrency ceiling.** A constant that was
generous on four cores serialises on thirty-two. Size from available
parallelism where that is the right envelope, and say what the extra slots
cost.

**Splitting a lock is a protocol change.** Write the old and new ownership maps
side by side, then list the orderings the single lock gave you for free:
admission against shutdown, publication against sleeping, last worker exiting
against new work arriving. Proving each shard thread-safe says nothing about
those. Details in
[patterns](../../system-architect/references/patterns.md#concurrency-and-failure).

**Route synchronisation primitives through one internal module** that
re-exports either the real ones or instrumented ones under a build flag, so the
exhaustive checker is a build configuration rather than a refactor. Shrink
capacity constants under that flag so it terminates.

## Errors, panics, and unsafe

**Panics are API.** Document the exact condition, annotate so the panic is
attributed to the caller, and collect the tests asserting it in one place so
the panic surface is reviewable as a set.

**Convert internal arithmetic failures into documented ones.** Check the
boundary explicitly and panic with a message naming the parameter, rather than
letting an overflow deep in a constructor produce something incomprehensible.

**Guard the algorithm's forbidden inputs at construction.** A zero seed, an
empty set where the loop assumes one element: reject them where the value is
built.

**Order the fallible step before you are holding something that needs
cleanup.** Any call that can panic between "took ownership" and "stored it
safely" is a leak or a double free waiting to happen.

**`Drop` cannot break a cycle that prevents `Drop`.** When bridging to another
ownership system (Objective-C, C++, OS callbacks), draw both sets of edges. If a
foreign retain cycle can keep the Rust owner alive, cleanup that lives only in
`Drop` never runs; release explicitly at the owner's lifecycle event.

**Native handles belong to the branch that uses them.** Acquire as late as
possible, after deciding which branch runs, and release on every path
including `?` and platform fallbacks. Progressive degradation (latency or
memory climbing over minutes) is the symptom; count retained handles alongside
CPU.

**Prefer early returns.** `let Some(x) = .. else { return }` and `?` keep the
happy path at one indentation level.

## Async

**A `Future` does nothing until polled.** Constructing one is free; not awaiting
one is usually a bug. Anything that must happen regardless of whether the
caller waits belongs in a spawned task.

**Say what happens on cancellation.** Any `async fn` that can be dropped
mid-way documents whether partial work is visible, and every `select!` arm is a
cancellation point.

**Say when output becomes observable.** Anything with `flush`, line buffering,
or incremental delivery in its vocabulary has a latency contract as well as a
throughput one, and buffering breaks it silently. Test the open-ended producer
that emits one unit at a time.

**A `buffered(n)` in one consumer is pacing, not a limit.** If the resource is
shared, the bound lives at the lowest owner every entry path traverses, as a
semaphore or an admission queue, and the caller's window shapes latency on top
of it. Test a second entry path, and that cancellation returns capacity.

**Never block in async context.** Filesystem calls, heavy computation, and
synchronous locks held across an `await` stall the executor. Move them to a
blocking pool, and ask "does this ever block?" of every new dependency.

**Do not hold a lock across an `await`.** It converts a fast mutex into a
source of deadlock.

## Testing, Rust specifics

The rules are in [testing](testing.md). What Rust adds:

- **Compile-fail tests protect type-level invariants**, with a snapshot of the
  error. Without one, a later refactor can quietly make the illegal state
  legal and nothing goes red.
- **Run the checkers as separate jobs**: Miri for undefined behaviour,
  sanitisers, the exhaustive concurrency checker, a fuzzer for anything parsing
  untrusted input, and a semver check on the public interface. Each answers one
  question.
- **Build the feature powerset and the minimum toolchain.** It is the only way
  to know that optional capabilities are actually optional.

## Performance in Rust

The method is in [`coding`](../SKILL.md#5-performance). What Rust adds:

- **Benchmark the contention, not only the throughput.** A change that improves
  single-threaded speed can lose under concurrency, and the reverse. If the
  code is shared, exercise it from several threads and report the row that
  loses.
- **A source-level reduction is a mechanism claim.** Removing a clone or a
  second lock acquisition is real, and it is not a measured speedup. Say which.
  When one change carries two optimisations, attribute the evidence per
  mechanism so a later regression can be reverted by the hunk that caused it.
- **Preserve representation across a transport boundary.** Bytes that are
  already bytes do not go through a text encoding and back because the
  convenient API takes a string. Text may be the correct stable contract; the
  thing to avoid is accidental amplification, not text.
