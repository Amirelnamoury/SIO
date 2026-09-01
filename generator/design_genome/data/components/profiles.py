"""Reviewed semantic profiles explicitly assigned by component registries."""

from __future__ import annotations

from ._factory import blueprint, component_profile, hero_blueprint


def header_spec(layout, brand, nav, cta, *, sticky="measured", transparent=False, secondary="none", mobile="drawer"):
    return blueprint(layout, "horizontal", desktop={"brand_placement": brand, "nav_placement": nav, "cta_placement": cta, "height_px": 80, "secondary_information": secondary}, mobile={"navigation_behavior": mobile, "brand_behavior": "preserve_legibility", "cta_behavior": "one_primary_action", "height_px": 64}, media={"logo_behavior": "intrinsic_ratio", "background_transparency": transparent}, content={"navigation_limit": 7, "secondary_information": secondary}, behavior={"sticky_behavior": sticky, "transparency": transparent, "scroll_transition": "contrast_safe"}, fallback="text brand and compact accessible navigation")


def services_spec(layout, item_layout, columns, *, item_density="medium", image="optional_ambient", index="none", interaction="none"):
    return blueprint(layout, "content_grid", desktop={"item_layout": item_layout, "columns": columns[0], "item_density": item_density, "index_behavior": index}, mobile={"tablet_columns": columns[1], "columns": columns[2], "transformation": "accordion" if interaction == "accordion" else "linear_stack", "action_behavior": "action_follows_item"}, media={"relationship": image, "count_policy": "one_per_item_only_when_relevant", "crop": "consistent_by_service_set"}, content={"title_limit": 48, "description_limit": 180, "item_action": "optional"}, behavior={"interaction": interaction, "sequence_energy": "medium"}, fallback="text-only services preserving hierarchy")


def gallery_spec(layout, provenance, count, ratios, *, captions, mobile, energy="strong"):
    return blueprint(layout, "visual_grid", desktop={"layout_behavior": layout, "item_count_min": count[0], "item_count_max": count[1], "rhythm": "vary_scale_with_alignment_anchor"}, mobile={"transformation": mobile, "caption_behavior": "attached_to_media"}, media={"provenance": provenance, "ratios": ratios, "crop": "role_specific", "stock_project_wording_forbidden": True}, content={"captions": captions, "project_claim_policy": "artisan_media_only"}, behavior={"sequence_energy": energy, "interaction": "native_scroll_or_snap"}, fallback="omit when minimum honest media is unavailable")


def about_spec(layout, narrative, image, facts):
    return blueprint(layout, "narrative", desktop={"narrative_zones": narrative, "image_placement": image, "facts_placement": facts, "columns": 12}, mobile={"order": ("title", "narrative", "image", "verified_facts"), "image_behavior": "context_safe"}, media={"relationship": image, "provenance": "artisan_preferred_stock_ambient_only"}, content={"narrative_limit": 600, "facts_policy": "verified_only", "quote_policy": "attributed_or_omit"}, behavior={"reading_rhythm": "quiet", "sticky": False}, fallback="text narrative without factual embellishment")


def trust_spec(layout, evidence, max_facts, visual):
    return blueprint(layout, "evidence", desktop={"visual_structure": visual, "columns": min(max_facts, 4), "maximum_facts": max_facts}, mobile={"transformation": "compact_verified_list", "priority": "decision_relevant_first"}, media={"provenance": "artisan_evidence_only", "decorative_stock": False}, content={"required_evidence": evidence, "fact_formats": ("label_value", "attributed_excerpt", "verified_badge"), "unsupported_fact_policy": "omit"}, behavior={"energy": "quiet", "placement": "near_supported_decision"}, fallback="omit trust block")


def cta_spec(layout, scale, primary, secondary, *, media="none"):
    return blueprint(layout, "action", desktop={"section_scale": scale, "primary_action": primary, "secondary_action": secondary, "action_alignment": "with_message"}, mobile={"transformation": "stack_message_then_actions", "persistence": "profile_dependent"}, media={"relationship": media, "supports_no_media": media == "none"}, content={"message_role": "decision_prompt_not_claim", "primary_limit": 1, "secondary_limit": 1}, behavior={"conversion_priority": "primary", "motion": "micro_feedback_only"}, fallback="single honest contact action")


