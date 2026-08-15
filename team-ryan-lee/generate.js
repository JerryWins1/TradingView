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

// ── Concept 1: Varsity ────────────────────────────────────────────────────
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

// ── Concept 2: Roundel ────────────────────────────────────────────────────
// Patch-style badge: RL monogram centred, name set straight (not arced) so the
// small type stays legible once it is stitched.
function roundel() {
  const S = 360, c = S / 2;
  // Ring as a true donut: outer contour and inner contour wound in opposite
  // directions so nonzero fill knocks the middle out.
  const ring = (R, r) =>
    `<path d="M${c - R} ${c} a${R} ${R} 0 1 0 ${2 * R} 0 a${R} ${R} 0 1 0 ${-2 * R} 0 Z ` +
    `M${c - r} ${c} a${r} ${r} 0 1 1 ${2 * r} 0 a${r} ${r} 0 1 1 ${-2 * r} 0 Z"/>`;
  return {
    w: S, h: S, label: 'Team Ryan Lee',
    main: [
      ring(176, 164),
      // Type sized so nothing stitches below the ~0.2in legibility floor when
      // the badge is worked at a 2.25in hat-front height.
      block('TEAM', 26, c, 88, 20),
      block('RL', 88, c, 126),
      block('RYAN LEE', 32, c, 240),
    ].join('\n    '),
    accent: [
      `<circle cx="${c}" cy="${c}" r="152" fill="none" stroke="ACCENT" stroke-width="3"/>`,
      `<rect x="130" y="226" width="100" height="4"/>`,
    ].join('\n    '),
  };
}

// ── Concept 3: Rising bubbles ─────────────────────────────────────────────
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

// ── Concept 4: Spine ──────────────────────────────────────────────────────
// A vertebral column for Straight Up Spine & Posture — the practice Ryan
// founded in 2016 and the thing most people knew him for. Vertebrae taper
// wider toward the lumbar end, and the column is dead straight, which is the
// practice name taken literally.
function spine() {
  const W = 480, H = 150;
  // Side view: a vertebral body plus its spinous process pointing back. Plain
  // stacked bars read as a cone; the process is what makes it a spine.
  const SX = 46, BAR_H = 13, PITCH = 21;   // 8-unit gap ≈ 1.9mm stitched
  const bodies = [30, 33, 36, 39, 42, 45];       // cervical → lumbar
  const top = (H - ((bodies.length - 1) * PITCH + BAR_H)) / 2;
  const vertebrae = bodies.flatMap((w, i) => {
    const y = top + i * PITCH;
    const right = SX + w / 2;
    return [
      `<rect x="${round(SX - w / 2)}" y="${round(y)}" width="${w}" height="${BAR_H}" rx="3.5"/>`,
      `<rect x="${round(right - 2)}" y="${round(y + 2)}" width="20" height="8" rx="4"/>`,
    ];
  });
  // Text is left-aligned beside the column rather than centred on the canvas.
  const teamT = setText('TEAM', 20), nameT = setText('RYAN LEE');
  const TX = 108;
  return {
    w: W, h: H, label: 'Team Ryan Lee',
    main: [
      `<g transform="translate(${TX},38) scale(${round(22 / 60)})">${teamT.body}</g>`,
      `<g transform="translate(${TX},68) scale(${round(46 / 60)})">${nameT.body}</g>`,
    ].join('\n    '),
    accent: vertebrae.join('\n    '),
  };
}

// ── Luna moth + Luna caterpillar ──────────────────────────────────────────
// Actias luna, drawn from the pair of tattoos: the larva and the adult of the
// same animal. All filled contours, no strokes, so a digitizer gets closed
// shapes to satin-fill rather than centre-lines to guess at.
const LUNA_GREEN = '#AFD46A';

// Local box 240 x 200, symmetric about x = 120.
const LUNA_FOREWING = 'M110 44 C86 22 46 14 20 26 C7 32 3 47 14 56 C27 69 66 75 110 66 Z';
// Hindwing and tail are ONE contour — the tail is the trailing edge drawn out
// and narrowed, not an appendage hung off the bottom.
// The tail is deliberately fatter than life: at cap scale a true-to-nature
// Luna tail stitches at ~1.0mm and disappears. This holds ~1.8mm throughout.
const LUNA_HINDWING = 'M110 70 C88 76 56 82 42 96 C29 109 27 128 38 142 C47 155 59 174 68 193 C71 200 84 198 82 188 C78 170 74 152 82 136 C90 118 105 100 110 90 Z';

