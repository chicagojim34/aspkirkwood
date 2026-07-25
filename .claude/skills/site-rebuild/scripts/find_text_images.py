#!/usr/bin/env python3
"""
find_text_images.py — Flag images that are probably pictures of text.

Legacy site builders (iWeb, FrontPage, Flash exporters) rendered headings and
whole paragraphs as image files. That text is invisible to search engines,
screen readers, and to the crawler's content inventory — so the coverage check
cannot notice when it goes missing, because it was never text to begin with.

This script does not read the images. It ranks them so you know which ones to
open and transcribe yourself: read each high-scoring file, decide whether it
carries real content (a heading, a paragraph, a price list) or is merely
decorative (a logo, a wordmark, a "Live Laugh Love" flourish), and write the
content ones into transcriptions.json. Feed that file back into
check_coverage.py so the transcribed text becomes part of the preservation
contract like any other block.

Signals used (no dependencies — dimensions are parsed from file headers):
  - Format: flat text renders are almost always PNG/GIF; photos are JPEG.
  - Bytes per pixel: text and flat graphics compress extremely well (< ~0.5
    bpp). Photographic PNGs land far higher. This is the strongest signal.
  - Aspect ratio: headings and text banners are wide and short.
  - Filename: shapeimage_N, text_N, heading_, title_, banner_ are tells.

Usage:
    python3 find_text_images.py --capture capture/ [--out transcriptions.json]
    python3 find_text_images.py --dir assets/images/ --min-score 3
"""

import argparse
import json
import os
import re
import struct
import sys

TEXTY_NAME = re.compile(
    r"(shapeimage|text[_-]?\d|heading|title|banner|headline|caption|words|type|"
    r"welcome|about[_-]?us|menu|hours|price)", re.I
)
DECOR_NAME = re.compile(r"(logo|icon|favicon|bullet|arrow|button|btn|divider|rule|bg|background)", re.I)


def png_size(fh):
    fh.seek(16)
    return struct.unpack(">II", fh.read(8))


def gif_size(fh):
    fh.seek(6)
    return struct.unpack("<HH", fh.read(4))


def jpeg_size(fh):
    fh.seek(2)
    while True:
        b = fh.read(1)
        if not b:
            raise ValueError("no SOF")
        if b != b"\xff":
            continue
        marker = fh.read(1)
        while marker == b"\xff":
            marker = fh.read(1)
        if marker in b"\xc0\xc1\xc2\xc3\xc5\xc6\xc7\xc9\xca\xcb\xcd\xce\xcf":
            fh.read(3)
            h, w = struct.unpack(">HH", fh.read(4))
            return w, h
        seg = fh.read(2)
        if len(seg) < 2:
            raise ValueError("truncated")
        fh.seek(struct.unpack(">H", seg)[0] - 2, os.SEEK_CUR)


def webp_size(fh):
    fh.seek(12)
    tag = fh.read(4)
    if tag == b"VP8X":
        fh.seek(24)
        d = fh.read(6)
        w = 1 + int.from_bytes(d[0:3], "little")
        h = 1 + int.from_bytes(d[3:6], "little")
        return w, h
    if tag == b"VP8 ":
        fh.seek(26)
        w, h = struct.unpack("<HH", fh.read(4))
        return w & 0x3FFF, h & 0x3FFF
    if tag == b"VP8L":
        fh.seek(21)
        b = int.from_bytes(fh.read(4), "little")
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    raise ValueError("unknown webp")


def dimensions(path):
    with open(path, "rb") as fh:
        head = fh.read(12)
        try:
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return png_size(fh) + ("png",)
            if head[:3] == b"GIF":
                return gif_size(fh) + ("gif",)
            if head[:2] == b"\xff\xd8":
                return jpeg_size(fh) + ("jpeg",)
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                return webp_size(fh) + ("webp",)
        except Exception:
            return None
    return None


