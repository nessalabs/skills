---
name: test-gaps
description: "Walk the fixes merged since a recorded checkpoint commit, work out for each one why the existing tests let the bug through, and add the missing coverage to the repository's chosen regression suite, all in one pull request that also moves the checkpoint forward. Built to run unattended on a schedule as well as by hand. Use when asked to find test gaps, do a retro on recent bugs, check why tests missed a fix, or when a scheduled job invokes /test-gaps."
---

# Test gaps

Every bug that reached the main branch got past the tests. The fix usually
adds a test, but that test was written by someone who already knew the bug,
so it often checks the one input that broke and nothing around it. This skill
goes back over recent fixes and asks a different question: **what did our
tests look at, and what did the bug need that they never looked at?** The
answer is a missing condition (a second conversation, a restart, a mode switch
mid-turn, a slow reply). Add that condition to the suite, and the next bug of
the same shape fails a test instead of reaching a user.

That question is [core rule 2](../system-architect/SKILL.md#core-rule-2-a-check-only-holds-for-what-it-looked-at)
applied to tests: a passing test only vouches for the conditions it ran
under.

## What the repository provides

1. **A checkpoint file.** Default path `.github/test-gap-checkpoint`; the
   repository's agent instructions may name another. The first line that is
   not blank and does not start with `#` is a full commit hash. Every change
   on the default branch up to and including that commit has been reviewed.
   Nothing else in the file matters.
2. **A suite of record.** The repository's agent instructions or coding
   standards name the suite new coverage goes into and say how to add a
   case. Read that section and follow it; do not guess a suite from the
   directory layout.

If either is missing, stop and say which.

## Before you start

- **One run at a time.** Look for an open pull request from an earlier run
  (one that changes the checkpoint file). If there is one, stop and report
  it. The checkpoint only moves when that pull request merges, so a second
  run would review the same range and add the same cases again.
- **Full history.** Scheduled jobs often start from a shallow clone, where
  the checkpoint commit is simply absent. Fetch the whole default branch
  (`git fetch --unshallow origin` when the clone is shallow) and work from
  `origin/<default>`, never from a local branch that may be stale.
- **The checkpoint is still on the branch.** Check
  `git merge-base --is-ancestor <checkpoint> origin/<default>`. If it is not
  (history was rewritten), stop and report it rather than picking a new
  starting point yourself. A commit that cannot be found at all is a fetch
  problem, not a rewrite.

## Procedure

1. **List what is new.** Take the tip of `origin/<default>` now as the end
   of this run's range. List merges in order:
   `git log --first-parent --reverse <checkpoint>..<tip>`. First-parent keeps
   one entry per merged pull request, whether it was squashed or merged.
   If the range is empty, stop: there is nothing to do and nothing to commit.
   For an entry that is a real merge commit, read its change with
   `git diff <sha>^1 <sha>` (`git show` prints a combined diff that is often
   empty) and undo it with `git revert -m 1`. Review at most 20 fixes in one
   run, oldest first; the rest wait for the next run.

2. **Pick out the fixes.** Read each entry's subject, body, and linked pull
   request or issue. A fix is a change that corrected behaviour already on
   the default branch: a reported bug, a regression, a revert, a flaky test
   whose cause was real. Judge by what changed, not by a `fix:` prefix; many
   fixes are titled as features ("let a conversation take messages again
   after a failed turn"). A change that bundles a fix with new work counts;
   review only the fix part. A fix to a test, a fake, or CI tooling is
   skipped as `tooling`, unless the bug it was hiding reached the product.
   A pure feature, refactor, or documentation change is not a fix; list it
   as skipped, with one word saying why.

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
   can: revert the fix's non-test changes in a scratch copy, run the test,
   see it fail, throw the copy away. Where that is too costly, say the
   verdict is inferred. A fix whose own test only checks the exact input
   that broke is still a gap if the condition behind it is not in the suite
   of record.

6. **Add the coverage.** For each gap, put the missing condition into the
   suite of record, following its own instructions for adding a case.
   - Extend an existing case before adding a new one. Group gaps that share
     a condition; one "reopen after a restart" case can hold three fixes.
   - The new case must fail with the fix undone and pass with it, checked
     the same way as in step 5. A case that passes either way is not
     coverage; drop it.
   - Write it as a regression test, as
     [testing](../coding/references/testing.md#regression-tests-carry-the-mechanism)
     and [`method`](../method/SKILL.md#turn-the-finding-into-an-artefact)
     describe: named after the defect, carrying its mechanism and the fix
     commit, plus whatever the suite's own instructions add.
   - A bug the suite cannot express (a pixel, a platform the suite does not
     run on) goes in the report with where it should be held instead.

7. **If the bug is back, stop treating it as coverage.** When a new case
   fails on the current branch with the fix in place, you have found a live
   defect. Do not weaken, skip, or delete the case to get a green run. Look
   for an existing issue about it first; if none, open one with the failing
   case as the reproduction, leave the case out of
   this pull request, and say so in the report.

8. **Move the checkpoint.** An entry counts as reviewed once it has a row
   in the report, "unclear" and "skipped" included. Set the checkpoint to
   the last entry of the unbroken run of reviewed entries from the start of
   the range: the tip from step 1 when you finished, an earlier entry when
   the cap or a problem stopped you. Never move it past an entry with no
   row, and never to a tip that appeared after step 1.

9. **Open one pull request** with the new cases and the checkpoint change
   together, described per [`pull-requests`](../pull-requests/SKILL.md).
   Before/After says which range was reviewed and how many gaps were closed.
   Under *How we checked it*, one row per reviewed entry: commit, the
   observable bug, why the tests missed it, and what holds it now (an
   existing test, a new case, an issue, or a skip reason). If no gaps were
   found, the pull request carries only the checkpoint change and that
   table; it is the record that the range was reviewed.

## Running on a schedule

An unattended run has no one to ask. Make every call yourself and write each
one into the pull request. Open the pull request as a draft and drive its
checks green, then mark it ready for review. When a check fails, first find
out whether it fails on the default branch too. If it does, say in the pull
request that it was already failing, leave it a draft, and stop; do not widen
the change to fix it. A failure you caused and could not fix is reported in
the pull request, never left silent. An empty range, or an earlier run's
pull request still open, ends the run with no branch and no pull request.
