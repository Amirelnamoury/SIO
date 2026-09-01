# Hero blueprint catalog

All 50 heroes declare their own composition and design intent. Distinction is measured from renderer-visible instructions, never registry position or the component ID.

## `full_bleed_photo_cover`

- Family / variant: `hero.photo_cover` / `full-bleed-photo-cover`
- Variant source: `explicit`
- Design intent: Lets one environmental image occupy the viewport while edge-anchored copy remains subordinate to place.
- Fingerprint: `1fd986ed79453d11c415cab7`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `layered_progression`; anchor `viewport_edge`; frame `unframed`.
- Mobile composition: order `('content', 'media')`; collapse `crop_then_stack`; priority `media_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Explicit architecture: `layered_progression`, `unframed`, `crop_then_stack` and `environment_to_action`.

## `centered_image_frame`

- Family / variant: `hero.photo_cover` / `centered-image-frame`
- Variant source: `explicit`
- Design intent: Gives one contained architectural image the status of an artwork on a generous centered canvas.
- Fingerprint: `351a2ff77db77f764f259042`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `centered_axis`; anchor `central_baseline`; frame `complete_frame`.
- Mobile composition: order `('content', 'media')`; collapse `framed_stack`; priority `title_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Explicit architecture: `centered_axis`, `complete_frame`, `framed_stack` and `frame_then_content`.

## `panorama_architectural`

- Family / variant: `hero.photo_cover` / `panorama-architectural`
- Variant source: `explicit`
- Design intent: Uses a low panoramic horizon band to prioritize architectural context over cinematic height.
- Fingerprint: `4dafc79ca461a19e95f9ff2c`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `panoramic_band`; anchor `horizon_line`; frame `letterbox_frame`.
- Mobile composition: order `('content', 'media')`; collapse `crop_then_stack`; priority `panorama_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Explicit architecture: `panoramic_band`, `letterbox_frame`, `crop_then_stack` and `horizon_to_detail`.

## `lighting_atmosphere_cover`

- Family / variant: `hero.photo_cover` / `lighting-atmosphere-cover`
- Variant source: `explicit`
- Design intent: Builds a dark image-dominant atmosphere with restrained copy and a measured light-preserving overlay.
- Fingerprint: `798ca16ada3f9dd88bfb28a1`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `layered_progression`; anchor `visual_center`; frame `dark_overlay`.
- Mobile composition: order `('content', 'media')`; collapse `separate_layers`; priority `media_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Explicit architecture: `layered_progression`, `dark_overlay`, `separate_layers` and `light_to_statement`.

## `photo_left_service_intro`

- Family / variant: `hero.split_photo` / `photo-left-service-intro`
- Variant source: `explicit`
- Design intent: Places service context in a left media field and lets the offer read on the right.
- Fingerprint: `9dd5ec8228cbafe22e4edfef`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `media_then_content`; priority `media_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Explicit architecture: `natural_sequence`, `unframed`, `media_then_content` and `media_to_service`.

## `photo_right_residential_intro`

- Family / variant: `hero.split_photo` / `photo-right-residential-intro`
- Variant source: `explicit`
- Design intent: Keeps calm residential copy on the left and a contextual room image on the right.
- Fingerprint: `cdb96e82e4796a11659a7b5d`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `content_then_media`; priority `content_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Explicit architecture: `reverse_axis`, `inset_rule`, `content_then_media` and `statement_to_room`.

## `split_service_photo`

- Family / variant: `hero.split_photo` / `split-service-photo`
- Variant source: `explicit`
- Design intent: Balances a concise service proposition and supporting image as equal split panels.
- Fingerprint: `5e146f38b6bf0b1ef4ba16dc`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `horizontal_progression`; anchor `central_baseline`; frame `complete_frame`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `linear_stack`; priority `content_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Explicit architecture: `horizontal_progression`, `complete_frame`, `linear_stack` and `service_to_evidence`.

## `offset_residential_photo`

- Family / variant: `hero.split_photo` / `offset-residential-photo`
- Variant source: `explicit`
- Design intent: Offsets the residential image from the text baseline to create a quieter editorial rhythm.
- Fingerprint: `5756bdb958f64bef9f0e8c6a`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `diagonal_offset`; anchor `offset_grid_line`; frame `partial_frame`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `alternating_stack`; priority `media_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Explicit architecture: `diagonal_offset`, `partial_frame`, `alternating_stack` and `diagonal_scan`.

## `residential_brief_intro`

