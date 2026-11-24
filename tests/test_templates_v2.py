import base64
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from generator.docs import render_playbook, render_portal
from generator.paged_report import ReportValidationError, main, render, render_report

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
XSS = '<script>alert(1)</script>"\'&'


def load(name):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


class SharedMasterTests(unittest.TestCase):
    def test_all_templates_default_to_noindex_and_viewport(self):
        outputs = [
            render_report(load("confirmation-data.json")),
            render_playbook(load("playbook-data.json"), base_dir=EXAMPLES),
            render_portal(load("portal-data.json")),
        ]
        for html in outputs:
            with self.subTest(html=html[:60]):
                self.assertIn('<meta name="robots" content="noindex, nofollow">', html)
                self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', html)
                self.assertIn("--accent: #1f4e5f", html)  # shared tokens
                self.assertIn("@page { size: A4;", html)
                self.assertNotIn("<link ", html)
                self.assertNotIn("http://", html.split("<style>")[0])

    def test_robots_can_be_overridden_and_is_escaped(self):
        data = load("confirmation-data.json")
        data["meta"]["robots"] = 'index, follow"><x'
        html = render_report(data)
        self.assertIn('<meta name="robots" content="index, follow&quot;&gt;&lt;x">', html)
        self.assertNotIn("noindex", html)

    def test_superseded_banner_on_every_template(self):
        for name, fn in (
            ("confirmation-data.json", render_report),
            ("playbook-data.json", lambda d: render_playbook(d, base_dir=EXAMPLES)),
            ("portal-data.json", render_portal),
        ):
            data = load(name)
            data["meta"]["superseded_by"] = "v3.html?a=1&b=2"
            html = fn(data)
            with self.subTest(name=name):
                self.assertIn('<div class="superseded" role="note">', html)
                self.assertIn('href="v3.html?a=1&amp;b=2"', html)
            del data["meta"]["superseded_by"]
            self.assertNotIn('class="superseded"', fn(data))

    def test_superseded_banner_english(self):
        data = load("confirmation-data.json")
        data["meta"].update(language="en", superseded_by="https://example.com/v3/")
        self.assertIn("This version has been superseded.", render_report(data))

    def test_unsafe_link_schemes_are_rejected(self):
        for href in (
            "javascript:alert(1)", " JaVa\tScript:alert(1)", "data:text/html,x", "vbscript:x",
            "\\\\host\\share", "//evil.example/x", "\\evil.example", "/\\evil.example",
        ):
            with self.subTest(href=href):
                data = load("confirmation-data.json")
                data["meta"]["superseded_by"] = href
                with self.assertRaises(ReportValidationError):
                    render_report(data)
                portal = load("portal-data.json")
                portal["docs"][0]["href"] = href
                with self.assertRaises(ReportValidationError):
                    render_portal(portal)


class ReportCompatibilityTests(unittest.TestCase):
    def test_v1_example_renders_without_script(self):
        html = render_report(load("confirmation-data.json"))
        self.assertNotIn("<script", html)
        self.assertIn('class="report-page cover"', html)

    def test_template_key_is_optional_and_must_be_report(self):
        data = load("confirmation-data.json")
        data["template"] = "report"
        self.assertEqual(render(data), render_report(load("confirmation-data.json")))
        data["template"] = "playbook"
        with self.assertRaises(ReportValidationError):
            render_report(data)

    def test_dispatch_rejects_unknown_template(self):
        with self.assertRaises(ReportValidationError):
            render({"template": "invoice"})


