# Blueprint differentiation audit

Distances are pure renderer-structure comparisons: `0.00` is exact, `<0.15` is near-duplicate, `0.15-0.40` is a related family variant, and `>0.40` is meaningfully different.

## Before and after

| Category | Components | Families | V1.1 unique | V1.2.1 explicit unique | Exact duplicates | Near pairs | Minimum intra-family |
|---|---:|---:|---:|---:|---:|---:|---:|
| header | 25 | 10 | 10 | 25 | 0 | 1 | 0.2145 |
| hero | 50 | 12 | 12 | 50 | 0 | 0 | 0.161 |
| services | 35 | 13 | 13 | 35 | 0 | 0 | 0.1605 |
| gallery | 30 | 9 | 9 | 30 | 0 | 0 | 0.1644 |
| about | 20 | 10 | 10 | 20 | 0 | 0 | 0.2301 |
| trust | 20 | 17 | 17 | 20 | 0 | 0 | 0.2317 |
| cta | 25 | 9 | 9 | 25 | 0 | 2 | 0.1666 |
| contact | 20 | 11 | 11 | 20 | 0 | 0 | 0.2317 |
| footer | 20 | 10 | 10 | 20 | 0 | 3 | 0.1684 |
| form | 15 | 6 | 6 | 15 | 0 | 1 | 0.1701 |

## V1.2 POSITIONAL SYSTEM REMOVED

Before: V1.2 selected one of ten structural variants from each component's tuple position by `enumerate()` and modulo.

After: V1.2.1 resolves every component through an explicit `StructuralVariantSpec` keyed by component ID. Reordering a family or registry leaves variant IDs, structural specs and fingerprints unchanged.

`design_intent` and identity labels remain outside the fingerprint. Only merged renderer instructions create structural novelty.

V1.1 had 107 unique structural blueprints for 260 IDs. V1.2.1 reports the honest explicit count below; no alias is currently necessary.

## Reviewed V1.2 near pairs

| Left | Right | V1.2.1 distance | Decision |
|---|---|---:|---|
| `local_info_strip` | `phone_first_compact` | 0.4068 | retained: horizontal local facts versus phone-priority action |
| `mega_contact_header` | `residential_project_header` | 0.4068 | retained: contact matrix versus calm project navigation |
| `two_row_local` | `utility_contact_bar` | 0.2974 | retained: locality-led hierarchy versus generic verified utility |
| `centered_image_frame` | `framed_luxury_scene` | 0.3922 | retained: artwork-like centered canvas versus luxury scene and external copy |
| `cinematic_overlay_story` | `full_bleed_photo_cover` | 0.4068 | retained: chapter-led cinematic narrative versus environmental cover |
| `layered_material_scene` | `photo_right_residential_intro` | 0.5016 | retained: overlapping material depth versus conventional residential split |
| `material_macro_title` | `photo_left_service_intro` | 0.2457 | retained: texture-scale study versus service-led split |
| `panorama_architectural` | `quiet_luxury_window` | 0.5617 | retained: horizon band versus small image window and intentional void |

No reviewed pair is an alias or merge: each now carries a useful renderer-visible difference and an explicit design intent.

