# skills

[![skills.sh](https://skills.sh/b/nessalabs/skills)](https://skills.sh/nessalabs/skills)

Engineering skills for agents and people: **how to design a system, how to write
a change, and how to find and prove things.**

They were distilled by reading the source, the commit history, and the pull
request discussions of long-lived, high-performance open source projects — async
runtimes, HTTP stacks, regex and search engines, concurrency libraries,
analytical databases, media frameworks, React renderers, compilers, and
component libraries — and keeping only what recurred across several of them.
Nothing here is one project's style guide restated. Where a rule exists, someone
had to learn it the expensive way first.

## Installation

Two ways in. **The Claude Code plugin** installs the set as a managed bundle
that updates when we ship. **[skills.sh](https://skills.sh/nessalabs/skills)**
copies editable files into your project so you can adapt them. Pick one;
installing both gives you every skill twice.

<details>
<summary><strong>Claude Code plugin</strong></summary>

```bash
/plugin marketplace add nessalabs/skills
/plugin install nessalabs-skills
```

</details>

<details>
<summary><strong>Codex, and any other agent</strong></summary>

```bash
npx skills@latest add nessalabs/skills
```

Choose which skills to take and which agents to install them on. Pull later
changes with `npx skills update`.

</details>

<details>
<summary><strong>Manually</strong></summary>

```bash
git clone https://github.com/nessalabs/skills.git
for s in coding system-architect pull-requests method; do
  ln -sfn "$PWD/skills/skills/engineering/$s" ~/.claude/skills/$s
done
```

Symlinks, so `git pull` keeps them current. Use `~/.agents/skills` instead for
Codex and other Agent Skills harnesses.

</details>

## The skills

All four are model-invoked: the agent reaches for them when a task fits, and
you can also type them.

| Skill | Reach for it when |
| --- | --- |
| **[coding](skills/engineering/coding/SKILL.md)** | You are about to write or modify code, or about to open a pull request. The working method: what to settle before writing, how to write, failure-first design, tests, performance method, how to shape the change, and how to review your own diff. |
| **[system-architect](skills/engineering/system-architect/SKILL.md)** | You are designing a module, adding a dependency between two parts of a system, arguing about boundaries or layering, or a change has started touching more files than it should. |
| **[pull-requests](skills/engineering/pull-requests/SKILL.md)** | You are opening, describing, splitting, or reviewing a pull request, or writing a commit message. The Motivation/Solution frame, before-and-after sections with mermaid diagrams, what evidence to show, and the review standard. |
| **[method](skills/engineering/method/SKILL.md)** | You are investigating a defect, chasing a performance problem, or deciding what to automate, test, or run in CI. |

Each carries references that load only when the skill needs them: Rust and
React/TypeScript practice and a testing guide under `coding`; structure,
concrete patterns, velocity diagnostics and decision records under
`system-architect`; diagram conventions under `pull-requests`.

Skills are grouped into buckets under `skills/`. There is one today —
[`engineering`](skills/engineering/README.md) — and its
[README](skills/engineering/README.md) is the index. New buckets get their own
folder and their own index.

## The idea

> Build the smallest system where each piece has a clear reason to exist, owns
> the information it needs, and can evolve independently.

Responsibility goes where the information is. Machinery stays separate from
rules, intent from execution, definition from running state. The core stays
small and knows nothing about the product built on it. Design starts at the
crash, the retry, and the race — not at the happy path. Flexibility is bought
only when a requirement forces it. The rules that matter most are stated as
absences — the imports and couplings that must never exist — which is why they
need tests. And a finding with no artefact holding it in place has a half-life
of about two refactors.

Velocity is not typing speed. It is how many changes can happen in parallel
without coordination, and that is a property you design for directly.

## Contributing

A rule earns its place by having been learned expensively somewhere real. If you
add one, say in the pull request where it came from and what it cost — the
citation does not belong in the skill, but a reviewer needs it. Rules that are
merely reasonable get cut; there are already too many of those in circulation.

MIT licensed.
