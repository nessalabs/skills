# Core rule examples

Full bug-to-rule index for the two core rules in [../SKILL.md](../SKILL.md#1-prime-directive).

When you learn a new lesson, ask which core rule it is an example of first. If
one fits, add a row to its table below and put the detail with the owning rule.
Add a new principle only when no row fits. When several lessons that fit no row
keep pointing the same way, name a new core rule with its own questions and
examples.

---

## Core rule 1: every fact has one authority

See [Core rule 1](../SKILL.md#core-rule-1-every-fact-has-one-authority).

| What went wrong | Who should be in charge | Rule |
| --- | --- | --- |
| Two runs each number things from zero, so merging them gives duplicate ids | The code that creates the id | [An id is only unique where it was made](../../coding/SKILL.md#3-failure-first) |
| One caller checks "rebuild needed", another does not, and the screen shows stale data | The one gateway every request passes | [Put a rule where every path has to pass](../../coding/SKILL.md#3-failure-first) |
| A queue of one item empties into an unlimited buffer, and memory grows anyway | The stage that actually holds the item | [A limit only works if the next step really took the item](../../coding/SKILL.md#3-failure-first) |
| Shutdown and the garbage collector both free the same memory | One owner holding a single "I'll do it" claim | [Idempotent, or keyed](../../coding/SKILL.md#3-failure-first) |
| A file at a shared path is deleted, but a newer process had already replaced it | Whoever created that file | [Clean up only what you created](../../coding/SKILL.md#3-failure-first) |
| A late reply from an old request clears what the user just typed | The current request | [Check meaning as well as shape](../../coding/SKILL.md#principle-explicit-contracts-and-state-transitions) |
| Code checks "has a terminal handle" when it means "owns the process" | The fact itself, stored as itself | [Store the real fact](../SKILL.md#4-tactical-rules-inside-a-context) |
| Dropping a handle is expected to stop a background task, and the task keeps running | Whoever holds the resource now | [Hand off the off switch too](../SKILL.md#9-failure-and-invariants-first) |
| A default is copied into a setting; the setting changes later and the copy is stale | One function that picks the winner | [A value picked from several sources](patterns.md#derived-state-and-accelerators) |
| A lookup table outlives the content it points into, and crashes on the new content | The content it was built from | [When the source changes, everything built from it changes too](patterns.md#derived-state-and-accelerators) |
| A request from localhost is trusted, but any web page on the machine can send one | The caller's identity, not the route it took | [Who sent it travels with the message](structure.md#rules-for-a-process-or-bundle-boundary) |
| A macro crate builds on old Rust, but the code it writes for users does not | The place the promise is made: the user's build | [Test the promise where it is made](../../method/SKILL.md#2-verifying) |
| A second layer keeps its own list of valid names, and rejects names added later | The module that parses those names; others call it | [Check meaning as well as shape](../../coding/SKILL.md#principle-explicit-contracts-and-state-transitions) |
| Each output printer counts matches to stop at a limit, and miscounts matches that span lines | The search step, which knows what one match is | [Who has the information](../SKILL.md#2-how-you-decide) |
| A low-level read retries "interrupted" by itself, so a custom reader can no longer use that error to mean something | The operation that promised to finish the whole job | [Mechanism from policy](../SKILL.md#5-the-three-separations) |
| A quick "is the message complete?" check disagrees with the real parser, so the same bytes hang when split differently | The real parser; the quick check only narrows the work | [A shortcut may change speed, never the answer](patterns.md#derived-state-and-accelerators) |
| Data and errors travel on separate channels, and an error overtakes data already accepted | One state holding the order of every signal | [Signals whose order matters are one protocol](patterns.md#concurrency-and-failure) |
| Two copies of a plan share one cache, so filling it for one changes the other's answer | Each copy, for its own derived state | [Cloning an `Arc<Mutex<_>>` shares the state](../../coding/references/rust.md#types-and-invariants) |
| A feature gate sits on one function, but an older allowed wrapper calls it | The point every path passes, usually the type or its constructor | [Both sides of a gate are tested](patterns.md#feature-and-capability-gating) |
| A loop spins forever because flush says "ready" while the real write is still waiting | The real write's own answer | [A hand-written poll loop can go wrong two ways](../../coding/references/rust.md#concurrency) |
| Code checks an environment variable a hosted builder sets, but users can switch the same mode on without it | The condition the compiler actually sees | [Key a mode on what the compiler sees](../../coding/references/rust.md#testing-rust-specifics) |
| A cheaper version of an operation skips a flush the original does, and both sides wait forever | The operation's contract, which every version follows | [A cheaper version keeps the contract](../../coding/SKILL.md#5-performance) |
| A retry keeps an old handle after the resource was replaced | The stable identity, resolved by its current owner when work runs | [An id is only unique where it was made](../../coding/SKILL.md#3-failure-first) |
| An error unregistering a native callback is treated as proof its state can be freed | The outside system that still holds the reference | [Cleanup is structural](../../coding/SKILL.md#3-failure-first) |
| A tracing callback panics after permits move, before the guard records that it must return them | The guard that now owns cleanup | [Every panic is a way out](../../coding/references/rust.md#how-to-think-in-rust) |
| A future reserves capacity during construction, but dropping it before its first poll leaks that capacity | The future holding the reservation from construction | [A future's constructor can act sooner](../../coding/references/rust.md#async) |
| A blocked output stream stops unrelated input from being read | Each stream's own progress contract | [Independent progress](patterns.md#concurrency-and-failure) |
| A one-shot callback runs again before queued removal | The callback's execution claim | [Idempotent, or keyed](../../coding/SKILL.md#3-failure-first) |
| A stored record is copied and its mutation vanishes | The original value, borrowed or explicitly replaced | [Rust temporary copies](../../coding/references/rust.md#types-and-invariants) |
| A helper uses a different API level from its parent | Each process at startup, using the scoped selection | [Helper capability declarations](patterns.md#feature-and-capability-gating) |
| A directory exists while another process is still building it | The publisher that controls completion | [Artifact publication](patterns.md#derived-state-and-accelerators) |

---

## Core rule 2: a check only holds for what it looked at

See [Core rule 2](../SKILL.md#core-rule-2-a-check-only-holds-for-what-it-looked-at).

| What went wrong | What the check should have covered | Rule |
| --- | --- | --- |
| A queued update runs after its target was deleted, and crashes | The target as it is when the work runs, not when it was queued | [What you saw is a clue](../../coding/SKILL.md#3-failure-first) |
| A permission check passes on a host name, which then resolves to a blocked address | The resolved address, at the step that uses it | [Check the thing you will use](../../coding/SKILL.md#3-failure-first) |
| A setting meant for the target machine is checked with the build machine's path rules | The rules of the machine that will read it | [Surrounding settings are inputs](../../coding/SKILL.md#3-failure-first) |
| The first request to fill a shared cache entry leaves its own base path inside, and later requests use the wrong base | Only what is the same for everyone; each request brings its own context | [A cache key must include everything that changes the result](patterns.md#derived-state-and-accelerators) |
| Min and max stored in text order are used to skip data compared as numbers | The ordering the summary was built with | [Write down which way the error may run](patterns.md#derived-state-and-accelerators) |
| Two equal facts are deduplicated, and the copy that said "hidden" is the one dropped | The tag, which is part of the fact | [A tag is part of the fact](../SKILL.md#4-tactical-rules-inside-a-context) |
| An atomic becomes a plain field because "a lock covers it now", but `Drop` reads it without the lock | Every access under today's sharing | [Changing how a field is protected is a protocol change](../../coding/references/rust.md#concurrency) |
| A scheduler runs two steps at once because they talk through a channel it cannot see | Only what the dependency list can see | [Only queue what has to wait](patterns.md#concurrency-and-failure) |
| A test covers work already ready, but the resumed path or its consumer still breaks | The decision and observable effect in each affected path, with valid input | [Plan the proof before the code](../../coding/references/testing.md#plan-the-proof-before-the-code) |
| A cache watches length, but the content is replaced without changing length | Every permitted mutation that changes the answer | [When the source changes](patterns.md#derived-state-and-accelerators) |
| A pool lends capacity because an old readiness signal survives taking work | Availability at the owner's current admission transition | [Failure first](../../coding/SKILL.md#3-failure-first) |
| A record says complete after one of several promised consumers ships | The full decided scope and the evidence for each delivered slice | [Reconciling records](adr.md#reconciling-records-with-the-system) |
| A feature is marked delivered by name, but its shipped contract differs from the decision | The decided guarantees and any explicit revision | [Reconciling records](adr.md#reconciling-records-with-the-system) |
| A capability is disabled at runtime, but its foreign import still prevents an older supported target from linking | The final downstream link, including capability-off builds | [Rust compatibility checks](../../coding/references/rust.md#testing-rust-specifics) |
| A blocking pool fills with waits whose release needs that same pool | The execution capacity needed for progress | [Blocking work](../../coding/references/rust.md#async) |
| A host-size assertion passes but a foreign buffer has the wrong stride | The consuming representation | [Rust layout](../../coding/references/rust.md#types-and-invariants) |
| A cost estimate arrives after the planner already chose | Evidence available at the deciding phase | [Only reorder with a reason](patterns.md#derived-state-and-accelerators) |
| A protocol round trip works but the host displays a blank document | The actual consumer, including navigation and origin | [Consumer validation](../../coding/references/testing.md#rules) |