def contact_spec(layout, details, form, hierarchy):
    return blueprint(layout, "conversion", desktop={"details_form_balance": (details, form), "layout": layout, "cta_hierarchy": hierarchy}, mobile={"order": ("primary_channel", "details", "form"), "persistent_action": "profile_dependent"}, media={"relationship": "none_or_contextual_ambient", "project_claims": False}, content={"required_channel": "phone_or_email_or_working_form", "privacy_notice": "required_with_form"}, behavior={"focus_order": "visual_matches_dom", "success_state": "explicit"}, fallback="verified contact details only")


def footer_spec(layout, columns, brand, contact, action):
    return blueprint(layout, "information", desktop={"columns": columns, "brand_placement": brand, "contact_placement": contact, "navigation": "grouped", "legal": "final_row", "cta_possibility": action}, mobile={"transformation": "single_column_priority", "order": ("brand", "contact", "navigation", "legal")}, media={"relationship": "none_by_default", "logo_behavior": "intrinsic"}, content={"navigation_limit_per_group": 7, "legal_required": True}, behavior={"energy": "quiet_close", "sticky": False}, fallback="brand, contact and legal minimum")


def form_spec(layout, fields, steps):
    return blueprint(layout, "form", desktop={"field_layout": fields, "steps": steps, "label_position": "visible_above_control"}, mobile={"transformation": "single_column", "input_size": "touch_safe", "error_summary": "before_fields"}, media={"relationship": "none"}, content={"consent": "explicit_when_required", "status": "announced", "required_fields": "minimum_viable"}, behavior={"validation": "field_and_summary", "submission": "single_idempotent_action"}, fallback="compact accessible enquiry form")


HEADER_PROFILES = {
    "classic": component_profile(header_spec("classic_horizontal", "left", "right", "nav_end"), traits=("balanced",), density=3, visual_weight=2, section_energy="quiet"),
    "centered": component_profile(header_spec("centered_brand", "center", "split_sides", "right"), traits=("centered", "quiet"), density=2, visual_weight=2, section_energy="quiet"),
    "contact": component_profile(header_spec("contact_utility", "left", "center", "right", secondary="verified_contact"), traits=("conversion_led", "phone_first"), required_any_data=("phone", "email"), compatible_archetypes=("conversion_first_local", "local_emergency_service"), compatible_directions=("conversion_premium",), density=4, conversion_score=.92, mobile_variant="bottom_action"),
    "overlay": component_profile(header_spec("transparent_overlay", "left", "center", "right", transparent=True), traits=("cinematic", "full_bleed"), compatible_directions=("cinematic_luxury", "editorial_luxury"), density=2, visual_weight=3),
    "editorial": component_profile(header_spec("editorial_index", "top_left", "index_rail", "none", sticky="section_aware", mobile="index_drawer"), traits=("editorial", "asymmetric"), compatible_archetypes=("editorial_studio", "material_led"), compatible_directions=("editorial_luxury", "material_editorial"), editorial_score=.92),
    "rail": component_profile(header_spec("architectural_rail", "rail_top", "vertical_rail", "rail_bottom", mobile="rail_to_topbar"), traits=("architectural", "rail"), compatible_archetypes=("architectural_contracting", "project_portfolio"), compatible_directions=("minimal_architecture", "architectural_brutalist")),
    "local": component_profile(header_spec("local_information", "left", "center", "right", secondary="verified_location"), traits=("local", "trust_led"), required_data=("city",), compatible_archetypes=("family_business", "conversion_first_local"), density=4),
    "technical": component_profile(header_spec("technical_utility", "left", "system_index", "right", secondary="verified_context", mobile="accordion_navigation"), traits=("technical", "information_dense"), compatible_archetypes=("technical_expert", "industrial_specialist"), compatible_directions=("technical_spatial",), density=5),
    "statement": component_profile(header_spec("statement_brand", "dominant", "menu_trigger", "none", mobile="oversized_menu"), traits=("bold", "minimal"), compatible_directions=("architectural_brutalist", "minimal_architecture"), density=1, visual_weight=4, section_energy="strong"),
    "gallery": component_profile(header_spec("gallery_navigation", "corner", "project_index", "contact_corner", mobile="project_index"), traits=("portfolio", "visual_led"), compatible_archetypes=("project_portfolio",), density=2),
}


