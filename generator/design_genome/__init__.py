"""Experimental Design Genome knowledge engine.

This package is intentionally disconnected from the production V3 renderer.
It builds and evaluates serializable SiteDNA candidates without rendering HTML.
"""

from .generator import DesignGenome, generate_site_dna
from .models import DesignInput, DesignQualityReport, MediaInventory, SiteDNA

__all__ = [
    "DesignGenome",
    "DesignInput",
    "DesignQualityReport",
    "MediaInventory",
    "SiteDNA",
    "generate_site_dna",
]
