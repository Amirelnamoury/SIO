# Cta component blueprints

Count: 25

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `phone_first_cta` | `phone` / `phone_action` | conversion_led, phone_first | phone / - | - / - | 3 | 3 | `bottom_action` / single honest contact action |
| `floating_phone_action` | `phone` / `phone_action` | conversion_led, phone_first | phone / - | - / - | 3 | 3 | `bottom_action` / single honest contact action |
| `callback_request_cta` | `phone` / `phone_action` | conversion_led, phone_first | phone / - | - / - | 3 | 3 | `bottom_action` / single honest contact action |
| `mobile_action_dock_cta` | `phone` / `phone_action` | conversion_led, phone_first | phone / - | - / - | 3 | 3 | `bottom_action` / single honest contact action |
| `quote_first_cta` | `quote` / `quote_action` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `sticky_quote_cta` | `quote` / `quote_action` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `footer_conversion_cta` | `quote` / `quote_action` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `compact_request_cta` | `quote` / `quote_action` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `dual_action_contact_cta` | `quote` / `quote_action` | conversion_led, quote_first | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `minimal_contact_link` | `contact` / `contact_prompt` | conversion_led | - / email, phone | - / - | 2 | 2 | `stack_priority_order` / single honest contact action |
| `side_information_cta` | `contact` / `contact_prompt` | conversion_led | - / email, phone | - / - | 2 | 2 | `stack_priority_order` / single honest contact action |
| `quiet_editorial_cta` | `contact` / `contact_prompt` | conversion_led | - / email, phone | - / - | 2 | 2 | `stack_priority_order` / single honest contact action |
| `split_project_cta` | `project` / `project_enquiry` | conversion_led, project_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `project_brief_cta` | `project` / `project_enquiry` | conversion_led, project_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `residential_consultation_cta` | `project` / `project_enquiry` | conversion_led, project_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `site_visit_cta` | `project` / `project_enquiry` | conversion_led, project_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `project_gallery_cta` | `project` / `project_enquiry` | conversion_led, project_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `emergency_phone_cta` | `emergency` / `emergency_phone` | conversion_led, phone_first | emergency_service, phone / - | - / - | 4 | 4 | `stack_priority_order` / single honest contact action |
| `minimal_email_cta` | `email` / `email_link` | conversion_led, minimal | email / - | - / - | 1 | 2 | `stack_priority_order` / single honest contact action |
| `availability_checked_cta` | `availability` / `availability_checked` | conversion_led, trust_led | availability / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `location_aware_cta` | `availability` / `availability_checked` | conversion_led, trust_led | availability / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `service_specific_cta` | `material` / `material_consultation` | conversion_led, material | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `material_sample_cta` | `material` / `material_consultation` | conversion_led, material | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `technical_diagnostic_cta` | `material` / `material_consultation` | conversion_led, material | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / single honest contact action |
| `monumental_statement_cta` | `statement` / `monumental_action` | bold, conversion_led | - / email, phone | - / - | 2 | 5 | `stack_priority_order` / single honest contact action |
