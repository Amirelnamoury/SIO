# Footer component blueprints

Count: 20

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `ultra_minimal_footer` | `minimal` / `minimal` | minimal, quiet | - / - | - / - | 1 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `legal_compact_footer` | `minimal` / `minimal` | minimal, quiet | - / - | - / - | 1 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `centered_mark_footer` | `minimal` / `minimal` | minimal, quiet | - / - | - / - | 1 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `business_information_footer` | `business` / `business_information` | information_dense | - / - | - / - | 4 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `local_business_footer` | `business` / `business_information` | information_dense | - / - | - / - | 4 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `navigation_columns_footer` | `navigation` / `navigation_columns` | modular | - / - | - / - | 4 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `editorial_directory_footer` | `navigation` / `navigation_columns` | modular | - / - | - / - | 4 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `service_links_footer` | `services` / `service_directory` | service_led | services / - | - / - | 4 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `service_area_footer` | `area` / `service_area` | local | service_areas / - | - / - | 3 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `contact_first_footer` | `contact` / `contact_first` | conversion_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / brand, contact and legal minimum |
| `cta_footer_hybrid` | `contact` / `contact_first` | conversion_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / brand, contact and legal minimum |
| `split_contact_footer` | `contact` / `contact_first` | conversion_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / brand, contact and legal minimum |
| `mobile_action_footer` | `contact` / `contact_first` | conversion_led | - / email, phone | - / - | 3 | 3 | `stack_priority_order` / brand, contact and legal minimum |
| `large_brand_statement_footer` | `statement` / `brand_statement` | bold, editorial | - / - | - / - | 2 | 4 | `stack_priority_order` / brand, contact and legal minimum |
| `oversized_wordmark_footer` | `statement` / `brand_statement` | bold, editorial | - / - | - / - | 2 | 4 | `stack_priority_order` / brand, contact and legal minimum |
| `workshop_signature_footer` | `statement` / `brand_statement` | bold, editorial | - / - | - / - | 2 | 4 | `stack_priority_order` / brand, contact and legal minimum |
| `project_index_footer` | `project` / `project_index` | project_led | - / - | artisan_project / - | 3 | 3 | `stack_priority_order` / brand, contact and legal minimum |
| `technical_spec_footer` | `technical` / `technical_spec` | information_dense, technical | - / - | - / - | 5 | 2 | `stack_priority_order` / brand, contact and legal minimum |
| `visual_image_footer` | `visual` / `visual_close` | visual_led | - / - | - / artisan_photo, stock_photo | 2 | 4 | `stack_priority_order` / brand, contact and legal minimum |
| `dark_overlay_footer` | `visual` / `visual_close` | visual_led | - / - | - / artisan_photo, stock_photo | 2 | 4 | `stack_priority_order` / brand, contact and legal minimum |
