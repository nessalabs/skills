# Working on this repo

This repo holds engineering skills that agents load and read in full. Every
sentence costs attention each time a skill loads, so changes here follow a few
rules. The detailed process for adding a lesson, and the table of which file
owns which kind of lesson, is in
[skills/engineering/README.md](skills/engineering/README.md). Read it before
editing a skill.

## How to think about a change

**Teach how to think, not project rules.** A skill should help an agent solve
a problem it has never seen. Write the general idea, then the rule. Each skill
and each language reference opens with "how to think" before the specifics.

**Look for the core rule first.** Most new lessons are another example of a
rule we already have. The main one so far is
[every fact has one authority](skills/engineering/system-architect/SKILL.md#the-core-rule-every-fact-has-one-authority):
one place makes, decides, checks, and ends each fact, and nothing else guesses
or keeps its own copy. When a study or a bug teaches something, ask which core
rule it is an example of. If one fits, add a row to that rule's examples table
and put the detail with the owning rule. Add a new principle only when nothing
fits. If several lessons keep pointing at a rule we have not named yet, name
it as a new core rule with its own examples.

**One owner per lesson.** Each rule lives in exactly one file. Other files link
to it in one sentence. Do not copy a rule into a second place.

**Fix a rule that is too absolute.** Change the existing sentence; do not add
an exception next to it.

## How to write

**Use plain words.** Say it the way you would explain it to a colleague out
loud. Lead with a simple sentence, then add a small concrete example where the
idea is hard to picture ("a file header written inside the loop looks fine
with one batch and breaks with two"). Swap a hard word for a simpler one
rather than defining it. The [wdym](skills/engineering/wdym/SKILL.md) skill is
the guide.

**Simple must stay exact.** When you simplify a rule, check that you did not
drop a condition. "A read by id can skip the queue" is wrong if the original
said "a read of an item that can never change". Reread the precise version
next to the plain one before committing.

**Keep case detail out of the skills.** Project names, PR numbers, line
counts, and percentages go in the pull request description and commit
messages, where a reviewer can check them. The skill text keeps only the
general lesson and, where it helps, a generic example.

## Folding in research studies

Studies arrive as long reports with their own proposed edits. Do not apply
them literally.

1. Read the current skills first, so you know what is already covered.
2. For each proposal, decide: new, amends an existing rule, already covered,
   or too specific to transfer. Merge proposals from different studies that
   teach the same lesson.
3. Map each lesson to a core rule (above), then to its owning file.
4. Reject review-question lists that only restate rules owned elsewhere.
5. Put sources and evidence for each lesson in the pull request description.
6. Bump the version in `package.json` and `.claude-plugin/plugin.json` for
   broad changes.

## Testing a skill

When you check a skill by having a subagent follow it against a real
repository, run that subagent on a smaller model (such as Sonnet). A skill
should work on a smaller model, and these runs are expensive on a large one.