HERO_PROFILES = {
    "photo_cover": component_profile(hero_blueprint("full_bleed_cover", alignment="overlay_or_edge", media_layout="single_full_bleed", media_count=(1, 1), orientations=("landscape",), crop="focal_subject_safe", spans=(5, 12), desktop_order=("media", "content"), mobile_order=("content", "media"), overlay="contrast_scrim_when_needed"), traits=("visual_led", "full_bleed"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), compatible_directions=("cinematic_luxury", "editorial_luxury"), density=2, visual_weight=5, section_energy="heroic", image_dependency=.95),
    "split_photo": component_profile(hero_blueprint("split_editorial", alignment="left", media_layout="single_contained", media_count=(1, 1), orientations=("portrait", "landscape"), crop="architectural_context", spans=(5, 7), desktop_order=("content", "media"), mobile_order=("title", "media", "copy", "actions")), traits=("split", "visual_led"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), compatible_directions=("editorial_luxury", "minimal_architecture", "conversion_premium"), visual_weight=4, section_energy="strong", image_dependency=.8),
    "collage": component_profile(hero_blueprint("asymmetric_editorial_collage", alignment="left", media_layout="primary_plus_offset_secondary", media_count=(2, 3), orientations=("portrait", "landscape"), crop="mixed_ratio_subject_safe", spans=(4, 8), desktop_order=("content", "primary_media", "secondary_media"), mobile_order=("title", "primary_media", "copy", "secondary_media", "actions"), motion=("measured_stagger", "image_crop_reveal")), traits=("editorial", "asymmetric", "visual_led"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), compatible_archetypes=("editorial_studio", "material_led"), compatible_directions=("editorial_luxury", "material_editorial"), visual_weight=5, section_energy="heroic", image_dependency=.95, editorial_score=.92),
    "cinematic": component_profile(hero_blueprint("cinematic_scene", alignment="center", media_layout="single_scene", media_count=(1, 1), orientations=("landscape",), crop="wide_environmental", spans=(6, 12), desktop_order=("media", "content"), mobile_order=("title", "poster", "copy", "actions"), overlay="measured_gradient_scrim", background="media_dominant", motion=("soft_scale", "chapter_crossfade")), traits=("cinematic", "story_led"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), compatible_archetypes=("luxury_renovation", "premium_residential"), compatible_directions=("cinematic_luxury",), density=2, visual_weight=5, section_energy="heroic", image_dependency=1.0),
    "project": component_profile(hero_blueprint("project_evidence_intro", alignment="edge", media_layout="project_contact_sheet", media_count=(1, 4), orientations=("landscape", "portrait"), crop="preserve_project_context", spans=(4, 8), desktop_order=("project_media", "project_context"), mobile_order=("title", "project_media", "verified_context", "actions"), supports_stock=False), traits=("project_led", "portfolio"), required_media=("artisan_project",), allowed_media_sources=("artisan",), compatible_archetypes=("project_portfolio", "architectural_contracting"), compatible_directions=("minimal_architecture", "editorial_luxury"), visual_weight=4, section_energy="strong", image_dependency=1.0),
    "material": component_profile(hero_blueprint("material_study", alignment="offset", media_layout="macro_plus_context", media_count=(1, 3), orientations=("portrait", "square", "landscape"), crop="material_detail_with_context", spans=(5, 7), desktop_order=("macro", "title", "context"), mobile_order=("title", "macro", "copy", "context"), motion=("image_crop_reveal",)), traits=("material", "tactile"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), compatible_archetypes=("material_led", "high_end_craft"), compatible_directions=("material_editorial", "warm_craft"), visual_weight=4, section_energy="strong", image_dependency=.85),
    "typographic": component_profile(hero_blueprint("typographic_statement", alignment="left", media_layout="none", media_count=(0, 0), orientations=(), crop="none", spans=(10, 0), desktop_order=("eyebrow", "title", "copy", "actions"), mobile_order=("eyebrow", "title", "copy", "actions"), title_scale="display_xl", supports_no_media=True, supports_stock=False, supports_artisan=False, mobile_media="none", fallback="typographic composition is the no-media fallback"), traits=("minimal", "editorial"), compatible_archetypes=("minimal_architecture", "editorial_studio", "quiet_luxury"), compatible_directions=("minimal_architecture", "editorial_luxury", "architectural_brutalist"), density=1, visual_weight=4, section_energy="strong", image_dependency=0.0, editorial_score=.85),
    "conversion": component_profile(hero_blueprint("conversion_problem_solution", alignment="left", media_layout="optional_ambient", media_count=(0, 1), orientations=("landscape",), crop="supporting_not_claim", spans=(7, 5), desktop_order=("problem", "identity", "solution", "actions", "optional_media"), mobile_order=("identity", "problem", "primary_action", "services_hint", "optional_media"), supports_no_media=True, max_title_width=22), traits=("conversion_led", "local"), required_any_data=("phone", "email"), compatible_archetypes=("conversion_first_local", "local_emergency_service"), compatible_directions=("conversion_premium",), density=4, visual_weight=4, section_energy="strong", conversion_score=.96),
    "technical": component_profile(hero_blueprint("technical_explainer", alignment="left", media_layout="diagram_or_none", media_count=(0, 1), orientations=("landscape",), crop="none_for_diagram", spans=(6, 6), desktop_order=("title", "capability_summary", "diagram"), mobile_order=("title", "summary", "static_diagram"), supports_no_media=True, supports_stock=False, motion=("diagram_progress",), fallback="static neutral diagram without unsupported factual labels"), traits=("technical", "information_dense"), compatible_archetypes=("technical_expert", "industrial_specialist"), compatible_directions=("technical_spatial", "minimal_architecture"), density=4, visual_weight=4, section_energy="strong"),
    "spatial": component_profile(hero_blueprint("spatial_explainer", alignment="center", media_layout="explanatory_layers", media_count=(0, 2), orientations=("landscape",), crop="not_applicable_to_diagram", spans=(5, 7), desktop_order=("content", "spatial_explainer"), mobile_order=("title", "static_explainer", "copy"), supports_no_media=True, supports_stock=False, motion=("depth_layers", "diagram_progress"), fallback="static diagram with identical hierarchy"), traits=("technical", "spatial", "layered"), compatible_archetypes=("spatial_technical", "technical_expert"), compatible_directions=("technical_spatial",), visual_weight=5, section_energy="heroic", image_dependency=.2),
    "transformation": component_profile(hero_blueprint("verified_transformation_pair", alignment="center", media_layout="paired_before_after", media_count=(2, 2), orientations=("matched",), crop="matched_framing_no_deceptive_crop", spans=(4, 8), desktop_order=("verified_pair", "context"), mobile_order=("title", "before", "after", "verified_context"), supports_stock=False, fallback="select another hero; never synthesize transformation"), traits=("project_led", "documentary"), required_media=("before_after",), allowed_media_sources=("artisan",), compatible_archetypes=("luxury_renovation", "documentary_craft"), visual_weight=5, section_energy="heroic", image_dependency=1.0),
    "rail": component_profile(hero_blueprint("horizontal_preview_rail", alignment="edge", media_layout="horizontal_rail", media_count=(2, 5), orientations=("landscape", "portrait"), crop="consistent_height_variable_width", spans=(4, 8), desktop_order=("title", "rail", "copy"), mobile_order=("title", "snap_rail", "copy", "actions"), motion=("horizontal_rail",)), traits=("rail", "portfolio"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), compatible_archetypes=("project_portfolio", "editorial_studio"), visual_weight=4, section_energy="strong", image_dependency=.85),
}