class PlaybookTests(unittest.TestCase):
    def setUp(self):
        self.data = load("playbook-data.json")

    def html(self, data=None):
        return render_playbook(data or self.data, base_dir=EXAMPLES)

    def test_intent_opens_the_document(self):
        html = self.html()
        self.assertLess(html.index("要解决的问题"), html.index('class="pb-section"'))
        self.assertIn("完成后的效果", html)

    def test_sections_get_stable_anchors_and_toc(self):
        html = self.html()
        self.assertIn('<section id="full-refund" class="pb-section"', html)
        self.assertIn('<a href="#full-refund">全额退款</a>', html)
        self.assertIn('<li class="pb-step" id="full-refund-step-2">', html)
        self.assertEqual(html, self.html())  # deterministic

    def test_slug_anchor_when_id_missing_and_duplicates_rejected(self):
        data = copy.deepcopy(self.data)
        del data["sections"][0]["id"]
        self.assertIn('<section id="全额退款" class="pb-section"', self.html(data))
        data["sections"][1]["id"] = "全额退款"
        with self.assertRaises(ReportValidationError):
            self.html(data)
        data = copy.deepcopy(self.data)
        data["sections"][1]["id"] = "full-refund-step-1"  # would duplicate the first section's step anchor
        with self.assertRaises(ReportValidationError):
            self.html(data)

    def test_search_index_and_script(self):
        html = self.html()
        self.assertIn('data-keywords="部分退款 缺货 破损 补偿 partial refund"', html)
        self.assertIn('data-title="订单改价"', html)
        self.assertIn('<input id="pb-q" type="search"', html)
        self.assertEqual(html.count("<script>"), 1)
        script = html.split("<script>")[1].split("</script>")[0]
        self.assertIn("scrollIntoView", script)
        self.assertIn("pb-hit", script)
        self.assertNotIn("innerHTML", script)  # results are written with textContent only

    def test_step_cards_have_path_warning_mistakes_rollback(self):
        html = self.html()
        self.assertIn("第 2 步", html)
        self.assertIn('<p class="pb-path"><strong>操作路径：</strong><code>', html)
        self.assertIn('class="callout red pb-warning"', html)
        self.assertIn('class="callout amber pb-mistakes"', html)
        self.assertIn('class="callout green pb-rollback"', html)
        self.assertIn('<table><thead>', html)  # report components reused

    def test_print_hides_search_and_keeps_steps_whole(self):
        html = self.html()
        self.assertIn(".pb-search, .pb-print { display: none !important; }", html)
        self.assertIn(".pb-step, .doc-card { page-break-inside: avoid; break-inside: avoid; }", html)

    def test_local_image_is_inlined_and_remote_rejected(self):
        uri = self.data["sections"][0]["steps"][0]["image"]["src"]
        self.assertIn(f'<img src="{uri}"', self.html())  # data URI passes through
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "shot.png").write_bytes(base64.b64decode(uri.split(",", 1)[1]))
            data = copy.deepcopy(self.data)
            data["sections"][0]["steps"][0]["image"]["src"] = "shot.png"
            html = render_playbook(data, base_dir=Path(tmp))
            self.assertIn(f'<img src="{uri}"', html)  # relative file inlined to the same bytes
            self.assertNotIn("shot.png", html)
            outside = Path(tmp).parent / "outside-shot.png"
            for src in (
                "https://cdn.example.com/a.png", "//cdn.example.com/a.png", "missing.png", "notes.txt",
                "../outside-shot.png", str(outside), "/etc/hosts.png",
            ):
                data["sections"][0]["steps"][0]["image"]["src"] = src
                with self.subTest(src=src), self.assertRaises(ReportValidationError):
                    render_playbook(data, base_dir=Path(tmp))

    def test_text_is_escaped(self):
        data = copy.deepcopy(self.data)
        data["meta"]["title"] = XSS
        data["intent"]["problem"] = XSS
        section = data["sections"][0]
        section["title"] = XSS
        section["keywords"] = [XSS]
        section["steps"][0].update(path=XSS, body=XSS, warning=XSS, rollback=XSS, mistakes=[XSS])
        section["steps"][0]["image"]["alt"] = XSS
        html = self.html(data)
        self.assertEqual(html.count("<script>"), 1)  # only the engine's own script
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;&quot;&#x27;&amp;", html)

    def test_english_labels(self):
        data = copy.deepcopy(self.data)
        data["meta"]["language"] = "en"
        html = self.html(data)
        self.assertIn("Step 1", html)
        self.assertIn("<strong>How to undo: </strong>", html)
        self.assertIn("<strong>Where: </strong>", html)
        self.assertNotIn("：</strong>", html)  # no full-width colon in English labels

    def test_english_portal_history_label(self):
        data = load("portal-data.json")
        data["meta"]["language"] = "en"
        self.assertIn("<summary>History (2)</summary>", render_portal(data))

    def test_rejects_unknown_fields_and_missing_intent(self):
        data = copy.deepcopy(self.data)
        data["sections"][0]["steps"][0]["unexpected"] = 1
        with self.assertRaises(ReportValidationError):
            self.html(data)
        data = copy.deepcopy(self.data)
        del data["intent"]
        with self.assertRaises(ReportValidationError):
            self.html(data)


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.data = load("portal-data.json")

    def test_groups_by_status_current_first_history_collapsed(self):
        html = render_portal(self.data)
        current, draft, history = (html.index(s) for s in ('id="current"', 'id="draft"', 'id="history"'))
        self.assertLess(current, draft)
        self.assertLess(draft, history)
        self.assertIn('<details class="portal-archive" id="history"><summary>历史版本（2）</summary>', html)
        self.assertEqual(html.count('class="doc-card status-current"'), 2)
        self.assertIn('<span class="tag green">当前有效</span><span class="tag">操作手册</span>', html)
        self.assertIn("更新于 2026-11-24", html)

    def test_archive_open_and_empty_groups_omitted(self):
        data = copy.deepcopy(self.data)
        data["archive_open"] = True
        data["docs"] = [d for d in data["docs"] if d["status"] != "draft"]
        html = render_portal(data)
        self.assertIn('id="history" open>', html)
        self.assertNotIn('id="draft"', html)

    def test_no_script_and_no_password_gate(self):
        html = render_portal(self.data)
        self.assertNotIn("<script", html)
        self.assertNotIn("password", html.lower())
        self.assertNotIn("sessionStorage", html)

    def test_rejects_unknown_status_type_and_escapes(self):
        for key, value in (("status", "live"), ("type", "video")):
            data = copy.deepcopy(self.data)
            data["docs"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ReportValidationError):
                render_portal(data)
        data = copy.deepcopy(self.data)
        data["docs"][0].update(title=XSS, summary=XSS, href='a.html"onmouseover="x')
        html = render_portal(data)
        self.assertNotIn("<script", html)
        self.assertIn('href="a.html&quot;onmouseover=&quot;x"', html)


