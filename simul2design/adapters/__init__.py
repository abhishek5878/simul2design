"""Input-shape adapters for upstream simulators.

Each adapter converts a simulator's native output into the shape
`simul2design.schemas.ComparisonData` accepts.
"""

from simul2design.adapters.ab_report import from_ab_report

__all__ = ["from_ab_report"]
