"""Build a genuinely single-file, offline-capable copy of the game.

The game loads PixiJS from `vendor/` with relative <script src> tags, so
downloading `260703_Cellsnake.html` on its own gives you a page that renders the
menu and then dies with "PIXI is not defined" — no canvas, and Start does
nothing, because the script threw before `window.startRound` was ever assigned.

This script inlines both libraries and writes:

    dist/Cellular_Zatacka.html

That file is self-contained: one download, no folder, no network, works from
file://. It is what you hand to somebody who just wants to play.

    python3 tools/build_standalone.py           # build
    python3 tools/build_standalone.py --check    # is dist/ current? (exit 1 if not)

## Keeping it fresh

A stale standalone build is worse than none — it silently ships an old game.
The build stamps a hash of the three inputs into the output, and `--check`
compares. **Rebuild whenever you change 260703_Cellsnake.html or vendor/.**
"""

import argparse
import hashlib
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "260703_Cellsnake.html")
OUT_DIR = os.path.join(REPO, "dist")
OUT = os.path.join(OUT_DIR, "Cellular_Zatacka.html")
STAMP = "<!-- standalone-build-inputs: "

# Matches <script src="vendor/anything.js"></script>, tolerating attribute order
# and whitespace. Deliberately narrow: only vendor/ paths are inlined.
TAG = re.compile(r'<script\s+src="(vendor/[^"]+)"\s*>\s*</script>')


def inputs_hash(html, assets):
    h = hashlib.sha256()
    h.update(html.encode())
    for name in sorted(assets):
        h.update(name.encode())
        h.update(assets[name].encode())
    return h.hexdigest()[:16]


def build():
    html = open(SRC, encoding="utf-8").read()
    refs = TAG.findall(html)
    if not refs:
        print("ERROR: no <script src=\"vendor/...\"> tags found in the source. "
              "Either the game no longer vendors its libraries, or the tag "
              "format changed and this script's regex needs updating.")
        return None, None, None

    assets = {}
    for rel in refs:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            print(f"ERROR: {rel} referenced by the HTML but missing on disk.")
            return None, None, None
        assets[rel] = open(path, encoding="utf-8").read()

    stamp = inputs_hash(html, assets)

    def replace(m):
        rel = m.group(1)
        body = assets[rel]
        # A literal </script> inside the payload would close the tag early.
        # Neither vendored library contains one today; guard anyway rather than
        # produce a file that breaks in a way nobody would think to look for.
        body = body.replace("</script", "<\\/script")
        return (f"<!-- inlined from {rel} -->\n<script>\n{body}\n</script>")

    out = TAG.sub(replace, html)
    out = out.replace("<head>", f"<head>\n{STAMP}{stamp} -->", 1)
    if STAMP not in out:                      # no <head> to anchor to
        out = f"{STAMP}{stamp} -->\n" + out
    return out, stamp, refs


def current_stamp():
    if not os.path.exists(OUT):
        return None
    with open(OUT, encoding="utf-8") as fh:
        for _ in range(40):
            line = fh.readline()
            if not line:
                break
            if STAMP in line:
                return line.split(STAMP)[1].split()[0]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if dist/ is missing or stale; build nothing")
    a = ap.parse_args()

    out, stamp, refs = build()
    if out is None:
        return 2

    if a.check:
        have = current_stamp()
        if have == stamp:
            print(f"dist/ is current ({stamp})")
            return 0
        print(f"dist/ is STALE — built from {have}, sources are now {stamp}. "
              f"Run: python3 tools/build_standalone.py")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    size = os.path.getsize(OUT) / 1024
    print(f"wrote {os.path.relpath(OUT, REPO)}  ({size:.0f} KB, stamp {stamp})")
    print(f"  inlined: {', '.join(refs)}")
    print("  self-contained: no folder, no network, runs from file://")
    return 0


if __name__ == "__main__":
    sys.exit(main())
