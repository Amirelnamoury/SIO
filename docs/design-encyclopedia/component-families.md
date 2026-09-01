# Component families

A family is a shared visual grammar. A variant is a renderer-visible structural decision, never a synonym or an ID-derived guess.

## `about.documentary`

- Purpose: about composition using `documentary_process`.
- Visual grammar: `rows`; `contained` edge; media intensity 2; `large` type role.
- Members: `workshop_documentary_about`, `process_manifesto`, `design_build_method`, `people_and_tools_about`.
- Variants: `workshop-documentary-about`, `process-manifesto`, `design-build-method`, `people-and-tools-about`.
- Design intents: Narrates documented workshop practice as a sequence of real process moments.; Sets an honest process manifesto beside its explicit method stages.; Explains design and build as connected phases on one practical timeline.; Balances verified people context with documented tools and process imagery.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2843.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 2.
- Mobile behavior: `chapter_stack`.

## `about.founder`

- Purpose: about composition using `founder_story`.
- Visual grammar: `split`; `contained` edge; media intensity 2; `large` type role.
- Members: `founder_story_split`, `framed_quote_about`.
- Variants: `founder-story-split`, `framed-quote-about`.
- Design intents: Pairs a verified founder portrait or role with the business story.; Frames an attributed quote separately from supporting founder context.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2898.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 2.
- Mobile behavior: `media_then_content`.

## `about.heritage`

- Purpose: about composition using `heritage_timeline`.
- Visual grammar: `timeline`; `contained` edge; media intensity 2; `large` type role.
- Members: `heritage_timeline_about`.
- Variants: `heritage-timeline-about`.
- Design intents: Orders only verified history dates along a restrained chronological line.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `timeline`.
- Poor transitions: repeat `timeline` with the same `contained` edge and media intensity 2.
- Mobile behavior: `timeline_stack`.

## `about.identity`

- Purpose: about composition using `business_identity`.
- Visual grammar: `split`; `contained` edge; media intensity 2; `large` type role.
- Members: `simple_business_identity`, `residential_approach_about`, `studio_statement_about`.
- Variants: `simple-business-identity`, `residential-approach-about`, `studio-statement-about`.
- Design intents: Explains identity and approach in one direct narrative flow.; Balances a calm residential approach with optional contextual media.; Uses a concise studio statement and measured whitespace as the primary identity.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2843.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 2.
- Mobile behavior: `linear_stack`.

## `about.local`

- Purpose: about composition using `local_commitment`.
- Visual grammar: `rows`; `contained` edge; media intensity 2; `large` type role.
- Members: `local_commitment_about`, `service_area_story`.
- Variants: `local-commitment-about`, `service-area-story`.
- Design intents: Connects business identity to verified locality in a direct narrative row.; Explains verified service geography as a story rather than an invented coverage claim.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3460.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 2.
- Mobile behavior: `linear_stack`.

## `about.material`

- Purpose: about composition using `material_philosophy`.
- Visual grammar: `split`; `contained` edge; media intensity 2; `large` type role.
- Members: `material_philosophy`, `craft_values_index`.
- Variants: `material-philosophy`, `craft-values-index`.
- Design intents: Pairs a material principle with contextual texture rather than unsupported claims.; Turns stated craft values into a quiet indexed reading sequence.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3460.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 2.
- Mobile behavior: `separate_layers`.

## `about.minimal`

- Purpose: about composition using `quiet_statement`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `large` type role.
- Members: `quiet_editorial_about`, `brutalist_factless_about`, `mobile_compact_about`.
- Variants: `quiet-editorial-about`, `brutalist-factless-about`, `mobile-compact-about`.
- Design intents: Lets one factual narrative occupy a narrow editorial measure with ample whitespace.; Uses rigid typography and geometry without adding unsupported business facts.; Compresses the honest identity narrative into a touch-friendly single-column order.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2301.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `centered_stack`.

## `about.project`

- Purpose: about composition using `project_context`.
- Visual grammar: `split`; `contained` edge; media intensity 2; `large` type role.
- Members: `project_context_about`.
- Variants: `project-context-about`.
- Design intents: Uses verified project media to explain working method and context.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 2.
- Mobile behavior: `media_then_content`.

## `about.team`

- Purpose: about composition using `team_portrait`.
- Visual grammar: `grid`; `contained` edge; media intensity 2; `large` type role.
- Members: `team_portrait_about`.
- Variants: `team-portrait-about`.
- Design intents: Uses verified team imagery and roles in an even people grid.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 2.
- Mobile behavior: `priority_matrix`.

## `about.technical`

- Purpose: about composition using `technical_expertise`.
- Visual grammar: `matrix`; `contained` edge; media intensity 2; `large` type role.
- Members: `technical_expertise_about`.
- Variants: `technical-expertise-about`.
- Design intents: Aligns method and verified qualifications in a precise capability matrix.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `contained` edge and media intensity 2.
- Mobile behavior: `priority_matrix`.

## `contact.channels`

- Purpose: contact composition using `multi_channel`.
- Visual grammar: `grid`; `contained` edge; media intensity 1; `large` type role.
- Members: `multi_channel_contact`.
- Variants: `multi-channel-contact`.
- Design intents: Ranks verified contact channels in a clear information matrix.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 1.
- Mobile behavior: `priority_matrix`.

## `contact.editorial`

- Purpose: contact composition using `editorial_statement`.
- Visual grammar: `typographic`; `contained` edge; media intensity 1; `large` type role.
- Members: `editorial_contact_statement`.
- Variants: `editorial-contact-statement`.
- Design intents: Uses a quiet statement to lead into one verified contact channel.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 1.
- Mobile behavior: `centered_stack`.

## `contact.emergency`

- Purpose: contact composition using `emergency_contact`.
- Visual grammar: `full_bleed`; `contained` edge; media intensity 1; `large` type role.
- Members: `emergency_contact`.
- Variants: `emergency-contact`.
- Design intents: Surfaces a verified emergency phone route with minimal competing input.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `full_bleed`.
- Poor transitions: repeat `full_bleed` with the same `contained` edge and media intensity 1.
- Mobile behavior: `bottom_action_dock`.

## `contact.local`

- Purpose: contact composition using `local_context`.
- Visual grammar: `split`; `contained` edge; media intensity 1; `large` type role.
- Members: `local_map_contact`, `service_area_contact`, `workshop_visit_contact`.
- Variants: `local-map-contact`, `service-area-contact`, `workshop-visit-contact`.
- Design intents: Balances verified geography with direct contact details.; Lists verified service areas before the relevant contact route.; Frames verified visit information and enquiry action without implying availability.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2897.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 1.
- Mobile behavior: `map_then_contact`.

## `contact.minimal`

- Purpose: contact composition using `minimal_details`.
- Visual grammar: `stack`; `contained` edge; media intensity 1; `large` type role.
- Members: `minimal_contact`, `side_information_contact`.
- Variants: `minimal-contact`, `side-information-contact`.
- Design intents: Shows only the verified contact details required to make contact.; Places useful verified information beside a narrow contact column.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2897.
- Ideal transitions: change pattern, edge or media intensity after `stack`.
- Poor transitions: repeat `stack` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `contact.panel`

