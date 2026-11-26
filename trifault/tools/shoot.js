// Screenshot slides at 1920x1080 and run layout checks.
// usage: node tools/shoot.js <outdir> [first] [last]   (1-based, inclusive)
const { chromium } = require('playwright');
const path = require('path');
const [outdir, first = '1', last = '999'] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('requestfailed', r => errs.push('FAILED ' + r.url()));
  page.on('request', r => { const u = r.url(); if (!u.startsWith('http://localhost') && !u.startsWith('data:')) errs.push('EXTERNAL ' + u); });
  await page.goto('http://localhost:8080/index.html', { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(() => Reveal.getTotalSlides());
  const a = Math.max(1, +first), b = Math.min(total, +last);
  for (let i = a; i <= b; i++) {
    await page.evaluate(i => Reveal.slide(i - 1, 0, 1000), i);
    await page.waitForTimeout(700);
    const issues = await page.evaluate(() => {
      const sec = Reveal.getCurrentSlide();
      const out = [];
      const W = 1920, H = 1080, M = 128, FOOT = 1080 - 72;
      sec.querySelectorAll('*').forEach(el => {
        if (el.closest('aside.notes')) return;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) return;
        const inFooter = el.closest('.ft');
        const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
        if (hasText) {
          const fs = parseFloat(cs.fontSize);
          const small = el.closest('.ft, .credit, .srcs, .cite, sub, sup') ;
          if (fs < 24 && !small) out.push(`font ${fs}px: "${el.textContent.trim().slice(0, 40)}"`);
        }
        if (!inFooter && (r.bottom > FOOT + 0.5)) out.push(`past footer (${Math.round(r.bottom)}): <${el.tagName.toLowerCase()} class="${el.className}"> "${(el.textContent||'').trim().slice(0, 40)}"`);
        if (r.right > W - M + 1 || r.left < M - 1) {
          if (!el.closest('.bleed')) out.push(`outside margins (${Math.round(r.left)}–${Math.round(r.right)}): <${el.tagName.toLowerCase()} class="${el.className}">`);
        }
        if (el.scrollWidth > el.clientWidth + 1 && ['PRE','P','DIV','TD','SPAN','H2','H1','LI'].includes(el.tagName) && cs.overflow !== 'visible')
          out.push(`clipped horizontally: <${el.tagName.toLowerCase()} class="${el.className}"> "${(el.textContent||'').trim().slice(0, 40)}"`);
      });
      return [...new Set(out)];
    });
    const file = path.join(outdir, `s${String(i).padStart(2, '0')}.png`);
    await page.screenshot({ path: file });
    console.log(`slide ${i}: ${issues.length ? issues.join('\n   ') : 'ok'}`);
  }
  if (errs.length) console.log('page errors:\n ' + [...new Set(errs)].join('\n '));
  await browser.close();
})();
