const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const BOOK = path.resolve(HERE, '..');
const DOCS = path.resolve(BOOK, '..');
const PROJECT = path.resolve(DOCS, '..');
const NM = 'C:\\Users\\mishrad\\CareerKB\\.book-build\\node_modules';
const SHARED_BUILD =
  'C:\\devdesk\\Copilot\\CopilotSessions\\KnowledgeLedger\\ServiceFabric\\book\\build';

const MarkdownIt = require(path.join(NM, 'markdown-it'));
const anchor = require(path.join(NM, 'markdown-it-anchor'));

const PART_META = {
  '00-onboarding': {
    title: 'Onboarding',
    order: ['principal-engineer-guide.md', 'zero-to-hero-guide.md'],
    blurb:
      'Choose the path that matches your goal: understand the architecture quickly, ' +
      'learn the system from first principles, or prepare to contribute safely.'
  },
  '01-foundations': {
    title: 'Foundations',
    order: ['product-requirements.md', 'visual-identity-and-source-avatar.md'],
    blurb:
      'The product boundary, privacy contract, visual identity, source avatar, and ' +
      'the deliberate choice to build one focused cardboard-head application.'
  },
  '02-architecture': {
    title: 'Architecture',
    order: [
      'system-architecture.md',
      'data-model.md',
      'camera-lifecycle.md',
      'textured-3d-renderer.md',
      'green-screen-compositing.md',
      'ps1-cardboard-renderer.md'
    ],
    blurb:
      'The complete real-time pipeline: capture, immutable state, tracking, filtering, ' +
      'GPU rendering, privacy-safe composition, diagnostics, and OBS presentation.'
  },
  '03-algorithms-and-data-structures': {
    title: 'Algorithms and Data Structures',
    order: [
      'latest-frame-slot.md',
      'condition-variable-synchronization.md',
      'finite-state-lifecycle.md',
      'monotonic-timing-and-fps.md',
      'asynchronous-live-inference.md',
      'blendshape-normalization.md',
      'transformation-matrix-decomposition.md',
      'facial-action-state-machine.md',
      'one-euro-filtering.md',
      'damped-spring-integration.md',
      'low-resolution-overlay-compositing.md'
    ],
    blurb:
      'The mechanisms that keep the avatar fresh, stable, responsive, testable, and ' +
      'visually coherent under concurrent camera and inference workloads.'
  },
  '04-design-principles': {
    title: 'Design Principles',
    order: [
      'latency-over-completeness.md',
      'dependency-inversion.md',
      'immutable-snapshots.md',
      'security-and-secret-boundaries.md'
    ],
    blurb:
      'The engineering values behind the implementation: freshness, narrow boundaries, ' +
      'immutable observations, explicit failures, and fail-closed privacy.'
  },
  '05-camera-ingestion': {
    title: 'Camera Ingestion',
    order: [
      'runtime-flow.md',
      'android-ip-webcam.md',
      'diagnostics-and-performance.md'
    ],
    blurb:
      'How local devices and Android streams are opened, transformed, measured, ' +
      'reconnected, and delivered without building a latency-producing queue.'
  },
  '06-face-tracking': {
    title: 'Face Tracking',
    order: ['normalized-face-state.md', 'live-debugging-and-validation.md'],
    blurb:
      'MediaPipe integration, normalized project contracts, independent eye and mouth ' +
      'signals, calibrated pose, filtering, action events, and live validation.'
  },
  '07-quality-and-testing': {
    title: 'Quality and Testing',
    order: ['validation-evidence.md'],
    blurb:
      'Deterministic tests, GPU checks, hardware probes, privacy validation, measured ' +
      'performance, and the evidence required before behavior is called complete.'
  },
  '08-roadmap': {
    title: 'Roadmap',
    order: [],
    blurb:
      'Completed milestones, remaining production-hardening work, acceptance gates, ' +
      'and the path from a working avatar to a dependable streaming tool.'
  },
  '09-desktop-studio': {
    title: 'Desktop Studio',
    order: [
      'research-and-design.md',
      'interface-specification.md',
      'runtime-architecture.md',
      'tutorial.md'
    ],
    blurb:
      'Native interaction, source-grounded toolkit and layout decisions, live eye calibration, ' +
      'bounded worker ownership, privacy-aware presets, recording, and a complete tutorial.'
  }
};

