# paged-report

> Generate professional client-facing HTML reports with perfect A4 print support. Works for any project — drop in your data, get a polished report.

A [Hermes Agent](https://hermes-agent.nousresearch.com) skill that turns structured data into beautiful, printable HTML reports using a shared CSS design system and 14 reusable components.

## Features

- **14 reusable components** — hero, TOC, cards, tables, callouts, KPIs, progress bars, checklists, status rows, compare tables, tags, dividers, footers
- **5 template families** — proposal, data-audit, progress, confirmation, handoff
- **Perfect A4 print** — `@page { size: A4 }`, auto page breaks, table header repeat, orphan/widow control
- **Short page handling** — flex layout auto-fills content to A4 height, footer always at bottom
- **Self-contained HTML** — one file, all CSS inline, no external dependencies
- **PDF via WebBridge** — `save_as_pdf(paper_format: "a4")` on any Chromium browser
- **Bilingual ready** — `lang="zh-CN"` or `lang="en"`, same template
- **Prompt-cache optimized** — static CSS + component spec caches across calls, only data is generated per report

## Quick start (Hermes users)

```bash
# Install
hermes skill install paged-report
```

Then in any Hermes session:

```
User: "帮我做个运费确认发给客户"
Agent: [loads paged-report skill, picks confirmation family, assembles HTML]
```

## Quick start (standalone)

1. Copy `templates/base.css` into a `<style>` tag
2. Pick components from the catalog below
3. Assemble HTML following the skeleton structure
4. Open in browser → Print → Save as PDF (A4)

## Template families

| Family | Use when | Typical length |
|--------|----------|----------------|
| **proposal** | Quote, pricing, service proposal | 3-7 pages |
| **data-audit** | Data quality, catalog audit, CSV analysis | 5-10 pages |
| **progress** | Status update, milestone, weekly report | 2-5 pages |
| **confirmation** | Rule change, shipping, delivery confirmation | 1-2 pages |
| **handoff** | Technical delivery, import prep, acceptance | 2-8 pages |

## Components

| Component | When | Key class |
|-----------|------|-----------|
| Hero | Cover page, always first | `.hero` |
| TOC | 3+ sections | `.toc` |
| Section | Logical content block | `section` |
| Grid + Card | Parallel items | `.grid`, `.card` |
| Callout (4 colors) | Info/success/warning/error | `.callout`, `.green`, `.amber`, `.red` |
| Table | Multi-row data | `table`, auto `thead` repeat |
| Compare Table | Before/after | `.compare-table` |
| Tag | Inline status | `.tag`, `.green`, `.blue`, `.amber`, `.red` |
| KPI | Big number | `.kpi` |
| Progress Bar | Percentage | `.progress-bar` |
| Status Row | Compact list | `.status-row` |
| Checklist | Action items | `.checklist` |
| Footer | Every page | `.footer` |
| Divider | Visual break | `hr` |

See [`templates/component-catalog.html`](templates/component-catalog.html) for a visual reference with all components rendered.

## HTML skeleton

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>{paste base.css here}</style>
</head>
<body>
<div class="page">
  <!-- Cover page -->
  <div class="report-page cover">
    <div class="hero">
      <p class="eyebrow">{client · category}</p>
      <h1>{title}</h1>
      <p class="subtitle">{description}</p>
      <div class="meta">
        <span>{date}</span><span>{version}</span>
      </div>
    </div>
    <nav class="toc">...</nav>
  </div>

  <!-- Content pages -->
  <div class="report-page flex-col">
    <div class="content-area">
      <section id="s1">
        <h2>{section title}</h2>
        {components}
      </section>
    </div>
    <div class="footer-area">
      <div class="footer"><p>{footer text}</p></div>
    </div>
  </div>
</div>
</body>
</html>
```

## A4 print rules

- `@page { size: A4; margin: 18mm 16mm; }` — fixed paper
- `.report-page { min-height: 880px; }` — prevents short pages on screen
- `.flex-col` + `.content-area { flex: 1 }` + `.footer-area { margin-top: auto }` — footer sticks to bottom
- `page-break-inside: avoid` on sections, tables, callouts, checklists
- `thead { display: table-header-group }` — table headers repeat across pages
- `page-break-after: always` — each `.report-page` = one printed page

## PDF generation

### Via Kimi WebBridge (recommended)

```bash
# Navigate to local file (reuses same tab)
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"file:///tmp/report.html"},"session":"report-gen"}'

# Save as A4 PDF
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"save_as_pdf","args":{"paper_format":"a4","print_background":true,"path":"/tmp/report.pdf"},"session":"report-gen"}'
```

### Via Playwright (Python)

```python
from playwright.sync_api import sync_playwright

def to_pdf(html_path, pdf_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path}")
        page.pdf(path=pdf_path, format="A4",
                 margin={"top":"18mm","bottom":"18mm","left":"16mm","right":"16mm"})
        browser.close()
```

### Via browser (manual)

Open HTML → `Cmd/Ctrl + P` → Save as PDF. Paper: A4, Margins: Default.

## Prompt caching (cost optimization)

The design system and component catalog are **static** — they don't change per report. In Hermes, the SKILL.md content is prompt-cached across calls:

- **Cached (fixed cost):** CSS design system, component specs, template families (~3000 tokens)
- **Generated per report:** data content only (~500-1000 tokens)

This means generating 10 reports costs roughly the same as generating 1 report's worth of unique tokens.

## Examples

See [`examples/`](examples/) for sample reports:

- `proposal.html` — A service proposal with pricing tables, timeline, terms
- `confirmation.html` — A shipping rule confirmation with compare table and checklist

## Project structure

```
paged-report/
├── README.md              ← You are here
├── LICENSE                ← MIT
├── SKILL.md               ← Hermes skill definition
├── templates/
│   ├── base.css           ← Design system (inline into reports)
│   └── component-catalog.html  ← Visual component reference
└── examples/
    ├── proposal.html      ← Example: service proposal
    └── confirmation.html  ← Example: rule confirmation
```

## Integration with artifact-delivery

For publishing reports online:

```
paged-report (generate) → artifact-delivery (publish)
```

1. Generate HTML with `paged-report`
2. Register with `artifact-delivery/scripts/register_artifact.py`
3. Deploy with `artifact-delivery/scripts/deploy_artifacts.py`
4. Share the URL

## License

MIT