- Family / variant: `hero.split_photo` / `residential-brief-intro`
- Variant source: `explicit`
- Design intent: Frames the project brief first, then uses imagery as atmosphere rather than evidence.
- Fingerprint: `56012f89aa2c9a6f45daeb7a`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `vertical_chapters`; anchor `chapter_rule`; frame `chapter_dividers`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `brief_then_media`; priority `statement_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Explicit architecture: `vertical_chapters`, `chapter_dividers`, `brief_then_media` and `brief_to_context`.

## `editorial_photo_collage`

- Family / variant: `hero.collage` / `editorial-photo-collage`
- Variant source: `explicit`
- Design intent: Builds a magazine-like hierarchy from one lead image and offset supporting crops.
- Fingerprint: `8ffeac5c41269b68cd2929bc`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `diagonal_offset`; anchor `asymmetric_intersection`; frame `partial_frame`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `alternating_stack`; priority `media_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `diagonal_offset`, `partial_frame`, `alternating_stack` and `lead_to_support`.

## `floating_image_statement`

- Family / variant: `hero.collage` / `floating-image-statement`
- Variant source: `explicit`
- Design intent: Floats one image against an oversized statement without enclosing either in a card.
- Fingerprint: `fcdb3938c4fc89ece1b9f9ea`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `separate_layers`; priority `statement_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `layered_progression`, `overlap_mask`, `separate_layers` and `statement_to_image`.

## `stacked_photos_narrative`

- Family / variant: `hero.collage` / `stacked-photos-narrative`
- Variant source: `explicit`
- Design intent: Sequences stacked images as chapters around a continuous narrative column.
- Fingerprint: `50af1bec602efc4c6e7ffbc9`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `vertical_chapters`; anchor `chapter_rule`; frame `chapter_dividers`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `chapter_stack`; priority `sequence_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `vertical_chapters`, `chapter_dividers`, `chapter_stack` and `chapter_by_chapter`.

## `diptych_transformation_intro`

- Family / variant: `hero.collage` / `diptych-transformation-intro`
- Variant source: `explicit`
- Design intent: Pairs two verified transformation views with a shared explanatory axis.
- Fingerprint: `bf18b203676997de3be5779b`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `horizontal_progression`; anchor `central_baseline`; frame `complete_frame`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `paired_stack`; priority `evidence_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `horizontal_progression`, `complete_frame`, `paired_stack` and `before_to_after`.

## `triptych_material_intro`

- Family / variant: `hero.collage` / `triptych-material-intro`
- Variant source: `explicit`
- Design intent: Uses three material views at unequal scale to move from context to detail.
- Fingerprint: `4dfea8783ef0c1179d3778c6`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `modular_matrix`; anchor `module_baseline`; frame `module_rules`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `priority_matrix`; priority `primary_module_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `modular_matrix`, `module_rules`, `priority_matrix` and `context_to_detail`.

## `cinematic_overlay_story`

- Family / variant: `hero.cinematic` / `cinematic-overlay-story`
- Variant source: `explicit`
- Design intent: Stages copy as timed story beats over a wide cinematic scene.
- Fingerprint: `b5010fdb5b1991079b977002`
- Layout pattern: `overlay`
- Desktop composition: `cinematic_scene`; order `('media', 'content')`; flow `layered_progression`; anchor `viewport_edge`; frame `dark_overlay`.
- Mobile composition: order `('title', 'poster', 'copy', 'actions')`; collapse `poster_then_chapters`; priority `media_first`.
- Media: `single_scene`; intensity 4; crop `wide_environmental`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Explicit architecture: `layered_progression`, `dark_overlay`, `poster_then_chapters` and `scene_to_story`.

## `framed_luxury_scene`

- Family / variant: `hero.cinematic` / `framed-luxury-scene`
- Variant source: `explicit`
- Design intent: Contains a premium scene inside a precise frame with copy held outside the image plane.
- Fingerprint: `1d7565811ab36ce6228857cb`
- Layout pattern: `overlay`
- Desktop composition: `cinematic_scene`; order `('media', 'content')`; flow `centered_axis`; anchor `frame_inset`; frame `complete_frame`.
- Mobile composition: order `('title', 'poster', 'copy', 'actions')`; collapse `framed_stack`; priority `media_first`.
- Media: `single_scene`; intensity 4; crop `wide_environmental`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Explicit architecture: `centered_axis`, `complete_frame`, `framed_stack` and `frame_then_statement`.

## `quiet_luxury_window`

