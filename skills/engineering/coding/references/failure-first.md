# Failure-first checklist

Design the interrupted, repeated, and concurrent paths before the happy path.
This file holds the full operational checklist behind
[`coding` §3](../SKILL.md#3-failure-first).

## State and identity

- **One meaning per state; one authority per fact.** If state must be mirrored
  across a native or process boundary, give one owner the job of keeping both
  copies in sync. A sentinel that means two different things will be misread on
  a retry or restart; give each state its own name before you need to tell them
  apart.
- **An id is only unique where it was made.** A counter that restarts at zero
  each run, or a slot number that gets reused, hands out the same id twice. When
  combining things built separately, make ids unique at creation instead of
  fixing duplicates after merging. List what makes two things distinct: running
  the same code twice creates two things, so add the run identity, not just the
  source location. A hash speeds up lookup; it does not prove two things are
  equal. If a cache outlives the thing an id points to, include a generation
  number in the key so a reused id never hits stale data. Delayed work should
  keep the stable identity and resolve a replaceable handle when it runs, rather
  than retrying with a handle from an older generation.
- **Authority is part of the key.** Store state owned by a principal (tenant,
  session, window, user) under the owner first and the local id second. That way
  a guessed id cannot select someone else's state and callers do not have to
  remember to check.
- **Write the durable fact before announcing it**, and announce it before acting
  on it.
- **Decide fatal versus survivable**, and stay consistent with the surrounding
  code.

## Cues versus facts

- **What you saw is a clue, not the fact you care about.** An empty read, a
  zero, a `None`, a timeout, a process exiting, a request from localhost, or a
  file at a known path each *suggests* something is finished, safe, or yours,
  but something else could have caused it. Before acting, list what else it
  could mean:
  - An empty read can mean the buffer was full, not that the stream ended.
  - A child process exiting does not mean everyone writing to its pipe is done;
    grandchildren may still hold it open.
  - A command that started is not a command that succeeded. Wait for the actual
    condition you need.
  - An id saved before a delay only proves the target existed *then*. When
    queued or delayed work runs, look it up again: skip quietly if it may
    legally be gone, or fail loudly if it must still exist.
  - A temporary `Pending` may mean the scheduler yielded, not that a queue is
    empty.
  - If taking work changes available capacity, update the published readiness at
    that transition, not only when work is queued.
  - Empty input bytes do not prove a decoder has no unfinished record in its
    private state.
  - Name the event that starts a deadline. Moving a timeout past setup does not
    have to move the request itself; keep message and acknowledgement order
    intact.
- **Check the thing you will use, not the name that led to it.** When a name
  resolves to something else before use (a host name to an address, a symlink to
  its target, a relative path to a full path), run the check on the resolved
  value at the step that uses it. Checking the name can reject early, but it
  cannot be the only check. Saved output that can move needs internal references
  anchored to that output, while external references keep their own identity.
  Check old stored forms and whether older readers understand the new form.
- **Surrounding settings are inputs.** The working directory, environment
  variables, locale, clock, operating system, and whatever a registry calls
  "latest" today can all change behaviour. Decide whether each is a stable
  snapshot or live state. Pass snapshots explicitly. For live process-wide
  changes, give one owner control over mutation and dependent native-cache
  refreshes; a lock protects only the participants that acquire it. When several
  places need the same setting, compute it in one function. When work is
  prepared on one machine and runs on another (cross-builds, remote jobs, saved
  config), state whose rules each value follows and check it against those
  rules.

## Bounds and resources

- **Put a rule where every path has to pass.** If a limit, a "rebuild needed"
  flag, or a permission check is enforced by only one caller, another caller
  will bypass it. Place it in the single gateway every request goes through, and
  keep the underlying resource private there.
- **Every queue, buffer, and retry loop has a bound** and a stated behaviour at
  the bound:
  - Name what the bound protects and which owner enforces it. A window in one
    caller is pacing, not a limit, if another path reaches the same resource.
  - Check the limit before taking more, not after. Cap each read or growth to
    the remaining room so one read cannot overshoot the limit.
  - A limit only holds if the next stage truly took the item. A small queue
    draining into an unlimited buffer protects nothing. Pop an item only once
    the next stage accepts it, and still let close and cancel through while data
    waits.
  - When several layers set numbers, distinguish the caller's hard limit from a
    default. A default never raises a caller's limit, and an automatic tuner may
    only lower it.
  - Name the unit. A parsed record's budget is different from its transport
    buffer's capacity. Bound both partial acquisition and the complete item
    (including secondary fragments) without charging unrelated buffered data
    against it.
- **Do not hold shared capacity for work that does not exist yet.** One idle
  stream holding a unit of a shared window can stall every other stream. Claim
  capacity when real work is ready to use it, unless a standing share per user
  is deliberate and sized against the total. *When* you claim capacity decides
  whether things can deadlock; *how much* decides how they compete. (This is
  separate from publishing intent early below, which marks work as in flight
  without holding scarce capacity.)
- **Returning a resource includes notifying live waiters owed that change.**
  Name who can still wait, what lets them proceed, and what makes them runnable.
  Skip a closed peer only if closing already woke or cancelled its waiters, or
  none can exist. When liveness is uncertain, a redundant wake is safer than a
  missed one.

## Cleanup and re-entrancy

- **Anything reserved is rolled back or filled.** A count, slot, or published
  handle left behind by a failing constructor leaves peers waiting forever.
  Inject a failure at each setup step and trace who wakes the participants
  already started. A published placeholder needs an owner that outlives its
  initiator, or cancellation must fill or revoke it for peers.
- **Publish intent before the first observable async boundary.** If an operation
  can be triggered again while its setup awaits, spawns, or calls out, make the
  in-flight reservation visible before that boundary. Clear it exactly once on
  every terminal path (success, error, cancellation) so a second trigger cannot
  start a duplicate.
- **A callback into code you do not control is a failure boundary.** While you
  hold a lock or sit mid-transition, a user-supplied callback, destructor,
  clone, or formatter can panic, re-enter your code, or block on the lock you
  hold. Snapshot before calling out, queue mutations to replay afterward, or
  prove locally that re-entry is impossible. Convention is not a proof.
- **Cleanup ownership starts at acquisition.** Tie cleanup to a scope, guard, or
  lifetime before the next fallible step, including during partial setup; a
  cleanup method on the finished object does not cover failures before that
  object exists. Acquire branch-specific resources inside that branch, as late
  as possible. Clean up only what you created: before deleting a shared file or
  slot, verify a newer owner has not replaced it. If an outside system can still
  hold a pointer or token into your state, cleanup does not mean you can free
  it; a failed unregister is not proof the reference is gone. Keep the state
  alive until revocation or another documented guarantee proves no outside user
  remains.
- **Release transient state at its lifecycle boundary.** A long-lived owner
  should drop heavy phase-specific state when the phase ends, with a clear way
  to re-acquire it if a later legal event needs it. Before freeing anything
  early, list every reader and what proves each reader is finished. Check live
  state rather than assuming "we are past that phase", because re-entry can
  bring you back.
- **Idempotent, or keyed.** Assume any operation can run twice. Overwrites
  tolerate retries; appends need an identity that lets the receiver spot a
  repeat. For work that must run exactly once (such as freeing memory) and can
  be reached from multiple paths (normal close, shutdown, timeout, garbage
  collection), give one owner a single execution claim. Take the claim before
  calling out; deferred unregistration alone cannot stop a queued replay.
  Whichever path wins the claim does the work; the others do nothing, and no
  path guesses from its own notes whether it already ran.

## Shutdown and progress

- **A temporary missing prerequisite does not finish accepted work.** Keep work
  that the contract says should retry, and name what schedules the next attempt.
  Remove it only on success, defined cancellation, or terminal refusal—not just
  because its dependency is not ready yet. Before retrying after a fallback,
  require real progress toward the retry condition or stop with the defined
  outcome instead of looping recovery forever.
- **Decide what happens to accepted work at shutdown.** For each kind of work,
  state what acceptance promises: buffered, queued, admitted, executed, or
  visible to the receiver. Work promised a drain must not vanish silently, and
  closed admission must return an honest refusal. Route graceful close through
  the layer that owns pending output or protocol state. Name the last owner able
  to clean up on each termination path (an in-process hook cannot run after a
  force-kill). Indefinite outside input must not accidentally block shutdown.
  State the smaller guarantee of a timed or forced stop separately.