function lunaMoth(tx, ty, s) {
  const at = `translate(${round(tx)},${round(ty)}) scale(${s})`;
  const wingPair = `<path d="${LUNA_FOREWING}"/><path d="${LUNA_HINDWING}"/>`;
  return {
    wings: `<g transform="${at}">${wingPair}<g transform="translate(240,0) scale(-1,1)">${wingPair}</g></g>`,
    body: `<g transform="${at}">` +
      `<ellipse cx="120" cy="44" rx="10" ry="15"/>` +
      `<path d="M112 54 C112 80 114 102 120 116 C126 102 128 80 128 54 Z"/>` +
      `<circle cx="120" cy="28" r="8"/>` +
      // plumose antennae
      `<path d="M118 24 C104 13 92 5 77 -1 C82 10 87 18 93 23 C99 27 106 31 112 35 Z"/>` +
      `<path d="M122 24 C136 13 148 5 163 -1 C158 10 153 18 147 23 C141 27 134 31 128 35 Z"/>` +
      `</g>`,
    // eyespots read as knockouts in the wing, so they take the ground colour
    spots: `<g transform="${at}">` +
      `<ellipse cx="62" cy="50" rx="8" ry="5.5"/><ellipse cx="178" cy="50" rx="8" ry="5.5"/>` +
      `<ellipse cx="70" cy="102" rx="7" ry="5"/><ellipse cx="170" cy="102" rx="7" ry="5"/>` +
      `</g>`,
  };
}

// Local box 150 x 62. Plump segmented larva, pale prolegs beneath, dot rows on
// the back — the same vertebra-like module as the spine concept, rolled round.
function lunaLarva(tx, ty, s) {
  const at = `translate(${round(tx)},${round(ty)}) scale(${s})`;
  const seg = [[16, 36, 11], [34, 31, 12.5], [52, 28, 13.5], [70, 28, 13.5], [88, 31, 13]]
    .map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join('');
  const legs = [[14, 47], [32, 44], [50, 42], [68, 42], [86, 44]]
    .map(([x, y]) => `<rect x="${x - 4}" y="${y}" width="8" height="13" rx="4"/>`).join('');
  const dots = [[32, 21], [50, 17], [68, 17], [86, 21]]
    .map(([x, y]) => `<circle cx="${x}" cy="${y}" r="5"/>`).join('');
  return {
    body: `<g transform="${at}">${seg}<circle cx="112" cy="33" r="15"/></g>`,
    detail: `<g transform="${at}">${legs}${dots}` +
      `<rect x="0" y="-3" width="15" height="6" rx="3" transform="translate(106,22) rotate(-113.2)"/>` +
      `<circle cx="100" cy="8" r="3.5"/>` +
      `<rect x="0" y="-3" width="15" height="6" rx="3" transform="translate(118,22) rotate(-61.7)"/>` +
      `<circle cx="125" cy="9" r="3.5"/>` +
      `</g>`,
  };
}

// ── Butterfly + caterpillar parts ─────────────────────────────────────────
// Both drawn as filled shapes only — no strokes — so a digitizer gets closed
// contours to satin-fill rather than centre-lines to guess at.
// Local box 140x110, symmetrical about x=70. Wings are accent, body is ink.
function butterfly(tx, ty, s) {
  const at = (x, y) => `translate(${round(tx + x * s)},${round(ty + y * s)}) scale(${s})`;
  const wingL = [
    `<path d="M70 50 L36 32 Q12 24 10 44 Q8 64 36 68 L70 68 Z"/>`,
    `<path d="M70 72 L46 78 Q22 84 24 96 Q26 107 46 102 L70 88 Z"/>`,
  ].join('');
  return {
    wings: `<g transform="${at(0, 0)}">${wingL}<g transform="translate(140,0) scale(-1,1)">${wingL}</g></g>`,
    body: `<g transform="${at(0, 0)}">` +
      `<rect x="64" y="30" width="12" height="62" rx="6"/>` +
      `<circle cx="70" cy="22" r="8"/>` +
      // antennae: rounded bars pivoted off the head, with a ball at each tip
      `<rect x="0" y="-4" width="22" height="8" rx="4" transform="translate(70,18) rotate(-144.2)"/>` +
      `<circle cx="52" cy="5" r="4.5"/>` +
      `<rect x="0" y="-4" width="22" height="8" rx="4" transform="translate(70,18) rotate(-35.8)"/>` +
      `<circle cx="88" cy="5" r="4.5"/>` +
      `</g>`,
  };
}

