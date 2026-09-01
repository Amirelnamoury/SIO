# Header component blueprints

Count: 25

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `classic_brand_left` | `classic` / `classic_horizontal` | balanced | - / - | - / - | 3 | 2 | `stack_priority_order` / text brand and compact accessible navigation |
| `split_navigation` | `classic` / `classic_horizontal` | balanced | - / - | - / - | 3 | 2 | `stack_priority_order` / text brand and compact accessible navigation |
| `compact_sticky_nav` | `classic` / `classic_horizontal` | balanced | - / - | - / - | 3 | 2 | `stack_priority_order` / text brand and compact accessible navigation |
| `framed_canvas_header` | `classic` / `classic_horizontal` | balanced | - / - | - / - | 3 | 2 | `stack_priority_order` / text brand and compact accessible navigation |
| `centered_brand_quiet` | `centered` / `centered_brand` | centered, quiet | - / - | - / - | 2 | 2 | `stack_priority_order` / text brand and compact accessible navigation |
| `minimal_logo_only` | `centered` / `centered_brand` | centered, quiet | - / - | - / - | 2 | 2 | `stack_priority_order` / text brand and compact accessible navigation |
| `utility_contact_bar` | `contact` / `contact_utility` | conversion_led, phone_first | - / email, phone | - / - | 4 | 3 | `bottom_action` / text brand and compact accessible navigation |
| `phone_first_compact` | `contact` / `contact_utility` | conversion_led, phone_first | phone / - | - / - | 4 | 3 | `bottom_action` / text brand and compact accessible navigation |
| `mega_contact_header` | `contact` / `contact_utility` | conversion_led, phone_first | - / email, phone | - / - | 4 | 3 | `bottom_action` / text brand and compact accessible navigation |
| `conversion_action_dock_header` | `contact` / `contact_utility` | conversion_led, phone_first | - / email, phone | - / - | 4 | 3 | `bottom_action` / text brand and compact accessible navigation |
| `transparent_overlay_nav` | `overlay` / `transparent_overlay` | cinematic, full_bleed | - / - | - / - | 2 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `dark_overlay_nav` | `overlay` / `transparent_overlay` | cinematic, full_bleed | - / - | - / - | 2 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `editorial_index_nav` | `editorial` / `editorial_index` | asymmetric, editorial | - / - | - / - | 3 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `oversized_menu_trigger` | `editorial` / `editorial_index` | asymmetric, editorial | - / - | - / - | 3 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `architectural_side_rail` | `rail` / `architectural_rail` | architectural, rail | - / - | - / - | 3 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `side_rail_projects` | `rail` / `architectural_rail` | architectural, rail | - / - | - / - | 3 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `two_row_local` | `local` / `local_information` | local, trust_led | city / - | - / - | 4 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `local_info_strip` | `local` / `local_information` | local, trust_led | city / - | - / - | 4 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `residential_project_header` | `local` / `local_information` | local, trust_led | city / - | - / - | 4 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `blueprint_utility_header` | `technical` / `technical_utility` | information_dense, technical | - / - | - / - | 5 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `service_category_header` | `technical` / `technical_utility` | information_dense, technical | - / - | - / - | 5 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
| `floating_capsule_nav` | `statement` / `statement_brand` | bold, minimal | - / - | - / - | 1 | 4 | `stack_priority_order` / text brand and compact accessible navigation |
| `workshop_mark_header` | `statement` / `statement_brand` | bold, minimal | - / - | - / - | 1 | 4 | `stack_priority_order` / text brand and compact accessible navigation |
| `statement_wordmark_header` | `statement` / `statement_brand` | bold, minimal | - / - | - / - | 1 | 4 | `stack_priority_order` / text brand and compact accessible navigation |
| `gallery_bottom_nav` | `gallery` / `gallery_navigation` | portfolio, visual_led | - / - | - / - | 2 | 3 | `stack_priority_order` / text brand and compact accessible navigation |
