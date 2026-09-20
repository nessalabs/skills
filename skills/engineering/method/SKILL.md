---
name: method
description: "How defects and regressions actually get found, how a hypothesis gets verified before it is acted on, and how a fix is stopped from being undone. Covers the instruments (property tests and fuzzing, exhaustive concurrency checking, differential testing, checkers, measurement kept as a record, production telemetry), reproducing and minimising, explaining the mechanism and bounding the blast radius, what counts as evidence, and which artefact holds each kind of finding in place. Use when investigating a bug, chasing a performance problem, deciding what to automate or test, or setting up CI checks."
---

# Finding, verifying, and not drifting

The patterns in the other skills are the *conclusions* long-lived systems
reached. This one is about the machinery that produced them, which is the more
valuable half: a team that can reliably find, prove, and hold will rediscover
every good pattern on its own. A team that cannot will lose them one refactor
at a time.

Three phases, and most codebases are weak at a different one than they think.

1. **Finding.** Most defects are not found by reading code. They are found by
   an instrument built before anyone knew what it would catch.
2. **Verifying.** A hypothesis is not a finding. The gap between "this looks
   wrong" and "here is the mechanism, the preconditions, and the blast radius"
   is where most wasted work happens.
3. **Not drifting.** A fix with no artefact holding it in place has a half-life
   of about two refactors.

---

## 1. Finding

Ranked by what each instrument catches that nothing else can. Build them in
this order.

### Properties and fuzzing

The highest-yield instrument for anything that parses, serialises, or
transforms. You do not assert an output; you assert a **property that must hold
for all inputs**, and let a generator attack it.

- **Round-trip**: parse, print, parse again; the two structures are equal.
- **Differential**: two implementations of one contract agree. A fast path and
  a reference path; an optimised strategy and the naive one.
- **Invariant**: the module's stated guarantee, asserted after every operation.
- **Never panics, never hangs** on arbitrary input, for anything reading data
  you do not control.

Three details separate a target that earns its keep from one that does not.
Scope the property to where it actually holds, rejecting the generated inputs
where it is legitimately ambiguous rather than weakening the assertion for
everyone. Make the crash output directly actionable, printing the reproducible
form of the input rather than an opaque structure. And check every finding in
as a permanent test, in a directory of nothing but fuzz-derived regressions.

### Exhaustive checking for concurrency

For anything with more than one thread of control, ordinary tests sample the
interleaving space at random and will not find the bug. A model checker that
enumerates the permutations will.

The practical shape: route every concurrency primitive through one internal
module that re-exports either the real implementations or instrumented ones
under a build flag, so the whole program becomes checkable by changing a build
configuration. Shrink capacity constants under that flag so exploration
terminates. Run it on every merge to the main branch, and on a pull request
when it carries a label saying it touches that area; run it as a matrix over
the alternative implementations, because "it works with the other queue" is
exactly what nobody checks by hand.

### Checkers that need no test authoring

Undefined-behaviour interpretation, address and memory sanitisers, leak
detection, a dependency-vulnerability audit on a schedule. They find things
nobody wrote a test for, which is their entire value. Each is a separate,
narrowly named job; a single "test" job that does everything tells you only
that *something* broke.

### One corpus, many implementations

When several implementations satisfy one contract, write the cases **as
data** in a declarative format and run the whole corpus against every
implementation. Per-implementation suites are slower to compile, harder to
maintain, and less clear; tests as data are readable by someone who does not
know the codebase.

### The whole matrix, not just the default

Compile-only jobs are cheap and catch a category nothing else does: a feature
combination that does not build, a minimum toolchain that broke, a platform
that no longer compiles. Run the feature powerset. It is the only way to know
that optional capabilities are actually optional.

### Your consumers' test suites

The strongest single practice observed anywhere: CI jobs that check out major
downstream projects and run *their* tests against the current branch. A
breaking change is caught by the people it would break, before merge. The
version you can afford with no external consumers: run the app's own
end-to-end suite against the library change, in the same pipeline.

### Measurement, kept as a record

- **Profile before believing anything about performance.** The function you
  suspect is usually not the one.
- **Read the timing data you already emit.** CI logs carry timestamps; a badly
  balanced pipeline can be found by parsing them with no new instrumentation.
- **Keep results in the repository**, dated and labelled with the machine and
  configuration, including allocator and libc, because those move results more
  than most code changes do. Hand comparison is still worth it; the alternative
  is a number in a comment from two years ago that nobody can reproduce.
