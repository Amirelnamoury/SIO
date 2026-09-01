# Trust component blueprints

Count: 20

Every ID is opaque: semantics come from the explicit profile, constraints and resolved blueprint spec.

| ID | Profile / layout | Traits | Data (all / any) | Media (all / any) | Density | Weight | Mobile / fallback |
|---|---|---|---|---|---:|---:|---|
| `verified_insurance_line` | `insurance` / `verified_line` | trust_led | insurance / - | - / - | 2 | 2 | `stack_priority_order` / omit trust block |
| `verified_certification_badges` | `certifications` / `verified_badges` | technical, trust_led | certifications / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
| `verified_review_excerpt` | `reviews` / `verified_reviews` | trust_led | reviews / - | - / - | 3 | 3 | `stack_priority_order` / omit trust block |
| `verified_review_summary` | `reviews` / `verified_reviews` | trust_led | reviews / - | - / - | 3 | 3 | `stack_priority_order` / omit trust block |
| `verified_project_statistics` | `statistics` / `verified_statistics` | information_dense, trust_led | statistics / - | - / - | 4 | 3 | `stack_priority_order` / omit trust block |
| `verified_client_statistics` | `statistics` / `verified_statistics` | information_dense, trust_led | statistics / - | - / - | 4 | 3 | `stack_priority_order` / omit trust block |
| `verified_team_credentials` | `team` / `team_credentials` | trust_led, warm | team / - | - / - | 3 | 3 | `stack_priority_order` / omit trust block |
| `verified_service_area_map` | `area` / `service_area` | local, trust_led | service_areas / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
| `verified_partner_directory` | `partners` / `partner_directory` | trust_led | partners / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
| `verified_brand_authorizations` | `brands` / `brand_authorizations` | trust_led | brands / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
| `verified_awards_ledger` | `awards` / `awards_ledger` | editorial, trust_led | awards / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
| `verified_guarantee_statement` | `guarantee` / `guarantee_statement` | trust_led | guarantee / - | - / - | 2 | 2 | `stack_priority_order` / omit trust block |
| `verified_opening_hours` | `hours` / `opening_hours` | local, trust_led | opening_hours / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
| `verified_emergency_availability` | `emergency` / `emergency_availability` | conversion_led, trust_led | emergency_service / - | - / - | 3 | 3 | `stack_priority_order` / omit trust block |
| `verified_response_delay` | `response` / `response_delay` | conversion_led, trust_led | response_delay / - | - / - | 2 | 2 | `stack_priority_order` / omit trust block |
| `documented_process_proof` | `process` / `documented_process` | story_led, trust_led | process / - | - / - | 3 | 3 | `stack_priority_order` / omit trust block |
| `artisan_project_evidence` | `project` / `artisan_project_evidence` | project_led, trust_led | - / - | artisan_project / - | 3 | 3 | `stack_priority_order` / omit trust block |
| `before_after_evidence` | `before_after` / `before_after_evidence` | project_led, trust_led | - / - | before_after / - | 3 | 3 | `stack_priority_order` / omit trust block |
| `combined_verified_fact_strip` | `facts` / `verified_fact_index` | trust_led | verified_facts / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
| `minimal_verified_fact_index` | `facts` / `verified_fact_index` | trust_led | verified_facts / - | - / - | 3 | 2 | `stack_priority_order` / omit trust block |
