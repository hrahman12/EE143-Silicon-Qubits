const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + path.resolve(__dirname, 'handout.html'));
  await p.pdf({ path: path.resolve(__dirname, '../Quantum_Biology_Term_Project.pdf'), format: 'Letter', preferCSSPageSize: true, printBackground: true, displayHeaderFooter: true, headerTemplate: '<span></span>', footerTemplate: '<div style="width:100%;text-align:center;font-family:Times New Roman,serif;font-size:10.3pt;margin-bottom:0.3in"><span class="pageNumber"></span></div>' });
  await b.close();
})();
