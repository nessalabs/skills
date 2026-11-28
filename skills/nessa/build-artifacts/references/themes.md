# Themes

Nessa owns the default look and voice. A user or a project can change any part
of it by setting only the keys they want. Everything they leave out falls
through to the layer below.

## The layers

From lowest to highest; a higher layer wins for each key it sets.

| Layer | File | Who edits it |
| --- | --- | --- |
| Nessa default | `references/template.html` (tokens) and `references/default-theme.toml` (voice, components) | this skill |
| User | `$NESSA_ARTIFACTS_THEME`, else `~/.nessa/artifacts/theme.toml` | the person, in Nessa user settings |
| Project | `.nessa/artifacts/theme.toml` in the repo, found by walking up from `--project` | the repo's owners, in review |
| One-off | `--theme file.toml` (repeatable, last wins) | whoever runs the render |

So the order is project over user over the Nessa default. A file can be
`.toml` or `.json` with the same shape. Python 3.11 or newer reads TOML; use
JSON on older Python.

`render.py --explain-theme --project <repo>` prints every key and the layer it
came from. Use it when a page does not look the way someone expects.

## How keys merge

- Tables merge key by key. Setting `components.labels.has` leaves the other
  labels alone.
- A plain value or a list replaces the one below it.
- Two lists add up instead: `voice.add_rules` and `voice.add_banned_words`.
  Every layer's additions apply together.
- `voice.floor` is fixed. A theme file that sets it is refused.

## The file

```toml
[meta]
name = "acme"                 # shown in the page footer

[tokens]                      # any token declared in template.html :root
color-accent = "#c2410c"
font-heading = "Fraunces, Georgia, serif"
font-body = "\"IBM Plex Sans\", ui-sans-serif, sans-serif"
measure = "52rem"

[tokens.dark]                 # the same names, for dark mode only
color-accent = "#fb923c"

[voice]
register = "plain"            # plain | formal | terse
person = "we"                 # first | we | neutral
audience = "engineers on the platform team"
max_sentence_words = 22
banned_words = ["..."]        # replaces the list below it; rarely wanted
add_banned_words = ["game-changer"]
add_rules = ["Spell out every acronym the first time."]

[components]
toc = "left"                  # left (sidebar) | right | inline | off
idea_layout = "grid"          # grid | stack
mermaid = "cdn"               # cdn | off
eyebrow = true

[components.style]            # how things look; Nessa defaults shown
labels = "text"               # text | badge
status = "text"               # text (bold word) | pill
ranks = "numeral"             # numeral | circle
markers = "bullet"            # bullet | symbol
callout = "border"            # border | tint | bar

[components.labels]           # the words used for labels and status
judgment = "Our view"

[components.kinds]            # the eyebrow text per kind
brief = "Decision brief"
```

### Contents

`components.toc` sets where the contents list goes. It appears only when the
page has three or more `##` sections.

- `left`, the default: a sticky sidebar to the left of the text, listing
  `##` and `###` headings. On a wide screen the sidebar, a short fixed gap,
  and the reading column are one tight group, centered so leftover space is
  equal on both sides. It marks the section being read with bold, darker
  text, and collapses with a plain sidebar-panel icon (a rounded rectangle
  with a vertical divider) that sits just after the "Contents" label. When
  hidden, the text recenters and the same icon sits just left of the column,
  aligned with the kicker; the choice is remembered in the browser's
  localStorage. On screens under 1000px the same icon followed by the word
  "Contents" opens a panel that slides in from the left; Esc or a click
  outside closes it.
  Plain inline JS, no dependencies. With JS off it is a static list. Print
  hides it.
- `right`: the same sidebar on the right of the text, still one centered
  group. The panel icon is mirrored (narrow column on the right). When
  collapsed the icon sits just right of the column. The narrow-screen
  panel slides in from the right.
- `inline`: a two-column list of `##` headings above the text.
- `off`: no contents list.

The sidebar width is the `toc-width` token (14rem by default). The gap
between the sidebar and the text is `--space-6`.

### Component style

The Nessa default bans side bars and pills, badges, chips, dots and colored
label backgrounds; labels, status and ranks are plain text. `[components.style]`
is the only way back to them. A user or project that sets `status = "pill"`
gets pills, because overrides are respected, but nothing in the default theme
or in a document turns them on. Unknown keys or values are ignored with a
warning. The renderer writes a chosen non-default value as a `data-` attribute
on the page's `<html>`, and the matching styles sit in an opt-in block at the
end of `template.html`.

### Tokens

The token names and defaults live in one place, the first `:root` block of
`template.html`. The renderer reads that list and ignores, with a warning, any
token a theme sets that is not in it. The groups are:

- **Color:** `color-bg`, `color-surface`, `color-surface-2`, `color-text`,
  `color-muted`, `color-border`, `color-accent`, `color-accent-ink`,
  `color-has`, `color-partial`, `color-missing`, `color-sourced`,
  `color-judgment`, `color-placeholder`, `color-code-bg`. The soft tints
  (`color-*-soft`) are mixed from these, so changing the accent also changes
  the lead background.
- **Type:** `font-body`, `font-heading`, `font-mono`, `text-xs` to `text-3xl`,
  `leading`, `leading-tight`, `weight-heading`.
- **Space and shape:** `space-1` to `space-8`, `measure`, `radius`,
  `radius-sm`, `border-width`, `shadow`, `toc-width`.

A color set only under `[tokens]` applies to light mode; dark mode keeps its
own default unless `[tokens.dark]` sets it, so a brand color picked for a
white page cannot make dark mode unreadable. Non-color tokens apply to both.
A layer that sets a light color without a dark value also drops any dark
value a lower layer set for it, so a project's brand color never pairs with a
user's dark brand color.
Values cannot contain `;`, `{`, `}` or `<`.

Fonts are names, not downloads. Name fonts the reader's machine has, with a
fallback stack. The page makes no network request except the optional
diagram script.

## How the voice settings combine with wdym

wdym is the base and is never replaced. The theme can only tune it.

1. **The floor** comes from the Nessa default and cannot change: answer first,
   sourced and judgment marked, placeholders labelled, gaps stated, no guesses
   stated as fact.
2. **wdym** owns the sentence rules: plain words, small words kept, no
   narration, light formatting.
3. **The theme** sets the dials: `register` changes formality, `person` changes
   who speaks, `audience` and `max_sentence_words` change the target,
   `add_rules` adds house rules, and the word lists add banned words.

When a theme rule seems to conflict with wdym, the narrower rule wins for the
page (a project that wants "we" gets "we"), but nothing may break the floor.
`render.py --voice` prints the combined result for the agent to follow; the
renderer's lint checks the word list and dashes, not tone.
