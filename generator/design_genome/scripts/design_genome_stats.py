"""Print structural counts and an intentionally conservative raw-space estimate."""

from __future__ import annotations

import json
from math import prod

from ..archetypes import ARCHETYPES
from ..data.color_systems import COLOR_SYSTEMS
from ..data.components import COMPONENT_REGISTRIES
from ..data.grids import GRID_SYSTEMS
from ..data.page_silhouettes import PAGE_SILHOUETTES
from ..data.systems import MOBILE_PERSONALITIES, MOTION_SYSTEMS, SPATIAL_SYSTEMS
from ..data.trade_grammar import TRADE_GRAMMARS
from ..data.typography_systems import TYPOGRAPHY_SYSTEMS
from ..photo_direction import PHOTO_DIRECTIONS


def stats() -> dict:
    component_counts = {category: len(items) for category, items in COMPONENT_REGISTRIES.items()}
    dimensions = (
        len(ARCHETYPES), 8, len(PAGE_SILHOUETTES), len(COLOR_SYSTEMS), len(TYPOGRAPHY_SYSTEMS),
        len(GRID_SYSTEMS), len(COMPONENT_REGISTRIES["header"]), len(COMPONENT_REGISTRIES["hero"]),
        len(COMPONENT_REGISTRIES["services"]), len(COMPONENT_REGISTRIES["footer"]),
        len(MOTION_SYSTEMS), len(SPATIAL_SYSTEMS), len(MOBILE_PERSONALITIES),
    )
    return {
        "archetypes": len(ARCHETYPES),
        "trade_grammars": len(TRADE_GRAMMARS),
        "colors": len(COLOR_SYSTEMS),
        "typography": len(TYPOGRAPHY_SYSTEMS),
        "grids": len(GRID_SYSTEMS),
        "silhouettes": len(PAGE_SILHOUETTES),
        "components": component_counts,
        "component_blueprints": sum(component_counts.values()),
        "photo_profiles": len(PHOTO_DIRECTIONS),
        "motion": len(MOTION_SYSTEMS),
        "spatial": len(SPATIAL_SYSTEMS),
        "mobile": len(MOBILE_PERSONALITIES),
        "raw_core_space": prod(dimensions),
        "raw_space_note": "Upper bound before data, media, compatibility and anti-clone constraints.",
    }


if __name__ == "__main__":
    print(json.dumps(stats(), indent=2))
