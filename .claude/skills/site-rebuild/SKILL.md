---
name: site-rebuild
description: >-
  Audit an outdated business website against best practices for its sector and rebuild it as a
  modern, fast, mobile-first static site that carries over 100% of the prospect's real content —
  every staff bio, company history, founder story, and photo — so it can be shown to them as a
  spec-built pitch of what their site could look like. Use this whenever someone points at a
  company's URL and wants it modernized, redesigned, rebuilt, refreshed, "brought up to date,"
  turned into a demo or mockup for a sales pitch, or asks how bad a site is versus its
  competitors — including bulk requests to work through a list of prospect sites. Also use it for
  the pieces on their own: crawling a site to inventory its content and images, scoring a site
  against sector best practices, or checking that a rebuild didn't drop anything.
---

# Site rebuild

You are building a speculative redesign of a real business's website, to be shown to that
business as a pitch. Two things follow from that, and they shape every decision below.

**It has to be visibly better.** The prospect already knows their site is dated. The rebuild
earns the meeting by being obviously faster, obviously usable on a phone, and obviously clearer
about what the business does and what to do next.

**It has to be unmistakably theirs.** The fastest way to lose the deal is for the owner to open
the demo and not find the photo of their father who founded the place, or their staff, or the
paragraph they wrote themselves years ago. Those pages are not filler to be replaced with
better-written copy — they are the reason the owner cares about the site at all. Treat their
words and photos as fixed material you are re-housing, not as a draft you are improving.

## The preservation contract

Everything on the source site falls into one of three buckets. Decide the bucket before you write
any markup.

**Preserve verbatim** — reproduce word for word, and carry every associated image:
- Founder and company history, origin stories, anniversary notes, "letter from the owner"
- Named people: staff, owners, instructors, providers, their bios, titles, credentials
- Testimonials, quotes, press mentions, awards, certifications, affiliations
- Prices, dates, schedules, policies, rules, requirements, hours, contact details
- Anything with a proper noun, a number, or a date in it

**Condense** — keep every fact, tighten the prose:
- Generic marketing throat-clearing, repeated boilerplate, verbose intros
- Long text is fine to restructure into a list, a table, or cards — restructuring is not cutting

**Drop, only with a declared reason:**
- Navigation labels, "click here", copyright lines, and other chrome
- Dead links, broken embeds, content about events that have visibly passed
- Duplicate text that appears identically on many pages

Never write facts the source did not state. No invented testimonials, statistics, awards,
credentials, service areas, or years-in-business. If the design calls for a stat strip and the
site gives you three real numbers, build a three-item strip. Fabricated claims on a live business's
website are a liability for them and destroy your credibility in the meeting.

If a source photo is genuinely unusable at any size (a 90×60px thumbnail, a broken file), it still
has to go somewhere — put it in a captioned archive gallery rather than dropping it. Historical
photos are usually low-resolution *and* the most emotionally important assets on the site.

## Workflow

Work through these in order. Steps 1–3 are cheap and prevent expensive rework.

### 1. Audit the current site

Fetch the homepage and two or three interior pages. Score them with the rubric in
`references/audit-rubric.md`, which covers both the universal checks (mobile, speed, HTTPS,
metadata, conversion path, accessibility) and what specifically matters in the prospect's sector.

Write `audit.md`: what the site is, the sector, the score per category, the three problems costing
them the most business, and one line on what the rebuild will fix. This doubles as the opening of
the sales conversation, so name concrete symptoms — "the phone number is an image, so it can't be
tapped on a phone" beats "poor mobile experience."

If the site is already modern and well-built, say so and stop. A rebuild pitch for a good site
wastes everyone's time, and telling the user that is more useful than a marginal redesign.

### 2. Capture everything

```bash
python3 scripts/crawl_site.py https://example.com --out capture/ --max-pages 40
```

This writes `capture/raw/` (verbatim HTML), `capture/images/<page>/` (every image, deduped by
content hash), `capture/inventory.json` (structured blocks for the coverage check),
`capture/content.md` (readable dump), and `capture/crawl_report.md`.

**Read `capture/content.md` end to end before designing anything.** This is the step people skip,
and it is where the pitch is won: the founder's letter, the 1962 photo caption, the note about
which sessions still have space. You cannot make good structural decisions about content you
haven't read.

Check `crawl_report.md` for fetch failures and for outbound links — booking systems, registration
platforms, ordering portals, and social profiles are usually the site's only real conversion path,
and they must survive into the rebuild.

If the crawler is blocked (egress policy, bot protection, a JS-only site), say so plainly and ask
the user how to get the content rather than rebuilding from guesses. A JS-rendered site may need
a headless browser; a blocked host is a policy decision that is not yours to route around.

### 3. Plan the information architecture

Write `plan.md` mapping every source page to a destination:

