// Generates the Team Ryan Lee hat artwork.
// One glyph set, three concepts, three colourways each — built by script so the
// letterforms stay byte-identical everywhere they appear.
const fs = require('fs');
const OUT = '/home/user/TradingView/team-ryan-lee';
fs.mkdirSync(OUT, { recursive: true });

// ── Geometric caps, 60-unit cap height, 14-unit stem ──────────────────────
// Counters wind opposite to their outer contour so nonzero fill cuts them out.
const G = {
  T: { w: 52, d: 'M0 0 H52 V14 H33 V60 H19 V14 H0 Z' },
  E: { w: 46, d: 'M0 0 H46 V12 H14 V24 H40 V36 H14 V48 H46 V60 H0 Z' },
  A: { w: 56, d: 'M0 60 L21 0 H35 L56 60 H42 L39.2 52 H16.8 L14 60 Z M20.7 41 H35.3 L28 20 Z' },
  M: { w: 68, d: 'M0 0 H16 L34 42 L52 0 H68 V60 H54 V30 L41 58 H27 L14 30 V60 H0 Z' },
  R: { w: 54, d: 'M0 0 H36 A16 16 0 0 1 36 32 H14 V60 H0 Z M14 22 H36 A6 6 0 0 0 36 10 H14 Z M20 28 H36 L54 60 H38 Z' },
  Y: { w: 52, d: 'M0 0 H17 L26 15 L35 0 H52 L33 31 V60 H19 V31 Z' },
  N: { w: 56, d: 'M0 0 H14 L42 37 V0 H56 V60 H42 L14 23 V60 H0 Z' },
  L: { w: 46, d: 'M0 0 H14 V46 H46 V60 H0 Z' },
};

// Optical kerning: letters whose diagonals or arms already lean into their
// neighbour get a tighter gap than the uniform default.
const KERN = { RY: 8, YA: 4, AN: 6, TE: 10, EA: 8, AM: 6, LE: 10, EE: 12, NL: 10 };
const DEFAULT_GAP = 10, SPACE = 40;

function setText(str, track = 0) {
  let x = 0, parts = [];
  for (let i = 0; i < str.length; i++) {
    const ch = str[i];
    if (ch === ' ') { x += SPACE + track; continue; }
    const g = G[ch];
    if (!g) throw new Error('no glyph for ' + ch);
    parts.push(`<path transform="translate(${round(x)},0)" d="${g.d}"/>`);
    x += g.w;
    const next = str[i + 1];
    if (next && next !== ' ') x += (KERN[ch + next] ?? DEFAULT_GAP) + track;
  }
  return { width: x, body: parts.join('\n      ') };
}

const round = n => Math.round(n * 100) / 100;

// Place a text block at a given cap height, horizontally centred on `cx`.
function block(str, cap, cx, yTop, track = 0) {
  const t = setText(str, track);
  const s = cap / 60;
  const x = cx - (t.width * s) / 2;
  return `<g transform="translate(${round(x)},${round(yTop)}) scale(${round(s)})">
      ${t.body}
    </g>`;
}

// Green and off-white taken from the Straight Up Spine & Posture logo.
const C = { cream: '#F6F1E5', navy: '#17293F', green: '#8CC63F' };

// colourway → [main ink, accent ink]
const WAYS = {
  'on-dark':  [C.cream, C.green],
  'on-light': [C.navy,  C.green],
  '1color':   ['currentColor', 'currentColor'],
};

function svg({ w, h, label, ink, accent, body }) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${label}">
  <title>${label}</title>
  <g fill="${ink}">
    ${body.main}
  </g>
  <g fill="${accent}">
    ${body.accent}
  </g>
