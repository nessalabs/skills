---
name: build-artifacts
description: "Write a document or report a person will read (a decision brief, a design doc, a status report, an idea portfolio) as one self-contained HTML page in Nessa's house style: the plain answer first, every claim marked sourced or judgment, made-up numbers labelled, and the same parts for parallel ideas. The agent writes Markdown with a few directives; scripts/render.py applies the winning theme (project over user over the Nessa default). Use when asked for an artifact, a page, a brief, a write-up, a report or a design doc, or when /build-artifacts is invoked."
---

# Build artifacts

Write the page the way you would brief a smart colleague who was not in the
room and has five minutes. They should get the answer from the first screen,
see which parts you checked and which parts are your opinion, and know what is
still open.

You write content, never HTML. Write a Markdown file with a few directives,
then run `scripts/render.py`. The renderer owns the look; the theme decides
the colors, fonts and voice settings.

## How to think about it

A long page fails in two ways. Either the reader cannot find the answer, or
they cannot tell what is true. Most of the rules below fix one of those.

- **The answer comes first.** A reader decides in the first screen whether to
  keep reading. Put the conclusion there in plain words, then the evidence.
- **Sourced and judgment stay apart.** Nothing loses trust faster than an
  opinion dressed as a fact. Mark every section, and any mixed claim, so the
  reader knows which one it is.
- **Parallel things get parallel shapes.** When ideas share the same parts in
  the same order, the reader compares them instead of decoding each one.
- **Say what you skipped.** What not to build, what you did not read, and what
  is still open are as useful as the recommendation.

## The procedure

1. **Load the voice.** Run `python3 scripts/render.py --voice --project <repo>`.
   It prints the resolved writing rules: the fixed floor, then the register,
   person and word list from the winning theme. Follow
   [wdym](../../engineering/wdym/SKILL.md) for every sentence; it owns those
   rules, and the voice settings only adjust them.
   - `--project <folder>` is where the renderer starts searching upward for
     `.nessa/artifacts/theme.toml`. When the page is not about a repo, leave
     it out (the search then starts from the document's folder, or the
     current folder for `--voice`) or pass `--no-project` to skip the
     project layer.
   - `--no-user` skips the user layer (`~/.nessa/artifacts/theme.toml` or
     `$NESSA_ARTIFACTS_THEME`). Use it when the page is for someone else and
     should not carry your personal theme, or to reproduce the plain Nessa
     default with `--no-user --no-project`.
2. **Pick the kind** and its skeleton below. Set `kind:` in the front matter.
3. **Gather, then label.** For each claim, note where it came from and when you
   read it. Anything you could not check is judgment or a gap, never a fact.
4. **Write the Markdown** in the [format](references/format.md). Start from
   [example.md](references/example.md), which uses every component.
5. **Render.** `python3 scripts/render.py page.md -o page.html --project <repo>`
   (same `--project` and `--no-user` rules as step 1). Fix every warning;
   `--strict` turns warnings into a failure.
6. **Look at it.** Run `scripts/screenshot.sh page.html page.png` and
   `scripts/screenshot.sh page.html page-dark.png dark`, then view both
   images. It measures the page and grows the window until the whole page
   fits, and warns if the page is still cut off. It needs Chrome or
   Chromium; without one, open the page in any browser. If you could not see it at all, say the look was not checked.
7. **Run the self-check** at the end of this file, then share the file.

## Sentence rules

Follow [wdym](../../engineering/wdym/SKILL.md) for every sentence, since it
owns those rules. The voice floor still requires what wdym does not: mark each
claim sourced or judgment, and label a made-up number or example as a
placeholder.

## Page rules

- **Title and summary carry the point.** The title names the question or the
  thing. The summary is exactly two sentences: what this is, and the main
  finding.
- **First section, the plain version.** Two to four plain sentences that
  answer the question, then one `:::lead` with the recommendation, tagged
  `judgment`. No table or diagram before it. The section needs no caption,
  but an invented or chosen number in it still gets an inline label right
  after the number: `about 40 users {placeholder}`.
- **Label at the right level.** When a whole section is one kind, put the label
  first in its `::caption`, with what it came from and when: `{sourced: repo,
  read Nov 26, 2026}`. A bare label caption (`::caption {judgment}`) is fine
  when the label says everything; add one or two sentences when the reader
  needs to know what part is sourced, what was chosen, or why. When a section mixes them, label the claim inline. A `###`
  subsection takes its parent's label. A card or lead with `tag=` counts.
