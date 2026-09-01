"""Thirty media compositions with explicit stock/project semantics."""

from ._factory import registry

GALLERY_IDS = (
    "inspiration_gallery_mosaic", "visual_atmosphere_sequence", "material_gallery_macro",
    "artisan_project_grid", "before_after_transformation_pairs", "documentary_work_log",
    "asymmetric_gallery_mosaic", "horizontal_gallery_scroll", "editorial_project_folio",
    "masonry_image_archive", "artisan_project_cards", "full_bleed_image_sequence", "image_diptych",
    "image_triptych", "project_contact_sheet", "alternating_project_stories", "featured_project_monument",
    "gallery_with_material_index", "residential_room_sequence", "workshop_documentary_gallery",
    "technical_detail_archive", "lighting_atmosphere_gallery", "quiet_captioned_gallery",
    "framed_canvas_gallery", "cinematic_chapter_gallery", "stock_ambient_collage",
    "artisan_casebook_rail", "construction_progress_ledger", "portrait_landscape_dialogue",
    "mobile_swipe_gallery",
)

GALLERY_COMPONENTS = registry("gallery", GALLERY_IDS)
assert len(GALLERY_COMPONENTS) == 30
