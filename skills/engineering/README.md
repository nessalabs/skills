# Engineering

How to design a system, how to write a change, and how to find and prove
things.

All of these are **model-invoked**: the agent reaches for them when a task
fits, and you can also invoke them by name.

- **[coding](./coding/SKILL.md)**: the working method for any code change. The
  problem-solving loop (restate, locate, hypothesise, refute, smallest change,
  prove, describe, hold), what to settle before writing, how to write,
  failure-first design, performance method, and how to report what you did.
  Reach for it whenever you are about to write or modify code.
  - References: [Rust](./coding/references/rust.md) and
    [React & TypeScript](./coding/references/react-typescript.md), each opening
    with how to think in that language before the specifics;
    [testing](./coding/references/testing.md), which owns every rule about
    what to test and how.
- **[system-architect](./system-architect/SKILL.md)**: how to structure a
  codebase so the next change stays cheap. Information ownership, boundaries,
  mechanism from policy, a small core with capability composed on top,
  invariants and authority-shaped state first. Reach for it before adding a
  module or a dependency between two parts of a system, or when a change
  starts touching more files than it should.
  - References: [structure](./system-architect/references/structure.md),
    [patterns](./system-architect/references/patterns.md),
    [velocity](./system-architect/references/velocity.md),
    [decision records](./system-architect/references/adr.md).
- **[pull-requests](./pull-requests/SKILL.md)**: how to describe a change and
  how to review one. The Motivation/Solution frame, what evidence each kind of
  claim needs, commit conventions, sizing and splitting, and the review
  standard including what blocks and what does not. Reach for it when opening,
  splitting, or reviewing a pull request, or writing a commit message.
  - References: [diagrams](./pull-requests/references/diagrams.md).
- **[method](./method/SKILL.md)**: how defects get found, how a hypothesis gets
  verified, what counts as evidence, and which artefact holds a fix in place.
  Reach for it when investigating a bug, chasing a performance problem, or
  deciding what to automate or run in CI.
- **[trace](./trace/SKILL.md)**: reconstruct the real runtime call path of a
  feature from source. Reach for it when someone asks how something flows or
  invokes `/trace`.
  - References: [format](./trace/references/format.md).
- **[wdym](./wdym/SKILL.md)**: say it in plain human language first. Reach for
  it when explaining a design, a change, a diagnosis, or a result, and
  whenever `/wdym` is invoked.

## How the set is organised

**One owner per lesson.** Each rule lives in exactly one file; other files
point at it with a sentence and a link rather than a second copy. When two
files disagree, the owner is right and the other is a bug. The owners:

| Lesson | Owner |
| --- | --- |
| The problem-solving loop; failure-first checklist; performance method; reporting | `coding` |
| What to test, how, and what not to; test seams; model-test conditions | `coding/references/testing.md` |
| Language-specific thinking and practice | `coding/references/<language>.md` |
| Design decisions, boundaries, core, invariants, authority-shaped state | `system-architect` |
| Layout, absences, process boundaries, architecture map | `system-architect/references/structure.md` |
| Concrete techniques: seams, gating, accelerators, concurrency protocols | `system-architect/references/patterns.md` |
| Description format, evidence per claim, commit shaping, review standard, what blocks | `pull-requests` |
| Finding instruments, verification, evidence classes, holding a fix in place, CI cadence | `method` |

**The general idea, not the case.** A rule is written as the transferable
principle. The project it came from, its pull request numbers, its line
counts, and its measured percentages stay in the pull request that added the
rule, where a reviewer can check them; they do not go into the skill, which is
read in full every time it loads.

**Meta before specifics.** Each skill and each language reference opens with
how to think, then gives the rules. An agent that has the way of thinking can
rederive most of the rules; one that has only the rules cannot handle the case
the rules did not anticipate.

## Adding a skill here

A skill earns a place by being a *procedure someone follows*, not a topic
someone reads. If the content is reference material for an existing skill, it
belongs in that skill's `references/` folder instead; references load only
when the skill needs them, which keeps the skill short enough to be read.

Every skill directory carries:

```
<name>/
  SKILL.md              name + description frontmatter, then the procedure
  agents/openai.yaml    display_name and short_description, for Codex
  references/           optional; loaded on demand by SKILL.md
```

The `description` is what makes the agent reach for the skill, so it states
what the skill covers *and* when to use it. Add the path to `skills` in
[`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json).

## Adding a lesson

1. Find the owner in the table above and put it there, in the surrounding
   voice, at the same length as its neighbours. A rule that takes a paragraph
   reads as more important than the ones around it, and it rarely is.
2. If an existing rule is too absolute, amend that rule; do not append an
   exception beside it and leave the absolute version authoritative.
3. State the applicability and the exception in the rule itself, so it reads
   as a probe rather than a ban.
4. Where another file would benefit from knowing, add one sentence and a
   link, never a restatement.
5. Put the source, the cost it was learned at, and the measurements in the
   pull request description.
