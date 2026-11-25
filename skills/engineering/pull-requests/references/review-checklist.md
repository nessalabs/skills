# Pull request review checklist

Detailed checks for [pull-requests](../SKILL.md#what-to-actually-look-for). Ask
these of every change that touches state, and walk the code to verify the
answers rather than taking them on trust.

## State, concurrency, and failure

- **Halfway, twice, concurrent**: what must stay true if this stops halfway
  through, runs twice, or runs in two places at once?
- **Dropped locks, guards, or surrounding steps**: did a refactor quietly drop a
  lock, a guard, or small steps around a call? For example: *this returns the
  pinned items, but it no longer holds the list lock that used to cover the
  whole loop.* When two copies of some logic are merged into one, write down
  what each old copy did before, after, on error, and on panic—identical main
  code does not guarantee identical behaviour.
- **Caching, buffering, and shared slots**: check for cycles (references looping
  back), hostile or unusually large sizes, and re-entrancy (calling back into
  the same code before the first call finishes).
- **Calling out while holding a lock or mid-transition**: what state can the
  called code reach, and what happens if it panics, calls back in, or blocks?
- **Unnecessary synchronisation**: is a lock or other synchronisation primitive
  being added where a design change would avoid sharing the state in the first
  place?
- **Safety comments**: does each safety comment justify *why* the invariant
  holds, or does it merely restate which operations are called?

## Boundaries, ownership, and API shape

- **Dependency direction and boundaries**: does this point a dependency the
  wrong way, or reach past a module boundary?
- **Rule ownership**: does it put a rule in a layer that does not own it?
- **Unused state kept for a hypothetical reader**: is any state stored only to
  serve a getter or helper that nothing actually uses yet? Delete the state, the
  helper, and the code that maintains it.
- **Repeated call-site obligations**: does every caller have to remember the
  same extra step instead of handling it once inside the called code? If the
  same requirement is added in many places, look for a less error-prone way to
  enforce it once.
- **Manual sync**: do two places now have to be kept in sync by hand?
- **Stale names**: did the behaviour change while the name stayed the same, so
  the name is now wrong?
- **Bloated shared types or enum variants**: does this add fields to a shared
  type just for one caller, or add extra data or a new variant just for a rare
  case? Consider a flag instead of multiplying variants for edge cases.
- **Unpromised bounds**: does a consumer assume a limit or bound that the
  producer never promised?
- **Silent partial support**: does a new engine or fast path accept an option it
  does not implement? Accepting an option and silently ignoring it is a bug even
  when the common case works.

## Leaks, build visibility, and claims

- **Leaking internals**: does this make something internal look public?
  Internals can leak through an export, documentation, a compiler's "did you
  mean" hint, or generated code.
- **Build visibility**: does the build see this change the way you expect? Watch
  for files outside the watched tree or imports that break tree shaking.
- **Description accuracy**: is the claim in the description actually true?

## Strategy on large diffs and follow-up probes

**On a large diff**, classify the lines first: semantic code, tests,
documentation, moves, generated output, dependencies, and formatting. Then
review new ownership, state transitions, admission rules, wake behaviour, and
public contracts before anything else. A large test addition carries very
different risk from a small changed wake condition.

**Reason forward to the unbuilt feature** when a change is preparing for one:
ask *"will this still be correct once the object can be swapped out mid-loop?"*

**Widen the threat model after the first fix.** Once one bypass of an invariant
is closed, ask what the second bypass looks like before approving; the author
usually spots it once asked.
