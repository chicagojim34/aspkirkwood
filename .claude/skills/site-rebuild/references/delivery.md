# Delivery

How to get the rebuild in front of the prospect. Three formats, used together: a live URL they can
open on their phone, a single file you can email or import into a site builder, and a short
summary that frames what they're looking at.

## Contents

- [Image weight](#image-weight) — do this before deploying
- [GitHub Pages](#github-pages)
- [Single-file bundle](#single-file-bundle)
- [Importing into a site builder](#importing-into-a-site-builder)
- [The handoff summary](#the-handoff-summary)
- [Boundaries](#boundaries)

## Image weight

Legacy sites ship enormous images, and if you copy them across unchanged you lose the performance
argument that justified the rebuild. Do this before deploying, not after.

```bash
find assets/images -type f -size +500k -exec ls -lh {} \; | awk '{print $5, $9}' | sort -rh
du -sh assets/images
```

Resize anything wider than ~2000px and re-encode large JPEGs. If ImageMagick is available:

```bash
mogrify -resize '2000x2000>' -quality 82 -strip assets/images/**/*.jpg
```

If it isn't, say so rather than shipping 40MB — an unoptimized demo undercuts the pitch. Never
upscale historical photos to hide their resolution; the lightbox already presents small originals
respectfully, and a blurry upscale looks worse than an honest small image.

Add `width` and `height` attributes to every `<img>` so the page doesn't shift while loading, and
`loading="lazy"` on anything below the fold — galleries especially.

## GitHub Pages

The fastest way to a shareable URL. Commit `.github/workflows/deploy-pages.yml`:

```yaml
name: Deploy static site to GitHub Pages
on:
  push:
    branches: [main]
  workflow_dispatch: {}
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - id: deployment
        uses: actions/deploy-pages@v4
```

Pages must be enabled for the repo with source set to GitHub Actions — the workflow cannot do that
for you, so tell the user if the first run fails on it. Since all links are relative, the site
works unchanged at `https://user.github.io/repo/`.

Deploying is publishing: it puts a version of another company's brand and content on the open web.
Keep the repo private or the URL unlisted unless the user has said they want it public, and don't
add analytics, tracking, or third-party embeds the prospect didn't already have.

## Single-file bundle

Site builders and email both want one file. `bundle_singlefile.py` inlines the stylesheet, script,
favicon, and images as data URIs, leaving web fonts and maps as remote references.

```bash
python3 scripts/bundle_singlefile.py index.html --out bundle/index.html \
  --max-image-kb 400 --asset-base https://USER.github.io/REPO/
```

- `--max-image-kb 400` keeps the file manageable by leaving big images as links; `--asset-base` is
  then **required**, or those images resolve to nothing. Deploy to Pages first so the base URL exists.
- `--max-image-kb 0` inlines everything for a genuinely standalone file. Expect ~700KB for a
  photo-rich homepage — fine for email, slow over a hotel connection.
- Bundle one page (usually the homepage) unless asked otherwise. Inter-page links still point at
  relative `.html` files, so a bundled page is a preview, not the whole site.

Open the result and confirm every image renders before sending it.

## Importing into a site builder

If the prospect is committed to Wix, Squarespace, GoDaddy, or similar, the bundle is the import
artifact. Set expectations honestly: these builders accept a single HTML page as an embed or
custom-code block, they will not reconstruct a multi-page site from it, and the imported page
usually sits inside the builder's own header and footer chrome.

When importing, remove the bundle's own `<header>` and `<footer>` if the builder supplies them, or
the page renders two navs. Keep the live GitHub Pages URL as the reference version — it is the one
that actually demonstrates the speed argument.

## The handoff summary

Write `summary.md` in the repo. It is what the user reads before the meeting.

```markdown
# <Business> — rebuild summary

**Live demo:** <url>   **Source site:** <url>

## What was wrong
<3–5 bullets from audit.md, in the owner's language.>

## What changed
<3–5 bullets. Tie each to a problem above.>

## Content carried over
- Text coverage: 99.6% (from coverage_report.md)
- Images: 57 of 57 unique photos
- Preserved verbatim: founder's letter, full company history, all staff bios, 1962 photo archive

## Deliberately left out
<Each item and its reason, from omissions.json.>

## Things the owner should check
<Contradictions and stale content you found but did not silently fix — e.g. two different prices
for Session 3, a staff member listed who may no longer work there, hours that disagree between
pages. Flagging these is genuinely useful to them and shows you read the site.>

## Notes
<Anything blocked: pages that wouldn't fetch, Flash content that no longer exists, text locked in
images that you transcribed by hand.>
```

The coverage numbers and the "things to check" list are what separate this from a template demo.
They demonstrate that someone actually read the business's website.

## Boundaries

This is speculative work on someone else's brand, so a few things stay off the table regardless of
how much better they'd make the demo:

- **Don't register domains, buy hosting, or point DNS.** Show a demo URL; the prospect decides.
- **Don't contact the prospect** — no emails, no contact-form submissions on their live site, no
  outreach on the user's behalf unless they explicitly ask for it.
- **Don't copy a competitor's design** as the prospect's new look, and don't lift copy from any
  other site into theirs.
- **Don't publish claims the source didn't make.** Certifications, awards, years in business,
  license numbers, and service areas come from their site or they don't appear.
- **Don't present the demo as their official site.** If the deploy is public, the summary should
  make clear it's an unaffiliated concept. If the user asks for something that would read as the
  real thing — their domain, their branding on a live commercial page, a form collecting real
  customer data — that's a conversation to have with them first.
