---
name: paged-report
description: "Generate client HTML reports with A4 print via WebBridge. Triggers: client report, 发给客户, 报价, 进度汇报, 确认函."
version: 1.1.0
metadata:
  hermes:
    tags: [reports, html, client, print, a4]
---

# Paged Report

Generate professional client-facing HTML reports with perfect A4 print support. Works for any client/project — not tied to a specific brand. One self-contained HTML file, 14 reusable components, 5 template families.

## Trigger

Any of: "client report", "send report to client", "发给客户", "报价方案", "进度汇报", "确认函", "数据报告", "导入报告", "make a report for", "生成报告", "paged report"

## How it works

1. Identify template family + client/project name
2. Pick components from catalog below
3. Assemble HTML → write to `/tmp/report-{project}-{type}.html`
4. WebBridge `navigate(file://)` + `save_as_pdf(paper_format: "a4")`
5. Optional: `artifact-delivery` to publish

**One reusable tab**: `session: "report-gen"` — navigate → save_as_pdf → repeat.

## Template families (5 universal types)

| Family | Use when | Typical pages |
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

  <!-- CONTENT PAGES: one .report-page per A4 page -->
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
- Each `.report-page` = one A4 page (`min-height: 880px` on screen)
- `flex-col` + `.content-area` + `.footer-area` pushes footer to bottom
- Multiple `.report-page` divs for multi-page reports
- `cover` class on first page (forces page-break-after in print)
- Self-contained: ALL CSS inline, no external links

## 14 Components

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

### Table — auto header repeat on page break
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

### Footer — every page
```html
<div class="footer"><p>{client} · {type} · {date}</p></div>
```

### Divider
```html
<hr>
```

## PDF via WebBridge

```bash
# Navigate (reuses same tab)
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"file:///tmp/report.html"},"session":"report-gen"}'

# Save A4 PDF
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"save_as_pdf","args":{"paper_format":"a4","print_background":true,"path":"/tmp/report.pdf"},"session":"report-gen"}'
```

## Short page handling

- `.report-page { min-height: 880px }` — fills A4 on screen
- `.flex-col` + `.content-area { flex: 1 }` + `.footer-area { margin-top: auto }` — footer to bottom
- Content <30% of page: merge with next section
- Long table: auto page break, `thead` repeats

## Bilingual

Same template, swap text. `lang="zh-CN"` or `lang="en"`. Generate two files if needed.

## Pitfalls

- Always inline CSS — never `<link>` external stylesheet
- One `.report-page` = one printed page — don't nest
- Hero only on first `.report-page.cover`
- WebBridge: reuse `session: "report-gen"`, don't create new session per report
- Content that needs images: use `<img>` with max-width:100%, CSS handles sizing
