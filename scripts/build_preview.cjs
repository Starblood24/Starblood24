#!/usr/bin/env node
// Capture the actual local HTML layout, including responsive image selection.
const { chromium } = require('playwright');
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');
const assert = require('node:assert/strict');

async function main() {
  const root = resolve(__dirname, '..');
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const results = [];
  try {
    for (const width of [1280, 640, 390, 320]) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route(/^https?:/, route => route.abort());
      await page.goto(pathToFileURL(resolve(root, 'preview/index.html')).href);
      await page.evaluate(() => document.fonts.ready);
      const state = await page.evaluate(() => ({
        width: innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        images: Array.from(document.images, image => ({
          source: image.currentSrc, loaded: image.complete && image.naturalWidth > 0
        })),
        demoLabelVisible: !!Array.from(document.querySelectorAll('.flag')).find(element =>
          element.getBoundingClientRect().width && getComputedStyle(element).display !== 'none')
      }));
      assert.equal(state.scrollWidth, width, `Horizontal overflow at ${width}px`);
      assert(state.images.every(image => image.loaded), `Missing image at ${width}px`);
      assert(state.demoLabelVisible, `Demo label hidden at ${width}px`);
      assert(state.images.some(image => image.source.endsWith('stats_mobile.svg')) === (width <= 640));
      assert(state.images.some(image => image.source.endsWith('pompompurin_idle_poster.png')));
      assert.deepEqual(errors, []);
      if (width === 1280 || width === 390) {
        await page.screenshot({ path: resolve(root, 'preview', width === 1280 ? 'preview.png' : 'mobile.png'), fullPage: true });
      }
      if (width === 1280) {
        await page.locator('.shell > picture').screenshot({ path: resolve(root, 'preview/header_preview.png') });
      }
      await page.emulateMedia({ reducedMotion: 'no-preference' });
      await page.waitForFunction(() => Array.from(document.images).some(image => image.currentSrc.endsWith('pompompurin_idle.gif')));
      results.push({ width, images: state.images.length, overflow: false, reducedMotion: true, animationSelected: true });
      await page.close();
    }
    console.log(JSON.stringify(results, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