## Header

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `centered_brand_quiet` | `split_navigation` | 0.1460 |
| `conversion_action_dock_header` | `phone_first_compact` | 0.2145 |
| `dark_overlay_nav` | `transparent_overlay_nav` | 0.2145 |
| `blueprint_utility_header` | `mega_contact_header` | 0.2474 |
| `classic_brand_left` | `minimal_logo_only` | 0.2512 |
| `framed_canvas_header` | `classic_brand_left` | 0.2692 |
| `local_info_strip` | `two_row_local` | 0.2692 |
| `statement_wordmark_header` | `workshop_mark_header` | 0.2692 |
| `compact_sticky_nav` | `local_info_strip` | 0.2796 |
| `utility_contact_bar` | `two_row_local` | 0.2974 |
| `architectural_side_rail` | `side_rail_projects` | 0.3237 |
| `editorial_index_nav` | `oversized_menu_trigger` | 0.3237 |
| `floating_capsule_nav` | `statement_wordmark_header` | 0.3237 |
| `residential_project_header` | `two_row_local` | 0.3237 |
| `service_category_header` | `blueprint_utility_header` | 0.3237 |
| `gallery_bottom_nav` | `side_rail_projects` | 0.3470 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Hero

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `editorial_title_index` | `no_image_editorial_manifesto` | 0.1610 |
| `mono_technical_diagnostic` | `technical_nodes_network` | 0.1610 |
| `no_image_typographic_signal` | `oversized_type_local` | 0.1610 |
| `editorial_columns_manifesto` | `no_image_editorial_manifesto` | 0.2110 |
| `layered_material_scene` | `parallax_layered_material` | 0.2110 |
| `compact_conversion_panel` | `edge_crop_conversion` | 0.2113 |
| `brutalist_block_intro` | `editorial_columns_manifesto` | 0.2132 |
| `material_macro_title` | `photo_left_service_intro` | 0.2457 |
| `gallery_led_sequence` | `horizontal_rail_preview` | 0.2626 |
| `architectural_void_statement` | `oversized_type_local` | 0.2655 |
| `asymmetric_project_intro` | `project_contact_sheet_hero` | 0.2655 |
| `centered_statement_quiet` | `oversized_type_local` | 0.2655 |
| `cinematic_overlay_story` | `framed_luxury_scene` | 0.2655 |
| `phone_first_problem_solution` | `edge_crop_conversion` | 0.2655 |
| `project_canvas_feature` | `project_contact_sheet_hero` | 0.2655 |
| `quote_first_project_brief` | `edge_crop_conversion` | 0.2655 |
| `workshop_gesture_cover` | `material_macro_title` | 0.2655 |
| `no_image_local_conversion` | `oversized_type_local` | 0.2658 |
| `photo_right_residential_intro` | `split_service_photo` | 0.2871 |
| `offset_residential_photo` | `photo_left_service_intro` | 0.3009 |
| `full_bleed_photo_cover` | `lighting_atmosphere_cover` | 0.3032 |
| `documentary_work_log_hero` | `stacked_photos_narrative` | 0.3057 |
| `before_after_transformation_pair` | `diptych_transformation_intro` | 0.3120 |
| `blueprint_spatial_scene` | `isometric_system_explainer` | 0.3200 |
| `condensed_industrial_capability` | `mono_technical_diagnostic` | 0.3200 |
| `diagrammatic_process_map` | `mono_technical_diagnostic` | 0.3200 |
| `editorial_photo_collage` | `diptych_transformation_intro` | 0.3200 |
| `floating_image_statement` | `editorial_photo_collage` | 0.3200 |
| `framed_blueprint_specification` | `mono_technical_diagnostic` | 0.3200 |
| `quiet_luxury_window` | `cinematic_overlay_story` | 0.3200 |
| `service_led_selector` | `edge_crop_conversion` | 0.3200 |
| `triptych_material_intro` | `editorial_photo_collage` | 0.3200 |
| `vertical_portrait_manifesto` | `horizontal_rail_preview` | 0.3200 |
| `residential_brief_intro` | `split_service_photo` | 0.3420 |
| `panorama_architectural` | `full_bleed_photo_cover` | 0.3643 |
| `centered_image_frame` | `framed_luxury_scene` | 0.3922 |

## Services

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `editorial_service_rows` | `quiet_service_chapters` | 0.1605 |
| `service_bento` | `service_matrix` | 0.2104 |
| `icon_service_grid` | `residential_room_services` | 0.2210 |
| `material_service_catalogue` | `photo_service_cards` | 0.2390 |
| `alternating_service_feature` | `sticky_service_detail` | 0.2755 |
| `large_typographic_service_index` | `scope_of_work_ledger` | 0.2755 |
| `capability_specification` | `technical_service_table` | 0.2772 |
| `numbered_service_list` | `editorial_service_rows` | 0.2772 |
| `problem_solution_services` | `service_map_and_list` | 0.2772 |
| `process_like_services` | `service_timeline` | 0.2772 |
| `service_comparison_columns` | `stacked_service_panels` | 0.2772 |
| `split_service_media` | `photo_service_cards` | 0.2772 |
| `stacked_service_panels` | `residential_room_services` | 0.2772 |
| `workshop_service_samples` | `material_service_catalogue` | 0.2772 |
| `horizontal_service_rail` | `service_timeline` | 0.2891 |
| `conversion_service_selector` | `icon_service_grid` | 0.2911 |
| `brutalist_service_stack` | `cinematic_service_reveal` | 0.3317 |
| `compact_mobile_service_actions` | `service_accordion` | 0.3317 |
| `editorial_service_folio` | `editorial_service_rows` | 0.3317 |
| `local_service_directory` | `large_typographic_service_index` | 0.3317 |
| `project_type_services` | `material_service_catalogue` | 0.3317 |
| `service_masonry` | `service_matrix` | 0.3317 |
| `technical_system_layers` | `technical_service_table` | 0.3317 |
| `minimal_service_links` | `stacked_service_panels` | 0.3588 |

