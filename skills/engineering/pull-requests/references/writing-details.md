# Pull request writing details

Detailed evidence rules and splitting recipes for [pull-requests](../SKILL.md).

## Evidence by kind of change

Match the evidence in *How we checked it* to the claim you are making. If you
could not write a test, say so and explain why.

- **A behaviour change**: name the test that fails without the change.
- **A bug fix**: include the smallest steps to reproduce the bug, the regression
  test, and the commit that introduced the defect.
- **A quantified performance claim**: report the workload, baseline, new result,
  machine, and number of runs. Use a table rather than prose. Always pair a
  number with the workload that produced it; if you did not measure a number
  yourself, state whose measurement it is.
- **A mechanism-only performance claim**: name the specific cost you removed
  (such as one fewer allocation per item, one fewer lock acquisition, or one
  fewer encode) and state plainly that you did not measure end-to-end impact.
  This is weaker than a benchmark, but it is honest and concrete.
- **A pure performance change**: state which observable contract stays the same
  and how you checked it. For a batch API, check byte-identical output across
  all fixtures. For anything that streams, buffers, or schedules, also check
  progress, ordering, and resource bounds.
- **A concurrency or resource change** (in addition to the above): state what
  each bound protects and which other entry paths could bypass it; state what
  releases the resource on cancellation; and state which exact state transition
  the regression test controls, plus whether the test could still pass if the
  intended operation never ran.
- **A user-visible change**: include a screenshot or recording (both before and
  after if the interface already existed).
- **A large mechanical change**: state which behaviour is preserved and how your
  checks cover it. For a generated rewrite, include a review of the
  specification and representative output, along with
  [consumer validation](../../coding/references/testing.md#rules). Isolate
  semantic choices—such as parser precedence or platform support—for explicit
  review, because existing tests prove only the paths they cover.
- **A native or platform lifecycle fix with no automated harness**: label the
  check as manual, and record what you actually ran, on which platform, and at
  which revision.

## Sizing and splitting recipes

- **One reason per pull request**: split refactors from behaviour changes so
  each can be reviewed, reverted, and bisected alone. Keep two pieces in one
  pull request only if either one alone would make things worse. When you do,
  put them in separate commits and state in the description that the first
  commit must not ship on its own.
- **Pin the current behaviour before changing it, in separate commits**: if a
  test can already reproduce the behaviour or failure, land that test first and
  refactor under it. If not, first extract the logic so a test can reach it
  ("no functional change"), then add tests whose recorded output captures the
  current behaviour—*including the parts that are wrong*. Change the behaviour
  last so the final diff shows only what actually changed.
- **Land structural work ahead of the feature that needs it**: a refactor landed
  on its own can be reviewed on its structure and reverted cheaply. Bundling it
  with the feature loses both advantages.
- **Land a large feature as inert infrastructure first**: add the types, wiring,
  and gate while it does nothing and cannot affect existing behaviour, with CI
  running on both sides of the gate from day one. Then ship one increment per
  pull request.
- **Put mechanical changes in their own labelled commit**: reviewers can check
  the edges and skip the repetitive body.
- **Keep evidence separate when two optimisations ship together**: if one later
  regresses, you can revert the hunk that caused it without guessing.
- **Judge size after subtracting noise**: line and file counts only tell you
  where to look. Subtract moved code, generated files, lockfiles, and formatting
  before judging how big a diff is—forty changed files with two real lines of
  code is just a dependency bump. Let the dependency structure between steps set
  the commit count (often around three, though there is no fixed quota), and
  make sure every step that can land on its own holds its stated invariants.
