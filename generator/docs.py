"""Playbook and portal templates on the shared paged-report design system."""

from __future__ import annotations

import base64
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .paged_report import (
    _MISSING,
    ReportValidationError,
    _boolean,
    _default_css_path,
    _escape,
    _head,
    _is_english,
    _list,
    _mapping,
    _normalize_meta,
    _optional_text,
    _reject_unknown,
    _render_component,
    _required_text,
    _safe_css,
    _safe_href,
    _slug,
    _superseded_banner,
    _validate_component,
)

IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
DOC_TYPES = ("report", "playbook", "data", "other")
DOC_STATUSES = ("current", "draft", "superseded", "archived")

LABELS = {
    "zh": {
        "contents": "目录", "intent": "这份手册解决什么", "problem": "要解决的问题", "outcome": "完成后的效果",
        "step": "第 {n} 步", "path": "操作路径：", "warning": "高风险提示：", "mistakes": "常见错误：",
        "rollback": "如何撤回：", "search": "搜索", "search_hint": "输入关键词定位章节，例如：退款、改价",
        "no_hit": "没有找到匹配的章节，换个说法试试", "print": "打印 / 保存 PDF",
        "current": "当前有效", "draft": "草稿", "superseded": "已被取代", "archived": "已归档",
        "group_current": "当前有效文档", "group_draft": "草稿与待确认", "group_history": "历史版本（{n}）",
        "updated": "更新于", "report": "报告", "playbook": "操作手册", "data": "数据表", "other": "其他",
    },
    "en": {
        "contents": "Contents", "intent": "What this guide solves", "problem": "Problem", "outcome": "Outcome",
        "step": "Step {n}", "path": "Where: ", "warning": "Warning: ", "mistakes": "Common mistakes: ",
        "rollback": "How to undo: ", "search": "Search", "search_hint": "Type a keyword to jump to a section",
        "no_hit": "No matching section. Try another word.", "print": "Print / Save PDF",
        "current": "Current", "draft": "Draft", "superseded": "Superseded", "archived": "Archived",
        "group_current": "Current documents", "group_draft": "Drafts", "group_history": "History ({n})",
        "updated": "Updated", "report": "Report", "playbook": "Playbook", "data": "Data", "other": "Other",
    },
}
STATUS_CLASS = {"current": "tag green", "draft": "tag blue", "superseded": "tag amber", "archived": "tag"}

# Static script: reads only the rendered DOM and writes with textContent, so no data is interpolated here.
SEARCH_SCRIPT = """(function(){
var q=document.getElementById('pb-q'),out=document.getElementById('pb-results');
function norm(t){return String(t||'').normalize('NFKC').toLowerCase();}
var idx=[].map.call(document.querySelectorAll('.pb-section'),function(s){
return {id:s.id,title:s.getAttribute('data-title'),text:norm(s.getAttribute('data-keywords')+' '+s.textContent)};});
function flash(el){el.classList.remove('pb-hit');void el.offsetWidth;el.classList.add('pb-hit');
setTimeout(function(){el.classList.remove('pb-hit');},2200);}
function go(id){var el=document.getElementById(id);if(!el)return;out.hidden=true;
el.scrollIntoView({behavior:'smooth',block:'start'});history.replaceState(null,'','#'+id);flash(el);}
function hits(){var terms=norm(q.value).split(/\\s+/).filter(Boolean);
return terms.length?idx.filter(function(e){return terms.every(function(t){return e.text.indexOf(t)>-1;});}):null;}
q.addEventListener('input',function(){var h=hits();out.textContent='';out.hidden=!h;if(!h)return;
if(!h.length){var li=document.createElement('li');li.textContent=out.getAttribute('data-empty');out.appendChild(li);return;}
h.forEach(function(e){var li=document.createElement('li'),a=document.createElement('a');
a.href='#'+e.id;a.textContent=e.title;li.appendChild(a);out.appendChild(li);});});
q.addEventListener('keydown',function(ev){if(ev.key==='Enter'){var h=hits();if(h&&h.length)go(h[0].id);}
if(ev.key==='Escape'){q.value='';out.hidden=true;}});
document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('.pb-results a,.toc a,.pb-rail a');
if(a){ev.preventDefault();go(dec(a.getAttribute('href').slice(1)));}
if(ev.target.closest&&ev.target.closest('.pb-print'))window.print();});
function dec(h){try{return decodeURIComponent(h);}catch(e){return h;}}
function onHash(){var t=location.hash&&document.getElementById(dec(location.hash.slice(1)));if(t)flash(t);}
window.addEventListener('hashchange',onHash);onHash();
var rail=[].slice.call(document.querySelectorAll('.pb-rail a'));
if(rail.length&&'IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){
if(!e.isIntersecting)return;rail.forEach(function(a){if(a.getAttribute('href')==='#'+e.target.id)a.setAttribute('aria-current','true');
else a.removeAttribute('aria-current');});});},{rootMargin:'-15% 0px -70% 0px'});
idx.forEach(function(e){io.observe(document.getElementById(e.id));});}
})();"""


