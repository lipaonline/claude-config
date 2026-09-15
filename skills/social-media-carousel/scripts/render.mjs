#!/usr/bin/env node
// Render a carousel JSON into PNG slides (+ optional PDF for LinkedIn).
// Zero dependencies: uses a locally installed Chrome/Chromium/Edge/Brave in headless mode.
//
//   node scripts/render.mjs carousel.json [--out ./out] [--pdf] [--no-png] [--html-only] [--scale 1]
//
// Output: <out>/index.html (all slides, printable), <out>/slide-01.png …, <out>/carousel.pdf (with --pdf).

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';

const args = process.argv.slice(2);
const input = args.find(a => !a.startsWith('--'));
if (!input) { console.error('usage: node render.mjs carousel.json [--out dir] [--pdf] [--no-png] [--html-only] [--scale N]'); process.exit(1); }
const opt = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const flag = name => args.includes(name);
const out = resolve(opt('--out', join(dirname(resolve(input)), 'out')));
const scale = Number(opt('--scale', '1'));
const wantPdf = flag('--pdf');
const wantPng = !flag('--no-png') && !flag('--html-only');

const here = dirname(fileURLToPath(import.meta.url));
const template = readFileSync(join(here, '..', 'assets', 'template.html'), 'utf8');
const data = JSON.parse(readFileSync(input, 'utf8'));
if (!Array.isArray(data.slides) || data.slides.length === 0) { console.error('carousel.json needs a non-empty "slides" array'); process.exit(1); }

// Resolve relative image paths against the JSON file location so file:// URLs work.
for (const s of data.slides) {
  if (s.type === 'image' && s.src && !/^(https?:|data:|file:)/.test(s.src)) s.src = pathToFileURL(resolve(dirname(resolve(input)), s.src)).href;
}

const SIZES = { instagram: [1080, 1350], linkedin: [1080, 1350], square: [1080, 1080], tiktok: [1080, 1920], story: [1080, 1920], wide: [1920, 1080] };
const [w, h] = SIZES[data.format] || SIZES.instagram;

mkdirSync(out, { recursive: true });
const html = template.replace('__DATA__', JSON.stringify(data).replace(/<\//g, '<\\/'));
const htmlPath = join(out, 'index.html');
writeFileSync(htmlPath, html);
console.log(`html  → ${htmlPath}`);
if (flag('--html-only')) process.exit(0);

function findChrome() {
  if (process.env.CHROME_PATH && existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const candidates = process.platform === 'darwin' ? [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
  ] : process.platform === 'win32' ? [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  ] : ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium', '/usr/bin/microsoft-edge'];
  const found = candidates.find(p => existsSync(p));
  if (found) return found;
  for (const bin of ['google-chrome', 'chromium', 'chromium-browser', 'chrome']) {
    try { return execFileSync(process.platform === 'win32' ? 'where' : 'which', [bin], { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim().split('\n')[0]; } catch {}
  }
  return null;
}
const chrome = findChrome();
if (!chrome) { console.error('No Chrome/Chromium found. Set CHROME_PATH=/path/to/chrome, or open out/index.html and export manually.'); process.exit(2); }

const base = ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
              '--disable-extensions', '--run-all-compositor-stages-before-draw', '--virtual-time-budget=1500'];
if (process.platform === 'linux') base.push('--no-sandbox');
const run = extra => execFileSync(chrome, [...base, ...extra], { stdio: ['ignore', 'ignore', 'pipe'] });

const fileUrl = pathToFileURL(htmlPath).href;
if (wantPng) {
  for (let i = 1; i <= data.slides.length; i++) {
    const png = join(out, `slide-${String(i).padStart(2, '0')}.png`);
    run([`--window-size=${w},${h}`, `--force-device-scale-factor=${scale}`, `--screenshot=${png}`, `${fileUrl}?slide=${i}`]);
    console.log(`png   → ${png}`);
  }
}
if (wantPdf) {
  const pdf = join(out, 'carousel.pdf');
  run([`--window-size=${w},${h}`, '--no-pdf-header-footer', `--print-to-pdf=${pdf}`, fileUrl]);
  console.log(`pdf   → ${pdf}`);
}
