---
name: coding
description: "The working method for any code change - a feature, a fix, a refactor, or a review. The problem-solving loop (restate, locate, hypothesise, refute, smallest change, prove, describe, hold), what to settle before writing, how to write, failure-first design, what to test, how to do performance work, how to shape the change, and how to report what you did. Points into language references for Rust and React/TypeScript. Use whenever you are about to write or modify code, or before opening a pull request."
---

# Coding

This skill covers how to work through a code change. Each rule lives in one
place; where a section links elsewhere, that file owns the rule.

| Layer | Where | When |
| --- | --- | --- |
| System design | [`system-architect`](../system-architect/SKILL.md) | Designing, structuring, or reviewing across files |
| Working method | this document | Every code change |
| Contracts and state | [contracts & state](references/contracts-and-state.md) | Input rules, intermediate states, or cross-owner messages |
| Failure-first checklist | [failure-first](references/failure-first.md) | Edge cases for state, bounds, cleanup, and shutdown |
| Performance checklist | [performance](references/performance.md) | Benchmarks, contract parity, caching, and scheduling |
| Testing | [testing](references/testing.md) | Choosing what to test and how |
| Language specifics | [Rust](references/rust.md), [React & TypeScript](references/react-typescript.md) | Writing in that language |
| Investigation and proof | [`method`](../method/SKILL.md) | Debugging, profiling, or deciding what to automate |
| Pull requests and review | [`pull-requests`](../pull-requests/SKILL.md) | Sizing, describing, or reviewing a change |
| Runtime paths | [`trace`](../trace/SKILL.md) | Tracing how a feature runs or invoking `/trace` |
| Plain writing | [`wdym`](../wdym/SKILL.md) | Explaining your work to a person |

For languages without a reference here, follow this method, match the
surrounding idioms, and state plainly that you had no language-specific guide.

## 0. The loop

Every change—from a one-line fix to a subsystem—follows these eight steps. When
stuck, check which step you skipped.

1. **Restate the problem** in the product's words and as a concrete condition
   that must hold afterward. Wait until "done" is clear before editing.
2. **Locate the information.** Find who owns the facts needed to decide; read
   similar code and the history of the files you plan to touch.
