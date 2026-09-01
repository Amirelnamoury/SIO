# Contact component blueprints

Count: 20

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `phone_first_contact` | `phone` / `phone_first` | conversion_led, phone_first | phone / - | - / - | 3 | 3 | `bottom_action` / verified contact details only |
| `floating_contact_action` | `phone` / `phone_first` | conversion_led, phone_first | phone / - | - / - | 3 | 3 | `bottom_action` / verified contact details only |
| `mobile_action_contact` | `phone` / `phone_first` | conversion_led, phone_first | phone / - | - / - | 3 | 3 | `bottom_action` / verified contact details only |
| `quote_first_contact` | `quote` / `quote_first` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `compact_request_contact` | `quote` / `quote_first` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `footer_contact_conversion` | `quote` / `quote_first` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `minimal_contact` | `minimal` / `minimal_details` | conversion_led, minimal, quiet | - / email, phone | - / - | 1 | 2 | `stack_priority_order` / verified contact details only |
| `side_information_contact` | `minimal` / `minimal_details` | conversion_led, minimal, quiet | - / email, phone | - / - | 1 | 2 | `stack_priority_order` / verified contact details only |
| `split_form_contact` | `split` / `split_details_form` | conversion_led, split | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `residential_project_contact` | `split` / `split_details_form` | conversion_led, split | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `sticky_contact_panel` | `panel` / `persistent_panel` | conversion_led, layered | - / email, phone | - / - | 4 | 4 | `stack_priority_order` / verified contact details only |
| `dark_overlay_contact` | `panel` / `persistent_panel` | conversion_led, layered | - / email, phone | - / - | 4 | 4 | `stack_priority_order` / verified contact details only |
| `project_brief_contact` | `project` / `project_brief` | conversion_led, project_led | - / email, phone | - / - | 4 | 3 | `stack_priority_order` / verified contact details only |
| `emergency_contact` | `emergency` / `emergency_contact` | conversion_led, phone_first | emergency_service, phone / - | - / - | 4 | 4 | `stack_priority_order` / verified contact details only |
| `local_map_contact` | `local` / `local_context` | conversion_led, local, trust_led | service_areas / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `service_area_contact` | `local` / `local_context` | conversion_led, local, trust_led | service_areas / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `workshop_visit_contact` | `local` / `local_context` | conversion_led, local, trust_led | service_areas / email, phone | - / - | 3 | 3 | `stack_priority_order` / verified contact details only |
| `technical_diagnostic_contact` | `technical` / `technical_diagnostic` | conversion_led, technical | - / email, phone | - / - | 4 | 3 | `stack_priority_order` / verified contact details only |
| `editorial_contact_statement` | `editorial` / `editorial_statement` | conversion_led, editorial, quiet | - / email, phone | - / - | 2 | 3 | `stack_priority_order` / verified contact details only |
| `multi_channel_contact` | `channels` / `multi_channel` | conversion_led, information_dense | - / email, phone | - / - | 4 | 3 | `stack_priority_order` / verified contact details only |
