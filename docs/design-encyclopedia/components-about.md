# About component blueprints

Count: 20

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `simple_business_identity` | `identity` / `business_identity` | story_led | - / - | - / - | 2 | 2 | `stack_priority_order` / text narrative without factual embellishment |
| `residential_approach_about` | `identity` / `business_identity` | story_led | - / - | - / - | 2 | 2 | `stack_priority_order` / text narrative without factual embellishment |
| `studio_statement_about` | `identity` / `business_identity` | story_led | - / - | - / - | 2 | 2 | `stack_priority_order` / text narrative without factual embellishment |
| `founder_story_split` | `founder` / `founder_story` | story_led, warm | - / founder, team | - / - | 2 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `framed_quote_about` | `founder` / `founder_story` | story_led, warm | - / founder, team | - / - | 2 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `workshop_documentary_about` | `documentary` / `documentary_process` | documentary, warm | process / - | - / - | 3 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `process_manifesto` | `documentary` / `documentary_process` | documentary, warm | process / - | - / - | 3 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `design_build_method` | `documentary` / `documentary_process` | documentary, warm | process / - | - / - | 3 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `people_and_tools_about` | `documentary` / `documentary_process` | documentary, warm | process / - | - / - | 3 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `material_philosophy` | `material` / `material_philosophy` | editorial, material | - / - | - / - | 2 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `craft_values_index` | `material` / `material_philosophy` | editorial, material | - / - | - / - | 2 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `local_commitment_about` | `local` / `local_commitment` | local, trust_led | city / - | - / - | 3 | 2 | `stack_priority_order` / text narrative without factual embellishment |
| `service_area_story` | `local` / `local_commitment` | local, trust_led | city / - | - / - | 3 | 2 | `stack_priority_order` / text narrative without factual embellishment |
| `team_portrait_about` | `team` / `team_portrait` | trust_led, warm | team / - | portrait / - | 3 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `heritage_timeline_about` | `heritage` / `heritage_timeline` | editorial, heritage | history / - | - / - | 3 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `technical_expertise_about` | `technical` / `technical_expertise` | information_dense, technical | process / - | - / - | 4 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `project_context_about` | `project` / `project_context` | project_led, story_led | - / - | artisan_project / - | 3 | 3 | `stack_priority_order` / text narrative without factual embellishment |
| `quiet_editorial_about` | `minimal` / `quiet_statement` | minimal, quiet | - / - | - / - | 1 | 2 | `stack_priority_order` / text narrative without factual embellishment |
| `brutalist_factless_about` | `minimal` / `quiet_statement` | minimal, quiet | - / - | - / - | 1 | 2 | `stack_priority_order` / text narrative without factual embellishment |
| `mobile_compact_about` | `minimal` / `quiet_statement` | minimal, quiet | - / - | - / - | 1 | 2 | `stack_priority_order` / text narrative without factual embellishment |