- Purpose: contact composition using `persistent_panel`.
- Visual grammar: `floating`; `contained` edge; media intensity 1; `large` type role.
- Members: `sticky_contact_panel`, `dark_overlay_contact`.
- Variants: `sticky-contact-panel`, `dark-overlay-contact`.
- Design intents: Keeps the contact action visible while detailed context scrolls beside it.; Uses a contrast-safe overlay plane to hold contact details over ambient media.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2317.
- Ideal transitions: change pattern, edge or media intensity after `floating`.
- Poor transitions: repeat `floating` with the same `contained` edge and media intensity 1.
- Mobile behavior: `panel_then_context`.

## `contact.phone`

- Purpose: contact composition using `phone_first`.
- Visual grammar: `floating`; `contained` edge; media intensity 1; `large` type role.
- Members: `phone_first_contact`, `floating_contact_action`, `mobile_action_contact`.
- Variants: `phone-first-contact`, `floating-contact-action`, `mobile-action-contact`.
- Design intents: Makes the verified phone channel primary before supporting details.; Keeps one contact action in a floating plane beside stable details.; Recomposes verified contact into a touch-safe mobile action dock.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2317.
- Ideal transitions: change pattern, edge or media intensity after `floating`.
- Poor transitions: repeat `floating` with the same `contained` edge and media intensity 1.
- Mobile behavior: `action_stack`.

## `contact.project`

- Purpose: contact composition using `project_brief`.
- Visual grammar: `split`; `contained` edge; media intensity 1; `large` type role.
- Members: `project_brief_contact`.
- Variants: `project-brief-contact`.
- Design intents: Orders project scope fields before direct contact channels.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 1.
- Mobile behavior: `brief_then_contact`.

## `contact.quote`

- Purpose: contact composition using `quote_first`.
- Visual grammar: `split`; `contained` edge; media intensity 1; `large` type role.
- Members: `quote_first_contact`, `compact_request_contact`, `footer_contact_conversion`.
- Variants: `quote-first-contact`, `compact-request-contact`, `footer-contact-conversion`.
- Design intents: Gives the enquiry form priority and keeps direct channels secondary.; Contains essential request fields and contact details in a compact stack.; Integrates a final enquiry action at the footer boundary without merging legal content.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2897.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 1.
- Mobile behavior: `form_then_channels`.

## `contact.split`

- Purpose: contact composition using `split_details_form`.
- Visual grammar: `split`; `contained` edge; media intensity 1; `large` type role.
- Members: `split_form_contact`, `residential_project_contact`.
- Variants: `split-form-contact`, `residential-project-contact`.
- Design intents: Balances verified contact details and a working form on a clear split grid.; Pairs calm project context with a residential enquiry form.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3513.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 1.
- Mobile behavior: `details_then_form`.

## `contact.technical`

- Purpose: contact composition using `technical_diagnostic`.
- Visual grammar: `matrix`; `contained` edge; media intensity 1; `large` type role.
- Members: `technical_diagnostic_contact`.
- Variants: `technical-diagnostic-contact`.
- Design intents: Groups technical scope fields and contact details on a specification grid.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `contained` edge and media intensity 1.
- Mobile behavior: `priority_matrix`.

## `cta.availability`

- Purpose: cta composition using `availability_checked`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `large` type role.
- Members: `availability_checked_cta`, `location_aware_cta`.
- Variants: `availability-checked-cta`, `location-aware-cta`.
- Design intents: Places verified availability context before a general contact action.; Uses verified service geography to contextualize one contact action.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2843.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.contact`

- Purpose: cta composition using `contact_prompt`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `large` type role.
- Members: `minimal_contact_link`, `side_information_cta`, `quiet_editorial_cta`.
- Variants: `minimal-contact-link`, `side-information-cta`, `quiet-editorial-cta`.
- Design intents: Reduces conversion to one quiet, clearly labelled contact link.; Places useful verified context beside one restrained contact action.; Uses an editorial sentence and low-pressure action with generous whitespace.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2898.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.email`

- Purpose: cta composition using `email_link`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `large` type role.
- Members: `minimal_email_cta`.
- Variants: `minimal-email-cta`.
- Design intents: Presents one verified email route as a restrained typographic action.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.emergency`

- Purpose: cta composition using `emergency_phone`.
- Visual grammar: `full_bleed`; `contained` edge; media intensity 0; `large` type role.
- Members: `emergency_phone_cta`.
- Variants: `emergency-phone-cta`.
- Design intents: Makes a verified emergency phone route dominant and immediately reachable.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `full_bleed`.
- Poor transitions: repeat `full_bleed` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.material`

- Purpose: cta composition using `material_consultation`.
- Visual grammar: `split`; `contained` edge; media intensity 0; `large` type role.
- Members: `service_specific_cta`, `material_sample_cta`, `technical_diagnostic_cta`.
- Variants: `service-specific-cta`, `material-sample-cta`, `technical-diagnostic-cta`.
- Design intents: Links one selected service context to a relevant enquiry action.; Pairs a material consultation prompt with a restrained contextual sample.; Frames diagnostic scope and contact action on a strict technical grid.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2843.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.phone`

- Purpose: cta composition using `phone_action`.
- Visual grammar: `floating`; `contained` edge; media intensity 0; `large` type role.
- Members: `phone_first_cta`, `floating_phone_action`, `callback_request_cta`, `mobile_action_dock_cta`.
- Variants: `phone-first-cta`, `floating-phone-action`, `callback-request-cta`, `mobile-action-dock-cta`.
- Design intents: Places the verified phone action before any secondary contact route.; Keeps a compact verified phone action visually available beside the prompt.; Pairs a callback prompt with one concise request action.; Recomposes into a touch-safe bottom phone action on narrow screens.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2282.
- Ideal transitions: change pattern, edge or media intensity after `floating`.
- Poor transitions: repeat `floating` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.project`

- Purpose: cta composition using `project_enquiry`.
- Visual grammar: `split`; `contained` edge; media intensity 0; `large` type role.
- Members: `split_project_cta`, `project_brief_cta`, `residential_consultation_cta`, `site_visit_cta`, `project_gallery_cta`.
- Variants: `split-project-cta`, `project-brief-cta`, `residential-consultation-cta`, `site-visit-cta`, `project-gallery-cta`.
- Design intents: Splits project prompt and contact action into balanced fields.; Invites a short project brief before exposing secondary contact channels.; Frames a calm residential consultation prompt with one clear next step.; Connects a site-visit request to the minimum verified contact route.; Bridges verified project viewing and project enquiry without merging the actions.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2227.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.quote`

- Purpose: cta composition using `quote_action`.
- Visual grammar: `centered`; `contained` edge; media intensity 0; `large` type role.
- Members: `quote_first_cta`, `sticky_quote_cta`, `footer_conversion_cta`, `compact_request_cta`, `dual_action_contact_cta`.
- Variants: `quote-first-cta`, `sticky-quote-cta`, `footer-conversion-cta`, `compact-request-cta`, `dual-action-contact-cta`.
- Design intents: Makes the quote request the primary decision after a concise project prompt.; Keeps one quote action attached to the reading edge without obscuring content.; Closes the page with a wide quote prompt immediately before the footer.; Contains a short request prompt and one action in a compact strip.; Ranks quote and verified contact actions on one shared baseline.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1666.
- Ideal transitions: change pattern, edge or media intensity after `centered`.
- Poor transitions: repeat `centered` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `cta.statement`

- Purpose: cta composition using `monumental_action`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `monumental` type role.
- Members: `monumental_statement_cta`.
- Variants: `monumental-statement-cta`.
- Design intents: Uses one large decision statement and a deliberately secondary action.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `stack_message_then_actions`.

## `footer.area`

- Purpose: footer composition using `service_area`.
- Visual grammar: `split`; `contained` edge; media intensity 0; `normal` type role.
- Members: `service_area_footer`.
- Variants: `service-area-footer`.
- Design intents: Places verified service geography in a dedicated closing column.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.business`

