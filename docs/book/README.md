# KardboardCode VTuber Engineering Handbook - build pipeline

This folder compiles the Markdown engineering book under `docs\` into:

`docs\KardboardCode-VTuber-Engineering-Handbook.pdf`

## Build

Run from `docs\book\build`:

```powershell
node build.js
node render.js
node overflow-check.js
```

The final command must print:

```text
PAGES_WITH_OVERFLOW=0
```

No local `npm install` is required. The pipeline reuses:

- Node modules from `C:\Users\mishrad\CareerKB\.book-build\node_modules`
- Print CSS and browser bootstrap from
  `C:\devdesk\Copilot\CopilotSessions\KnowledgeLedger\ServiceFabric\book\build`

## Structure

- `docs\README.md` becomes the Introduction.
- Numbered folders `00-*` through `08-*` become Parts I-IX.
- Each folder's `README.md` leads its Part.
- `docs\99-appendix\` becomes Appendices A-D.
- Mermaid fences render to SVG before Paged.js paginates the book.
- Markdown links to included chapters become in-book links.
- Links outside this edition render as italic cross-references.
- Relative images are resolved from their source Markdown file.
- YAML front matter is removed before Markdown rendering.

To add a chapter, place a Markdown file in the appropriate numbered folder and
add it to that folder's `order` array in `PART_META` inside `build.js`. Unlisted
files are still included alphabetically, so content is not silently dropped.

## Files

- `build.js` - discovers chapters and assembles `book.html`.
- `render.js` - renders Mermaid, paginates, writes the PDF and chapter index.
- `overflow-check.js` - checks every printed page for right-edge clipping.
- `chapter-pages.txt` - generated chapter-to-page index.
- `book.html` - generated printable HTML.

