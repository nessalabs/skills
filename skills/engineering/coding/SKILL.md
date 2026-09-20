---
name: coding
description: "The working method for any code change - a feature, a fix, a refactor, or a review. The problem-solving loop (restate, locate, hypothesise, refute, smallest change, prove, describe, hold), what to settle before writing, how to write, failure-first design, what to test, how to do performance work, how to shape the change, and how to report what you did. Points into language references for Rust and React/TypeScript. Use whenever you are about to write or modify code, or before opening a pull request."
---

# Coding

This is the layer for *how to work*. The other layers, and when each applies:

| Layer | Where | When |
| --- | --- | --- |
| How to think about the system | [`system-architect`](../system-architect/SKILL.md) | Designing, structuring, or reviewing anything spanning more than one file |
| How to work | this document | Every code change |
| How to think in the language | [Rust](references/rust.md), [React & TypeScript](references/react-typescript.md) | While writing in that language |
| What to test, and how | [testing](references/testing.md) | Deciding whether something needs a test, and which kind |
| How to find and prove things | [`method`](../method/SKILL.md) | Investigating a bug, chasing a performance problem, deciding what to automate |
| How to describe and review a change | [`pull-requests`](../pull-requests/SKILL.md) | Writing the description, sizing the change, reviewing someone else's |
| How a feature actually runs | [`trace`](../trace/SKILL.md) | Asking what happens on an action, or invoking `/trace` |
| How to say it | [`wdym`](../wdym/SKILL.md) | Explaining any of the above to a person |

Each lesson lives in exactly one of these. Where a section here points
elsewhere, the pointer is the whole rule; do not expect a second copy.

If you are writing in a language with no reference here, the method below still
applies in full. Follow the surrounding code's idiom, and say plainly that you
had no language-specific guidance to lean on.

---

## 0. The loop

Every task below, from a one-line fix to a subsystem, is this loop. When you
are stuck, find which step you skipped.

1. **Restate the problem** in the product's words and as a condition that must
   be true afterwards. If you cannot say what "done" looks like, you are not
   ready to write.
2. **Locate the information.** Who has what is needed to decide this? Read the
   code that already does something similar; read the history of the code you
   are about to touch.
3. **Hypothesise the mechanism**, not the symptom. "It is slow" is a symptom;
   "a per-item function walks all items" is a mechanism.
4. **Try to refute it** before acting on it: reproduce, trace, measure. A
   hypothesis that survives an honest attempt to break it is a finding; one
   that has merely been stated is not.
5. **Make the smallest change that makes the condition true**, designing the
   interrupted, repeated, and concurrent cases before the happy one.
6. **Prove it** the way the claim demands: a test that fails without the change,
   a measurement with its workload, an argument that the invariant holds.
7. **Describe it** so a stranger can evaluate it: why, what, what you did not
   do, what you did not run.
8. **Leave something that fails when the finding stops being true.** A fix
   with no artefact holding it has a half-life of about two refactors.

Steps 3 and 4 are where most wasted work lives, in both directions: acting on
a hypothesis nobody tried to refute, and refusing to act until certainty
arrives. The standard is a mechanism you can state and a way you tried to
break it.

## 1. Before writing anything

**Read enough to be boring.** Find two or three places that already do
something like what you are about to do, and match them: naming, error
handling, layout, test style, comment density. Code that reads like the code
around it is cheaper for everyone forever; a second style has to justify
itself.

**Name the thing in the product's words.** If you cannot name the concept
without inventing a word, you have not found it yet. Go find it before you
write a type.

**Answer four questions.** They take two minutes and they prevent most rework:

1. *Who has the information needed to make this decision?* Put the
   responsibility there, not where it is convenient to call from.
2. *What must always be true?* Name the invariant and the function that
   enforces it.
3. *What happens if this stops halfway, runs twice, or races?* Design for that
   before the happy path (§3).
4. *How does this get deleted?* If the answer touches more than this module
   plus one adapter, the boundary is wrong.

