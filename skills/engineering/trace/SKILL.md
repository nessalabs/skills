---
name: trace
description: "Reconstruct the real runtime path of a feature from source: every hop with its file and line, every branch that can run, and at each hop what state is written, what is locked, where it waits, and where it crosses a thread or process. Walks the syntax tree one hop at a time with scripts/expand.py instead of reading whole files. Regenerated from current source every time. In debugging mode it starts from a symptom, keeps only the branches that could produce it, and ends with ranked suspects, a probe for each, the invariants to assert, and where a test goes. Use when the user asks how something flows, what happens when they click/send/call X, for a stack or call trace, where a delay or hang or duplicate could come from, or when they invoke /trace."
---

# Trace

Print how a named feature actually runs through the codebase right now: entry
point, each hop, what each hop does to state, where it waits, where it hands
off to another thread or process, and what comes back. Not an architecture
essay. Not a remembered path from an earlier chat.

Two questions a trace answers, and the mode follows from which was asked:

| The user asks | Mode | The trace ends with |
| --- | --- | --- |
| "What happens when…", "how does X flow" | **Understanding** | The gaps: where the path leaves the repo or dies at a stub |
| "Why is it slow / late / hung / duplicated / missing", "where could Y come from" | **Debugging** | Ranked suspects, a probe per suspect, invariants to assert, where a test goes |

A debugging trace is a [`method`](../method/SKILL.md) investigation drawn as a
path: the symptom is restated as an observable, the hops that could produce it
are hypotheses, and the trace exists to say where to look and how to refute
each one. It does not conclude; it points.

This skill is agent-agnostic. Prefer a smaller explore-style subagent for the
walk when the harness can delegate; otherwise walk the code yourself with the
same rules. Do not use it for "why did we design it this way"; that is
[`system-architect`](../system-architect/SKILL.md). Do not use it to argue a
fix; that is [`method`](../method/SKILL.md). Trace answers *what runs* and
*where it could go wrong*.

---

## Procedure

