#!/usr/bin/env python3
"""
check_coverage.py — Prove the rebuild kept the prospect's content.

Compares the crawl inventory against the site you built. Every source text
block must appear in the new site (verbatim, or as a close paraphrase), and
every source image must be present by content hash. Anything you deliberately
dropped has to be declared in an omissions file, with a reason.

The point is not to be pedantic. It's that a rebuild pitch dies the moment a
prospect finds their staff bios or their grandfather's photo missing, and that
is very easy to do by accident across a 40-page site.

Usage:
    python3 check_coverage.py --capture capture/ --site . [options]

Options:
    --omissions FILE   JSON list of intentionally dropped items (see below)
    --min-chars N      Ignore source blocks shorter than N chars (default 25)
    --threshold F      Word-overlap ratio counted as a match (default 0.72)
    --report FILE      Write markdown report here (default coverage_report.md)
    --fail-under F     Exit 1 if text coverage falls below this (default 0.97)

omissions.json format:
    {
      "text": [{"match": "substring or full block", "reason": "duplicate nav label"}],
      "images": [{"file": "images/home/spacer.gif", "reason": "layout spacer"}]
    }
"""

import argparse
import hashlib
import json
import os
import re
import sys

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "at", "is",
    "are", "was", "were", "be", "with", "as", "by", "that", "this", "it", "from",
    "we", "our", "you", "your", "will", "have", "has", "not", "but", "all", "can",
}

TEXT_EXT = (".html", ".htm", ".md", ".js", ".json", ".css", ".txt", ".xml", ".svg")
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif", ".bmp")
SKIP_DIRS = {".git", "node_modules", ".claude", "capture", "__pycache__", ".github"}


def normalize(text):
    text = re.sub(r"&[a-z]+;|&#\d+;", " ", text or "", flags=re.I)
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def content_words(text):
    return [w for w in normalize(text).split() if w not in STOPWORDS and len(w) > 2]


def collect_site(site_dir):
    """Return (normalized text corpus, {sha1: [paths]}, {referenced asset names})."""
    corpus_parts = []
    hashes = {}
    referenced = set()
    raw_html = []

    for root, dirs, files in os.walk(site_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, site_dir)
            low = name.lower()
            if low.endswith(IMG_EXT):
                with open(path, "rb") as fh:
                    digest = hashlib.sha1(fh.read()).hexdigest()
                hashes.setdefault(digest, []).append(rel)
                if low.endswith(".svg"):
                    continue
            if low.endswith(TEXT_EXT):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                except OSError:
                    continue
                if low.endswith((".html", ".htm", ".md")):
                    raw_html.append(text)
                    stripped = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
                    stripped = re.sub(r"<[^>]+>", " ", stripped)
                    corpus_parts.append(stripped)
                for m in re.finditer(r'(?:src|href|url\()\s*=?\s*["\']?([^"\')\s>]+)', text, re.I):
                    referenced.add(os.path.basename(m.group(1)))
    return normalize(" ".join(corpus_parts)), hashes, referenced


def load_omissions(path):
    if not path or not os.path.exists(path):
        return [], []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("text", []), data.get("images", [])


