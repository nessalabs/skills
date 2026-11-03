---
id: "skill-verification"
title: "Check the atlas and the executable helper"
kind: "guide"
status: "reference"
summary: "This atlas distinguishes written agent procedures from executable code. Most skills are guides, so a diagram of their prescribed steps is not evidence that an agent actually followed them."
parent: "skills"
sources:
  [
    "skills/engineering/trace/scripts/expand.py",
    ".claude-plugin/plugin.json",
    "package.json",
  ]
sourceRevision: "1ae753c25b29967c0a8672c275d3d1d40f0de865"
diagramLinks: {}
---

# Check the atlas and the executable helper

This atlas distinguishes written agent procedures from executable code. Most skills are guides, so a diagram of their prescribed steps is not evidence that an agent actually followed them.

The trace helper has a selected bounded traversal model and direct Python behavior checks. All nine manifest skill paths are mapped in [the inventory](ownership.md), including the two Nessa product skills. Immutable metadata and human/agent procedures have no invented runtime model. External installers, agent hosts, Nessa services and parser internals remain explicit boundaries.

## Reproduce the checks

From this repository, with a built Nessa Docs checkout and installed canonical checker cache:

```sh
NESSA_DOCS_ROOT=/absolute/nessa-docs node scripts/state-docs/verify.mjs --write
python3 verification/state-models/check_trace.py
```

The first command validates all pages, checks the original model and runs persisted negative controls in memory. Only original model receipts may be written into the page. It does not install a checker. The second command runs production traversal code against a temporary Python fixture using an installed ast-grep executable. Set `AST_GREP_BIN` when it is not on PATH. A missing parser is a failure, not a successful empty trace.

## Recorded results

The canonical catalog accepted 12 pages with no issues. One traversal model passed both invariants; both guard-removal controls broke their expected rule without unchecked results. [Exact model results](../../verification/state-models/results.json) retain source/checker/digest evidence. [Control definitions](../../verification/state-models/controls.json) are reproducible and do not modify the authored model.

Six [direct Python checks](../../verification/state-models/check_trace.py) passed using real ast-grep 0.51.1 on temporary Python fixtures. They exercise positive and nonpositive depth, depth-first traversal, cycle/shared-definition suppression, duplicate call text, missing definitions and multiple same-name methods in the selected candidate file. [Execution log](../../verification/state-models/trace-tests.log) records the run. These checks execute the shipped helper, but cover neither all supported languages nor parser internals.

Chrome opened all 12 pages and rendered all seven diagrams without errors; [browser results](../../verification/state-models/browser.json) record the check. Independent docs-only and source/model review found an overstatement about first-candidate selection: the chosen candidate selects a file, after which all bare-name definitions in that file can be inspected. That wording and the positive-depth explanation were corrected, and a real-parser regression probe demonstrates the distinction. [Review record](../../verification/state-models/review.md) records the final decision.

These checks do not validate whether the nine prose skills make good decisions on arbitrary projects. The broader reader-quality skill pilot is separate evidence, and any unmerged skill changes are not silently treated as this atlas's source revision.
