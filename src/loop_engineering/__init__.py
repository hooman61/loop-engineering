"""Loop Engineering read-only inspection control-plane.

The package intentionally separates deterministic measurement and control from
language-model actuation.  Stage one contains no actuator and never writes to
the inspected product repository.
"""

from .engine import InspectionEngine, InspectionOutcome

__all__ = ["InspectionEngine", "InspectionOutcome"]
__version__ = "0.1.0"