def _labels(meta: Mapping[str, Any]) -> dict[str, str]:
    return LABELS["en" if _is_english(meta) else "zh"]


def _css() -> str:
    templates = _default_css_path().parent
    return _safe_css(
        templates.joinpath("base.css").read_text(encoding="utf-8")
        + "\n"
        + templates.joinpath("docs.css").read_text(encoding="utf-8")
    )


def _paragraphs(text: str, css_class: str = "") -> str:
    class_attr = f' class="{css_class}"' if css_class else ""
    return "".join(
        f"<p{class_attr}>{_escape(chunk.strip())}</p>"
        for chunk in re.split(r"\n\s*\n", text)
        if chunk.strip()
    )


def _hero(meta: Mapping[str, Any]) -> list[str]:
    eyebrow = " · ".join(part for part in (meta["client"], meta["category"]) if part)
    parts = ['<div class="hero">', f'<p class="eyebrow">{_escape(eyebrow)}</p>', f'<h1>{_escape(meta["title"])}</h1>']
    if meta["subtitle"]:
        parts.append(f'<p class="subtitle">{_escape(meta["subtitle"])}</p>')
    values = [value for value in (meta["date"], meta["version"], meta["project"]) if value]
    if values:
        parts.append('<div class="meta">' + "".join(f"<span>{_escape(v)}</span>" for v in values) + "</div>")
    parts.append("</div>")
    return parts


def _image_src(src: str, field: str, base_dir: Path) -> str:
    if re.fullmatch(r"data:image/(png|jpeg|gif|webp);base64,[A-Za-z0-9+/=\s]+", src):
        return src
    if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:|//", src):
        raise ReportValidationError(f"{field} must be a local image path or data:image base64 URI")
    root = base_dir.resolve()
    path = (root / src).resolve()
    if root not in path.parents:  # resolved path must stay inside the JSON folder (blocks ../ and outside absolute paths)
        raise ReportValidationError(f"{field} must stay inside the folder of the input JSON")
    mime = IMAGE_TYPES.get(path.suffix.lower())
    if not mime:
        raise ReportValidationError(f"{field} must be a .png, .jpg, .gif or .webp file")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ReportValidationError(f"{field} cannot be read: {src}") from exc
    return f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}"


def _text_list(value: Any, field: str) -> list[str]:
    return [_required_text(item, f"{field}[{i}]") for i, item in enumerate(_list(value, field))]


