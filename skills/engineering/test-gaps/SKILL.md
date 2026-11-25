---
name: test-gaps
description: "Look over the bug fixes that landed recently (by default the last 24 hours of the default branch), work out for each one why the existing tests let the bug through, and add the missing coverage, in one pull request. Works on any repository with no setup, and runs unattended on a schedule as well as by hand. Use when asked to find test gaps, do a retro on recent bugs, check why tests missed a fix, or when a scheduled job invokes /test-gaps."
---

# Test gaps

Every bug that reached the main branch got past the tests. The fix usually adds
a test, but someone who already knows the bug often checks only the one input
that broke. This skill asks a broader question: **what did our tests look at,
and what did the bug need that they never looked at?** The answer is a missing
condition (a second request, a restart, a setting changed partway, a slow
reply). Adding that condition means the next bug of the same shape fails before
reaching users.

That is [core rule
2](../system-architect/SKILL.md#core-rule-2-a-check-only-holds-for-what-it-looked-at)
applied to tests: a passing test only vouches for the conditions it ran under.

## Range and workspace

Pick the start of the range, first match wins:

1. **What the person asked for**: a commit, tag, or date ("since Monday",
   "since abc123").
2. **The last run on this machine**, from the XDG state file at
   `${XDG_STATE_HOME:-$HOME/.local/state}/test-gaps/<host>/<owner>/<repo>`.
3. **Otherwise, the last 24 hours** of the default branch (scheduled daily runs
   should ask for a slightly longer window, such as 26 hours, for late starts).

Fetch the remote default branch first, resolve the start commit, and list
first-parent entries up to `<tip>`. If the range is empty, stop. Otherwise do
all work in a clean git worktree on a new branch from `<tip>`, following repo
branch naming rules.

See [git-and-automation.md](references/git-and-automation.md) for git commands,
shallow-clone/root-commit edge cases, rebased PR grouping, reversing non-test
diffs safely, cursor rules, and unattended scheduled runs.

## Where new tests go

If the repository's agent instructions, contributing guide, or coding standards
name a suite for regression or end-to-end coverage and explain how to add a
case, follow those instructions (a passing mention of "regression tests" does
not count). Otherwise put each test next to the existing tests for the code the
fix touched, in their style. Do not start a new test framework.

## Procedure

A review-only run (dry run, or "why did the tests miss these") runs steps 1–5,
reports the table with the case it would add for each gap, and stops without
writing tests or updating the state file.

1. **Check for an earlier run's work.** Pull requests from this skill start
   with `test-gaps:`. Search open change requests on the forge for that prefix
   and skip fixes already covered. Search again right before opening yours; if
   another run's request appeared in between, add your remaining cases to it or
   close yours to avoid duplicates. If forge access is unavailable, say so in
   the report and continue.

2. **Pick out the fixes.** Read each entry's subject, body, and linked PR/issue
   when the message is thin. Keywords (fix, bug, regression, revert, crash,
   broken, missing, wrong, "again") are a first signal, but judge by what
   changed — fixes are often titled as features. Bundled fix-plus-feature
   entries count (review only the fix part). Skip test or CI tooling fixes as
   `tooling` (a fix making a fake match the real component is `tooling` too,
   and counts as evidence of "fake disagrees with real" for the product fix it
   hid). Skip pure features, refactors, and docs with a one-word reason,
   grouped onto one line per reason by hash. Cap at 20 fixes (not entries) per
   run, oldest first, finishing the entry the cap falls in. If unreviewed fixes
   remain with no state file to resume from, list them in the PR (or an issue)
   so they are not silently dropped.

3. **State each bug as something observable.** Write one sentence a test could
   check ("the second message in a reopened conversation was never delivered",
   not "fixed a race in the outbox"). Read the diff and added tests until you
   can write it. Mark `unclear` only after reading the diff; never invent a bug.

4. **Find why the tests missed it.** Name the tests that ran over the broken
   code before the fix, then pick the main reason the bug got through:

   | Why it got through | What it looks like |
   | --- | --- |
   | Nothing reached it | No test executed the broken path at all |
   | Wrong conditions | A test ran the path, but never with what the bug needed: a second time, after a restart, with two at once, a setting changed partway, a delay, a failure |
   | Wrong thing checked | The test asserted a stand-in ("no error", "request sent", "animations finished") instead of what the user sees |
   | Fake disagrees with real | A mock or fake behaved differently from the real component in exactly the way that mattered |
   | Wrong level | Unit tests passed on each part; the bug lived in how the parts met |

   Several can apply; name the one the bug most depended on.

5. **Decide whether it is still a gap.** A fix is covered when a test that CI
   actually runs fails with the bug put back, checking the promise where it is
   made ([`method`](../method/SKILL.md#2-verifying)) at a level the
   [testing rules](../coding/references/testing.md) allow. Verify in a scratch
   copy by reversing only non-test changes (or making the smallest edit that
   restores the old behaviour for large/tangled fixes), running the test to see
   it fail, and discarding the copy. If you could not run it, mark the verdict
   inferred. A test checking only the exact failing input still leaves a gap if
   the underlying condition is tested nowhere else.

6. **Add the coverage.** For each gap, add a case in the location chosen above:
   - Extend an existing scenario or fixture first; gaps sharing a condition can
     share setup, while each fix keeps its own test (one behaviour per test).
   - Verify the new case fails with the bug put back and passes without it. If
     you cannot restore the bug, omit the case and record it as `unproven`;
     drop any case that passes either way.
   - Write it as a regression test per
     [testing](../coding/references/testing.md#regression-tests-carry-the-mechanism)
     plus repo instructions.
   - If the suite cannot express the bug (a pixel issue, a platform CI does not
     run), report it with where it should be held instead.

7. **Handle live regressions separately.** If a new case fails on the current
   branch with the fix in place, do not weaken, skip, or delete it. Check for
   an existing issue; if none exists, open one with the failing case as the
   reproduction, omit the case from this PR, and note it in the report.

8. **Open one pull request** titled `test-gaps: <range>`, per
   [`pull-requests`](../pull-requests/SKILL.md). State the range and gap count
   in Before/After. Under *How we checked it*, include one row per reviewed
   entry: commit, observable bug, why tests missed it, and what holds it now
   (existing test, new case, issue, unproven, or skip reason). If no gaps were
   found, open no PR and end with the table. Unattended scheduled runs open as
   a draft per [git-and-automation.md](references/git-and-automation.md#running-on-a-schedule).

9. **Record where you stopped.** On a persistent machine (not a fresh cloud
   job), advance the XDG state file to the last commit of the unbroken run of
   reviewed entries from the start of the range, per
   [git-and-automation.md](references/git-and-automation.md#state-file-and-cursor-advancement).