- **Two sections need no label.** The first section (the plain version: its
  `:::lead` carries its own tag, and it only sums up labelled sections below)
  and the closing section that holds `:::sources`. The renderer warns about
  any other `##` section with no label.
- **Invented input is a placeholder, never sourced.** Made-up survey answers,
  sample users, example logs and demo numbers get `{placeholder: invented
  survey}` in the caption, and the caption says they are made up and what a
  real page would cite instead.
- **One date format.** Write every date as `Mon D, YYYY` (`Nov 26, 2026`),
  in labels, quotes, sources and front matter.
- **Quotes name who and when.** Use `:::quote cite="who, where" date="Oct 25,
  2026"`. Who is a name or handle plus the place (`@handle, X reply`,
  `Respondent 14, sample survey`). Dates are `Mon D, YYYY`; add the time and
  zone only when order matters (`Oct 25, 2026, 7:19 PM (UTC-7)`). Quote the
  words exactly; cut with `...`, never reword inside quotes.
- **Sources without a link still get named.** Give the title, where it lives
  (a file path, a channel, a meeting) and the date you read it:
  `- Support log, shared drive support/2026-11.csv, read Nov 27, 2026`.
- **Be honest about gaps and numbers.** "I didn't find it in what I read" is
  not "missing". A number you chose to show the shape of the math is
  `{placeholder}`, and the caption says so. A status table's labels are
  judgment even when its facts are sourced.
- **Rank with reasons.** A ranked list is ordered by what to do first. Each
  item opens with a short bold claim, then the reason in one or two sentences.
- **Repeat the card.** Every idea card uses the same fields in the same order:
  Pitch, Who it's for, Why we win, Smallest first version, Risks. Risks are
  real and specific, not a formality.
- **Use a table only for parallel facts.** Rows that share columns. Use a list
  when the items are not parallel, and prose when there are only two or three.
- **A lifecycle gets a state table, a diagram, and invariants.** The table says
  what each state holds and how it is left. The diagram shows the failure and
  retry paths, not only the happy path. Invariants are "must always hold"
  sentences someone could test.
- **End with skip, open questions, and how the page was made.** Name what to
  avoid building and why. List the risks and questions you could not settle.
  Close with what you read, when, and what you did not read.
- **Skipped parts.** Leave out a part marked optional without comment. When
  you leave out any other part of the skeleton (a status table, a skip list,
  open questions), say why in one sentence in "How this page was made":
  "No status table: nothing is built yet."
- **One name per thing.** Pick a name and use it in prose, tables and diagrams.
- **Keep case detail in the page, not the theme.** Project names, numbers and
  links belong in the document. Nothing project-specific goes into a theme.

## Skeletons

Headings are suggestions; keep the order. Every kind opens with the plain
version and a `:::lead`, and closes with sources.

**Decision or strategy brief** (`kind: brief`). This is the order
[example.md](references/example.md) uses:

1. The short version, with the `:::lead`.
2. Optional, when there is outside input: what it says, as short
   `:::quote`s, sourced or placeholder.
3. Where we stand: a status table with `{has}`, `{partial}` and `{missing}`.
4. Options compared: a comparison table.
5. What to do first: `:::ranked`.
6. Ideas: `:::idea` cards.
7. Optional, when the decision turns on a flow: a state table, a diagram and
   invariants, as in a design doc.
8. What to skip: `:::skip`.
9. Risks and open questions: `:::risks`, then `:::questions`.
10. How this page was made: what you read, then `:::sources`.

**Design doc** (`kind: design`). In plain words and lead. The building blocks,
with what each one promises. How they combine, with a comparison table. Math
or limits, with placeholder labels on chosen numbers. The lifecycle: state
table, diagram, invariants. First version and roadmap, ranked. Open questions
and risks. Sources and judgment.

**Status report** (`kind: status`). What changed and what it means, then lead
with the one thing the reader must act on. Status table by workstream. What is
blocked and who can unblock it. Next steps, ranked. What was checked and how.

**Idea portfolio** (`kind: portfolio`). The pick and why, in the lead. The
problem each idea answers, sourced. Idea cards, same fields each time. A
comparison table of effort and payoff, labelled judgment. What to skip. Open
questions. Sources.

