# Hero blueprint catalog

All 50 heroes expose a unique structural fingerprint. Distinction is measured from renderer-visible instructions, never the component ID.

## `full_bleed_photo_cover`

- Family / variant: `hero.photo_cover` / `v01`
- Fingerprint: `de0bb2576a0ca70717ff8e5b`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('content', 'media')`; collapse `linear_stack`; priority `content_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `centered_image_frame`

- Family / variant: `hero.photo_cover` / `v02`
- Fingerprint: `9692e7db1615050dca187a00`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('content', 'media')`; collapse `media_then_content`; priority `media_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `panorama_architectural`

- Family / variant: `hero.photo_cover` / `v03`
- Fingerprint: `4bc081e8c95900a61127474a`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('content', 'media')`; collapse `framed_stack`; priority `title_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `lighting_atmosphere_cover`

- Family / variant: `hero.photo_cover` / `v04`
- Fingerprint: `938264bbeb238c190199d204`
- Layout pattern: `full_bleed`
- Desktop composition: `full_bleed_cover`; order `('media', 'content')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('content', 'media')`; collapse `snap_rail`; priority `action_first`.
- Media: `single_full_bleed`; intensity 4; crop `focal_subject_safe`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `photo_left_service_intro`

- Family / variant: `hero.split_photo` / `v01`
- Fingerprint: `10a6ef2b060a9ff3062e72cf`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `linear_stack`; priority `content_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `photo_right_residential_intro`

- Family / variant: `hero.split_photo` / `v02`
- Fingerprint: `66e7c8d070cfabea4855d263`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `media_then_content`; priority `media_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `split_service_photo`

- Family / variant: `hero.split_photo` / `v03`
- Fingerprint: `ceaf92c1e81ab6df2b7afac3`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `framed_stack`; priority `title_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `offset_residential_photo`

- Family / variant: `hero.split_photo` / `v04`
- Fingerprint: `551357f9fe316ff172e4bdfd`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `snap_rail`; priority `action_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `residential_brief_intro`

- Family / variant: `hero.split_photo` / `v05`
- Fingerprint: `76870ac5b9bca24c585d525e`
- Layout pattern: `split`
- Desktop composition: `split_editorial`; order `('content', 'media')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('title', 'media', 'copy', 'actions')`; collapse `separate_layers`; priority `evidence_first`.
- Media: `single_contained`; intensity 3; crop `architectural_context`.
- Edge / type scale: `contained` / `oversized`.
- Distinct because: `layered_progression`, `overlap_mask`, `separate_layers` and `depth_then_action` form one explicit architecture.

## `editorial_photo_collage`

- Family / variant: `hero.collage` / `v01`
- Fingerprint: `db62c1e4f7e620de5ef0435e`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `linear_stack`; priority `content_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `floating_image_statement`

- Family / variant: `hero.collage` / `v02`
- Fingerprint: `536f88e59c36a3dfc6becec1`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `media_then_content`; priority `media_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `stacked_photos_narrative`

- Family / variant: `hero.collage` / `v03`
- Fingerprint: `001c2c7474e210b47fdf6174`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `framed_stack`; priority `title_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `diptych_transformation_intro`

- Family / variant: `hero.collage` / `v04`
- Fingerprint: `96ac69cace2a9e24b41f5801`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `snap_rail`; priority `action_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `triptych_material_intro`

- Family / variant: `hero.collage` / `v05`
- Fingerprint: `df0134533498cad9bd0b9174`
- Layout pattern: `asymmetric`
- Desktop composition: `asymmetric_editorial_collage`; order `('content', 'primary_media', 'secondary_media')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('title', 'primary_media', 'copy', 'secondary_media', 'actions')`; collapse `separate_layers`; priority `evidence_first`.
- Media: `primary_plus_offset_secondary`; intensity 4; crop `mixed_ratio_subject_safe`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `layered_progression`, `overlap_mask`, `separate_layers` and `depth_then_action` form one explicit architecture.

## `cinematic_overlay_story`

- Family / variant: `hero.cinematic` / `v01`
- Fingerprint: `cd20275391d93d419f31206d`
- Layout pattern: `overlay`
- Desktop composition: `cinematic_scene`; order `('media', 'content')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'poster', 'copy', 'actions')`; collapse `linear_stack`; priority `content_first`.
- Media: `single_scene`; intensity 4; crop `wide_environmental`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `framed_luxury_scene`

