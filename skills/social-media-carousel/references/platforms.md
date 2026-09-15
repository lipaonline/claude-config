# Platform specs & JSON schema

Contents: sizes → platform rules → JSON schema → theme options → slide types.

## Sizes (`format` field)

| format | px | ratio | use for |
|---|---|---|---|
| `instagram` (default) | 1080×1350 | 4:5 | Instagram feed carousel. Max reach format. |
| `linkedin` | 1080×1350 | 4:5 | LinkedIn document post — render with `--pdf`, upload the PDF. |
| `square` | 1080×1080 | 1:1 | Instagram / LinkedIn when the user asks for square. |
| `tiktok` | 1080×1920 | 9:16 | TikTok photo carousel. Keep text in the middle 60 % (UI overlays top/bottom). |
| `story` | 1080×1920 | 9:16 | Instagram stories / Reels cover. |
| `wide` | 1920×1080 | 16:9 | X/Twitter, slides for a talk. |

## Platform rules

- **Instagram**: 2–20 slides (10 is the comfortable max for readers). All slides share one ratio. PNG or JPG. Cover must work as a square crop on the profile grid: keep the title in the central 1080×1080.
- **LinkedIn**: upload one PDF (≤ 300 pages, ≤ 100 MB). 4:5 or square. Add a document title in the post UI. Links go in the first comment.
- **TikTok**: 1–35 photos, 9:16 preferred, plays as a slideshow with music; users can also swipe. Text large (≥ 44px at 1080 wide).
- **X**: up to 4 images, no swipe order guarantee — number the slides visibly.

## JSON schema (`carousel.json`)

```json
{
  "format": "instagram | linkedin | square | tiktok | story | wide",
  "theme": {
    "preset": "minimal | bold | dark | editorial",
    "handle": "@brand",
    "swipe": "Swipe →",
    "bg": "#fff", "fg": "#111", "muted": "#666", "accent": "#2F5BFF", "card": "#f3f4f6",
    "font": "\"Inter\", sans-serif", "display": "\"Georgia\", serif",
    "pad": "96px", "radius": "28px"
  },
  "slides": [ { "type": "…", "…": "…" } ]
}
```

`theme`: `preset` sets a full palette; any explicit key overrides it. Fonts must be installed on the rendering machine (no network). `**text**` inside titles, bodies, labels and list items colours that span with the accent. `\n` forces a line break. Add `"top": true` on a slide to top-align it instead of centring.

## Slide types

| type | fields | notes |
|---|---|---|
| `cover` | `kicker?`, `title`, `sub?` | Counter is replaced by the swipe label. |
| `point` | `n?`, `kicker?`, `title`, `body?` | `n` renders as a big "01". |
| `list` | `kicker?`, `title`, `items[]`, `checks?` | Arrows by default, ✓ with `checks: true`. |
| `quote` | `text`, `author?` | Curly quotes added automatically. |
| `stat` | `kicker?`, `value`, `label`, `body?` | `value` is huge; keep it ≤ 6 characters. |
| `image` | `src`, `caption?` | Full-bleed image (path relative to the JSON, or URL). No handle/counter on this slide. |
| `cta` | `kicker?`, `title`, `body?`, `button?` | Last slide. |

## Rendering

```bash
node <skill>/scripts/render.mjs carousel.json --out ./out            # PNGs
node <skill>/scripts/render.mjs carousel.json --out ./out --pdf      # + carousel.pdf (LinkedIn)
node <skill>/scripts/render.mjs carousel.json --scale 2              # 2160px wide PNGs
node <skill>/scripts/render.mjs carousel.json --html-only            # just out/index.html to inspect
```

Needs Chrome, Chromium, Brave or Edge installed (auto-detected; override with `CHROME_PATH`). ~2–3 s per slide. If no browser is found, open `out/index.html` and print to PDF manually; `?slide=3` shows a single slide.
