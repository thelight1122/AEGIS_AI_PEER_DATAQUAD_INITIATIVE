"""Local Portal Pod formation layer.

This package is an additive contract/runtime facade over the already-proven
Portal and capability-router components. It does not read DataQuad directly.
"""

from .runtime import PortalPod, PortalPodError, NormalizedInvocation

__all__ = ["PortalPod", "PortalPodError", "NormalizedInvocation"]