class SchemaDriftTests(unittest.TestCase):
    """Schemas are documentation for AI authors; keep their field lists equal to what the renderer accepts."""

    def schema(self, name):
        return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))

    def test_schema_fields_match_renderer(self):
        from generator.paged_report import META_FIELDS

        report, playbook, portal = self.schema("report"), self.schema("playbook"), self.schema("portal")
        self.assertEqual(set(report["$defs"]["meta"]["properties"]), META_FIELDS)
        self.assertEqual(set(playbook["properties"]), {"template", "meta", "intent", "toc", "sections"})
        self.assertEqual(
            set(playbook["$defs"]["section"]["properties"]), {"id", "title", "summary", "keywords", "components", "steps"}
        )
        self.assertEqual(
            set(playbook["$defs"]["step"]["properties"]),
            {"title", "path", "body", "image", "warning", "mistakes", "rollback"},
        )
        self.assertEqual(set(portal["properties"]), {"template", "meta", "intro", "archive_open", "docs"})
        patterns = [item["pattern"] for item in report["$defs"]["href"]["not"]["anyOf"]]
        for href, rejected in (
            ("javascript:x", True), ("java\nscript:x", True), ("//evil.example", True), ("\\evil", True),
            ("https://example.com/a", False), ("v2.html", False), ("#refund", False), ("/docs/a.html", False),
        ):
            with self.subTest(href=href):
                self.assertEqual(any(re.search(p, href) for p in patterns), rejected)
        self.assertEqual(
            set(portal["properties"]["docs"]["items"]["properties"]),
            {"title", "href", "type", "status", "updated", "summary"},
        )


class QaGateTests(unittest.TestCase):
    """The v1 QA gate accepts the playbook's single inline script and nothing more."""

    def evidence(self, html):
        from qa.paged_report_qa import _html_evidence

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "out.html")
            path.write_text(html, encoding="utf-8")
            return _html_evidence(path)["checks"]["self_containment"]

    def test_playbook_passes_and_extra_or_foreign_scripts_fail(self):
        playbook = render_playbook(load("playbook-data.json"), base_dir=EXAMPLES)
        self.assertEqual(self.evidence(playbook)["status"], "PASS")
        self.assertEqual(self.evidence(render_portal(load("portal-data.json")))["status"], "PASS")
        doubled = playbook.replace("</body>", "<script>1</script></body>")
        self.assertEqual(self.evidence(doubled)["status"], "FAIL")
        report = render_report(load("confirmation-data.json")).replace("</body>", "<script>1</script></body>")
        self.assertEqual(self.evidence(report)["status"], "FAIL")


class CliTests(unittest.TestCase):
    def test_one_command_renders_every_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, marker in (
                ("confirmation-data.json", 'data-family="confirmation"'),
                ("playbook-data.json", 'data-template="playbook"'),
                ("portal-data.json", 'data-template="portal"'),
            ):
                target = Path(tmp) / f"{name}.html"
                with self.subTest(name=name):
                    self.assertEqual(main([str(EXAMPLES / name), "-o", str(target)]), 0)
                    self.assertIn(marker, target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