- **Measure the costs that are not runtime.** Clean build time, binary size per
  feature against a hello-world baseline. A flag that adds nothing to runtime
  and seconds to every build is still expensive.
- **Upstream numbers stay upstream numbers.** A result reported in someone
  else's pull request is labelled as theirs, with its workload, and is not
  converted into a verified measurement by being repeated.

### Production, and the users in it

Benchmarks model the workloads you thought of. The regression that matters
arrives in a shape you did not imagine, and the only instrument that sees it is
telemetry built before you needed it. Build the counters and timings *now*,
behind a flag, on the paths you believe are hot. With per-worker metrics a user
can hand you a twenty-line reproduction; without them the report is "it got
slower", which is unactionable.

### Coverage, as a finder and never as a target

Measuring coverage to find code nobody has executed is valuable; writing tests
for such an area routinely surfaces probable bugs, which get filed separately.
Measuring coverage as a number to raise produces tests that assert nothing.
The tell is whether the result is "we found these three things" or "we got to
80%".

### Bots, models, and other hypothesis generators

Automated reviewers, static analysers, and language-model audits produce
*candidates*. They are not evidence. Worth copying exactly:

- A bug found by asking a model to look at one specific function, with the pull
  request saying so plainly.
- A bot flagging a flaw, the author saying it was fixed, and **a human
  re-deriving the failure path and finding it was not**. That reviewer is where
  the value was.
- A contribution policy requiring that a human can explain the change in their
  own words, with model-derived context quoted and marked rather than pasted
  as the contributor's reasoning.

Every generated finding enters phase 2. None is merged on the strength of its
confidence.

---

## 2. Verifying

**Reproduce before fixing.** A fix for a defect you cannot reproduce is a guess
with a diff attached, and you will not know whether it worked.

**Minimise the reproduction, and treat it as the deliverable.** Twenty lines
that fail deterministically are worth more than the report, the fix, and often
the analysis, because they outlive all three as a test.

**Explain the mechanism, not the symptom.** The best defect write-ups share a
shape:

- the exact chain of events, step by step;
- **a numbered list of the preconditions** required to trigger it, including
  the non-obvious one about ordering;
- **an explicit bound on the blast radius**: "because of precondition three,
  this can never produce a wrong answer; it is strictly about which span is
  reported." That sentence lets everyone else decide whether they are affected;
- for a regression, the commit that introduced it, by hash and subject.

**Know what class of evidence you hold.** A written policy, a reviewer's
request, a configured CI job, a job that actually passed, a bisection showing
that toggling one call changes the symptom, and your own reproduction are
different things. Correlation from bisection is useful and is not root cause.
An approval proves that someone approved. A closed proposal does not prove its
design was rejected. Say which you have, and do not upgrade one into another.

**Do not re-run a flake.** When a test fails intermittently, reconstruct the
interleaving that produces the observed value and explain why it is now
possible. A scheduling change can legitimately remove one wake-up and change a
counter; find out whether that is what happened.

