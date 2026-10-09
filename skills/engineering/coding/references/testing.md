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

## Plan the proof before the code

For a changed async, I/O, or retry guarantee, take the risky step in the planned
flow and name its deciding owner, required state and input, observable effect,
and result, including the failure meaning owed to the caller. A sequence arrow
saying "check", "send", or "stop" does not tell you when the decision holds or
what proves the effect finished. Attach the proof to that step in the existing
plan; a small local change does not need a new document or a concurrency suite.

Choose the cases from the contract before choosing the fixture. Where readiness
or timing matters, distinguish work already ready from work that suspends and
later becomes ready; control the boundary where the decision can change. For a
shared guarantee, follow each result path that uses different machinery,
including refusal. Follow the guarantee through affected consumers that start
or skip consequential work; observe their decisions, not only the producer's
returned value. Distinguish a signal or returned answer from the physical
effect and retained resource it is supposed to establish. Keep typed
failure meaning observable across those paths, including a later refresh or
retry when that is part of the operation.

Make the negative case reach the last decision before the forbidden effect:
keep earlier input and authority valid, and pair it with a permitted case that
actually reaches that effect. An earlier validation error can make a no-effect
assertion pass without testing the intended guard. Use malformed input when
parsing is the boundary under test, not as a substitute for valid admission.
An effect observation can be bytes, durable state, a closed listener, or an
external port invocation when that invocation itself is the forbidden effect.

The plan is sufficient when each changed guarantee has a controlled violating
case, a valid counterpart, and an observation that distinguishes them. State
what the seam cannot establish; add cases only for a remaining contract risk,
not to enumerate every combination or claim exhaustive scheduling proof.

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

A second exception: the usual client tidies input before it reaches you
(lowercases, sorts, removes duplicates), so the input that triggers the bug
never arrives through it. Send the raw input at the lowest real boundary that
keeps it, check the public result, and say which client step hid the bug.

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
broken. Sometimes the shared thing *is* what you are testing, such as
environment variables, which the whole process shares. Then tests running at
the same time can trip over each other. Make them take turns on one shared
lock (including tests that only read), or run them in a separate process. One
lock per variable is not enough, because the whole environment is one shared
thing.

**Control the transition, not elapsed time.** For a race, inject a gate at the
boundary where the overlap can happen, force the overlap, and assert the exact
positive outcome. A sleep and an upper-bound assertion are not evidence when
zero work would also pass. Sometimes you cannot control when the two sides
run, for example when one is the garbage collector. Then pull out the small
piece of shared state they both change, and test it directly in every order
(A then B, B then A). Keep the full end-to-end reproduction as an extra, but
never as the only test, because it only fails some of the time.

**A test must be unable to pass when the intended work never happened.** Before
asserting cleanup, prove the thing existed. Before asserting "no duplicate",
prove exactly one. Before asserting "nothing was parsed", put something
malformed where parsing would have happened. Before asserting something was
*added*, put something else there first and check it is still there
afterwards; otherwise "add" and "replace" look the same. If your fix hides a
warning or error in one case, also check the warning still appears in the
cases next to it; otherwise switching the warning off everywhere would pass
too. Benchmarks follow the same rule: check each loop really did the work, and
that threads, file handles, and memory go back to normal between runs.

**Test with two, not just one.** With one item, you cannot tell "done once per
item" from "done once in total". A file header written inside the loop looks
fine with one batch and breaks with two. Use at least two (including two runs
of the same thing, not only two different things), and check that
headers, footers, and run-once steps appear exactly once, in the right place.

**The same meaning written differently gives the same result.** Many formats let
you say one thing several ways: a field repeated or written as a list, upper or
lower case, a different order. Test that every way gives the same answer,
including the same bytes arriving in different-sized pieces: split the input at
every point and check the answer does not change, with near-misses that must
still count as incomplete. When two inputs disagree and one wins, check the
losing one is removed from what gets passed on, whichever order they came in.

**Async assertions poll by default.** Sample the observable state until the
condition holds or a timeout fires. A fixed sleep is either slow or flaky, and
usually becomes both. Use real time only when the real timer is the thing
being tested. Keep those tests together, give them generous margins, and check
that something actually happened.

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
- Call counts standing in for behaviour. Prefer the observable effect. An
  external port invocation count is useful when dispatch itself is the effect
  the contract forbids, with valid input and a permitted counterpart; counting
  internal helper calls is still an implementation assertion. The exception is
  when the count *is* the bug, such as a loop that spins forever doing nothing.
  Then count it, and also check the task is still alive and waiting, so a task
  that simply crashed cannot pass.
- Each piece of generated code, or boilerplate. But the generator itself is
  code. If a macro or code generator decides behaviour, visibility, or types,
  it is a small compiler: test it once, with examples that must work and
  examples that must fail to compile.
- Framework behaviour. The UI library renders; assume it.
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
  When features split a suite, check its default and aggregate membership too:
  a test or benchmark that builds alone may never be reached by the intended
  CI command. Show that command discovers and executes the affected case.
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
