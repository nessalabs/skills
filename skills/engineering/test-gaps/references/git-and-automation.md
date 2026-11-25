# Git plumbing, state cursors, and scheduled runs

Detailed git commands, edge cases, cursor rules, and unattended-run handling
for [`SKILL.md`](../SKILL.md).

## Remote and default branch

- `<remote>` is the remote where the shared branch lives — usually `origin`,
  but check `git remote` (a fork may call it `upstream`). With no remote at
  all, use the local default branch and say so in the report.
- Find the default branch name with `git ls-remote --symref <remote> HEAD`
  rather than guessing `main`.
- The end of the range (`<tip>`) is the tip of `<remote>/<default>` when you
  start.

## Fetching history

- Always fetch first; never work from a local branch that may be stale.
- Use an explicit refspec so single-branch clones still update the remote
  tracking branch:

  ```sh
  git fetch <remote> <default>:refs/remotes/<remote>/<default>
  ```

- In a shallow clone, pass `--shallow-since="<date>"` or `--unshallow` so you
  fetch enough history to reach the start of the range.

## Resolving the start commit

- Turn a date into a fixed commit so the range does not depend on commit dates
  being in order:

  ```sh
  git rev-list -1 --first-parent --before="<date>" <remote>/<default>
  ```

- **Root-commit quirk:** if `rev-list` prints nothing, the whole branch is
  newer than the date. List all commits with
  `git log --first-parent --reverse <tip>`, because `<root>..<tip>` would leave
  the root commit out.
- **Ancestry check:** verify `git merge-base --is-ancestor <start> <remote>/<default>`.
  If `<start>` is not an ancestor, it was mistyped or history was rewritten.
  Ask the person if one is present; an unattended run notes this and falls back
  to the 24-hour window.

## Listing entries and diffing changes

- List entries with `git log --first-parent --reverse <start>..<tip>`.
  First-parent produces one entry per merged change for squash and merge
  workflows.
- **Rebased pull requests:** a repository that rebases changes onto the default
  branch has several commits per change. Group them by their pull request (from
  the forge or from commit messages) and treat each group as one entry.
- **Entry diff:** compute each entry's change with `git diff <before> <after>`,
  where `<after>` is the entry's last commit and `<before>` is the commit right
  before it on the branch (`<sha>^1` for a single commit or a merge; the parent
  of the first commit for a rebased group).
- **Merge combined-diff quirk:** `git show` on a merge commit prints a combined
  diff that is often empty. Always use `git diff <before> <after>` instead.

## Putting a bug back safely

- Reverse only the non-test files of the change:

  ```sh
  git diff <before> <after> -- <non-test paths> | git apply -R
  ```

  Never do a full `git revert`, which would remove the fix's own tests too.
- **Inline tests (e.g. Rust `#[cfg(test)]` modules):** strip the test hunks
  from the diff before piping to `git apply -R`, or the fix's own tests will be
  reverted along with the code.
- **Root commit:** has no `<before>` commit; put its bug back by hand (as
  step 5 allows).

## Worktree isolation

- If the range is empty, stop: nothing to do, nothing to commit.
- Otherwise do all work in a clean worktree on a new branch created from
  `<tip>`:

  ```sh
  git worktree add -b <branch> <dir> <tip>
  ```

- Never work in the checkout you were started in, which may hold someone's
  unrelated changes. Follow the repository's own branch naming rules.

## State file and cursor advancement

- **Path:** `${XDG_STATE_HOME:-$HOME/.local/state}/test-gaps/<host>/<owner>/<repo>`,
  where `<host>` is the remote's host (for example `github.com`).
- **Contents:** only the commit hash the previous run reviewed up to. Keeping
  it outside the repository means nothing is committed and each person keeps
  their own cursor.
- **What counts as reviewed:** an entry is reviewed once its hash appears in
  the report, including `unclear` and `skipped` entries.
- **When to update:** only on a machine that keeps files between runs (a
  person's own machine, not a fresh cloud job), and only when the range started
  from the state file itself, or the file did not exist yet, or the file held a
  commit no longer on the branch and the run fell back to the window. Leave the
  file alone when a person chose a custom range, because that range may have
  skipped commits the file has not seen.
- **Which hash to write:** the last entry of the unbroken run of reviewed
  entries from the start of the range — `<tip>` when you finished, or an
  earlier entry when the 20-fix cap stopped you. Never advance past an entry
  with no row in the report.

## Running on a schedule

- An unattended run has no one to ask. Make every call yourself and record each
  decision in the pull request.
- Open the pull request as a draft, drive its checks green, then mark it ready
  for review.
- When a check fails, first find out whether it already fails on the default
  branch. If it does, say in the pull request that it was already failing,
  leave it as a draft, and stop; do not widen the change to fix it.
- Report any failure you caused and could not fix in the pull request; never
  leave it silent.
- A fresh cloud job starts with no state file and relies on the date window.
  Schedule it daily and ask for a window slightly longer than the interval
  (such as "since 26 hours ago" for a daily run) so late starts do not miss
  commits; overlap is harmless because step 5 skips fixes already covered.