**A stated claim is a hypothesis.** Apply it to your own work first: take your
own claim that a case is handled, and try to construct the interruption,
repetition, or re-entry that breaks it. The review-side version is in
[`pull-requests`](../pull-requests/SKILL.md#the-claim-is-a-hypothesis).

**Try to refute, not to confirm.** For anything subtle, the question is not
"does my test pass" but "what input would make this wrong". Confirmation is
cheap and nearly worthless.

**For a pure performance change, the correctness argument is the unchanged
observable contract**, proved at the level the contract is stated: bytes for a
batch API, progress and ordering for anything that streams or schedules. The
full rule is in [`coding`](../coding/SKILL.md#5-performance).

**Measure the fix, and report honestly when it does not help.** The two moves
that mark a serious engineer: discovering that the obvious narrow fix
reintroduces the exact defect the original change existed to prevent, and
saying so instead of shipping it; and measuring a cleverer fix and reporting
"this does not help as much as I hoped" rather than quietly merging it.

**Ask what the fix costs, not just what it buys.** A correctness improvement
that loses measurable CPU on a real workload is a trade, and it is named as
one.

**Reverting is a normal outcome.** When a change costs more than it bought,
take it out rather than carrying it plus a partial fix while hunting for the
real one. An optimisation nobody can safely modify is removed whatever its
benchmark says; "too subtle to fix properly" is a correct reason and a rare
thing to say out loud.

**Check the follow-ups before treating a merged change as an example.** A
change that was reverted a month later, or patched three times, teaches
something different from what its description claims. Read forward in the
history before copying a pattern from it.

---

## 3. Not drifting

A finding with no artefact behind it will be reintroduced. Every phase-2
conclusion leaves something that fails when it stops being true.

### Turn the finding into an artefact

| What you learned | What holds it |
| --- | --- |
| A specific defect | A regression test named after the defect, failing on the old code, naming the commit that introduced it |
| A defect found by fuzzing | The input checked into a fuzz-regression directory, with a comment explaining the mechanism |
| A subtle semantic | Documentation *plus* tests asserting exactly what the documentation claims |
| A type-level invariant | A compile-fail test with a snapshot of the error message |
| A performance property | The relevant counters written into the recorded test baseline, rounded so noise makes no diff |
| A structural rule | A test over the module graph that fails on violation |
| An interface promise | A compatibility check, and a list of which external types may appear in the public surface |
| A concurrency protocol | A bounded model in the module, with what it bounded written down, plus a public regression test |
| A heuristic that can go stale | A logged signal that says when it has: the diff against the previous measurement, the variance, the hit rate |
| A decision that was expensive to make | A dated decision record, including the options rejected |

**Record the mechanism in the regression test, not just the input.** The best
regression files explain what the engine was doing, why the bug was possible,
and, the valuable part, **the more thorough fix that was considered and not
done, and why.** Without it the next person "fixes" it properly and
reintroduces something worse.

### Make drift impossible rather than discouraged

- **One place for policy.** Conditional compilation and feature gating live in
  one file as named capabilities; call sites reference the capability, never
  the raw condition.
- **Write complementary conditions so a human can verify them by eye.** One is
  written as exactly `not(...)` around what the other writes; no de-Morgan
  transformations. Two conditions that need boolean algebra to check will
  drift.
- **Documentation and enforcement are provably in sync.** When the docs claim
  three things are unsupported and only two have a guard, the fix is not "fix
  the docs" but "make them match and keep them matching".
- **New surface enters behind an instability gate**, and the promise is made
  later as its own decision. Otherwise every merged feature is an accidental
  permanent commitment.
- **Untrusted inputs cannot write a shared cache.** A measurement cache or a
  scheduling record that anything can write is an injection point; trusted runs
  write, untrusted runs read.

The rules on updating invalidated prose and naming the offending commit are
owned by [`pull-requests`](../pull-requests/SKILL.md); the one on escape-hatch
flags by [`system-architect`](../system-architect/SKILL.md#9-failure-and-invariants-first).

### Cadence

| Frequency | What |
| --- | --- |
| Every commit | Fast unit and integration tests, lint, format, type check |
| Every pull request | The full ordinary suite, the compile matrix, interface-compatibility checks, and the expensive area-specific checks *when the change carries the label for that area* |
| Every merge to main | Everything, unconditionally, including the exhaustive concurrency checks that are label-gated on pull requests |
| Nightly | Dependency audit, long fuzz runs, stress tests, platform matrices |
| Per release | Downstream consumers' suites; a benchmark run recorded into the repository with its environment |

Label-gating lets an expensive check be opt-in for contributors and mandatory
at the point where mistakes become permanent.

---

## Adopting this incrementally

You cannot build all of the above, and a small codebase should not try. In
rough order of value per hour:

1. **A minimal reproduction before any fix.** Free, and it becomes the test.
2. **A regression test per defect, named after the defect.** Free.
3. **Injected clock, I/O, and randomness.** Nothing else on this list is
   possible without them, and retrofitting them is expensive.
4. **A property test on the most arithmetic-heavy pure function you have**:
   geometry, layout, parsing, scheduling, money. One good property test is
   worth thirty examples.
5. **A round-trip property on anything you serialise.** Most codebases depend
   on it and none assert it.
6. **A compile or build matrix** over the configurations you claim to support.
7. **A structure test for the absences** once there is more than one module.
8. **Dated measurement records in the repository**, with the machine written
   down, once there is anything worth timing.

Then, only when a class of defect starts recurring, add the instrument that
catches that class: fuzzing when parsing bugs repeat, exhaustive concurrency
checking when races repeat, downstream suites when you keep breaking consumers.

**The order matters.** Build the seams first. An instrument you cannot point at
anything is worse than no instrument, because it looks like coverage.
