// Render SVG files to PNG with headless Chromium.
// usage: node render.js out.png in.svg [scale] [bg]
//        node render.js --batch jobs.json   (jobs: [{in, out, scale, bg}])
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function renderOne(browser, inp, out, scale = 1, bg = null) {
  const svg = fs.readFileSync(inp, 'utf8');
  const m = svg.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/);
  const w = Math.ceil(parseFloat(m[1])), h = Math.ceil(parseFloat(m[2]));
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: scale, reducedMotion: 'reduce' });
  const bgcss = bg ? `background:${bg};` : 'background:transparent;';
  await page.setContent(`<html><body style="margin:0;${bgcss}">${svg}</body></html>`);
  await page.waitForTimeout(150);
  await page.screenshot({ path: out, omitBackground: !bg, clip: { x: 0, y: 0, width: w, height: h } });
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const args = process.argv.slice(2);
  if (args[0] === '--batch') {
    const jobs = JSON.parse(fs.readFileSync(args[1], 'utf8'));
    for (const j of jobs) { await renderOne(browser, j.in, j.out, j.scale || 1, j.bg || null); console.log('rendered', j.out); }
  } else {
    await renderOne(browser, args[1], args[0], parseFloat(args[2] || '1'), args[3] || null);
    console.log('rendered', args[0]);
  }
  await browser.close();
})();
