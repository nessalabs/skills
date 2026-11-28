#!/usr/bin/env bash
# Screenshot a rendered artifact with a headless Chrome or Chromium.
#   screenshot.sh page.html page.png [light|dark]
# Grows the window (8000, 16000, then 32000 px) until the page's content ends
# above the bottom edge, then crops the empty space. Warns if the page is
# still cut off at the largest size. Waits up to 15 s for the diagram script.
# Needs Python with Pillow to measure; without it, one 8000 px shot is taken
# and the cut-off check is skipped (a warning says so).
set -euo pipefail
in=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
out=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
scheme=${3:-light}
blink=1; [ "$scheme" = dark ] && blink=0
browser=""
for b in google-chrome google-chrome-stable chromium chromium-browser \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if command -v "$b" >/dev/null 2>&1 || [ -x "$b" ]; then browser=$b; break; fi
done
if [ -z "$browser" ]; then
  echo "no Chrome or Chromium found; open $1 in a browser and check it by eye" >&2
  exit 2
fi
if ! python3 -c "import PIL" 2>/dev/null; then
  "$browser" --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
    --force-prefers-color-scheme="$scheme" --blink-settings=preferredColorScheme=$blink \
    --window-size=1100,8000 --virtual-time-budget=15000 --screenshot="$out" "file://$in" 2>/dev/null
  echo "warning: Pillow not installed, so the page height was not measured; a page taller than 8000 px is cut off" >&2
  echo "wrote $out"
  exit 0
fi
for height in 8000 16000 32000; do
  "$browser" --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
    --force-prefers-color-scheme="$scheme" --blink-settings=preferredColorScheme=$blink \
    --window-size=1100,$height --virtual-time-budget=15000 --screenshot="$out" "file://$in" 2>/dev/null
  # Exit 0: the content ends above the bottom edge (cropped and done).
  # Exit 3: the content reaches the bottom edge, so the page may be cut off.
  set +e
  python3 - "$out" <<'PY'
import sys
from PIL import Image, ImageChops
p = sys.argv[1]
im = Image.open(p).convert("RGB")
bg = Image.new("RGB", im.size, im.getpixel((5, 5)))
box = ImageChops.difference(im, bg).getbbox()
if box and box[3] >= im.height - 8:
    sys.exit(3)
if box:
    im.crop((0, 0, im.width, min(im.height, box[3] + 60))).save(p)
PY
  status=$?
  set -e
  if [ $status -eq 0 ]; then echo "wrote $out"; exit 0; fi
  if [ $status -ne 3 ]; then echo "error: could not measure $out" >&2; exit 1; fi
done
echo "warning: the page is taller than 32000 px; $out is cut off at the bottom" >&2
echo "wrote $out"
