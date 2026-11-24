---
name: paged-report
description: "Generate client delivery HTML (report, playbook, portal) from one JSON file and one command: A4 print, noindex, offline single file. Triggers: client report, 发给客户, 报价, 进度汇报, 确认函, 操作手册, 后台教程, 文档入口."
version: 2.0.0
status: development
stability: stable
author: Ming Fang
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [reports, html, client, print, a4]
---

# Paged Report

Generate professional client-facing HTML reports with A4-oriented print styles and self-contained HTML. Browser/PDF pagination and physical page count require verification. Works for any client/project — not tied to a specific brand. The current catalog documents 14 entries (10 typed renderer components plus structural hero, TOC, section, and footer); the 5 family labels are accepted metadata values, not family-specific rendering policies.

## Trigger

Any of: "client report", "send report to client", "发给客户", "报价方案", "进度汇报", "确认函", "数据报告", "导入报告", "make a report for", "生成报告", "paged report", "操作手册", "后台教程", "客户手册", "documentation", "playbook", "文档入口", "portal"

## AI calling convention (v2, mandatory)

Client delivery documents are written as **one JSON file + one command**. Do not hand-write HTML or CSS, and do not copy an old HTML file and edit it.

1. Pick the template:
   - `report`: report, problem explanation, quote confirmation, delivery summary (v1 JSON, unchanged; `template` key optional)
   - `playbook`: admin how-to, client operations manual, documentation (intent opener, anchored sections, one card per step, offline search)
   - `portal`: one clean entry page per client listing documents by status (current first, history collapsed)
2. Write the JSON against `schemas/report.schema.json`, `schemas/playbook.schema.json` or `schemas/portal.schema.json`. Start from `examples/confirmation-data.json`, `examples/playbook-data.json` or `examples/portal-data.json`.
3. Render from the repository root (the same command for all three):
   `python3 -m generator.paged_report input.json --output out.html`
4. Open the file to check it, then export a PDF if needed (see "PDF export (native A4 print)").

Every output is one self-contained HTML file (inline CSS, local images inlined as base64, no CDN, works offline by double-click) and carries `<meta name="robots" content="noindex, nofollow">` unless `meta.robots` overrides it. When a document is replaced, keep the old file and URL and re-render it with `meta.superseded_by` pointing at the new file: the old page then shows a banner linking to the current version instead of returning 404.

Shared `meta` fields for all templates: `language`, `title` (required), `client`, `category`, `subtitle`, `date`, `version`, `project`, `footer`, `robots`, `superseded_by`. Links (`superseded_by`, portal `href`) accept relative paths, `#fragments` and http(s) URLs only.

### Playbook minimal shape

```json
{
  "template": "playbook",
  "meta": {"title": "订单退款操作手册", "client": "客户名称", "date": "2026-11-24"},
  "intent": {"problem": "要解决的问题", "outcome": "完成后的效果"},
  "sections": [
    {
      "id": "refund",
      "title": "全额退款",
      "summary": "什么时候用这一节",
      "keywords": ["退款", "退钱", "refund"],
      "steps": [
        {
          "title": "点击 Refund（退款）",
          "path": "Orders（订单） → 订单详情 → Refund（退款）",
          "body": "一步一个动作。空行分段。",
          "image": {"src": "shots/refund.png", "alt": "退款按钮位置", "caption": "截图：订单详情页"},
          "warning": "高风险提示",
          "mistakes": ["常见错误一"],
          "rollback": "如何撤回"
        }
      ]
    }
  ]
}
```

- Section anchors are `id` or a deterministic slug of `title`; step anchors are `<section-id>-step-<n>`. Link to them as `playbook.html#refund`.
- `keywords` feed the search bar: add synonyms and intent words a client would type. Search matches section text plus keywords; all terms must match; Enter jumps to the first hit and highlights it. The search bar is hidden in print.
- Sections may also hold any report `components` (table, checklist, callout, ...).
- `image.src` is a local .png/.jpg/.gif/.webp path relative to the JSON file; the renderer inlines it. Remote image URLs are rejected.

### Portal minimal shape

```json
{
  "template": "portal",
  "meta": {"title": "客户名称 交付文档", "client": "客户名称"},
  "intro": "请以「当前有效」版本为准。",
  "docs": [
    {"title": "退款操作手册", "href": "playbook-refund-v1.html", "type": "playbook", "status": "current", "updated": "2026-11-24"},
    {"title": "运费确认（旧版）", "href": "shipping-v1.html", "type": "report", "status": "superseded"}
  ]
}
```