- Family / variant: `hero.cinematic` / `v02`
- Fingerprint: `62b0bf94c0d088620eac5c28`
- Layout pattern: `overlay`
- Desktop composition: `cinematic_scene`; order `('media', 'content')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'poster', 'copy', 'actions')`; collapse `media_then_content`; priority `media_first`.
- Media: `single_scene`; intensity 4; crop `wide_environmental`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `quiet_luxury_window`

- Family / variant: `hero.cinematic` / `v03`
- Fingerprint: `f8d74c98450e52235aec748e`
- Layout pattern: `overlay`
- Desktop composition: `cinematic_scene`; order `('media', 'content')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('title', 'poster', 'copy', 'actions')`; collapse `framed_stack`; priority `title_first`.
- Media: `single_scene`; intensity 4; crop `wide_environmental`.
- Edge / type scale: `viewport_edge` / `oversized`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `project_contact_sheet_hero`

- Family / variant: `hero.project` / `v01`
- Fingerprint: `2f04a39fa62e5bad12956106`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `linear_stack`; priority `content_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `asymmetric_project_intro`

- Family / variant: `hero.project` / `v02`
- Fingerprint: `893df4aba13402dda8c98cfc`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `media_then_content`; priority `media_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `project_canvas_feature`

- Family / variant: `hero.project` / `v03`
- Fingerprint: `b27b95ce0703b916fcd293bc`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `framed_stack`; priority `title_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `gallery_led_sequence`

- Family / variant: `hero.project` / `v04`
- Fingerprint: `d12efaa336261b9363afb825`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `snap_rail`; priority `action_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `documentary_work_log_hero`

- Family / variant: `hero.project` / `v05`
- Fingerprint: `3cf59714084a227444238610`
- Layout pattern: `grid`
- Desktop composition: `project_evidence_intro`; order `('project_media', 'project_context')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('title', 'project_media', 'verified_context', 'actions')`; collapse `separate_layers`; priority `evidence_first`.
- Media: `project_contact_sheet`; intensity 3; crop `preserve_project_context`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `layered_progression`, `overlap_mask`, `separate_layers` and `depth_then_action` form one explicit architecture.

## `material_macro_title`

- Family / variant: `hero.material` / `v01`
- Fingerprint: `0828ef21d024809317021e2d`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `linear_stack`; priority `content_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `layered_material_scene`

- Family / variant: `hero.material` / `v02`
- Fingerprint: `8c93a304bb9d5c3a7d0db0ab`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `media_then_content`; priority `media_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `parallax_layered_material`

- Family / variant: `hero.material` / `v03`
- Fingerprint: `76c56fc5739a0f7eadd56b2d`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `framed_stack`; priority `title_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `workshop_gesture_cover`

- Family / variant: `hero.material` / `v04`
- Fingerprint: `fdb52a653b414b18fdd0f034`
- Layout pattern: `split`
- Desktop composition: `material_study`; order `('macro', 'title', 'context')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('title', 'macro', 'copy', 'context')`; collapse `snap_rail`; priority `action_first`.
- Media: `macro_plus_context`; intensity 3; crop `material_detail_with_context`.
- Edge / type scale: `offset` / `oversized`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `oversized_type_local`

- Family / variant: `hero.typographic` / `v01`
- Fingerprint: `8a3afe01a1b34963053ff754`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `linear_stack`; priority `content_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `editorial_title_index`

- Family / variant: `hero.typographic` / `v02`
- Fingerprint: `21b0bda5ede7552b5e38b77b`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `media_then_content`; priority `media_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `centered_statement_quiet`

- Family / variant: `hero.typographic` / `v03`
- Fingerprint: `ebef51cd97276b3b9e7f9f83`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `framed_stack`; priority `title_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `editorial_columns_manifesto`

- Family / variant: `hero.typographic` / `v04`
- Fingerprint: `959b7e12b6ef35ab7347dd0b`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `snap_rail`; priority `action_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `no_image_typographic_signal`

- Family / variant: `hero.typographic` / `v05`
- Fingerprint: `1114c6b4614bb9cb9bb39bfb`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `separate_layers`; priority `evidence_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `layered_progression`, `overlap_mask`, `separate_layers` and `depth_then_action` form one explicit architecture.

