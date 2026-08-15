// One printable letter-size sheet per concept, plus a combined booklet.
// The "actual size" block is rendered at true stitched dimensions, so a printed
// page can be held against a real cap.
const fs = require('fs');
const { chromium } = require('playwright-core');
const D = '/home/user/TradingView/team-ryan-lee';
const OUT = `${D}/print`;
fs.mkdirSync(OUT, { recursive: true });

const svg = (name, cls) =>
  fs.readFileSync(`${D}/${name}.svg`, 'utf8')
    .replace(/ width="[\d.]+" height="[\d.]+"/, '')
    .replace(/<svg /, `<svg class="${cls}" `);

const CONCEPTS = [
  { slug: 'rise', name: 'Rise', blurb:
    'The caterpillar low on the left, the moth high on the right, and the diffuser plume rising between them — the bubbles Ryan was designing doing the work of the change. His tattoos and his engineering in one mark, read left to right and bottom to top.' },
  { slug: 'luna', name: 'Luna', blurb:
    'The moth from Ryan’s tattoo — <i>Actias luna</i>, drawn to the real proportions of the species: the near-straight forewing edge, the eyespots, the feathery antennae, and the long trailing tails. Stitched in moth green.' },
  { slug: 'metamorphosis', name: 'Metamorphosis', blurb:
    'Both tattoos together, in reading order — the caterpillar on the left, the moth on the right. The same animal twice. The change in size carries the idea, so there is no arrow between them.' },
  { slug: 'spine', name: 'Spine', blurb:
    'A vertebral column beside the name, seen from the side and perfectly straight — which is <i>Straight Up Spine &amp; Posture</i> taken literally. The concept tied to the practice rather than to the tattoos.' },
  { slug: 'varsity', name: 'Varsity', blurb:
    'TEAM set small above a full-width RYAN LEE, closed by a rule and a diamond. The plainest of the seven and the one that reads fastest from across a room.' },
  { slug: 'roundel', name: 'Roundel', blurb:
    'A patch-style badge: an RL monogram in a double ring with the full name beneath. Holds together at the smallest size, so it also works on a shirt or a jacket.' },
  { slug: 'bubbles', name: 'Bubbles', blurb:
    'A rising plume drawn from the fine-bubble diffuser Ryan was designing — bubbles leaving one source and spreading as they climb. The concept that points at his engineering work.' },
];

const CSS = `
  @page { size: letter; margin: 0; }
  * { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { margin: 0; font-family: Helvetica, Arial, sans-serif; color: #1B2733; background: #fff; }
  .sheet {
    width: 8.5in; height: 11in; padding: 0.55in 0.6in 0.5in;
    display: flex; flex-direction: column; page-break-after: always; position: relative;
  }
  .sheet:last-child { page-break-after: auto; }

  .top { display: flex; justify-content: space-between; align-items: baseline;
         border-bottom: 1px solid #C9C9C2; padding-bottom: 7px; }
  .top .who { font-size: 8.5pt; letter-spacing: .14em; text-transform: uppercase; color: #7A8592; }
  .top .of  { font-size: 8.5pt; color: #9AA3AE; }

  h1 { font-family: Georgia, "Times New Roman", serif; font-size: 27pt; font-weight: normal;
       margin: 13px 0 0; letter-spacing: -.01em; }
  .blurb { font-size: 10pt; line-height: 1.5; color: #4A5563; margin: 7px 0 0; max-width: 6.1in; }

  .hero { margin-top: 12px; background: #17293F; border-radius: 4px;
          padding: 20px 18px; display: flex; justify-content: center; align-items: center; }
  .hero svg { width: 4.6in; height: auto; }
  .hero.sq svg { width: 1.85in; }

  .pair { margin-top: 10px; display: flex; gap: 10px; }
  .pair > figure { margin: 0; flex: 1; border: 1px solid #D5D5CE; border-radius: 4px; overflow: hidden; }
  .pair .win { padding: 12px 10px; display: flex; justify-content: center; align-items: center; min-height: 0.85in; }
  .pair .khaki { background: #D9CDB4; }
  .pair .one   { background: #3A3A38; color: #F6F1E5; }
  .pair svg { width: 2.1in; height: auto; }
  .pair.sq svg { width: 0.85in; }
  .pair figcaption { font-size: 7.5pt; color: #6B7580; padding: 4px 8px; border-top: 1px solid #E6E6E0; }

  /* True-size block. The dashed rule is the real stitching area on a
     structured six-panel cap front, printed at 1:1. */
  .actual { margin-top: 12px; }
  .actual .lede { font-size: 8pt; letter-spacing: .1em; text-transform: uppercase;
                  color: #7A8592; font-weight: bold; margin: 0 0 6px; }
  .area {
    width: 4.5in; height: 2.25in; border: 1.2px dashed #8C96A1; border-radius: 3px;
    background: #fff; display: flex; justify-content: center; align-items: center;
    position: relative; margin: 0 auto;
  }
  .area svg { width: 4in; height: auto; }
  .area.sq svg { width: auto; height: 1.95in; }
  .dim {
    position: absolute; font-size: 7pt; color: #7A8592; letter-spacing: .04em;
  }
  .dim.w { bottom: -15px; left: 0; right: 0; text-align: center; }
  .dim.h { top: 0; bottom: 0; right: -0.52in; width: 0.5in;
           display: flex; align-items: center; justify-content: center; }
  .actual .tag { font-size: 7.5pt; color: #6B7580; margin: 20px 0 0; text-align: center; }

  .vote { margin-top: auto; border-top: 1px solid #C9C9C2; padding-top: 11px; }
  .vote h2 { font-size: 9pt; letter-spacing: .12em; text-transform: uppercase;
             color: #7A8592; margin: 0 0 9px; font-weight: bold; }
  .fields { display: flex; gap: 16px; align-items: flex-end; font-size: 9.5pt; }
  .fld { flex: 1; }
  .fld span { font-size: 8pt; color: #7A8592; display: block; margin-bottom: 3px; }
  .line { border-bottom: 1px solid #9AA3AE; height: 17px; }
  .boxes { display: flex; gap: 13px; font-size: 9.5pt; padding-bottom: 1px; }
  .boxes label { display: flex; align-items: center; gap: 5px; }
  .bx { width: 13px; height: 13px; border: 1.2px solid #6B7580; border-radius: 2px; display: inline-block; }
  .notes { margin-top: 9px; }
  .notes span { font-size: 8pt; color: #7A8592; }
  .notes .line { margin-top: 6px; }
  .foot { margin-top: 9px; font-size: 7.5pt; color: #9AA3AE; }
`;

