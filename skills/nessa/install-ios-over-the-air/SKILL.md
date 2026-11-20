---
name: install-ios-over-the-air
description: "Put a signed nessa-ios build on a registered iPhone from a link instead of a cable or devicectl: archive and export with development signing on a Mac, publish the .ipa with an itms-services manifest over HTTPS, and tap Install in Safari. Use when someone wants the iPhone app on their phone without being at the Mac, a Remote Control install is the only way in, or /install-ios-over-the-air is invoked."
---

# Install the iPhone app over the air

Source: [Build an iPhone App on Your iPhone, Then Install It Over the Air](https://jfdi.bot/blog/build-iphone-app-on-iphone-install-over-the-air)
(JFDI Bot). The technique below is that article's, applied to
nessa-ios.

An iPhone will install an app from a web page when three things hold. The
page links to `itms-services://?action=download-manifest&url=…`; the manifest
and the `.ipa` it names are served over HTTPS with a real certificate; and the
app is signed with a profile that lists this phone. iOS fetches the manifest
and the `.ipa` itself, outside Safari, with no cookies. So a login page in
front of them fails: the permission has to be in the URL (an unguessable
path, or a signed link).

Two parts, which fail for different reasons: **signing** (a Mac with the
team's certificate, and a profile listing the phone) and **delivery** (an
HTTPS place the phone can reach). Over the air changes only delivery. The
build still needs a Mac with Xcode and the team's signing identity, or a
CI Mac given those as secrets. Most failures are a phone missing from the
profile, or a link that is not HTTPS with a real certificate. Check those
two before anything else.

Run each command yourself where you can, and tell the person what you found
in plain words. Ask before you register a device, create a certificate, or
publish anything outside their tailnet.

## What this changes in the nessa-ios flow

Today `./iphone.sh` builds Debug and installs with `xcrun devicectl`. That
needs the phone paired with the Mac, unlocked and on the same network or
cable, and the install runs in a Remote Control session on the Mac. Over the
air:

- **Removes** the phone's link to the Mac: the person installs from anywhere,
  whenever they open the link.
- **Keeps** the Mac. The build still runs where the signing identity is. On
  the person's Mac, that is still one Remote Control session, which needs
  their OK, but it can end with a link instead of waiting for the phone.
- **Removes the Mac step entirely** only when a CI Mac builds it (step 6).

Build **Release**. Debug builds of nessa-ios use the mock repository, so a
Debug build on a phone talks to no gateway.

## 1. Once: what only the account holder can provide

- **A paid Apple Developer membership** on the team in
  `App/Nessa.xcodeproj` (`DEVELOPMENT_TEAM`). Read the team from there;
  never copy it into a public file.
- **The phone registered on that team.** A phone that `./iphone.sh` has
  installed to is already registered, since it builds with
  `-allowProvisioningDeviceRegistration`. A new phone: get its UDID (Finder
  or Xcode's Devices window with the phone plugged in, or a Profile Service
  configuration profile as the article shows) and add it in the developer
  portal under Devices. Apple allows 100 iPhones per membership year, and a
  disabled device still uses its slot.
- **Developer Mode on the phone** (Settings › Privacy & Security). Phones
  that took `./iphone.sh` installs have it.
- **An HTTPS host the phone can reach** (step 3).

## 2. Archive and export with development signing

On the Mac, in the nessa-ios checkout:

```sh
mkdir -p build
cat > build/DevExportOptions.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>method</key><string>debugging</string>
  <key>signingStyle</key><string>automatic</string>
</dict></plist>
PLIST
xcodebuild -project App/Nessa.xcodeproj -scheme Nessa -configuration Release \
  -destination generic/platform=iOS \
  -archivePath build/Nessa.xcarchive -allowProvisioningUpdates archive
xcodebuild -exportArchive -archivePath build/Nessa.xcarchive \
  -exportOptionsPlist build/DevExportOptions.plist -exportPath build/export \
  -allowProvisioningUpdates
```

`debugging` is the current name for a development
export; older Xcode wants `development`. Automatic signing with
`-allowProvisioningUpdates` makes a profile listing every registered phone,
so a newly registered phone needs a fresh build, not a fresh link. Raise
`CURRENT_PROJECT_VERSION` when you want the phone to see a new build number.

## 3. Choose where the phone downloads from

The phone needs HTTPS with a certificate it trusts. Pick by reach:

- **The Mac over Tailscale**, when the phone runs Tailscale on the same
  tailnet (see [connect-a-computer](../connect-a-computer/SKILL.md)). Nothing
  is public, and the `*.ts.net` certificate is real. Serve a folder through a
  local server, since the Mac App Store build of Tailscale cannot read
  files from disk itself:

  ```sh
  mkdir -p ~/nessa-ota
  nohup python3 -m http.server 8787 --bind 127.0.0.1 --directory ~/nessa-ota \
    > ~/nessa-ota.log 2>&1 &
  tailscale serve --bg --https=8443 http://127.0.0.1:8787
  ```

  The base URL is `https://<mac>.<tailnet>.ts.net:8443`. Port 8443 keeps
  this apart from anything already served on 443; `tailscale serve status`
  shows both. `nohup` keeps the server up after the session that started it
  ends, so the link still works when the person taps it later. Anyone on
  the tailnet can reach the port; the random folder name is what keeps one
  build's link from finding the others.
- **Any static HTTPS host or bucket** when the phone is not on the tailnet.
  Upload the folder step 4 writes to an unguessable path. A presigned link
  (S3, R2) signs each file on its own, so sign the `.ipa` first, write its
  link into the manifest, then sign the manifest; the script below does not
  do that.

Whatever the host: never one fixed "latest" path, send
`Cache-Control: no-store` where you control headers, and keep only the last
few builds.

## 4. Publish the build

```sh
python3 <skills>/skills/nessa/install-ios-over-the-air/scripts/ota_page.py \
  build/export/Nessa.ipa --base-url https://<mac>.<tailnet>.ts.net:8443 \
  --out ~/nessa-ota
```

It reads the bundle id, version and name out of the `.ipa`, writes
`index.html`, `manifest.plist` and the `.ipa` into a fresh random folder,
keeps the last five builds it made, and prints the page URL. It puts an
empty `index.html` at the folder's root so the server lists no builds. It escapes `&` in the
manifest and URL-encodes the manifest's URL inside the `itms-services` link;
missing either breaks the install. Before handing it over, run `curl -I` on
the page, the manifest and the `.ipa` URLs and expect `200` for each.

## 5. Install on the phone

The person opens the page **in Safari** on the phone and taps Install. The
app appears on the home screen with a progress ring. Give them the page URL,
not the `itms-services` link: other apps do not open it.

When it fails:

| What they see | Usually |
| --- | --- |
| Nothing happens on tap | Not Safari, or the manifest URL is not HTTPS or not reachable from the phone |
| "Unable to install" | The phone is not in the build's profile: register it and build again |
| "This provisioning profile cannot be installed on this device" | Stale profiles on the Mac: clear `~/Library/Developer/Xcode/UserData/Provisioning Profiles` and build again |
| App installs but will not open | Developer Mode is off, or the development certificate or profile expired (each lasts a year): build again |
| App opens to the demo chats | A Debug build: export Release |

## 6. Without the Mac: a CI Mac

To drop the Remote Control step, a macOS CI runner runs steps 2 and 4. It
needs, as secrets, what only the account holder can give: an App Store
Connect API key that can manage certificates and profiles (pass it with
`-authenticationKeyPath`, `-authenticationKeyID` and
`-authenticationKeyIssuerID` next to `-allowProvisioningUpdates`), and a
bucket or host the runner can upload to. macOS runner minutes cost more
than Linux ones.

At that point compare TestFlight. The same API key can upload the build;
internal testers install it from the TestFlight app with no device list
and no hosting. Over the air wins when the build must not go through App
Store Connect, or must land in seconds.