SERVICES_PROFILES = {
    "rows": component_profile(services_spec("editorial_rows", "full_width_rows", (1, 1, 1), index="ordered"), traits=("editorial", "service_led"), required_data=("services",), compatible_directions=("editorial_luxury", "material_editorial"), editorial_score=.82),
    "grid": component_profile(services_spec("service_grid", "equal_modules", (3, 2, 1)), traits=("modular", "service_led"), required_data=("services",)),
    "photo": component_profile(services_spec("photo_service_cards", "media_text_pair", (3, 2, 1), image="ambient_or_documented_context"), traits=("visual_led", "service_led"), required_data=("services",), required_any_media=("artisan_photo", "stock_photo"), visual_weight=4, section_energy="strong", image_dependency=.75),
    "rail": component_profile(services_spec("horizontal_service_rail", "snap_items", (3, 2, 1), index="progress"), traits=("rail", "service_led"), required_data=("services",)),
    "index": component_profile(services_spec("typographic_index", "indexed_rows", (1, 1, 1), item_density="dense", index="numbered"), traits=("editorial", "information_dense"), required_data=("services",), density=4),
    "accordion": component_profile(services_spec("service_accordion", "disclosure_rows", (1, 1, 1), item_density="dense", interaction="accordion"), traits=("service_led", "compact"), required_data=("services",), density=4, visual_weight=2, section_energy="quiet"),
    "matrix": component_profile(services_spec("capability_matrix", "matrix", (4, 2, 1), item_density="dense", index="capability_axis"), traits=("information_dense", "technical"), required_data=("services",), compatible_archetypes=("technical_expert", "industrial_specialist"), compatible_directions=("technical_spatial",), density=5, visual_weight=4, section_energy="strong"),
    "process": component_profile(services_spec("process_services", "phased_rows", (3, 2, 1), index="phase"), traits=("story_led", "service_led"), required_data=("services", "process")),
    "technical": component_profile(services_spec("technical_specification", "specification_rows", (2, 1, 1), item_density="dense", index="system"), traits=("technical", "information_dense"), required_data=("services",), compatible_directions=("technical_spatial",), density=5),
    "minimal": component_profile(services_spec("minimal_links", "title_links", (2, 1, 1), item_density="airy"), traits=("minimal", "quiet"), required_data=("services",), density=2, visual_weight=2, section_energy="quiet"),
    "bento": component_profile(services_spec("asymmetric_bento", "variable_modules", (4, 2, 1), item_density="dense"), traits=("modular", "bold"), required_data=("services",), density=4, visual_weight=5, section_energy="heroic"),
    "conversion": component_profile(services_spec("conversion_selector", "action_rows", (3, 2, 1), interaction="selection"), traits=("conversion_led", "service_led"), required_data=("services",), compatible_directions=("conversion_premium",), density=4, conversion_score=.95),
    "material": component_profile(services_spec("material_catalogue", "sample_rows", (3, 2, 1), image="material_ambient_only"), traits=("material", "tactile"), required_data=("services",), compatible_directions=("material_editorial", "warm_craft"), visual_weight=4, section_energy="strong"),
}


