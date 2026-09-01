# Gallery component blueprints

Count: 30

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `inspiration_gallery_mosaic` | `ambient` / `ambient_mosaic` | visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `visual_atmosphere_sequence` | `ambient` / `ambient_mosaic` | visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `lighting_atmosphere_gallery` | `ambient` / `ambient_mosaic` | visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `stock_ambient_collage` | `ambient` / `ambient_mosaic` | visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `portrait_landscape_dialogue` | `ambient` / `ambient_mosaic` | visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `artisan_project_grid` | `project` / `project_grid` | portfolio, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `artisan_project_cards` | `project` / `project_grid` | portfolio, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `project_contact_sheet` | `project` / `project_grid` | portfolio, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `featured_project_monument` | `project` / `project_grid` | portfolio, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `residential_room_sequence` | `project` / `project_grid` | portfolio, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `technical_detail_archive` | `project` / `project_grid` | portfolio, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `before_after_transformation_pairs` | `before_after` / `before_after_pairs` | documentary, project_led | - / - | before_after / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `asymmetric_gallery_mosaic` | `masonry` / `masonry_archive` | masonry, visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `masonry_image_archive` | `masonry` / `masonry_archive` | masonry, visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `framed_canvas_gallery` | `masonry` / `masonry_archive` | masonry, visual_led | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `horizontal_gallery_scroll` | `rail` / `horizontal_rail` | rail, visual_led | - / - | - / artisan_photo, artisan_project, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `editorial_project_folio` | `editorial_project` / `editorial_casebook` | editorial, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `alternating_project_stories` | `editorial_project` / `editorial_casebook` | editorial, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `quiet_captioned_gallery` | `editorial_project` / `editorial_casebook` | editorial, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `cinematic_chapter_gallery` | `editorial_project` / `editorial_casebook` | editorial, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `artisan_casebook_rail` | `editorial_project` / `editorial_casebook` | editorial, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `material_gallery_macro` | `material` / `material_study` | material, tactile | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `image_diptych` | `material` / `material_study` | material, tactile | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `image_triptych` | `material` / `material_study` | material, tactile | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `gallery_with_material_index` | `material` / `material_study` | material, tactile | - / - | - / artisan_photo, stock_photo | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `documentary_work_log` | `documentary` / `documentary_work_log` | documentary, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `workshop_documentary_gallery` | `documentary` / `documentary_work_log` | documentary, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `construction_progress_ledger` | `documentary` / `documentary_work_log` | documentary, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `full_bleed_image_sequence` | `documentary` / `documentary_work_log` | documentary, project_led | - / - | artisan_project / - | 3 | 4 | `stack_priority_order` / omit when minimum honest media is unavailable |
| `mobile_swipe_gallery` | `mobile` / `mobile_swipe` | compact, visual_led | - / - | - / artisan_photo, artisan_project, stock_photo | 3 | 3 | `stack_priority_order` / omit when minimum honest media is unavailable |
