---
name: connect-a-computer
description: "Get another computer running agents for a Nessa hub over Tailscale: install and sign in on both machines, let the hub be reached, enroll with a code from Devices › Add a computer, approve its key, grant what it may run, and keep it serving. Use when someone wants to add a computer or worker to Nessa, a worker cannot reach its hub, or /connect-a-computer is invoked."
---

# Connect a computer

A computer that works for Nessa calls the hub, the Mac Nessa runs on, and
keeps that call open. So two things have to be true before anything else:
the computer can reach the hub's address, and the hub is listening there for
more than itself. Tailscale gives both machines a private network that
reaches from anywhere, with nothing open to the internet. Most failures are
one of those two things, so check them in that order before reading logs.

Run each command yourself where you can, and tell the person what you found
in plain words. Ask before installing anything or signing in for them.

## 1. Both machines on one tailnet

On each machine, check first:

```sh
tailscale status
```

If it is missing, install it: on a Mac the Tailscale app from
tailscale.com/download (open it once); on Linux `curl -fsSL
https://tailscale.com/install.sh | sh`; on Windows the installer from
tailscale.com. Then sign in to the **same** account or tailnet on both:
`sudo tailscale up` on Linux, the app's menu elsewhere. Signing in opens a
browser page the person completes; wait for them.

Find the hub's name on the tailnet. On the hub:

```sh
tailscale status --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))'
```

The first part of that name (`studio` in `studio.tail1234.ts.net`) is what
Nessa shows. If MagicDNS is off on the tailnet, use the hub's address from
`tailscale ip -4` instead, everywhere a name appears below.

## 2. The hub listens for other computers

In Nessa on the hub, open **Devices › Add a computer**. If it says no other
computer can reach the hub, press **Let other computers reach it**: Nessa
starts again listening on every interface, port 47650 unless the page shows
another. If it names a loopback address someone chose by hand, change
`native.listenAddress` in the hub's `config.json` to `0.0.0.0:<port>` and turn
linking off and on in Settings › Linked devices.

From the other computer, check it can reach that port before going on:

```sh
tailscale ping <hub>
nc -vz <hub> 47650        # or: Test-NetConnection <hub> -Port 47650 on Windows
```

`ping` works and `nc` does not: the hub is not listening there yet (step 2),
the macOS firewall is blocking Nessa (allow it in System Settings › Network ›
Firewall), or the tailnet's access rules do not allow that port.

## 3. Enroll, approve, grant

The other computer needs a Nessa build that speaks the hub's lease protocol
(`nessa env protocol` prints the same on both) and its own `config.json` with an `agents` section naming the
agents it may run, readable only by its own account (`chmod 600`).

Run the two commands the Add a computer page shows, on the other computer,
in order. The code lasts ten minutes; the page makes a new one on request.

```sh
nessa env enroll <hub>:47650 <CODE>
nessa env dial <hub>:47650
```

`enroll` answers "Paired" and `dial` waits for approval. On the hub the
page shows that a computer used the code, with its key's fingerprint:
approve only if it used the code just now, on the computer the person meant.
A code that someone else used is cancelled with **New code** instead.

Then say what the hub may run there. Nothing runs until it is granted:

```sh
nessa env grant --agent claude        # each agent the person wants, by name
nessa env grant --commands --max-timeout 10m   # only if they want commands run there
nessa env grants                      # check
```

The computer now shows **Online** in Devices with its processor, memory and
disks.

## 4. Keep it serving

`nessa env dial` serves only while it runs, and calls again by itself when
its connection drops. To survive a logout or restart, run it as a service the
computer already uses (a systemd user unit, a launchd agent, or a container
with a restart policy), with `--drain-deadline 20s` added. With it, Ctrl-C or
SIGTERM lets the work the hub gave the computer end cleanly first; without
it, a stop drops that work at once. Keep the deadline below a container's
stop grace.

## When it does not connect

Read the symptom against the two facts at the top before anything else.

| What you see | What it means |
| --- | --- |
| `enroll` cannot connect | Step 1 or 2: not on the tailnet, or the hub not listening there |
| `enroll` says it is not a pairing code, or the gateway refused | Mistyped, used or expired: make a new code on the page |
| `enroll` says this machine is already paired, or has a pairing waiting | Run `dial` instead; to start over, remove the pairing directory it names |
| `dial` waits and the page never shows a key | The page was left or made a new code before approving: start again from `enroll` with a new code |
| Approved, but Devices says Offline | `dial` is not running on the computer |
| Online, but its threads say the environment is unavailable | Nothing granted: step 3's `grant` |
| Refused for its build or protocol | The two machines run different Nessa builds |
