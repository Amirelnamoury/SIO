# Blueprint differentiation audit

Distances are pure renderer-structure comparisons: `0.00` is exact, `<0.15` is near-duplicate, `0.15-0.40` is a related family variant, and `>0.40` is meaningfully different.

## Before and after

| Category | Components | Families | V1.1 unique | V1.2 unique | Exact duplicates | Near pairs | Minimum intra-family |
|---|---:|---:|---:|---:|---:|---:|---:|
| header | 25 | 10 | 10 | 25 | 0 | 11 | 0.3237 |
| hero | 50 | 12 | 12 | 50 | 0 | 0 | 0.32 |
| services | 35 | 13 | 13 | 35 | 0 | 34 | 0.3317 |
| gallery | 30 | 9 | 9 | 30 | 0 | 9 | 0.346 |
| about | 20 | 10 | 10 | 20 | 0 | 4 | 0.346 |
| trust | 20 | 17 | 17 | 20 | 0 | 63 | 0.3513 |
| cta | 25 | 9 | 9 | 25 | 0 | 32 | 0.346 |
| contact | 20 | 11 | 11 | 20 | 0 | 28 | 0.3513 |
| footer | 20 | 10 | 10 | 20 | 0 | 18 | 0.3376 |
| form | 15 | 6 | 6 | 15 | 0 | 14 | 0.343 |

V1.1 had 107 unique structural blueprints for 260 IDs. V1.2 has 260 unique fingerprints. No alias is currently necessary.

## Header

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `local_info_strip` | `phone_first_compact` | 0.0831 |
| `mega_contact_header` | `residential_project_header` | 0.0831 |
| `two_row_local` | `utility_contact_bar` | 0.0831 |
| `architectural_side_rail` | `gallery_bottom_nav` | 0.1324 |
| `editorial_index_nav` | `architectural_side_rail` | 0.1352 |
| `oversized_menu_trigger` | `side_rail_projects` | 0.1352 |
| `centered_brand_quiet` | `classic_brand_left` | 0.1460 |
| `minimal_logo_only` | `split_navigation` | 0.1460 |
| `compact_sticky_nav` | `residential_project_header` | 0.1706 |
| `blueprint_utility_header` | `two_row_local` | 0.1751 |
| `service_category_header` | `local_info_strip` | 0.1751 |
| `floating_capsule_nav` | `editorial_index_nav` | 0.1866 |
| `workshop_mark_header` | `oversized_menu_trigger` | 0.1866 |
| `conversion_action_dock_header` | `framed_canvas_header` | 0.1884 |
| `statement_wordmark_header` | `compact_sticky_nav` | 0.1906 |
| `dark_overlay_nav` | `minimal_logo_only` | 0.2043 |
| `transparent_overlay_nav` | `centered_brand_quiet` | 0.2043 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Hero

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `centered_image_frame` | `framed_luxury_scene` | 0.1580 |
| `cinematic_overlay_story` | `full_bleed_photo_cover` | 0.1580 |
| `layered_material_scene` | `photo_right_residential_intro` | 0.1580 |
| `material_macro_title` | `photo_left_service_intro` | 0.1580 |
| `offset_residential_photo` | `workshop_gesture_cover` | 0.1580 |
| `panorama_architectural` | `quiet_luxury_window` | 0.1580 |
| `parallax_layered_material` | `split_service_photo` | 0.1580 |
| `asymmetric_project_intro` | `vertical_portrait_manifesto` | 0.2081 |
| `horizontal_rail_preview` | `project_contact_sheet_hero` | 0.2081 |
| `before_after_transformation_pair` | `project_contact_sheet_hero` | 0.2215 |
| `documentary_work_log_hero` | `residential_brief_intro` | 0.2230 |
| `gallery_led_sequence` | `offset_residential_photo` | 0.2230 |
| `project_canvas_feature` | `split_service_photo` | 0.2230 |
| `compact_conversion_panel` | `condensed_industrial_capability` | 0.2347 |
| `diagrammatic_process_map` | `service_led_selector` | 0.2347 |
| `edge_crop_conversion` | `mono_technical_diagnostic` | 0.2347 |
| `framed_blueprint_specification` | `quote_first_project_brief` | 0.2347 |
| `phone_first_problem_solution` | `technical_nodes_network` | 0.2347 |
| `editorial_photo_collage` | `horizontal_rail_preview` | 0.2573 |
| `floating_image_statement` | `vertical_portrait_manifesto` | 0.2573 |
| `diptych_transformation_intro` | `workshop_gesture_cover` | 0.2683 |
| `stacked_photos_narrative` | `parallax_layered_material` | 0.2683 |
| `lighting_atmosphere_cover` | `offset_residential_photo` | 0.2765 |
| `triptych_material_intro` | `residential_brief_intro` | 0.2816 |
| `blueprint_spatial_scene` | `mono_technical_diagnostic` | 0.2894 |
| `isometric_system_explainer` | `condensed_industrial_capability` | 0.2894 |
| `architectural_void_statement` | `oversized_type_local` | 0.3200 |
| `brutalist_block_intro` | `oversized_type_local` | 0.3200 |
| `centered_statement_quiet` | `oversized_type_local` | 0.3200 |
| `editorial_columns_manifesto` | `oversized_type_local` | 0.3200 |
| `editorial_title_index` | `oversized_type_local` | 0.3200 |
| `no_image_editorial_manifesto` | `oversized_type_local` | 0.3200 |
| `no_image_local_conversion` | `oversized_type_local` | 0.3200 |
| `no_image_typographic_signal` | `oversized_type_local` | 0.3200 |

