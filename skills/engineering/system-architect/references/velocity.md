# Velocity diagnostics

Velocity is not typing speed. It is how many changes can happen in parallel
without coordination — a property of the structure, which means it can be
measured and it can be designed for.

Run these periodically. They tell you whether the structure is still earning its
keep, and each of them goes wrong long before anyone says "the codebase is
getting hard to work in".

- **Files per routine change.** Rising means boundaries are drifting. Look at
  the last ten changes and ask, for each, how many files it *should* have
  touched. The gap between should and did is your architectural debt, measured
  honestly.
- **Modules per feature.** A normal feature touching three or more contexts is a
  boundary in the wrong place, not a big feature. Fix the boundary rather than
  getting better at touching four modules.
- **Time from open to merge.** If it is growing, changes are too large or
  ownership is unclear.
- **The file everyone edits.** Whichever file appears in the most diffs
  regardless of subject is either a composition root (fine) or a god object
  (not).
- **Setup lines per test.** Growing setup is the earliest warning of coupling,
  and it shows up long before anything else does.
- **How often a change to one feature breaks another.** If two things fail
  together repeatedly, they share something they should not.

## Keeping the map current

The architecture map is updated in the same change that invalidates it, or it is
not updated at all. A stale map is worse than no map, because people trust it.
When a change adds a module, moves a boundary, or breaks an absence, the map
moves with it or the change is not done.

For how an individual change should be sized, described, and reviewed, see the
[`pull-requests`](../../pull-requests/SKILL.md) skill.