def _normalize_step(value: Any, field: str, base_dir: Path) -> dict[str, Any]:
    step = _mapping(value, field)
    _reject_unknown(step, {"title", "path", "body", "image", "warning", "mistakes", "rollback"}, field)
    out: dict[str, Any] = {"title": _required_text(step.get("title", _MISSING), f"{field}.title")}
    for key in ("path", "body", "warning", "rollback"):
        out[key] = _optional_text(step.get(key, _MISSING), f"{field}.{key}")
    out["mistakes"] = _text_list(step.get("mistakes", []), f"{field}.mistakes")
    out["image"] = None
    if "image" in step:
        image = _mapping(step["image"], f"{field}.image")
        _reject_unknown(image, {"src", "alt", "caption"}, f"{field}.image")
        out["image"] = {
            "src": _image_src(_required_text(image.get("src", _MISSING), f"{field}.image.src"), f"{field}.image.src", base_dir),
            "alt": _required_text(image.get("alt", _MISSING), f"{field}.image.alt"),
            "caption": _optional_text(image.get("caption", _MISSING), f"{field}.image.caption"),
        }
    return out


def _normalize_playbook(data: Any, base_dir: Path) -> dict[str, Any]:
    data = _mapping(data, "playbook")
    _reject_unknown(data, {"template", "meta", "intent", "toc", "sections"}, "playbook")
    meta = _normalize_meta(data.get("meta"))
    intent = _mapping(data.get("intent"), "intent")
    _reject_unknown(intent, {"problem", "outcome"}, "intent")
    sections = _list(data.get("sections", _MISSING), "sections")
    if not sections:
        raise ReportValidationError("sections must contain at least one section")
    used: set[str] = set()
    normalized = []
    for index, value in enumerate(sections):
        field = f"sections[{index}]"
        section = _mapping(value, field)
        _reject_unknown(section, {"id", "title", "summary", "keywords", "components", "steps"}, field)
        title = _required_text(section.get("title", _MISSING), f"{field}.title")
        section_id = _slug(_optional_text(section.get("id", _MISSING), f"{field}.id", title), f"section-{index + 1}")
        if section_id in used:
            raise ReportValidationError(f"duplicate section id: {section_id}")
        used.add(section_id)
        steps = [
            _normalize_step(s, f"{field}.steps[{i}]", base_dir)
            for i, s in enumerate(_list(section.get("steps", []), f"{field}.steps"))
        ]
        step_ids = {f"{section_id}-step-{n}" for n in range(1, len(steps) + 1)}
        if step_ids & used:  # generated step anchors share the page's id namespace
            raise ReportValidationError(f"section id collides with a step anchor: {sorted(step_ids & used)[0]}")
        used |= step_ids
        normalized.append(
            {
                "id": section_id,
                "title": title,
                "summary": _optional_text(section.get("summary", _MISSING), f"{field}.summary"),
                "keywords": _text_list(section.get("keywords", []), f"{field}.keywords"),
                "components": [
                    _validate_component(c, f"{field}.components[{i}]")
                    for i, c in enumerate(_list(section.get("components", []), f"{field}.components"))
                ],
                "steps": steps,
            }
        )
    return {
        "meta": meta,
        "intent": {
            "problem": _required_text(intent.get("problem", _MISSING), "intent.problem"),
            "outcome": _required_text(intent.get("outcome", _MISSING), "intent.outcome"),
        },
        "toc": _boolean(data.get("toc", _MISSING), "toc", True),
        "sections": normalized,
    }


def _render_step(step: Mapping[str, Any], step_id: str, number: int, labels: Mapping[str, str]) -> str:
    parts = [
        f'<li class="pb-step" id="{_escape(step_id)}">',
        f'<p class="pb-step-no">{_escape(labels["step"].format(n=number))}</p>',
        f'<h3>{_escape(step["title"])}</h3>',
    ]
    if step["path"]:
        parts.append(f'<p class="pb-path"><strong>{labels["path"]}</strong><code>{_escape(step["path"])}</code></p>')
    if step["body"]:
        parts.append(_paragraphs(step["body"]))
    if step["image"]:
        image = step["image"]
        caption = f'<figcaption>{_escape(image["caption"])}</figcaption>' if image["caption"] else ""
        parts.append(f'<figure><img src="{_escape(image["src"])}" alt="{_escape(image["alt"])}">{caption}</figure>')
    if step["warning"]:
        parts.append(f'<div class="callout red pb-warning"><strong>{labels["warning"]}</strong>{_escape(step["warning"])}</div>')
    if step["mistakes"]:
        items = "".join(f"<li>{_escape(m)}</li>" for m in step["mistakes"])
        parts.append(f'<div class="callout amber pb-mistakes"><strong>{labels["mistakes"]}</strong><ul>{items}</ul></div>')
    if step["rollback"]:
        parts.append(f'<div class="callout green pb-rollback"><strong>{labels["rollback"]}</strong>{_escape(step["rollback"])}</div>')
    parts.append("</li>")
    return "".join(parts)


