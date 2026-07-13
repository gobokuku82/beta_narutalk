const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle', timeout: 30000 }).catch(e => console.log('goto warn:', e.message));
  await page.waitForTimeout(1800);
  await page.screenshot({ path: '_meta-shot.png', fullPage: false });
  const info = await page.evaluate(() => {
    const body = getComputedStyle(document.body);
    const html = document.documentElement;
    const cards = [...document.querySelectorAll('[class*="rounded"]')].slice(0, 6).map(el => ({
      cls: (el.getAttribute('class') || '').slice(0, 60),
      r: getComputedStyle(el).borderRadius,
    }));
    const btn = document.querySelector('button');
    return {
      htmlDataTheme: html.getAttribute('data-theme'),
      bodyBg: body.backgroundColor,
      bodyColor: body.color,
      firstButton: btn ? { cls: (btn.getAttribute('class')||'').slice(0,50), r: getComputedStyle(btn).borderRadius, bg: getComputedStyle(btn).backgroundColor } : null,
      roundedSamples: cards,
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})().catch(e => { console.error('FATAL', e.message); process.exit(1); });
