#!/usr/bin/env python3
"""Publish one signed .ipa as an over-the-air install page.

Writes <out>/<random id>/{index.html, manifest.plist, <App>.ipa} and prints the
page URL and the itms-services link. Serve <out> over HTTPS with a real
certificate at --base-url. Standard library only, so the Mac's python3 runs it.

Usage: ota_page.py IPA --base-url https://host/path --out DIR [--keep 5]
"""
import argparse
import re
import html
import plistlib
import secrets
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote


BUILD_ID = re.compile(r"[A-Za-z0-9_-]{22}")  # what secrets.token_urlsafe(16) makes


def app_info(ipa: Path) -> dict:
    """Read the app's own Info.plist out of the .ipa (Payload/<Name>.app/)."""
    if not ipa.is_file():
        sys.exit(f"no such file: {ipa}")
    if not zipfile.is_zipfile(ipa):
        sys.exit(f"not an .ipa (zip) file: {ipa}")
    with zipfile.ZipFile(ipa) as z:
        names = [
            n for n in z.namelist()
            if n.startswith("Payload/") and n.count("/") == 2
            and n.split("/")[1].endswith(".app") and n.endswith("/Info.plist")
        ]
        if len(names) != 1:
            sys.exit(f"expected one Payload/*.app/Info.plist in {ipa}, found {len(names)}")
        info = plistlib.loads(z.read(names[0]))
    if not info.get("CFBundleIdentifier"):
        sys.exit(f"{names[0]} has no CFBundleIdentifier")
    return info


def manifest(ipa_url: str, info: dict) -> bytes:
    # plistlib escapes '&' in a presigned URL as &amp;, which iOS needs.
    return plistlib.dumps({
        "items": [{
            "assets": [{"kind": "software-package", "url": ipa_url}],
            "metadata": {
                "bundle-identifier": info["CFBundleIdentifier"],
                "bundle-version": info.get("CFBundleShortVersionString", "0"),
                "kind": "software",
                "title": info.get("CFBundleDisplayName") or info.get("CFBundleName", "App"),
            },
        }]
    })


def page(title: str, version: str, build: str, link: str) -> str:
    t, v, b, l = (html.escape(s, quote=True) for s in (title, version, build, link))
    return f"""<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Install {t}</title>
<style>body{{font:17px -apple-system,system-ui;margin:3em 1.5em;text-align:center}}
a{{display:inline-block;padding:.8em 1.6em;border-radius:12px;background:#0a84ff;color:#fff;text-decoration:none}}
p{{color:#888}}</style>
<h1>{t}</h1><p>Version {v} ({b})</p>
<a href="{l}">Install</a>
<p>Open this page in Safari on a registered iPhone.</p>
"""


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("ipa", type=Path)
    p.add_argument("--base-url", required=True, help="HTTPS URL that serves --out")
    p.add_argument("--out", required=True, type=Path, help="folder to publish; builds this script made there beyond --keep are deleted")
    p.add_argument("--keep", type=int, default=5, help="builds to keep (default 5)")
    a = p.parse_args()
    if not a.base_url.startswith("https://"):
        sys.exit("--base-url must be https://: iOS refuses to install over plain HTTP")
    if "?" in a.base_url or "#" in a.base_url:
        sys.exit("--base-url is a plain folder URL; presigned links are signed per file, not by this script")
    if a.keep < 1:
        sys.exit("--keep must be at least 1")

    info = app_info(a.ipa)
    # An empty page at the root, so a static server lists no build folders:
    # the unguessable folder name is the only permission a link carries.
    # Written before any build folder exists, so a first publish lists none.
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "index.html").write_text("")
    build_id = secrets.token_urlsafe(16)  # unguessable; never a fixed "latest"
    folder = a.out / build_id
    folder.mkdir(parents=True)
    ipa_name = quote(a.ipa.name)
    base = f"{a.base_url.rstrip('/')}/{build_id}"
    shutil.copyfile(a.ipa, folder / a.ipa.name)
    (folder / "manifest.plist").write_bytes(manifest(f"{base}/{ipa_name}", info))
    link = "itms-services://?action=download-manifest&url=" + quote(f"{base}/manifest.plist", safe="")
    title = info.get("CFBundleDisplayName") or info.get("CFBundleName", "App")
    (folder / "index.html").write_text(page(
        title, info.get("CFBundleShortVersionString", "?"), info.get("CFBundleVersion", "?"), link))

    # Prune only folders this script made.
    builds = sorted(
        (d for d in a.out.iterdir()
         if d.is_dir() and BUILD_ID.fullmatch(d.name) and (d / "manifest.plist").is_file()),
        key=lambda d: d.stat().st_mtime)
    for old in builds[:-a.keep]:
        shutil.rmtree(old)

    print(f"page: {base}/")
    print(f"link: {link}")


if __name__ == "__main__":
    main()