def score_image(path):
    """Higher score = more likely to be text rendered as an image."""
    info = dimensions(path)
    if not info:
        return None
    w, h, fmt = info
    if w < 8 or h < 8:
        return None
    size = os.path.getsize(path)
    bpp = size / float(w * h)
    name = os.path.basename(path)
    aspect = w / float(h)

    score = 0
    reasons = []

    if fmt in ("png", "gif"):
        score += 2
        reasons.append(f"{fmt} (flat-graphic format)")
    if bpp < 0.25:
        score += 3
        reasons.append(f"{bpp:.2f} bytes/px (very flat)")
    elif bpp < 0.6:
        score += 2
        reasons.append(f"{bpp:.2f} bytes/px (flat)")
    elif bpp < 1.2:
        score += 1
        reasons.append(f"{bpp:.2f} bytes/px")
    if aspect > 3:
        score += 2
        reasons.append(f"wide banner {w}x{h}")
    elif aspect > 1.8 and h < 300:
        score += 1
        reasons.append(f"short and wide {w}x{h}")
    if TEXTY_NAME.search(name):
        score += 2
        reasons.append("filename suggests text")
    if DECOR_NAME.search(name):
        score -= 2
        reasons.append("filename suggests decoration")
    if h < 60 and w > 200:
        score += 1
        reasons.append("thin strip (heading-shaped)")

    return {
        "file": path,
        "width": w,
        "height": h,
        "format": fmt,
        "bytes": size,
        "bytes_per_pixel": round(bpp, 3),
        "score": score,
        "reasons": reasons,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--capture", help="crawl output directory (scans <capture>/images)")
    src.add_argument("--dir", help="any directory of images")
    ap.add_argument("--out", default="transcriptions.json")
    ap.add_argument("--min-score", type=int, default=3)
    args = ap.parse_args()

    root = os.path.join(args.capture, "images") if args.capture else args.dir
    if not os.path.isdir(root):
        print(f"No such directory: {root}", file=sys.stderr)
        return 1

    results = []
    for dirpath, _, files in os.walk(root):
        for name in sorted(files):
            if not name.lower().endswith((".png", ".gif", ".jpg", ".jpeg", ".webp")):
                continue
            r = score_image(os.path.join(dirpath, name))
            if r:
                results.append(r)

    results.sort(key=lambda r: (-r["score"], -r["bytes"]))
    flagged = [r for r in results if r["score"] >= args.min_score]

    print(f"Scanned {len(results)} images; {len(flagged)} scored >= {args.min_score}\n")
    print(f"{'score':>5}  {'size':>11}  {'bpp':>6}  file")
    print("-" * 78)
    for r in flagged:
        print(
            f"{r['score']:>5}  {r['width']:>5}x{r['height']:<5}  "
            f"{r['bytes_per_pixel']:>6}  {os.path.relpath(r['file'], root)}"
        )
        print(f"{'':>5}  {' · '.join(r['reasons'])}")

    template = {
        "_instructions": (
            "Open each file below with the Read tool and look at it. If it shows real "
            "content (heading, paragraph, prices, hours), put that text in \"text\" exactly "
            "as written and set \"kind\" to \"content\". If it is decorative (logo, "
            "wordmark, a stylistic flourish), leave \"text\" empty and set \"kind\" to "
            "\"decorative\". Then pass this file to check_coverage.py --transcriptions so "
            "the content entries are enforced like any other source text."
        ),
        "images": [
            {
                "file": r["file"],
                "dimensions": f"{r['width']}x{r['height']}",
                "score": r["score"],
                "kind": "",
                "text": "",
            }
            for r in flagged
        ],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(template, fh, indent=2, ensure_ascii=False)

    print(f"\nWrote {args.out} with {len(flagged)} entries to review.")
    print("Read each flagged image, then fill in \"kind\" and \"text\".")
    if not flagged:
        print("Nothing flagged — but skim a few PNGs by hand anyway if the site looks pre-2010.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
