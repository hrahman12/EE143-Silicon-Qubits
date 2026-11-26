// Deck checks + notes.md export. Needs the deck served on :8080.
// 1) every number on a slide (and in the notes) appears in the brief (tools/ref/prompt_spec.txt), Lean, or the source links
// 2) the four Lean blocks match tools/lean/*.lean byte for byte
// 3) banned words, on-slide word counts, timings that run 00:00 → 60:00 with no gaps
// 4) writes deck/notes.md
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const spec = fs.readFileSync(path.join(__dirname, 'ref/prompt_spec.txt'), 'utf8');
const leanDir = path.join(__dirname, 'lean');
const leanAll = fs.readdirSync(leanDir).map(f => fs.readFileSync(path.join(leanDir, f), 'utf8')).join('\n');
const norm = s => s.replace(/,(?=\d{3})/g, '');           // 45,000 → 45000
const numsIn = s => (norm(s).match(/\d+(?:\.\d+)?/g) || []);
const specNums = new Set(numsIn(spec));
const BANNED = /\b(revolutionary|game-changing|unlock\w*|leverag\w*|seamless\w*|cutting-edge|paradigm\w*|supercharg\w*)\b|in today's world/i;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('http://localhost:8080/index.html?export', { waitUntil: 'load' });
  const slides = await page.evaluate(() => [...document.querySelectorAll('.reveal .slides > section')].map((s, i) => {
    const c = s.cloneNode(true);
    c.querySelectorAll('*').forEach(e => { if (!e.closest('pre')) e.append(' '); });
    const notes = (c.querySelector('aside.notes') || {}).textContent || '';
    c.querySelectorAll('aside.notes, .ft .n').forEach(e => e.remove());
    const src = (c.querySelector('.ft .src') || {}).textContent || '';
    const srcs = c.querySelector('.srcs'); const links = srcs ? srcs.textContent : '';
    const code = [...c.querySelectorAll('pre.lean')].map(p => ({ name: p.dataset.lean, text: p.textContent }));
    c.querySelectorAll('pre.lean, .ft, .srcs').forEach(e => e.remove());
    const title = s.dataset.title || '';
    return { i: i + 1, title, body: c.textContent.replace(/\s+/g, ' ').trim(), src, notes: notes.trim(), code, links };
  }));
  await browser.close();

  let problems = 0;
  const say = m => { problems++; console.log('  ✗ ' + m); };
  console.log(`slides: ${slides.length}`);

  // 1. numbers
  console.log('\n[numbers not found in the brief]');
  for (const s of slides) {
    const allowed = new Set([...specNums, ...numsIn(leanAll), ...numsIn(s.links)]);
    for (const [where, text] of [['slide', s.body + ' ' + s.src], ['notes', s.notes.replace(/^\[[^\]]*\]/, '')]]) {
      const bad = [...new Set(numsIn(text).filter(n => !allowed.has(n)))];
      if (bad.length) console.log(`  slide ${s.i} ${where}: ${bad.join(', ')}`);
    }
  }

  // 2. Lean
  console.log('\n[Lean blocks]');
  for (const s of slides) for (const c of s.code) {
    const want = fs.readFileSync(path.join(leanDir, c.name + '.lean'), 'utf8').replace(/\n$/, '');
    if (c.text === want) console.log(`  ✓ slide ${s.i}: ${c.name} matches byte for byte (${Buffer.byteLength(want)} bytes)`);
    else say(`slide ${s.i}: ${c.name} differs`);
  }

  // 3. banned words, word counts
  console.log('\n[banned words]');
  for (const s of slides) for (const t of [s.body, s.notes]) { const m = t.match(BANNED); if (m) say(`slide ${s.i}: "${m[0]}"`); }
  console.log('\n[on-slide words, excluding code, footer and tables of sources]');
  for (const s of slides) {
    const w = s.body.split(/\s+/).filter(x => /[A-Za-z]/.test(x)).length;
    if (w > 30) console.log(`  slide ${s.i} (${s.title}): ${w} words`);
  }

  // timings
  console.log('\n[timings]');
  const toS = t => { const [m, s] = t.split(':').map(Number); return m * 60 + s; };
  let prev = 0, timed = 0;
  for (const s of slides) {
    const m = s.notes.match(/^\[(\d\d:\d\d)–(\d\d:\d\d)\]/);
    if (!m) { if (!/^\[backup/.test(s.notes)) say(`slide ${s.i}: notes don't start with a time range`); continue; }
    const a = toS(m[1]), b = toS(m[2]);
    if (a !== prev) say(`slide ${s.i}: starts at ${m[1]}, previous ended at ${Math.floor(prev / 60)}:${prev % 60}`);
    prev = b; timed += b - a;
  }
  console.log(`  timed total ${Math.floor(timed / 60)}:${String(timed % 60).padStart(2, '0')} ${timed === 3600 ? '✓' : '✗'}`);

  // 4. notes.md
  const md = ['# Does Lean say that? · speaker notes', '', 'TriFault · SF Lean Meetup · 60 minutes (50 talk + 10 Q&A). Generated from the `<aside class="notes">` in index.html.', ''];
  for (const s of slides) {
    const m = s.notes.match(/^\[([^\]]*)\]\s*/);
    md.push(`## ${s.i}. ${s.title}`, '', `**Time:** ${m ? m[1] : '—'}`, '', s.notes.replace(/^\[[^\]]*\]\s*/, ''), '');
  }
  fs.writeFileSync(path.join(root, 'deck', 'notes.md'), md.join('\n'));
  console.log(`\nwrote deck/notes.md · ${problems} hard problems`);
})();
