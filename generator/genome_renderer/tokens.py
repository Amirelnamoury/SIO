"""Translate SiteDNA systems into concrete CSS custom properties."""

from __future__ import annotations

from generator.design_genome.data.color_systems import COLOR_SYSTEMS
from generator.design_genome.data.foundations import GEOMETRY_SYSTEMS, SPACING_SYSTEMS
from generator.design_genome.data.grids import GRID_SYSTEMS
from generator.design_genome.data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from generator.design_genome.data.typography_systems import TYPOGRAPHY_SYSTEMS
from generator.design_genome.models import SiteDNA


def _font_stack(values: tuple[str, ...]) -> str:
    generic = {"serif", "sans-serif", "monospace", "ui-monospace", "system-ui"}
    return ", ".join(value if value in generic else f'"{value}"' for value in values)


def css_tokens(dna: SiteDNA) -> str:
    color = COLOR_SYSTEMS[dna.color_system]
    typography = TYPOGRAPHY_SYSTEMS[dna.typography_system]
    grid = GRID_SYSTEMS[dna.grid_system]
    spacing = SPACING_SYSTEMS[dna.spacing_system]
    geometry = GEOMETRY_SYSTEMS[dna.geometry_system]
    mobile = MOBILE_PERSONALITIES[dna.mobile_personality]
    motion = MOTION_SYSTEMS[dna.motion_system]
    spatial = SPATIAL_SYSTEMS[dna.spatial_system]
    token = color.tokens
    variables = {
        "color-canvas": token["canvas"],
        "color-canvas-alt": token["canvas_alt"],
        "color-surface": token["surface"],
        "color-surface-raised": token["surface_raised"],
        "color-text": token["text_primary"],
        "color-muted": token["text_muted"],
        "color-brand": token["brand"],
        "color-brand-text": token["brand_text"],
        "color-accent": token["accent"],
        "color-border": token["border_default"],
        "color-border-strong": token["border_strong"],
        "color-focus": token["focus"],
        "font-display": _font_stack(typography.fallback_stack),
        "font-body": _font_stack(tuple(dict.fromkeys((typography.body_family, "Arial", "sans-serif")))),
        "font-accent": _font_stack(tuple(dict.fromkeys((typography.accent_family, "Arial", "sans-serif")))),
        "font-hero": f"{typography.hero_size_range[1]}px",
        "font-hero-mobile": f"{max(36, round(typography.hero_size_range[1] * typography.mobile_scale))}px",
        "font-section": f"{typography.section_title_range[1]}px",
        "font-section-mobile": f"{max(28, round(typography.section_title_range[0] * typography.mobile_scale))}px",
        "line-body": str(typography.line_height_scale[-1]),
        "measure": f"{typography.body_measure}ch",
        "title-measure": f"{typography.max_title_width}ch",
        "content-max": f"{grid.max_width}px",
        "grid-columns": str(grid.columns),
        "grid-gap": f"{grid.gutter}px",
        "outer-margin": f"{grid.outer_margins[0]}px",
        "space-section": f"{spacing.section_padding[1]}px",
        "space-section-small": f"{spacing.section_padding[0]}px",
        "space-component": f"{spacing.component_gap}px",
        "space-text": f"{spacing.text_gap}px",
        "hero-pad": f"{spacing.hero_padding[1]}px",
        "radius": f"{geometry.radius}px",
        "border-width": "1px" if geometry.border_behavior != "none" else "0",
        "mobile-header": f"{mobile.header_height}px",
        "mobile-section": f"{mobile.section_spacing}px",
        "motion-duration": f"{max(0, motion.performance_budget_ms)}ms",
        "spatial-depth": str(spatial.level),
    }
    return ":root{" + "".join(f"--{key}:{value};" for key, value in variables.items()) + "}"
