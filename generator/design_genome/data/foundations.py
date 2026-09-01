"""Structured spacing and geometry systems."""

from ..models import GeometrySystem, SpacingSystem


SPACING_SYSTEMS = {
    item.id: item for item in (
        SpacingSystem("compact_technical", (64, 104), 20, 12, 16, (72, 96), .72, 5),
        SpacingSystem("balanced_operational", (80, 128), 28, 16, 24, (88, 128), .76, 3),
        SpacingSystem("generous_editorial", (112, 176), 40, 20, 28, (120, 176), .68, 2),
        SpacingSystem("cinematic_pause", (136, 220), 48, 24, 32, (144, 224), .64, 1),
        SpacingSystem("material_breathing", (96, 160), 36, 18, 24, (112, 160), .72, 2),
    )
}

GEOMETRY_SYSTEMS = {
    item.id: item for item in (
        GeometrySystem("square_precise", 0, "one-pixel structural", "continuous alignment", "orthogonal", "square", "square_or_2px", "unframed_rows"),
        GeometrySystem("soft_residential", 6, "soft low-contrast", "short dividers", "measured soft corners", "4px", "4px", "individual_items_only"),
        GeometrySystem("framed_architectural", 2, "strong frame at page or media level", "architectural rules", "rectilinear framed", "square", "square", "no_nested_cards"),
        GeometrySystem("offset_editorial", 0, "selective hairline", "offset baseline rules", "asymmetric rectangular", "square", "text_link_or_square", "unframed_editorial_zones"),
        GeometrySystem("material_organic", 4, "material-toned subtle", "rare dividers", "natural rectangles without blobs", "2px", "2px", "sample_items_not_page_sections"),
    )
}
