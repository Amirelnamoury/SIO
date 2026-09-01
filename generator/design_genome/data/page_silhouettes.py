"""Thirty narrative page silhouettes, not interchangeable section stacks."""

from ..models import PageSilhouette


def _s(id, sections, archetypes, optional, forbidden, data, density, images, trust, conversion, mobile, traits):
    return PageSilhouette(
        id=id,
        sections=tuple(sections.split()),
        target_archetypes=frozenset(archetypes.split()),
        optional_sections=frozenset(optional.split()),
        forbidden_sections=frozenset(forbidden.split()),
        minimum_data=frozenset(data.split()),
        maximum_density=density,
        expected_image_count=images,
        trust_requirements=frozenset(trust.split()),
        conversion_intensity=conversion,
        mobile_transformation=mobile,
        traits=frozenset(traits.split()),
    )


PAGE_SILHOUETTES = {
    item.id: item for item in (
        _s("local_conversion", "header hero trust services area reviews faq contact footer", "conversion_first_local family_business", "reviews faq area", "before_after", "services city", 5, (0, 4), "", .92, "cta_first_stack", "local conversion_led service_led"),
        _s("premium_residential", "header hero manifesto services gallery about process contact footer", "premium_residential quiet_luxury", "gallery about process", "emergency", "services", 3, (3, 10), "", .52, "editorial_sequence", "luxurious visual_led story_led"),
        _s("project_ledger", "header hero featured_project project_grid services about reviews contact footer", "project_portfolio architectural_contracting", "reviews about", "stock_projects", "project_media", 3, (6, 18), "", .34, "project_cards_to_rail", "portfolio project_led architectural"),
        _s("technical_capabilities", "utility_header hero capabilities process technical_details proof area contact footer", "technical_expert industrial_specialist spatial_technical", "proof area", "decorative_reviews", "services", 5, (1, 6), "", .66, "technical_compact", "technical information_dense trust_led"),
        _s("craft_material_story", "header hero materials services process workshop gallery contact footer", "high_end_craft material_led heritage_craft", "workshop gallery", "emergency", "services", 3, (3, 12), "", .38, "material_swipe", "warm tactile material_led"),
        _s("cinematic_residential", "overlay_header hero story projects before_after testimonial contact footer", "luxury_renovation premium_residential", "before_after testimonial", "dense_table", "services", 3, (5, 14), "", .42, "cinematic_to_chapters", "cinematic visual_led story_led"),
        _s("urgent_local", "phone_header problem_hero urgent_actions services area trust faq contact footer", "local_emergency_service", "trust faq area", "manifesto", "services phone emergency_service", 5, (0, 3), "emergency_service", .98, "sticky_call", "phone_first conversion_led local"),
        _s("minimal_statement", "quiet_header statement_hero projects services about contact footer", "minimal_architecture quiet_luxury", "projects about", "stats_strip", "services", 2, (0, 8), "", .22, "quiet_stack", "minimal quiet architectural"),
        _s("quote_first_service", "header quote_hero service_index process proof form footer", "conversion_first_local technical_expert", "proof process", "cinematic_gallery", "services", 5, (0, 4), "", .90, "form_first", "quote_first conversion_led service_led"),
        _s("phone_first_service", "phone_header compact_hero issue_index services area contact footer", "local_emergency_service conversion_first_local", "area", "manifesto", "services phone", 5, (0, 2), "", .96, "bottom_call_dock", "phone_first local compact"),
        _s("editorial_residential", "index_header editorial_hero essay gallery selected_services about contact footer", "premium_residential editorial_studio", "gallery about", "utility_table", "services", 2, (4, 12), "", .30, "magazine_stack", "editorial story_led luxurious"),
        _s("architectural_contracting", "rail_header hero project_intro capabilities project_grid process contact footer", "architectural_contracting design_build", "process", "reviews_carousel", "services", 4, (4, 12), "", .45, "rail_to_index", "architectural project_led technical"),
        _s("specification_first", "utility_header technical_hero specification services process proof contact footer", "technical_expert industrial_specialist", "proof", "decorative_quote", "services", 5, (0, 5), "", .62, "accordion_spec", "technical information_dense"),
        _s("family_trust", "local_header hero family_story services proof reviews area contact footer", "family_business", "reviews proof area", "spatial_canvas", "services", 4, (1, 6), "", .68, "trust_before_story", "warm local trust_led"),
        _s("local_service_story", "header hero story services process area contact footer", "family_business warm_artisan", "process area", "project_grid", "services", 4, (1, 6), "", .60, "linear_story", "local story_led warm"),
        _s("transformation_story", "overlay_header hero before_after narrative services process projects contact footer", "luxury_renovation design_build", "before_after projects", "stock_before_after", "services", 3, (4, 14), "", .48, "paired_transformations", "story_led project_led cinematic"),
        _s("industrial_capabilities", "utility_header hero sectors capabilities process certifications contact footer", "industrial_specialist", "certifications sectors", "playful_gallery", "services", 5, (1, 7), "", .58, "capability_accordion", "industrial technical information_dense"),
        _s("magazine_service", "editorial_header cover_hero contents services essays gallery contact footer", "editorial_studio material_led", "essays gallery", "sticky_quote", "services", 3, (2, 10), "", .25, "contents_to_tabs", "magazine editorial story_led"),
        _s("warm_artisan", "atelier_header hero introduction services process workshop contact footer", "warm_artisan family_business", "process workshop", "technical_table", "services", 3, (1, 8), "", .58, "warm_compact", "warm local craft"),
        _s("bold_local", "bold_header oversized_hero services proof area reviews contact footer", "bold_local conversion_first_local", "proof reviews area", "quiet_essay", "services", 5, (0, 5), "", .88, "bold_action_stack", "bold local conversion_led"),
        _s("documentary_process", "quiet_header documentary_hero process_chapters services people gallery contact footer", "documentary_craft high_end_craft", "people gallery", "stock_projects", "services", 3, (5, 16), "", .30, "chapter_scroll", "documentary story_led craft"),
        _s("design_build_journey", "header hero brief design build reveal services contact footer", "design_build luxury_renovation", "reveal", "emergency", "services", 4, (4, 14), "", .50, "phase_accordion", "story_led project_led architectural"),
        _s("heritage_story", "classic_header hero heritage materials process projects contact footer", "heritage_craft", "projects", "futuristic_canvas", "services", 3, (3, 12), "", .28, "heritage_chapters", "heritage warm material_led"),
        _s("spatial_explainer", "minimal_header spatial_hero system_map capabilities process contact footer", "spatial_technical technical_expert", "system_map", "heavy_gallery", "services", 4, (0, 5), "", .44, "static_diagram", "spatial technical layered"),
        _s("material_library", "index_header macro_hero material_index services applications gallery contact footer", "material_led high_end_craft", "gallery applications", "emergency", "services", 3, (6, 18), "", .24, "material_carousel", "material tactile visual_led"),
        _s("quiet_luxury", "minimal_header statement_hero selected_services image_sequence about contact footer", "quiet_luxury premium_residential", "image_sequence about", "stats_strip", "services", 2, (2, 8), "", .24, "quiet_sequence", "quiet luxurious minimal"),
        _s("gallery_sequence", "overlay_header visual_hero gallery_sequence service_links about contact footer", "project_portfolio material_led", "about", "dense_proof", "services project_media", 2, (8, 20), "", .22, "horizontal_to_vertical", "visual_led portfolio cinematic"),
        _s("editorial_manifesto", "index_header type_hero manifesto services visual_break about contact footer", "editorial_studio material_led", "visual_break about", "utility_table", "services", 2, (0, 6), "", .20, "type_scale_reduction", "editorial story_led quiet"),
        _s("service_matrix", "utility_header compact_hero service_matrix process proof faq contact footer", "technical_expert conversion_first_local", "proof faq", "cinematic_story", "services", 5, (0, 4), "", .76, "matrix_to_accordion", "service_led information_dense conversion_led"),
        _s("before_after_casebook", "header hero casebook before_after services process contact footer", "luxury_renovation documentary_craft", "casebook", "stock_before_after", "services before_after", 3, (6, 20), "", .40, "paired_sliders_to_stack", "project_led documentary transformation"),
    )
}


assert len(PAGE_SILHOUETTES) == 30