`type`: report | playbook | data | other. `status`: current | draft | superseded | archived. Current and draft get their own groups; superseded and archived go into a collapsed history block (`"archive_open": true` expands it). The portal has no script and no password field: access control belongs to the hosting layer, never to page JavaScript.

## How it works (report)

1. Identify template family + client/project name
2. Put report content in the structured JSON contract below
3. Render HTML from the paged-report repository root with `python3 -m generator.paged_report input.json --output report.html`
4. Export a PDF with the browser print dialog, Chrome headless or Playwright (see "PDF export (native A4 print)"); verify the resulting PDF
5. Optional: `artifact-delivery` to publish a reviewed preview

## Structured JSON generator

The repository includes a standard-library renderer and the canonical input schema at `schemas/report.schema.json`. Use it for repeatable reports instead of hand-editing a copied HTML file.

Minimal shape:

```json
{
  "family": "confirmation",
  "toc": true,
  "meta": {
    "language": "zh-CN",
    "title": "运费规则确认",
    "client": "客户名称",
    "category": "运营确认",
    "subtitle": "一句话说明",
    "date": "2026-09-07",
    "version": "v1.0"
  },
  "pages": [
    {
      "label": "规则与确认",
      "sections": [
        {
          "id": "rules",
          "title": "规则变更对比",
          "components": [
            {
              "type": "compare_table",
              "columns": ["项目", "变更前", "变更后"],
              "rows": [["免运门槛", "$200", "$150"]]
            }
          ]
        }
      ]
    }
  ]
}
```

Supported component types are `table`, `compare_table`, `callout`, `tag`, `kpi`, `progress`, `status_row`, `checklist`, `grid`, and `divider`; hero, TOC, sections, pages, and footer are generated structurally. Text is escaped by default. Do not put raw HTML, secrets, or unverified customer facts in the JSON.

`data_appendix` and package-level delivery manifests are proposed follow-up contracts, not supported input features in v1.2.1. Do not claim that the renderer provides searchable relational appendices, CSV export, or package registration until a later implementation passes its contract tests; see the review-pending design under `docs/reports/`.

## Accepted family labels (5 metadata values; family-specific rendering policies are not enforced)

| Family | Use when | Planning range (not enforced) |
|--------|----------|---------------|
| **proposal** | Quote, pricing, service proposal, 报价, 方案 | 3-7 |
| **data-audit** | Data quality, catalog audit, CSV analysis, 数据审计 | 5-10 |
| **progress** | Status update, milestone, 项目进展, 周报 | 2-5 |
| **confirmation** | Rule change, shipping, delivery, 确认函, 变更通知 | 1-2 |
| **handoff** | Technical delivery, import prep, 验收, 交付 | 2-8 |

Invoice excluded (accounting standards apply separately).

## CSS: load linked file

```
skill_view(name='paged-report', file_path='templates/base.css')
```

Inline entire CSS into `<style>` tag. Self-contained HTML, no external deps.

## HTML skeleton

```html
<!DOCTYPE html>
<html lang="zh-CN">  <!-- or lang="en" for English -->
<head>
<meta charset="UTF-8">
<title>{report title}</title>
<style>{full base.css content}</style>
</head>
<body>
<div class="page">
  <!-- COVER: hero + optional toc -->
  <div class="report-page cover">
    <div class="hero">
      <p class="eyebrow">{client} · {category}</p>
      <h1>{title}</h1>
      <p class="subtitle">{description}</p>
      <div class="meta">
        <span>{date}</span><span>{version}</span><span>{project}</span>
      </div>
    </div>
    <!-- optional TOC if 3+ sections -->
    <nav class="toc">
      <h2>目录</h2>
      <ol><li><a href="#s1">{section}</a></li></ol>
    </nav>
  </div>

  <!-- CONTENT PAGES: one logical authoring boundary per .report-page -->
  <div class="report-page flex-col">
    <div class="content-area">
      <section id="s1">
        <h2>{section title}</h2>
        {components: tables, callouts, cards, kpis, etc.}
      </section>
    </div>
    <div class="footer-area">
      <div class="footer"><p>{client} · {report type} · {date}</p></div>
    </div>
  </div>
</div>
</body>
</html>
```

Rules:
- Each `.report-page` is a logical authoring boundary with `min-height: 880px` on screen; it is not a guarantee of one physical A4 page
- `flex-col` + `.content-area` + `.footer-area` can push a footer after content when that logical page has spare space; overflow can reflow it
- Multiple `.report-page` divs provide authoring boundaries for multi-page reports
- `cover` class on the first page requests a print break after the cover; verify the target PDF
- Print-only `.page-label, .footer` horizontal padding (`4mm`) prevents left-edge glyph clipping when print mode resets report-page padding
- Self-contained: ALL CSS inline, no external links