- Family / variant: `hero.cinematic` / `quiet-luxury-window`
- Variant source: `explicit`
- Design intent: Uses a smaller image window and expansive negative space for restrained residential luxury.
- Fingerprint: `5171ecf5fcc8360ce3c5dbab`
- Layout pattern: `overlay`
- Desktop composition: `cinematic_scene`; order `('media', 'content')`; flow `offset_sequence`; anchor `quiet_grid_line`; frame `inset_rule`.
- Mobile composition: order `('title', 'poster', 'copy', 'actions')`; collapse `window_then_copy`; priority `statement_first`.
- Media: `single_scene`; intensity 4; crop `wide_environmental`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Explicit architecture: `offset_sequence`, `inset_rule`, `window_then_copy` and `void_to_window`.

## `project_contact_sheet_hero`

- Family / variant: `hero.project` / `project-contact-sheet-hero`
- Variant source: `explicit`
- Design intent: Opens with a dense contact sheet of real project evidence and concise context.
- Fingerprint: `09def768366aa45e96e48ba3`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `modular_matrix`; anchor `module_baseline`; frame `module_rules`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `priority_matrix`; priority `evidence_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `modular_matrix`, `module_rules`, `priority_matrix` and `module_scan`.

## `asymmetric_project_intro`

- Family / variant: `hero.project` / `asymmetric-project-intro`
- Variant source: `explicit`
- Design intent: Offsets one lead project view against a narrow verified project summary.
- Fingerprint: `3a2b1fa235d5da6bc270c314`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `diagonal_offset`; anchor `asymmetric_intersection`; frame `partial_frame`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `media_then_context`; priority `evidence_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `diagonal_offset`, `partial_frame`, `media_then_context` and `project_to_context`.

## `project_canvas_feature`

- Family / variant: `hero.project` / `project-canvas-feature`
- Variant source: `explicit`
- Design intent: Presents one project image on a contained gallery canvas with factual context below.
- Fingerprint: `37635d06503746ae1c8efe8c`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `centered_axis`; anchor `central_baseline`; frame `complete_frame`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `framed_stack`; priority `evidence_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `centered_axis`, `complete_frame`, `framed_stack` and `frame_to_context`.

## `gallery_led_sequence`

- Family / variant: `hero.project` / `gallery-led-sequence`
- Variant source: `explicit`
- Design intent: Lets a short project sequence establish evidence before title and action.
- Fingerprint: `5b86111ba2dd7234ee91a669`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `snap_rail`; priority `evidence_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan`.

## `documentary_work_log_hero`

- Family / variant: `hero.project` / `documentary-work-log-hero`
- Variant source: `explicit`
- Design intent: Introduces the site through a chronological set of documented work moments.
- Fingerprint: `eca96195e4f2b2facb62f105`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `vertical_chapters`; anchor `chapter_rule`; frame `chapter_dividers`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `chapter_stack`; priority `sequence_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `vertical_chapters`, `chapter_dividers`, `chapter_stack` and `chapter_by_chapter`.

## `material_macro_title`

- Family / variant: `hero.material` / `material-macro-title`
- Variant source: `explicit`
- Design intent: Places an oversized material crop beside a title calibrated to its texture and scale.
- Fingerprint: `c5e26c95683aae7b14ea65e5`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `media_then_content`; priority `media_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `natural_sequence`, `unframed`, `media_then_content` and `macro_to_title`.

## `layered_material_scene`

- Family / variant: `hero.material` / `layered-material-scene`
- Variant source: `explicit`
- Design intent: Overlaps macro and contextual material views to create depth without invented claims.
- Fingerprint: `343e1ff02b4398d974721fda`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `separate_layers`; priority `media_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `layered_progression`, `overlap_mask`, `separate_layers` and `depth_then_statement`.

## `parallax_layered_material`

- Family / variant: `hero.material` / `parallax-layered-material`
- Variant source: `explicit`
- Design intent: Separates material planes into a measured depth progression with a static mobile recomposition.
- Fingerprint: `912deeabbc3c676b1634e3ba`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `diagonal_offset`; anchor `asymmetric_intersection`; frame `partial_frame`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `separate_layers`; priority `media_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `diagonal_offset`, `partial_frame`, `separate_layers` and `near_to_far`.

## `workshop_gesture_cover`

- Family / variant: `hero.material` / `workshop-gesture-cover`
- Variant source: `explicit`
- Design intent: Centers a documented hand or tool gesture as the emotional entry to craft.
- Fingerprint: `008e0539fc798679bfbfe8eb`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `centered_axis`; anchor `gesture_axis`; frame `contained_axis`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `gesture_then_copy`; priority `media_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Explicit architecture: `centered_axis`, `contained_axis`, `gesture_then_copy` and `gesture_to_identity`.