const APPENDIX_ORDER = [
  'README.md',
  'glossary.md',
  'repository-map.md',
  'command-reference.md'
];

const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'];
const pathToId = new Map();
const missingImages = new Set();
let chapterNumber = 0;
let appendixNumber = 0;

const escapeHtml = value => String(value)
  .replace(/&/g, '&amp;')
  .replace(/</g, '&lt;')
  .replace(/>/g, '&gt;');
const normalizePath = value => path.resolve(value).replace(/\\/g, '/').toLowerCase();
const fileUrl = value =>
  encodeURI('file:///' + path.resolve(value).replace(/\\/g, '/'));
const sourcePath = relative => path.join(DOCS, relative);
const excluded = name => /^(instructions|plan)\.md$/i.test(name);
const leadingNumber = name => {
  const match = name.match(/^(\d+)/);
  return match ? parseInt(match[1], 10) : Number.POSITIVE_INFINITY;
};
const compareNames = (left, right) => {
  const leftNumber = leadingNumber(left);
  const rightNumber = leadingNumber(right);
  return leftNumber !== rightNumber
    ? leftNumber - rightNumber
    : left.localeCompare(right);
};

function stripFrontMatter(markdown) {
  return markdown.replace(/^---\s*\r?\n[\s\S]*?\r?\n---\s*\r?\n/, '');
}

const EMOJI =
  /[\u200D\uFE0F\u2300-\u27BF\u2B00-\u2BFF\u{1F000}-\u{1FAFF}]/gu;
