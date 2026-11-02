const path = require('path');

const NM = 'C:\\Users\\mishrad\\CareerKB\\.book-build\\node_modules';
const puppeteer = require(path.join(NM, 'puppeteer'));
const htmlPath = 'file:///' +
  path.join(__dirname, 'book.html').replace(/\\/g, '/');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--allow-file-access-from-files',
      '--font-render-hinting=none'
    ]
  });
  const page = await browser.newPage();

  await page.goto(htmlPath, { waitUntil: 'load', timeout: 180000 });
  await page.waitForFunction('window.__BOOK_READY__ === true', {
    timeout: 900000
  });

  const failures = await page.evaluate(() => {
    const tolerance = 2;
    const results = [];
    const pages = Array.from(document.querySelectorAll('.pagedjs_page'));

    pages.forEach((printedPage, index) => {
      const area = printedPage.querySelector('.pagedjs_area') || printedPage;
      const areaBounds = area.getBoundingClientRect();
      const rightEdge = areaBounds.right;
      const pageNumber =
        parseInt(printedPage.getAttribute('data-page-number'), 10) ||
        index + 1;

      area.querySelectorAll(
        'pre, table, img, figure, svg, code, p, td, th, ' +
        'h1, h2, h3, h4, li, blockquote'
      ).forEach(element => {
        Array.from(element.getClientRects())
          .filter(bounds =>
            bounds.bottom > areaBounds.top &&
            bounds.top < areaBounds.bottom &&
            bounds.right > areaBounds.left &&
            bounds.left < areaBounds.right
          )
          .forEach(bounds => {
            if (bounds.width === 0 || bounds.height === 0) return;
            const overflow = bounds.right - rightEdge;
            if (overflow > tolerance) {
              results.push({
                page: pageNumber,
                tag: element.tagName.toLowerCase(),
                overflow: Math.round(overflow),
                text: (element.textContent || '')
                  .replace(/\s+/g, ' ')
                  .trim()
                  .slice(0, 70)
              });
            }
          });
      });
    });

    return results;
  });

  const byPage = {};
  failures.forEach(failure => {
    (byPage[failure.page] = byPage[failure.page] || []).push(failure);
  });

  const pages = Object.keys(byPage).map(Number).sort((a, b) => a - b);
  console.log('PAGES_WITH_OVERFLOW=' + pages.length);
  pages.forEach(pageNumber => {
    byPage[pageNumber]
      .sort((a, b) => b.overflow - a.overflow)
      .slice(0, 3)
      .forEach(failure => {
        console.log(
          'p.' + String(pageNumber).padStart(3) +
          '  +' + String(failure.overflow).padStart(4) + 'px' +
          '  <' + failure.tag + '>  "' + failure.text + '"'
        );
      });
  });

  await browser.close();
  if (pages.length > 0) process.exit(1);
})().catch(error => {
  console.error(error);
  process.exit(1);
});