GALLERY_PROFILES = {
    "ambient": component_profile(gallery_spec("ambient_mosaic", "artisan_or_stock_ambient_never_project", (3, 10), ("landscape", "portrait", "square"), captions="descriptive_not_project_claim", mobile="two_column_or_stack"), traits=("visual_led",), required_any_media=("artisan_photo", "stock_photo"), visual_weight=4, section_energy="strong", image_dependency=.9),
    "project": component_profile(gallery_spec("project_grid", "artisan_project_only", (3, 12), ("landscape", "portrait"), captions="verified_project_context", mobile="project_cards"), traits=("project_led", "portfolio"), required_media=("artisan_project",), allowed_media_sources=("artisan",), visual_weight=4, section_energy="strong", image_dependency=1.0),
    "before_after": component_profile(gallery_spec("before_after_pairs", "artisan_before_after_only", (2, 12), ("matched",), captions="verified_transformation_context", mobile="paired_stack"), traits=("project_led", "documentary"), required_media=("before_after",), allowed_media_sources=("artisan",), visual_weight=4, section_energy="strong", image_dependency=1.0),
    "masonry": component_profile(gallery_spec("masonry_archive", "artisan_or_stock_ambient", (5, 16), ("portrait", "landscape"), captions="optional_descriptive", mobile="two_column_masonry"), traits=("masonry", "visual_led"), required_any_media=("artisan_photo", "stock_photo"), visual_weight=4, section_energy="strong", image_dependency=.9),
    "rail": component_profile(gallery_spec("horizontal_rail", "role_aware_mixed", (4, 14), ("landscape", "portrait"), captions="attached_below_item", mobile="snap_rail"), traits=("rail", "visual_led"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), visual_weight=4, section_energy="strong", image_dependency=.9),
    "editorial_project": component_profile(gallery_spec("editorial_casebook", "artisan_project_only", (3, 10), ("landscape", "portrait"), captions="verified_case_context", mobile="chapter_stack"), traits=("editorial", "project_led"), required_media=("artisan_project",), allowed_media_sources=("artisan",), visual_weight=4, section_energy="strong", image_dependency=1.0),
    "material": component_profile(gallery_spec("material_study", "artisan_or_stock_ambient", (3, 12), ("macro", "square", "landscape"), captions="material_description_not_project_claim", mobile="material_swipe"), traits=("material", "tactile"), required_any_media=("artisan_photo", "stock_photo"), visual_weight=4, section_energy="strong", image_dependency=.9),
    "documentary": component_profile(gallery_spec("documentary_work_log", "artisan_project_only", (4, 16), ("landscape", "portrait"), captions="verified_sequence_context", mobile="chronological_stack"), traits=("documentary", "project_led"), required_media=("artisan_project",), allowed_media_sources=("artisan",), visual_weight=4, section_energy="strong", image_dependency=1.0),
    "mobile": component_profile(gallery_spec("mobile_swipe", "role_aware_mixed", (3, 8), ("portrait", "landscape"), captions="short_attached_caption", mobile="single_card_snap", energy="medium"), traits=("visual_led", "compact"), required_any_media=("artisan_photo", "stock_photo", "artisan_project"), visual_weight=3, image_dependency=.8),
}