## Component catalog (14 documented entries: 10 typed renderer components + 4 structural wrappers)

### Hero — required, cover page only
```html
<div class="hero">
  <p class="eyebrow">{client · category}</p>
  <h1>{main title}</h1>
  <p class="subtitle">{one-line summary}</p>
  <div class="meta"><span>{date}</span><span>{version}</span></div>
</div>
```

### TOC — when 3+ sections
```html
<nav class="toc"><h2>目录</h2>
<ol><li><a href="#s1">{title}</a></li></ol></nav>
```

### Section — logical content block
```html
<section id="s1"><h2>{title}</h2>{content}</section>
```

### Grid + Card — parallel items
```html
<div class="grid two">
  <div class="card"><h3>{title}</h3><p>{body}</p></div>
</div>
```

### Callout — 4 variants
```html
<div class="callout">{info}</div>
<div class="callout green">{success}</div>
<div class="callout amber">{warning}</div>
<div class="callout red">{error}</div>
```

### Table — header-repeat hint on page break; verify target PDF
```html
<table><thead><tr><th>A</th><th>B</th></tr></thead>
<tbody><tr><td>1</td><td><span class="tag green">Done</span></td></tr></tbody></table>
```

### Compare Table — before/after
```html
<table class="compare-table"><thead><tr><th>项目</th><th>旧</th><th>新</th></tr></thead>
<tbody><tr><td>X</td><td class="old">$200</td><td class="new">$150</td></tr></tbody></table>
```

### Tag — inline status
```html
<span class="tag green">完成</span>
<span class="tag amber">进行中</span>
<span class="tag red">待处理</span>
<span class="tag blue">信息</span>
```

### KPI — big number
```html
<div class="kpi">598 <span class="unit">产品</span></div>
```

### Progress Bar
```html
<div class="progress-bar green"><div class="fill" style="width:76%"></div></div>
```

### Status Row — compact list
```html
<div class="status-row">
  <span class="label">{what}</span>
  <span class="value"><span class="tag green">{status}</span></span>
</div>
```

### Checklist — action items
```html
<ul class="checklist">
  <li class="done">已完成</li><li>待完成</li>
</ul>
```

### Footer — generated per logical content page; verify physical placement
```html
<div class="footer"><p>{client} · {type} · {date}</p></div>
```

### Divider
```html
<hr>
```

## PDF export (native A4 print)

The CSS sets `@page { size: A4; margin: 18mm 16mm }` and hides screen-only controls (the playbook search bar) in print. Any Chromium print path gives a clean A4 PDF:

- Manual: open the HTML, press `Cmd/Ctrl + P`, choose A4, Save as PDF. Playbooks also have a "打印 / 保存 PDF" button.
- Chrome headless:
  ```bash
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --no-pdf-header-footer \
    --print-to-pdf=/tmp/report.pdf file:///tmp/report.html
  ```
- Playwright (repeatable checks): `page.goto(file_url)` then `page.pdf(path=..., format="A4", prefer_css_page_size=True, print_background=True)`.

Verify the physical page count and layout of the PDF; a logical `.report-page` is not guaranteed to be one printed page.

## Short page handling

- `.report-page { min-height: 880px }` — fills A4 on screen
- `.flex-col` + `.content-area { flex: 1 }` + `.footer-area { margin-top: auto }` — can push a footer toward the bottom when that logical page has spare space; verify print placement
- Content <30% of page: merge with next section
- Long table: the browser may split it; `thead` repetition is a print hint and must be verified in the target PDF

## Bilingual

Same template, swap text. `lang="zh-CN"` or `lang="en"`. Generate two files if needed.

## Pitfalls

- Always inline CSS — never `<link>` external stylesheet
- A `.report-page` is one logical authoring boundary; do not assume it maps to one printed page or nest page containers
- Hero only on first `.report-page.cover`
- **Long content overflow**: if a section is likely to exceed one A4 page, use the ~880px / ~45–50 line figure only as a rough screen-space planning heuristic, split it into multiple `.report-page` authoring boundaries when practical, and verify the resulting physical PDF. A single `.report-page` with `page-break-after: always` can spill onto a second physical page then force a break, leaving a mostly-blank page.
- Content that needs images: use `<img>` with max-width:100%, CSS handles sizing
- `lang="en"` reports: replace TOC heading `目录` with `Contents`, hero eyebrow with English labels
- Font weights 620/630/650 rely on Inter variable font; fallback stacks (PingFang SC, YaHei) will synthesize — acceptable but worth noting
