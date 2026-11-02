// Render build/deck.html to a 20-page PDF (1280 x 720 px pages).
// Usage: node report/deck/render_pdf.js build/deck.html docs/briefing.pdf
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const [src, out] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + path.resolve(src));
  await p.waitForFunction(() => window.__done === 1, { timeout: 20000 });
  await p.waitForTimeout(800);
  await p.emulateMedia({ media: 'screen' });
  await p.pdf({ path: out, width: '1280px', height: '720px', printBackground: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 }, preferCSSPageSize: true });
  await b.close();
  if (errs.length) { console.error(errs); process.exit(1); }
  console.log('wrote', out);
})();
