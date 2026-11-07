---
id: "skill-pull-requests"
title: "Explain a change and review its claims"
kind: "guide"
status: "reference"
summary: "A pull request should let a new reader understand the problem, the resulting behavior and the evidence without reconstructing the author's chat. Review then challenges those claims rather than assuming a passing check proves them all."
parent: "skills"
sources:
  [
    "skills/engineering/pull-requests/SKILL.md",
    "skills/engineering/pull-requests/references/diagrams.md",
    "skills/engineering/pull-requests/references/pull_request_template.md",
  ]
sourceRevision: "1ae753c25b29967c0a8672c275d3d1d40f0de865"
diagramLinks: {}
---

# Explain a change and review its claims

A pull request should let a new reader understand the problem, the resulting behavior and the evidence without reconstructing the author's chat. Review then challenges those claims rather than assuming a passing check proves them all.

The [description procedure](../../skills/engineering/pull-requests/SKILL.md#writing-the-description) and [copyable template](../../skills/engineering/pull-requests/references/pull_request_template.md) own the required sections. They start with before/after behavior, give context, explain the problem and solution, then state checks, tradeoffs and rollout. Keep sources and case-specific measurements in the PR rather than teaching them as permanent skill policy.

For example, a concurrency fix should explain what owns cleanup when cancellation races with completion and show the test that exercises that boundary. A screenshot demonstrates what was rendered; it does not prove network behavior. A before/after diagram is useful when the shape or ordering changes, but not required decoration for a renamed value.

The [review procedure](../../skills/engineering/pull-requests/SKILL.md#reviewing) checks scope, design and meaningful evidence before preference. It asks reviewers to construct a failing case for a claimed fix, and to resolve findings with a correction or an evidence-backed explanation. The host and forge own actual publication and permissions. The skill is neither a merge bot nor an automatic review approval.