def classify(block_text, corpus, corpus_words, threshold):
    norm = normalize(block_text)
    if not norm:
        return "empty", 1.0
    if norm in corpus:
        return "verbatim", 1.0
    words = content_words(block_text)
    if not words:
        return "verbatim" if norm in corpus else "missing", 0.0
    present = sum(1 for w in set(words) if w in corpus_words)
    ratio = present / len(set(words))
    if ratio >= threshold:
        return "paraphrased", ratio
    return "missing", ratio


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--capture", required=True)
    ap.add_argument("--site", default=".")
    ap.add_argument("--omissions")
    ap.add_argument("--min-chars", type=int, default=25)
    ap.add_argument("--threshold", type=float, default=0.72)
    ap.add_argument("--report", default="coverage_report.md")
    ap.add_argument("--fail-under", type=float, default=0.97)
    args = ap.parse_args()

    with open(os.path.join(args.capture, "inventory.json"), encoding="utf-8") as fh:
        inv = json.load(fh)

    corpus, site_hashes, referenced = collect_site(args.site)
    corpus_words = set(corpus.split())
    omit_text, omit_images = load_omissions(args.omissions)
    omit_norms = [(normalize(o.get("match", "")), o.get("reason", "")) for o in omit_text]
    omit_files = {o.get("file", ""): o.get("reason", "") for o in omit_images}

    results = {"verbatim": [], "paraphrased": [], "missing": [], "omitted": []}
    missing_images, orphan_images, omitted_images = [], [], []
    seen_hashes = set()

    for page in inv["pages"]:
        for block in page["blocks"]:
            if block["chars"] < args.min_chars:
                continue
            norm = normalize(block["text"])
            hit = next((r for m, r in omit_norms if m and (m in norm or norm in m)), None)
            if hit is not None:
                results["omitted"].append({"page": page["slug"], "text": block["text"], "reason": hit})
                continue
            status, ratio = classify(block["text"], corpus, corpus_words, args.threshold)
            if status == "empty":
                continue
            results[status].append(
                {"page": page["slug"], "tag": block["tag"], "text": block["text"], "ratio": round(ratio, 2)}
            )

        for img in page["images"]:
            if img.get("duplicate_of") or img["sha1"] in seen_hashes:
                continue
            seen_hashes.add(img["sha1"])
            if img["file"] in omit_files:
                omitted_images.append({"file": img["file"], "reason": omit_files[img["file"]]})
                continue
            if img["sha1"] not in site_hashes:
                missing_images.append(
                    {"file": img["file"], "page": page["slug"], "alt": img.get("alt", ""), "url": img["source_url"]}
                )

    for digest, paths in site_hashes.items():
        for rel in paths:
            if "capture" in rel.split(os.sep):
                continue
            if os.path.basename(rel) not in referenced:
                orphan_images.append(rel)

    scored = len(results["verbatim"]) + len(results["paraphrased"]) + len(results["missing"])
    text_cov = (len(results["verbatim"]) + len(results["paraphrased"])) / scored if scored else 1.0
    img_total = len(seen_hashes)
    img_cov = (img_total - len(missing_images)) / img_total if img_total else 1.0

    lines = [
        "# Content coverage report",
        "",
        f"Source: {inv['source_url']} · {inv['page_count']} pages captured",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Text coverage | **{text_cov:.1%}** ({len(results['verbatim'])} verbatim, "
        f"{len(results['paraphrased'])} reworded, {len(results['missing'])} missing) |",
        f"| Image coverage | **{img_cov:.1%}** ({img_total - len(missing_images)}/{img_total} unique images carried over) |",
        f"| Declared omissions | {len(results['omitted'])} text, {len(omitted_images)} images |",
        f"| Unreferenced files in build | {len(orphan_images)} |",
        "",
    ]

    if results["missing"]:
        lines += ["## Missing text — place these or declare them in omissions.json", ""]
        for item in sorted(results["missing"], key=lambda x: -len(x["text"])):
            snippet = item["text"] if len(item["text"]) <= 300 else item["text"][:300] + "…"
            lines.append(f"- **[{item['page']} / {item['tag']}]** (overlap {item['ratio']}) {snippet}")
        lines.append("")

    if missing_images:
        lines += ["## Missing images — every one of these is a photo the prospect will look for", ""]
        for item in missing_images:
            lines.append(f"- `{item['file']}` (from {item['page']}) alt: {item['alt'] or '(none)'}")
        lines.append("")

    if orphan_images:
        lines += ["## Files present but never referenced by any page", ""]
        for rel in sorted(orphan_images)[:80]:
            lines.append(f"- `{rel}`")
        lines.append("")

    if results["paraphrased"]:
        lines += ["<details><summary>Reworded blocks (matched by word overlap)</summary>", ""]
        for item in results["paraphrased"][:120]:
            snippet = item["text"] if len(item["text"]) <= 200 else item["text"][:200] + "…"
            lines.append(f"- ({item['ratio']}) {snippet}")
        lines += ["", "</details>", ""]

    if results["omitted"] or omitted_images:
        lines += ["## Declared omissions", ""]
        for item in results["omitted"]:
            snippet = item["text"] if len(item["text"]) <= 160 else item["text"][:160] + "…"
            lines.append(f"- _{item['reason']}_ — {snippet}")
        for item in omitted_images:
            lines.append(f"- _{item['reason']}_ — `{item['file']}`")
        lines.append("")

    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"Text coverage:  {text_cov:.1%}  ({len(results['missing'])} missing blocks)")
    print(f"Image coverage: {img_cov:.1%}  ({len(missing_images)} missing images)")
    print(f"Report: {args.report}")

    if text_cov < args.fail_under or missing_images:
        print("\nFAIL: content is still unaccounted for. Place it or declare it in omissions.json.")
        return 1
    print("\nPASS: all source content accounted for.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