ABOUT_PROFILES = {
    "identity": component_profile(about_spec("business_identity", "identity_then_approach", "optional_contextual", "none"), traits=("story_led",), density=2, visual_weight=2, section_energy="quiet"),
    "founder": component_profile(about_spec("founder_story", "person_then_business", "verified_portrait_preferred", "verified_role"), traits=("story_led", "warm"), required_any_data=("founder", "team"), density=2),
    "documentary": component_profile(about_spec("documentary_process", "method_chapters", "artisan_process_preferred", "process_only"), traits=("documentary", "warm"), required_data=("process",)),
    "material": component_profile(about_spec("material_philosophy", "principle_then_application", "ambient_material", "none"), traits=("material", "editorial"), compatible_directions=("material_editorial", "warm_craft"), density=2),
    "local": component_profile(about_spec("local_commitment", "identity_location_service", "optional_local_ambient", "verified_location"), traits=("local", "trust_led"), required_data=("city",), visual_weight=2, section_energy="quiet"),
    "team": component_profile(about_spec("team_portrait", "team_then_roles", "artisan_team_portrait", "verified_roles"), traits=("trust_led", "warm"), required_data=("team",), required_media=("portrait",), allowed_media_sources=("artisan",)),
    "heritage": component_profile(about_spec("heritage_timeline", "chronological", "artisan_archive_preferred", "verified_dates"), traits=("heritage", "editorial"), required_data=("history",)),
    "technical": component_profile(about_spec("technical_expertise", "method_capability_context", "diagram_or_artisan_detail", "verified_qualifications_only"), traits=("technical", "information_dense"), required_data=("process",), density=4),
    "project": component_profile(about_spec("project_context", "project_then_method", "artisan_project", "verified_project_context"), traits=("project_led", "story_led"), required_media=("artisan_project",), allowed_media_sources=("artisan",)),
    "minimal": component_profile(about_spec("quiet_statement", "single_narrative_zone", "none", "none"), traits=("minimal", "quiet"), density=1, visual_weight=2, section_energy="quiet"),
}


TRUST_PROFILES = {
    name: component_profile(trust_spec(layout, evidence, maximum, visual), traits=traits, required_data=required_data, required_media=required_media, allowed_media_sources=allowed, density=density, visual_weight=weight, section_energy=energy)
    for name, layout, evidence, maximum, visual, traits, required_data, required_media, allowed, density, weight, energy in (
        ("insurance", "verified_line", "insurance", 1, "single_fact", ("trust_led",), ("insurance",), (), ("artisan", "none"), 2, 2, "quiet"),
        ("certifications", "verified_badges", "certifications", 6, "badge_grid", ("trust_led", "technical"), ("certifications",), (), ("artisan", "none"), 3, 2, "quiet"),
        ("reviews", "verified_reviews", "reviews", 4, "attributed_excerpts", ("trust_led",), ("reviews",), (), ("artisan", "none"), 3, 3, "medium"),
        ("statistics", "verified_statistics", "statistics", 4, "number_label_grid", ("trust_led", "information_dense"), ("statistics",), (), ("artisan", "none"), 4, 3, "medium"),
        ("team", "team_credentials", "team", 6, "credential_list", ("trust_led", "warm"), ("team",), (), ("artisan", "none"), 3, 3, "medium"),
        ("area", "service_area", "service_areas", 8, "area_list_or_map", ("trust_led", "local"), ("service_areas",), (), ("artisan", "none"), 3, 2, "quiet"),
        ("partners", "partner_directory", "partners", 8, "name_directory", ("trust_led",), ("partners",), (), ("artisan", "none"), 3, 2, "quiet"),
        ("brands", "brand_authorizations", "brands", 8, "verified_name_grid", ("trust_led",), ("brands",), (), ("artisan", "none"), 3, 2, "quiet"),
        ("awards", "awards_ledger", "awards", 6, "dated_ledger", ("trust_led", "editorial"), ("awards",), (), ("artisan", "none"), 3, 2, "quiet"),
        ("guarantee", "guarantee_statement", "guarantee", 2, "verified_statement", ("trust_led",), ("guarantee",), (), ("artisan", "none"), 2, 2, "quiet"),
        ("hours", "opening_hours", "opening_hours", 7, "schedule", ("trust_led", "local"), ("opening_hours",), (), ("artisan", "none"), 3, 2, "quiet"),
        ("emergency", "emergency_availability", "emergency_service", 1, "verified_availability", ("trust_led", "conversion_led"), ("emergency_service",), (), ("artisan", "none"), 3, 3, "medium"),
        ("response", "response_delay", "response_delay", 1, "verified_delay", ("trust_led", "conversion_led"), ("response_delay",), (), ("artisan", "none"), 2, 2, "quiet"),
        ("process", "documented_process", "process", 5, "phase_evidence", ("trust_led", "story_led"), ("process",), (), ("artisan", "none"), 3, 3, "medium"),
        ("project", "artisan_project_evidence", "artisan_project_media", 4, "project_evidence", ("trust_led", "project_led"), (), ("artisan_project",), ("artisan",), 3, 3, "medium"),
        ("before_after", "before_after_evidence", "artisan_before_after", 4, "paired_evidence", ("trust_led", "project_led"), (), ("before_after",), ("artisan",), 3, 3, "medium"),
        ("facts", "verified_fact_index", "verified_facts", 5, "fact_strip", ("trust_led",), ("verified_facts",), (), ("artisan", "none"), 3, 2, "quiet"),
    )
}