| Source page | Destination | Treatment |
|---|---|---|
| index.html | index.html hero + welcome | condense marketing, preserve owner's letter verbatim |
| about-us.html | history.html | preserve verbatim, restructure as timeline |
| photos.html | pools.html gallery | all 30 images, lightbox |

Old sites are usually either sprawling (20 thin pages) or cramped (everything on one page).
Aim for 5–8 pages, each one answering a question a real visitor has. Order the nav by what
visitors need most, and put the single most important action — book, register, call, order,
request a quote — as a button in the header on every page.

Confirm the IA with the user before building if the mapping involves real judgment calls.

### 4. Design

Pick a direction that fits the sector, not your taste — a children's camp and an estate law firm
need opposite treatments. `references/audit-rubric.md` gives per-sector cues.

Set the palette by editing the eight tokens at the top of `assets/starter/style.css`. Derive them
from the prospect's existing brand colours where those are usable (a logo, an awning, a uniform),
which makes the demo feel like *their* site rather than a template. Keep body text at 4.5:1
contrast minimum.

Then build pages from the components in `references/build-patterns.md` — it documents the markup
for the nav, hero, section bands, cards, split text/image, galleries with lightbox, responsive
tables, timelines, people grids, and callouts, all of which the starter stylesheet already styles.

### 5. Build

Copy the starter assets and write plain semantic HTML — one file per page, one shared stylesheet,
one small script. No build step, no framework, no dependencies. This matters: the prospect's
current webmaster has to be able to take it over, it deploys anywhere, it loads instantly on the
rural 4G connection their customers actually use, and it will still work in five years.

```bash
cp .claude/skills/site-rebuild/assets/starter/style.css assets/css/
cp .claude/skills/site-rebuild/assets/starter/main.js  assets/js/
cp -r capture/images/* assets/images/
```

Non-negotiables on every page: unique `<title>` and meta description, one `<h1>`, a skip link,
`alt` text on every image (write real alt text from the content — the source site's alt attributes
are usually empty or a filename), `width`/`height` on images to stop layout shift, `tel:` and
`mailto:` links on every phone number and email, and a tap target of at least 44px on anything
clickable.

### 6. Verify — do not skip this

```bash
python3 scripts/check_coverage.py --capture capture/ --site . --omissions omissions.json
```

It reports the share of source text blocks present in your build (verbatim or reworded) and the
share of source images carried over by content hash, and it fails if anything is unaccounted for.
For each item it flags, either place the content or add it to `omissions.json` with a reason:

```json
{
  "text":   [{"match": "Site design by WebCo 2009", "reason": "old vendor credit"}],
  "images": [{"file": "images/index/spacer.gif", "reason": "layout spacer"}]
}
```

Writing the reason is the point — it forces a deliberate decision on every dropped item instead of
a silent loss. Expect a few false positives where the crawler captured a wrapper element whose text
is the concatenation of its children; confirm by eye, then declare them.

Then check by hand what a script can't: load the site at 375px and 1280px wide, tab through it to
confirm focus is visible and the nav is reachable, click every internal link, and confirm the
primary CTA works from every page.

### 7. Deliver

See `references/delivery.md` for the GitHub Pages workflow, the single-file bundle for site
builders that only import one HTML file, and what to put in the handoff summary. In short:

```bash
python3 scripts/bundle_singlefile.py index.html --out bundle/index.html --max-image-kb 400 \
  --asset-base https://USER.github.io/REPO/
```

Close with a short `summary.md` for the user: what was wrong, what changed, the coverage numbers
from step 6, and anything you deliberately dropped. The coverage numbers are the credibility
argument — "every one of your 57 photos and 99% of your text carried over" is what lets the
prospect trust the demo enough to look at it properly.

## Working through a list of sites

When given several prospects, do them one at a time in separate directories, and audit all of them
(step 1) before building any of them. The audit is cheap and the build is not, so lead with the
worst-scoring sites in sectors where you can reuse a design direction. Keep a single
`prospects.md` table of URL, sector, score, and status so the batch stays legible.

## Bundled resources

- `references/audit-rubric.md` — scoring categories, thresholds, and per-sector expectations and
  design cues. Read at step 1.
- `references/build-patterns.md` — component markup for every class in the starter stylesheet,
  plus how to convert common legacy patterns (image-of-text, table layouts, framesets, PDF-only
  content). Read at steps 4–5.
- `references/delivery.md` — GitHub Pages deploy, single-file bundling for Wix/Squarespace import,
  image weight budgets, and the handoff summary format. Read at step 7.
- `scripts/crawl_site.py` — capture pages, images, and a content inventory.
- `scripts/check_coverage.py` — verify nothing was dropped.
- `scripts/bundle_singlefile.py` — inline a page into one portable HTML file.
- `assets/starter/style.css`, `assets/starter/main.js` — token-driven stylesheet and interactions.

All scripts are stdlib-only (`requests` used if present) and take `--help`.
