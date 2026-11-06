import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = path.join(ROOT, 'build', 'gui-visual-reference');
const MANIFEST = path.join(BUILD, 'capture-manifest.json');
const OUTPUT = path.join(ROOT, 'docs', 'KardboardCode-Studio-GUI-Visual-Reference.html');
const NM = process.env.KARDBOARD_BOOK_NODE_MODULES ||
  'C:\\Users\\mishrad\\CareerKB\\.book-build\\node_modules';
const MarkdownIt = require(path.join(NM, 'markdown-it'));
const puppeteer = require(path.join(NM, 'puppeteer'));
const escape = value => String(value).replace(/[&<>"']/g, c => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[c]);
const hash = buffer => crypto.createHash('sha256').update(buffer).digest('hex');
const slug = value => value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const citation = source => `${source.file}:${source.line} (${source.symbol})`;

const DIAGRAMS = [
  `flowchart TD
    Studio["Current native Studio"] --> Pages["8 settings pages"]
    Pages --> Sections["Every named expanded section / scroll parts"]
    Sections --> Controls["45 runtime controls / represented output-size selector"]
    Studio --> Views["Work modes / Tools / diagnostics / menus / selectors"]
    Studio --> Dialogs["Tutorial / calibration / consent / controlled file pickers"]
    Controls --> Capture["Owned-widget screenshots in both themes"]
    Views --> Capture
    Dialogs --> Capture
    Capture --> Receipt["Coverage and PNG hash receipt"]
    classDef default fill:#2d333b,stroke:#6d5dfc,color:#e6edf3`,
  `sequenceDiagram
    autonumber
    participant Fixture as Synthetic capture fixture
    participant Studio as Native Studio widgets
    participant Receipt as Coverage receipt
    participant Builder as Reference builder
    participant Reader as Offline browser
    Fixture->>Studio: Select named view and safe example values
    Studio->>Fixture: Owned widget pixels, not the desktop
    Fixture->>Receipt: PNG bytes, sources, visible controls and view IDs
    Builder->>Receipt: Check both themes and every declared surface
    Builder->>Builder: Render navigation diagrams and embed all PNG bytes
    Builder->>Reader: One self-contained HTML file
    Reader->>Reader: Search, filter, expand and inspect screenshots offline`,
];

const CSS = `
:root{color-scheme:dark;--bg:#11251f;--panel:#19332b;--ink:#fff4db;--muted:#c2cfb9;--line:#5d7c68;--accent:#9ce3bc;--kraft:#d5a568}
:root[data-theme=light]{color-scheme:light;--bg:#f3e7cc;--panel:#fff4db;--ink:#19332b;--muted:#4d6251;--line:#a68c64;--accent:#276447}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Segoe UI",sans-serif}
main{max-width:1500px;margin:auto;padding:24px}h1,h2,h3{line-height:1.25}h1{font-size:clamp(27px,4vw,44px);margin:6px 0}
h2{font-size:25px}h3{font-size:19px}a{color:var(--accent)}code{overflow-wrap:anywhere;font-size:.9em}
.hero,.panel,.reference-group{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px;margin-bottom:20px;box-shadow:0 0 25px #9ce3bc08}
.eyebrow{font-size:11px;letter-spacing:.1em;color:var(--kraft);font-weight:700}.muted,figcaption{color:var(--muted)}
.notice{border-left:4px solid var(--kraft);padding:8px 14px;background:var(--panel)}.toolbar{position:sticky;top:0;z-index:5;display:flex;gap:10px;flex-wrap:wrap;background:var(--bg);padding:12px 0;border-bottom:1px solid var(--line);margin-bottom:18px}
button,input,select{font:inherit;color:var(--ink);background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:9px 12px}
button{cursor:pointer;box-shadow:0 0 15px #9ce3bc0c}button:hover,button:focus-visible{border-color:var(--accent);box-shadow:0 0 12px #9ce3bc30}
input{flex:1;min-width:180px}button svg{width:18px;height:18px;vertical-align:-3px;margin-right:5px}
.index{display:flex;gap:8px;flex-wrap:wrap}.index a{border:1px solid var(--line);border-radius:8px;padding:5px 10px;text-decoration:none}
.reference-group{padding:0;overflow:hidden}.reference-group>summary{padding:18px 22px;font-size:22px;font-weight:650;cursor:pointer}
.group-body{padding:0 18px 18px}.view{border-top:1px solid var(--line);padding:14px 0}.shots,.diagrams{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
figure{margin:0;min-width:0}figure img{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:8px;cursor:zoom-in}
figcaption{padding:8px 3px;font-size:13px}.source{display:block;font-size:11px;overflow-wrap:anywhere}.diagram{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;overflow:auto}
.diagram svg{max-width:100%;height:auto}.counts{display:flex;gap:12px;flex-wrap:wrap}.count{border:1px solid var(--line);border-radius:10px;padding:10px 16px}
.count strong{font-size:24px;display:block}.count span{font-size:12px;color:var(--muted)}table{border-collapse:collapse;width:100%;margin:16px 0}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}
.table-wrap{overflow:auto}pre{max-width:100%;overflow:auto;padding:14px;background:var(--bg);border:1px solid var(--line);border-radius:8px}
dialog{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:14px;max-width:96vw;max-height:96vh;padding:14px}
dialog::backdrop{background:#000b}dialog img{display:block;max-width:90vw;max-height:78vh;width:auto;height:auto}dialog header{display:flex;justify-content:space-between;gap:20px;align-items:center}
[hidden]{display:none!important}.footer{font-size:12px;color:var(--muted)}.error{color:#f2b48c}
@media(max-width:700px){main{padding:12px}.hero,.panel{padding:16px}.shots,.diagrams{grid-template-columns:1fr}.toolbar{gap:7px}button,input,select{padding:8px;font-size:13px}.reference-group>summary{font-size:19px}dialog img{max-width:85vw}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
@media print{.toolbar,.index,dialog{display:none}.reference-group{break-inside:auto}.view{break-inside:avoid}body{background:white;color:black}}
`;

const JS = `
const root=document.documentElement,search=document.querySelector('#search'),filter=document.querySelector('#photo-theme');
const groups=[...document.querySelectorAll('.reference-group')],views=[...document.querySelectorAll('.view')];
function update(){
 const query=search.value.trim().toLowerCase(),theme=filter.value;let visible=0;
 for(const view of views){
  const matches=!query||view.dataset.search.includes(query);
  for(const figure of view.querySelectorAll('figure'))figure.hidden=theme!=='all'&&figure.dataset.theme!==theme;
  view.hidden=!matches||![...view.querySelectorAll('figure')].some(f=>!f.hidden);
  if(!view.hidden)visible++;
 }
 for(const group of groups){group.hidden=![...group.querySelectorAll('.view')].some(v=>!v.hidden);if(query&&!group.hidden)group.open=true;}
 document.querySelector('#result-count').textContent=visible+' named screenshot views shown';
 document.querySelector('#empty').hidden=visible>0;
}
search.addEventListener('input',update);filter.addEventListener('change',update);
document.querySelector('#theme-toggle').addEventListener('click',()=>{root.dataset.theme=root.dataset.theme==='light'?'dark':'light';});
document.querySelector('#expand').addEventListener('click',()=>groups.forEach(g=>g.open=true));
document.querySelector('#collapse').addEventListener('click',()=>groups.forEach(g=>g.open=false));
document.querySelector('#refresh').addEventListener('click',()=>location.reload());
const lightbox=document.querySelector('#lightbox'),large=lightbox.querySelector('img'),title=lightbox.querySelector('strong');
function openImage(image){large.src=image.src;large.alt=image.alt;title.textContent=image.alt;lightbox.showModal();}
for(const image of document.querySelectorAll('figure img')){
 image.addEventListener('click',()=>openImage(image));
 image.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();openImage(image);}});
}
document.querySelector('#close-image').addEventListener('click',()=>lightbox.close());
lightbox.addEventListener('close',()=>large.removeAttribute('src'));update();window.__REFERENCE_READY__=true;
`;

function loadManifest() {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
  if (manifest.schemaVersion !== 1 || !manifest.syntheticOnly) throw new Error('Invalid capture receipt');
  const ids = new Set();
  for (const image of manifest.screenshots) {
    if (ids.has(image.id)) throw new Error('Duplicate screenshot: ' + image.id);
    ids.add(image.id);
    const bytes = fs.readFileSync(path.join(BUILD, image.file));
    if (hash(bytes) !== image.sha256 || bytes.length !== image.bytes) {
      throw new Error('Screenshot bytes do not match receipt: ' + image.id);
    }
    if (bytes.readUInt32BE(16) !== image.width || bytes.readUInt32BE(20) !== image.height) {
      throw new Error('PNG dimensions do not match receipt: ' + image.id);
    }
  }
  for (const [filename, expected] of Object.entries(manifest.sourceHashes)) {
    if (hash(fs.readFileSync(path.join(ROOT, filename))) !== expected) {
      throw new Error('Captured GUI source is stale: ' + filename);
    }
  }
  for (const theme of ['dark', 'light']) {
    const images = manifest.screenshots.filter(i => i.theme === theme);
    for (const [category, expected] of Object.entries(manifest.expected)) {
      const covered = new Set(images.flatMap(i => i.coverage[category] || []));
      const missing = expected.filter(value => !covered.has(value));
      if (missing.length) throw new Error(theme + ' missing ' + category + ': ' + missing.join(', '));
    }
    const controls = new Set(images.flatMap(i => [...i.visibleControls, ...i.representedControls]));
    const missing = manifest.runtimeControls.filter(name => !controls.has(name));
    if (missing.length) throw new Error(theme + ' missing visible controls: ' + missing.join(', '));
  }
  if (new Set(manifest.sources.map(s => s.file)).size < 5) {
    throw new Error('Reference needs at least five verified source files');
  }
  return manifest;
}

async function renderDiagrams() {
  const browser = await puppeteer.launch({ headless: 'new' });
  try {
    const page = await browser.newPage();
    await page.setContent('<html><body></body></html>');
    await page.addScriptTag({
      content: fs.readFileSync(path.join(NM, 'mermaid', 'dist', 'mermaid.min.js'), 'utf8'),
    });
    return await page.evaluate(async diagrams => {
      mermaid.initialize({
        startOnLoad: false, securityLevel: 'strict', theme: 'dark',
        themeVariables: {
          primaryColor: '#2d333b', primaryBorderColor: '#6d5dfc',
          primaryTextColor: '#e6edf3', lineColor: '#8b949e',
          secondaryColor: '#161b22', tertiaryColor: '#161b22',
        },
      });
      const results = [];
      for (let index = 0; index < diagrams.length; index++) {
        const result = await mermaid.render('reference-diagram-' + index, diagrams[index]);
        results.push(result.svg);
      }
      return results;
    }, DIAGRAMS);
  } finally {
    await browser.close();
  }
}

function narrative(manifest, diagrams) {
  const sources = manifest.sources.map(s => '- `' + citation(s) + '`').join('\n');
  const rows = Object.entries(manifest.expected).map(([category, values]) =>
    `| ${category} | ${values.length} | Every declared name in both themes |`).join('\n');
  // The authored page is Markdown; the deliverable embeds the compiled page and all images.
  const markdownSource = `---
title: "KardboardCode Studio - Complete GUI Visual Reference"
description: "Every named Studio section, view and dialog in a portable native screenshot reference."
---

## Overview

This reference answers "where is that view?" without hiding a long settings section below
the viewport. It contains real owned-widget screenshots, not mockups or desktop captures.
The application source and screenshot bytes are recorded together.

Synthetic avatar/landmark fixtures and example paths are used throughout. Calibration and
busy/error/progress scenes are explicitly illustrative. Controlled Qt file-picker specimens
do not promise the exact appearance of your normal operating-system picker.

## Architecture

The left inspector, protected viewer, right-hand diagnostic rail and viewer-only Tools footer
are built by \`src\\kardboard_vtuber\\gui\\window.py\` (see verified source references below).
Every section is captured through all required scroll parts. The two hidden output-size
fields are represented by their actual resolution selector.

<div class="diagrams"><div class="diagram">${diagrams[0]}</div><div class="diagram">${diagrams[1]}</div></div>

## Core components and coverage

| Surface | Named surfaces | Coverage |
|---|---:|---|
${rows}

All ${manifest.runtimeControls.length} runtime controls are either fully visible in a screenshot
or explicitly represented by the native output-resolution selector. This is coverage of the
current named GUI surfaces, not every numeric value, resizing combination or OS dialog variant.

## Data flow and capture integrity

The capture tool selects real native widgets, uses \`QWidget.grab()\`, records visible control
regions, and hashes each PNG. The builder checks those bytes and app-source hashes before
embedding them. Raw camera pixels, credentials, personal calibration and desktop captures
are not inputs. The shipped file makes no external image/script/network requests.

## Implementation and regeneration

From the source checkout, use the established Python 3.12 GUI environment:

\`\`\`powershell
.\u005c.venv312\u005cScripts\u005cpython.exe scripts\u005ccapture_gui_visual_reference.py
node scripts\u005cbuild_gui_visual_reference.mjs
node scripts\u005cbuild_gui_visual_reference.mjs --check
\`\`\`

Native captures require Windows and the existing GUI/rendering dependencies. The builder
reuses the same local Markdown/Mermaid/Puppeteer modules as the engineering handbook.
The final HTML needs only a browser. Refresh reloads the saved reference, not the camera/tool.

## References

${sources}
`;
  const markdown = new MarkdownIt({ html: true, linkify: false });
  return {
    source: markdownSource,
    html: markdown.render(markdownSource.replace(/^---\n[\s\S]*?\n---\n/, '')),
  };
}

function gallery(manifest) {
  const groups = new Map();
  for (const image of manifest.screenshots) {
    if (!groups.has(image.group)) groups.set(image.group, new Map());
    const views = groups.get(image.group);
    const id = image.id.replace(/-(dark|light)$/, '');
    if (!views.has(id)) views.set(id, []);
    views.get(id).push(image);
  }
  const index = [...groups.keys()].map(group =>
    `<a href="#group-${slug(group)}">${escape(group)}</a>`).join('');
  const content = [...groups].map(([group, views], groupIndex) => {
    const articles = [...views].map(([id, images]) => {
      const title = images[0].title;
      const search = [group, title, ...images.flatMap(i => i.visibleControls)].join(' ').toLowerCase();
      const figures = images.map(image => {
        const bytes = fs.readFileSync(path.join(BUILD, image.file)).toString('base64');
        const alt = `${image.title} / ${image.theme} theme / ${image.mode}`;
        return `<figure data-theme="${image.theme}" data-image-id="${escape(image.id)}">
<img src="data:image/png;base64,${bytes}" alt="${escape(alt)}" width="${image.width}" height="${image.height}" loading="lazy" tabindex="0" role="button" aria-label="Inspect ${escape(alt)}">
<figcaption><strong>${escape(image.theme.toUpperCase())} / ${escape(image.mode)}</strong> ${escape(image.note)}
<span class="source">${image.sources.map(citation).map(escape).join(' · ')}</span></figcaption></figure>`;
      }).join('');
      return `<article class="view" id="view-${escape(id)}" data-search="${escape(search)}">
<h3>${escape(title)}</h3><div class="shots">${figures}</div></article>`;
    }).join('');
    return `<details class="reference-group" id="group-${slug(group)}" ${groupIndex === 0 ? 'open' : ''}>
<summary>${escape(group)} <span class="muted">/ ${views.size} views</span></summary>
<div class="group-body">${articles}</div></details>`;
  }).join('\n');
  return { index, content, viewCount: [...groups.values()].reduce((n, g) => n + g.size, 0) };
}

async function build() {
  const manifest = loadManifest();
  const diagrams = await renderDiagrams();
  const prose = narrative(manifest, diagrams);
  const images = gallery(manifest);
  const receipt = JSON.stringify(manifest).replace(/</g, '\\u003c');
  const markdownSource = JSON.stringify(prose.source).replace(/</g, '\\u003c');
  const sun = '<svg viewBox="0 0 24 24" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 1v3m0 16v3M1 12h3m16 0h3M4 4l2 2m12 12 2 2M20 4l-2 2M6 18l-2 2"/></g></svg>';
  const moon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/></svg>';
  const html = `<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Complete native Studio screenshot reference, self-contained and offline.">
<title>KardboardCode Studio - Complete GUI Visual Reference</title><style>${CSS}</style></head><body><main>
<header class="hero"><div class="eyebrow">KARDBOARD / STUDIO / v${escape(manifest.version)}</div>
<h1>Every view. One reference.</h1><p class="muted">Native screenshots of every current named page, section, tab, menu, choice and dialog, in both themes.</p>
<div class="counts"><div class="count"><strong>${images.viewCount}</strong><span>named screenshot views / scroll parts</span></div>
<div class="count"><strong>${manifest.screenshots.length}</strong><span>embedded native screenshots</span></div>
<div class="count"><strong>${manifest.runtimeControls.length}</strong><span>runtime controls visually accounted for</span></div></div>
<p class="notice">Synthetic/example data only. No camera input, personal calibration, recordings, downloads or publication.
This is a saved visual reference, not a live control panel. Captured ${escape(manifest.capturedAt)}.</p></header>
<div class="toolbar" aria-label="Reference controls">
<input id="search" type="search" aria-label="Find a GUI view" placeholder="Find a page, setting, dialog or control...">
<select id="photo-theme" aria-label="Screenshot theme"><option value="all">Both screenshot themes</option><option value="dark">Dark screenshots</option><option value="light">Light screenshots</option></select>
<button id="theme-toggle" type="button" aria-label="Toggle reference dark/light theme">${sun}${moon}Theme</button>
<button id="expand" type="button">Expand all</button><button id="collapse" type="button">Collapse all</button>
<button id="refresh" type="button" title="Reload this saved file; does not refresh or start Studio">Refresh file</button></div>
<nav class="index" aria-label="Screenshot index">${images.index}<a href="#coverage">Coverage and sources</a></nav>
<p id="result-count" class="muted" aria-live="polite"></p><p id="empty" hidden>No views match this filter.</p>
${images.content}
<section class="panel" id="coverage">${prose.html}</section>
<footer class="footer">One file: screenshots, diagrams, styles, controls and coverage receipt are embedded.
Open in a browser; no server or internet is needed. Source and capture tools remain in the repository.</footer>
<dialog id="lightbox" aria-label="Full screenshot"><header><strong>Screenshot</strong><button id="close-image" type="button">Close</button></header><img alt=""></dialog>
<script id="capture-receipt" type="application/json">${receipt}</script>
<script id="reference-markdown" type="application/json">${markdownSource}</script>
<script>${JS}</script></main></body></html>`;
  fs.mkdirSync(path.dirname(OUTPUT), { recursive: true });
  const temporary = OUTPUT + '.tmp';
  fs.writeFileSync(temporary, html, 'utf8');
  fs.renameSync(temporary, OUTPUT);
  console.log(`Wrote ${OUTPUT}: ${manifest.screenshots.length} screenshots, ${images.viewCount} views, ${Buffer.byteLength(html)} bytes`);
}

async function check() {
  const manifest = loadManifest();
  const html = fs.readFileSync(OUTPUT, 'utf8');
  const embedded = [...html.matchAll(/data-image-id="([^"]+)"[\s\S]*?<img src="data:image\/png;base64,([^"]+)"/g)];
  if (embedded.length !== manifest.screenshots.length) throw new Error('Embedded screenshot count mismatch');
  const byId = new Map(manifest.screenshots.map(image => [image.id, image]));
  const found = new Set();
  for (const match of embedded) {
    const image = byId.get(match[1]);
    if (!image || found.has(match[1]) || hash(Buffer.from(match[2], 'base64')) !== image.sha256) {
      throw new Error('Embedded screenshot differs: ' + match[1]);
    }
    found.add(match[1]);
  }
  const portable = path.join(BUILD, 'portable-copy', 'reference.html');
  fs.mkdirSync(path.dirname(portable), { recursive: true });
  fs.copyFileSync(OUTPUT, portable);
  const browser = await puppeteer.launch({ headless: 'new' });
  try {
    const page = await browser.newPage();
    const errors = [];
    const external = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.setRequestInterception(true);
    page.on('request', request => {
      if (/^https?:/i.test(request.url())) {
        external.push(request.url());
        request.abort();
      } else request.continue();
    });
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto(pathToFileURL(portable).href, { waitUntil: 'load', timeout: 120000 });
    await page.waitForFunction('window.__REFERENCE_READY__ === true');
    if (await page.$$eval('figure img', images => images.length) !== manifest.screenshots.length) {
      throw new Error('Browser screenshot count mismatch');
    }
    if (await page.$$eval('.diagram svg', images => images.length) !== 2) {
      throw new Error('Diagram count mismatch');
    }
    await page.click('#theme-toggle');
    if (await page.evaluate(() => document.documentElement.dataset.theme) !== 'light') {
      throw new Error('Theme control failed');
    }
    await page.type('#search', 'calibration');
    if (!await page.evaluate(() => [...document.querySelectorAll('.view')].some(v => !v.hidden))) {
      throw new Error('Search failed');
    }
    await page.$eval('#search', input => { input.value = ''; input.dispatchEvent(new Event('input')); });
    await page.select('#photo-theme', 'dark');
    if (!await page.evaluate(() => [...document.querySelectorAll('figure[data-theme=light]')].every(f => f.hidden))) {
      throw new Error('Screenshot theme filtering failed');
    }
    await page.select('#photo-theme', 'all');
    await page.click('#expand');
    if (!await page.evaluate(() => [...document.querySelectorAll('.reference-group')].every(g => g.open))) {
      throw new Error('Expand control failed');
    }
    await page.click('#collapse');
    await page.$eval('.reference-group', group => { group.open = true; });
    await page.$eval('figure img', async image => { image.loading = 'eager'; await image.decode(); });
    await page.click('figure img');
    if (!await page.$eval('#lightbox', dialog => dialog.open)) throw new Error('Full screenshot failed');
    await page.click('#close-image');
    for (const width of [1440, 390]) {
      await page.setViewport({ width, height: 900 });
      await page.evaluate(() => scrollTo({ top: 0, left: 0, behavior: 'instant' }));
      if (!await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)) {
        throw new Error('Reference overflows viewport at ' + width);
      }
      await page.screenshot({ path: path.join(BUILD, `reference-review-${width}.png`) });
    }
    if (errors.length || external.length) {
      throw new Error(JSON.stringify({ errors, external }));
    }
  } finally {
    await browser.close();
    fs.rmSync(portable);
  }
  console.log(`Reference verified offline: ${manifest.screenshots.length} embedded images, both themes, coverage, diagrams and controls.`);
}

if (process.argv.includes('--check')) await check();
else await build();
