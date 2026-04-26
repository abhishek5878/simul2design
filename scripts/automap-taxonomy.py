#!/usr/bin/env python3
"""Thin CLI wrapper. Logic lives in simul2design.automap_rules.

Kept at the legacy path scripts/automap-taxonomy.py for back-compat with
existing docs, sim-flow, and the test suite. Re-exports all helpers the
test suite imports via importlib.

CLI behavior is unchanged — see `simul2design/automap_rules.py` _cli_main for flags.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simul2design.automap_rules import (  # noqa: F401
    CTA_LABEL_PATTERN,
    NEEDS_REVIEW,
    RULES,
    automap,
    collect_text,
    extract_cta_label,
    map_cell,
    _derive_inferences,
    _cli_main as main,
)

if __name__ == "__main__":
    sys.exit(main())