3. **Hypothesise the mechanism.** State what causes the behaviour ("a per-item
   function scans the whole list") rather than the symptom ("it is slow").
4. **Try to refute it** before acting: reproduce, trace, or measure. Avoid both
   untested guesses and waiting for certainty; state a mechanism and try to
   break it.
5. **Make the smallest change that satisfies the condition**, designing
   interrupted, repeated, and concurrent paths before the happy path.
6. **Prove it** as the claim demands: a test that fails without the change, a
   measurement with its workload, or an argument that the invariant holds.
7. **Describe it** so a stranger can judge it: why, what changed, what you left
   out, and what you did not run.
8. **Leave an automated check** that fails if the finding stops holding, so a
   later refactor cannot quietly undo it.

## 1. Before writing anything

**Match the surrounding code.** Read two or three nearby places doing similar
work and match their naming, error handling, layout, test style, and comment
density; introduce a new style only when justified. **Use the product's words**
before writing a type—if you have to invent a word, keep looking.

**Answer four questions before editing:**
1. *Who owns the information to decide?* Put the logic there instead of
   guessing, copying, or re-checking another owner's fact
   ([core rule 1](../system-architect/SKILL.md#core-rule-1-every-fact-has-one-authority)).
2. *What must always stay true?* Name the invariant and the enforcing function.
3. *What happens if this stops halfway, runs twice, or races?* Solve that before
   the happy path (§3).
4. *How would someone delete this?* If removal touches more than this module
   plus one adapter, the boundary is wrong.

**Check the level of the change.** Needing a new parameter on a core type, a new
branch in a core function, or a threaded flag usually means composing on top of
the core instead
([`system-architect`](../system-architect/SKILL.md#6-small-core-composable-pieces)).

### Principle: explicit contracts and state transitions

When correctness depends on input rules, intermediate states, or messages
between owners, define inputs, preconditions, invariants, and postconditions up
front. Validate meaning before transforms erase bad input, keep pure decisions
separate from effects, and prove transitions through observable behaviour. Full
rules: [contracts & state](references/contracts-and-state.md).

## 2. While writing

- **Build only what is needed now.** Wait for the third real instance before
  designing a general abstraction.
- **Skip speculative options.** Do not add unused settings, extension points, or
  forwarding layers. A setting earns its place when a caller contract or
  supported workloads need policies the owner cannot pick; state its default,
  range, and trade-off, and verify it changes behaviour. One caller alone proves
  neither that a setting is needed nor that it must be a constant.
- **Extract on the second use**, only when both places express the same idea
  rather than matching lines by coincidence. A local, block, or comment is often
  simpler than a helper function.
- **Keep control flow obvious.** Use early returns, hoist conditions to the
  caller, and avoid hidden global state. Exception: if another thread can
  invalidate a check, keep the check and action in one protected owner
  operation—a caller-side pre-check is only a hint.
- **Make costs visible.** Surface allocation, blocking, I/O, and retries at the
  call site or in the signature.
- **Comments explain why**—constraints, surprises, dead ends, or the issue that
  forced a shape. Delete comments that paraphrase the code.
- **Fix stale names in the same change.**
- **Audit every caller when merging cases.** Merging `Warning` and `Error` into
  `Message` with a level still compiles, but old checks may quietly match both;
  verify whether each site meant "any of these" or "only this one".

## 3. Failure first

Design interrupted, repeated, and concurrent paths before the happy path. Ask
six core questions:

1. **State and identity:** Does every state have one meaning and one owner, with
   ids unique across runs/generations and authority in the key?
2. **Cues versus facts:** Are you acting on a confirmed fact, or a clue (empty
   read, exit, timeout, unresolved name, ambient setting) with other causes?
3. **Bounds and resources:** Does every queue, buffer, and retry loop enforce a
   real bound on the single path all callers pass, without holding shared
   capacity for idle work?
4. **Cleanup and re-entrancy:** Is every reservation rolled back or filled on
   failure, intent published before the first async boundary, cleanup tied to
   acquisition, and every external callback treated as a panic/re-entry boundary?
5. **Retries and duplication:** If this runs twice, is it idempotent or keyed,
   with one execution claim for work that must run once?
6. **Shutdown and progress:** What does accepting work promise at shutdown, and
   does a temporary missing prerequisite keep accepted work alive?

Full 20-rule operational checklist: [failure-first](references/failure-first.md).

## 4. Tests

Choose evidence using [testing](references/testing.md#what-gets-a-test),
including unchanged-contract evidence for refactors; explain if a check cannot
be written or run.

Defaults on every change: test through the public surface, prefer real
dependencies over mocks, inject determinism, poll rather than sleep, keep setup
minimal, name tests after behaviour, and ensure the test fails if the work never
happened. File unrelated bugs found while testing separately.

## 5. Performance

Locate bottlenecks before optimising:

1. **Reproduce and profile first**, and name what you found
   ([`method`](../method/SKILL.md)).
2. **Investigate in order:** repeated work (accidental quadratics, copying in a
   growing loop, per-item recomputation), synchronisation and wake-up overhead,
   queueing and retention, then data movement and allocation.
3. **State the expected impact** ("1–2% of runtime, so expect 0.5–1% overall")
   so reviewers can weigh the complexity.
4. **Match evidence to the claim.** Quantified claims need scenario, baseline,
   result, and machine; mechanism-only claims name the removed cost without
   claiming end-to-end speedup.

Full rules: [performance](references/performance.md) (strategy switches,
contract/flush parity, losing workloads, skipping work, lazy construction, cache
lifetimes, maintainability, tuned numbers). Language specifics:
[Rust](references/rust.md#performance-in-rust),
[React & TypeScript](references/react-typescript.md#performance-in-react).

## 6. Shaping the change

One reason per change; separate refactor, test, and behaviour commits; land
structural prep ahead of features; ship large features as inert infrastructure
first; aim for under a couple hundred changed lines where practical
([`pull-requests`](../pull-requests/SKILL.md#size-and-shape)). Update prose and
configuration invalidated by the change in the same diff, including CI pins.

## 7. Reviewing your own diff

Read your diff in the web view as a stranger before sharing, checking in order:
right problem, right design, correct, tested, readable, domain names, tidy
([`pull-requests`](../pull-requests/SKILL.md#what-to-actually-look-for)). First
verify that your description's claim is true by walking interrupted, repeated,
and re-entered paths yourself. When using
[contracts & state](references/contracts-and-state.md), check the representation
against promised behaviour, enforcing code, transition tests, and deferred
follow-up.

## 8. Finishing and reporting

- The change does one thing, and the description says what; a test fails without
  it.
- It touches only the files it should (subtracting moves, generated files,
  lockfiles, and formatting), and breaks no absence-invariant
  ([structure](../system-architect/references/structure.md#the-absences)).
- Anything expensive to reverse has a written note or
  [decision record](../system-architect/references/adr.md); names match the
  domain language, including in tests.
- **Report what actually happened.** Mark every check as run, not run, blocked,
  or inconclusive, with output on failure. State skipped scope and why rather
  than shrinking work silently. Report unmeasured numbers as someone else's or
  leave them out.
