# Testing

Tests exist to make change safe and to give early feedback on coupling. Code
that is hard to test is not "hard to test"; it is badly coupled, and the test is
telling you so. A test that does neither job is overhead. This file owns the
rules; [`coding`](../SKILL.md#4-tests), [`system-architect`](../../system-architect/SKILL.md#11-tests-are-a-design-instrument),
and the language references point here rather than restating them.

## What gets a test

| Situation | Test |
| --- | --- |
| New behaviour | A test that fails without the change |
| Bug fix | A regression test named after the defect, failing on the old code |
| Domain rule or invariant | Unit test, real objects, no doubles |
| Use case over real infrastructure | Integration test against the real dependency, through the public entry point |
| Contract between modules | Consumer-owned test on the event or DTO shape |
| Architectural absence | Structure test over the module graph |
| Subtle documented semantic | Tests asserting exactly what the documentation claims |
| Type-level invariant | A compile-fail test with a snapshot of the error |
| Quantified performance claim | A benchmark with the stated workload and baseline, kept in CI when it is stable enough to catch regressions |
| Mechanism-only cost reduction | Direct evidence of the removed cost (allocation count, syscalls, a profile), plus the contract tests; no end-to-end magnitude claimed |
| Pure rendering | Nothing, usually. Assert behaviour, not markup |

## Rules

**Public surface by default.** No test-only visibility, no test-only
constructors. If a state is unreachable through the real API, it should not
exist. Building fixtures by calling the same methods production calls is not
friction; it is the test proving the API is usable.

The exception is a protocol the public API cannot drive to the point where it
breaks: a cancellation race, an unsafe representation, a lock-ordering rule. A
module-local test or a bounded model checker is the right instrument there, on
four conditions. It stays in the module, it widens no visibility, it is paired
with a public regression test, and the change says what the model bounded. A
model proves a property of the model within the schedules it explored; that is
worth a lot and is not a proof about production. A single-shard model says
nothing about cross-shard behaviour.

**Real dependencies over mocks.** Mock only what you cannot run: a third-party
service, a paid API, hardware you do not have. Mocking your own domain tests
your mocks. For anything with a local equivalent, use the equivalent.

**Fake the external mechanism, not your orchestration.** When a test replaces
the filesystem, the watcher, the clock, or the transport, production's
ordering, deduplication, lifecycle, and retry logic must still run. Substitute
the lowest nondeterministic boundary only. If the fake contains a second
coordinator or state machine, the seam is too high; move it down.

**Determinism is injected wherever it can be.** Clock, randomness, scheduling,
and ordering arrive as parameters. A test that passes ninety-nine times in a
hundred has already failed: it has taught the team that red does not mean
broken. Where the ambient facility *is* the contract (the environment, a
process-wide engine), isolate at its true scope: one serial domain every
conflicting test takes, including the ones that only read, or a separate
process. A lock per variable does not make a process-global mutation safe.

**Control the transition, not elapsed time.** For a race, inject a gate at the
boundary where the overlap can happen, force the overlap, and assert the exact
positive outcome. A sleep and an upper-bound assertion are not evidence when
zero work would also pass. Where the overlap cannot be gated (a garbage
collector, a native scheduler), extract the shared state transition and test
every ordering of it deterministically; the end-to-end reproduction is a
supplement, never the only gate.

**A test must be unable to pass when the intended work never happened.** Before
asserting cleanup, prove the thing existed. Before asserting "no duplicate",
prove exactly one. Before asserting "nothing was parsed", put something
malformed where parsing would have happened. Before asserting something was
added, seed an unrelated value and assert it survives, or replace and append
look the same. A fix that suppresses a warning, error, retry, or denial also
asserts the signal still fires on the nearby cases, one per leg of the new
condition, or turning the checker off everywhere passes too. A benchmark is
held to the same standard: assert the work each iteration must do, and that
threads, handles, and memory return to baseline between samples.

**Exercise the plural case.** A fixture with one chunk, one item, or one worker
cannot tell per-iteration work from per-container work. Force at least two, and
assert that headers, footers, and one-shot finalisers appear exactly once,
where the format puts them.

**Every legal spelling of one fact gives one result.** Where a format allows
several spellings (repeated fields, lists, case, order), test that each reaches
the same decision and the same normalised value. Where conflicting inputs
resolve to one authority, assert the loser is gone from what goes downstream,
in every order.

**Async assertions poll by default.** Sample the observable state until the
condition holds or a timeout fires. A fixed sleep is either slow or flaky, and
usually becomes both. Real time belongs only in a test whose subject is the
real timer or event loop; group those, use coarse margins, and assert a
positive event.

**One behaviour per test, minimal setup.** Strip the fixture to exactly what
the assertion needs. Anything left in that does not affect the outcome is
misdirection for whoever debugs it later.

**Name the test after the behaviour**, in domain language: what it does, under
what condition, with what result. A numbered test name is a note saying "I did
not know what I was asserting".

**When automation cannot observe the thing**, such as a native or foreign
lifecycle with no harness, say so, and attach reproducible before-and-after
diagnostics from the exact revision, labelled as manual evidence. Do not call
that an automated test.

## What not to test

- Private methods and internal call sequences. These are the things you most
  want to be free to change; a test on them is a refactoring tax. Asserting a
  state or ownership relationship is the exception above; asserting which
  helper was called in which order is the tax.
- Call counts standing in for behaviour. A spy on a counter asserts the
  implementation; a malformed input where the work would have happened asserts
  the behaviour. The exception is where the count *is* the defect, such as a
  busy loop: count the repeated operation, and prove the task is still alive
  and parked, so a dead task cannot pass.
- Framework behaviour. The UI library renders; assume it.
- Each generated instance, or trivially derived boilerplate. The generator is
  code: a macro or code generator that carries behaviour, visibility, or a
  type-level promise is a small compiler, and is tested once at the generator,
  with runtime and compile-fail fixtures for what its output must do.
- Exact markup or pixel output, except where a rendering *is* the product
  behaviour and a snapshot is cheaper than a description.
- Anything that exists for coverage. Coverage finds code nobody has executed;
  it is not a reason for a test to exist. Delete tests that do not earn their
  place.

## Structure and placement

- Unit tests live beside the code they test.
- Integration tests live in their own tree and use only public entry points,
  which is what makes them integration tests rather than large unit tests.
- Separate trees for separate questions: does it compile in every
  configuration, does it work against real external components, does it
  survive load, how fast is it. Each runs on a different cadence and fails for
  a different reason; merged, the slow one stops being run.
- One test file per concern, named for it. A regression file named after the
  defect tells you what it protects without being opened.
- Fixtures and builders are shared *within* a context, never across contexts.
  A fixture shared across a boundary is a shared kernel with worse ergonomics.
- Once there is more than one context, a structure test reads the module graph
  and fails on a violated absence from
  [structure](../../system-architect/references/structure.md#the-absences).
  It converts a recurring review comment into a red build.

## Regression tests carry the mechanism

The regression test for a defect records more than the input: a comment
explaining what the code was doing, why the failure was possible, and the more
thorough fix that was considered and not done, and why. Without that, the next
person "fixes" it properly and reintroduces something worse. The commit that
introduced the defect is named in the fix; the convention is in
[`pull-requests`](../../pull-requests/SKILL.md#commit-messages).
