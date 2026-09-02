# Genome Renderer V0.2 — Before / After Report (same 12 fixtures)

Aesthetic status for every V0.2 result below is **NOT_REVIEWED**. This table
reports structural, verifiable facts (DNA, media resolution, component
mechanism, completeness dimensions) — it makes no beauty claim. Human
review happens next, via the before/after lab
(`artifacts/genome-renderer-lab/index.html`) and the Figma/Vercel package.

Initial DNA and resolved DNA are identical for all 12 (no recomposition was
needed once the media-resolution bug was fixed — see the main doc, §8, for
why the recomposition path is real but untriggered by this corpus).

| Site | V0.1 issue (confirmed in code, not just observed) | V0.2 engine change that fixed it | Media allocation (V0.2) | Visual completeness (dimensions < 1.0) | Component realization | Aesthetic status |
|---|---|---|---|---|---|---|
| **01** Plomberie Rive Gauche | `offset_residential_photo` hero showed the abstract fallback despite 2 stock photos present | `media_for()` OR/AND fix (§1.1): `split_photo` family's `required_any_media` includes `artisan_project`, which vetoed the compatible `stock_photo` | hero ← stock hero-role photo; gallery role photo → reserved but no gallery in this DNA; about — not present | none | `conversion_service_selector` → REALIZED (selector cards + real quote links) | NOT_REVIEWED |
| **02** Maison Eau | Split hero rendered with no photo at all; about section weak (tagline repeated) | Same `media_for` fix; **also** fixed the independent rail-misclassification bug (§1.5) that was forcing this `split`-pattern hero into a horizontal-rail wrapper | hero ← real bathroom/architecture photo, genuine 2-column split | visual_rhythm 0.85 (one repeated layout pattern) | `conversion_service_selector` → REALIZED; about → reduced to micro (duplicate tagline detected) | NOT_REVIEWED |
| **03** Flux Technique | Already had media (technical family bypassed the bug by accident, §1.1); services and about were fully generic | About's empty-media path fixed; trust honesty fix (process vs verified) applies here | hero ← real photo (unchanged path); about ← opportunistic ambient photo now allowed | none | `local_service_directory` → PARTIAL (index-family generic, still improved) | NOT_REVIEWED |
| **04** Nuance Habitat | `parallax_layered_material` hero had a photo already; about/gallery/services fully generic, no differentiation | Empty-media fix for about; services grid family gets its own equal-module treatment | hero ← real architectural photo; gallery ← 1 stock ambient photo; about ← none left (2-photo scarcity, honestly reported) | media_readiness 0.67 (about wanted a photo, none left after hero+gallery) | `icon_service_grid` → REALIZED (equal-module grid, distinct from bento) | NOT_REVIEWED |
| **05** Atelier des Teintes | `material_macro_title` — "ne donne pas réellement une sensation matière" (confirmed: generic split wrapper, no macro/frame treatment) | New `render_material_hero()`: macro frame with negative-margin copy overlap (§2.5); **also** fixed a real CSS bug found during verification (`align-items:center` on the material grid made the image collapse to zero height) | hero ← macro texture photo in the new frame treatment; gallery ← remaining photo; about ← none left | media_readiness 0.67, visual_rhythm 0.85 | `workshop_service_samples` → REALIZED (sample-tag/swatch framing) | NOT_REVIEWED |
| **06** Trame Maçonnerie | Already reasonable (technical family); about/trust fully generic | Trust process/verified honesty fix; empty-media fix | hero ← real photo (unchanged path) | visual_rhythm 0.85 | `minimal_service_links` → REALIZED (quiet list) | NOT_REVIEWED |
| **07** Ligne Porteuse | "Le test principal de réalisation composant" — `technical_nodes_network` was text+photo; `service_bento` was a generic 2-col grid, no hierarchy | New `render_technical_network_hero()` (real hub/node diagram from the 3 real services) + new `render_services_bento()` (asymmetric spans: 1 dominant + 1 tall + standard modules) | hero — no_image (network diagram doesn't use a photo by design); services — no media (bento is typographic/tokens) | visual_rhythm 0.85 | `technical_nodes_network` → REALIZED; `service_bento` → REALIZED | NOT_REVIEWED |
| **08** Circuit Atelier | Already had media; services (`problem_solution_services`) fully generic | New selector-ledger ochre for `problem_solution_services`; contact fallback now gives it a conversion path (had none in V0.1) | hero ← real photo (unchanged path) | visual_rhythm 0.85 | `problem_solution_services` → REALIZED (ledger variant) | NOT_REVIEWED |
| **09** Électricité des Dômes | Typographic hero *accidentally* showed a stock photo it was never meant to use (§1.2 — `media_count_max=0` not respected); about absent, so less exposed to the duplication bug | `limit=0` fix + resolver's `no_media_by_design` mode; new manifesto-columns typographic treatment | hero — intentionally no image (by design, now actually enforced) | none | `editorial_columns_manifesto` → REALIZED (manifesto columns); `large_typographic_service_index` → REALIZED (dominant index) | NOT_REVIEWED |
| **10** Bois de Ligne | Same `material_macro_title` issue as site-05 | Same material hero fix | hero ← macro texture photo; gallery ← remaining photo; about ← none left | media_readiness 0.67, visual_rhythm 0.85 | `workshop_service_samples` → REALIZED | NOT_REVIEWED |
| **11** Volume Intérieur | "Le test principal de cohérence globale" — cinematic luxury hero showed the abstract fallback; about was a generic technical block | `media_for` fix resolves the real stock photo for the `cinematic` family (`hero.cinematic` policy `requires_media`, now correctly matched); about reduced (duplicate tagline) | hero ← real wood-texture photo; gallery ← remaining photo; about ← none left, reduced to micro instead of a weak full section | none | Cinematic family now media-led as promised; about → micro (no more "technical about" mismatch) | NOT_REVIEWED |
| **12** Séquence Rénovation | Hero fallback; about weak; photos only reached the gallery | `media_for` fix (`split_photo` family) puts a real bathroom-renovation photo in the hero, side-by-side split, framed; new folio treatment for services | hero ← real photo; gallery ← remaining photos (masonry); about ← reduced (duplicate tagline) | visual_rhythm 0.85 | `editorial_service_folio` → REALIZED (large numerals, offset rows) | NOT_REVIEWED |

## Regression check — sites the human review already liked (03, 04, 06, 08, 09, 10)

None of the six were rebuilt from scratch; the engine changes are additive
(new dispatch branches, bug fixes to shared primitives). What made each one
work is preserved:

- **03** technical/minimal clarity — hero still media-led via the same
  (now-correct) path; the technical `matrix`-pattern service treatment is
  unchanged for this component.
- **04** warm/editorial/gallery personality — centered-brand header
  (`header.editorial`) untouched; gallery still masonry/ambient; the only
  change is about no longer risking an empty media div, and services moving
  to a real equal-module grid instead of the old 2-col generic cards.
- **06** architectural/minimal framing — `framed_blueprint_specification`
  hero's `complete_frame` treatment is untouched (that comes from
  `component_attributes()`/`data-frame`, not from anything this pass
  changed); `minimal_service_links` now REALIZED as a quiet list rather than
  the old numbered grid, which is a closer match to "minimal," not a
  departure from it.
- **08** conversion clarity — the real quote-form contact fallback *adds* a
  conversion path this fixture did not have in V0.1; `conversion`-family
  services keep their action-oriented framing (now via the ledger
  treatment).
- **09** rail + typographic signature — the header's rail treatment is
  untouched; the hero's typographic signature is now *actually* typographic
  (V0.1 accidentally leaked a stock photo into it — see the site-09 row
  above), which strengthens the signature rather than changing it.
- **10** material/craft rhythm — same fix family as site-05; the craft
  rhythm intent (`workshop_service_samples`) is now a real material sample
  treatment instead of a generic list, i.e. more rhythm, not less.

No pixel-identical claim is made or intended (rule AK explicitly does not
ask for one); every site above still renders, still uses the same DNA
systems (color/typography/grid/spacing/geometry), and the properties the
human review named as working are either untouched or reinforced.