CTA_PROFILES = {
    "phone": component_profile(cta_spec("phone_action", "medium", "phone", "contact_form"), traits=("conversion_led", "phone_first"), required_data=("phone",), conversion_score=.96, mobile_variant="bottom_action"),
    "quote": component_profile(cta_spec("quote_action", "medium", "quote_request", "phone_or_email"), traits=("conversion_led", "quote_first"), required_any_data=("phone", "email"), conversion_score=.96),
    "contact": component_profile(cta_spec("contact_prompt", "small", "contact", "none"), traits=("conversion_led",), required_any_data=("phone", "email"), density=2, visual_weight=2, section_energy="quiet", conversion_score=.82),
    "project": component_profile(cta_spec("project_enquiry", "medium", "project_brief", "gallery"), traits=("project_led", "conversion_led"), required_any_data=("phone", "email")),
    "emergency": component_profile(cta_spec("emergency_phone", "strong", "phone", "service_area"), traits=("conversion_led", "phone_first"), required_data=("phone", "emergency_service"), density=4, visual_weight=4, section_energy="strong", conversion_score=1.0),
    "email": component_profile(cta_spec("email_link", "small", "email", "none"), traits=("conversion_led", "minimal"), required_data=("email",), density=1, visual_weight=2, section_energy="quiet"),
    "availability": component_profile(cta_spec("availability_checked", "medium", "contact", "verified_availability"), traits=("conversion_led", "trust_led"), required_data=("availability",), required_any_data=("phone", "email")),
    "material": component_profile(cta_spec("material_consultation", "medium", "consultation", "contact"), traits=("material", "conversion_led"), required_any_data=("phone", "email")),
    "statement": component_profile(cta_spec("monumental_action", "monumental", "contact", "none"), traits=("bold", "conversion_led"), required_any_data=("phone", "email"), density=2, visual_weight=5, section_energy="heroic"),
}


