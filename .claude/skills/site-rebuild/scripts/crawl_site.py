#!/usr/bin/env python3
"""
crawl_site.py — Capture everything a prospect's current website contains.

This is the evidence-gathering step of a site rebuild. It walks the site,
saves raw HTML, downloads every image it can find, and writes a structured
inventory of every visible text block. The inventory is what later lets you
prove that no content was silently dropped in the rebuild.

Stdlib only, except `requests` (falls back to urllib if unavailable).

Usage:
    python3 crawl_site.py https://example.com --out capture/ [options]

Options:
    --max-pages N     Stop after N pages (default 40)
    --depth N         Max link depth from the start URL (default 3)
    --delay SECONDS   Politeness delay between requests (default 0.5)
    --no-images       Skip image downloads (text inventory only)
    --include-pdf     Also download linked PDFs

Outputs (under --out):
    raw/<slug>.html            verbatim HTML of each page
    images/<slug>/<file>       every image referenced by that page
    inventory.json             machine-readable content inventory
    content.md                 human-readable dump, page by page
    crawl_report.md            what was found, what failed, what to check
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import OrderedDict
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, unquote

try:
    import requests

    _SESSION = requests.Session()
    _SESSION.headers.update(
        {"User-Agent": "Mozilla/5.0 (compatible; SiteRebuildBot/1.0; +site-audit)"}
    )

    def fetch(url, timeout=30):
        r = _SESSION.get(url, timeout=timeout)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        return r.content, ctype

except ImportError:  # pragma: no cover - fallback path
    from urllib.request import Request, urlopen

    def fetch(url, timeout=30):
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (SiteRebuildBot/1.0)"})
        with urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.headers.get("Content-Type", "")


# Blocks whose text is structural noise rather than content.
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg", "head"}

# Tags whose text we record as discrete content blocks.
BLOCK_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "li", "td", "th", "dt", "dd",
    "blockquote", "figcaption", "caption", "label", "summary",
    "a", "span", "div", "strong", "em", "b",
}

IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif", ".bmp", ".tif", ".tiff")


def slugify(value, fallback="page"):
    value = unquote(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:80] or fallback


def url_to_slug(url, base):
    path = urlparse(url).path
    if path in ("", "/"):
        return "index"
    path = re.sub(r"\.(html?|php|aspx?|jsp)$", "", path, flags=re.I)
    return slugify(path)


def norm_ws(text):
    return re.sub(r"\s+", " ", text or "").strip()


class PageParser(HTMLParser):
    """Extracts text blocks, links, images and metadata from one page."""

    def __init__(self, page_url):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.stack = []
        self.buffers = {}          # id(frame) -> accumulated text
        self.blocks = []           # ordered content blocks
        self.links = []            # (href, anchor_text)
        self.images = OrderedDict()  # absolute url -> alt text
        self.title = ""
        self.meta_description = ""
        self._in_title = False
        self._frame_id = 0
        self._seen_block_text = set()

    # -- helpers -------------------------------------------------------
    def _abs(self, url):
        if not url:
            return None
        url = url.strip()
        if url.startswith(("data:", "javascript:", "#")):
            return None
        return urljoin(self.page_url, url)

    def _record_image(self, url, alt=""):
        absu = self._abs(url)
        if not absu:
            return
        # Ignore obvious tracking pixels / spacers by filename hint.
        if re.search(r"(spacer|pixel|blank|1x1)\.(gif|png)$", absu, re.I):
            return
        if absu not in self.images or (alt and not self.images[absu]):
            self.images[absu] = norm_ws(alt)

    def _harvest_srcset(self, value):
        for candidate in (value or "").split(","):
            url = candidate.strip().split(" ")[0]
            if url:
                self._record_image(url)

    def _harvest_style(self, value):
        for match in re.finditer(r"url\((['\"]?)(.*?)\1\)", value or "", re.I):
            url = match.group(2)
            if url.lower().endswith(IMG_EXT) or "/" in url:
                self._record_image(url)

    # -- HTMLParser API ------------------------------------------------
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = {k.lower(): (v or "") for k, v in attrs}

        if tag == "title":
            self._in_title = True
        if tag == "meta":
            if a.get("name", "").lower() == "description":
                self.meta_description = norm_ws(a.get("content", ""))
            if a.get("property", "").lower() in ("og:image", "twitter:image"):
                self._record_image(a.get("content", ""))

        if tag == "img":
            self._record_image(a.get("src") or a.get("data-src"), a.get("alt", ""))
            self._harvest_srcset(a.get("srcset") or a.get("data-srcset"))
        if tag == "source":
            self._harvest_srcset(a.get("srcset"))
        if tag in ("video", "embed", "object"):
            self._record_image(a.get("poster"))
        if a.get("style"):
            self._harvest_style(a["style"])

        if tag == "a" and a.get("href"):
            self.links.append([self._abs(a["href"]) or a["href"], ""])

        self._frame_id += 1
        frame = (tag, self._frame_id, len(self.links) - 1 if tag == "a" else None)
        self.stack.append(frame)
        if tag in BLOCK_TAGS:
            self.buffers[self._frame_id] = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._in_title and tag == "title":
            self._in_title = False
        # Unwind to the matching open tag (tolerates unclosed markup).
        for idx in range(len(self.stack) - 1, -1, -1):
            if self.stack[idx][0] == tag:
                for frame in self.stack[idx:]:
                    self._close_frame(frame)
                del self.stack[idx:]
                return

    def _close_frame(self, frame):
        tag, fid, link_idx = frame
        parts = self.buffers.pop(fid, None)
        if parts is None:
            return
        text = norm_ws("".join(parts))
        if tag == "a" and link_idx is not None and 0 <= link_idx < len(self.links):
            self.links[link_idx][1] = text
        if not text:
            return
        # Generic containers only count when they hold text no child block claimed.
        if tag in ("div", "span", "strong", "em", "b", "a") and len(text) < 3:
            return
        key = (tag, text.lower())
        if key in self._seen_block_text:
            return
        self._seen_block_text.add(key)
        self.blocks.append({"tag": tag, "text": text, "chars": len(text)})

    def handle_data(self, data):
        if self._in_title:
            self.title = norm_ws(self.title + " " + data)
        if not self.stack:
            return
        if any(t in SKIP_TEXT_TAGS for t, _, _ in self.stack):
            return
        for _, fid, _ in self.stack:
            if fid in self.buffers:
                self.buffers[fid].append(data)

    def close(self):
        super().close()
        for frame in reversed(self.stack):
            self._close_frame(frame)
        self.stack = []


def dedupe_nested_blocks(blocks):
    """Drop container blocks whose text is just the concatenation of children.

    A <div> wrapping three <p>s otherwise shows up as a fourth, redundant block,
    which inflates the inventory and makes coverage checking noisy.
    """
    kept = []
    texts = [b["text"] for b in blocks]
    for i, b in enumerate(blocks):
        if b["tag"] not in ("div", "span", "li", "td"):
            kept.append(b)
            continue
        others = " ".join(t for j, t in enumerate(texts) if j != i and len(t) > 25)
        if len(b["text"]) > 60 and b["text"] in others:
            continue
        kept.append(b)
    return kept


def download(url, dest_dir, seen_hashes):
    os.makedirs(dest_dir, exist_ok=True)
    name = os.path.basename(urlparse(url).path) or "image"
    name = unquote(name)
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name)[:100]
    if not name.lower().endswith(IMG_EXT):
        name += ".jpg"
    path = os.path.join(dest_dir, name)
    n = 1
    while os.path.exists(path):
        stem, ext = os.path.splitext(name)
        path = os.path.join(dest_dir, f"{stem}-{n}{ext}")
        n += 1
    data, _ = fetch(url)
    if len(data) < 512:  # spacer gifs and broken responses
        return None, None, len(data)
    digest = hashlib.sha1(data).hexdigest()
    with open(path, "wb") as fh:
        fh.write(data)
    seen_hashes.setdefault(digest, path)
    return path, digest, len(data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", default="capture")
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--include-pdf", action="store_true")
    args = ap.parse_args()

    start = args.url if "://" in args.url else "https://" + args.url
    host = urlparse(start).netloc
    root_host = host[4:] if host.startswith("www.") else host

    out = args.out
    os.makedirs(os.path.join(out, "raw"), exist_ok=True)

    queue = [(start, 0)]
    visited = OrderedDict()
    failures = []
    external_links = OrderedDict()
    docs = []
    image_hashes = {}

    while queue and len(visited) < args.max_pages:
        url, depth = queue.pop(0)
        clean = url.split("#")[0].rstrip("/") or url
        if clean in visited:
            continue
        try:
            body, ctype = fetch(clean)
        except Exception as exc:
            failures.append({"url": clean, "error": str(exc)})
            continue
        if "html" not in ctype.lower() and not clean.lower().endswith((".html", ".htm", "/")):
            continue

        html = body.decode("utf-8", errors="replace")
        slug = url_to_slug(clean, start)
        if slug in [v["slug"] for v in visited.values()]:
            slug = f"{slug}-{len(visited)}"

        parser = PageParser(clean)
        try:
            parser.feed(html)
            parser.close()
        except Exception as exc:
            failures.append({"url": clean, "error": f"parse: {exc}"})

        with open(os.path.join(out, "raw", slug + ".html"), "w", encoding="utf-8") as fh:
            fh.write(html)

        blocks = dedupe_nested_blocks(parser.blocks)

        images = []
        if not args.no_images:
            img_dir = os.path.join(out, "images", slug)
            for img_url, alt in parser.images.items():
                try:
                    path, digest, size = download(img_url, img_dir, image_hashes)
                except Exception as exc:
                    failures.append({"url": img_url, "error": str(exc)})
                    continue
                if not path:
                    continue
                images.append(
                    {
                        "source_url": img_url,
                        "file": os.path.relpath(path, out),
                        "alt": alt,
                        "sha1": digest,
                        "bytes": size,
                        "duplicate_of": None
                        if image_hashes.get(digest) == path
                        else os.path.relpath(image_hashes[digest], out),
                    }
                )
                time.sleep(args.delay * 0.2)

        page_links = []
        for href, anchor in parser.links:
            if not href or "://" not in href:
                continue
            netloc = urlparse(href).netloc
            netloc_root = netloc[4:] if netloc.startswith("www.") else netloc
            target = href.split("#")[0].rstrip("/") or href
            if netloc_root == root_host:
                page_links.append(target)
                if depth < args.depth and target not in visited:
                    if re.search(r"\.(pdf|docx?|xlsx?|zip)$", target, re.I):
                        if args.include_pdf:
                            docs.append(target)
                        continue
                    queue.append((target, depth + 1))
            elif href.startswith(("mailto:", "tel:")):
                external_links.setdefault(href, anchor)
            else:
                external_links.setdefault(target, anchor)

        visited[clean] = {
            "url": clean,
            "slug": slug,
            "depth": depth,
            "title": parser.title,
            "meta_description": parser.meta_description,
            "blocks": blocks,
            "text_chars": sum(b["chars"] for b in blocks),
            "images": images,
            "internal_links": sorted(set(page_links)),
        }
        print(f"  [{len(visited):>2}] {slug:<28} {len(blocks):>3} blocks, {len(images):>3} images  {clean}")
        time.sleep(args.delay)

    contacts = {
        "emails": sorted({u[7:] for u in external_links if u.startswith("mailto:")}),
        "phones": sorted({u[4:] for u in external_links if u.startswith("tel:")}),
    }

    inventory = {
        "source_url": start,
        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "page_count": len(visited),
        "pages": list(visited.values()),
        "contacts": contacts,
        "external_links": [
            {"url": u, "anchor": a}
            for u, a in external_links.items()
            if not u.startswith(("mailto:", "tel:"))
        ],
        "documents": docs,
        "failures": failures,
    }

    with open(os.path.join(out, "inventory.json"), "w", encoding="utf-8") as fh:
        json.dump(inventory, fh, indent=2, ensure_ascii=False)

    # Human-readable dump — this is what you actually read while rebuilding.
    with open(os.path.join(out, "content.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# Content capture — {start}\n\nCrawled {inventory['crawled_at']}\n\n")
        for page in visited.values():
            fh.write(f"\n---\n\n## {page['title'] or page['slug']}\n\n")
            fh.write(f"`{page['url']}` · slug `{page['slug']}`\n\n")
            if page["meta_description"]:
                fh.write(f"> meta: {page['meta_description']}\n\n")
            for b in page["blocks"]:
                fh.write(f"- **[{b['tag']}]** {b['text']}\n")
            if page["images"]:
                fh.write("\n**Images**\n\n")
                for im in page["images"]:
                    dup = f" (dupe of {im['duplicate_of']})" if im["duplicate_of"] else ""
                    fh.write(f"- `{im['file']}` — alt: {im['alt'] or '(none)'}{dup}\n")

    total_imgs = sum(len(p["images"]) for p in visited.values())
    uniq_imgs = len(image_hashes)
    total_blocks = sum(len(p["blocks"]) for p in visited.values())

    with open(os.path.join(out, "crawl_report.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# Crawl report — {start}\n\n")
        fh.write(f"- Pages captured: **{len(visited)}**\n")
        fh.write(f"- Content blocks: **{total_blocks}**\n")
        fh.write(f"- Images downloaded: **{total_imgs}** ({uniq_imgs} unique by content hash)\n")
        fh.write(f"- Emails found: {', '.join(contacts['emails']) or 'none'}\n")
        fh.write(f"- Phones found: {', '.join(contacts['phones']) or 'none'}\n")
        if inventory["external_links"]:
            fh.write("\n## Outbound links (check for booking/registration systems)\n\n")
            for link in inventory["external_links"][:60]:
                fh.write(f"- {link['anchor'] or '(no text)'} → {link['url']}\n")
        if failures:
            fh.write("\n## Failures — fetch these by hand if they matter\n\n")
            for f in failures:
                fh.write(f"- {f['url']}: {f['error']}\n")

    print(
        f"\nCaptured {len(visited)} pages, {total_blocks} content blocks, "
        f"{total_imgs} images ({uniq_imgs} unique) -> {out}/"
    )
    if failures:
        print(f"WARNING: {len(failures)} fetch/parse failures — see {out}/crawl_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
