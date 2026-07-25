# Audit rubric

Use this to score a prospect's current site and to decide whether a rebuild is worth pitching.
Score each category 0–5. Anything scoring 2 or below is a talking point; a site averaging 3.5+
is probably not worth rebuilding, and you should say so.

## Contents

- [How to gather evidence](#how-to-gather-evidence)
- [Universal categories](#universal-categories)
- [Legacy tells](#legacy-tells) — what dates a site at a glance
- [Sector expectations](#sector-expectations) — what each sector's visitors need
- [Writing audit.md](#writing-auditmd)

## How to gather evidence

Fetch the homepage and 2–3 interior pages and look at the actual HTML, not just the rendered page.
The markup tells you when the site was built and what it will cost the owner.

```bash
curl -sS -o /tmp/home.html -w "status=%{http_code} bytes=%{size_download} time=%{time_total}s\n" https://example.com
grep -ic "viewport"        /tmp/home.html   # 0 = not mobile-responsive, the single biggest finding
grep -oi "<table[^>]*>"    /tmp/home.html | wc -l   # many = table-based layout, pre-2010
grep -oi 'meta name="description"[^>]*' /tmp/home.html
grep -oi "wp-content\|squarespace\|wix\|iweb\|frontpage\|dreamweaver\|godaddy" /tmp/home.html | sort -u
grep -oi "<img[^>]*>" /tmp/home.html | grep -civ "alt="   # images with no alt text
```

Check `https://` actually loads and that `http://` redirects to it. Check the page on a narrow
viewport. Note the total page weight and how much of it is uncompressed images — legacy sites
routinely ship 8MB of full-resolution JPEGs scaled down in HTML.

## Universal categories

**Mobile experience (weight this highest).** No viewport meta tag, fixed pixel widths, horizontal
scrolling, text that requires pinch-zoom, tap targets under 44px, phone numbers as images rather
than `tel:` links. Most of these businesses get the majority of their traffic from phones, so a
desktop-only site is not a cosmetic problem — it is the problem.

**Performance.** Page weight over ~2MB, uncompressed images, no caching, render-blocking scripts,
Flash or Java remnants, slow TTFB. Score the number, not the vibe: measure it.

**Trust and security.** No HTTPS, mixed content, expired certificate, visible copyright year more
than two years stale, "best viewed in Internet Explorer", broken images, dead links, a contact
form that silently fails.

**Findability.** Missing or duplicated `<title>` and meta descriptions, no `<h1>` or many, text
baked into images so search engines can't read it, no location or hours in crawlable text, no
structured data, no sitemap.

**Conversion path.** Can a visitor tell in five seconds what the business does, where it is, and
how to buy/book/call? Is the primary action visible without scrolling, and available on every
page? Is the phone number tappable? Is there a form, and does it work?

**Accessibility.** Missing alt text, poor colour contrast, no keyboard focus states, no skip link,
non-semantic markup (`<div>` soup, layout tables), text as images, auto-playing media. This is
both an ethical baseline and, for many sectors, a legal exposure worth naming in the audit.

**Content quality.** Stale dates ("Summer 2019"), prices that contradict each other across pages,
placeholder text, dead staff listings, "under construction". Note these carefully — the rebuild
should surface them to the owner as things to update, not silently correct them, because you don't
know which version is current.

## Legacy tells

Fast identification of what you're dealing with, and what it implies:

| Tell | Implies |
|---|---|
| `<table>` used for layout, spacer GIFs | Hand-built pre-2010; content is trapped in markup, crawl carefully |
| iWeb / FrontPage / Dreamweaver generator tags | Abandoned toolchain, owner cannot edit it at all |
| Text rendered as images (`shapeimage_1.png`) | Invisible to search and screen readers; run `find_text_images.py`, read each hit, transcribe the ones carrying content (step 2b) |
| Frames or framesets | Crawler will miss pages; enumerate frame `src` targets manually |
| Flash/Silverlight embeds | Content is simply gone; ask the owner for the originals |
| Everything on one long homepage | Needs splitting into an IA, not just restyling |
| PDF-only menus, schedules, price lists | Retype into real HTML; PDFs are unreadable on phones and invisible to search |
| A `mailto:` as the only contact method | Add tappable phone and a clear location block |

The image-of-text case deserves special attention: old site builders like iWeb rendered headings
and even whole paragraphs as PNGs. `crawl_site.py` downloads those files but has no way to know
what they say, so the content inventory — and therefore the coverage check — has no record of that
text existing.

Closing the gap is step 2b of the workflow: run `find_text_images.py` to rank the candidates, then
open each one and read it. Sort them into text that carries information (transcribe it into real
HTML) and text that *is* artwork — a logo, a wordmark, a stylized "Live. Laugh. Love." — which
needs no transcription beyond good `alt` text. That judgment is why the script ranks rather than
decides.

For the audit itself, count how much of the site's real content is trapped this way and name it in
the findings. A business whose address, hours, and phone number exist only as pixels is invisible
to search for its own name and city, and unusable to anyone on a screen reader — a concrete
consequence the owner will understand.

## Sector expectations

What visitors actually came for, what the rebuild must therefore make prominent, and the design
register that fits. Use these as cues, not templates; read the prospect's own content first.

**Camps, schools, childcare, youth programs.** Parents need: ages served, dates and sessions,
price, location, what a day looks like, safety and staff credentials, and a working registration
path. Preserve family history and staff bios verbatim — these businesses run on multigenerational
trust. Warm, bright, photo-heavy; rounded shapes; friendly display face.

**Restaurants, cafés, bars.** Hours (today's hours, prominently), full menu as HTML text, location
with a map link, phone, reservation or ordering link, parking. Never leave the menu as a PDF.
Appetite-driven: big food photography, dark or warm palette, minimal chrome.

**Trades and home services** (plumbing, HVAC, roofing, landscaping, electrical). Service area,
services list, emergency phone number above the fold, licensing and insurance, before/after
gallery, quote request, reviews. Owners' photos build trust — keep them. Solid, high-contrast,
utilitarian; a bold accent for the call button.

**Medical, dental, veterinary, therapy.** Provider bios and credentials (verbatim — these are
regulated claims), insurance accepted, appointment booking, new-patient forms, location and
parking, hours. Calm, clean, generous whitespace, low-saturation palette, restrained radii.

**Legal, accounting, financial, insurance.** Practice areas, attorney/advisor bios and bar
admissions verbatim, case results or specializations, consultation request, office locations.
Formal and conservative: serif headings, small radii, muted palette, no playful decoration.

**Nonprofits, churches, community organizations.** Mission, what they do, service or event times,
how to give, how to volunteer, board and staff, history. History and named people are the whole
point — preserve exhaustively. Human-centred photography, warm accent, clear donate button.

**Retail, boutiques, galleries, salons.** What they sell, hours, location, booking or shop link,
gallery, brand story. Visual-first, editorial layout, restrained typography.

**Trades-adjacent B2B, manufacturing, industrial.** What they make, capabilities, certifications,
industries served, quote request, spec sheets. Preserve certification and capability lists
verbatim — buyers filter on them. Sober, structured, table-friendly.

For any sector not listed: read the source content and ask what question a visitor arrives with,
what proof they need, and what single action ends the visit. Build the IA around those three.

## Writing audit.md

Keep it to one page. Structure:

```markdown
# Website audit — <Business name>
<url> · <sector> · reviewed <date>

**Verdict:** <one sentence — rebuild worth pitching, or not, and why>

| Category | Score | Evidence |
|---|---|---|
| Mobile experience | 1/5 | No viewport tag; fixed 900px layout; phone number is an image |
| Performance | 2/5 | 6.4MB homepage, 41 uncompressed JPEGs |
| ... | | |

## The three problems costing them business
1. **<Symptom in plain language>** — <consequence for their customer>
2. ...

## What the rebuild fixes
<2–3 sentences. Concrete, tied to the three problems above.>

## What must be preserved
<Named pages/assets that are the heart of the site — history, staff, founder story, photo archive.>
```

Write the evidence column in terms the owner will recognize. They do not care about semantic
markup; they care that customers can't find their hours on a phone.