## `no_image_editorial_manifesto`

- Family / variant: `hero.typographic` / `v06`
- Fingerprint: `c435b60190f1363ab1b83eb8`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `centered_axis`; anchor `central_baseline`; frame `contained_axis`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `centered_stack`; priority `statement_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `centered_axis`, `contained_axis`, `centered_stack` and `center_outward` form one explicit architecture.

## `no_image_local_conversion`

- Family / variant: `hero.typographic` / `v07`
- Fingerprint: `c822b2a5d2a8444c89754be3`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `vertical_chapters`; anchor `chapter_rule`; frame `chapter_dividers`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `chapter_stack`; priority `sequence_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `vertical_chapters`, `chapter_dividers`, `chapter_stack` and `chapter_by_chapter` form one explicit architecture.

## `architectural_void_statement`

- Family / variant: `hero.typographic` / `v08`
- Fingerprint: `9c196f7b556ca527cfa83ff0`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `diagonal_offset`; anchor `asymmetric_intersection`; frame `partial_frame`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `alternating_stack`; priority `contrast_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `diagonal_offset`, `partial_frame`, `alternating_stack` and `diagonal_scan` form one explicit architecture.

## `brutalist_block_intro`

- Family / variant: `hero.typographic` / `v09`
- Fingerprint: `70b34cd2c5335a0934a8b50a`
- Layout pattern: `typographic`
- Desktop composition: `typographic_statement`; order `('eyebrow', 'title', 'copy', 'actions')`; flow `modular_matrix`; anchor `module_baseline`; frame `module_rules`.
- Mobile composition: order `('eyebrow', 'title', 'copy', 'actions')`; collapse `priority_matrix`; priority `primary_module_first`.
- Media: `none`; intensity 0; crop `none`.
- Edge / type scale: `contained` / `monumental`.
- Distinct because: `modular_matrix`, `module_rules`, `priority_matrix` and `module_scan` form one explicit architecture.

## `edge_crop_conversion`

- Family / variant: `hero.conversion` / `v01`
- Fingerprint: `7027d76421fdd7069e0979ca`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `linear_stack`; priority `content_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `compact_conversion_panel`

- Family / variant: `hero.conversion` / `v02`
- Fingerprint: `5c7f92083e79620f34b05c4a`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `media_then_content`; priority `media_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `service_led_selector`

- Family / variant: `hero.conversion` / `v03`
- Fingerprint: `5ae3fef12d877460f90e3f46`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `framed_stack`; priority `title_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `phone_first_problem_solution`

- Family / variant: `hero.conversion` / `v04`
- Fingerprint: `18b947e6e935d9787e02ea28`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `snap_rail`; priority `action_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `quote_first_project_brief`

- Family / variant: `hero.conversion` / `v05`
- Fingerprint: `aca25e2c21de7e688fb0ac7e`
- Layout pattern: `split`
- Desktop composition: `conversion_problem_solution`; order `('problem', 'identity', 'solution', 'actions', 'optional_media')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('identity', 'problem', 'primary_action', 'services_hint', 'optional_media')`; collapse `separate_layers`; priority `evidence_first`.
- Media: `optional_ambient`; intensity 1; crop `supporting_not_claim`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `layered_progression`, `overlap_mask`, `separate_layers` and `depth_then_action` form one explicit architecture.

## `mono_technical_diagnostic`

- Family / variant: `hero.technical` / `v01`
- Fingerprint: `8ab476b2866117d063988493`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `linear_stack`; priority `content_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `condensed_industrial_capability`

- Family / variant: `hero.technical` / `v02`
- Fingerprint: `d120d05dc7aa1e666b2904c3`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `media_then_content`; priority `media_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `diagrammatic_process_map`

- Family / variant: `hero.technical` / `v03`
- Fingerprint: `5ab5eb660052bbe8f25108a4`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `offset_sequence`; anchor `offset_grid_line`; frame `complete_frame`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `framed_stack`; priority `title_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Distinct because: `offset_sequence`, `complete_frame`, `framed_stack` and `frame_then_content` form one explicit architecture.

