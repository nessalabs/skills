# Explicit contracts and state transitions

Use this approach when correctness depends on input expectations, intermediate
states, or messages between owners. It applies to UI actions, background work,
persistence, and messages between systems.

For each operation, define four things: what it accepts (inputs), what must
already be true (preconditions), what must stay true (invariants), and what each
output guarantees (postconditions).

Pick the simplest representation that makes those expectations clear: validated
methods, a reducer, a transition table, or a state machine. Any approach works if
it makes the behaviour and its guarantees just as clear and testable.

## Check meaning as well as shape

A well-formed message can still belong to another owner, request, or generation,
or arrive in a state that cannot accept it.

- **One validator and transition owner.** Name the single owner that validates
  and transitions state. Route every entry path through it so callers consume
  its decision instead of reimplementing the check.
- **Check returned results before acting.** Validate every returned result
  against the request and current state before letting it change anything. That
  includes every side effect it would trigger: showing an error, clearing what
  the user typed, starting a timer, or running cleanup. A late reply from an old
  request can be logged, but it must do nothing else.
- **Validate before transforms erase bad input.** Zipping, truncating,
  deduplicating, or coercing can make invalid input look valid. Check shape and
  meaning first unless that loss is part of the promised behaviour.
- **Apply protocol precedence and clean raw values.** When a protocol allows
  repeated or conflicting declarations, apply its precedence rules across all of
  them. When writing the result, remove conflicting raw values even if they
  failed to parse, and keep unrelated values intact. A parsed absence does not
  prove the raw declaration is gone.

## Write the transitions before implementing them

For a flow with meaningful intermediate states, add a transition table to its
existing design document or module contract with six columns: current state,
event or input, guard, effects, next state, and returned outcome.

Include refusal, interruption, retry, and uncertain-effect paths where they
apply. A sequence diagram shows messages and order; the table defines what each
step is allowed to do. Update the table whenever you add a state or change
ordering.

A simple operation does not need a state-machine framework or a new ADR; its
signature, API documentation, and tests are enough.

## Keep decisions separate from effects

Where practical, split the decision from the side effects:

- A pure step takes the current state and event and returns either a validated
  next state with intended effects, or a typed refusal.
- Distinguish `written`, `unchanged`, and `rejected` when only actual writes
  should notify dependents.
- Orchestration runs the effects and feeds their observed outcomes back to the
  owner.
- Define when state becomes visible or durable, and what stays authoritative if
  an effect fails or its outcome is unknown. Every intermediate state needs an
  honest meaning.
- **Treat error timing as part of compatibility.** Moving validation from
  definition time to use time changes which unused declarations get checked.

## Prefer sequential work with one writer per consistency boundary

Reach for concurrency only for a concrete reason, such as responsiveness or
independent I/O. When you do use it:

- Name the protected state, synchronization mechanism, critical section, lock
  acquisition order (when several locks exist), and ownership across
  cancellation and failure.
- **Watch await boundaries.** An async function can interleave at any `await`,
  even on a single thread. Revalidate your assumptions after the `await`, or
  hold explicit exclusive ownership across it.
- **Local locks do not protect remote state.** Independent processes need their
  own transaction or protocol guarantee.

Language-specific concurrency rules live in [Rust](rust.md) and
[React & TypeScript](react-typescript.md).

## Prove the contract through observable behaviour

Map the transition table to tests covering valid inputs, invalid combinations,
and the failure orderings that apply. Assert both the return value and the
resulting authoritative state, including what stayed unchanged on refusal.

Use controlled scheduling for competing events. For async, I/O, or retry
guarantees, [plan the proof before the code](testing.md#plan-the-proof-before-the-code).

## Adopt gradually

Use this approach on new work and tighten existing boundaries as you touch them.
If applying it cleanly requires a large unrelated refactor, describe that
follow-up separately. Claims about guarantees still need evidence, but adopting
this principle never requires an app-wide rewrite.