- Purpose: footer composition using `business_information`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `business_information_footer`, `local_business_footer`.
- Variants: `business-information-footer`, `local-business-footer`.
- Design intents: Organizes verified business details and navigation into stable columns.; Gives verified locality and contact information priority in the closing hierarchy.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3376.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.contact`

- Purpose: footer composition using `contact_first`.
- Visual grammar: `split`; `contained` edge; media intensity 0; `normal` type role.
- Members: `contact_first_footer`, `cta_footer_hybrid`, `split_contact_footer`, `mobile_action_footer`.
- Variants: `contact-first-footer`, `cta-footer-hybrid`, `split-contact-footer`, `mobile-action-footer`.
- Design intents: Makes verified contact the dominant first column before navigation and legal.; Separates a final action plane from the footer's information architecture.; Balances contact and navigation in two broad closing fields.; Recomposes the primary contact route into a touch-safe mobile close.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1684.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.minimal`

- Purpose: footer composition using `minimal`.
- Visual grammar: `stack`; `contained` edge; media intensity 0; `normal` type role.
- Members: `ultra_minimal_footer`, `legal_compact_footer`, `centered_mark_footer`.
- Variants: `ultra-minimal-footer`, `legal-compact-footer`, `centered-mark-footer`.
- Design intents: Closes with the smallest viable brand, contact and legal sequence.; Compresses required legal and contact information into a disciplined final row.; Centers the brand mark above a quiet legal close.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2760.
- Ideal transitions: change pattern, edge or media intensity after `stack`.
- Poor transitions: repeat `stack` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.navigation`

- Purpose: footer composition using `navigation_columns`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `navigation_columns_footer`, `editorial_directory_footer`.
- Variants: `navigation-columns-footer`, `editorial-directory-footer`.
- Design intents: Groups page navigation into clear directories before the legal row.; Treats navigation as an editorial index with a paced closing sequence.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2760.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.project`

- Purpose: footer composition using `project_index`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `project_index_footer`.
- Variants: `project-index-footer`.
- Design intents: Closes a project-led page with a verified project index and enquiry route.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.services`

- Purpose: footer composition using `service_directory`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `service_links_footer`.
- Variants: `service-links-footer`.
- Design intents: Keeps real service links grouped and secondary to verified contact details.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.statement`

- Purpose: footer composition using `brand_statement`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `oversized` type role.
- Members: `large_brand_statement_footer`, `oversized_wordmark_footer`, `workshop_signature_footer`.
- Variants: `large-brand-statement-footer`, `oversized-wordmark-footer`, `workshop-signature-footer`.
- Design intents: Uses a large brand statement to open the closing section before utility information.; Lets an oversized wordmark span the footer boundary while details remain restrained.; Pairs a workshop signature mark with practical contact and legal details.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2226.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.technical`

- Purpose: footer composition using `technical_spec`.
- Visual grammar: `matrix`; `contained` edge; media intensity 0; `normal` type role.
- Members: `technical_spec_footer`.
- Variants: `technical-spec-footer`.
- Design intents: Aligns dense utility information to a technical specification grid.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column_priority`.

## `footer.visual`

- Purpose: footer composition using `visual_close`.
- Visual grammar: `overlay`; `contained` edge; media intensity 1; `normal` type role.
- Members: `visual_image_footer`, `dark_overlay_footer`.
- Variants: `visual-image-footer`, `dark-overlay-footer`.
- Design intents: Uses one contextual image as a visual close while contact remains legible outside it.; Places restrained closing information on a contrast-safe dark media plane.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3376.
- Ideal transitions: change pattern, edge or media intensity after `overlay`.
- Poor transitions: repeat `overlay` with the same `contained` edge and media intensity 1.
- Mobile behavior: `single_column_priority`.

## `form.accessible`

- Purpose: form composition using `accessible_minimal`.
- Visual grammar: `stack`; `contained` edge; media intensity 0; `normal` type role.
- Members: `accessible_minimal_form`.
- Variants: `accessible-minimal-form`.
- Design intents: Uses a strict single-column label, error and focus order with no decorative interruption.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `stack`.
- Poor transitions: repeat `stack` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column`.

## `form.compact`

- Purpose: form composition using `compact_callback`.
- Visual grammar: `stack`; `contained` edge; media intensity 0; `normal` type role.
- Members: `compact_callback_form`, `emergency_minimal_form`, `accordion_mobile_form`.
- Variants: `compact-callback-form`, `emergency-minimal-form`, `accordion-mobile-form`.
- Design intents: Limits callback request to the minimum usable fields and one action.; Keeps emergency contact input minimal and secondary to the verified phone route.; Groups optional fields behind touch-friendly disclosure sections.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2280.
- Ideal transitions: change pattern, edge or media intensity after `stack`.
- Poor transitions: repeat `stack` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column`.

## `form.multi_step`

- Purpose: form composition using `multi_step`.
- Visual grammar: `timeline`; `contained` edge; media intensity 0; `normal` type role.
- Members: `multi_step_project_brief`, `service_selector_form`.
- Variants: `multi-step-project-brief`, `service-selector-form`.
- Design intents: Advances project context one topic at a time with visible progress.; Starts with service selection and reveals only relevant follow-up fields.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3430.
- Ideal transitions: change pattern, edge or media intensity after `timeline`.
- Poor transitions: repeat `timeline` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column`.

## `form.single`

- Purpose: form composition using `single_column`.
- Visual grammar: `stack`; `contained` edge; media intensity 0; `normal` type role.
- Members: `single_column_quote_form`, `contact_details_form`, `site_visit_request_form`, `material_consultation_form`, `inline_footer_form`, `full_page_enquiry_form`.
- Variants: `single-column-quote-form`, `contact-details-form`, `site-visit-request-form`, `material-consultation-form`, `inline-footer-form`, `full-page-enquiry-form`.
- Design intents: Orders essential quote fields in one clear top-to-bottom path.; Groups verified contact inputs before the enquiry message.; Collects the minimum visit context before contact details and submit.; Separates material interest from contact details in a concise form sequence.; Fits minimal contact fields on one footer-aligned row before stacking on mobile.; Uses a generous page canvas for a longer but clearly grouped enquiry.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1701.
- Ideal transitions: change pattern, edge or media intensity after `stack`.
- Poor transitions: repeat `stack` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column`.

