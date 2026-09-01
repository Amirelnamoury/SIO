"""Twenty layout grids with explicit responsive transformations."""

from ..models import GridSystem


SPECS = (
    ("classic_12", 12, 1280, 24, ("3/12", "6/12", "9/12", "12/12"), (72, 128), "stack_preserve_order", "modular balanced"),
    ("editorial_8", 8, 1320, 28, ("2/8", "5/8", "7/8"), (88, 160), "single_column_with_insets", "editorial asymmetric"),
    ("asymmetric_5_7", 12, 1360, 30, ("5/12", "7/12"), (96, 168), "media_then_text", "asymmetric split"),
    ("split_50_50", 2, 1440, 0, ("1/2", "1/2"), (72, 120), "stack_equal", "split full_bleed"),
    ("split_40_60", 10, 1400, 24, ("4/10", "6/10"), (80, 144), "content_priority_stack", "split offset"),
    ("split_35_65", 20, 1460, 20, ("7/20", "13/20"), (88, 152), "image_crop_then_stack", "split cinematic"),
    ("architectural_3", 3, 1380, 32, ("1/3", "2/3", "3/3"), (96, 176), "single_column_indexed", "architectural strict"),
    ("portfolio_matrix", 12, 1520, 18, ("4/12", "6/12", "8/12"), (64, 136), "two_then_one", "portfolio modular"),
    ("modular_blocks", 16, 1440, 16, ("4/16", "6/16", "10/16", "16/16"), (72, 144), "ordered_blocks", "modular stacked"),
    ("oversized_margin", 10, 1600, 32, ("2/10", "6/10", "8/10"), (112, 192), "reduced_margin", "framed quiet"),
    ("centered_narrow", 6, 880, 22, ("4/6", "6/6"), (80, 136), "full_width_readable", "centered minimal"),
    ("wide_cinematic", 16, 1760, 20, ("10/16", "14/16", "16/16"), (120, 220), "panorama_crop", "cinematic full_bleed"),
    ("broken_editorial", 14, 1480, 22, ("5/14", "8/14", "11/14"), (96, 184), "linearize_offsets", "broken_grid editorial"),
    ("masonry_adaptive", 12, 1460, 20, ("3/12", "4/12", "5/12"), (72, 132), "two_column_masonry", "masonry visual_led"),
    ("rail_navigation", 12, 1500, 24, ("2/12", "10/12"), (80, 152), "rail_to_topbar", "rail architectural"),
    ("edge_to_edge", 12, 1920, 0, ("6/12", "12/12"), (72, 128), "edge_crop", "edge_to_edge bold"),
    ("framed_canvas", 12, 1500, 28, ("10/12", "12/12"), (96, 168), "remove_frame", "framed luxurious"),
    ("layered_depth", 12, 1440, 26, ("5/12", "8/12", "12/12"), (104, 184), "flatten_layers", "layered spatial"),
    ("offset_sequence", 10, 1380, 30, ("4/10", "7/10", "9/10"), (88, 160), "alternating_stack", "offset story_led"),
    ("diagonal_rhythm", 12, 1520, 24, ("5/12", "7/12", "10/12"), (96, 176), "remove_diagonal_overlap", "asymmetric bold"),
)


GRID_SYSTEMS = {
    id: GridSystem(id, columns, width, gutter, content, spacing, (640, 900, 1200), mobile, frozenset(traits.split()))
    for id, columns, width, gutter, content, spacing, mobile, traits in SPECS
}


assert len(GRID_SYSTEMS) == 20
