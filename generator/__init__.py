"""Paged-report generator package."""

__all__ = ["ReportValidationError", "render", "render_playbook", "render_portal", "render_report"]


def __getattr__(name):
    if name in {"render_playbook", "render_portal"}:
        from . import docs

        return getattr(docs, name)
    if name in __all__:
        from . import paged_report

        return getattr(paged_report, name)
    raise AttributeError(name)