// Local box 140x50. Segments are the spine concept's vertebra module rolled
// round — the same shape that makes a vertebral column makes a caterpillar.
function caterpillar(tx, ty, s) {
  const seg = [[14, 32, 9], [32, 27, 10.5], [50, 24, 11.5], [68, 24, 11.5], [86, 27, 11]]
    .map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join('');
  return `<g transform="translate(${round(tx)},${round(ty)}) scale(${s})">` +
    seg +
    `<circle cx="110" cy="29" r="13"/>` +
    `<rect x="0" y="-3" width="15" height="6" rx="3" transform="translate(106,20) rotate(-113.2)"/>` +
    `<circle cx="100" cy="6" r="3.5"/>` +
    `<rect x="0" y="-3" width="15" height="6" rx="3" transform="translate(116,20) rotate(-61.7)"/>` +
    `<circle cx="123" cy="7" r="3.5"/>` +
    `</g>`;
}

// ── Concept 5: Luna ───────────────────────────────────────────────────────
function luna() {
  const W = 480, H = 224, cx = W / 2, s = 0.50;
  const m = lunaMoth(cx - (240 * s) / 2, 4, s);   // moth occupies y 4..104
  return {
    w: W, h: H, label: 'Team Ryan Lee', accentColor: LUNA_GREEN,
    main: [m.body, m.spots, block('TEAM', 24, cx, 114, 20), block('RYAN LEE', 56, cx, 146)].join('\n    '),
    accent: m.wings,
  };
}

// ── Concept 6: Metamorphosis ──────────────────────────────────────────────
// Larva left, moth right — the same animal twice. The progression is carried by
// reading order and the change in scale; no arrow needed.
function metamorphosis() {
  const W = 480, H = 228, cx = W / 2;
  const m = lunaMoth(281, 2, 0.52);    // moth  y 2..106, x 281..406
  const c = lunaLarva(73, 58, 0.72);   // larva y 58..103, x 73..181
  return {
    w: W, h: H, label: 'Team Ryan Lee', accentColor: LUNA_GREEN,
    main: [m.body, m.spots, c.detail, block('TEAM', 24, cx, 118, 20), block('RYAN LEE', 56, cx, 150)].join('\n    '),
    accent: [c.body, m.wings].join('\n    '),
  };
}

// ── Concept 7: Rise ───────────────────────────────────────────────────────
// Larva low on the left, moth high on the right, and the diffuser plume rising
// diagonally between them — the bubbles doing the work of the transformation.
// Creatures in moth green; bubbles in the ink colour so they read as air rather
// than as more of the animal, and so it still stitches in two threads.
function rise() {
  const W = 480, H = 228, cx = W / 2;
  const m = lunaMoth(345, 4, 0.50);     // moth  x 345..465, y 4..104
  const c = lunaLarva(14, 60, 0.75);    // larva x 14..127,  y 60..107
  // Sizes alternate and the line is scattered off true, so the plume reads as
  // bubbles rather than as a dotted leader. Smallest is 1.9mm stitched.
  const plume = [
    [138, 99, 4.5], [157, 90, 6.5], [174, 84, 4], [193, 74, 6], [209, 68, 4.5],
    [228, 58, 7], [246, 52, 4.5], [264, 42, 6], [283, 36, 4], [301, 28, 6.5], [319, 22, 4.5],
  ].map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}"/>`).join('\n    ');
  return {
    w: W, h: H, label: 'Team Ryan Lee', accentColor: LUNA_GREEN,
    main: [m.body, m.spots, c.detail, plume,
           block('TEAM', 24, cx, 118, 20), block('RYAN LEE', 56, cx, 150)].join('\n    '),
    accent: [c.body, m.wings].join('\n    '),
  };
}

const CONCEPTS = {
  varsity: varsity(), roundel: roundel(), bubbles: bubbles(), spine: spine(),
  luna: luna(), metamorphosis: metamorphosis(), rise: rise(),
};

for (const [name, spec] of Object.entries(CONCEPTS)) {
  for (const [way, [ink, goldAccent]] of Object.entries(WAYS)) {
    // A concept may pin its own accent (the Luna marks want moth green, not
    // gold) — but the single-thread cut still collapses to one colour.
    const accent = way === '1color' ? goldAccent : (spec.accentColor ?? goldAccent);
    const body = { main: spec.main, accent: spec.accent.replaceAll("'ACCENT'", accent).replaceAll('ACCENT', accent) };
    const file = `${OUT}/${name}-${way}.svg`;
    fs.writeFileSync(file, svg({ w: spec.w, h: spec.h, label: spec.label, ink, accent, body }));
    console.log('wrote', file.split('/').pop());
  }
}
