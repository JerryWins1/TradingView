# Ryan — Brand Mark

The identity is a geometric **R** whose stem doubles as a candlestick body, with a
thin wick running above and below it. The trading reference is in the construction
rather than bolted on, so the letter stays legible all the way down to a 16px favicon.

## Files

### Vector (preferred — use these wherever SVG is supported)

| File | Use |
| --- | --- |
| `ryan-logo-horizontal.svg` | Primary lockup. Site headers, docs, email signatures. |
| `ryan-logo-horizontal-reversed.svg` | Primary lockup on dark backgrounds. |
| `ryan-logo-stacked.svg` | Square-ish spaces — cards, splash screens, print. |
| `ryan-mark.svg` | Mark alone, gradient tile. App icon, avatar. |
| `ryan-mark-flat.svg` | Mark alone, solid tile. Print, single-ink, low-res contexts. |
| `ryan-badge.svg` | Circular mark. Social avatars that crop to a circle. |
| `ryan-mark-bare.svg` | Letterform only, no tile. Inherits `currentColor`. |
| `ryan-wordmark.svg` | "RYAN" alone, no mark. Inherits `currentColor`. |
| `favicon.svg` | Browser tab. Wick removed, letter enlarged to survive 16px. |

### Raster (`png/`)

Generated from the SVGs — do not edit by hand. `ryan-mark-{512,256,128}.png`,
`favicon-{64,32,16}.png`, and `@3x` lockups for contexts that reject SVG.

To regenerate after changing a source SVG, re-run the export used to build them
(headless Chromium screenshotting each inlined SVG at the target size).

## Colour

| Token | Hex | Role |
| --- | --- | --- |
| Ink | `#081726` | Gradient terminus, deepest value |
| Navy | `#0E2740` | Flat tile, wordmark on light backgrounds |
| Steel | `#1B4A72` | Gradient origin |
| Bull | `#00D18F` | The wick. The only accent — keep it rare. |
| Paper | `#F6F9FB` | Wordmark and letterform on dark backgrounds |

The tile gradient runs Steel → Navy → Ink on the diagonal (top-left to bottom-right).

## Construction

Everything is built on a 128×128 tile with the letterform on a 60-unit cap height.
Stem width is 14 units; bowl and crossbar strokes are 10, which keeps the stem
optically heavier than the curves the way a text face would.

The wordmark letters are **drawn as outlines, not live text**. There is no font
dependency, so the lockups render identically in every browser, design tool, and
print pipeline. Letterspacing is kerned optically rather than metrically — the gaps
after `R` and around `A` are tighter than a uniform value, because the R's leg and
the A's slanted sides already nest into their neighbours.

## Using it

**Clear space.** Keep free space equal to the tile's corner radius (28 units, or
22% of the tile height) on all sides. Nothing else enters that margin.

**Minimum sizes.** Mark: 24px. Horizontal lockup: 120px wide — below that the
wordmark closes up and you should switch to the mark alone. Use `favicon.svg`,
not `ryan-mark.svg`, anywhere under 24px; the wick is too fine to survive.

**Don't:** recolour the tile, re-typeset the wordmark in a live font, stretch
either axis independently, add effects to the letterform, rotate the lockup, or
place the gradient tile on a busy photo — use `ryan-mark-flat.svg` there.

### Web

```html
<link rel="icon" href="/brand/favicon.svg" type="image/svg+xml">
<link rel="alternate icon" href="/brand/png/favicon-32.png">
<img src="/brand/ryan-logo-horizontal.svg" alt="Ryan" height="40">
```

`ryan-mark-bare.svg` and `ryan-wordmark.svg` fill with `currentColor`, so inline
them and let them take the surrounding text colour:

```html
<span style="color: var(--fg)"><!-- inline contents of ryan-wordmark.svg --></span>
```
