# Review posture, working checklist, and boundary smells

Reference catalogues for [../SKILL.md](../SKILL.md). Use these when reviewing a
change that spans files, before starting a design, or when a module starts to
feel hard to edit.

---

## Review posture

The review standard, order of attention, conventions, and full question list
live in [`pull-requests`](../../pull-requests/SKILL.md#reviewing). What an
architect checks in addition:

- Does this change point a dependency the wrong way, or reach past a contracts
  boundary?
- Does it put a domain rule in the application layer, or an application
  concern in the domain?
- Does it introduce a `util` by another name?
- Does it add configurability nobody asked for, or a flag that hides a design
  flaw?
- Does it split a lock or a component without carrying the orderings the old
  boundary supplied?
- Does it move a decision to where the code is rather than where the
  information is?
- Does it make the common case harder to read to serve a rare one?
- If this is the third similar thing, is the duplication now telling us
  something, and is the abstraction it implies the right one?

An architectural direction you would like to see is a non-blocking note, and
you say so.

---

## Working checklist

Before you write:

- [ ] The responsibility sits where the information is.
- [ ] Every fact this touches has one place in charge, and nothing else
      guesses, copies, or re-checks it.
- [ ] I can name the concept in the product's own words.
- [ ] I know which context owns it and what the invariant is.
- [ ] Machinery and rules are separable; definition and running state are
      separate values.
- [ ] Nothing product-specific went into the core.
- [ ] I know what happens if it crashes halfway, runs twice, or races.
- [ ] Owned state is keyed by its owner before its local id.
- [ ] I know how this gets deleted.
- [ ] The dependency this adds points inward.

Before you open a change: follow the checklist in
[`coding`](../../coding/SKILL.md#8-finishing-and-reporting).

---

## Smells that mean stop and re-cut the boundary

- A feature request routinely touches three or more modules.
- Two modules import each other, directly or through a third.
- A file is edited by every feature regardless of subject.
- A shared type has grown optional fields that only some callers set.
- Tests need elaborate setup to reach a simple assertion.
- A name in code needs translating before you can talk to product about it.
- Someone says "just add a flag."
- A core type has a field, branch, or variant that names one product feature.
- The machinery has to change every time a rule changes.
- A caller must check something before it is allowed to call.
- The description of a thing and the state of running it are the same object.
- A lookup by id alone can reach state that belongs to someone else.
- Code checks "has a handle" or "has an index" when what it really wants to
  know is something else.
- The only reason something is in the core is that it was easier to put it
  there.
- Someone says "we'll clean it up later" for the third time about the same
  file.

None of these are emergencies, but every one of them adds friction that
compounds over time.
