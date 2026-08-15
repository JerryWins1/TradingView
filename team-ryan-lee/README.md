# Team Ryan Lee — hat artwork

Three concepts for an embroidered cap, in memory of Ryan Lee Winslow. Each one is
supplied in three colourways, as vector SVG plus a 2000px PNG proof.

## The concepts

**Spine** — `spine-*.svg`
The spine from the *Straight Up Spine & Posture* logo, redrawn as embroidery
artwork rather than invented: the same angular, woodcut-style vertebrae with
clean slashes between them, a smooth contour down the front and a jagged process
edge down the back, over a heavier sacrum. In the practice's own green.

Eight segments plus the sacrum. The practice logo packs in more, but at cap size
the disc gaps have to clear the ~1.5mm stitch floor — more vertebrae would be
truer to the original and would stitch as mush. Vertebrae land at 2.6mm with
1.8mm gaps.

**Varsity** — `varsity-*.svg`
TEAM set small and tracked above a full-width RYAN LEE, closed by a rule and a
diamond. The most straightforward of the three and the one that reads fastest
across a room. Safe for any kind of team.

**Bubbles** — `bubbles-*.svg`
The same wordmark under a rising plume of bubbles, drawn from Ryan's fine-bubble
diffuser work. The bubbles leave a single source and spread as they climb. It is
the one concept that says something specific about him rather than about teams in
general — which may be exactly right, or may be too close to a subject the family
is still working through. Your call entirely.

## Colourways

| Suffix | Threads | For |
| --- | --- | --- |
| `-on-dark` | Cream + green | Navy, black, charcoal caps |
| `-on-light` | Navy + green | Khaki, stone, natural, white caps |
| `-1color` | One thread | Cheapest to stitch; fills with `currentColor` in the SVG |

## Thread colour

| Name | Hex | What to ask for |
| --- | --- | --- |
| Practice green | `#8CC63F` | The green from the Straight Up logo — bright yellow-green |
| Cream | `#F6F1E5` | Soft off-white, not a stark bright white |
| Navy | `#17293F` | Deep, near-black navy |

Take the hex values to the shop and match against their own thread book. Screens
lie, and thread codes vary by brand and range, so match to the swatch rather than
to a number. Ask for a stitch-out on the actual cap colour before the full run.

## Giving these to an embroiderer

Send the **SVG**, not the PNG. Any shop will re-digitize the artwork into a stitch
file (`.DST`, `.PES`, `.EXP`) on their own machine — that step is theirs, is
usually a one-time charge of about $25–75, and cannot be done properly from a
raster image.

Tell them:

- **Placement:** cap front, centred, standard 6-panel
- **Size:** 4.5in wide max, 2.25in tall
- **Stitch:** satin on all lettering; bubbles and vertebrae run as satin-filled shapes

### Why these are built the way they are

Cap embroidery has a floor below which detail turns to mush, and the artwork is
drawn to stay above it:

- Letter strokes are 14 units on a 60-unit cap height — about 3.3mm stitched, well
  clear of the ~1.5mm minimum
- No text stitches below roughly 0.2in cap height
- The smallest bubble is 2.4mm across; spine vertebrae are 2.6mm with 1.8mm disc gaps
- No gradients, no hairlines, and never more than two thread colours
- Letterforms are drawn as outlines, so there is no font to license or supply

On a structured 6-panel cap the centre seam runs straight through the middle of
the design. All three marks have open space on the centreline — no counter or fine
detail lands on the seam, where it would distort.

## Printable review sheets

`print/` holds one letter-size PDF per concept plus `all-three-concepts.pdf`,
for printing and passing round. Each sheet shows the mark large, the khaki and
single-thread cuts, and the mark at true stitched size inside a dashed
4.5 x 2.25in rule — the real cap-front stitching area, printed 1:1. Hold the page
against a cap and the size question answers itself.

**Print at 100% / Actual Size, not Fit to Page**, or the true-size panel is not
true. Regenerate with `node make-print-sheets.js`.

## Still open

- **A year or dates.** Memorial team hats often carry them. Nothing is invented
  here. Public records give March 25, 2024 and age 37, which puts the birth year
  at either 1986 or 1987 depending on his birthday — not something to guess at on
  a hat. Confirm the wording and I'll set it.
- **The practice name in words.** The spine mark is now the practice's, at your
  direction. "Straight Up Spine & Posture" or "Gurnee, IL" could also run as text
  under the spine or replace the rule in the varsity mark — not added unasked.
- **Back or side embroidery.** A small `RL` on the back strap or a side panel is
  inexpensive to add and looks considered.
