# React and TypeScript

How to think in React and TypeScript, then what to do. Distilled from
performance and correctness work in large React applications, component
libraries, and the rendering libraries underneath them. Every entry is the
general idea, not the case it came from. The working method is in
[`coding`](../SKILL.md); test rules are in [testing](testing.md). This file
holds only what is specific to the language and the framework.

## How to think in React and TypeScript

**Render is a function of state; everything else is a side effect you must
account for.** The framework decides when to call your function. Your job is to
know what causes it to be called, and to stop paying for work nobody asked for.

**Work is invisible until you measure it.** Nothing in the source tells you a
component rendered four hundred times. Before optimising anything, know which
of four things you are looking at, because they have different fixes and
guessing wrong makes it worse:

1. Too many renders: a component re-runs when its inputs did not really change.
2. Too much work per render: the render allocates, computes, or walks something
   large.
3. Too much committed: the diff is fine but the DOM mutation or layout it
   triggers is expensive.
4. Work outside render: an effect, subscription, timer, or instrumentation doing
   more than the frame can afford.

**Identity is an interface.** When a value feeds a memoised child, a dependency
array, or a context, its reference identity is part of the contract. A
"harmless" change from a hoisted constant to an inline literal silently
un-memoises a subtree.

**The type is a claim, not a guarantee.** `readonly` does not stop mutation
through an untyped reference; a payload type redeclared on the other side of a
boundary compiles happily while the two drift. Where a guarantee matters at
runtime, enforce it at runtime, at the boundary, once.

**The lifetime you do not control is the one that leaks.** A listener, a
subscription, a snapshot kept "in case", a closure captured by something the
caller holds: each keeps whatever it references alive until someone removes it,
and the path that forgets is the successful one.

---

## Do not pay for what was not requested

**Gate optional work on whether anything consumes it.** Derived data built for
an optional callback, instrumentation collected when nothing is profiling,
formatted strings for a log level that is off, tracked wrappers created for
consumers that read the raw value. The largest wins in this space come from
noticing that a feature existed but was not in use.

**Instrumentation is off, or bounded, when nobody is observing.** Buffered
performance entries retain everything they reference. Emit only while
profiling, and clear what you accumulate.

## Per-item work

**A function called once per item that computes something over all items is
quadratic.** Hoist the whole-set computation out and pass the result in. It
does not show until the list is big, which is exactly when a user notices.

**Deduplicate idempotent fan-out.** "Notify everyone about X" runs once per
distinct X, not once per caller.

**Special-case the common shape.** A generic recursive comparison pays for its
generality on every call; a direct loop for the shape that dominates is a large
win for little code.

**Do not allocate per iteration in hot code.** A closure inside a recursive
comparison, a `map` used only to iterate, an object literal rebuilt per row.

**Do not read past the end of an array.** It changes the array's internal
representation and deoptimises the surrounding function. Bounds-check in the
loop.

## Memoisation

**Purity is the precondition.** A per-render, per-instance function can be
cached because it is a pure function of stable inputs. If it reads props, the
clock, or module state, memoising it is a bug.

**The highest-value target is a pure function of a stable input called once
per instance per render**: styling functions, formatter construction, derived
configuration.

**Memoise the expensive thing, not the cheap thing.** `useMemo` around a
primitive comparison costs more than it saves. Reserve it for allocation-heavy
derivations and for values whose identity feeds a dependency array.

**Memoising components is the blunt instrument, not the first one.** It helps,
rarely resolves, and adds a comparison at every render. Fix the input that
keeps changing.

## Retention and cleanup

The general rule, cleanup is structural and never remembered, is in
[`coding`](../SKILL.md#3-failure-first). The React forms:

- **Clear a rollback or snapshot field the moment its purpose expires.** On
  success, null it.
- **Every subscription has a removal path that runs on the success case.** A
  listener on a caller-supplied signal, removed only from inside the listener,
  never fires on success and keeps the whole finished result reachable. Prefer
  an `AbortSignal` passed to `addEventListener`, a scope, or a disposer bag
  over a teardown someone must remember.
- **Encapsulate a repeated cleanup obligation in a hook.** If every call site
  must clear a timer or cancel a request, one of them will not.
- **Effects clean up in reverse**, including when the effect re-runs because a
  dependency changed, not only on unmount.

## Animation and interaction

**Anything per-frame is scaled by elapsed time.** A flat per-tick multiplier
decays twice as fast at 120 Hz as at 60 Hz. Write decay as a power of elapsed
time and velocity as units per second. The bug report for getting this wrong is
"feels wrong on my machine", which is nearly impossible to act on.

**Fake the clock in tests.** Stub the high-resolution timer so animation and
timing fixtures are deterministic.

**Keep pointer and scroll handlers off the render path.** Coalesce to the next
frame, and read layout once per frame rather than per event.

**Cache derived geometry and invalidate it explicitly.** Hit testing and bounds
recomputed per pointer move dominate canvas-style interactions. Key the cache
by what it derives from and be deliberate about what invalidates it.

## State and data flow

**Model states explicitly.** A `null` meaning both "not loaded yet" and
"loaded, nothing found" will be read as the wrong one on a retry or remount. A
discriminated union is cheaper than the bug.

**Do not share a counter or a version between two independent concerns.**
Activity in one lane makes the other look changed.

**Derive rather than duplicate.** State computable from other state is a
synchronisation problem you chose to have. Store the minimum; compute the rest
during render.

**Lift state to the lowest common owner, not to the top.** State parked above
where it is used re-renders everything between.

## Boundaries

**One definition of every shape that crosses a process or bundle boundary.**
Generate one side from the other, or hand-write one declaration both import.

**Inline the first payload; lazy-load the heavy parts.** Give an embedded view
what it needs for its first frame along with the view itself, and defer
anything large not needed for that frame.

**Validate at the boundary, then trust inwards.** Parse untrusted input into a
domain type once, at the edge. Downstream receives the type, not the raw
payload plus a promise that someone checked it.

**Review the build's view of a change too.** A new file outside a watched
directory silently stops triggering rebuilds; a new import can break tree
shaking; a moved module can leave a bundle entry stale. None of it shows in the
diff.

## TypeScript specifically

**Prefer discriminated unions over optional-field soup.** Four optional fields
where only some combinations are legal is sixteen states of which twelve are
bugs.

**Give three-valued things names.** A nullable field of a nullable type, or a
boolean pair standing for three states, is a missing union. A bare boolean
parameter becomes an object or a union of literals so the call site says what
it means.

**Type the boundary, infer the interior.** Annotate exported signatures and
anything crossing a seam; let inference handle locals.

**Do not widen a shared type for one caller.** An optional field only one
consumer sets makes every consumer handle a case that cannot happen for them.
Split the type.

**Mark a lazily initialised constant so the bundler can drop it when unused.**
Eager work at module load is still work, and it is paid by every consumer of
the bundle.

## Performance in React

The method is in [`coding`](../SKILL.md#5-performance). What React adds:

- **Name which of the four causes you found** before changing anything. The fix
  for too many renders makes too much work per render worse if you guessed
  wrong.
- **For a pure performance change, the contract is the rendered result** on the
  full fixture set, not a passing suite.
- **Record counts in test baselines.** Write render counts, node counts, or
  work units into the recorded output, rounded coarsely enough that noise
  produces no diff. A regression then arrives as a text diff in review beside
  the behavioural changes, rather than in a dashboard nobody opens.