## `oversized_type_local`

- Family / variant: `hero.typographic` / `oversized-type-local`
- Variant source: `explicit`
- Design intent: Makes locality a bold typographic statement with contact action anchored to its edge.
- Fingerprint: `010969e5a34668b9d9e386c5`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `layered_progression`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `type_then_action`; priority `statement_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `layered_progression`, `unframed`, `type_then_action` and `place_to_action`.

## `editorial_title_index`

- Family / variant: `hero.typographic` / `editorial-title-index`
- Variant source: `explicit`
- Design intent: Composes title, section index and supporting copy as a magazine opening page.
- Fingerprint: `85689967408a1f4ae152f2c0`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `vertical_chapters`; anchor `index_rule`; frame `chapter_dividers`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `index_then_story`; priority `title_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `vertical_chapters`, `chapter_dividers`, `index_then_story` and `index_to_title`.

## `centered_statement_quiet`

- Family / variant: `hero.typographic` / `centered-statement-quiet`
- Variant source: `explicit`
- Design intent: Uses a centered statement and generous whitespace with no competing media plane.
- Fingerprint: `c435b60190f1363ab1b83eb8`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `centered_axis`; anchor `central_baseline`; frame `contained_axis`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `centered_stack`; priority `statement_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `centered_axis`, `contained_axis`, `centered_stack` and `center_outward`.

## `editorial_columns_manifesto`

- Family / variant: `hero.typographic` / `editorial-columns-manifesto`
- Variant source: `explicit`
- Design intent: Breaks a manifesto into asymmetric reading columns under one dominant title.
- Fingerprint: `1d94aa4a845faf1a7c7ed2c2`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `modular_matrix`; anchor `column_baseline`; frame `column_rules`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `chapter_stack`; priority `title_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `modular_matrix`, `column_rules`, `chapter_stack` and `title_to_columns`.

## `no_image_typographic_signal`

- Family / variant: `hero.typographic` / `no-image-typographic-signal`
- Variant source: `explicit`
- Design intent: Uses one sharp typographic signal and minimal support copy as a no-media identity.
- Fingerprint: `44c4c757dab351abb4a5e45e`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `linear_stack`; priority `statement_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `natural_sequence`, `unframed`, `linear_stack` and `signal_to_action`.

## `no_image_editorial_manifesto`

- Family / variant: `hero.typographic` / `no-image-editorial-manifesto`
- Variant source: `explicit`
- Design intent: Creates editorial depth through text hierarchy, rules and deliberate reading pace only.
- Fingerprint: `3b30b0f3d628710134d98f6e`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `vertical_chapters`; anchor `chapter_rule`; frame `chapter_dividers`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `chapter_stack`; priority `title_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `vertical_chapters`, `chapter_dividers`, `chapter_stack` and `chapter_by_chapter`.

## `no_image_local_conversion`

- Family / variant: `hero.typographic` / `no-image-local-conversion`
- Variant source: `explicit`
- Design intent: Combines a local proposition and immediate verified contact path without decorative imagery.
- Fingerprint: `1891d1c3aff756c88aa2a5d4`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `reverse_axis`; anchor `action_edge`; frame `inset_rule`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `action_after_statement`; priority `action_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `reverse_axis`, `inset_rule`, `action_after_statement` and `place_to_action`.

## `architectural_void_statement`

- Family / variant: `hero.typographic` / `architectural-void-statement`
- Variant source: `explicit`
- Design intent: Uses intentional empty space and one offset title as the primary architectural gesture.
- Fingerprint: `30513705dc31bb263a29d695`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `diagonal_offset`; anchor `asymmetric_intersection`; frame `partial_frame`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `void_then_statement`; priority `statement_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `diagonal_offset`, `partial_frame`, `void_then_statement` and `void_to_title`.

## `brutalist_block_intro`

