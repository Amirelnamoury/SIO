"""Thirty galleries with explicit provenance and layout policies."""

from ._factory import registry
from .profiles import GALLERY_PROFILES
from .variants import GALLERY_VARIANTS

GALLERY_GROUPS = {
    "ambient": ("inspiration_gallery_mosaic", "visual_atmosphere_sequence", "lighting_atmosphere_gallery", "stock_ambient_collage", "portrait_landscape_dialogue"),
    "project": ("artisan_project_grid", "artisan_project_cards", "project_contact_sheet", "featured_project_monument", "residential_room_sequence", "technical_detail_archive"),
    "before_after": ("before_after_transformation_pairs",),
    "masonry": ("asymmetric_gallery_mosaic", "masonry_image_archive", "framed_canvas_gallery"),
    "rail": ("horizontal_gallery_scroll",),
    "editorial_project": ("editorial_project_folio", "alternating_project_stories", "quiet_captioned_gallery", "cinematic_chapter_gallery", "artisan_casebook_rail"),
    "material": ("material_gallery_macro", "image_diptych", "image_triptych", "gallery_with_material_index"),
    "documentary": ("documentary_work_log", "workshop_documentary_gallery", "construction_progress_ledger", "full_bleed_image_sequence"),
    "mobile": ("mobile_swipe_gallery",),
}

GALLERY_COMPONENTS = registry("gallery", GALLERY_GROUPS, GALLERY_PROFILES, GALLERY_VARIANTS)
assert len(GALLERY_COMPONENTS) == 30