const sheet = (c, i, total) => {
  const sq = c.slug === 'roundel' ? ' sq' : '';
  return `<div class="sheet">
    <div class="top">
      <span class="who">Team Ryan Lee &nbsp;·&nbsp; hat artwork</span>
      <span class="of">Concept ${i + 1} of ${total}</span>
    </div>
    <h1>${c.name}</h1>
    <p class="blurb">${c.blurb}</p>

    <div class="hero${sq}">${svg(`${c.slug}-on-dark`, '')}</div>

    <div class="pair${sq}">
      <figure><div class="win khaki">${svg(`${c.slug}-on-light`, '')}</div>
        <figcaption>On a khaki or stone cap</figcaption></figure>
      <figure><div class="win one">${svg(`${c.slug}-1color`, '')}</div>
        <figcaption>One thread only — cheapest to stitch</figcaption></figure>
    </div>

    <div class="actual">
      <p class="lede">Actual size on the hat — printed 1:1</p>
      <div class="area${sq}">
        ${svg(`${c.slug}-on-light`, '')}
        <span class="dim w">4½ in — the full width of a cap front</span>
        <span class="dim h">2¼ in<br>tall</span>
      </div>
      <p class="tag">The dashed line is all the room there is to stitch into.
        Hold this page against a cap to judge it. Shown in dark thread for clarity —
        on a navy cap it stitches as above.</p>
    </div>

    <div class="vote">
      <h2>What do you think?</h2>
      <div class="fields">
        <div class="fld"><span>Your name</span><div class="line"></div></div>
        <div class="boxes">
          <label><i class="bx"></i> Love it</label>
          <label><i class="bx"></i> It&rsquo;s fine</label>
          <label><i class="bx"></i> Not this one</label>
        </div>
      </div>
      <div class="notes"><span>Anything you&rsquo;d change</span><div class="line"></div></div>
      <p class="foot">Still to decide: cap colour, and whether the hat carries a date.</p>
    </div>
  </div>`;
};

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });

  const render = async (html, out) => {
    const file = `${OUT}/_tmp.html`;
    fs.writeFileSync(file, `<style>${CSS}</style>${html}`);
    const page = await browser.newPage();
    await page.goto('file://' + file);
    await page.waitForTimeout(250);
    await page.pdf({ path: out, format: 'Letter', printBackground: true });
    await page.close();
  };

  for (const [i, c] of CONCEPTS.entries()) {
    await render(sheet(c, i, CONCEPTS.length), `${OUT}/${i + 1}-${c.slug}.pdf`);
    console.log('wrote', `${i + 1}-${c.slug}.pdf`);
  }
  await render(CONCEPTS.map((c, i) => sheet(c, i, CONCEPTS.length)).join('\n'),
               `${OUT}/all-seven-concepts.pdf`);
  console.log('wrote all-seven-concepts.pdf');

  fs.unlinkSync(`${OUT}/_tmp.html`);
  await browser.close();
})();
