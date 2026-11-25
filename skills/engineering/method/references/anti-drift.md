# Preventing drift

Detailed artefact mappings, structural guardrails, and CI cadence for
[`SKILL.md`](../SKILL.md#3-not-drifting).

## Turn each finding into an artefact

Every phase-2 conclusion should leave behind something that fails when the
finding stops being true.

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

**Record the mechanism in the regression test, not just the input.** Explain
what the engine was doing, why the bug was possible, and **any more thorough
fix that was considered and rejected, and why**. Without that note, the next
person may "fix" it more thoroughly and reintroduce something worse.

## Make drift structural

- **One place for policy.** Put conditional compilation and feature gating in
  one file as named capabilities. Call sites reference the capability name,
  never the raw condition.
- **Write complementary conditions so a human can check them by eye.** Write
  the complement as exact `not(...)` around the first condition, without De
  Morgan transformations. Conditions that take boolean algebra to compare will
  drift.
- **Keep documentation and enforcement in sync.** When the docs claim three
  things are unsupported and only two have a guard, make them match and keep
  them matching instead of only editing the docs.
- **Put new public surface behind an instability gate.** Make stabilising it a
  separate decision later; otherwise every merged feature becomes an accidental
  permanent commitment.
- **Keep untrusted inputs out of shared caches.** A measurement cache or
  scheduling record that untrusted runs can write is an injection point;
  trusted runs write, untrusted runs read.

Related rules live with their owners: updating invalidated prose and naming the
offending commit are in [`pull-requests`](../../pull-requests/SKILL.md);
escape-hatch flags are in
[`system-architect`](../../system-architect/SKILL.md#9-failure-and-invariants-first).

## CI cadence

| Frequency | What runs |
| --- | --- |
| Every commit | Fast unit and integration tests, lint, format, type check |
| Every pull request | The full ordinary suite, the compile matrix, interface-compatibility checks, and expensive area-specific checks *when the change carries the label for that area* |
| Every merge to main | Everything, unconditionally, including exhaustive concurrency checks that are label-gated on pull requests |
| Nightly | Dependency audit, long fuzz runs, stress tests, platform matrices |
| Per release | Downstream consumers' suites; a benchmark run recorded into the repository with its environment |

Label-gating lets an expensive check stay opt-in during review while remaining
mandatory at the point where changes become permanent.