</svg>
`;
}

// ── Varsity ────────────────────────────────────────────────────
// TEAM tracked small over a full-size RYAN LEE, closed by a rule and diamond.
function varsity() {
  const W = 480, H = 176, cx = W / 2;
  return {
    w: W, h: H, label: 'Team Ryan Lee',
    main: [block('TEAM', 26, cx, 18, 22), block('RYAN LEE', 60, cx, 60)].join('\n    '),
    accent: [
      `<rect x="140" y="140" width="88" height="5"/>`,
      `<rect x="252" y="140" width="88" height="5"/>`,
      `<path d="M240 134 L247 142.5 L240 151 L233 142.5 Z"/>`,
    ].join('\n    '),
  };
}

// ── Rising bubbles ─────────────────────────────────────────────
// The plume is drawn from Ryan's fine-bubble diffuser work: bubbles leave a
// single source and spread as they rise.
function bubbles() {
  const W = 480, H = 200, cx = W / 2;
  const plume = [
    [240, 60, 5],
    [220, 44, 6], [259, 45, 5.5],
    [200, 28, 7], [239, 30, 6], [278, 27, 6.5],
    [181, 12, 6], [218, 14, 5], [260, 12, 5.5], [299, 14, 6],
  ];
  return {
    w: W, h: H, label: 'Team Ryan Lee',
    main: [block('TEAM', 26, cx, 74, 20), block('RYAN LEE', 60, cx, 110)].join('\n    '),
    accent: plume.map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join('\n    '),
  };
}

// ── Spine ─────────────────────────────────────────────────────────────────
// Redrawn to match the Straight Up Spine & Posture logo rather than invented:
// that mark is angular and woodcut-like, not pill-shaped — chunky quadrilateral
// vertebrae with clean slashes between them, a smooth anterior contour down the
// left and a jagged process edge down the right, over a heavier sacrum.
// Local box 84 x 200. Anterior faces left.
//
// Eight segments plus the sacrum. The practice logo packs in more, but at cap
// size the disc gaps have to clear the ~1.5mm stitch floor; these hold ~1.8mm.
//
// [cy, cx, bodyW, bodyH, procLen, procDrop, tilt]  — cx traces the S-curve
const VERTS = [
  [ 14, 36, 17, 13,  8, 2, -10],
  [ 33, 31, 19, 13,  9, 3,  -4],
  [ 52, 29, 21, 14, 10, 4,   4],
  [ 71, 32, 23, 14, 12, 5,  10],
  [ 90, 38, 25, 15, 13, 5,   8],
  [110, 42, 27, 15, 13, 4,  -2],
  [130, 40, 29, 16, 12, 3, -11],
  [150, 33, 30, 16, 10, 2, -15],
];
const SACRUM = 'M18 161 L46 165 L47 176 L41 190 L34 197 L26 194 L22 182 L18 170 Z';

const vertebra = (w, h, p, drop) => {
  const x0 = -w / 2, x1 = w / 2;
  return `M${x0 + 2} ${-h / 2} L${x1 - 2} ${-h / 2 + 1} L${x1 + p} ${-h / 2 + 2 + drop}` +
    ` L${x1 + p - 2} ${-h / 2 + 11 + drop} L${x1 - 3} ${h / 2 - 1} L${x0 + 1} ${h / 2}` +
    ` L${x0 - 1} ${h / 2 - 4} L${x0} ${-h / 2 + 4} Z`;
};

function spineColumn(tx, ty, s) {
  const verts = VERTS.map(([cy, cx, w, h, p, drop, tilt]) =>
    `<path transform="translate(${cx},${cy}) rotate(${tilt})" d="${vertebra(w, h, p, drop)}"/>`
  ).join('\n    ');
  return `<g transform="translate(${tx},${ty}) scale(${s})">${verts}<path d="${SACRUM}"/></g>`;
}

function spine() {
  const W = 480, H = 190;
  const teamT = setText('TEAM', 20), nameT = setText('RYAN LEE');
  const TX = 116;
  return {
    w: W, h: H, label: 'Team Ryan Lee',
    main: [
      `<g transform="translate(${TX},57) scale(${round(22 / 60)})">${teamT.body}</g>`,
      `<g transform="translate(${TX},89) scale(${round(48 / 60)})">${nameT.body}</g>`,
    ].join('\n    '),
    accent: spineColumn(14, 8, 0.87),
  };
}

const CONCEPTS = { spine: spine(), varsity: varsity(), bubbles: bubbles() };

for (const [name, spec] of Object.entries(CONCEPTS)) {
  for (const [way, [ink, accent]] of Object.entries(WAYS)) {
    const body = { main: spec.main, accent: spec.accent.replaceAll("'ACCENT'", accent).replaceAll('ACCENT', accent) };
    const file = `${OUT}/${name}-${way}.svg`;
    fs.writeFileSync(file, svg({ w: spec.w, h: spec.h, label: spec.label, ink, accent, body }));
    console.log('wrote', file.split('/').pop());
  }
}
