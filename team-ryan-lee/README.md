# Team Ryan Lee — hat artwork

Seven concepts for an embroidered cap, in memory of Ryan Lee Winslow. Each one is
supplied in three colourways, as vector SVG plus a 2000px PNG proof.

## The concepts

**Rise** — `rise-*.svg`
The caterpillar low on the left, the moth high on the right, and the diffuser
plume rising diagonally between them — the bubbles doing the work of the change.
Reads left to right and bottom to top at once. The only mark that carries the
tattoos, the practice and the engineering together.

Bubbles run in the ink colour rather than moth green, so they read as air rather
than as more of the animal, and so the mark still stitches in two threads.

**Luna** — `luna-*.svg`
The moth from the tattoo: *Actias luna*, drawn to its own proportions — the
near-straight forewing leading edge, the eyespots, the plumose antennae, and the
long trailing hindwing tails that are the signature of the species. Runs in moth
green rather than gold.

The tails and antennae are drawn deliberately fatter than life. At cap scale a
true-to-nature Luna tail works out to roughly 1mm and would disappear; these hold
about 1.8mm throughout.

**Metamorphosis** — `metamorphosis-*.svg`
Both tattoos together in reading order — larva left, moth right, the same animal
twice. There is no arrow between them; the change in scale carries the
progression, and an arrow would turn it into a diagram. The larva's segments are
built from the same module as the spine concept, because a caterpillar's segments
and a vertebral column are the same shape.

**Varsity** — `varsity-*.svg`
TEAM set small and tracked above a full-width RYAN LEE, closed by a rule and a
diamond. The most straightforward of the seven and the one that reads fastest
across a room. Safe for any kind of team.

**Roundel** — `roundel-*.svg`
A patch-style badge: an RL monogram centred in a double ring, with the full name
beneath. Works as a cap front, and equally as a left-chest mark on a polo or
jacket if the team wants matching pieces.

**Spine** — `spine-*.svg`
A vertebral column beside the name, drawn as a side view — bodies plus spinous
processes, tapering cervical to lumbar, and dead straight, which is
*Straight Up Spine & Posture* taken literally. This is the concept tied to the
practice Ryan founded in 2016 and to what most people knew him for. It is also
the widest and shortest of the seven, which suits a cap front better than the
rest.

**Bubbles** — `bubbles-*.svg`
The same wordmark under a rising plume of bubbles, drawn from Ryan's fine-bubble
diffuser work. The bubbles leave a single source and spread as they climb. It is
the one concept that says something specific about him rather than about teams in
general — which may be exactly right, or may be too close to a subject the family
is still working through. Your call entirely.

## Colourways

| Suffix | Threads | For |
| --- | --- | --- |
| `-on-dark` | Cream + gold | Navy, black, charcoal caps |
| `-on-light` | Navy + gold | Khaki, stone, natural, white caps |
| `-1color` | One thread | Cheapest to stitch; fills with `currentColor` in the SVG |

The Rise, Luna and Metamorphosis marks substitute moth green for gold in both
two-colour cuts.

## Thread colour

| Name | Hex | Nearest common thread |
| --- | --- | --- |
| Cream | `#F6F1E5` | Madeira 1082 / Isacord 0670 — off-white |
| Navy | `#17293F` | Madeira 1243 / Isacord 3554 — navy |
| Gold | `#D9A441` | Madeira 1126 / Isacord 0702 — old gold |
| Moth green | `#AFD46A` | Madeira 1370 / Isacord 6011 — Rise, Luna, Metamorphosis |

Match to the shop's own thread book rather than trusting these on screen. Ask for
a stitch-out on the actual cap colour before the full run.

## Giving these to an embroiderer

Send the **SVG**, not the PNG. Any shop will re-digitize the artwork into a stitch
file (`.DST`, `.PES`, `.EXP`) on their own machine — that step is theirs, is
usually a one-time charge of about $25–75, and cannot be done properly from a
raster image.

Tell them:

- **Placement:** cap front, centred, standard 6-panel
- **Size:** 4.5in wide max on every mark except the roundel, which is 2.25in tall
- **Stitch:** satin on all lettering; bubbles and eyespots run as satin-filled shapes

### Why these are built the way they are

Cap embroidery has a floor below which detail turns to mush, and the artwork is
drawn to stay above it:

- Letter strokes are 14 units on a 60-unit cap height — about 3.3mm stitched, well
  clear of the ~1.5mm minimum
- No text stitches below roughly 0.2in cap height, which is what set the roundel's
  internal sizes
- The smallest bubble is 2.4mm across, and the Luna tails and antennae hold
  about 1.8mm — drawn fatter than the real moth, which would stitch at ~1mm
- No gradients, no hairlines, and never more than two thread colours
- Letterforms are drawn as outlines, so there is no font to license or supply

On a structured 6-panel cap the centre seam runs straight through the middle of
the design. All seven marks have open space on the centreline — no counter or fine
detail lands on the seam, where it would distort.

## Printable review sheets

`print/` holds one letter-size PDF per concept plus `all-seven-concepts.pdf`,
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
- **The practice name.** "Straight Up Spine & Posture" or "Gurnee, IL" can replace
  the rule in the varsity mark, or run under the spine column. Not added unasked —
  the practice name is estate property and how it gets used is your call.
- **Back or side embroidery.** A small `RL` on the back strap or a side panel is
  inexpensive to add and looks considered.
