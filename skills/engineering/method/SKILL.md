---
name: method
description: "How defects and regressions actually get found, how a hypothesis gets verified before it is acted on, and how a fix is stopped from being undone. Covers the instruments (property tests and fuzzing, exhaustive concurrency checking, differential testing, checkers, measurement kept as a record, production telemetry), reproducing and minimising, explaining the mechanism and bounding the blast radius, what counts as evidence, and which artefact holds each kind of finding in place. Use when investigating a bug, chasing a performance problem, deciding what to automate or test, or setting up CI checks."
---

# Finding, verifying, and not drifting

The other skills describe the patterns long-lived systems end up with. This
skill is about the process behind them:

1. **Finding.** Most defects are caught by instruments built ahead of time,
   rather than by reading code.
2. **Verifying.** A hunch needs a reproduction, a mechanism, preconditions, and
   a bounded blast radius before you change code.
3. **Not drifting.** Without a check or record behind it, a fix is easily
   undone by a later refactor.

## 1. Finding

Build instruments roughly in order of what they catch that nothing else can
(see [instruments.md](references/instruments.md) for setup details):

- **Properties and fuzzing.** Highest yield for parsers, serialisers, and
  transforms: assert round-trip, differential, invariant, or crash/hang-free
  properties across generated inputs.
- **Exhaustive concurrency checking.** Ordinary tests sample interleavings at
  random; model-checking primitives behind a build flag enumerates them.
- **Zero-authoring checkers.** Undefined-behaviour interpreters, sanitisers,
  leak detectors, and scheduled vulnerability audits catch bugs nobody wrote a
  test for. Run each in its own narrowly named CI job.
- **Shared corpora, build matrices, and consumer suites.** Run one declarative
  corpus across every implementation, compile the feature powerset so optional
  features stay optional, and run downstream suites (or your app's end-to-end
  suite) against branch changes.
- **Recorded measurements and production telemetry.** Profile before acting on
  a performance guess, commit dated benchmarks with machine and library details,
  track build time and binary size alongside runtime, and keep flagged telemetry
  on hot paths so unexpected production regressions produce actionable data.

**Use coverage to find untested code, never as a numeric target.** Exploring
unexecuted paths routinely turns up real bugs to file separately; chasing a
percentage produces tests that assert nothing. The tell is whether the result
is "we found these three bugs" or "we reached 80%".

**Treat bots, static analysers, and LLMs as hypothesis generators.** They
produce candidates, never proof. Ask a model to inspect a specific function and
say so plainly in the pull request; have a human re-derive a bot-flagged
failure path to confirm the fix actually closed it; require contributors to
explain changes in their own words with model-derived context quoted and
marked. Every generated finding enters phase 2 before merge.

## 2. Verifying

**Reproduce before fixing.** Without a reproduction, you cannot tell whether
your change fixed the defect.

**Minimise the reproduction and treat it as a deliverable.** Twenty lines that
fail deterministically outlive the bug report, the fix, and the analysis
because they become a permanent test.

**Explain the mechanism.** A complete write-up gives the step-by-step chain of
events, a numbered list of the preconditions (including ordering), an explicit
bound on the blast radius (for example: "because of precondition three, this
can never return a wrong answer; it only affects which span is reported"), and
for a regression the introducing commit by hash and subject. Once you know the
mechanism, check neighbouring paths where the same code was copied.

**Know what class of evidence you hold.** A written policy, a reviewer's
request, a configured CI job, a passed job, a bisection showing that toggling
one call changes the symptom, and your own reproduction are distinct things.
Bisection shows correlation, not root cause; an approval proves someone
approved; a closed proposal does not prove its design was rejected. State which
kind you have, and do not upgrade one into another.

**Test the promise where it is made.** One part working does not prove the
whole promise holds. A bounded queue means little if it drains into an
unlimited one; a macro crate that builds proves nothing about whether its
generated code builds for users; dropping a handle does not prove the task
holding the resource stopped; a compiled feature does not prove it is enabled
at runtime. Ask where the promise is actually made, and test there.

**Do not re-run a flake.** Reconstruct the interleaving that produced the
observed value and explain why it can happen. A scheduling change can
legitimately remove a wake-up and change a counter; check whether that is what
occurred.

**Treat your own claims as hypotheses.** Take your claim that a case is handled
and try to construct the interruption, repetition, or re-entry that breaks it
(review-side version in
[`pull-requests`](../pull-requests/SKILL.md#the-claim-is-a-hypothesis)).

**Try to refute your fix.** For anything subtle, ask what input or sequence
would make your change fail rather than only checking that your test passes.

**Prove performance changes preserve the observable contract.** State the
contract at the right level — bytes for a batch API, progress and ordering for
streaming or scheduling (see [`coding`](../coding/SKILL.md#5-performance)).

**Measure the fix and report honestly when it falls short.** If a narrow fix
reintroduces the defect the original change existed to prevent, say so instead
of shipping it. If a cleverer optimisation barely helps, report that plainly
rather than merging it anyway.

**Weigh what the fix costs alongside what it buys.** A correctness fix that
adds measurable CPU cost on a real workload is a trade-off; name it as one.

**Reverting is a normal outcome.** When a change costs more than it buys, take
it out instead of carrying it alongside a partial fix while looking for the
real one. Remove an optimisation that nobody can safely modify, regardless of
its benchmark; "too subtle to fix safely" is a valid reason.

**Check follow-up history before copying a merged change.** A change reverted a
month later or patched three times teaches something different from what its
original description claims. Read forward in history first.

## 3. Not drifting

Turn every phase-2 finding into an artefact that fails when the property stops
holding, and make drift structural rather than relying on discipline. In
regression tests, record the mechanism — what the code was doing, why the bug
was possible, and any more thorough fix considered and rejected and why — so
later readers do not reintroduce something worse.

See [anti-drift.md](references/anti-drift.md) for the finding-to-artefact
table, drift-prevention patterns (single-file capability gating, `not(...)`
complements without De Morgan rewrites, doc/guard sync, instability gates, and
untrusted-input cache isolation), and CI cadence. Updating invalidated prose
and naming the offending commit live in
[`pull-requests`](../pull-requests/SKILL.md); escape-hatch flags live in
[`system-architect`](../system-architect/SKILL.md#9-failure-and-invariants-first).

## Adopting this incrementally

A small codebase should not build everything at once. Roughly by value per hour:

1. **A minimal reproduction before any fix.** Free, and it becomes the test.
2. **A regression test per defect, named after the defect.** Free.
3. **Injected clock, I/O, and randomness.** Everything else depends on these
   seams, and retrofitting them later is expensive.
4. **A property test on your most arithmetic-heavy pure function** (geometry,
   layout, parsing, scheduling, money).
5. **A round-trip property on anything you serialise.**
6. **A compile or build matrix** over the configurations you claim to support.
7. **A structure test for forbidden dependencies** once you have multiple
   modules.
8. **Dated measurement records in the repository**, with machine and
   environment details, once performance matters.

Add heavier instruments only when a defect class recurs (fuzzing for parsing
bugs, concurrency model checking for races, downstream suites for consumer
breakage). Build the seams first so each instrument actually exercises the code
you care about.