const cleanTitle = value => String(value)
  .replace(/`/g, '')
  .replace(/^\s*\d+\s*[\u00b7.\-\u2014:]\s*/, '')
  .replace(EMOJI, '')
  .replace(/\s+([)\].,;:])/g, '$1')
  .replace(/\s{2,}/g, ' ')
  .trim();

function firstHeading(absolutePath) {
  const markdown = stripFrontMatter(fs.readFileSync(absolutePath, 'utf8'));
  const match = markdown.match(/^#\s+(.+?)\s*#*\s*$/m);
  return cleanTitle(
    match ? match[1] : path.basename(absolutePath, path.extname(absolutePath))
  );
}

function markdownFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true })
    .filter(entry =>
      entry.isFile() &&
      entry.name.toLowerCase().endsWith('.md') &&
      !excluded(entry.name)
    )
    .map(entry => entry.name);
}

function orderedFiles(directory, order) {
  const files = markdownFiles(directory);
  const readme = files.filter(name => name.toLowerCase() === 'readme.md');
  const remaining = new Map(
    files
      .filter(name => name.toLowerCase() !== 'readme.md')
      .map(name => [name.toLowerCase(), name])
  );
  const result = [...readme];

  order.forEach(name => {
    const key = name.toLowerCase();
    if (remaining.has(key)) {
      result.push(remaining.get(key));
      remaining.delete(key);
    }
  });

  return result.concat(
    Array.from(remaining.values()).sort(compareNames)
  );
}

function chapter(relative, title) {
  chapterNumber++;
  const absolute = sourcePath(relative);
  const id = 'ch' + String(chapterNumber).padStart(2, '0');
  pathToId.set(normalizePath(absolute), id);
  return {
    id,
    label: 'Chapter ' + chapterNumber,
    title: title || firstHeading(absolute),
    absolute,
    appendix: false
  };
}

function appendix(relative, title) {
  const letter = String.fromCharCode(65 + appendixNumber++);
  const absolute = sourcePath(relative);
  const id = 'apx' + letter;
  pathToId.set(normalizePath(absolute), id);
  return {
    id,
    label: 'Appendix ' + letter,
    title: title || firstHeading(absolute),
    absolute,
    appendix: true
  };
}

const markdown = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: false
});
markdown.use(anchor, {
  permalink: false,
  slugify: text => text
    .toLowerCase()
    .replace(/[^\w]+/g, '-')
    .replace(/^-+|-+$/g, '')
});

const defaultFence = markdown.renderer.rules.fence.bind(markdown.renderer.rules);
markdown.renderer.rules.fence = (tokens, index, options, environment, renderer) => {
  const language = (tokens[index].info || '').trim().toLowerCase();
  if (language === 'mermaid') {
    return '<pre class="mermaid">' +
      escapeHtml(tokens[index].content) +
      '</pre>\n';
  }
  return defaultFence(tokens, index, options, environment, renderer);
};

function resolveImage(baseDirectory, rawSource) {
  let decodedSource = rawSource.split('#')[0];
  try {
    decodedSource = decodeURIComponent(decodedSource);
  } catch {
    // Keep the literal path so the missing-image check reports it clearly.
  }
  const absolute = path.resolve(baseDirectory, decodedSource);
  if (!fs.existsSync(absolute)) missingImages.add(absolute);
  return fileUrl(absolute);
}

function postProcess(html, baseDirectory) {
  html = html.replace(
    /<a\s+href="([^"]*)"([^>]*)>([\s\S]*?)<\/a>/g,
    (whole, href, attributes, text) => {
      if (/^(https?:|mailto:)/i.test(href)) {
        return '<a href="' + href + '"' + attributes + '>' + text + '</a>';
      }
      if (href.startsWith('#')) {
        return '<span class="xref">' + text + '</span>';
      }
      const filePart = href.split('#')[0];
      if (!filePart) return '<span class="xref">' + text + '</span>';

      let decodedFile = filePart;
      try {
        decodedFile = decodeURIComponent(filePart);
      } catch {
        // Use the original value if decoding fails.
      }
      const targetId = pathToId.get(
        normalizePath(path.resolve(baseDirectory, decodedFile))
      );
      return targetId
        ? '<a href="#' + targetId + '">' + text + '</a>'
        : '<span class="xref">' + text + '</span>';
    }
  );

  return html.replace(
    /<img\s+([^>]*?)src="([^"]+)"([^>]*)>/g,
    (whole, before, source, after) => {
      if (/^(https?:|data:|file:)/i.test(source)) return whole;
      return '<img ' + before +
        'src="' + resolveImage(baseDirectory, source) + '"' +
        after + '>';
    }
  );
}

function renderMarkdown(absolutePath) {
  const source = stripFrontMatter(fs.readFileSync(absolutePath, 'utf8'));
  return postProcess(markdown.render(source), path.dirname(absolutePath));
}

const parts = [{
  title: 'Introduction',
  label: 'Introduction',
  kicker: 'Meet the project',
  blurb:
    'A map of the working KardboardCode VTuber, its privacy contract, visual ' +
    'identity, implemented milestone, and the reading paths through this book.',
  chapters: [chapter('README.md', 'KardboardCode VTuber Engineering Book')]
}];

Object.keys(PART_META).sort(compareNames).forEach((folder, index) => {
  const meta = PART_META[folder];
  const directory = sourcePath(folder);
  const files = orderedFiles(directory, meta.order);
  parts.push({
    title: meta.title,
    label: meta.title,
    roman: ROMAN[index],
    blurb: meta.blurb,
    chapters: files.map(file => chapter(path.join(folder, file)))
  });
});

const appendixDirectory = sourcePath('99-appendix');
const appendixFiles = orderedFiles(appendixDirectory, APPENDIX_ORDER);
parts.push({
  title: 'Appendices',
  label: 'Appendices',
  kicker: 'Reference',
  blurb:
    'Commands, vocabulary, repository navigation, and the source-of-truth ' +
    'hierarchy for operating and extending the project.',
  chapters: appendixFiles.map(file =>
    appendix(path.join('99-appendix', file))
  )
});

function chapterLabel(part, item) {
  const kicker = part.roman
    ? 'Part ' + part.roman + ' \u00b7 ' + part.label
    : part.label;
  return '<div class="chaplabel">' +
    '<span class="kick">' + escapeHtml(kicker) + '</span>' +
    '<span class="num">' + escapeHtml(item.label) + '</span>' +
    '<span class="bar"></span></div>';
}

function chapterHtml(part, item) {
  return '<section class="chapter' + (item.appendix ? ' apx' : '') +
    '" id="' + item.id + '">\n' +
    chapterLabel(part, item) + '\n' +
    renderMarkdown(item.absolute) +
    '\n</section>';
}

function partDivider(part) {
  const number = part.roman
    ? 'Part ' + part.roman
    : part.kicker || part.label;
  return '<section class="part">' +
    '<div class="pnum">' + escapeHtml(number) + '</div>' +
    '<div class="pline"></div>' +
    '<h1>' + escapeHtml(part.title) + '</h1>' +
    '<div class="pdesc">' + escapeHtml(part.blurb) + '</div>' +
    '</section>';
}

function chapterDivider(part, item) {
  const kicker = part.roman
    ? 'Part ' + part.roman + ' \u00b7 ' + part.label
    : part.label;
  const number = item.label.replace(/^(Chapter|Appendix)\s+/, '');
  return '<section class="chapdiv' + (item.appendix ? ' apx' : '') +
    '" id="' + item.id + '-t">' +
    '<div class="cd-ghost">' + escapeHtml(number) + '</div>' +
    '<div class="cd-inner">' +
    '<div class="cd-kick">' + escapeHtml(kicker) + '</div>' +
    '<div class="cd-label">' + escapeHtml(item.label) + '</div>' +
    '<h1 class="cd-title">' + escapeHtml(item.title) + '</h1>' +
    '<div class="cd-rule"></div>' +
    '</div></section>';
}

const body = parts.map(part =>
  partDivider(part) + '\n' +
  part.chapters.map(item =>
    chapterDivider(part, item) + '\n' + chapterHtml(part, item)
  ).join('\n')
).join('\n');

if (missingImages.size > 0) {
  throw new Error(
    'Missing referenced images:\n' +
    Array.from(missingImages).map(image => '  ' + image).join('\n')
  );
}

const diagramCount = (body.match(/class="mermaid"/g) || []).length;
const sourceCount = pathToId.size;
const generatedDate = new Date().toLocaleDateString('en-GB', {
  day: 'numeric',
  month: 'long',
  year: 'numeric'
});

const customCover = fs.readdirSync(DOCS)
  .find(name => /^book cover\.png$/i.test(name));
const coverPath = customCover
  ? path.join(DOCS, customCover)
  : path.join(DOCS, 'images', 'kardboardcode-hero.png');
const customCoverHtml = customCover
  ? '<section class="cover cover-image">' +
    '<img class="cover-img" src="' + fileUrl(coverPath) +
    '" alt="KardboardCode VTuber Engineering Handbook"></section>'
  : '<section class="cover">' +
    '<div class="cv-top">KardboardCode Engineering</div>' +
    '<div class="cv-animal"><img src="' + fileUrl(coverPath) +
    '" alt="Synthetic KardboardCode textured 3D avatar"></div>' +
    '<div class="cv-titlewrap">' +
    '<div class="cv-kicker">The architecture and implementation of</div>' +
    '<h1 class="cv-title">KardboardCode<br><span>VTuber</span></h1>' +
    '<div class="cv-sub">Camera ingestion, MediaPipe tracking, real-time ' +
    'algorithms, privacy boundaries, low-poly GPU rendering, compositing, ' +
    'testing, and operations.</div></div>' +
    '<div class="cv-foot"><span class="cv-author">Debashish Mishra</span>' +
    '<span class="cv-imprint">Engineering Handbook<br>' +
    escapeHtml(generatedDate) + '</span></div></section>';

const colophon = '<section class="front" id="colophon">' +
  '<h1>About this book</h1>' +
  '<p class="lede">A living engineering handbook compiled directly from the ' +
  'KardboardCode-VTuber documentation.</p>' +
  '<p>This edition contains <strong>' + sourceCount +
  ' source documents</strong> and <strong>' + diagramCount +
  ' Mermaid diagrams</strong>. It explains the current implementation from ' +
  'product constraints and visual identity through capture, tracking, ' +
  'algorithms, GPU rendering, privacy, testing, and roadmap.</p>' +
  '<div class="callout"><span class="k">Generated from source</span>' +
  'The Markdown documentation remains authoritative. Rebuild this PDF after ' +
  'documentation changes so the printable edition never becomes a separate, ' +
  'manually maintained copy.</div>' +
  '<h2>Privacy boundary</h2>' +
  '<p>The book uses repository documentation and approved synthetic or ' +
  'face-safe visual assets. It must never embed camera credentials, private ' +
  'authenticated URLs, raw face captures, or private regression recordings.</p>' +
  '<p style="color:#5c6b73;font-size:9.5pt">Generated ' +
  escapeHtml(generatedDate) +
  ' &middot; KardboardCode VTuber Engineering Handbook.</p></section>';

const preface = '<section class="front" id="preface">' +
  '<h1>Preface - how to read this book</h1>' +
  '<p class="lede">Use the reading path that matches the work in front of you.</p>' +
  '<p>Start with Onboarding for a guided route. Read Foundations and ' +
  'Architecture to understand the complete system. Use the algorithm and ' +
  'design-principle Parts when changing concurrency, filtering, tracking, or ' +
  'composition. Camera Ingestion and Face Tracking are operational guides. ' +
  'Quality and Testing defines the evidence required before completion.</p>' +
  '<div class="callout warn"><span class="k">Evidence over assumption</span>' +
  'Chapters distinguish implemented behavior, measured runtime evidence, and ' +
  'planned work. When documentation and code conflict, current code and tests ' +
  'win and the book must be corrected.</div></section>';

const tocEntry = (id, text) =>
  '<a class="toc-entry" href="#' + id + '">' +
  '<span class="t">' + escapeHtml(text) + '</span>' +
  '<span class="lead"></span></a>';
let toc = '<section class="toc" id="toc"><h1>Table of Contents</h1>' +
  '<div class="group">Front matter</div>' +
  tocEntry('colophon', 'About this book') +
  tocEntry('preface', 'Preface - how to read this book');
parts.forEach(part => {
  const heading = part.roman
    ? 'Part ' + part.roman + ' \u00b7 ' + part.title
    : part.title;
  toc += '<div class="group">' + escapeHtml(heading) + '</div>';
  part.chapters.forEach(item => {
    toc += tocEntry(
      item.id + '-t',
      item.label + ' - ' + item.title
    );
  });
});
toc += '</section>';

let css = fs.readFileSync(path.join(SHARED_BUILD, 'book.css'), 'utf8');
css = css.replace(
  /content:\s*"MAB Architecture Handbook"/,
  'content: "KardboardCode VTuber Handbook"'
);
css += `
:root {
  --brand: #6b4423;
  --brand2: #9a6738;
  --accent: #6d5dfc;
  --rule: #d8c9b8;
  --soft: #f4eee6;
  --soft2: #f0edf8;
}
section.part {
  background: linear-gradient(160deg, #3c2515 0%, #6b4423 55%, #9a6738 100%);
}
section.part .pnum { color: #e6c9a8; }
section.part .pdesc { color: #f5e8d8; }
.cv-animal img {
  display: block;
  width: 152mm;
  max-height: 142mm;
  object-fit: contain;
  image-rendering: pixelated;
}
table {
  table-layout: fixed;
  break-inside: auto !important;
}
`;
const bootstrap = fs.readFileSync(
  path.join(SHARED_BUILD, 'bootstrap.js'),
  'utf8'
);

const html = '<!doctype html><html lang="en"><head>' +
  '<meta charset="utf-8">' +
  '<title>KardboardCode VTuber Engineering Handbook</title>' +
  '<style>' + css + '</style>' +
  '<script>window.PagedConfig = { auto: false };</script>' +
  '<script src="' +
  fileUrl(path.join(NM, 'pagedjs', 'dist', 'paged.polyfill.js')) +
  '"></script>' +
  '<script src="' +
  fileUrl(path.join(NM, 'mermaid', 'dist', 'mermaid.min.js')) +
  '"></script></head><body>' +
  customCoverHtml + colophon + preface + toc + body +
  '<script>' + bootstrap + '</script></body></html>';

const outputPath = path.join(HERE, 'book.html');
fs.writeFileSync(outputPath, html, 'utf8');
console.log('Wrote ' + outputPath + ' (' + Math.round(html.length / 1024) + ' KB)');
console.log(
  '  parts=' + parts.length +
  '  chapters=' + chapterNumber +
  '  appendices=' + appendixNumber +
  '  source-docs=' + sourceCount +
  '  diagrams=' + diagramCount
);
console.log('  project=' + PROJECT);
