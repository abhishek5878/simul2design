#!/usr/bin/env python3
"""Thin CLI wrapper. Logic lives in simul2design.automap_llm.

Kept at the legacy path scripts/automap-taxonomy-llm.py for back-compat
with existing docs, sim-flow, and the test suite. Re-exports all helpers
the test suite imports via importlib.

CLI behavior is unchanged — see `simul2design/automap_llm.py` _cli_main for flags.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simul2design.automap_llm import (  # noqa: F401
    DEFAULT_MODEL,
    NEEDS_REVIEW,
    PRICING,
    build_system_prompt,
    build_user_prompt,
    call_llm,
    collect_variant_text,
    estimate_cost,
    run_llm_fallback,
    select_cells_to_map,
    _cli_main as main,
)
# Tests import these by their original names from the script — alias for back-compat
from simul2design.taxonomy import load_base_taxonomy as load_taxonomy_text  # noqa: F401
from simul2design.taxonomy import parse_allowed_values  # noqa: F401

# Tests also call the helper that's now in automap_rules but used to live here
# under a different name. Re-export the equivalent for any callers.
from simul2design.automap_rules import _derive_inferences  # noqa: F401

if __name__ == "__main__":
    sys.exit(main())
