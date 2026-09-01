"""Structured spacing and geometry systems."""

from ..models import GeometrySystem, SpacingSystem


SPACING_SYSTEMS = {
    item.id: item for item in (
        SpacingSystem("compact_technical", (64, 104), 20, 12, 16, (72, 96), .72, 5, frozenset(("technical", "information_dense")), frozenset(("technical_expert", "industrial_specialist")), frozenset(("technical_spatial",)), (4, 5)),
        SpacingSystem("balanced_operational", (80, 128), 28, 16, 24, (88, 128), .76, 3, frozenset(("balanced", "conversion_led")), frozenset(("conversion_first_local", "family_business")), frozenset(("conversion_premium",)), (2, 4)),
        SpacingSystem("generous_editorial", (112, 176), 40, 20, 28, (120, 176), .68, 2, frozenset(("editorial", "quiet")), frozenset(("editorial_studio", "quiet_luxury")), frozenset(("editorial_luxury", "minimal_architecture")), (1, 3)),
        SpacingSystem("cinematic_pause", (136, 220), 48, 24, 32, (144, 224), .64, 1, frozenset(("cinematic", "luxurious")), frozenset(("luxury_renovation", "premium_residential")), frozenset(("cinematic_luxury",)), (1, 2)),
        SpacingSystem("material_breathing", (96, 160), 36, 18, 24, (112, 160), .72, 2, frozenset(("material", "tactile", "warm")), frozenset(("material_led", "high_end_craft")), frozenset(("material_editorial", "warm_craft")), (1, 3)),
    )
}

GEOMETRY_SYSTEMS = {
    item.id: item for item in (
        GeometrySystem("square_precise", 0, "one-pixel structural", "continuous alignment", "orthogonal", "square", "square_or_2px", "unframed_rows", frozenset(("technical", "precise")), frozenset(("technical_expert", "industrial_specialist")), frozenset(("technical_spatial",))),
        GeometrySystem("soft_residential", 6, "soft low-contrast", "short dividers", "measured soft corners", "4px", "4px", "individual_items_only", frozenset(("warm", "residential")), frozenset(("premium_residential", "family_business")), frozenset(("conversion_premium", "warm_craft"))),
        GeometrySystem("framed_architectural", 2, "strong frame at page or media level", "architectural rules", "rectilinear framed", "square", "square", "no_nested_cards", frozenset(("architectural", "framed")), frozenset(("architectural_contracting", "minimal_architecture")), frozenset(("minimal_architecture", "architectural_brutalist"))),
        GeometrySystem("offset_editorial", 0, "selective hairline", "offset baseline rules", "asymmetric rectangular", "square", "text_link_or_square", "unframed_editorial_zones", frozenset(("editorial", "asymmetric")), frozenset(("editorial_studio", "quiet_luxury")), frozenset(("editorial_luxury", "material_editorial"))),
        GeometrySystem("material_organic", 4, "material-toned subtle", "rare dividers", "natural rectangles without blobs", "2px", "2px", "sample_items_not_page_sections", frozenset(("material", "tactile")), frozenset(("material_led", "high_end_craft")), frozenset(("material_editorial", "warm_craft"))),
    )
}
