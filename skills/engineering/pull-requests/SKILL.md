---
name: pull-requests
description: "Write a pull request description, and review one. Covers the Motivation/Solution structure, before-and-after sections with mermaid class and flow diagrams, how to map steps to commits, what to say about testing and performance, commit message conventions, splitting a change so it is reviewable, and the review standard - what to look for, in what order, how to mark optional feedback, how to disagree, and how to receive review. Use when opening, describing, splitting, or reviewing a pull request, when writing a commit message, or when asked to explain a change to other people."
---

# Pull requests

A pull request is not a delivery mechanism for a diff. It is the artefact that
future readers use to understand *why* the code looks like this, long after
everyone involved has forgotten. Write it for them.

Two jobs here: [writing one](#writing-the-description), and
[reviewing one](#reviewing).

---

## Writing the description

### The frame

Two headings, always, in this order. Everything else is optional.

```markdown
## Motivation

What problem this solves, and for whom. Link the report, the prior attempts,
and the workarounds that were rejected. If there is no problem — a refactor, a
cleanup — say what makes it worth doing now.

## Solution

What you did, as a numbered list of steps, each naming the commit that performs
it. Then anything the reviewer needs in order to follow the code.
```

**Motivation is the part people skip and the part that matters.** A reviewer who
does not understand the problem cannot evaluate the solution — they can only
check that the code compiles and matches the description, which is the least
valuable thing they could do. Spend the paragraphs here.

**Link the history.** Every prior issue, every workaround that was shipped and
found wanting, every earlier attempt. This is what tells a reviewer whether the
obvious cheaper fix has already been tried.

**Map the steps to commits.** A numbered solution where each step names its
commit lets a reviewer take one idea at a time. It is five minutes of authoring
for a qualitatively better review.

### Say what you deliberately did not do

The single most under-used section. State the restructuring you considered and
rejected, and why — for example: *I chose not to move this logic into the queue,
because it depends on other state the queue does not own; instead the queue
exposes two operations and the caller stays a small diff.*

Without it, the next person "tidies" the code into the exact shape you already
considered and rejected, and nobody remembers why it was wrong.

### Before and after

For anything that changes a shape — a structure, a state machine, a control
flow, an ownership relationship — show it. Two sections, stacked, never
side-by-side:

```markdown
### Before

<prose: what the old shape was, and the specific way it was wrong>

<diagram>

### After

<prose: what the new shape is>

<diagram>
```

**Prose first, diagram second.** The diagram illustrates a claim; it does not
make one. A diagram with no sentence saying what to notice is decoration.

The *Before* section is where you name the defect precisely. Good examples of
that sentence:

- "Friction was applied once per frame as a flat multiplier, so speed decayed as
  `f^(2n)` at 120 Hz where it should have been `f^n` over the same wall-clock
  time."
- "`null` was doing double duty as *never looked up* and *looked up, nothing
  found*, and under retry those two need opposite behaviour."
- "Every worker incremented a shared counter per work item; the counter was the
  contention."

Diagram conventions and syntax: [references/diagrams.md](references/diagrams.md).

### Evidence

Whatever kind of change this is, show that it works:

- **A behaviour change** — the test that fails without it. Name it.
- **A bug fix** — the minimal reproduction, and the regression test.
- **A performance change** — the scenario, the numbers, the machine. *"10,000
  items, each updated once inside one batch, median of five runs: 1,444 ms → 46
  ms."* A table beats a sentence. A number without its workload is a rumour.
- **A pure performance change** — state that the output is unchanged, and how
  you checked. *"All fixtures produce byte-identical output; also verified
  against real inputs and pathological cases."*
- **A user-visible change** — a screenshot, or a recording. Two, if there was a
  before.
- **A large mechanical change** — say what makes it safe. *"If there are
  unexpected divergences, the existing tests catch them"* is a legitimate
  argument, and the only one available at that size.

If you could not write a test, say so and say why. That is a normal thing to
report and an abnormal thing to hide.

### Honesty markers

These cost nothing and buy trust:

- **What you are unsure about.** Name the part you want a second opinion on.
- **What this does not fix.** Adjacent problems the reviewer will spot and
  wonder about.
- **What you tried that did not work.** Especially when the obvious approach was
  the one that failed — it stops the reviewer suggesting it.
- **Dependencies.** *"This depends on #1234"*, at the top, not buried.
- **Follow-ups.** What is deliberately left for later, and whether it is filed.

### Size and shape

- **One reason per pull request.** A refactor and a behaviour change do not
  travel together — split them so each can be reviewed, reverted, and bisected
  alone.
- **Aim under a couple of hundred changed lines** where you can. Review quality
  collapses past that; the reviewer starts skimming without admitting it.
- **Refactor, then test, then change — as three commits.** Extract the logic so
  it is reachable from a test ("no functional change"). Add tests whose recorded
  output captures current behaviour, *including the parts that are wrong*. Then
  change the behaviour, so the third diff is a precise list of what changed.
- **Land a large feature as inert infrastructure first** — types, wiring, and
  the gate, doing nothing and unable to affect existing behaviour — then one
  increment per pull request.
- **Land structural work ahead of the feature that needs it, alone.** A refactor
  motivated by a capability that does not exist yet is reviewable on its
  structure and revertible for free. Bundled with the feature, it is neither.
- **Mechanical changes go in their own commit, clearly labelled**, so the
  reviewer can check the edges and skip the body.

### Before large or irreversible work

Write the note *first*: a page describing the problem, the proposed change, the
alternatives, and the consequences accepted, circulated before implementation.
It is the cheapest possible place to discover the design is wrong. Discovering
it in review costs a week; after merge, a quarter.

### Commit messages

- First line: imperative, lowercase, prefixed with the module, under ~50
  characters, no trailing period — `parser: reject malformed status lines`.
- Blank second line.
- Body wrapped at 72, explaining **why**, referencing the issue it closes.
- **A regression fix names the commit that introduced the defect**, by hash and
  subject. One `git blame`, and the history becomes queryable: what did this
  break, how long did it take to notice, which areas keep regressing.

The message answers the question a future reader actually has, which is never
"what changed" — the diff says that — but "why was this acceptable".

### Update what the change invalidates

Prose, diagrams, the architecture map, the docs. In the same change. **Grep for
the term**, because the sentence you invalidated is rarely in the file you
edited. A stale map is worse than no map, because people trust it.

---

## Reviewing

### The standard

Approve when the change **definitely improves the overall health of the system**,
even if it is not perfect. Perfection is not the bar, and withholding approval in
pursuit of it costs more than the imperfection. Only incremental improvement is
needed to land; follow-ups can continue the work.

The two goals, held together: **the codebase improves, and the person submitting
succeeds.** Even where a change does not land, the author should come away
feeling their effort was neither wasted nor unappreciated.

### Order of attention

1. Does this solve the right problem?
2. Is the design right — do dependencies point inward, does the logic sit in the
   layer that owns it, is a boundary being crossed?
3. Is it correct?
4. Is it tested, and would the test have failed before?
5. Is it readable by someone who was not in the conversation?
6. Are the names the product's names?
7. Is it tidy?

**Never lead with 7.** Leading with formatting on a change that has a layering
problem wastes the author's revision and yours. Machines do 7 anyway.

### What to actually look for

- Does this point a dependency the wrong way, or reach past a boundary?
- Does it put a rule in a layer that does not own it — a domain decision in the
  application layer, an application concern in the domain?
- **Did a refactor quietly narrow a lock, a scope, or a guard?** This is the
  classic thing a diff does not make obvious. *"This returns the pinned items
  but no longer holds the list lock, where before we held it for the whole
  loop."*
- Is there state here that exists only to serve a speculative accessor? Delete
  the state, the accessor, and the code that maintained it.
- Is an obligation repeated at every call site instead of encapsulated once? *"This
  is added in many places — there is probably a less error-prone way."*
- Do two things now have to be kept in sync by hand?
- Is a name now wrong? The change was correct; the name no longer describes it.
- Does it widen a shared type for one caller, or fatten one variant for a rare
  case?
- For anything new that caches, buffers, or holds a shared slot: **cycles,
  adversarial size, re-entrancy.** *"Does this handle circular references?"
  "What happens under load in the degenerate case?" "Does this need to save and
  restore the previous value if it is re-entered?"*
- Is the claim in the description true?

### The claim is a hypothesis

The highest-value review comment there is, in every codebase worth imitating, is
some form of **"I do not think that is actually fixed"** — followed by the
reviewer walking the failure path themselves and finding it still open.

An author's statement that a case is handled is a hypothesis. So is a bot's
finding, a static analyser's warning, and an LLM's audit. Take the claim, and go
construct the interruption, the repetition, or the re-entry that breaks it. When
you are right, say so plainly; when the author says "you're right, it wasn't
fixed", that exchange was the entire value of the review.

Ask the interrupted, repeated, and re-entered questions of every change that
touches state:

- What must stay true if this stops halfway?
- What if it runs twice?
- What if two run at once?

### Conventions

- **`Nit:` prefixes anything the author may ignore.** Everything without the
  prefix is expected to be addressed or argued with. This one convention removes
  most of the friction from review, because it removes the guessing. Better
  still: fix the nits yourself while landing.
- **Facts, then principles, then the author's preference.** Technical facts win.
  Where a written principle applies, cite it. Where neither applies, it is the
  author's call — *"I would have done it differently"* is not a review comment.
- **Explain the principle, not just the correction.** The goal is that the same
  comment is not needed next time.
- **Request changes; do not demand them.** And do not assume the author knows
  how to add a test or run a benchmark — offer.
- **Review a bit at a time.** Do not overwhelm someone with every possible
  improvement at once. Focus on what matters most; the rest can follow.
- **Two rounds without convergence means talk, not type.**
- **If you think it should not land, say why.** "No" without an explanation does
  not block anything and is not a review.

### Receiving review

- A stated concern deserves either a change or an argument, not silence.
- When you disagree, say what you believe and why, and be willing to be wrong.
- When the reviewer is right and you claimed otherwise, say so plainly and move
  on — no ceremony, no over-correction.
- Push the fix upstream where the defect actually is. *"Did you open a pull
  request against the dependency?"* is a fair question, and working around
  someone else's bug is a permanent local cost to avoid a one-time external one.

### Self-review first

Everything above applies to your own diff before anyone else sees it. Read it as
a stranger, in the web view rather than the editor, and answer the questions in
[What to actually look for](#what-to-actually-look-for) yourself. Most review
comments are things the author would have caught by reading their own change
once, deliberately.

---

## Related

- [`coding`](../coding/SKILL.md) — the working method that produces the change.
- [`system-architect`](../system-architect/SKILL.md) — what "is the design
  right" means, and
  [velocity diagnostics](../system-architect/references/velocity.md) for whether
  your change sizes are actually improving.
- [`method`](../method/SKILL.md) — how to verify a claim before you make it, or
  before you accept one.