- Family / variant: `hero.typographic` / `brutalist-block-intro`
- Variant source: `explicit`
- Design intent: Locks title, copy and action into rigid edge-aligned blocks with visible structural rules.
- Fingerprint: `c583748b95979928eefef4ae`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `modular_matrix`; anchor `module_baseline`; frame `module_rules`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `priority_matrix`; priority `title_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Explicit architecture: `modular_matrix`, `module_rules`, `priority_matrix` and `block_scan`.

## `edge_crop_conversion`

- Family / variant: `hero.conversion` / `edge-crop-conversion`
- Variant source: `explicit`
- Design intent: Uses a supporting crop at the edge while problem, solution and action remain primary.
- Fingerprint: `c3ab53bc9bf083c162d9943f`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `reverse_axis`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `content_then_media`; priority `action_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `reverse_axis`, `edge_rule`, `content_then_media` and `problem_to_action`.

## `compact_conversion_panel`

- Family / variant: `hero.conversion` / `compact-conversion-panel`
- Variant source: `explicit`
- Design intent: Contains the proposition and one action in a compact high-clarity panel.
- Fingerprint: `527781ad9a20ec513bb5424c`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `centered_axis`; anchor `central_baseline`; frame `complete_frame`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `centered_stack`; priority `action_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `centered_axis`, `complete_frame`, `centered_stack` and `problem_to_action`.

## `service_led_selector`

- Family / variant: `hero.conversion` / `service-led-selector`
- Variant source: `explicit`
- Design intent: Begins with a service choice and progressively reveals the relevant contact action.
- Fingerprint: `3434bdc1826d58b47a360722`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `modular_matrix`; anchor `module_baseline`; frame `module_rules`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `priority_matrix`; priority `primary_module_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `modular_matrix`, `module_rules`, `priority_matrix` and `service_to_action`.

## `phone_first_problem_solution`

- Family / variant: `hero.conversion` / `phone-first-problem-solution`
- Variant source: `explicit`
- Design intent: Moves from customer problem to verified phone action before secondary context.
- Fingerprint: `07c3518dbd9ac52986856879`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `vertical_chapters`; anchor `action_rule`; frame `chapter_dividers`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `phone_action_dock`; priority `action_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `vertical_chapters`, `chapter_dividers`, `phone_action_dock` and `problem_to_phone`.

## `quote_first_project_brief`

- Family / variant: `hero.conversion` / `quote-first-project-brief`
- Variant source: `explicit`
- Design intent: Treats a short project brief as the first conversion step before supporting media.
- Fingerprint: `37247e513bed036cb07a5386`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `natural_sequence`; anchor `content_start`; frame `inset_rule`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `brief_then_media`; priority `action_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `natural_sequence`, `inset_rule`, `brief_then_media` and `brief_to_quote`.

## `mono_technical_diagnostic`

- Family / variant: `hero.technical` / `mono-technical-diagnostic`
- Variant source: `explicit`
- Design intent: Presents a diagnostic statement and capability facts on a strict technical baseline.
- Fingerprint: `bd197e15595e41dc245d8b21`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `modular_matrix`; anchor `module_baseline`; frame `module_rules`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `priority_matrix`; priority `statement_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Explicit architecture: `modular_matrix`, `module_rules`, `priority_matrix` and `diagnostic_scan`.

## `condensed_industrial_capability`

- Family / variant: `hero.technical` / `condensed-industrial-capability`
- Variant source: `explicit`
- Design intent: Condenses capabilities into a narrow industrial ledger beside the title.
- Fingerprint: `cc41f00fa379c89b949eabe2`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `horizontal_progression`; anchor `content_start`; frame `edge_rule`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `ledger_stack`; priority `evidence_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Explicit architecture: `horizontal_progression`, `edge_rule`, `ledger_stack` and `title_to_ledger`.

## `diagrammatic_process_map`

- Family / variant: `hero.technical` / `diagrammatic-process-map`
- Variant source: `explicit`
- Design intent: Uses a process diagram as the central explanatory route from need to outcome.
- Fingerprint: `84d861baba9733157ef4d6a2`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `vertical_chapters`; anchor `process_rule`; frame `chapter_dividers`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `static_process_stack`; priority `sequence_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Explicit architecture: `vertical_chapters`, `chapter_dividers`, `static_process_stack` and `node_by_node`.

## `technical_nodes_network`

- Family / variant: `hero.technical` / `technical-nodes-network`
- Variant source: `explicit`
- Design intent: Organizes capabilities as connected technical nodes around one primary system.
- Fingerprint: `b2e2782184b7c5e1b95196ff`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `modular_matrix`; anchor `network_center`; frame `module_rules`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `priority_matrix`; priority `primary_module_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Explicit architecture: `modular_matrix`, `module_rules`, `priority_matrix` and `center_to_nodes`.

## `framed_blueprint_specification`

