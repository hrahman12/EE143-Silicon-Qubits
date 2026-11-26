// Builds deck/index.html from tools/deck.src.html + tools/slides/*.html.
// tools/order.txt: one slide per line, "name seconds" (seconds = talk time; "backup" = untimed).
// The notes of each timed slide get their [mm:ss–mm:ss] range stamped from that list, so timings always add up.
// {{lean:NAME}} is replaced by tools/lean/NAME.lean, HTML-escaped, so the slides carry the Lean byte for byte.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const mmss = t => `${String(Math.floor(t / 60)).padStart(2, '0')}:${String(t % 60).padStart(2, '0')}`;

const order = fs.readFileSync(path.join(__dirname, 'order.txt'), 'utf8')
  .split('\n').map(l => l.replace(/#.*/, '').trim()).filter(Boolean).map(l => l.split(/\s+/));
let t = 0;
const slides = order.map(([name, dur]) => {
  let html = fs.readFileSync(path.join(__dirname, 'slides', name + '.html'), 'utf8');
  const stamp = dur === 'backup' ? '[backup, not timed]' : `[${mmss(t)}–${mmss(t += +dur)}]`;
  html = html.replace(/<aside class="notes">\s*(\[[^\]]*\]\s*)?/, `<aside class="notes">${stamp} `);
  return html;
});
let html = fs.readFileSync(path.join(__dirname, 'deck.src.html'), 'utf8').replace('<!--slides-->', slides.join('\n'));
html = html.replace(/\{\{lean:(\w+)\}\}/g, (_, name) => {
  const code = fs.readFileSync(path.join(__dirname, 'lean', name + '.lean'), 'utf8').replace(/\n$/, '');
  return `<pre class="lean" data-lean="${name}"><code>${esc(code)}</code></pre>`;
});
fs.writeFileSync(path.join(root, 'deck', 'index.html'), html);
console.log(`wrote deck/index.html: ${order.length} slides, timed ${mmss(t)}`);
