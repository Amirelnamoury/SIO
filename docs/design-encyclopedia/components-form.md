# Form component blueprints

Count: 15

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `single_column_quote_form` | `single` / `single_column` | conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `contact_details_form` | `single` / `single_column` | conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `site_visit_request_form` | `single` / `single_column` | conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `material_consultation_form` | `single` / `single_column` | conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `inline_footer_form` | `single` / `single_column` | conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `full_page_enquiry_form` | `single` / `single_column` | conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `split_project_form` | `split` / `split_fields` | conversion_led, split | - / - | - / - | 4 | 3 | `stack_priority_order` / compact accessible enquiry form |
| `residential_scope_form` | `split` / `split_fields` | conversion_led, split | - / - | - / - | 4 | 3 | `stack_priority_order` / compact accessible enquiry form |
| `compact_callback_form` | `compact` / `compact_callback` | compact, conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `emergency_minimal_form` | `compact` / `compact_callback` | compact, conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `accordion_mobile_form` | `compact` / `compact_callback` | compact, conversion_led | - / - | - / - | 3 | 2 | `stack_priority_order` / compact accessible enquiry form |
| `multi_step_project_brief` | `multi_step` / `multi_step` | conversion_led, information_dense | - / - | - / - | 4 | 3 | `stack_priority_order` / compact accessible enquiry form |
| `service_selector_form` | `multi_step` / `multi_step` | conversion_led, information_dense | - / - | - / - | 4 | 3 | `stack_priority_order` / compact accessible enquiry form |
| `technical_diagnostic_form` | `technical` / `technical_scope` | information_dense, technical | - / - | - / - | 5 | 3 | `stack_priority_order` / compact accessible enquiry form |
| `accessible_minimal_form` | `accessible` / `accessible_minimal` | accessible, minimal | - / - | - / - | 2 | 2 | `stack_priority_order` / compact accessible enquiry form |
