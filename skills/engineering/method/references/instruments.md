# Instruments for finding defects

Detailed setup and mechanics for the finding instruments summarised in
[`SKILL.md`](../SKILL.md#1-finding). Build them roughly in this order.

## Properties and fuzzing

Assert a property that must hold for all inputs and let a generator attack it:

- **Round-trip**: parse, print, and parse again; the two structures are equal.
- **Differential**: two implementations of one contract agree — a fast path
  against a reference path, or an optimised strategy against a naive one. If
  you claim to match an existing tool, use that tool as the answer key: feed
  the same inputs to both, ignore formatting differences, and turn every
  disagreement into a test of your own. Two formulas that are equal on paper
  can round differently (`(a / n) * s` vs `a * s / n`), so generate inputs at
  the rounding, overflow, cast, and null edges, and either share one order of
  operations or state the tolerance explicitly.
- **Invariant**: assert the module's stated guarantee after every operation.
- **Never panics, never hangs**: on arbitrary input, for anything reading data
  you do not control.

Three details make a fuzz target pull its weight:

- **Scope the property to where it actually holds.** Reject generated inputs
  where behaviour is legitimately ambiguous instead of weakening the assertion
  for all inputs.
- **Make crash output directly actionable.** Print the input in a reproducible
  form rather than an opaque internal structure.
- **Keep every finding permanently.** Check each discovered input into a
  dedicated directory of fuzz-derived regression tests.

## Exhaustive checking for concurrency

Ordinary tests sample thread interleavings at random and miss races. A model
checker enumerates the permutations.

- Route every concurrency primitive through one internal module that re-exports
  either the real primitives or instrumented ones behind a build flag, so the
  whole program becomes checkable by switching build configuration.
- Shrink capacity constants under that build flag so state-space exploration
  terminates.
- Run the model checker on every merge to the main branch, and on pull requests
  labelled as touching that area.
- Run it as a matrix over alternative implementations (such as different queue
  backends), because nobody checks every combination by hand.

## Checkers that need no test authoring

Undefined-behaviour interpreters, address and memory sanitisers, leak
detectors, and scheduled dependency-vulnerability audits catch classes of bugs
nobody wrote a test for.

- Run each checker as its own narrowly named CI job. A single generic "test"
  job that bundles everything only tells you that something broke, not which
  checker tripped.

## One corpus, many implementations

When several implementations satisfy one contract, write the test cases **as
data** in a declarative format and run the whole corpus against every
implementation. Per-implementation suites compile slower, drift apart, and are
harder for newcomers to read.

## The whole matrix, not just the default

Compile-only jobs are cheap and catch broken feature combinations, minimum
toolchain regressions, and broken platform builds.

- Run the feature powerset. It is the only way to verify that optional
  capabilities really are optional.

## Your consumers' test suites

Check out major downstream projects in CI and run *their* test suites against
the current branch so breaking changes are caught before merge. If you have no
external consumers, run the application's own end-to-end suite against the
library change in the same pipeline.

## Measurement, kept as a record

- **Profile before acting on any performance hypothesis.** The function you
  suspect is usually not the bottleneck.
- **Mine the timing data you already emit.** CI logs already carry timestamps;
  parse them to spot badly balanced pipelines without adding new
  instrumentation.
- **Commit benchmark logs to the repository**, dated and labelled with the
  machine and configuration, including the allocator and libc (which shift
  numbers more than most code changes). Hand comparison against a dated record
  beats an unreproducible number in an old comment.
- **Measure non-runtime costs.** Track clean build time and binary size per
  feature against a hello-world baseline. A flag that adds nothing to runtime
  and seconds to every build is still expensive.
- **Keep upstream numbers labelled as upstream.** A benchmark from someone
  else's pull request stays tagged as theirs, with its workload; repeating it
  does not turn it into a verified measurement.

## Production telemetry

Benchmarks only cover workloads you thought of. Unexpected regressions show up
in production, where the only instrument that sees them is telemetry built
before you needed it.

- Add counters and timings behind a flag on the paths you expect to be hot.
- Per-worker metrics let a user hand you a twenty-line reproduction instead of
  an unactionable "it got slower".