CONTACT_PROFILES = {
    "phone": component_profile(contact_spec("phone_first", "primary", "secondary", "phone_then_form"), traits=("phone_first", "conversion_led"), required_data=("phone",), mobile_variant="bottom_action"),
    "quote": component_profile(contact_spec("quote_first", "secondary", "primary", "form_then_channels"), traits=("quote_first", "conversion_led"), required_any_data=("phone", "email")),
    "minimal": component_profile(contact_spec("minimal_details", "primary", "none", "single_channel"), traits=("minimal", "quiet", "conversion_led"), required_any_data=("phone", "email"), density=1, visual_weight=2, section_energy="quiet"),
    "split": component_profile(contact_spec("split_details_form", "5/12", "7/12", "form_primary"), traits=("split", "conversion_led"), required_any_data=("phone", "email")),
    "panel": component_profile(contact_spec("persistent_panel", "4/12", "8/12", "primary_action_visible"), traits=("conversion_led", "layered"), required_any_data=("phone", "email"), density=4, visual_weight=4, section_energy="strong"),
    "project": component_profile(contact_spec("project_brief", "4/12", "8/12", "brief_then_contact"), traits=("project_led", "conversion_led"), required_any_data=("phone", "email"), density=4),
    "emergency": component_profile(contact_spec("emergency_contact", "primary", "minimal", "phone_immediate"), traits=("phone_first", "conversion_led"), required_data=("phone", "emergency_service"), density=4, visual_weight=4, section_energy="strong"),
    "local": component_profile(contact_spec("local_context", "5/12", "7/12", "area_then_contact"), traits=("local", "trust_led", "conversion_led"), required_data=("service_areas",), required_any_data=("phone", "email")),
    "technical": component_profile(contact_spec("technical_diagnostic", "4/12", "8/12", "scope_then_form"), traits=("technical", "conversion_led"), required_any_data=("phone", "email"), density=4),
    "editorial": component_profile(contact_spec("editorial_statement", "6/12", "6/12", "message_then_channel"), traits=("editorial", "quiet", "conversion_led"), required_any_data=("phone", "email"), density=2),
    "channels": component_profile(contact_spec("multi_channel", "primary", "optional", "ranked_channels"), traits=("conversion_led", "information_dense"), required_any_data=("phone", "email"), density=4),
}


FOOTER_PROFILES = {
    "minimal": component_profile(footer_spec("minimal", 1, "top", "inline", "none"), traits=("minimal", "quiet"), density=1, visual_weight=2, section_energy="quiet"),
    "business": component_profile(footer_spec("business_information", 4, "first_column", "second_column", "optional"), traits=("information_dense",), density=4, visual_weight=2, section_energy="quiet"),
    "navigation": component_profile(footer_spec("navigation_columns", 4, "first_column", "contact_column", "optional"), traits=("modular",), density=4, visual_weight=2, section_energy="quiet"),
    "services": component_profile(footer_spec("service_directory", 4, "first_column", "last_column", "optional"), traits=("service_led",), required_data=("services",), density=4, visual_weight=2, section_energy="quiet"),
    "area": component_profile(footer_spec("service_area", 3, "first_column", "area_column", "optional"), traits=("local",), required_data=("service_areas",), visual_weight=2, section_energy="quiet"),
    "contact": component_profile(footer_spec("contact_first", 3, "first_column", "dominant", "primary"), traits=("conversion_led",), required_any_data=("phone", "email")),
    "statement": component_profile(footer_spec("brand_statement", 2, "dominant", "secondary", "optional"), traits=("bold", "editorial"), density=2, visual_weight=4, section_energy="strong"),
    "project": component_profile(footer_spec("project_index", 3, "first_column", "last_column", "project_enquiry"), traits=("project_led",), required_media=("artisan_project",), allowed_media_sources=("artisan",)),
    "technical": component_profile(footer_spec("technical_spec", 5, "first_column", "last_column", "optional"), traits=("technical", "information_dense"), density=5, visual_weight=2, section_energy="quiet"),
    "visual": component_profile(footer_spec("visual_close", 2, "overlay", "overlay", "optional"), traits=("visual_led",), required_any_media=("artisan_photo", "stock_photo"), density=2, visual_weight=4, section_energy="strong", image_dependency=.8),
}


FORM_PROFILES = {
    "single": component_profile(form_spec("single_column", "single_column", 1), traits=("conversion_led",), visual_weight=2, section_energy="quiet"),
    "split": component_profile(form_spec("split_fields", "two_columns_then_full", 1), traits=("split", "conversion_led"), density=4),
    "compact": component_profile(form_spec("compact_callback", "minimal_fields", 1), traits=("compact", "conversion_led"), visual_weight=2, section_energy="quiet"),
    "multi_step": component_profile(form_spec("multi_step", "one_topic_per_step", 3), traits=("conversion_led", "information_dense"), density=4),
    "technical": component_profile(form_spec("technical_scope", "grouped_fields", 2), traits=("technical", "information_dense"), density=5),
    "accessible": component_profile(form_spec("accessible_minimal", "single_column", 1), traits=("minimal", "accessible"), density=2, visual_weight=2, section_energy="quiet"),
}
