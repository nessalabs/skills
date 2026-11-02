# Nessa

Skills for the agent helping a person with Nessa: setting a machine up, and
writing the docs Nessa shows. They follow the same rules as the engineering
skills: a procedure someone follows, the way to think first, then the steps.

- **[connect-a-computer](./connect-a-computer/SKILL.md)**: get another
  computer running agents for a Nessa hub over Tailscale. Install and sign in
  on both machines, let the hub be reached, enroll, approve, grant, and keep
  it serving. Reach for it when someone wants to add a computer, a worker
  says it cannot reach the hub, or `/connect-a-computer` is invoked.
- **[nessa-docs](./nessa-docs/SKILL.md)**: write a project's system map and
  statecharts in `docs/state`, grounded in the current source. For a risky
  flow (pairing, a lease, saving a secret, cleanup, resume), add a small model
  and check it before stamping the page. Reach for it when documenting a
  service, a user flow, or a lifecycle, or when `/nessa-docs` is invoked.
  The file format lives in
  [references/format.md](./nessa-docs/references/format.md).
