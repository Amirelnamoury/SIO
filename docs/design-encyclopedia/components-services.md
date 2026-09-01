# Services component blueprints

Count: 35

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `editorial_service_rows` | `rows` / `editorial_rows` | editorial, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `numbered_service_list` | `rows` / `editorial_rows` | editorial, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `sticky_service_detail` | `rows` / `editorial_rows` | editorial, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `alternating_service_feature` | `rows` / `editorial_rows` | editorial, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `quiet_service_chapters` | `rows` / `editorial_rows` | editorial, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `editorial_service_folio` | `rows` / `editorial_rows` | editorial, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `icon_service_grid` | `grid` / `service_grid` | modular, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `stacked_service_panels` | `grid` / `service_grid` | modular, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `residential_room_services` | `grid` / `service_grid` | modular, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `service_comparison_columns` | `grid` / `service_grid` | modular, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `photo_service_cards` | `photo` / `photo_service_cards` | service_led, visual_led | services / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
| `split_service_media` | `photo` / `photo_service_cards` | service_led, visual_led | services / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
| `horizontal_service_rail` | `rail` / `horizontal_service_rail` | rail, service_led | services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `large_typographic_service_index` | `index` / `typographic_index` | editorial, information_dense | services / - | - / - | 4 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `local_service_directory` | `index` / `typographic_index` | editorial, information_dense | services / - | - / - | 4 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `scope_of_work_ledger` | `index` / `typographic_index` | editorial, information_dense | services / - | - / - | 4 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `service_accordion` | `accordion` / `service_accordion` | compact, service_led | services / - | - / - | 4 | 2 | `stack_priority_order` / text-only services preserving hierarchy |
| `compact_mobile_service_actions` | `accordion` / `service_accordion` | compact, service_led | services / - | - / - | 4 | 2 | `stack_priority_order` / text-only services preserving hierarchy |
| `service_matrix` | `matrix` / `capability_matrix` | information_dense, technical | services / - | - / - | 5 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
| `service_masonry` | `matrix` / `capability_matrix` | information_dense, technical | services / - | - / - | 5 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
| `service_bento` | `matrix` / `capability_matrix` | information_dense, technical | services / - | - / - | 5 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
| `process_like_services` | `process` / `process_services` | service_led, story_led | process, services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `service_timeline` | `process` / `process_services` | service_led, story_led | process, services / - | - / - | 3 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `technical_service_table` | `technical` / `technical_specification` | information_dense, technical | services / - | - / - | 5 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `capability_specification` | `technical` / `technical_specification` | information_dense, technical | services / - | - / - | 5 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `technical_system_layers` | `technical` / `technical_specification` | information_dense, technical | services / - | - / - | 5 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `minimal_service_links` | `minimal` / `minimal_links` | minimal, quiet | services / - | - / - | 2 | 2 | `stack_priority_order` / text-only services preserving hierarchy |
| `brutalist_service_stack` | `bento` / `asymmetric_bento` | bold, modular | services / - | - / - | 4 | 5 | `stack_priority_order` / text-only services preserving hierarchy |
| `cinematic_service_reveal` | `bento` / `asymmetric_bento` | bold, modular | services / - | - / - | 4 | 5 | `stack_priority_order` / text-only services preserving hierarchy |
| `problem_solution_services` | `conversion` / `conversion_selector` | conversion_led, service_led | services / - | - / - | 4 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `conversion_service_selector` | `conversion` / `conversion_selector` | conversion_led, service_led | services / - | - / - | 4 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `service_map_and_list` | `conversion` / `conversion_selector` | conversion_led, service_led | services / - | - / - | 4 | 3 | `stack_priority_order` / text-only services preserving hierarchy |
| `material_service_catalogue` | `material` / `material_catalogue` | material, tactile | services / - | - / - | 3 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
| `project_type_services` | `material` / `material_catalogue` | material, tactile | services / - | - / - | 3 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
| `workshop_service_samples` | `material` / `material_catalogue` | material, tactile | services / - | - / - | 3 | 4 | `stack_priority_order` / text-only services preserving hierarchy |