## `technical_nodes_network`

- Family / variant: `hero.technical` / `v04`
- Fingerprint: `9c2b3e53b4cbe4265c6058ab`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `horizontal_progression`; anchor `viewport_edge`; frame `edge_rule`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `snap_rail`; priority `action_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Distinct because: `horizontal_progression`, `edge_rule`, `snap_rail` and `horizontal_scan` form one explicit architecture.

## `framed_blueprint_specification`

- Family / variant: `hero.technical` / `v05`
- Fingerprint: `d02c2c6167d82c661b7a3b98`
- Layout pattern: `matrix`
- Desktop composition: `technical_explainer`; order `('title', 'capability_summary', 'diagram')`; flow `layered_progression`; anchor `visual_center`; frame `overlap_mask`.
- Mobile composition: order `('title', 'summary', 'static_diagram')`; collapse `separate_layers`; priority `evidence_first`.
- Media: `diagram_or_none`; intensity 1; crop `none_for_diagram`.
- Edge / type scale: `framed` / `large`.
- Distinct because: `layered_progression`, `overlap_mask`, `separate_layers` and `depth_then_action` form one explicit architecture.

## `blueprint_spatial_scene`

- Family / variant: `hero.spatial` / `v01`
- Fingerprint: `f9c2ceb85ad68e7342893c9c`
- Layout pattern: `overlay`
- Desktop composition: `spatial_explainer`; order `('content', 'spatial_explainer')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'static_explainer', 'copy')`; collapse `linear_stack`; priority `content_first`.
- Media: `explanatory_layers`; intensity 1; crop `not_applicable_to_diagram`.
- Edge / type scale: `framed` / `oversized`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `isometric_system_explainer`

- Family / variant: `hero.spatial` / `v02`
- Fingerprint: `8b3e0c2cc1461376e99ce912`
- Layout pattern: `overlay`
- Desktop composition: `spatial_explainer`; order `('content', 'spatial_explainer')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'static_explainer', 'copy')`; collapse `media_then_content`; priority `media_first`.
- Media: `explanatory_layers`; intensity 1; crop `not_applicable_to_diagram`.
- Edge / type scale: `framed` / `oversized`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

## `before_after_transformation_pair`

- Family / variant: `hero.transformation` / `v01`
- Fingerprint: `b409c97aa16f97b3549868e6`
- Layout pattern: `split`
- Desktop composition: `verified_transformation_pair`; order `('verified_pair', 'context')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'before', 'after', 'verified_context')`; collapse `linear_stack`; priority `content_first`.
- Media: `paired_before_after`; intensity 4; crop `matched_framing_no_deceptive_crop`.
- Edge / type scale: `contained` / `large`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `horizontal_rail_preview`

- Family / variant: `hero.rail` / `v01`
- Fingerprint: `de8ed3b0e5eb40c94ce2fe59`
- Layout pattern: `rail`
- Desktop composition: `horizontal_preview_rail`; order `('title', 'rail', 'copy')`; flow `natural_sequence`; anchor `content_start`; frame `unframed`.
- Mobile composition: order `('title', 'snap_rail', 'copy', 'actions')`; collapse `linear_stack`; priority `content_first`.
- Media: `horizontal_rail`; intensity 4; crop `consistent_height_variable_width`.
- Edge / type scale: `viewport_edge` / `large`.
- Distinct because: `natural_sequence`, `unframed`, `linear_stack` and `top_to_bottom` form one explicit architecture.

## `vertical_portrait_manifesto`

- Family / variant: `hero.rail` / `v02`
- Fingerprint: `ba8c23b470213fdd6558f070`
- Layout pattern: `rail`
- Desktop composition: `horizontal_preview_rail`; order `('title', 'rail', 'copy')`; flow `reverse_axis`; anchor `content_end`; frame `inset_rule`.
- Mobile composition: order `('title', 'snap_rail', 'copy', 'actions')`; collapse `media_then_content`; priority `media_first`.
- Media: `horizontal_rail`; intensity 4; crop `consistent_height_variable_width`.
- Edge / type scale: `viewport_edge` / `large`.
- Distinct because: `reverse_axis`, `inset_rule`, `media_then_content` and `edge_to_center` form one explicit architecture.

