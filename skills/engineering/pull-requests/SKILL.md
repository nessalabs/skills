---
name: pull-requests
description: "Write a pull request description, and review one. Owns the description template (Background, The problem, The solution, How we checked it, Tradeoffs and follow-ups, Rollout) with before-and-after mermaid diagrams, what evidence each kind of change needs, commit message conventions, how to size and split a change, and the review standard - what to look for in what order, how to treat a claim, what blocks and what does not, how to mark optional feedback, how to disagree, and how to receive review. Use when opening, describing, splitting, or reviewing a pull request, when writing a commit message, or when asked to explain a change to other people."
---

# Pull requests

A pull request is the record future readers use to understand *why* the code
looks the way it does, long after everyone involved has forgotten. Write it for
them.

Two jobs: [writing the description](#writing-the-description) and
[reviewing](#reviewing). This file owns both; [`coding`](../coding/SKILL.md)
and [`system-architect`](../system-architect/SKILL.md) point here.

---

## Writing the description

### The frame

Write for a reader who has never seen this code and has five minutes. Use plain
words ([wdym](../wdym/SKILL.md)); reach for a technical term only when nothing
simpler says it. Copy the template from
[references/pull_request_template.md](references/pull_request_template.md) to
`.github/pull_request_template.md`. Any tool-added block (such as an attribution
line) goes above the template, never inside a section.

1. **Before / After**: one sentence each from the user's point of view, then
   `Closes #N` (or `Part of #N` if the issue stays open).
2. **Background**: only the parts involved and what each does, with a small
   diagram if it helps.
3. **The problem**: what goes wrong, told first as what the user sees ("you
   press Send twice and the message appears twice"), then the flow with the
   break marked. Link prior issues, workarounds, and earlier attempts. For a
   refactor or cleanup, explain why it is worth doing now.
4. **The solution**: the same flow redrawn, then the steps in plain words, each
   naming the commit that does it (avoid a file-by-file list).
5. **How we checked it**: plain bullets on what was asked and how you verified
   it. See [Evidence](#evidence).
6. **Tradeoffs and follow-ups**: what the change gives up and leaves for later.
   See [Say what you deliberately did not do](#say-what-you-deliberately-did-not-do).
7. **Rollout**: breaking changes, migrations, settings, and how to undo it
   ("Nothing special" is fine).

Write from the issue and the diff rather than your notes: user-visible symptoms
first, only the function names a reviewer needs to check, and review history in
one line. Read the draft as a stranger before posting. When a change alters a
structure, state machine, control flow, or ownership relationship, stack a
before diagram (*The problem*) above an after diagram (*The solution*) over the
same participants, after stating the defect in prose. Diagram rules:
[references/diagrams.md](references/diagrams.md).

### Say what you deliberately did not do

In *Tradeoffs and follow-ups*, state the alternative or restructuring you
considered and rejected, and why (*I left this logic out of the queue because it
depends on state the queue does not own; instead the queue exposes two
operations and the caller stays small*). Otherwise the next person may refactor
into the shape you ruled out. Name any cost you accepted too: extra memory, a
slower path, harder future extensions, or a size limit.

### Evidence

Match the evidence to the claim: put plain bullets in *How we checked it*
describing what you did, and name a test where that test is the proof. If you
could not write a test, say so and explain why. For the exact proof required per
kind of change (behaviour, bug fix, quantified or mechanism-only performance,
pure performance, concurrency/bounds/cancellation, UI, mechanical rewrite, and
manual native fixes), see
[references/writing-details.md](references/writing-details.md#evidence-by-kind-of-change).

Include honesty markers in *How we checked it* and *Tradeoffs and follow-ups*:
what you are unsure about; adjacent issues left unfixed; obvious approaches you
tried that failed; every check marked run, not run, blocked, or inconclusive;
dependencies (at the top); and follow-ups (and whether they are filed).

### Size and shape

- **One reason per pull request.** Split refactors from behaviour changes so
  each can be reviewed, reverted, and bisected alone. Bundle two pieces only if
  either one alone would make things worse; then separate them into commits and
  note that the first commit must not ship on its own.
- **Aim under a couple of hundred semantic lines** where you can, after
  subtracting moves, generated files, lockfiles, and formatting.
- **Pin behaviour before changing it, and land structure or inert wiring ahead
  of features.** Put mechanical edits in their own labelled commit, and keep
  evidence separate when two optimisations ship together. Splitting recipes,
  dual-side CI gates, and diff-size rules:
  [references/writing-details.md](references/writing-details.md#sizing-and-splitting-recipes).
- **Before large or irreversible work**, circulate a one-page design note first
  (problem, proposal, alternatives, accepted consequences). Durable format:
  [decision records](../system-architect/references/adr.md).

### Commit messages

- First line: imperative, lowercase, prefixed with the module, under ~50 chars,
  no trailing period (`parser: reject malformed status lines`).
- Blank second line, then body wrapped at 72 chars explaining **why** this
  change is acceptable and referencing the issue it closes. Regression fixes
  name the introducing commit by hash and subject.
- **Update what the change invalidates** in the same change (prose, diagrams,
  architecture map, docs); grep for the changed term across the repo.

---

## Reviewing

### The standard

Approve when the change **clearly improves the overall health of the system**,
even if it is imperfect; follow-ups can handle the rest. Hold two goals
together: the codebase improves, and the author succeeds—even when a change does
not land, their effort should feel respected.

**What blocks:** a demonstrated violation of a contract or invariant with the
path that reaches it; a required project validation that was not run; or a claim
in the description unsupported by evidence. Record an unrun check as an evidence
gap rather than a proven bug. Style, layout, or naming preferences and future
architectural wishes are non-blocking comments.

**Approval is separate from execution evidence.** Record what was tested,
benchmarked, and checked on which platform separately from who approved.

**Order of attention:** (1) solves the right problem, (2) sound design
(dependencies point inward, logic in the owning layer, clean boundaries),
(3) correctness, (4) evidence fits
[the kind of change](../coding/references/testing.md#what-gets-a-test),
(5) readable outside the conversation, (6) names match the product, (7) tidiness.
Never lead with tidiness.

### What to actually look for

For every change that touches state, ask these questions and walk the code to
verify the answers:

- **Halfway, twice, concurrent:** what must stay true if this stops halfway
  through, runs twice, or runs in two places at once?
- **Ownership and boundaries:** do dependencies point the right way, does every
  rule sit in the layer that owns it, and did a refactor drop a lock, guard, or
  surrounding step?
- **Evidence matches claim:** is the description's claim true, and does the test
  or check actually prove it?
- **Walk the failure path:** what happens on error, cancellation, panic,
  re-entry, or unexpected input size?

Full 18-point checklist (caching, locks, unused state, bloated types, leaked
internals, build visibility, large-diff triage, forward-reasoning, and widening
the threat model):
[references/review-checklist.md](references/review-checklist.md).

### The claim is a hypothesis

Treat every claim that a case is handled as a hypothesis—whether from the
author, a bot, a static analyser, an LLM audit, or a bisection showing that
toggling a call changes the symptom (correlation rather than root cause). Walk
the failure path yourself and try to build the interruption, repetition, or
re-entry that still breaks it. Showing *"I do not think this is actually fixed"*
with a concrete open path is the highest-value feedback a review can give.

### Conventions and receiving review

- **Prefix optional feedback with `Nit:`** so the author knows they may ignore
  it (or fix nits yourself while landing). Everything unprefixed expects a fix
  or a reply.
- **Facts first, then written principles, then the author's call.** Explain the
  principle behind a comment so it transfers to future changes.
- **Request changes rather than demanding them**, and offer to help if the
  author may not know how to add a test or benchmark. Review the most important
  parts first. If two rounds of comments do not converge, switch to a live
  conversation. If a change should not land, explain why. Check whether a fix
  belongs upstream using
  [patterns](../system-architect/references/patterns.md#concurrency-and-failure).
- **Receiving review:** answer every concern with a change or an explanation.
  When you disagree, explain why while staying open to being wrong; when the
  reviewer is right, say so plainly and move on.
- **Self-review first:** read your own diff in the web view as a stranger and
  answer [What to actually look for](#what-to-actually-look-for) before asking
  anyone else.

---

## Related

- [`coding`](../coding/SKILL.md): the working method that produces the change.
- [`system-architect`](../system-architect/SKILL.md): what "sound design" means,
  and [velocity diagnostics](../system-architect/references/velocity.md) for
  whether your change sizes are improving.
- [`method`](../method/SKILL.md): how to verify a claim before you make it or
  accept one.