## `form.split`

- Purpose: form composition using `split_fields`.
- Visual grammar: `split`; `contained` edge; media intensity 0; `normal` type role.
- Members: `split_project_form`, `residential_scope_form`.
- Variants: `split-project-form`, `residential-scope-form`.
- Design intents: Balances project scope and contact fields in two aligned groups.; Separates residential scope choices from personal contact details.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1738.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column`.

## `form.technical`

- Purpose: form composition using `technical_scope`.
- Visual grammar: `matrix`; `contained` edge; media intensity 0; `normal` type role.
- Members: `technical_diagnostic_form`.
- Variants: `technical-diagnostic-form`.
- Design intents: Groups diagnostic scope fields on a precise technical grid before contact.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `contained` edge and media intensity 0.
- Mobile behavior: `single_column`.

## `gallery.ambient`

- Purpose: gallery composition using `ambient_mosaic`.
- Visual grammar: `asymmetric`; `contained` edge; media intensity 4; `normal` type role.
- Members: `inspiration_gallery_mosaic`, `visual_atmosphere_sequence`, `lighting_atmosphere_gallery`, `stock_ambient_collage`, `portrait_landscape_dialogue`.
- Variants: `inspiration-gallery-mosaic`, `visual-atmosphere-sequence`, `lighting-atmosphere-gallery`, `stock-ambient-collage`, `portrait-landscape-dialogue`.
- Design intents: Builds an asymmetric ambient mosaic without presenting stock imagery as completed work.; Sequences ambient images at a measured pace from wide context to detail.; Uses alternating dark and light frames to study atmosphere rather than claim projects.; Keeps licensed ambient images in a clearly non-project editorial collage.; Alternates portrait and landscape ratios as paired visual sentences.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2227.
- Ideal transitions: change pattern, edge or media intensity after `asymmetric`.
- Poor transitions: repeat `asymmetric` with the same `contained` edge and media intensity 4.
- Mobile behavior: `two_column_or_stack`.

## `gallery.before_after`

- Purpose: gallery composition using `before_after_pairs`.
- Visual grammar: `split`; `contained` edge; media intensity 3; `normal` type role.
- Members: `before_after_transformation_pairs`.
- Variants: `before-after-transformation-pairs`.
- Design intents: Keeps every verified before and after image locked in a matched pair.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 3.
- Mobile behavior: `paired_stack`.

## `gallery.documentary`

- Purpose: gallery composition using `documentary_work_log`.
- Visual grammar: `timeline`; `viewport_edge` edge; media intensity 4; `normal` type role.
- Members: `documentary_work_log`, `workshop_documentary_gallery`, `construction_progress_ledger`, `full_bleed_image_sequence`.
- Variants: `documentary-work-log`, `workshop-documentary-gallery`, `construction-progress-ledger`, `full-bleed-image-sequence`.
- Design intents: Presents verified work images as a chronological field log.; Observes documented workshop gestures in a quiet narrative sequence.; Aligns verified progress images and dates in a construction ledger.; Alternates full-width verified images as immersive but distinct chapters.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2282.
- Ideal transitions: change pattern, edge or media intensity after `timeline`.
- Poor transitions: repeat `timeline` with the same `viewport_edge` edge and media intensity 4.
- Mobile behavior: `chronological_stack`.

## `gallery.editorial_project`

- Purpose: gallery composition using `editorial_casebook`.
- Visual grammar: `rows`; `contained` edge; media intensity 3; `normal` type role.
- Members: `editorial_project_folio`, `alternating_project_stories`, `quiet_captioned_gallery`, `cinematic_chapter_gallery`, `artisan_casebook_rail`.
- Variants: `editorial-project-folio`, `alternating-project-stories`, `quiet-captioned-gallery`, `cinematic-chapter-gallery`, `artisan-casebook-rail`.
- Design intents: Pairs verified project images and folio captions in an editorial index.; Alternates project media and verified context across successive chapters.; Uses small attached captions and generous whitespace around verified images.; Lets wide project scenes open distinct visual chapters.; Combines a casebook index with a horizontal rail of verified work.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2843.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 3.
- Mobile behavior: `chapter_stack`.

## `gallery.masonry`

- Purpose: gallery composition using `masonry_archive`.
- Visual grammar: `masonry`; `contained` edge; media intensity 4; `normal` type role.
- Members: `asymmetric_gallery_mosaic`, `masonry_image_archive`, `framed_canvas_gallery`.
- Variants: `asymmetric-gallery-mosaic`, `masonry-image-archive`, `framed-canvas-gallery`.
- Design intents: Creates a deliberate hierarchy of unequal image spans around shared alignment lines.; Preserves source ratios in a column-led masonry archive.; Places varied imagery inside a single precise gallery canvas.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2843.
- Ideal transitions: change pattern, edge or media intensity after `masonry`.
- Poor transitions: repeat `masonry` with the same `contained` edge and media intensity 4.
- Mobile behavior: `two_column_masonry`.

## `gallery.material`

- Purpose: gallery composition using `material_study`.
- Visual grammar: `grid`; `contained` edge; media intensity 3; `normal` type role.
- Members: `material_gallery_macro`, `image_diptych`, `image_triptych`, `gallery_with_material_index`.
- Variants: `material-gallery-macro`, `image-diptych`, `image-triptych`, `gallery-with-material-index`.
- Design intents: Moves from material macro views to wider contextual images.; Holds two related images in a balanced shared frame.; Uses a three-part image rhythm with one deliberate lead panel.; Links a material index to corresponding ambient image groups.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2843.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 3.
- Mobile behavior: `material_swipe`.

## `gallery.mobile`

- Purpose: gallery composition using `mobile_swipe`.
- Visual grammar: `rail`; `contained` edge; media intensity 3; `normal` type role.
- Members: `mobile_swipe_gallery`.
- Variants: `mobile-swipe-gallery`.
- Design intents: Prioritizes one touch-safe image at a time with visible snap progression.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rail`.
- Poor transitions: repeat `rail` with the same `contained` edge and media intensity 3.
- Mobile behavior: `single_card_snap`.

## `gallery.project`

- Purpose: gallery composition using `project_grid`.
- Visual grammar: `grid`; `contained` edge; media intensity 3; `normal` type role.
- Members: `artisan_project_grid`, `artisan_project_cards`, `project_contact_sheet`, `featured_project_monument`, `residential_room_sequence`, `technical_detail_archive`.
- Variants: `artisan-project-grid`, `artisan-project-cards`, `project-contact-sheet`, `featured-project-monument`, `residential-room-sequence`, `technical-detail-archive`.
- Design intents: Displays verified artisan projects in an even comparison grid.; Attaches verified context directly below each project image in discrete modules.; Uses a dense contact sheet to show breadth while preserving project provenance.; Gives one verified project a dominant full-width frame before supporting work.; Moves through verified room images as a calm spatial sequence.; Catalogues verified construction details against a precise archive index.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1644.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 3.
- Mobile behavior: `project_cards`.

## `gallery.rail`

