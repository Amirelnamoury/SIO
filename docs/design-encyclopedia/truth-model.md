# Data truth and media provenance

## Four classes

1. `fact`: a claim backed by an explicit artisan field.
2. `derived_fact`: a transparent transformation of supplied data.
3. `safe_generic_copy`: a non-factual prompt such as “Parlons de votre projet”.
4. `forbidden_invention`: a factual assertion whose required source field is absent.

The classifier detects claims about experience, projects, clients, response time, ratings, RGE, insurance, guarantees, emergency service and certifications. The component registry independently requires the data behind reviews, statistics, badges, insurance, partners, brands, awards, delays, availability and service areas.

`ClaimRequirement` is the structured authority behind those decisions. A future copy layer must ask `can_render_claim(claim_type, facts)` before composing the sentence; text-pattern classification is a secondary audit guard, never the sole authorization.

## Missing information

A missing section is valid. An invented section is not. Galleries may disappear when no usable image exists; trust strips disappear when no verified fact exists; contact/form/CTA components disappear without a verified contact channel.

## Photo Director

The 192 photo profiles cover six trades, eight art directions and four section roles. Stock is permitted for ambient or illustrative roles only. Project evidence, before/after and artisan casebooks require artisan-owned media. Provider choice and downloading remain outside this package and outside public pages.

`can_use_media_wording(source, role, wording_role)` rejects stock paired with project, realization, worksite, before/after, team or selected-project wording.