**Check the altitude.** A feature that needs a new parameter on a core type, a
new branch in a core function, or a flag threaded through is usually a
capability that should be composed on top rather than absorbed into the middle.
The exceptions and the reasoning are in
[`system-architect`](../system-architect/SKILL.md#6-small-core-composable-pieces).

## 2. While writing

**Write the smallest thing that makes the requirement true.** Not the
framework for a family of things like it. You will know the right abstraction
on the third instance, and you will be wrong about it on the first.

**Do not build what nobody asked for.** No configurability, no extension point,
no generality, no layer that only forwards. A parameter with one caller is a
constant that has not admitted it yet.

**Extract on the second use, not the first**, and only when the two uses are
the same *idea*, not coincidentally the same lines. A block, a local, or a
comment is a cheaper abstraction than a function.

**Make the control flow visible.** Early returns; conditions hoisted to the
caller; no hidden global state deciding whether a function does anything. The
one thing that does not move to the caller is a check another thread can
invalidate: the owner of the state gets one operation that decides and acts
under the same protection, and a caller-side pre-check is a hint, never the
authority.

**Put costs where the caller can see them.** Allocation, blocking, I/O, and
retries are visible at the call site or named in the signature. A function that
silently does an expensive thing is a landmine.

**Comments say why.** The code says what. A comment earns its place by holding
what the reader will not have: the constraint, the surprise, the thing you
tried that did not work, the issue that caused this shape. A comment that
paraphrases the line below it gets deleted.

**Correct the name in the same change that invalidates it.** Renaming is cheap.
Living with a name that no longer describes the thing is not.

## 3. Failure first

Design the interrupted case before the happy path. The happy path will be
fine; the system's real shape is decided by what happens when it is stopped,
repeated, or entered twice.

- **One state, one representation.** A sentinel meaning two things will be read
  as the wrong one, and the case where it matters is always a retry or a
  restart. Give each state its own name before you need to tell them apart.
- **An ambiguous observation is not a terminal state.** Before a zero, an empty,
  a `None`, or a timeout moves something to finished or closed, write down what
  else it could mean. A read that returned nothing because the buffer had no
  room is not end of stream; the damage shows on the *next* call.
- **Anything reserved is rolled back or filled.** A count, a slot, or a
  published handle for a participant that a failing constructor never created
  is a peer waiting forever. Inject the failure at each setup position and ask
  who wakes the ones already started.
- **Publish intent before the first observable async boundary.** When one
  operation can be triggered again while its setup can await, spawn, or call
  out, the reservation is visible before that point, and every terminal path
  (success, error, cancellation) clears it exactly once. Otherwise the second
  trigger sees nothing in flight and starts a duplicate.
- **A callback into code you do not control is a failure boundary.** While you
  hold a lock or sit between two halves of a transition, a user-supplied
  callback, destructor, clone, or formatter can panic, re-enter you, or block
  on the thing you hold. Snapshot before dispatch, or queue the mutation and
  replay it after, or prove locally that re-entry is impossible. Convention is
  not a proof.
- **Ambient state is an input.** Working directory, environment, locale, clock:
  if it decides what the operation *means*, capture it once at the boundary and
  pass that value down, rather than letting each layer reread it.
- **Cleanup is structural, never remembered.** Tie removal to a scope, a guard,
  or a lifetime, not to a teardown call on every exit path, because the path
  that gets forgotten is the successful one. A resource owned by a branch is
  acquired by that branch, as late as possible, not up front for every branch.
- **Releasing a resource is half the obligation; waking whoever waits on it is
  the other half.** For every exit, name the owner that returns the resource and
  the transition that makes the waiter runnable.
- **Release transient state at its lifecycle boundary.** A long-lived owner
  holds heavy phase-specific state no longer than the phase, with a defined way
  to re-acquire it if a later legal event needs it.
- **Idempotent, or keyed.** Assume anything can run twice. Overwriting
  operations tolerate retries; appending ones need an identity that makes the
  second attempt recognisable.
- **Every queue, buffer, and retry loop has a bound** and a stated behaviour at
  the bound. Name what the bound protects and at which owner it is enforced:
  a window in one caller is pacing, not a limit, if another path reaches the
  same resource.
- **Authority is part of the key.** State owned by a principal (tenant, session,
  window, user) is stored under the owner first and the local id second, so a
  guessed id cannot select someone else's state and no caller has to remember
  to check.
- **Write the durable fact before announcing it**, and announce before acting on
  it.
- **Decide fatal versus survivable, and be consistent with the code around you.**

## 4. Tests

**A change either adds behaviour or fixes broken behaviour. Both have a test
that would have failed before.** If you cannot write one, say so in the change
and say why.

The rules for what to test, how, and what not to, live in
[testing](references/testing.md). The ones you will need on every change:
through the public surface, real dependencies over mocks, determinism injected,
poll never sleep, minimal setup, named after the behaviour, and a test that
cannot pass when the intended work never happened. When writing tests
surfaces a probable bug, file it separately rather than fixing it inside the
test change.

## 5. Performance

Do not sprinkle it. Locate it.

1. **Reproduce and profile first**, and name what you found. The function you
   suspect is usually not the one. See [`method`](../method/SKILL.md) for the
   full loop.
2. **Look in this order**: repeated work (the accidental quadratic, the
   defensive copy in a growing loop, the same thing computed per item);
   synchronisation and wake-up overhead; queueing and retention; data movement
   and allocation. It is an investigation order, not a frequency ranking, but
   the first category dominates the others by orders of magnitude when it is
   present.
3. **State the expected magnitude.** "This is 1–2% of runtime, so expect
   0.5–1% overall" tells the reviewer how much complexity the change may
   justify.
4. **Match the evidence to the claim.** A quantified claim carries its
   scenario, baseline, result, and machine. A mechanism-only claim ("removes
   one serialisation per request") names the cost that disappeared and says
   that end-to-end impact was not measured. Both are honest; an invented
   magnitude and a bare "faster" are not.
5. **For a pure performance change, prove the observable contract is
   unchanged.** For a deterministic batch API that is identical output on the
   full fixture set and on pathological inputs. Where the API promises
   streaming, progress, cancellation, or scheduling, *when* a result becomes
   visible, what ordering is permitted, and what resources are bounded are all
   part of the contract. The same final bytes arriving only at end of stream is
   a regression.
6. **Benchmark the workload it should lose on** and report both: low and high
   concurrency, short and long tasks, full and partial batches. For code-size or
   compile-time work, report the counter-metrics too (build time, runtime if
   dispatch changed). Mixed results are reported as mixed, not summarised as
   "faster".
7. **Skip work only when its result cannot reach anything**: no future
   iteration, no output, no error still owed. Keep the structural bookkeeping
   the surrounding protocol needs. Test it by putting something malformed where
   the work would have happened and asserting nothing surfaces.
8. **Do not start work before its consumer can schedule it.** If the consumer
   owns batching, admission, or priority, construction stays lazy; an operation
   that is already running when it is handed over makes the window decorative.
9. **Prefer once-and-only-if-needed** over eager, and eager over recomputed.
10. **Revert an optimisation you cannot maintain.** Whatever the benchmark says,
    code nobody can safely modify is a liability.

Language specifics: [Rust](references/rust.md#performance-in-rust),
[React & TypeScript](references/react-typescript.md#performance-in-react).

## 6. Shaping the change

One reason per change; refactor, test, then change as separate commits;
structural work landed ahead of the feature that needs it; large features as
inert infrastructure first; under a couple of hundred changed lines where you
can. The mechanics, the description format, and what to subtract before judging
a diff's size are owned by
[`pull-requests`](../pull-requests/SKILL.md#size-and-shape).

**Update the prose the change invalidates**, in the same change. Grep for the
term; the invalidated sentence is rarely in the file you edited.

## 7. Reviewing your own diff

Read it as a stranger, in the web view rather than the editor, before anyone
else sees it. Attention in this order: right problem, right design, correct,
tested, readable, named in the product's words, tidy. Never lead with tidy.

The questions to ask are the reviewer's questions in
[`pull-requests`](../pull-requests/SKILL.md#what-to-actually-look-for). The
one to ask first of your own work: **is the claim in my description actually
true?** Walk the interrupted, repeated, and re-entered paths yourself rather
than accepting your own answer.

## 8. Finishing and reporting

- The change does one thing, and the message says which.
- A test fails without it.
- It touches the number of files it *should* touch, after subtracting moves,
  generated files, lockfiles, and formatting.
- No absence-invariant was violated (see
  [structure](../system-architect/references/structure.md#the-absences)).
- Anything expensive to reverse has a written note or a
  [decision record](../system-architect/references/adr.md).
- Names match the domain language, including in tests.
- **Report what actually happened.** Every check is run, not run, blocked, or
  inconclusive, and the report says which. If tests fail, say so with the
  output. If part of the scope was skipped, say which part and why; scaling the
  work down is not your call to make silently. A number you did not measure is
  reported as someone else's, or not at all.
