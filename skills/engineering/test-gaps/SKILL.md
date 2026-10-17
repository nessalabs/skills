---
name: test-gaps
description: "Look over the bug fixes that landed recently (by default the last 24 hours of the default branch), work out for each one why the existing tests let the bug through, and add the missing coverage, in one pull request. Works on any repository with no setup, and runs unattended on a schedule as well as by hand. Use when asked to find test gaps, do a retro on recent bugs, check why tests missed a fix, or when a scheduled job invokes /test-gaps."
---

# Test gaps

Every bug that reached the main branch got past the tests. The fix usually
adds a test, but that test was written by someone who already knew the bug,
so it often checks the one input that broke and nothing around it. This skill
goes back over recent fixes and asks a different question: **what did our
tests look at, and what did the bug need that they never looked at?** The
answer is a missing condition (a second request, a restart, a setting changed
partway, a slow reply). Add that condition to the tests, and the next bug of
the same shape fails a test instead of reaching a user.

That question is [core rule 2](../system-architect/SKILL.md#core-rule-2-a-check-only-holds-for-what-it-looked-at)
applied to tests: a passing test only vouches for the conditions it ran
under.

## Which commits to look at

Pick the start of the range, first match wins:

1. **What the person asked for**: a commit, a tag, or a date ("since
   Monday", "since abc123").
2. **The last run on this machine**, if a state file exists at
   `${XDG_STATE_HOME:-~/.local/state}/test-gaps/<host>/<owner>/<repo>`. Its
   only content is the commit hash the previous run reviewed up to. It lives
   outside the repository, so nothing is committed and every person keeps
   their own.
3. **Otherwise, the last 24 hours** of the default branch. A daily schedule
   with this default covers every commit once, with no state to keep.

The end of the range is the tip of `origin/<default>` when you start. Fetch
it first, and fetch enough history to reach the start (`git fetch
--shallow-since=<date>` or `--unshallow` in a shallow clone); never work from
a local branch that may be stale. If the start is a commit, check
`git merge-base --is-ancestor <start> origin/<default>`; if it is not an
ancestor, history was rewritten, so say so and fall back to the 24-hour
window.

List the entries with `git log --first-parent --reverse <start>..<tip>`, or
`--since=<date>` for a date. First-parent keeps one entry per merged change,
whether it was squashed or merged. For an entry that is a real merge commit,
read its change with `git diff <sha>^1 <sha>` (`git show` prints a combined
diff that is often empty) and undo it with `git revert -m 1`.

If the range is empty, stop: nothing to do, nothing to commit.

## Where new tests go

If the repository's agent instructions, contributing guide, or coding
standards name a suite for regression or end-to-end coverage and say how to
add a case, use that and follow its instructions. Otherwise put each test
next to the existing tests for the code the fix touched, in their style. Do
not start a new test framework.

## Procedure

1. **Check for an earlier run's work.** Look for open pull requests from
   earlier test-gap runs. Leave out any fix they already cover, so two runs
   never add the same case.

2. **Pick out the fixes.** Read each entry's subject and body, and its linked
   pull request or issue when the message is too thin ("Merge pull request
   #12 from …"). Words like fix, bug, regression, revert, crash, broken,
   missing, wrong, or "again" are the first signal, but judge by what
   changed: many fixes are titled as features ("let a conversation take
   messages again after a failed turn"). A change that bundles a fix with
   new work counts; review only the fix part. A fix to a test, a fake, or
   CI tooling is skipped as `tooling`, unless the bug it was hiding reached
   the product. A pure feature, refactor, or documentation change is not a
   fix; list it as skipped, with one word saying why. Review at most 20
   fixes in one run, oldest first.

3. **For each fix, state the bug as something observable.** One sentence a
   test could check: "the second message in a reopened conversation was
   never delivered", not "fixed a race in the outbox". If the fix does not
   say, read the diff and the tests it added until you can write that
   sentence. If you cannot, mark it unclear and move on; do not invent a
   bug to test.

4. **Find why the tests missed it.** Name the tests that ran over the
   broken code before the fix, then say which of these let it through:

   | Why it got through | What it looks like |
   | --- | --- |
   | Nothing reached it | No test executed the broken path at all |
   | Wrong conditions | A test ran the path, but never with what the bug needed: a second time, after a restart, with two at once, a setting changed partway, a delay, a failure |
   | Wrong thing checked | The test asserted a stand-in ("no error", "request sent", "animations finished") instead of what the user sees |
   | Fake disagrees with real | A mock or fake behaved differently from the real component in exactly the way that mattered |
   | Wrong level | Unit tests passed on each part; the bug lived in how the parts met |

   Several can apply; name the one the bug most depends on. This is the
   finding the pull request exists to report.

5. **Decide whether it is still a gap.** It is covered when a test on the
   current branch would fail if the fix were undone, and that test checks
   the promise where it is made, as
   [`method`](../method/SKILL.md#2-verifying) puts it. Prove it where you
   can: undo the fix's non-test changes in a scratch copy, run the test, see
   it fail, throw the copy away. Where that is too costly, say the verdict
   is inferred. A fix whose own test only checks the exact input that broke
   is still a gap if the condition behind it is tested nowhere else.

6. **Add the coverage.** For each gap, add a case where the section above
   says.
   - Extend an existing case before adding a new one. Group gaps that share
     a condition; one "reopen after a restart" case can hold three fixes.
   - A new case must be seen failing with the fix undone and passing with
     it. If the fix cannot be undone cleanly, leave the case out and record
     it as unproven. A case that passes either way is not coverage; drop it.
   - Write it as a regression test, as
     [testing](../coding/references/testing.md#regression-tests-carry-the-mechanism)
     and [`method`](../method/SKILL.md#turn-the-finding-into-an-artefact)
     describe: named after the defect, carrying its mechanism and the fix
     commit, plus whatever the repository's own instructions add.
   - A bug the tests cannot express (a pixel, a platform CI does not run)
     goes in the report with where it should be held instead.

7. **If the bug is back, stop treating it as coverage.** When a new case
   fails on the current branch with the fix in place, you have found a live
   defect. Do not weaken, skip, or delete the case to get a green run. Look
   for an existing issue about it first; if none, open one with the failing
   case as the reproduction, leave the case out of this pull request, and
   say so in the report.

8. **Open one pull request** with the new cases, described per
   [`pull-requests`](../pull-requests/SKILL.md). Before/After says which
   range was reviewed and how many gaps were closed. Under *How we checked
   it*, one row per reviewed entry: commit, the observable bug, why the tests
   missed it, and what holds it now (an existing test, a new case, an issue,
   unproven, or a skip reason). If no gaps were found, open no pull request
   and give the table in your summary instead.

9. **Record where you stopped.** An entry counts as reviewed once it has a
   row, "unclear" and "skipped" included. If a state file is in use, write
   the last entry of the unbroken run of reviewed entries from the start of
   the range: the tip you started from when you finished, an earlier entry
   when the cap stopped you. Never record a commit past an entry with no
   row. Without a state file, say in the summary where you stopped if it
   was short of the tip, so the next run can be pointed there.

## Running on a schedule

An unattended run has no one to ask. Make every call yourself and write each
one into the pull request. Open the pull request as a draft and drive its
checks green, then mark it ready for review. When a check fails, first find
out whether it fails on the default branch too. If it does, say in the pull
request that it was already failing, leave it a draft, and stop; do not widen
the change to fix it. A failure you caused and could not fix is reported in
the pull request, never left silent. Schedule the run daily to match the
24-hour default; a cloud run starts with no state file, so it relies on that
window.
