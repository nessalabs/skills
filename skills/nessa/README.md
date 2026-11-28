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
- **[build-artifacts](./build-artifacts/SKILL.md)**: write a brief, design
  doc, status report or idea portfolio as one HTML page in Nessa's house
  style: the plain answer first, every claim marked sourced or judgment, and
  the same parts for parallel ideas. The agent writes Markdown with a few
  directives and [render.py](./build-artifacts/scripts/render.py) applies the
  winning theme (project, then user, then the Nessa default). Reach for it
  when someone asks for a page, a write-up or a report, or when
  `/build-artifacts` is invoked. The syntax lives in
  [references/format.md](./build-artifacts/references/format.md) and theming
  in [references/themes.md](./build-artifacts/references/themes.md).
- **[install-ios-over-the-air](./install-ios-over-the-air/SKILL.md)**: put a
  signed nessa-ios build on a registered iPhone from a link: export with
  development signing on a Mac, publish it with an `itms-services` manifest
  over HTTPS, and tap Install in Safari. Reach for it when someone wants the
  app on their phone without being at the Mac, or when
  `/install-ios-over-the-air` is invoked. The script
  [ota_page.py](./install-ios-over-the-air/scripts/ota_page.py) writes the
  page and manifest for one build.