def render_playbook(data: Mapping[str, Any], base_dir: Path | None = None) -> str:
    """Render an operations playbook: intent, anchored sections, step cards and offline search."""
    playbook = _normalize_playbook(data, base_dir or Path.cwd())
    meta = playbook["meta"]
    labels = _labels(meta)
    parts = [
        *_head(meta, _css()),
        "<body>",
        '<div class="page doc" data-template="playbook">',
        _superseded_banner(meta),
        # search sits before the cover so it is on the first screen and sticks from scrollY=0
        '<div class="pb-search" role="search">',
        f'<label for="pb-q">{labels["search"]}</label>',
        f'<input id="pb-q" type="search" placeholder="{labels["search_hint"]}" autocomplete="off">',
        f'<button type="button" class="pb-print">{labels["print"]}</button>',
        f'<ul id="pb-results" class="pb-results" hidden data-empty="{labels["no_hit"]}"></ul>',
        "</div>",
        '<div class="report-page cover doc-cover">',
        *_hero(meta),
        f'<h2 class="pb-intent-title">{labels["intent"]}</h2>',
        '<div class="grid two pb-intent">',
        f'<div class="card"><h3>{labels["problem"]}</h3>{_paragraphs(playbook["intent"]["problem"])}</div>',
        f'<div class="card"><h3>{labels["outcome"]}</h3>{_paragraphs(playbook["intent"]["outcome"])}</div>',
        "</div>",
    ]
    if playbook["toc"]:
        parts.append(f'<nav class="toc"><h2>{labels["contents"]}</h2><ol>')
        parts.extend(
            f'<li><a href="#{_escape(s["id"])}">{_escape(s["title"])}</a></li>' for s in playbook["sections"]
        )
        parts.append("</ol></nav>")
    parts.append("</div>")
    if playbook["toc"]:  # wide-screen side rail; the cover TOC above stays the printed one
        parts.append(f'<nav class="pb-rail" aria-label="{labels["contents"]}"><p>{labels["contents"]}</p><ol>')
        parts.extend(
            f'<li><a href="#{_escape(s["id"])}">{_escape(s["title"])}</a></li>' for s in playbook["sections"]
        )
        parts.append("</ol></nav>")
    parts.append('<main class="report-page doc-main">')
    for section in playbook["sections"]:
        parts.append(
            f'<section id="{_escape(section["id"])}" class="pb-section" data-title="{_escape(section["title"])}"'
            f' data-keywords="{_escape(" ".join(section["keywords"]))}">'
        )
        parts.append(f'<h2>{_escape(section["title"])}</h2>')
        if section["summary"]:
            parts.append(_paragraphs(section["summary"], "pb-summary"))
        parts.extend(_render_component(c) for c in section["components"])
        if section["steps"]:
            parts.append('<ol class="pb-steps">')
            parts.extend(
                _render_step(step, f'{section["id"]}-step-{n}', n, labels)
                for n, step in enumerate(section["steps"], start=1)
            )
            parts.append("</ol>")
        parts.append("</section>")
    parts.extend(
        [
            f'<div class="footer"><p>{_escape(meta["footer"])}</p></div>',
            "</main>",
            "</div>",
            f"<script>{SEARCH_SCRIPT}</script>",
            "</body>",
            "</html>",
        ]
    )
    return "".join(parts)