## Services

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `material_service_catalogue` | `photo_service_cards` | 0.0741 |
| `project_type_services` | `split_service_media` | 0.0741 |
| `icon_service_grid` | `process_like_services` | 0.0914 |
| `service_timeline` | `stacked_service_panels` | 0.0914 |
| `editorial_service_rows` | `large_typographic_service_index` | 0.1148 |
| `local_service_directory` | `numbered_service_list` | 0.1148 |
| `scope_of_work_ledger` | `sticky_service_detail` | 0.1148 |
| `capability_specification` | `service_masonry` | 0.1226 |
| `service_bento` | `technical_system_layers` | 0.1226 |
| `service_matrix` | `technical_service_table` | 0.1226 |
| `horizontal_service_rail` | `icon_service_grid` | 0.1242 |
| `conversion_service_selector` | `stacked_service_panels` | 0.1262 |
| `problem_solution_services` | `icon_service_grid` | 0.1262 |
| `residential_room_services` | `service_map_and_list` | 0.1262 |
| `alternating_service_feature` | `service_comparison_columns` | 0.1287 |
| `workshop_service_samples` | `residential_room_services` | 0.1493 |
| `compact_mobile_service_actions` | `local_service_directory` | 0.1535 |
| `service_accordion` | `large_typographic_service_index` | 0.1535 |
| `brutalist_service_stack` | `service_matrix` | 0.1549 |
| `cinematic_service_reveal` | `service_masonry` | 0.1549 |
| `minimal_service_links` | `editorial_service_rows` | 0.1610 |
| `editorial_service_folio` | `editorial_service_rows` | 0.3317 |
| `quiet_service_chapters` | `editorial_service_rows` | 0.3317 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Gallery

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `alternating_project_stories` | `artisan_project_cards` | 0.1456 |
| `artisan_casebook_rail` | `residential_room_sequence` | 0.1456 |
| `artisan_project_grid` | `editorial_project_folio` | 0.1456 |
| `cinematic_chapter_gallery` | `featured_project_monument` | 0.1456 |
| `project_contact_sheet` | `quiet_captioned_gallery` | 0.1456 |
| `gallery_with_material_index` | `featured_project_monument` | 0.1494 |
| `image_diptych` | `artisan_project_cards` | 0.1494 |
| `image_triptych` | `project_contact_sheet` | 0.1494 |
| `material_gallery_macro` | `artisan_project_grid` | 0.1494 |
| `before_after_transformation_pairs` | `artisan_project_grid` | 0.2017 |
| `documentary_work_log` | `horizontal_gallery_scroll` | 0.2151 |
| `asymmetric_gallery_mosaic` | `inspiration_gallery_mosaic` | 0.2212 |
| `framed_canvas_gallery` | `lighting_atmosphere_gallery` | 0.2212 |
| `masonry_image_archive` | `visual_atmosphere_sequence` | 0.2212 |
| `portrait_landscape_dialogue` | `artisan_casebook_rail` | 0.2237 |
| `stock_ambient_collage` | `cinematic_chapter_gallery` | 0.2237 |
| `construction_progress_ledger` | `framed_canvas_gallery` | 0.2346 |
| `workshop_documentary_gallery` | `masonry_image_archive` | 0.2346 |
| `mobile_swipe_gallery` | `horizontal_gallery_scroll` | 0.2375 |
| `full_bleed_image_sequence` | `featured_project_monument` | 0.2394 |
| `technical_detail_archive` | `artisan_project_grid` | 0.3460 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## About

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `craft_values_index` | `framed_quote_about` | 0.1248 |
| `founder_story_split` | `material_philosophy` | 0.1248 |
| `residential_approach_about` | `craft_values_index` | 0.1320 |
| `simple_business_identity` | `material_philosophy` | 0.1320 |
| `local_commitment_about` | `workshop_documentary_about` | 0.1515 |
| `process_manifesto` | `service_area_story` | 0.1515 |
| `heritage_timeline_about` | `workshop_documentary_about` | 0.1577 |
| `project_context_about` | `workshop_documentary_about` | 0.1577 |
| `team_portrait_about` | `workshop_documentary_about` | 0.1577 |
| `technical_expertise_about` | `founder_story_split` | 0.1944 |
| `design_build_method` | `studio_statement_about` | 0.2212 |
| `brutalist_factless_about` | `residential_approach_about` | 0.2351 |
| `mobile_compact_about` | `studio_statement_about` | 0.2351 |
| `quiet_editorial_about` | `simple_business_identity` | 0.2351 |
| `people_and_tools_about` | `workshop_documentary_about` | 0.3460 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Trust

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `artisan_project_evidence` | `before_after_evidence` | 0.0659 |
| `verified_brand_authorizations` | `verified_partner_directory` | 0.0659 |
| `combined_verified_fact_strip` | `verified_awards_ledger` | 0.0872 |
| `verified_certification_badges` | `verified_brand_authorizations` | 0.0872 |
| `verified_opening_hours` | `verified_awards_ledger` | 0.0872 |
| `verified_team_credentials` | `verified_certification_badges` | 0.0927 |
| `verified_insurance_line` | `verified_response_delay` | 0.1006 |
| `verified_service_area_map` | `verified_brand_authorizations` | 0.1006 |
| `verified_emergency_availability` | `verified_review_excerpt` | 0.1085 |
| `verified_guarantee_statement` | `verified_response_delay` | 0.1085 |
| `minimal_verified_fact_index` | `verified_review_summary` | 0.1140 |
| `documented_process_proof` | `verified_review_excerpt` | 0.1219 |
| `verified_project_statistics` | `verified_team_credentials` | 0.1240 |
| `verified_client_statistics` | `verified_review_summary` | 0.1374 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Cta

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `material_sample_cta` | `project_brief_cta` | 0.0585 |
| `residential_consultation_cta` | `technical_diagnostic_cta` | 0.0585 |
| `service_specific_cta` | `split_project_cta` | 0.0585 |
| `minimal_contact_link` | `minimal_email_cta` | 0.0758 |
| `availability_checked_cta` | `quote_first_cta` | 0.0914 |
| `compact_request_cta` | `site_visit_cta` | 0.0914 |
| `dual_action_contact_cta` | `project_gallery_cta` | 0.0914 |
| `footer_conversion_cta` | `residential_consultation_cta` | 0.0914 |
| `location_aware_cta` | `sticky_quote_cta` | 0.0914 |
| `monumental_statement_cta` | `minimal_contact_link` | 0.1025 |
| `callback_request_cta` | `footer_conversion_cta` | 0.1163 |
| `floating_phone_action` | `location_aware_cta` | 0.1163 |
| `mobile_action_dock_cta` | `compact_request_cta` | 0.1163 |
| `phone_first_cta` | `availability_checked_cta` | 0.1163 |
| `side_information_cta` | `location_aware_cta` | 0.1549 |
| `emergency_phone_cta` | `quote_first_cta` | 0.1744 |
| `quiet_editorial_cta` | `footer_conversion_cta` | 0.1744 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Contact

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `local_map_contact` | `split_form_contact` | 0.0638 |
| `residential_project_contact` | `service_area_contact` | 0.0638 |
| `compact_request_contact` | `residential_project_contact` | 0.0851 |
| `footer_contact_conversion` | `workshop_visit_contact` | 0.0851 |
| `quote_first_contact` | `local_map_contact` | 0.0851 |
| `project_brief_contact` | `technical_diagnostic_contact` | 0.0985 |
| `emergency_contact` | `sticky_contact_panel` | 0.1197 |
| `multi_channel_contact` | `project_brief_contact` | 0.1197 |
| `floating_contact_action` | `compact_request_contact` | 0.1447 |
| `mobile_action_contact` | `footer_contact_conversion` | 0.1447 |
| `phone_first_contact` | `local_map_contact` | 0.1447 |
| `editorial_contact_statement` | `quote_first_contact` | 0.1624 |
| `dark_overlay_contact` | `floating_contact_action` | 0.1794 |
| `minimal_contact` | `quote_first_contact` | 0.1891 |
| `side_information_contact` | `compact_request_contact` | 0.1891 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Footer

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `business_information_footer` | `navigation_columns_footer` | 0.0334 |
| `editorial_directory_footer` | `local_business_footer` | 0.0334 |
| `service_links_footer` | `business_information_footer` | 0.0334 |
| `contact_first_footer` | `service_area_footer` | 0.0769 |
| `project_index_footer` | `contact_first_footer` | 0.0802 |
| `technical_spec_footer` | `service_links_footer` | 0.1061 |
| `legal_compact_footer` | `editorial_directory_footer` | 0.1563 |
| `ultra_minimal_footer` | `business_information_footer` | 0.1563 |
| `cta_footer_hybrid` | `local_business_footer` | 0.1663 |
| `centered_mark_footer` | `split_contact_footer` | 0.1830 |
| `dark_overlay_footer` | `oversized_wordmark_footer` | 0.1830 |
| `large_brand_statement_footer` | `visual_image_footer` | 0.1830 |
| `workshop_signature_footer` | `centered_mark_footer` | 0.2256 |
| `mobile_action_footer` | `contact_first_footer` | 0.3376 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

## Form

### Closest structural pairs

| Component | Closest | Distance |
|---|---|---:|
| `accordion_mobile_form` | `site_visit_request_form` | 0.0425 |
| `compact_callback_form` | `single_column_quote_form` | 0.0425 |
| `contact_details_form` | `emergency_minimal_form` | 0.0425 |
| `accessible_minimal_form` | `single_column_quote_form` | 0.0580 |
| `multi_step_project_brief` | `split_project_form` | 0.0985 |
| `residential_scope_form` | `service_selector_form` | 0.0985 |
| `technical_diagnostic_form` | `split_project_form` | 0.1352 |
| `full_page_enquiry_form` | `single_column_quote_form` | 0.3430 |
| `inline_footer_form` | `single_column_quote_form` | 0.3430 |
| `material_consultation_form` | `single_column_quote_form` | 0.3430 |

Near pairs remain explicitly visible for renderer review; they are not hidden by identity labels.

