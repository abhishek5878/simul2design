"""simul2design.synthesize — cascade steps after the auto-mapper.

The five steps from .claude/skills/ ported to standalone Python:

| Step | Module | Status | Needs LLM? |
|---|---|---|---|
| weigh-segments | weigh_segments.py | ✅ shipped | No (deterministic) |
| estimate-conversion (Wilson math) | estimate_conversion.py | ✅ shipped | No (math) |
| synthesize | synthesize.py | ⚠️ skeleton | Yes (Opus 4.7) |
| adversary | adversary.py | ⚠️ skeleton | Yes (Opus 4.7) |
| generate-spec | generate_spec.py | ⚠️ skeleton | Yes (Sonnet 4.6) |

Each step is a pure function. SynthesisPipeline composes them.
"""

from simul2design.synthesize.weigh_segments import weigh_segments
from simul2design.synthesize.estimate_conversion import (
    wilson_95_interval,
    apply_wilson_to_segments,
)
from simul2design.synthesize.synthesize import run_synthesize
from simul2design.synthesize.adversary import run_adversary
from simul2design.synthesize.generate_spec import run_generate_spec

__all__ = [
    "weigh_segments",
    "wilson_95_interval",
    "apply_wilson_to_segments",
    "run_synthesize",
    "run_adversary",
    "run_generate_spec",
]