## Gallery

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `artisan_project_grid` | `project_contact_sheet` | 0.1644 |
| `inspiration_gallery_mosaic` | `stock_ambient_collage` | 0.2227 |
| `artisan_project_cards` | `featured_project_monument` | 0.2282 |
| `documentary_work_log` | `full_bleed_image_sequence` | 0.2282 |
| `cinematic_chapter_gallery` | `full_bleed_image_sequence` | 0.2394 |
| `image_triptych` | `artisan_project_grid` | 0.2652 |
| `asymmetric_gallery_mosaic` | `inspiration_gallery_mosaic` | 0.2755 |
| `alternating_project_stories` | `editorial_project_folio` | 0.2843 |
| `artisan_casebook_rail` | `editorial_project_folio` | 0.2843 |
| `framed_canvas_gallery` | `asymmetric_gallery_mosaic` | 0.2843 |
| `image_diptych` | `material_gallery_macro` | 0.2843 |
| `lighting_atmosphere_gallery` | `inspiration_gallery_mosaic` | 0.2843 |
| `masonry_image_archive` | `asymmetric_gallery_mosaic` | 0.2843 |
| `portrait_landscape_dialogue` | `inspiration_gallery_mosaic` | 0.2843 |
| `quiet_captioned_gallery` | `cinematic_chapter_gallery` | 0.2843 |
| `technical_detail_archive` | `artisan_project_grid` | 0.2843 |
| `workshop_documentary_gallery` | `full_bleed_image_sequence` | 0.2843 |
| `horizontal_gallery_scroll` | `mobile_swipe_gallery` | 0.2991 |
| `construction_progress_ledger` | `documentary_work_log` | 0.3460 |
| `gallery_with_material_index` | `material_gallery_macro` | 0.3460 |
| `residential_room_sequence` | `artisan_project_grid` | 0.3460 |
| `visual_atmosphere_sequence` | `inspiration_gallery_mosaic` | 0.3460 |
| `before_after_transformation_pairs` | `image_diptych` | 0.3738 |

## About

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `mobile_compact_about` | `quiet_editorial_about` | 0.2301 |
| `local_commitment_about` | `simple_business_identity` | 0.2487 |
| `design_build_method` | `workshop_documentary_about` | 0.2843 |
| `process_manifesto` | `workshop_documentary_about` | 0.2843 |
| `residential_approach_about` | `simple_business_identity` | 0.2843 |
| `founder_story_split` | `framed_quote_about` | 0.2898 |
| `team_portrait_about` | `technical_expertise_about` | 0.3103 |
| `heritage_timeline_about` | `design_build_method` | 0.3242 |
| `brutalist_factless_about` | `quiet_editorial_about` | 0.3460 |
| `craft_values_index` | `material_philosophy` | 0.3460 |
| `people_and_tools_about` | `workshop_documentary_about` | 0.3460 |
| `service_area_story` | `local_commitment_about` | 0.3460 |
| `studio_statement_about` | `simple_business_identity` | 0.3460 |
| `project_context_about` | `residential_approach_about` | 0.3658 |

## Trust

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `verified_insurance_line` | `verified_response_delay` | 0.1585 |
| `verified_certification_badges` | `verified_partner_directory` | 0.1994 |
| `verified_client_statistics` | `verified_project_statistics` | 0.2317 |
| `verified_brand_authorizations` | `verified_partner_directory` | 0.2360 |
| `artisan_project_evidence` | `before_after_evidence` | 0.2397 |
| `verified_awards_ledger` | `verified_opening_hours` | 0.2610 |
| `verified_review_summary` | `verified_awards_ledger` | 0.2877 |
| `combined_verified_fact_strip` | `minimal_verified_fact_index` | 0.2897 |
| `verified_review_excerpt` | `verified_review_summary` | 0.2897 |
| `verified_team_credentials` | `verified_review_summary` | 0.2956 |
| `verified_guarantee_statement` | `verified_review_excerpt` | 0.3767 |
| `verified_service_area_map` | `verified_brand_authorizations` | 0.3903 |
| `verified_emergency_availability` | `verified_service_area_map` | 0.4053 |
| `documented_process_proof` | `verified_review_summary` | 0.4152 |