## Visual rules

The renderer and theme apply these. Do not work around them in content. The
look is calm and editorial: type and whitespace do the work, and color stays
minimal.

**Hard bans for the Nessa default.** The default theme never uses any of these:

- A colored bar or line down the left or right side of anything: the lead box,
  notes, cards, quotes, blockquotes or sections.
- Pills, badges, chips, status dots, rounded tag shapes or colored label
  backgrounds. That covers sourced, judgment and placeholder labels, status
  words, the page-type line above the title, rank numbers, and the markers on
  skip, risk and question lists.

**What it uses instead.**

- Labels are italic muted text: *Sourced: tenant survey, read Nov 27, 2026.* or
  *Judgment.*
- Status is a plain bold word in the cell: **Has**, **Partial**, **Missing**.
  No colored background, no dot.
- Ranks are plain numerals. Lists use ordinary bullets.
- The lead box is set apart by whitespace and a thin full border on a barely
  different background. No side bar.
- Small-caps muted text for the page type, table headers and card field names.
- Contents sit in a left sidebar by default (`components.toc = "left"`):
  a sticky column of the `##` and `###` headings beside the reading column.
  On a wide screen the sidebar, a short fixed gap, and the reading column
  are one tight group, centered in the viewport so leftover space is equal
  on the left and the right. A theme can move the sidebar to the right of
  the text (still one centered group). The section being read is shown in
  bold, darker text. A plain sidebar-panel icon (a rounded rectangle with
  a vertical divider; mirrored when the sidebar is on the right) sits
  just after the "Contents" label and collapses the list; the text
  recenters, the same icon sits just left of the column aligned with the
  kicker, and the choice is remembered. Below about 1000px wide the same
  icon followed by the word "Contents" opens a panel that slides in from
  the same side; Esc or a click outside closes it. No divider bar, no
  marker on the current item. With JS off it is a static list, and print
  leaves it out.
- One readable column, about 46rem wide. Tables have hairline rules and no
  stripes. Cards only for parallel ideas. Diagrams sit in a thin bordered
  figure with a caption.
- The accent color is for links only. No emojis or decorative icons. The
  contents toggle is a plain sidebar-panel icon.
- It works in light, dark and print.

A user or project theme may opt back in to badges, pills, circled ranks,
symbol markers or a side bar through `[components.style]` (see
[themes](references/themes.md)), and the renderer respects that. The Nessa
default never sets them, and content never asks for them.

## What render.py checks

The renderer checks only these. Everything else on this page, including
plain words, honest labels and the right skeleton, is yours to check.

Errors (the render stops): an unknown directive; a directive or code fence
that is never closed; a list directive with no list; `:::states` without a
table; a theme file that sets `[voice.floor]`.

Warnings (printed; `--strict` makes them fail):

- No title, or a summary that is missing or not exactly two sentences.
- No `:::lead`, or a lead after the third directive.
- No `:::sources` list.
- No sourced or judgment label anywhere, or a `##` section other than the
  first and the sources section with no label.
- A `:::quote` without `cite=` or `date=`.
- A sentence longer than `voice.max_sentence_words` (25 by default) in
  paragraphs, lists, captions, the lead and idea cards. Quotes, tables, code
  and diagrams are not checked.
- A banned word from the voice, and a dash used as punctuation.
- Unknown theme tokens or style options (ignored).

## Self-check

Before sharing, check each line. Fix the page, not the checklist.

- [ ] The first screen answers the question in plain words, with a lead.
- [ ] Every section except the first and the sources section has a label.
- [ ] Sourced claims say what they came from and when it was read.
- [ ] Every chosen number, made-up example and invented input is marked
      placeholder.
- [ ] Every quote has `cite=` and `date=`; every source without a URL says
      where it lives and when you read it.
- [ ] Idea cards have the same fields in the same order.
- [ ] Ranked items each give a reason.
- [ ] Any lifecycle has its failure path in the diagram and testable invariants.
- [ ] Every skeleton part that is not marked optional is there, or "How this
      page was made" says why it is not.
- [ ] The summary is exactly two sentences.
- [ ] Open questions and what you did not read are stated.
- [ ] One name per thing across prose, tables and diagrams.
- [ ] render.py printed no warnings, and you looked at the page, or said you
      could not.
