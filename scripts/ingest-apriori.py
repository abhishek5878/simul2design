#!/usr/bin/env python3
"""Thin CLI wrapper. Logic lives in simul2design.ingest.

Kept at the legacy path scripts/ingest-apriori.py for back-compat with
existing docs, sim-flow, and the test suite. Re-exports all helpers the
test suite imports via importlib.

CLI behavior is unchanged — see `simul2design/ingest.py` _cli_main for flags.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Make the package importable when running from the repo (no `pip install -e .` needed)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Re-export public helpers so existing tests (importlib-loaded) keep working
from simul2design.ingest import (  # noqa: F401
    DEFAULT_VARIANT_LABEL_MAP,
    NEEDS_REVIEW,
    build_matrix,
    build_source_md,
    fetch_screenshots,
    map_aggregate_metrics,
    map_apriori_next_test,
    map_citations,
    map_friction,
    map_segments,
    map_variants,
    slugify,
    variant_label,
    _cli_main as main,
)

if __name__ == "__main__":
    sys.exit(main())
