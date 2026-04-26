"""Bundled element-taxonomy-base.md loader.

The package ships with its own copy of the taxonomy in `taxonomy_data/`. For
in-repo development, the loader prefers the canonical `.claude/rules/` copy
when running from the repo root (so taxonomy edits land in the package
without an extra sync step).

Test `tests/test_taxonomy_synced.py` keeps the two copies in sync.
"""

from __future__ import annotations
import re
from importlib.resources import files
from pathlib import Path


def _repo_root_taxonomy() -> Path | None:
    """Find .claude/rules/element-taxonomy-base.md if running from the repo."""
    candidate = Path.cwd()
    for _ in range(6):
        p = candidate / ".claude" / "rules" / "element-taxonomy-base.md"
        if p.is_file():
            return p
        if candidate.parent == candidate:
            break
        candidate = candidate.parent
    return None


def load_base_taxonomy() -> str:
    """Return the full base taxonomy markdown.

    Priority: repo .claude/rules/ (if present) → bundled package data.
    """
    repo_path = _repo_root_taxonomy()
    if repo_path:
        return repo_path.read_text(encoding="utf-8")
    bundled = files("simul2design.taxonomy_data").joinpath("element-taxonomy-base.md")
    return bundled.read_text(encoding="utf-8")


def parse_allowed_values(taxonomy_md: str | None = None) -> dict[str, list[str]]:
    """Extract per-dimension allowed enum values from the taxonomy markdown.

    Parses lines like '- `value_name` — description' under '### N. `dim`' headings.
    """
    if taxonomy_md is None:
        taxonomy_md = load_base_taxonomy()
    allowed: dict[str, list[str]] = {}
    current_dim = None
    for line in taxonomy_md.splitlines():
        m = re.match(r"^###\s+\d+\.\s*`(\w+)`", line)
        if m:
            current_dim = m.group(1)
            allowed.setdefault(current_dim, [])
            continue
        if current_dim:
            m = re.match(r"^-\s+`([\w_]+)`", line)
            if m:
                allowed[current_dim].append(m.group(1))
    return allowed


# Dimensions the package treats as enum-typed (vs. cta_primary_label which is freeform).
ENUM_DIMENSIONS = (
    "layout", "modal_interrupt", "branding", "price_visibility",
    "cta_style", "cta_stack", "urgency_mechanism",
    "refund_or_guarantee_copy", "trust_signal", "evidence_detail",
)
FREEFORM_DIMENSIONS = ("cta_primary_label",)
