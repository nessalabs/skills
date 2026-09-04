# Engineering

How to design a system, how to write a change, and how to find and prove things.

They are **model-invoked**: the agent reaches for them when a task fits,
and you can also invoke them by name.

- **[coding](./coding/SKILL.md)** — the working method for any code change. What
  to settle before writing, how to write, failure-first design, tests,
  performance method, how to shape and describe the change, and how to review
  your own diff. Reach for it whenever you are about to write or modify code.
  - References: [Rust](./coding/references/rust.md),
    [React & TypeScript](./coding/references/react-typescript.md),
    [testing](./coding/references/testing.md).
- **[system-architect](./system-architect/SKILL.md)** — how to structure a
  codebase so the next change stays cheap. Information ownership, boundaries,
  separating mechanism from policy, a small core with capability composed on
  top, invariants first. Reach for it before adding a module or a dependency
  between two parts of a system, or when a change starts touching more files
  than it should.
  - References: [structure](./system-architect/references/structure.md),
    [patterns](./system-architect/references/patterns.md),
    [velocity](./system-architect/references/velocity.md),
    [decision records](./system-architect/references/adr.md).
- **[pull-requests](./pull-requests/SKILL.md)** — how to describe a change and
  how to review one. The Motivation/Solution frame, before-and-after sections
  with diagrams, what evidence to show, commit conventions, and the review
  standard. Reach for it when opening, splitting, or reviewing a pull request,
  or when writing a commit message.
  - References: [diagrams](./pull-requests/references/diagrams.md).
- **[method](./method/SKILL.md)** — how defects get found, how a hypothesis gets
  verified, and which artefact holds a fix in place. Reach for it when
  investigating a bug, chasing a performance problem, or deciding what to
  automate or run in CI.
- **[wdym](./wdym/SKILL.md)** — say it in plain human language first. Reach for
  it when explaining a design, a change, a diagnosis, or a result; when the
  user asks what something means or wants it said more simply; and whenever
  `/wdym` is invoked.

## Adding a skill here

A skill earns a place by being a *procedure someone follows*, not a topic
someone reads. If the content is reference material for an existing skill, it
belongs in that skill's `references/` folder instead — references load only when
the skill needs them, which keeps the skill itself short enough to be read.

Every skill directory carries:

```
<name>/
  SKILL.md              name + description frontmatter, then the procedure
  agents/openai.yaml    display_name and short_description, for Codex
  references/           optional; loaded on demand by SKILL.md
```

The `description` is what makes the agent reach for the skill, so it states what
the skill covers *and* when to use it. Add the path to `skills` in
[`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json).
