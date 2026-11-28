# Document format

A document is one Markdown file: front matter, ordinary Markdown, and a small
set of directives. `scripts/render.py` turns it into one HTML file. This file
owns the syntax; [SKILL.md](../SKILL.md) owns when to use each part.

## Front matter

```yaml
---
title: "Should Acme Notes add offline sync?"
summary: "What this is, and the main finding, in two sentences."
kind: brief          # brief | design | status | portfolio
date: Nov 27, 2026   # optional, shown under the summary
author: Saurav       # optional
status: Draft        # optional
---
```

One `key: value` per line. Do not use `#` headings for the title; the title
comes from here.

## Markdown that works

`##` sections and `###` subsections (they build the contents sidebar; it
appears once there are three or more `##` sections), `####`, paragraphs,
`-` and `1.` lists (one level), pipe tables, fenced code, `>` quotes,
`**bold**`, `*italic*`, `` `code` ``, and `[links](url)`. Raw HTML is escaped,
not passed through.

## Inline labels

Write these anywhere in text or a table cell.

| Write | Shows | Use for |
| --- | --- | --- |
| `{sourced}` or `{sourced: ADR 329, read Nov 26, 2026}` | italic muted text | a claim you read somewhere |
| `{judgment}` | italic muted text | your opinion, ranking or design |
| `{placeholder}` or `{placeholder: example price}` | italic muted text | a number or example you made up |
| `{has}` `{partial}` `{missing}` | a plain bold word | status in a status table |

The visible words come from the theme's `components.labels`. How they look
comes from `components.style` (see [themes](themes.md)); the Nessa default is
plain text, never a badge or pill.

## Leaf directive

`::caption {sourced: repo, read Nov 26, 2026} The status labels are my judgment.`
goes right under a heading. A caption is one or more labels first, then
optionally one or two sentences. A bare label (`::caption {judgment}`) is
fine when the label says everything about the section. In a caption each
label ends with a period, so it reads *Judgment.* The rest.

Write every date as `Mon D, YYYY` (`Nov 26, 2026`), in labels, quotes,
sources and front matter. Add a time and zone only when order matters:
`Oct 25, 2026, 7:19 PM (UTC-7)`.

## Block directives

Open with `:::name attributes`, close with a line that is only `:::`.
`tag=sourced|judgment|placeholder` adds a label where a block has a header.

| Directive | Body | Renders as |
| --- | --- | --- |
| `:::lead label="Recommendation" tag=judgment` | Markdown | the answer, in a thin bordered box |
| `:::note label="..." tone=info\|warn` | Markdown | a quiet side note |
| `:::quote cite="who, where" date="Oct 25, 2026" href="..." tag=...` | the exact words | quote with attribution line |
| `:::ranked` | a `1.` list, each item `**Claim.** Reason.` | plain numerals, bold claim, reason below |
| `:::idea title="..." tag=judgment` | `Field: value` lines | one card; cards in a row form a grid |
| `:::states` | a pipe table, first column the state | state table, states in mono |
| `:::diagram caption="..."` | a fenced `mermaid` block | bordered figure with caption |
| `:::invariants` | a `1.` list of "must always hold" sentences | numbered I1, I2 rules |
| `:::skip` | a `-` list | ordinary bullets |
| `:::risks` | a `-` list | ordinary bullets |
| `:::questions` | a `-` list | ordinary bullets |
| `:::sources` | a `-` list of `[title](url), note`, or for no URL: `title, where it lives, read Mon D, YYYY` | plain bulleted list; print shows URLs |

### Source items

Each item is a link or a named source, then what it is or when you read it.
End an item with `{placeholder}` when the source itself is invented, such as
sample data written for an example. It renders as a trailing italic
*Placeholder*:

```text
:::sources
- [ADR 329: subagents](https://example.com/adr/329), read Nov 26, 2026
- Support log, shared drive support/2026-11.csv, read Nov 27, 2026
- Sample survey of 40 users, made up for this example {placeholder}
:::
```

Idea cards in a row share a two-column grid. An odd last card spans the full
row with its fields in two columns. `components.idea_layout = "stack"` puts
every card on its own row.

A plain fenced `mermaid` block without `:::diagram` also renders, without a
caption. A plain pipe table is a comparison table.

### Idea card fields

Each field starts at the beginning of a line with a capitalised name and a
colon. Indented lines continue the field above. Use these fields, in this
order, for every card in a document:

```text
:::idea title="Big red button" tag=judgment
Pitch: One press stops every agent and takes their access away.
Who it's for: Anyone running more than a few agents at once.
Why we win: The gateway already owns the tokens and the stop.
Smallest first version: A halt command plus one button.
Risks: Offline machines stop only when they reconnect.
:::
```

## What the renderer checks

[SKILL.md](../SKILL.md#what-renderpy-checks) owns the list of checks. Errors
stop the render; warnings print to stderr, and `--strict` turns them into a
failure.