- Purpose: gallery composition using `horizontal_rail`.
- Visual grammar: `rail`; `viewport_edge` edge; media intensity 3; `normal` type role.
- Members: `horizontal_gallery_scroll`.
- Variants: `horizontal-gallery-scroll`.
- Design intents: Extends imagery beyond the viewport in an explicit horizontal browsing rail.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rail`.
- Poor transitions: repeat `rail` with the same `viewport_edge` edge and media intensity 3.
- Mobile behavior: `snap_rail`.

## `header.centered`

- Purpose: header composition using `centered_brand`.
- Visual grammar: `centered`; `contained` edge; media intensity 0; `normal` type role.
- Members: `centered_brand_quiet`, `minimal_logo_only`.
- Variants: `centered-brand-quiet`, `minimal-logo-only`.
- Design intents: Uses symmetry and surrounding whitespace to make a restrained brand the visual anchor.; Reduces the header to one quiet identity mark and an unobtrusive menu affordance.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2692.
- Ideal transitions: change pattern, edge or media intensity after `centered`.
- Poor transitions: repeat `centered` with the same `contained` edge and media intensity 0.
- Mobile behavior: `centered_stack`.

## `header.classic`

- Purpose: header composition using `classic_horizontal`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `classic_brand_left`, `split_navigation`, `compact_sticky_nav`, `framed_canvas_header`.
- Variants: `classic-brand-left`, `split-navigation`, `compact-sticky-nav`, `framed-canvas-header`.
- Design intents: Keeps the brand on the opening edge and lets navigation resolve toward the primary action.; Balances two navigation groups around a stable central brand axis.; Compresses navigation into a persistent utility line without changing page width.; Treats the header as the top edge of a deliberately framed page canvas.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2692.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `linear_stack`.

## `header.contact`

- Purpose: header composition using `contact_utility`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `utility_contact_bar`, `phone_first_compact`, `mega_contact_header`, `conversion_action_dock_header`.
- Variants: `utility-contact-bar`, `phone-first-compact`, `mega-contact-header`, `conversion-action-dock`.
- Design intents: Separates verified contact utility from the main navigation row.; Makes the verified phone action immediate while keeping navigation secondary and compact.; Organizes several verified contact channels as a deliberate information matrix.; Docks one conversion action to the edge while identity and navigation remain readable.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2145.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `utility_then_nav`.

## `header.editorial`

- Purpose: header composition using `editorial_index`.
- Visual grammar: `asymmetric`; `contained` edge; media intensity 0; `normal` type role.
- Members: `editorial_index_nav`, `oversized_menu_trigger`.
- Variants: `editorial-index-nav`, `oversized-menu-trigger`.
- Design intents: Treats navigation as a magazine index with a strong reading sequence.; Opposes a large menu trigger to a sparse wordmark for editorial tension.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3237.
- Ideal transitions: change pattern, edge or media intensity after `asymmetric`.
- Poor transitions: repeat `asymmetric` with the same `contained` edge and media intensity 0.
- Mobile behavior: `index_drawer`.

## `header.gallery`

- Purpose: header composition using `gallery_navigation`.
- Visual grammar: `rail`; `contained` edge; media intensity 0; `normal` type role.
- Members: `gallery_bottom_nav`.
- Variants: `gallery-bottom-nav`.
- Design intents: Places project navigation on the lower image boundary like a gallery caption rail.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rail`.
- Poor transitions: repeat `rail` with the same `contained` edge and media intensity 0.
- Mobile behavior: `bottom_to_topbar`.

## `header.local`

- Purpose: header composition using `local_information`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `two_row_local`, `local_info_strip`, `residential_project_header`.
- Variants: `two-row-local`, `local-info-strip`, `residential-project-header`.
- Design intents: Gives verified local context its own row above a conventional navigation line.; Runs concise verified locality and contact facts as a thin scanning strip.; Pairs a calm residential identity with direct access to project navigation.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2692.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `local_then_nav`.

## `header.overlay`

- Purpose: header composition using `transparent_overlay`.
- Visual grammar: `overlay`; `viewport_edge` edge; media intensity 0; `normal` type role.
- Members: `transparent_overlay_nav`, `dark_overlay_nav`.
- Variants: `transparent-overlay-nav`, `dark-overlay-nav`.
- Design intents: Floats a light navigation layer over media while preserving the opening scene.; Uses a dark contrast plane over media to hold navigation and action together.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2145.
- Ideal transitions: change pattern, edge or media intensity after `overlay`.
- Poor transitions: repeat `overlay` with the same `viewport_edge` edge and media intensity 0.
- Mobile behavior: `contrast_topbar`.

## `header.rail`

- Purpose: header composition using `architectural_rail`.
- Visual grammar: `rail`; `contained` edge; media intensity 0; `normal` type role.
- Members: `architectural_side_rail`, `side_rail_projects`.
- Variants: `architectural-side-rail`, `side-rail-projects`.
- Design intents: Uses a full-height side rail as the page's permanent architectural datum.; Turns the rail into a project index that advances beside the page content.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3237.
- Ideal transitions: change pattern, edge or media intensity after `rail`.
- Poor transitions: repeat `rail` with the same `contained` edge and media intensity 0.
- Mobile behavior: `rail_to_topbar`.

## `header.statement`

