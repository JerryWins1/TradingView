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

const C = { cream: '#F6F1E5', navy: '#17293F', gold: '#D9A441' };

// colourway → [main ink, accent ink]
const WAYS = {
  'on-dark':  [C.cream, C.gold],
  'on-light': [C.navy,  C.gold],
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
// Lateral view of a real spine. Anterior faces left, so spinous processes point
// right and sweep downward. Three things make it read as anatomy rather than as
// a ladder: the S-curve (cervical lordosis, thoracic kyphosis, lumbar
// lordosis), vertebrae that grow toward the base, and a fused sacrum.
// Local box 80 x 195.
//
// Seven segments, not more: each body has to stay tall enough to read as a
// block against a visibly thinner process, and the disc gaps have to clear the
// ~1.5mm stitch floor. More vertebrae would be more accurate and would stitch
// as mush.
//
// [cy, cx, bodyW, bodyH, procLen, procAngle, tilt]
const VERTS = [
  [ 12, 34, 16, 12, 12, 18,  -8],
  [ 33, 29, 18, 12, 14, 24,  -3],
  [ 54, 30, 20, 13, 16, 32,   6],
  [ 75, 37, 23, 13, 17, 36,  10],
  [ 96, 43, 26, 13, 17, 32,   3],
  [117, 40, 28, 14, 16, 22,  -9],
  [138, 32, 30, 14, 14, 12, -13],
];
const SACRUM = 'M16 150 L44 154 C46 165 43 176 37 185 C33 191 26 190 24 183 C20 172 17 161 16 150 Z';

function spineColumn(tx, ty, s) {
  const verts = VERTS.map(([cy, cx, w, h, p, pa, tilt]) =>
    `<g transform="translate(${cx},${cy}) rotate(${tilt})">` +
      `<rect x="${-w / 2}" y="${-h / 2}" width="${w}" height="${h}" rx="3.5"/>` +
      // process springs from the upper-posterior corner and sweeps down, so the
      // tips shingle over the vertebra below
      `<g transform="translate(${round(w / 2 - 2)},${round(-h / 5)}) rotate(${pa})">` +
        `<path d="M0 -3.6 L${p} -2.3 Q${p + 2} 0 ${p} 2.3 L0 3.6 Z"/>` +
      `</g>` +
    `</g>`).join('\n    ');
  return `<g transform="translate(${tx},${ty}) scale(${s})">${verts}<path d="${SACRUM}"/></g>`;
}

function spine() {
  const W = 480, H = 190;
  const teamT = setText('TEAM', 20), nameT = setText('RYAN LEE');
  const TX = 112;
  return {
    w: W, h: H, label: 'Team Ryan Lee',
    main: [
      `<g transform="translate(${TX},57) scale(${round(22 / 60)})">${teamT.body}</g>`,
      `<g transform="translate(${TX},89) scale(${round(48 / 60)})">${nameT.body}</g>`,
    ].join('\n    '),
    accent: spineColumn(16, 9, 0.88),
  };
}

const CONCEPTS = { spine: spine(), varsity: varsity(), bubbles: bubbles() };

for (const [name, spec] of Object.entries(CONCEPTS)) {
  for (const [way, [ink, goldAccent]] of Object.entries(WAYS)) {
    const accent = goldAccent;
    const body = { main: spec.main, accent: spec.accent.replaceAll("'ACCENT'", accent).replaceAll('ACCENT', accent) };
    const file = `${OUT}/${name}-${way}.svg`;
    fs.writeFileSync(file, svg({ w: spec.w, h: spec.h, label: spec.label, ink, accent, body }));
    console.log('wrote', file.split('/').pop());
  }
}
