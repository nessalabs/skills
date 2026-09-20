---
name: pull-requests
description: "Write a pull request description, and review one. Owns the Motivation/Solution frame, before-and-after sections with mermaid diagrams, what evidence each kind of change needs, commit message conventions, how to size and split a change, and the review standard - what to look for in what order, how to treat a claim, what blocks and what does not, how to mark optional feedback, how to disagree, and how to receive review. Use when opening, describing, splitting, or reviewing a pull request, when writing a commit message, or when asked to explain a change to other people."
---

# Pull requests

A pull request is not a delivery mechanism for a diff. It is the artefact
future readers use to understand *why* the code looks like this, long after
everyone involved has forgotten. Write it for them.

Two jobs: [writing one](#writing-the-description) and
[reviewing one](#reviewing). This file owns both; [`coding`](../coding/SKILL.md)
and [`system-architect`](../system-architect/SKILL.md) point here.

---

## Writing the description

### The frame

Two headings, always, in this order. Everything else is optional.

```markdown
## Motivation

What problem this solves, and for whom. Link the report, the prior attempts,
and the workarounds that were rejected. If there is no problem (a refactor, a
cleanup), say what makes it worth doing now.

## Solution

What you did, as a numbered list of steps, each naming the commit that performs
it. Then anything the reviewer needs in order to follow the code.
```

**Motivation is the part people skip and the part that matters.** A reviewer
who does not understand the problem can only check that the code compiles and
matches the description, which is the least valuable thing they could do.

**Link the history.** Every prior issue, every workaround that was shipped and
found wanting, every earlier attempt. It tells the reviewer whether the obvious
cheaper fix has already been tried.

**Map the steps to commits.** A reviewer can then take one idea at a time.
Five minutes of authoring for a qualitatively better review.

### Say what you deliberately did not do

The most under-used section. State the restructuring you considered and
rejected, and why: *I chose not to move this logic into the queue, because it
depends on state the queue does not own; instead the queue exposes two
operations and the caller stays a small diff.* Without it, the next person
tidies the code into the exact shape you already rejected, and nobody
remembers why it was wrong.

### Before and after

For anything that changes a shape (a structure, a state machine, a control
flow, an ownership relationship), show it. Two sections, stacked, never side
by side:

```markdown
### Before

<prose: what the old shape was, and the specific way it was wrong>

<diagram>

### After

<prose: what the new shape is>

<diagram>
```

**Prose first, diagram second.** The diagram illustrates a claim; it does not
make one. The *Before* prose is where you name the defect precisely: "null was
doing double duty as *never looked up* and *looked up, nothing found*, and
under retry those two need opposite behaviour." Diagram conventions and syntax:
[references/diagrams.md](references/diagrams.md).

### Evidence

Match the evidence to the claim. The claim is what the description says; the
evidence is what would make a stranger believe it.

- **A behaviour change**: the test that fails without it, by name.
- **A bug fix**: the minimal reproduction and the regression test, and the
  commit that introduced the defect.
- **A quantified performance claim**: scenario, baseline, result, machine, and
  repetitions. A table beats a sentence. A number without its workload is a
  rumour; a number you did not measure is reported as someone else's.
- **A mechanism-only performance claim**: name the cost that disappeared (one
  fewer allocation per item, one fewer lock acquisition, one fewer encode) and
  say plainly that end-to-end impact was not measured. This is weaker than a
  benchmark and stronger than "obviously faster"; it is the honest form.
- **A pure performance change**: which observable contract is unchanged, and
  how you checked. Byte-identical output on all fixtures for a batch API; for
  anything that streams, buffers, or schedules, also progress, ordering, and
  resource bounds.
- **A concurrency or resource change**, in addition: what each bound protects
  and which other entry path could bypass it; what releases the resource on
  cancellation; which exact transition the regression test controls, and
  whether the test could pass if the intended operation never happened.
- **A user-visible change**: a screenshot or recording. Two, if there was a
  before.
- **A large mechanical change**: what makes it safe. *"If there are unexpected
  divergences, the existing tests catch them"* is a legitimate argument, and
  the only one available at that size.
- **A native or platform lifecycle fix** with no automated harness: what you
  actually ran, on which platform, at which revision, labelled as manual.

If you could not write a test, say so and say why. That is a normal thing to
report and an abnormal thing to hide.

### Honesty markers

- **What you are unsure about.** Name the part you want a second opinion on.
- **What this does not fix.** Adjacent problems the reviewer will spot.
- **What you tried that did not work**, especially when it was the obvious
  approach. It stops the reviewer suggesting it.
- **What you did not run.** Every check is run, not run, blocked, or
  inconclusive; say which.
- **Dependencies**, at the top, not buried.
- **Follow-ups**: what is deliberately left for later, and whether it is filed.

### Size and shape

- **One reason per pull request.** A refactor and a behaviour change do not
  travel together; split them so each can be reviewed, reverted, and bisected
  alone.
- **Aim under a couple of hundred changed lines** where you can. Review quality
  collapses past that; the reviewer skims without admitting it.
- **Refactor, then test, then change, as separate commits.** Extract the logic
  so it is reachable from a test ("no functional change"). Add tests whose
  recorded output captures current behaviour, *including the parts that are
  wrong*. Then change the behaviour, so the last diff is a precise list of what
  changed.
- **Land structural work ahead of the feature that needs it, alone.** A
  refactor motivated by a capability that does not exist yet is reviewable on
  its structure and revertible for free. Bundled with the feature it is
  neither.
- **Land a large feature as inert infrastructure first**: types, wiring, and
  the gate, doing nothing and unable to affect existing behaviour, with CI on
  both sides of the gate from that day. Then one increment per pull request.
- **Mechanical changes go in their own commit, labelled**, so the reviewer can
  check the edges and skip the body.
- **When two optimisations ride together, keep their evidence separate**, so a
  later regression can be reverted by the hunk that caused it.
- **Counts start an investigation; they do not end one.** Subtract moves,
  generated files, lockfiles, and formatting before judging a diff's size:
  forty files and two semantic lines is a dependency bump wearing a costume.
  Three commits is the usual shape, not a quota. Take the number from the
  dependency structure, and make every step that lands on its own hold its
  stated invariants.

### Before large or irreversible work

Write the note *first*: a page with the problem, the proposed change, the
alternatives, and the consequences accepted, circulated before implementation.
Discovering the design is wrong there costs an hour; in review, a week; after
merge, a quarter. The format for the durable version is in
[decision records](../system-architect/references/adr.md).

### Commit messages

- First line: imperative, lowercase, prefixed with the module, under about
  fifty characters, no trailing period: `parser: reject malformed status lines`.
- Blank second line.
- Body wrapped at 72, explaining **why**, referencing the issue it closes.
- **A regression fix names the commit that introduced the defect**, by hash
  and subject. One `git blame`, and the history becomes queryable: what did
  this break, how long did it take to notice, which areas keep regressing.

The message answers the question a future reader actually has, which is never
"what changed" (the diff says that) but "why was this acceptable".

### Update what the change invalidates

Prose, diagrams, the architecture map, the docs, in the same change. **Grep for
the term**, because the sentence you invalidated is rarely in the file you
edited. A stale map is worse than no map, because people trust it.

---

## Reviewing

### The standard

Approve when the change **definitely improves the overall health of the
system**, even if it is not perfect. Perfection is not the bar, and withholding
approval in pursuit of it costs more than the imperfection. Follow-ups can
continue the work.

Two goals, held together: **the codebase improves, and the person submitting
succeeds.** Even where a change does not land, the author should come away
feeling their effort was neither wasted nor unappreciated.

### What blocks

Review is evidence-oriented, not stylistic. A change is blocked by:

- a demonstrated violation of a contract or an invariant, with the path that
  reaches it;
- a validation the project explicitly requires that was not run;
- a claim in the description that the evidence does not support.

A check that was not run is an evidence gap, recorded as one. It is not a
proven bug, and it is not promoted to one. Preference for another layout,
another folder, or another name is a comment, not a blocker. An architectural
direction you would like to see is recorded as a non-blocking note for later,
and said to be one.

**Approval is not execution evidence.** A reviewer can approve a design they
did not run. Record what was tested, benchmarked, and checked on which
platform separately from who approved.

### Order of attention

1. Does this solve the right problem?
2. Is the design right: do dependencies point inward, does the logic sit in the
   layer that owns it, is a boundary being crossed?
3. Is it correct?
4. Is it tested, and would the test have failed before?
5. Is it readable by someone who was not in the conversation?
6. Are the names the product's names?
7. Is it tidy?

**Never lead with 7.** Machines do 7 anyway.

### What to actually look for

Ask these of every change that touches state, and walk the answers rather than
accepting them:

- **What must stay true if this stops halfway? What if it runs twice? What if
  two run at once?**
- Does this point a dependency the wrong way, or reach past a boundary?
- Does it put a rule in a layer that does not own it?
- **Did a refactor quietly narrow a lock, a scope, or a guard?** The classic
  thing a diff does not make obvious: *"this returns the pinned items but no
  longer holds the list lock, where before we held it for the whole loop."*
- Is there state that exists only to serve a speculative accessor? Delete the
  state, the accessor, and the code that maintained it.
- Is an obligation repeated at every call site instead of encapsulated once?
  *"This is added in many places; there is probably a less error-prone way."*
- Do two things now have to be kept in sync by hand?
- Is a name now wrong? The change was correct; the name no longer describes it.
- Does it widen a shared type for one caller, or fatten one variant for a rare
  case? *"Make it a flag, or we will have a fourth variant next month."*
- Does a consumer assume a bound the producer never promised?
- Does a new engine or fast path accept an option it does not implement?
  Silent partial support is a bug even when the common case looks right.
- For anything that caches, buffers, or holds a shared slot: **cycles,
  adversarial size, re-entrancy.**
- For anything that calls out while holding a lock or mid-transition: what can
  the callee reach, and what happens if it panics, re-enters, or blocks?
- Is a synchronisation primitive being added where a design change would remove
  the need for one?
- Does the safety comment justify, or merely restate which operations are
  called?
- Does this accidentally document an internal as a promise?
- Does the build see this change the way you do? A file outside the watched
  tree, an import that breaks tree shaking.
- Is the claim in the description true?

**On a large diff**, classify the lines first: semantic code, tests,
documentation, moves, generated output, dependencies, formatting. Then review
the new ownership, state transitions, admission rules, wake behaviour, and
public contracts before anything else. A large test addition is not the same
risk as a small changed wake condition.

**Reason forward to the unbuilt feature** when a change is preparing for one:
*"will this still be correct once the object can be swapped out mid-loop?"*

**Widen the threat model after the first fix.** When one bypass of an invariant
has been closed, ask what the second one looks like before approving; the
author usually finds it once asked.

### The claim is a hypothesis

The highest-value review comment there is, in every codebase worth imitating,
is some form of **"I do not think that is actually fixed"**, followed by the
reviewer walking the failure path themselves and finding it still open.

An author's statement that a case is handled is a hypothesis. So is a bot's
finding, a static analyser's warning, an LLM's audit, and a bisection that
shows toggling one call changes the symptom (correlation, not root cause).
Take the claim and construct the interruption, the repetition, or the re-entry
that breaks it. When the author says "you're right, it wasn't fixed", that
exchange was the entire value of the review.

### Conventions

- **`Nit:` prefixes anything the author may ignore.** Everything without the
  prefix is expected to be addressed or argued with. This one convention
  removes most of the friction from review, because it removes the guessing.
  Better still: fix the nits yourself while landing.
- **Facts, then principles, then the author's preference.** Technical facts
  win. Where a written principle applies, cite it. Where neither applies, it is
  the author's call; *"I would have done it differently"* is not a review
  comment.
- **Explain the principle, not just the correction**, so the same comment is
  not needed next time.
- **Request changes; do not demand them.** Do not assume the author knows how
  to add a test or run a benchmark; offer.
- **Review a bit at a time.** Focus on what matters most; the rest can follow.
- **Two rounds without convergence means talk, not type.**
- **If you think it should not land, say why.** "No" without an explanation
  does not block anything and is not a review.
- **Push the fix upstream where the defect actually is.** *"Did you open a pull
  request against the dependency?"* is a fair question. Working around someone
  else's bug is a permanent local cost to avoid a one-time external one.

### Receiving review

- A stated concern deserves either a change or an argument, not silence.
- When you disagree, say what you believe and why, and be willing to be wrong.
- When the reviewer is right and you claimed otherwise, say so plainly and move
  on. No ceremony, no over-correction.

### Self-review first

Everything above applies to your own diff before anyone else sees it. Read it
as a stranger, in the web view rather than the editor, and answer the questions
in [What to actually look for](#what-to-actually-look-for) yourself. Most
review comments are things the author would have caught by reading their own
change once, deliberately.

---

## Related

- [`coding`](../coding/SKILL.md): the working method that produces the change.
- [`system-architect`](../system-architect/SKILL.md): what "is the design
  right" means, and [velocity diagnostics](../system-architect/references/velocity.md)
  for whether your change sizes are actually improving.
- [`method`](../method/SKILL.md): how to verify a claim before you make it, or
  before you accept one.
