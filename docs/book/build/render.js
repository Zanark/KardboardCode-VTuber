const fs = require('fs');
const path = require('path');

const NM = 'C:\\Users\\mishrad\\CareerKB\\.book-build\\node_modules';
const puppeteer = require(path.join(NM, 'puppeteer'));

const HERE = __dirname;
const DOCS = path.resolve(HERE, '..', '..');
const htmlPath = path.join(HERE, 'book.html');
const outputPath = process.argv[2] ||
  path.join(DOCS, 'KardboardCode-VTuber-Engineering-Handbook.pdf');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--allow-file-access-from-files',
      '--font-render-hinting=none'
    ]
  });
  const page = await browser.newPage();

  let mermaidFailures = 0;
  page.on('console', message => {
    const text = message.text();
    if (text.startsWith('MERMAID_FAIL')) {
      mermaidFailures++;
      console.log('  [diagram] ' + text);
    } else if (
      text.startsWith('BOOK_READY') ||
      text.startsWith('BOOTSTRAP_ERROR')
    ) {
      console.log('  [page] ' + text);
    }
  });
  page.on('pageerror', error => console.log('  [pageerror] ' + error.message));

  console.log('Loading ' + htmlPath);
  await page.goto('file:///' + htmlPath.replace(/\\/g, '/'), {
    waitUntil: 'load',
    timeout: 180000
  });
  await page.waitForFunction('window.__BOOK_READY__ === true', {
    timeout: 900000
  });

  const pages = await page.evaluate('window.__PAGES__ || 0');
  console.log(
    'Paged.js produced ' + pages +
    ' pages; mermaid failures: ' + mermaidFailures
  );

  if (mermaidFailures > 0) {
    throw new Error('Mermaid rendering failed for ' + mermaidFailures + ' diagram(s).');
  }

  const chapterPages = await page.evaluate(() => {
    const allPages = Array.from(document.querySelectorAll('.pagedjs_page'));
    const pageNumber = element => {
      const printedPage = element.closest('.pagedjs_page');
      if (!printedPage) return null;
      const dataNumber = printedPage.getAttribute('data-page-number');
      return dataNumber
        ? parseInt(dataNumber, 10)
        : allPages.indexOf(printedPage) + 1;
    };
    const text = (element, selector) => {
      const node = element.querySelector(selector);
      return node ? node.textContent.trim() : '';
    };
    return Array.from(document.querySelectorAll('section.chapdiv')).map(
      element => ({
        kick: text(element, '.cd-kick'),
        label: text(element, '.cd-label'),
        title: text(element, '.cd-title'),
        page: pageNumber(element)
      })
    );
  });

  const indexPath = path.join(HERE, 'chapter-pages.txt');
  fs.writeFileSync(
    indexPath,
    'KardboardCode VTuber Engineering Handbook - chapter title pages\n' +
      '(page numbers are the printed folio in the PDF)\n\n' +
      chapterPages.map(chapter =>
        'p.' + String(chapter.page).padStart(3) + '\t' +
        chapter.label + '\t' + chapter.title + '\t' + chapter.kick
      ).join('\n') +
      '\n',
    'utf8'
  );

  await page.pdf({
    path: outputPath,
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: false,
    margin: 0
  });

  await browser.close();
  console.log('Wrote ' + outputPath);
})().catch(error => {
  console.error(error);
  process.exit(1);
});