- Purpose: header composition using `statement_brand`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `normal` type role.
- Members: `floating_capsule_nav`, `workshop_mark_header`, `statement_wordmark_header`.
- Variants: `floating-capsule-nav`, `workshop-mark-header`, `statement-wordmark-header`.
- Design intents: Contains sparse navigation inside a floating control plane distinct from the canvas.; Anchors a workshop mark to an offset grid line with a practical menu counterweight.; Lets an oversized wordmark establish identity before a minimal navigation trigger.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2692.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_drawer`.

## `header.technical`

- Purpose: header composition using `technical_utility`.
- Visual grammar: `matrix`; `contained` edge; media intensity 0; `normal` type role.
- Members: `blueprint_utility_header`, `service_category_header`.
- Variants: `blueprint-utility-header`, `service-category-header`.
- Design intents: Aligns identity, system index and utility actions to a technical module grid.; Exposes service categories as the primary navigation hierarchy.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3237.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `contained` edge and media intensity 0.
- Mobile behavior: `priority_matrix`.

## `hero.cinematic`

- Purpose: hero composition using `cinematic_scene`.
- Visual grammar: `overlay`; `viewport_edge` edge; media intensity 4; `oversized` type role.
- Members: `cinematic_overlay_story`, `framed_luxury_scene`, `quiet_luxury_window`.
- Variants: `cinematic-overlay-story`, `framed-luxury-scene`, `quiet-luxury-window`.
- Design intents: Stages copy as timed story beats over a wide cinematic scene.; Contains a premium scene inside a precise frame with copy held outside the image plane.; Uses a smaller image window and expansive negative space for restrained residential luxury.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2655.
- Ideal transitions: change pattern, edge or media intensity after `overlay`.
- Poor transitions: repeat `overlay` with the same `viewport_edge` edge and media intensity 4.
- Mobile behavior: `poster_then_chapters`.

## `hero.collage`

- Purpose: hero composition using `asymmetric_editorial_collage`.
- Visual grammar: `asymmetric`; `offset` edge; media intensity 4; `oversized` type role.
- Members: `editorial_photo_collage`, `floating_image_statement`, `stacked_photos_narrative`, `diptych_transformation_intro`, `triptych_material_intro`.
- Variants: `editorial-photo-collage`, `floating-image-statement`, `stacked-photos-narrative`, `diptych-transformation-intro`, `triptych-material-intro`.
- Design intents: Builds a magazine-like hierarchy from one lead image and offset supporting crops.; Floats one image against an oversized statement without enclosing either in a card.; Sequences stacked images as chapters around a continuous narrative column.; Pairs two verified transformation views with a shared explanatory axis.; Uses three material views at unequal scale to move from context to detail.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3200.
- Ideal transitions: change pattern, edge or media intensity after `asymmetric`.
- Poor transitions: repeat `asymmetric` with the same `offset` edge and media intensity 4.
- Mobile behavior: `alternating_stack`.

## `hero.conversion`

- Purpose: hero composition using `conversion_problem_solution`.
- Visual grammar: `split`; `contained` edge; media intensity 1; `large` type role.
- Members: `edge_crop_conversion`, `compact_conversion_panel`, `service_led_selector`, `phone_first_problem_solution`, `quote_first_project_brief`.
- Variants: `edge-crop-conversion`, `compact-conversion-panel`, `service-led-selector`, `phone-first-problem-solution`, `quote-first-project-brief`.
- Design intents: Uses a supporting crop at the edge while problem, solution and action remain primary.; Contains the proposition and one action in a compact high-clarity panel.; Begins with a service choice and progressively reveals the relevant contact action.; Moves from customer problem to verified phone action before secondary context.; Treats a short project brief as the first conversion step before supporting media.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2113.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 1.
- Mobile behavior: `content_then_media`.

## `hero.material`

- Purpose: hero composition using `material_study`.
- Visual grammar: `split`; `offset` edge; media intensity 3; `oversized` type role.
- Members: `material_macro_title`, `layered_material_scene`, `parallax_layered_material`, `workshop_gesture_cover`.
- Variants: `material-macro-title`, `layered-material-scene`, `parallax-layered-material`, `workshop-gesture-cover`.
- Design intents: Places an oversized material crop beside a title calibrated to its texture and scale.; Overlaps macro and contextual material views to create depth without invented claims.; Separates material planes into a measured depth progression with a static mobile recomposition.; Centers a documented hand or tool gesture as the emotional entry to craft.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2110.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `offset` edge and media intensity 3.
- Mobile behavior: `media_then_content`.

## `hero.photo_cover`

- Purpose: hero composition using `full_bleed_cover`.
- Visual grammar: `full_bleed`; `viewport_edge` edge; media intensity 4; `oversized` type role.
- Members: `full_bleed_photo_cover`, `centered_image_frame`, `panorama_architectural`, `lighting_atmosphere_cover`.
- Variants: `full-bleed-photo-cover`, `centered-image-frame`, `panorama-architectural`, `lighting-atmosphere-cover`.
- Design intents: Lets one environmental image occupy the viewport while edge-anchored copy remains subordinate to place.; Gives one contained architectural image the status of an artwork on a generous centered canvas.; Uses a low panoramic horizon band to prioritize architectural context over cinematic height.; Builds a dark image-dominant atmosphere with restrained copy and a measured light-preserving overlay.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3032.
- Ideal transitions: change pattern, edge or media intensity after `full_bleed`.
- Poor transitions: repeat `full_bleed` with the same `viewport_edge` edge and media intensity 4.
- Mobile behavior: `crop_then_stack`.

## `hero.project`

- Purpose: hero composition using `project_evidence_intro`.
- Visual grammar: `grid`; `contained` edge; media intensity 3; `large` type role.
- Members: `project_contact_sheet_hero`, `asymmetric_project_intro`, `project_canvas_feature`, `gallery_led_sequence`, `documentary_work_log_hero`.
- Variants: `project-contact-sheet-hero`, `asymmetric-project-intro`, `project-canvas-feature`, `gallery-led-sequence`, `documentary-work-log-hero`.
- Design intents: Opens with a dense contact sheet of real project evidence and concise context.; Offsets one lead project view against a narrow verified project summary.; Presents one project image on a contained gallery canvas with factual context below.; Lets a short project sequence establish evidence before title and action.; Introduces the site through a chronological set of documented work moments.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2655.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 3.
- Mobile behavior: `priority_matrix`.

## `hero.rail`

- Purpose: hero composition using `horizontal_preview_rail`.
- Visual grammar: `rail`; `viewport_edge` edge; media intensity 4; `large` type role.
- Members: `horizontal_rail_preview`, `vertical_portrait_manifesto`.
- Variants: `horizontal-rail-preview`, `vertical-portrait-manifesto`.
- Design intents: Previews several visual directions as a horizontal edge-to-edge rail.; Pairs a tall portrait rhythm with a vertically paced manifesto and restrained action.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3200.
- Ideal transitions: change pattern, edge or media intensity after `rail`.
- Poor transitions: repeat `rail` with the same `viewport_edge` edge and media intensity 4.
- Mobile behavior: `snap_rail`.

## `hero.spatial`

- Purpose: hero composition using `spatial_explainer`.
- Visual grammar: `overlay`; `framed` edge; media intensity 1; `oversized` type role.
- Members: `blueprint_spatial_scene`, `isometric_system_explainer`.
- Variants: `blueprint-spatial-scene`, `isometric-system-explainer`.
- Design intents: Layers a spatial explanation over a restrained blueprint-like coordinate field.; Uses an isometric module hierarchy to explain a system without decorative 3D excess.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3200.
- Ideal transitions: change pattern, edge or media intensity after `overlay`.
- Poor transitions: repeat `overlay` with the same `framed` edge and media intensity 1.
- Mobile behavior: `separate_layers`.

## `hero.split_photo`

- Purpose: hero composition using `split_editorial`.
- Visual grammar: `split`; `contained` edge; media intensity 3; `oversized` type role.
- Members: `photo_left_service_intro`, `photo_right_residential_intro`, `split_service_photo`, `offset_residential_photo`, `residential_brief_intro`.
- Variants: `photo-left-service-intro`, `photo-right-residential-intro`, `split-service-photo`, `offset-residential-photo`, `residential-brief-intro`.
- Design intents: Places service context in a left media field and lets the offer read on the right.; Keeps calm residential copy on the left and a contextual room image on the right.; Balances a concise service proposition and supporting image as equal split panels.; Offsets the residential image from the text baseline to create a quieter editorial rhythm.; Frames the project brief first, then uses imagery as atmosphere rather than evidence.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2871.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 3.
- Mobile behavior: `media_then_content`.

## `hero.technical`

- Purpose: hero composition using `technical_explainer`.
- Visual grammar: `matrix`; `framed` edge; media intensity 1; `large` type role.
- Members: `mono_technical_diagnostic`, `condensed_industrial_capability`, `diagrammatic_process_map`, `technical_nodes_network`, `framed_blueprint_specification`.
- Variants: `mono-technical-diagnostic`, `condensed-industrial-capability`, `diagrammatic-process-map`, `technical-nodes-network`, `framed-blueprint-specification`.
- Design intents: Presents a diagnostic statement and capability facts on a strict technical baseline.; Condenses capabilities into a narrow industrial ledger beside the title.; Uses a process diagram as the central explanatory route from need to outcome.; Organizes capabilities as connected technical nodes around one primary system.; Frames the proposition like a specification sheet with aligned factual modules.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1610.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `framed` edge and media intensity 1.
- Mobile behavior: `priority_matrix`.

## `hero.transformation`

- Purpose: hero composition using `verified_transformation_pair`.
- Visual grammar: `split`; `contained` edge; media intensity 4; `large` type role.
- Members: `before_after_transformation_pair`.
- Variants: `before-after-transformation-pair`.
- Design intents: Keeps a verified before and after pair in one matched comparison frame.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 4.
- Mobile behavior: `paired_stack`.

## `hero.typographic`

- Purpose: hero composition using `typographic_statement`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `monumental` type role.
- Members: `oversized_type_local`, `editorial_title_index`, `centered_statement_quiet`, `editorial_columns_manifesto`, `no_image_typographic_signal`, `no_image_editorial_manifesto`, `no_image_local_conversion`, `architectural_void_statement`, `brutalist_block_intro`.
- Variants: `oversized-type-local`, `editorial-title-index`, `centered-statement-quiet`, `editorial-columns-manifesto`, `no-image-typographic-signal`, `no-image-editorial-manifesto`, `no-image-local-conversion`, `architectural-void-statement`, `brutalist-block-intro`.
- Design intents: Makes locality a bold typographic statement with contact action anchored to its edge.; Composes title, section index and supporting copy as a magazine opening page.; Uses a centered statement and generous whitespace with no competing media plane.; Breaks a manifesto into asymmetric reading columns under one dominant title.; Uses one sharp typographic signal and minimal support copy as a no-media identity.; Creates editorial depth through text hierarchy, rules and deliberate reading pace only.; Combines a local proposition and immediate verified contact path without decorative imagery.; Uses intentional empty space and one offset title as the primary architectural gesture.; Locks title, copy and action into rigid edge-aligned blocks with visible structural rules.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1610.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `type_then_action`.

## `services.accordion`

- Purpose: services composition using `service_accordion`.
- Visual grammar: `stack`; `contained` edge; media intensity 1; `large` type role.
- Members: `service_accordion`, `compact_mobile_service_actions`.
- Variants: `service-accordion`, `compact-mobile-service-actions`.
- Design intents: Uses disclosure rows so detail appears only for the service the visitor opens.; Prioritizes compact touch actions and short service labels on narrow screens.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3317.
- Ideal transitions: change pattern, edge or media intensity after `stack`.
- Poor transitions: repeat `stack` with the same `contained` edge and media intensity 1.
- Mobile behavior: `accordion`.

## `services.bento`

- Purpose: services composition using `asymmetric_bento`.
- Visual grammar: `asymmetric`; `contained` edge; media intensity 1; `large` type role.
- Members: `brutalist_service_stack`, `cinematic_service_reveal`.
- Variants: `brutalist-service-stack`, `cinematic-service-reveal`.
- Design intents: Stacks rigid edge-aligned service blocks with visible structural rules.; Reveals service chapters in a measured sequence around one visual plane.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.3317.
- Ideal transitions: change pattern, edge or media intensity after `asymmetric`.
- Poor transitions: repeat `asymmetric` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.conversion`