1. **Name the feature, the entry point, and the question.** One sentence each.
   If several entries exist (UI, CLI, RPC), ask which, or trace each as its own
   tree. In debugging mode, restate the symptom as something observable ("no
   `write(1)` until the pipe closes"; "the join handle is never woken") so the
   trace can be checked against it.
2. **In debugging mode, list the mechanisms that could produce the symptom
   before walking.** Three to five, one line each: a buffer that waits for a
   terminator, a bound that is reached, a wake-up that can be lost, a mode that
   defers to end of stream. This list is the stopping rule for step 5: a
   branch earns a path only if it realises one of these mechanisms. Write the
   list into the output so the reader sees what was looked for.
3. **Walk one hop at a time from the syntax tree.** Run
   `scripts/expand.py SYMBOL --root <repo>` on the entry; it prints the
   definition's file and lines, every call in its body with its line, a tag
   where the callee looks like a lock, wait, handoff, spawn, I/O, or state
   write, and the candidate definition sites of each callee. Pick the callees
   that matter for the question, run the script on each, and only then open
   the file at the lines that matter to read the conditions and the writes.
   Details in [Walking with the parser](#walking-with-the-parser). When
   delegating, brief the walker with: the feature, the entry, the question,
   the candidate mechanisms, the script, and these rules. Do not accept a
   prior chat's trace as input.
4. **Always regenerate from current source.** When a hop leaves the repository
   (standard library, a dependency), follow it into the installed source and
   mark it as external with the crate and version. The load-bearing hop is
   often there: the flush heuristic, the buffer bypass, the default capacity.
   If the source is not installed, fetch it (`cargo fetch`, `cargo vendor`,
   `go mod download`, `npm ci`, the language's equivalent); if you cannot,
   write a gap naming what could not be read.
5. **Follow every branch that can run**, then choose which to render:
   - Understanding mode: every branch, each as its own full path. Partial
     trees are wrong.
   - Debugging mode: every branch that realises one of the step 2 mechanisms,
     including siblings reached by a different flag or configuration, because
     those are what the reader needs to rule in or out. Omit the rest, and
     list them in one line each with the reason, so the reader knows they were
     considered.
6. **At every hop that gates the observable, ask the failure-first
   questions.** What is written, under what protection? What if it stops here?
   What if two run here? Which observation is ambiguous (a zero-length read is
   not end of stream; a timed-out wait is not a notification)? Mark what you
   find. Mark the state writes that decide whether the observable happens, not
   every counter the code touches; a trace where every line is marked has no
   marks.
7. **Stop at meaningful hops.** Include module boundaries, named functions the
   reader must know, and every hop that writes gating state, takes or releases
   a lock, waits, spawns, or crosses a thread or process. Collapse plumbing
   (a chain of forwards that does none of those) into one line citing its
   entry and exit. A one-line function that decides whether the line
   terminator is included in the write is not plumbing.
8. **Render** with the rules below, and **lead with the mechanism in plain
   words**: two or three sentences, before any tree, saying what the path does
   and where the interesting decisions are. The tree is evidence for those
   sentences.
9. **End the way the mode requires.** Debugging: suspects, probes, invariants,
   test location. Understanding: gaps.

---

## Walking with the parser

`scripts/expand.py` uses [ast-grep](https://ast-grep.github.io) to read the
syntax tree, so a hop costs one command and returns names, not files. It
handles Rust, Python, Go, JavaScript, TypeScript, Java, Kotlin, Ruby, C#, C,
and C++. It needs `ast-grep` or `sg` on the path, or node, in which case it
runs the npm package on demand.

```bash
python3 scripts/expand.py 'LockedImpl::spawn_task' --root tokio
```

```text
def src/runtime/blocking/pool.rs:611-647   fn spawn_task<F>(
    620  self.mutex.lock [lock]
         -> src/loom/std/parking_lot.rs:61  -> src/loom/std/mutex.rs:21
    630  locked.queue.push_back [state]
         -> src/runtime/scheduler/multi_thread/queue.rs:139
    633  metrics.num_idle_threads
         -> src/runtime/blocking/pool.rs:42
    634  on_no_idle
         -> (not defined in repo: external, trait, or builtin)
    643  self.condvar.notify_one [handoff]
         -> src/loom/std/parking_lot.rs:147
```

How to use it:

- **Expand, don't read.** Start at the entry, run the script, choose the
  callees that bear on the question, run it on those. Open a file only at the
  lines the script gave you, to read a predicate or a write. The whole walk
  for a ten-hop path is ten short commands and a few `sed -n` ranges, not ten
  files.
- **Tags are hints to look, not conclusions.** `[lock]`, `[wait]`, `[handoff]`,
  `[spawn]`, `[io]`, `[state]` come from the callee's name. Confirm each by
  reading the line before you put a marker in the trace.
- **An unresolved callee is a finding.** "Not defined in repo" means the path
  leaves the repository (a dependency, the standard library), goes through a
  trait object or function pointer, or is a closure passed in. Each of those is
  either an `ext:` hop to follow into the installed source or a `gap:` line.
- **Qualified names disambiguate.** `Type::method` and `Class.method` pick the
  definition inside that container; a bare name lists every definition with
  that name, nearest to the caller first.
- **`--depth 2` pre-expands** the callees defined in the repo, breadth-first.
  Useful for a first look; too noisy past two.
- **Extras per language** are printed as `~await`, `~unsafe`, `~macro`,
  `~with`, `~go`, `~defer`, `~select` lines: the points where control can
  leave, block, or be re-entered.
- When the script has no rule for the language, or the code is generated or
  dynamically dispatched beyond what a syntax tree shows, fall back to grep
  and reading, and say so in the header.

---

## Render rules

**Default to ASCII.** Use mermaid only when the user asks for it or the surface
clearly renders it (GitHub markdown, an IDE chat known to render it). If unsure,
ASCII only. Never default to both. Flags: `--ascii`, `--mermaid`, `--both`;
explicit flags win.

### Header and summary

```text
# Trace: <feature>
Entry: <symbol or UI action>            <path:line>
Question: <understanding | debugging: symptom as an observable>
Source: <repo> @ <revision>; external: <crate@version, ...>

<Mechanism, in plain words. Two or three sentences. Where the decisions are.>

Mechanisms considered: M1 <...>  M2 <...>  M3 <...>      (debugging mode)
```

### Line forms

One spine per thread of control. Every hop carries its location. The markers
are the whole point; a trace without them is a call list.

```text
|-----> Symbol                                  path:line     call, next hop
|-----> A … D (via B, C)                        path:line     collapsed plumbing; cite entry and exit
|   ? predicate                → A | B           path:line     decision; names the paths it selects
|   ? predicate [set at path:line]  → A | B                    decision made earlier, observed here
|   // state: field = value                                    write that gates the observable
|   +lock name  ...  -lock name                                lock held from + to - (bracket the hops between)
|=====> Symbol   WAITS: until <condition>        path:line     blocking point; say what unblocks it
|=====> wait(cv)  WAITS: … (releases name; reacquires on wake)  a wait that is also the lock's release
|<----- loop to Symbol                                         back edge; say what advances it
|-----> run(f)   [opaque: user code; may block or re-enter]    loop body or callback you cannot see into
|   ~~~> notify/wake/send  ==> [thread: name]                  cross-thread or cross-process handoff
|   ext: crate@version path:line                               hop outside the repo
|   !! S1 <why this hop could produce the symptom>             suspect marker (debugging mode)
|   gap: <stub, dynamic dispatch, callback registry>           the static walk cannot continue
```

Layers are boxes labelled with the names the codebase uses, and with the
thread when more than one is involved: `[ blocking::pool · thread: worker ]`.

Across a handoff, the sender keeps its `+lock` bracket open through the
`~~~>` line if it still holds the lock there, and closes it after. The
receiver's wait line says which lock it releases while waiting. That is the
convention for every condition-variable pool; write it, do not reinvent it.

### Shape

```text
## Common prefix

|
|  [ <Layer> ]
|     <Entry>                                    path:line
|-----> <hop>                                    path:line
|   // state: <what changed>
|   ? <predicate>              → A | B           path:line

## Path A — <label>, from ? <predicate>

|
|  [ <Layer> ]
|-----> <hop>                                    path:line
|   +lock <name>
|-----> <hop>                                    path:line
|   // state: <counter> += 1
|   ~~~> notify_one            ==> [thread: worker]
|   -lock <name>
|
|  [ <Layer> · thread: worker ]
|=====> wait_timeout   WAITS: until notify or keep_alive (releases <name>; reacquires on wake)   path:line
|   ? num_notify != 0          → continue | timed out (Path G)
|-----> <hop>                                    path:line
|<----- loop to <hop>                            advances when queue empties

## Path B — <label>, from ? <predicate>
...

## Actor — <name>  (runtime shutdown, a signal handler, a timer: not selected by any predicate above)

|
|  [ <Layer> · thread: <who> ]
|-----> <hop>                                    path:line
|   ~~~> notify_all            ==> [thread: every worker]
```

The common prefix is written once and ends at the first decision. Each path
starts by naming the predicate and value that selects it. A path that shares
its middle with another says `as Path A from <hop> to <hop>` for that stretch
only; the hops that differ are written in full. A thread that acts on the
traced state without being selected by a decision in the path (shutdown, a
signal, a timer) is an `## Actor` spine, joined to the paths by `~~~>` lines.
Same feature, other outcomes: separate paths, never footnotes.

### Ending

Debugging mode, all four, in this order:

```text
## Suspects

S1 <mechanism>, at <Symbol path:line>. Would produce the symptom when <condition>.
   Probe: <one command, breakpoint, log line, or counter that confirms or refutes it>.
S2 ...

Ruled out: <mechanism> — <the line that rules it out, and why>.

## Invariants to assert
- <counter or relation that must hold, and the two hops it must hold between>

## Where a test goes
- <file>: <what the test controls and asserts; the transition, not elapsed time>
- or: no unit seam exists because <reason>; the boundary to test from is <process, pty, socket>

## Gaps
- <what the static walk could not follow, and the candidates>
```

Suspects are ranked by how directly the hop produces the observable, not by
how interesting they are. A suspect outside the repository (the upstream
process, the kernel, the terminal) is listed with its probe like any other;
the most likely cause of "no output" is often the process before this one.
A mechanism you checked and rejected goes under *Ruled out* with the evidence,
not in the ranked list. Each probe is something the reader can run in under a
minute.

Understanding mode ends with `## Gaps` only.

### Mermaid (when allowed)

Same hops as `flowchart TB`, one subgraph per layer, node labels as code
symbols, decisions as diamond nodes, cross-thread handoffs as dashed edges.
Prose header first; diagram second. See [format](references/format.md) for a
worked example and the mermaid twin.

---

## Output checklist

- [ ] Header names the feature, the entry, the question, and the revision
- [ ] The mechanism is stated in plain words before any tree
- [ ] Debugging mode lists the mechanisms considered, and they are the stopping rule for branches
- [ ] Every hop has a file and line; external hops name the crate and version
- [ ] Every decision is a `?` line naming the predicate and the paths it selects
- [ ] Gating state writes, lock brackets, waits, back edges, and handoffs are marked; plumbing is collapsed
- [ ] Every branch the mode requires has its own path or actor spine; omitted branches are listed with a reason
- [ ] Symbols match the code; syscalls and foreign processes are labelled as such
- [ ] Render is ASCII unless mermaid was justified
- [ ] Debugging mode ends with suspects (and ruled out), probes, invariants, and a test location
- [ ] Trace was regenerated from current source
