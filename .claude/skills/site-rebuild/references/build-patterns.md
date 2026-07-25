# Build patterns

Markup for every component in `assets/starter/style.css`. Copy, fill with the prospect's real
content, delete what you don't need. The stylesheet is the only CSS you need — resist adding
one-off styles until you've checked whether a component already covers it.

## Contents

- [Page skeleton](#page-skeleton)
- [Header and nav](#header-and-nav)
- [Hero and page banners](#hero-and-page-banners)
- [Section bands](#section-bands)
- [Content components](#content-components) — cards, splits, facts, checklists, callouts, people
- [Galleries and lightbox](#galleries-and-lightbox)
- [Tables](#tables)
- [Timeline](#timeline)
- [Contact and footer](#contact-and-footer)
- [Converting legacy patterns](#converting-legacy-patterns)
- [Choosing a layout for a source page](#choosing-a-layout-for-a-source-page)

## Page skeleton

Every page uses this shell. The `<title>` and description must be unique per page — that alone
fixes a category on most audits.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page name | Business — short differentiator</title>
  <meta name="description" content="One sentence, ~155 chars, containing what they do and where.">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=...&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">…</header>
<main id="main">…</main>
<footer class="site-footer">…</footer>
<script src="assets/js/main.js"></script>
</body>
</html>
```

Set `--font-head` and `--font-body` in the stylesheet to match whatever you load. Two families is
plenty; one is often better. If the sector is formal, a serif heading face does more for
credibility than any layout change.

## Header and nav

Identical on every page except which link carries `class="active"`. The primary action is a
button inside the nav so it is reachable from anywhere.

```html
<header class="site-header">
  <div class="wrap nav">
    <a class="brand" href="index.html">
      <span class="brand-badge"><svg viewBox="0 0 64 64" aria-hidden="true"><!-- mark --></svg></span>
      <span class="brand-name">Business<span>Tagline</span></span>
    </a>
    <button class="nav-toggle" aria-label="Menu" aria-expanded="false"><span></span></button>
    <ul class="nav-links">
      <li><a href="index.html" class="active">Home</a></li>
      <li><a href="services.html">Services</a></li>
      <li><a class="btn btn--accent" href="https://booking.example.com" target="_blank" rel="noopener">Book now</a></li>
    </ul>
  </div>
</header>
```

`main.js` wires the toggle and closes the menu on link tap. Keep the nav to 5–7 items plus the
button; more than that and the mobile menu becomes a scroll.

If the prospect has no usable logo, build a `brand-badge` from an inline SVG glyph plus the
`brand-name` lockup. It reads as deliberate, and it beats a stretched 90s GIF.

## Hero and page banners

Homepage gets `.hero`; interior pages get the lighter `.page-banner`.

```html
<section class="hero">
  <div class="wrap">
    <div class="badge-row">
      <span class="chip">📍 City, ST</span>
      <span class="chip">Since 1962</span>
    </div>
    <h1>The one thing they do, in the visitor's words</h1>
    <p>One sentence of substance. Real facts from the source site, not slogans.</p>
    <div class="cta-row">
      <a class="btn btn--accent" href="…">Primary action →</a>
      <a class="btn btn--ghost" href="…">Secondary</a>
    </div>
  </div>
  <svg class="wave-divider" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true">
    <path fill="#ffffff" d="M0,32 C240,80 480,80 720,48 C960,16 1200,16 1440,48 L1440,90 L0,90 Z"></path>
  </svg>
</section>
```

The `.wave-divider` softens the transition into white. Drop it for formal sectors — add
`.wave-divider.top` above a section to flip it. Chips should carry real facts (location, years in
business, ages served); they are worthless as decoration.

```html
<section class="page-banner">
  <div class="wrap"><h1>Our history</h1><p>One line of orientation.</p></div>
</section>
```

## Section bands

Alternate backgrounds so long pages have rhythm. Never stack two of the same in a row.

- `.section` — white, the default
- `.section--wash` — pale brand tint
- `.section--accent-wash` — pale accent tint, use sparingly
- `.section--deep` — dark brand, white text; good for the contact block and one mid-page break

Each opens with an optional `.eyebrow` label, then `h2`, then a `.lead` paragraph:

```html
<section class="section section--wash">
  <div class="wrap">
    <div class="center" style="max-width:640px;margin-inline:auto;">
      <span class="eyebrow">Why families choose us</span>
      <h2>Heading in their language</h2>
      <p class="lead">Supporting sentence.</p>
    </div>
    <div class="grid grid-3" style="margin-top:44px;">…</div>
  </div>
</section>
```

## Content components

**Cards** in a `.grid.grid-2/3/4` (collapses to 2 then 1 automatically):

```html
<div class="card">
  <h3><span class="icon">🌊</span>Benefit in three words</h3>
  <p>Two sentences from their content. Facts, not adjectives.</p>
</div>
```

**Split** — text beside an image, the workhorse for any "story + photo" block. Add `.reverse` to
put the image first on mobile:

```html
<div class="wrap split">
  <div>
    <span class="eyebrow">A note from our family</span>
    <h2>Heading</h2>
    <div class="stack"><p>Preserved paragraphs…</p></div>
  </div>
  <div class="split-media">
    <img src="assets/images/…" alt="Descriptive alt" width="657" height="347">
  </div>
</div>
```

**Facts strip** — only with real numbers from the source:

```html
<div class="facts">
  <div class="fact"><div class="num">1942</div><div class="lbl">Family owned since</div></div>
</div>
```

**Checklist** for requirements, what-to-bring, what's-included lists:

```html
<ul class="checklist"><li>Bring a towel and sunscreen.</li></ul>
```

**Callout** for the one time-sensitive message the owner most wants seen (openings, closures,
seasonal notes). `.callout.info` is the calmer blue variant:

```html
<div class="callout">
  <span class="co-ico">🎉</span>
  <p><strong>Still openings in Session 6.</strong> Preserved sentence from the source.</p>
</div>
```

**People** — the staff/owner grid. Round crops handle inconsistent source photos gracefully,
which matters because old sites have wildly mixed image quality:

```html
<div class="person">
  <img src="assets/images/…" alt="Jane Doe">
  <h3 style="margin-bottom:2px;">Jane Doe</h3>
  <div class="role">Owner &amp; Manager</div>
  <div class="sub">2nd generation · Certified Pool Operator</div>
</div>
```

**Photo card** when an image needs a caption and body text (facilities, services, locations):

```html
<div class="photo-card">
  <img src="…" alt="…">
  <div class="pc-body"><h3>Name</h3><p>Description.</p></div>
</div>
```

**Press logos** — `.press-grid` with the source's media mentions. Keep these; third-party logos
are earned trust that no design can manufacture.

## Galleries and lightbox

The main mechanism for honouring the "every photo carries over" contract. A masonry gallery
absorbs dozens of mixed-aspect images without looking like a dump, and `main.js` attaches a
keyboard-navigable lightbox to `.gallery` automatically.

```html
<div class="gallery">
  <img src="assets/images/history/pool-1962.jpg" alt="The first pool under construction, 1962">
  <img src="assets/images/history/opening-day.jpg" alt="Opening day, 1963">
</div>
```

Write the alt text from what the content told you about the photo. For archives, group galleries
under `h2`/`h3` headings by era or subject rather than making one 60-image wall — the grouping is
what turns a pile of photos into a story worth scrolling.

The lightbox scales small source images up to fill the viewer with `object-fit: contain`, so
low-resolution historical photos still read as intentional rather than broken.

## Tables

Schedules, prices, and menus. Always wrapped so they scroll on a phone instead of breaking layout:

```html
<div class="table-wrap">
  <table class="sessions">
    <caption>Summer 2026 sessions</caption>
    <thead><tr><th>Session</th><th>Dates</th><th>Price</th><th>Status</th></tr></thead>
    <tbody>
      <tr><td>Session 1</td><td>June 1–12</td><td class="price">$425</td>
          <td><span class="badge full">Full</span></td></tr>
    </tbody>
  </table>
</div>
```

Badges: `.badge.open`, `.badge.full`, `.badge.closed`. Copy prices and dates exactly — a wrong
price in a demo is worse than no demo.

## Timeline

For company history, which is the page owners care most about. One `.tl-item` per era, image
optional inside the card:

```html
<div class="timeline">
  <div class="tl-item">
    <div class="tl-year">1942</div>
    <div class="tl-card">
      <h3>The beginning</h3>
      <p>Preserved paragraph, verbatim.</p>
      <img src="assets/images/history/…" alt="…">
    </div>
  </div>
</div>
```

If the source history is one long undated block of prose, keep the prose in a `.split` or `.stack`
rather than inventing years to fill a timeline.

## Contact and footer

Every phone and email must be a tappable link — this is frequently the single highest-value fix
on the whole rebuild.

```html
<ul class="contact-links">
  <li><a href="https://www.google.com/maps/search/?api=1&query=1044+Curran+Ave+Kirkwood+MO"
         target="_blank" rel="noopener">
    <span class="ci-icon">📍</span><span>1044 Curran Ave, Kirkwood, MO<small>Tap for directions</small></span></a></li>
  <li><a href="tel:+13148211070"><span class="ci-icon">📞</span><span>(314) 821-1070<small>Camp</small></span></a></li>
  <li><a href="mailto:hello@example.com"><span class="ci-icon">✉️</span><span>hello@example.com<small>General</small></span></a></li>
</ul>
```

Put this inside `.section--deep` on the homepage and repeat the essentials in the footer.

Footer is `.footer-grid` (brand blurb, explore links, contact) plus `.footer-bottom` with the
copyright. `main.js` fills `<span id="year">` with the current year so the site never goes stale —
a stale copyright year is on almost every audit, so fixing it structurally is worth the two lines.

## Converting legacy patterns

| Source | Rebuild as |
|---|---|
| Layout `<table>` | `.grid` or `.split` |
| Text baked into an image | Retyped HTML text; keep the image only if it is a real photo |
| PDF menu, schedule, or price list | A real `.table-wrap` table; link the PDF as a secondary download |
| Frameset | Separate pages in the nav |
| Long single-page site | Split by visitor question, one page each |
| Twenty thin pages | Merge into 5–8 by theme; every source paragraph still lands somewhere |
| Flash gallery | `.gallery` with lightbox |
| Guestbook, hit counter, "under construction" | Delete; declare in `omissions.json` |
| Image-map navigation | Real `<ul>` nav links |
| Marquee / blinking text | The `.callout` component |

## Choosing a layout for a source page

- Mostly prose with one or two photos → `.split`, prose in a `.stack`
- Prose with many photos → prose section, then `.gallery` beneath
- A list of services/benefits → `.grid.grid-3` of `.card`
- People → `.grid.grid-3` of `.person`
- Dated events → `.timeline`
- Prices, schedules, hours → `.table-wrap`
- Requirements or what-to-bring → `.checklist`
- One urgent notice → `.callout`

When a source page has no clear structure — a wall of text with images scattered through it —
read it for the natural breaks (each new topic gets an `h2`) rather than forcing it into a grid.
Preserving readability of the owner's own words matters more than component variety.