- Family / variant: `hero.technical` / `framed-blueprint-specification`
- Variant source: `explicit`
- Design intent: Frames the proposition like a specification sheet with aligned factual modules.
- Fingerprint: `2015d32719891353ca6930e7`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `offset_sequence`; anchor `frame_inset`; frame `complete_frame`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `framed_stack`; priority `title_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Explicit architecture: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_modules`.

## `blueprint_spatial_scene`

- Family / variant: `hero.spatial` / `blueprint-spatial-scene`
- Variant source: `explicit`
- Design intent: Layers a spatial explanation over a restrained blueprint-like coordinate field.
- Fingerprint: `e402bfc8620fbfe4bd7d562f`
- Layout pattern: `overlay`
- Desktop composition: `spatial_explainer`; order `('content', 'spatial_explainer')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('title', 'static_explainer', 'copy')`; collapse `separate_layers`; priority `sequence_first`.
- Media: `explanatory_layers`; intensity 1; crop `not_applicable_to_diagram`.
- Edge / type scale: `framed` / `oversized`.
- Explicit architecture: `layered_progression`, `overlap_mask`, `separate_layers` and `space_to_detail`.

## `isometric_system_explainer`

- Family / variant: `hero.spatial` / `isometric-system-explainer`
- Variant source: `explicit`
- Design intent: Uses an isometric module hierarchy to explain a system without decorative 3D excess.
- Fingerprint: `7a07616c4473e39575f18c05`
- Layout pattern: `overlay`
- Desktop composition: `spatial_explainer`; order `('content', 'spatial_explainer')`; flow `modular_matrix`; anchor `module_baseline`; frame `module_rules`.
- Mobile composition: order `('title', 'static_explainer', 'copy')`; collapse `priority_matrix`; priority `primary_module_first`.
- Media: `explanatory_layers`; intensity 1; crop `not_applicable_to_diagram`.
- Edge / type scale: `framed` / `oversized`.
- Explicit architecture: `modular_matrix`, `module_rules`, `priority_matrix` and `system_to_parts`.

## `before_after_transformation_pair`

- Family / variant: `hero.transformation` / `before-after-transformation-pair`
- Variant source: `explicit`
- Design intent: Keeps a verified before and after pair in one matched comparison frame.
- Fingerprint: `2908ebc52feafd95c715809e`
- Layout pattern: `split`
- Desktop composition: `verified_transformation_pair`; order `('verified_pair', 'context')`; flow `horizontal_progression`; anchor `comparison_axis`; frame `complete_frame`.
- Mobile composition: order `('title', 'before', 'after', 'verified_context')`; collapse `paired_stack`; priority `evidence_first`.
- Media: `paired_before_after`; intensity 4; crop `matched_framing_no_deceptive_crop`.
- Edge / type scale: `contained` / `large`.
- Explicit architecture: `horizontal_progression`, `complete_frame`, `paired_stack` and `before_to_after`.

## `horizontal_rail_preview`

- Family / variant: `hero.rail` / `horizontal-rail-preview`
- Variant source: `explicit`
- Design intent: Previews several visual directions as a horizontal edge-to-edge rail.
- Fingerprint: `0ecafdd396e3cdd408098e3e`
- Layout pattern: `rail`
- Desktop composition: `horizontal_preview_rail`; order `('title', 'rail', 'copy')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('title', 'snap_rail', 'copy', 'actions')`; collapse `snap_rail`; priority `media_first`.
- Media: `horizontal_rail`; intensity 4; crop `consistent_height_variable_width`.
- Edge / type scale: `viewport_edge` / `large`.
- Explicit architecture: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan`.

## `vertical_portrait_manifesto`

- Family / variant: `hero.rail` / `vertical-portrait-manifesto`
- Variant source: `explicit`
- Design intent: Pairs a tall portrait rhythm with a vertically paced manifesto and restrained action.
- Fingerprint: `3005bf7967986208a1c009d4`
- Layout pattern: `rail`
- Desktop composition: `horizontal_preview_rail`; order `('title', 'rail', 'copy')`; flow `vertical_chapters`; anchor `portrait_axis`; frame `inset_rule`.
- Mobile composition: order `('title', 'snap_rail', 'copy', 'actions')`; collapse `portrait_then_chapters`; priority `statement_first`.
- Media: `horizontal_rail`; intensity 4; crop `consistent_height_variable_width`.
- Edge / type scale: `viewport_edge` / `large`.
- Explicit architecture: `vertical_chapters`, `inset_rule`, `portrait_then_chapters` and `portrait_to_manifesto`.