## Cta

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `minimal_contact_link` | `minimal_email_cta` | 0.1300 |
| `quote_first_cta` | `residential_consultation_cta` | 0.1456 |
| `dual_action_contact_cta` | `footer_conversion_cta` | 0.1666 |
| `split_project_cta` | `dual_action_contact_cta` | 0.2018 |
| `compact_request_cta` | `site_visit_cta` | 0.2072 |
| `callback_request_cta` | `split_project_cta` | 0.2267 |
| `floating_phone_action` | `sticky_quote_cta` | 0.2267 |
| `phone_first_cta` | `floating_phone_action` | 0.2282 |
| `service_specific_cta` | `site_visit_cta` | 0.2305 |
| `monumental_statement_cta` | `quiet_editorial_cta` | 0.2765 |
| `availability_checked_cta` | `location_aware_cta` | 0.2843 |
| `mobile_action_dock_cta` | `phone_first_cta` | 0.2843 |
| `project_brief_cta` | `split_project_cta` | 0.2843 |
| `technical_diagnostic_cta` | `service_specific_cta` | 0.2843 |
| `project_gallery_cta` | `split_project_cta` | 0.2898 |
| `material_sample_cta` | `service_specific_cta` | 0.3460 |
| `side_information_cta` | `minimal_contact_link` | 0.3460 |
| `emergency_phone_cta` | `mobile_action_dock_cta` | 0.4026 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Contact

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `quote_first_contact` | `split_form_contact` | 0.2009 |
| `dark_overlay_contact` | `sticky_contact_panel` | 0.2317 |
| `floating_contact_action` | `phone_first_contact` | 0.2317 |
| `mobile_action_contact` | `floating_contact_action` | 0.2354 |
| `compact_request_contact` | `quote_first_contact` | 0.2897 |
| `footer_contact_conversion` | `quote_first_contact` | 0.2897 |
| `local_map_contact` | `service_area_contact` | 0.2897 |
| `minimal_contact` | `side_information_contact` | 0.2897 |
| `workshop_visit_contact` | `local_map_contact` | 0.2897 |
| `multi_channel_contact` | `technical_diagnostic_contact` | 0.2935 |
| `residential_project_contact` | `split_form_contact` | 0.3513 |
| `emergency_contact` | `mobile_action_contact` | 0.3842 |
| `project_brief_contact` | `technical_diagnostic_contact` | 0.3881 |
| `editorial_contact_statement` | `quote_first_contact` | 0.4557 |

## Footer

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `business_information_footer` | `navigation_columns_footer` | 0.0876 |
| `service_links_footer` | `business_information_footer` | 0.1410 |
| `contact_first_footer` | `split_contact_footer` | 0.1684 |
| `cta_footer_hybrid` | `mobile_action_footer` | 0.1684 |
| `technical_spec_footer` | `service_links_footer` | 0.2137 |
| `large_brand_statement_footer` | `oversized_wordmark_footer` | 0.2226 |
| `editorial_directory_footer` | `navigation_columns_footer` | 0.2760 |
| `legal_compact_footer` | `ultra_minimal_footer` | 0.2760 |
| `workshop_signature_footer` | `large_brand_statement_footer` | 0.2760 |
| `local_business_footer` | `editorial_directory_footer` | 0.3177 |
| `centered_mark_footer` | `ultra_minimal_footer` | 0.3376 |
| `dark_overlay_footer` | `visual_image_footer` | 0.3376 |
| `project_index_footer` | `service_links_footer` | 0.3421 |
| `service_area_footer` | `split_contact_footer` | 0.3611 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Form

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `accessible_minimal_form` | `single_column_quote_form` | 0.1123 |
| `accordion_mobile_form` | `contact_details_form` | 0.1542 |
| `full_page_enquiry_form` | `contact_details_form` | 0.1701 |
| `material_consultation_form` | `contact_details_form` | 0.1701 |
| `site_visit_request_form` | `contact_details_form` | 0.1701 |
| `residential_scope_form` | `split_project_form` | 0.1738 |
| `compact_callback_form` | `emergency_minimal_form` | 0.2280 |
| `inline_footer_form` | `compact_callback_form` | 0.2738 |
| `service_selector_form` | `technical_diagnostic_form` | 0.3049 |
| `multi_step_project_brief` | `split_project_form` | 0.3256 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