def _normalize_portal(data: Any) -> dict[str, Any]:
    data = _mapping(data, "portal")
    _reject_unknown(data, {"template", "meta", "intro", "archive_open", "docs"}, "portal")
    docs = _list(data.get("docs", _MISSING), "docs")
    if not docs:
        raise ReportValidationError("docs must contain at least one document")
    normalized = []
    for index, value in enumerate(docs):
        field = f"docs[{index}]"
        doc = _mapping(value, field)
        _reject_unknown(doc, {"title", "href", "type", "status", "updated", "summary"}, field)
        doc_type = _optional_text(doc.get("type", _MISSING), f"{field}.type", "report")
        status = _optional_text(doc.get("status", _MISSING), f"{field}.status", "current")
        if doc_type not in DOC_TYPES:
            raise ReportValidationError(f"{field}.type must be one of {', '.join(DOC_TYPES)}")
        if status not in DOC_STATUSES:
            raise ReportValidationError(f"{field}.status must be one of {', '.join(DOC_STATUSES)}")
        normalized.append(
            {
                "title": _required_text(doc.get("title", _MISSING), f"{field}.title"),
                "href": _safe_href(doc.get("href", _MISSING), f"{field}.href"),
                "type": doc_type,
                "status": status,
                "updated": _optional_text(doc.get("updated", _MISSING), f"{field}.updated"),
                "summary": _optional_text(doc.get("summary", _MISSING), f"{field}.summary"),
            }
        )
    return {
        "meta": _normalize_meta(data.get("meta")),
        "intro": _optional_text(data.get("intro", _MISSING), "intro"),
        "archive_open": _boolean(data.get("archive_open", _MISSING), "archive_open"),
        "docs": normalized,
    }


def _doc_card(doc: Mapping[str, Any], labels: Mapping[str, str]) -> str:
    parts = [
        f'<article class="doc-card status-{doc["status"]}">',
        '<p class="doc-badges">',
        f'<span class="{STATUS_CLASS[doc["status"]]}">{labels[doc["status"]]}</span>',
        f'<span class="tag">{labels[doc["type"]]}</span>',
        "</p>",
        f'<h3><a href="{_escape(doc["href"])}">{_escape(doc["title"])}</a></h3>',
    ]
    if doc["summary"]:
        parts.append(f'<p>{_escape(doc["summary"])}</p>')
    if doc["updated"]:
        parts.append(f'<p class="doc-updated">{labels["updated"]} {_escape(doc["updated"])}</p>')
    parts.append("</article>")
    return "".join(parts)


def render_portal(data: Mapping[str, Any]) -> str:
    """Render a per-client document index grouped by status. No script, no client-side gate."""
    portal = _normalize_portal(data)
    meta = portal["meta"]
    labels = _labels(meta)
    by_status = {s: [d for d in portal["docs"] if d["status"] == s] for s in DOC_STATUSES}
    parts = [
        *_head(meta, _css()),
        "<body>",
        '<div class="page doc" data-template="portal">',
        _superseded_banner(meta),
        '<main class="report-page doc-main portal">',
        *_hero(meta),
    ]
    if portal["intro"]:
        parts.append(_paragraphs(portal["intro"], "portal-intro"))
    for status, key in (("current", "group_current"), ("draft", "group_draft")):
        if by_status[status]:
            parts.append(f'<section class="portal-group" id="{status}"><h2>{labels[key]}</h2><div class="portal-grid">')
            parts.extend(_doc_card(d, labels) for d in by_status[status])
            parts.append("</div></section>")
    history = by_status["superseded"] + by_status["archived"]
    if history:
        open_attr = " open" if portal["archive_open"] else ""
        parts.append(
            f'<details class="portal-archive" id="history"{open_attr}><summary>{labels["group_history"].format(n=len(history))}</summary><div class="portal-grid">'
        )
        parts.extend(_doc_card(d, labels) for d in history)
        parts.append("</div></details>")
    parts.extend(
        [f'<div class="footer"><p>{_escape(meta["footer"])}</p></div>', "</main>", "</div>", "</body>", "</html>"]
    )
    return "".join(parts)
