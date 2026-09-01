"""Experimental Design Genome knowledge engine.

This package is intentionally disconnected from the production V3 renderer.
It builds and evaluates serializable SiteDNA candidates without rendering HTML.
"""

from .generator import DesignGenome, generate_site_dna
from .blueprints import blueprint_fingerprint, blueprint_structural_distance
from .composition import composition_report, composition_report_markdown, visual_diversity_report
from .models import DesignInput, DesignQualityReport, MediaInventory, SiteDNA

__all__ = [
    "DesignGenome",
    "DesignInput",
    "DesignQualityReport",
    "MediaInventory",
    "SiteDNA",
    "generate_site_dna",
    "blueprint_fingerprint",
    "blueprint_structural_distance",
    "composition_report",
    "composition_report_markdown",
    "visual_diversity_report",
]