- Purpose: services composition using `conversion_selector`.
- Visual grammar: `rows`; `contained` edge; media intensity 1; `large` type role.
- Members: `problem_solution_services`, `conversion_service_selector`, `service_map_and_list`.
- Variants: `problem-solution-services`, `conversion-service-selector`, `service-map-and-list`.
- Design intents: Pairs each customer problem with one relevant service response.; Turns service selection into the first deliberate step toward contact.; Balances a verified service-area context with a scannable service list.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2772.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.grid`

- Purpose: services composition using `service_grid`.
- Visual grammar: `grid`; `contained` edge; media intensity 1; `large` type role.
- Members: `icon_service_grid`, `stacked_service_panels`, `residential_room_services`, `service_comparison_columns`.
- Variants: `icon-service-grid`, `stacked-service-panels`, `residential-room-services`, `service-comparison-columns`.
- Design intents: Uses equal icon-led modules for a compact set of clearly differentiated services.; Stacks broad service panels to preserve room for useful descriptions.; Groups services by residential room context without implying project evidence.; Aligns comparable service scopes in columns with a shared reading baseline.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2210.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.index`

- Purpose: services composition using `typographic_index`.
- Visual grammar: `rows`; `contained` edge; media intensity 1; `large` type role.
- Members: `large_typographic_service_index`, `local_service_directory`, `scope_of_work_ledger`.
- Variants: `large-typographic-service-index`, `local-service-directory`, `scope-of-work-ledger`.
- Design intents: Makes service names the dominant typographic index and descriptions secondary.; Organizes the verified local offer as a practical directory with short routes to contact.; Presents service scope as a precise ledger of included work.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2755.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.material`

- Purpose: services composition using `material_catalogue`.
- Visual grammar: `grid`; `contained` edge; media intensity 2; `large` type role.
- Members: `material_service_catalogue`, `project_type_services`, `workshop_service_samples`.
- Variants: `material-service-catalogue`, `project-type-services`, `workshop-service-samples`.
- Design intents: Presents services as a tactile catalogue using contextual material imagery only.; Groups services by project type with no invented project claims.; Pairs service descriptions with restrained workshop or material samples.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2772.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 2.
- Mobile behavior: `linear_stack`.

## `services.matrix`

- Purpose: services composition using `capability_matrix`.
- Visual grammar: `matrix`; `contained` edge; media intensity 1; `large` type role.
- Members: `service_matrix`, `service_masonry`, `service_bento`.
- Variants: `service-matrix`, `service-masonry`, `service-bento`.
- Design intents: Crosses services and capability dimensions in a strict comparison matrix.; Varies module height according to real description needs while preserving column alignment.; Assigns deliberate span hierarchy to primary and secondary services.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2104.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.minimal`

- Purpose: services composition using `minimal_links`.
- Visual grammar: `rows`; `contained` edge; media intensity 1; `large` type role.
- Members: `minimal_service_links`.
- Variants: `minimal-service-links`.
- Design intents: Reduces the offer to a quiet list of clear service links.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.photo`

- Purpose: services composition using `photo_service_cards`.
- Visual grammar: `grid`; `contained` edge; media intensity 2; `large` type role.
- Members: `photo_service_cards`, `split_service_media`.
- Variants: `photo-service-cards`, `split-service-media`.
- Design intents: Pairs each service with contextual media in consistent, non-nested modules.; Uses one contextual media field beside a concise service directory.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2772.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 2.
- Mobile behavior: `linear_stack`.

## `services.process`

- Purpose: services composition using `process_services`.
- Visual grammar: `timeline`; `contained` edge; media intensity 1; `large` type role.
- Members: `process_like_services`, `service_timeline`.
- Variants: `process-like-services`, `service-timeline`.
- Design intents: Explains services through a phased customer journey rather than isolated cards.; Places service stages on a continuous timeline with attached scope detail.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2772.
- Ideal transitions: change pattern, edge or media intensity after `timeline`.
- Poor transitions: repeat `timeline` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.rail`

