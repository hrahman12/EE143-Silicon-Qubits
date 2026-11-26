// Builds deck/index.html from tools/deck.src.html.
// {{lean:NAME}} is replaced by tools/lean/NAME.lean, HTML-escaped, so the slides carry the Lean byte for byte.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
let html = fs.readFileSync(path.join(__dirname, 'deck.src.html'), 'utf8');
html = html.replace(/<!--include:([\w.\/-]+)-->/g, (_, f) => fs.readFileSync(path.join(__dirname, f), 'utf8'));
html = html.replace(/\{\{lean:(\w+)\}\}/g, (_, name) => {
  const code = fs.readFileSync(path.join(__dirname, 'lean', name + '.lean'), 'utf8').replace(/\n$/, '');
  return `<pre class="lean" data-lean="${name}"><code>${esc(code)}</code></pre>`;
});
fs.writeFileSync(path.join(root, 'deck', 'index.html'), html);
console.log('wrote deck/index.html', html.length, 'bytes');
