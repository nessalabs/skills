---
name: test-gaps
description: "Look over the bug fixes that landed recently (by default the last 24 hours of the default branch), work out for each one why the existing tests let the bug through, and add the missing coverage, in one pull request. Works on any repository with no setup, and runs unattended on a schedule as well as by hand. Use when asked to find test gaps, do a retro on recent bugs, check why tests missed a fix, or when a scheduled job invokes /test-gaps."
---

# Test gaps

Every bug that reached the main branch got past the tests. The fix usually
adds a test, but that test was written by someone who already knew the bug, so
it often checks the one input that broke and nothing around it. This skill
goes back over recent fixes and asks a different question: **what did our
tests look at, and what did the bug need that they never looked at?** The
answer is a missing condition (a second request, a restart, a setting changed
partway, a slow reply). Add that condition to the tests, and the next bug of
the same shape fails a test instead of reaching a user.

That question is [core rule
2](../system-architect/SKILL.md#core-rule-2-a-check-only-holds-for-what-it-looked-at)
applied to tests: a passing test only vouches for the conditions it ran under.

## Which commits to look at

Pick the start of the range, first match wins:

1. **What the person asked for**: a commit, a tag, or a date ("since Monday",
   "since abc123").
2. **The last run on this machine**, if a state file exists at
   `${XDG_STATE_HOME:-~/.local/state}/test-gaps/<host>/<owner>/<repo>`, where
   `<host>` is the remote's host (`github.com`). Its only content is the
   commit hash the previous run reviewed up to. It lives outside the
   repository, so nothing is committed and every person keeps their own.
3. **Otherwise, the last 24 hours** of the default branch. A schedule should
   ask for a window a little longer than its interval ("since 26 hours ago"
   for a daily run), because jobs start late; the overlap is harmless, since
   step 5 finds fixes already covered.

The end of the range is the tip of `origin/<default>` when you start. Find the
default branch's name with `git ls-remote --symref origin HEAD` rather than
guessing `main`. Fetch it first, and fetch enough history to reach the start
(`git fetch --shallow-since=<date>` or `--unshallow` in a shallow clone);
never work from a local branch that may be stale. Turn a date into a commit,
so the range has a fixed edge and does not depend on commit dates being in
order: `git rev-list -1 --first-parent --before=<date> origin/<default>` (if
it prints nothing, the whole branch is newer than the date: list it all with
`git log --first-parent --reverse <tip>`, since `<root>..<tip>` would leave
the root out). Then check `git merge-base --is-ancestor <start>
origin/<default>`; if it is not an ancestor, it was mistyped or history was
rewritten. Ask the person if there is one; an unattended run says so and falls
back to the 24-hour window.

List the entries with `git log --first-parent --reverse <start>..<tip>`.
First-parent keeps one entry per merged change when changes land squashed or
as merge commits. A repository that rebases changes onto the branch has
several commits per change; group them by their pull request (from the forge,
or the commit messages) and treat each group as one entry. For an entry that
is a real merge commit, read its change with `git diff <sha>^1 <sha>` (`git
show` prints a combined diff that is often empty) and undo it with `git revert
-m 1`.

If the range is empty, stop: nothing to do, nothing to commit.

## Where new tests go

If the repository's agent instructions, contributing guide, or coding
standards name a suite for regression or end-to-end coverage and say how to
add a case, use that and follow its instructions. A passing mention of
"regression tests" does not count as naming one. Otherwise put each test next
to the existing tests for the code the fix touched, in their style. Do not
start a new test framework.

## Procedure

A review-only run (a dry run, or someone asking only "why did the tests miss
these") does steps 1 to 5, reports the table with the case it would add for
each gap, and stops; it writes no tests and no state file.

1. **Check for an earlier run's work.** Every run's pull request has a title
   starting `test-gaps:`. Search the forge's open change requests (pull
   requests on GitHub, merge requests on GitLab, and so on) for that prefix,
   and leave out any fix they already cover, so two runs never add the same
   case. Use whatever access to that forge you have; if none works, say so in
   the report and carry on.

2. **Pick out the fixes.** Read each entry's subject and body, and its linked
   pull request or issue when the message is too thin ("Merge pull request #12
   from …"). Words like fix, bug, regression, revert, crash, broken, missing,
   wrong, or "again" are the first signal, but judge by what changed: many
   fixes are titled as features ("let a conversation take messages again after
   a failed turn"). A change that bundles a fix with new work counts; review
   only the fix part. A fix to a test or CI tooling is skipped as `tooling`. A
   fix that only makes a fake match the real component is `tooling` too, but
   note it: it is evidence of "fake disagrees with real" for the product fix
   it had been hiding. A pure feature, refactor, or documentation change is
   not a fix; list it as skipped, with one word saying why; skipped entries
   share one line per reason in the report, each listed by its hash. Review at
   most 20 fixes (not entries) in one run, oldest first. If the cap leaves
   fixes unreviewed and there is no state file to resume from, list them in
   the pull request (or in an issue, if there is no pull request) as left for
   the next run or a person, so they are not silently dropped.

3. **For each fix, state the bug as something observable.** One sentence a
   test could check: "the second message in a reopened conversation was never
   delivered", not "fixed a race in the outbox". If the fix does not say, read
   the diff and the tests it added until you can write that sentence. Mark it
   unclear only after reading the diff, which should be rare; do not invent a
   bug to test.

4. **Find why the tests missed it.** Name the tests that ran over the broken
   code before the fix, then say which of these let it through:

   | Why it got through | What it looks like |
   | --- | --- |
   | Nothing reached it | No test executed the broken path at all |
   | Wrong conditions | A test ran the path, but never with what the bug needed: a second time, after a restart, with two at once, a setting changed partway, a delay, a failure |
   | Wrong thing checked | The test asserted a stand-in ("no error", "request sent", "animations finished") instead of what the user sees |
   | Fake disagrees with real | A mock or fake behaved differently from the real component in exactly the way that mattered |
   | Wrong level | Unit tests passed on each part; the bug lived in how the parts met |

   Several can apply; name the one the bug most depends on. This is the
   finding the pull request exists to report.

5. **Decide whether it is still a gap.** It is covered when a test that CI
   actually runs would fail with the bug back, and that test checks the
   promise where it is made, as [`method`](../method/SKILL.md#2-verifying)
   puts it, at a level the [testing rules](../coding/references/testing.md)
   allow for that kind of defect. A test CI never runs covers nothing. To put
   the bug back, in a scratch copy, either undo the fix's non-test changes or,
   when the fix is large or tangled with other work, make the smallest edit
   that brings back the old behaviour the bug sentence describes. Run the
   test, see it fail, throw the copy away. When you did not run it, say the
   verdict is inferred. A fix whose own test only checks the exact input that
   broke is still a gap if the condition behind it is tested nowhere else.

6. **Add the coverage.** For each gap, add a case where the section above
   says.
   - Extend an existing case before adding a new one. Group gaps that share a
     condition; one "reopen after a restart" case can hold three fixes.
   - A new case must be seen failing with the bug put back (as in step 5) and
     passing without it. If you cannot put the bug back at all, leave the case
     out and record it as unproven. A case that passes either way is not
     coverage; drop it.
   - Write it as a regression test, as
     [testing](../coding/references/testing.md#regression-tests-carry-the-mechanism)
     and [`method`](../method/SKILL.md#turn-the-finding-into-an-artefact)
     describe: named after the defect, carrying its mechanism and the commit
     that introduced it (find it with `git log -S` or blame on the lines the
     fix changed; name the fix commit when you cannot), plus whatever the
     repository's own instructions add.
   - A bug the tests cannot express (a pixel, a platform CI does not run) goes
     in the report with where it should be held instead.

7. **If the bug is back, stop treating it as coverage.** When a new case fails
   on the current branch with the fix in place, you have found a live defect.
   Do not weaken, skip, or delete the case to get a green run. Look for an
   existing issue about it first; if none, open one with the failing case as
   the reproduction, leave the case out of this pull request, and say so in
   the report.

8. **Open one pull request** titled `test-gaps: <range>` with the new cases,
   described per [`pull-requests`](../pull-requests/SKILL.md). Before/After
   says which range was reviewed and how many gaps were closed. Under *How we
   checked it*, one row per reviewed entry: commit, the observable bug, why
   the tests missed it, and what holds it now (an existing test, a new case,
   an issue, unproven, or a skip reason). If no gaps were found, open no pull
   request and end with the table as your final message; in an unattended run
   that message, kept in the job's log, is the only record, and that is
   enough.

9. **Record where you stopped.** An entry counts as reviewed once its hash
   appears in the report, "unclear" and "skipped" included. On a machine that
   keeps its files between runs (a person's own, not a fresh cloud job),
   create or update the state file with the last entry of the unbroken run of
   reviewed entries from the start of the range: the tip you started from when
   you finished, an earlier entry when the cap stopped you. Never record a
   commit past an entry with no row.

## Running on a schedule

An unattended run has no one to ask. Make every call yourself and write each
one into the pull request. Open the pull request as a draft and drive its
checks green, then mark it ready for review. When a check fails, first find
out whether it fails on the default branch too. If it does, say in the pull
request that it was already failing, leave it a draft, and stop; do not widen
the change to fix it. A failure you caused and could not fix is reported in
the pull request, never left silent. A fresh cloud job starts with no state
file, so it relies on the date window; schedule it daily and ask for the
slightly longer window described above.
