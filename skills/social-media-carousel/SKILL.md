---
name: social-media-carousel
description: Write and render social media carousels (Instagram, LinkedIn document/PDF, TikTok photo carousel, square, story) from a topic or a draft — hook-driven outline, one idea per slide, CTA, caption with hashtags, then PNG slides and a PDF via a zero-dependency Chrome renderer. Trigger on "carousel", "carrousel", "slides for LinkedIn/Instagram", "swipe post", "document post", "turn this article/thread into a carousel".
---

# Social Media Carousel

Turn a topic, an article, a thread or a set of notes into a ready-to-post carousel: copy first,
then a `carousel.json`, then rendered slides. The renderer is `scripts/render.mjs`
(Node ≥ 18 + any installed Chrome/Chromium; no npm install).

Read `references/writing.md` before writing copy. Read `references/platforms.md` when picking
a format, filling the JSON, or when a slide type / theme option is unclear.

## Workflow

### 1. Brief (ask only what's missing, one message)

Collect: **platform** (default Instagram 4:5), **topic + source material**, **audience**,
**goal of the CTA** (save / follow / comment keyword / link), **tone**, **handle**, and any
**brand colours or fonts**. If the user pasted a long text, extract the 5–8 strongest claims
before anything else.

### 2. Outline before slides

Propose the outline as a numbered list (slide type + title + one-line body) and **three cover
hook options**. Aim for 7–10 slides. Wait for a pick when the user is present; otherwise take
the first hook and continue. Rules that matter most:

- One idea per slide; title ≤ 7 words, body ≤ 25 words.
- Cover promises something specific; last slide asks for **one** action.
- Numbers get their own `stat` slide; steps get a `list`; proof gets a `quote` or `image`.

### 3. Write `carousel.json`

Follow the schema in `references/platforms.md`. Start from `assets/example.json`. Pick a theme
preset (`minimal`, `bold`, `dark`, `editorial`) or set brand tokens explicitly; wrap the one
accent word of each title in `**…**`. Save next to the user's project, not inside the skill.

### 4. Render

```bash
node <skill-dir>/scripts/render.mjs carousel.json --out ./carousel-out          # PNG per slide
node <skill-dir>/scripts/render.mjs carousel.json --out ./carousel-out --pdf    # + PDF for LinkedIn
```

Then **look at the PNGs** (open two or three, at least the cover and the longest slide) and
fix overflow: shorten copy, split the slide, or lower `pad`. Never ship a slide you haven't seen.
For a different look, offer 2–3 preset variants of the cover only, then render the full set once.

### 5. Deliver

- Path to the PNGs (and PDF when LinkedIn), in posting order.
- The caption in a fenced block (hook line, 2–5 lines, CTA, hashtags per platform rules).
- Three alternative cover hooks for A/B testing.
- One line on where the copy could be tightened if the user has an edit pass.

## Quick reference

| Platform | `format` | Deliver |
|---|---|---|
| Instagram | `instagram` (1080×1350) | PNGs |
| LinkedIn | `linkedin` (1080×1350) | `carousel.pdf` (`--pdf`) |
| TikTok | `tiktok` (1080×1920) | PNGs, text in the middle 60 % |
| Square / X | `square` / `wide` | PNGs |

Slide types: `cover`, `point`, `list`, `quote`, `stat`, `image`, `cta`.

## Don't

- Don't write more than 10 slides unless the user asks; don't pad with a "thanks for reading" slide.
- Don't invent statistics or quotes. Mark anything unsourced as an estimate or drop it.
- Don't put links on the slides for LinkedIn (they aren't clickable in documents).
- Don't render before the outline is agreed when the user is in the loop.
