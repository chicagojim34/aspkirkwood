#!/usr/bin/env python3
"""
bundle_singlefile.py — Flatten a built page into one portable HTML file.

Most website builders (Wix, Squarespace, GoDaddy, HubSpot landing pages) will
import a single self-contained HTML file but choke on a folder of linked
assets. Prospects also forward "the mockup" by email, where a lone .html has to
survive on its own. This inlines local CSS, JS, images and the favicon as
data URIs while leaving remote resources (web fonts, maps) alone.

Usage:
    python3 bundle_singlefile.py index.html --out bundle/index.html [options]

Options:
    --base DIR          Root for resolving relative paths (default: page's dir)
    --max-image-kb N    Images above this stay as links instead of data URIs
                        (default 400; set 0 to inline everything)
    --asset-base URL    Absolute URL prefix for images that were not inlined,
                        e.g. https://user.github.io/site/ — required if any
                        image exceeds --max-image-kb, or the bundle breaks
"""

import argparse
import base64
import mimetypes
import os
import re
import sys
from urllib.parse import urljoin

mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/avif", ".avif")


def is_remote(url):
    return url.startswith(("http://", "https://", "//", "data:", "mailto:", "tel:", "#"))


def data_uri(path):
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "application/octet-stream"
    with open(path, "rb") as fh:
        payload = base64.b64encode(fh.read()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--out", required=True)
    ap.add_argument("--base")
    ap.add_argument("--max-image-kb", type=int, default=400)
    ap.add_argument("--asset-base", default="")
    args = ap.parse_args()

    base = args.base or os.path.dirname(os.path.abspath(args.page)) or "."
    with open(args.page, encoding="utf-8") as fh:
        html = fh.read()

    stats = {"css": 0, "js": 0, "img_inlined": 0, "img_linked": 0, "missing": []}

    def local_path(url):
        clean = url.split("?")[0].split("#")[0]
        return os.path.normpath(os.path.join(base, clean))

    # --- stylesheets -> <style> ---------------------------------------
    def repl_css(m):
        tag = m.group(0)
        if not re.search(r'rel=["\']?stylesheet', tag, re.I):
            return tag
        href_m = re.search(r'href=["\']([^"\']+)["\']', tag, re.I)
        if not href_m:
            return tag
        href = href_m.group(1)
        if is_remote(href):
            return tag
        path = local_path(href)
        if not os.path.exists(path):
            stats["missing"].append(href)
            return tag
        with open(path, encoding="utf-8") as fh:
            css = fh.read()
        css_dir = os.path.dirname(path)

        def repl_css_url(um):
            u = um.group(2)
            if is_remote(u):
                return um.group(0)
            p = os.path.normpath(os.path.join(css_dir, u.split("?")[0]))
            if not os.path.exists(p):
                return um.group(0)
            return f"url({data_uri(p)})"

        css = re.sub(r"url\((['\"]?)(.*?)\1\)", repl_css_url, css)
        stats["css"] += 1
        return f"<style>\n{css}\n</style>"

    html = re.sub(r"<link\b[^>]*>", repl_css, html, flags=re.I)

    # --- scripts -> inline --------------------------------------------
    def repl_js(m):
        src = m.group(1)
        if is_remote(src):
            return m.group(0)
        path = local_path(src)
        if not os.path.exists(path):
            stats["missing"].append(src)
            return m.group(0)
        with open(path, encoding="utf-8") as fh:
            js = fh.read()
        stats["js"] += 1
        return f"<script>\n{js}\n</script>"

    html = re.sub(r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>\s*</script>', repl_js, html, flags=re.I)

    # --- images / favicon -> data URIs --------------------------------
    limit = args.max_image_kb * 1024

    def repl_attr(m):
        prefix, url, suffix = m.group(1), m.group(2), m.group(3)
        if is_remote(url):
            return m.group(0)
        path = local_path(url)
        if not os.path.exists(path):
            stats["missing"].append(url)
            return m.group(0)
        size = os.path.getsize(path)
        if limit and size > limit:
            stats["img_linked"] += 1
            if args.asset_base:
                return f"{prefix}{urljoin(args.asset_base, url)}{suffix}"
            return m.group(0)
        stats["img_inlined"] += 1
        return f"{prefix}{data_uri(path)}{suffix}"

    html = re.sub(
        r'(<img[^>]*\ssrc=["\'])([^"\']+)(["\'])',
        repl_attr,
        html,
        flags=re.I,
    )
    html = re.sub(
        r'(<link[^>]*rel=["\'][^"\']*icon[^"\']*["\'][^>]*href=["\'])([^"\']+)(["\'])',
        repl_attr,
        html,
        flags=re.I,
    )
    html = re.sub(
        r'(style=["\'][^"\']*url\()([^"\')]+)(\))',
        repl_attr,
        html,
        flags=re.I,
    )
    # srcset would multiply the payload; a single src is enough in a bundle.
    html = re.sub(r'\ssrcset=["\'][^"\']*["\']', "", html, flags=re.I)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)

    kb = os.path.getsize(args.out) / 1024
    print(f"Wrote {args.out} — {kb:.0f} KB")
    print(f"  inlined: {stats['css']} stylesheet(s), {stats['js']} script(s), {stats['img_inlined']} image(s)")
    if stats["img_linked"]:
        where = args.asset_base or "ORIGINAL RELATIVE PATHS (will break!)"
        print(f"  left as links: {stats['img_linked']} image(s) over {args.max_image_kb} KB -> {where}")
    if stats["missing"]:
        print(f"  WARNING: {len(stats['missing'])} asset(s) not found: {', '.join(sorted(set(stats['missing']))[:8])}")
    if kb > 2000:
        print("  NOTE: over 2 MB. Compress images or lower --max-image-kb before importing into a site builder.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