- Purpose: services composition using `horizontal_service_rail`.
- Visual grammar: `rail`; `viewport_edge` edge; media intensity 1; `large` type role.
- Members: `horizontal_service_rail`.
- Variants: `horizontal-service-rail`.
- Design intents: Lets services advance as a horizontal snap rail with visible progress.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rail`.
- Poor transitions: repeat `rail` with the same `viewport_edge` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.rows`

- Purpose: services composition using `editorial_rows`.
- Visual grammar: `rows`; `contained` edge; media intensity 1; `large` type role.
- Members: `editorial_service_rows`, `numbered_service_list`, `sticky_service_detail`, `alternating_service_feature`, `quiet_service_chapters`, `editorial_service_folio`.
- Variants: `editorial-service-rows`, `numbered-service-list`, `sticky-service-detail`, `alternating-service-feature`, `quiet-service-chapters`, `editorial-service-folio`.
- Design intents: Runs services as spacious editorial rows with a stable title and action rhythm.; Uses visible numbering to make a long service offer easy to scan in order.; Keeps the selected service detail fixed while the service index advances beside it.; Alternates service summary and supporting context across the grid.; Separates service chapters with whitespace instead of heavy containers.; Pairs a folio index with service narratives in a magazine-like sequence.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.1605.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `services.technical`

- Purpose: services composition using `technical_specification`.
- Visual grammar: `matrix`; `contained` edge; media intensity 1; `large` type role.
- Members: `technical_service_table`, `capability_specification`, `technical_system_layers`.
- Variants: `technical-service-table`, `capability-specification`, `technical-system-layers`.
- Design intents: Uses aligned technical rows for direct capability comparison.; Frames each capability as a concise specification with stable labels.; Orders services as dependent system layers from foundation to finish.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2772.
- Ideal transitions: change pattern, edge or media intensity after `matrix`.
- Poor transitions: repeat `matrix` with the same `contained` edge and media intensity 1.
- Mobile behavior: `linear_stack`.

## `trust.area`

- Purpose: trust composition using `service_area`.
- Visual grammar: `split`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_service_area_map`.
- Variants: `verified-service-area-map`.
- Design intents: Balances a verified area list with a non-claiming geographic view.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.awards`

- Purpose: trust composition using `awards_ledger`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_awards_ledger`.
- Variants: `verified-awards-ledger`.
- Design intents: Orders verified awards and dates in an editorial ledger.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.before_after`

- Purpose: trust composition using `before_after_evidence`.
- Visual grammar: `split`; `contained` edge; media intensity 1; `normal` type role.
- Members: `before_after_evidence`.
- Variants: `before-after-evidence`.
- Design intents: Locks verified before and after evidence to a matched comparison axis.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 1.
- Mobile behavior: `compact_verified_list`.

## `trust.brands`

- Purpose: trust composition using `brand_authorizations`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_brand_authorizations`.
- Variants: `verified-brand-authorizations`.
- Design intents: Displays only verified brand authorizations in an aligned name grid.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.certifications`

- Purpose: trust composition using `verified_badges`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_certification_badges`.
- Variants: `verified-certification-badges`.
- Design intents: Arranges only verified certifications in an even badge grid.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.emergency`

- Purpose: trust composition using `emergency_availability`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_emergency_availability`.
- Variants: `verified-emergency-availability`.
- Design intents: Makes verified emergency availability and its contact route immediately legible.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.facts`

- Purpose: trust composition using `verified_fact_index`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `combined_verified_fact_strip`, `minimal_verified_fact_index`.
- Variants: `combined-verified-fact-strip`, `minimal-verified-fact-index`.
- Design intents: Runs several verified facts in one concise horizontal evidence strip.; Lists verified facts with minimal labels and generous separation.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2897.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.guarantee`

- Purpose: trust composition using `guarantee_statement`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_guarantee_statement`.
- Variants: `verified-guarantee-statement`.
- Design intents: Gives one verified guarantee statement clear prominence without embellishment.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.hours`

- Purpose: trust composition using `opening_hours`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_opening_hours`.
- Variants: `verified-opening-hours`.
- Design intents: Aligns verified opening hours in a practical day-and-time schedule.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.insurance`

- Purpose: trust composition using `verified_line`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_insurance_line`.
- Variants: `verified-insurance-line`.
- Design intents: Shows one verified insurance fact on a restrained evidence line.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.partners`

- Purpose: trust composition using `partner_directory`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_partner_directory`.
- Variants: `verified-partner-directory`.
- Design intents: Lists verified partners in a sober directory rather than decorative logos.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.process`

- Purpose: trust composition using `documented_process`.
- Visual grammar: `timeline`; `contained` edge; media intensity 0; `normal` type role.
- Members: `documented_process_proof`.
- Variants: `documented-process-proof`.
- Design intents: Turns documented process evidence into a clear sequence of supported phases.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `timeline`.
- Poor transitions: repeat `timeline` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.project`

- Purpose: trust composition using `artisan_project_evidence`.
- Visual grammar: `split`; `contained` edge; media intensity 1; `normal` type role.
- Members: `artisan_project_evidence`.
- Variants: `artisan-project-evidence`.
- Design intents: Pairs verified project media with its attached factual context.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `split`.
- Poor transitions: repeat `split` with the same `contained` edge and media intensity 1.
- Mobile behavior: `compact_verified_list`.

## `trust.response`

- Purpose: trust composition using `response_delay`.
- Visual grammar: `typographic`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_response_delay`.
- Variants: `verified-response-delay`.
- Design intents: Shows a verified response delay as one precise label-value statement.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `typographic`.
- Poor transitions: repeat `typographic` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.reviews`

- Purpose: trust composition using `verified_reviews`.
- Visual grammar: `rows`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_review_excerpt`, `verified_review_summary`.
- Variants: `verified-review-excerpt`, `verified-review-summary`.
- Design intents: Gives one attributed review excerpt a quiet reading measure.; Summarizes verified review evidence before showing attributed detail.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2897.
- Ideal transitions: change pattern, edge or media intensity after `rows`.
- Poor transitions: repeat `rows` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.statistics`

- Purpose: trust composition using `verified_statistics`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_project_statistics`, `verified_client_statistics`.
- Variants: `verified-project-statistics`, `verified-client-statistics`.
- Design intents: Presents verified project statistics as a comparable number grid.; Separates verified client statistics into compact label-value modules.
- Explicit differences: desktop flow/anchor/frame, mobile collapse/priority and focus progression; minimum pair distance 0.2317.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

## `trust.team`

- Purpose: trust composition using `team_credentials`.
- Visual grammar: `grid`; `contained` edge; media intensity 0; `normal` type role.
- Members: `verified_team_credentials`.
- Variants: `verified-team-credentials`.
- Design intents: Links verified credentials to the relevant team roles.
- Explicit differences: single-member family.
- Ideal transitions: change pattern, edge or media intensity after `grid`.
- Poor transitions: repeat `grid` with the same `contained` edge and media intensity 0.
- Mobile behavior: `compact_verified_list`.

