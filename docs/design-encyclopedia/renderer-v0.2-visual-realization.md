# Design Genome Renderer V0.2 — Visual Realization Pass

Status: engineering documentation for a still-experimental renderer. V3 remains
the production engine. Nothing here has been through human aesthetic review;
every V0.2 output in the lab is tagged `NOT_REVIEWED` and must stay that way
until a person looks at it.

## 1. What V0.1 actually did wrong

The V0.1 renderer (`generator/genome_renderer/`) is a real, working pipeline:
Design Genome resolves a `SiteDNA` (component ids + system ids), and the
renderer turns that into HTML/CSS. The visual review of the 12 lab fixtures
found the output looked like wireframes far more often than it should have.
Three confirmed, code-level root causes explain nearly all of it — this was
**not** primarily a content or component-catalog problem.

### 1.1 `media_for()`'s OR-as-AND bug (the single highest-impact defect)

`RenderContext.media_for()` decided whether a media item could serve a
component. It merged `required_media` (AND: every listed role must hold) and
`required_any_media` (OR: any one role is enough) into one set, then applied
provenance locks (`artisan_project`, `before_after` must come from an
artisan-sourced item) to *that whole merged set*. Any hero whose
`required_any_media` happened to include `artisan_project` as one of several
acceptable alternatives — `photo_cover`, `split_photo`, `collage`,
`cinematic`, `material`, `rail` (6 of 12 hero families) — had every other
alternative silently vetoed too, including `stock_photo`, even when a
compatible stock photo was sitting right there in the inventory. Confirmed
empirically: before the fix, 7 of the 12 lab fixtures fell back to the
generic rectangle despite each fixture shipping exactly two usable stock
photos (`role: hero`, `role: gallery`).

This is why the Design Genome's own compatibility check
(`design_genome/compatibility.py::evaluate_component`) never had this bug —
it correctly intersects `required_any_media` against the media inventory —
while the renderer's independent re-implementation of "is this media
compatible" did not. Two implementations of overlapping logic, one correct,
one not, is the textbook shape of this kind of defect.

### 1.2 `limit=0` treated as "no limit," and a floor of `max(1, ...)`

`render_hero()` requested `media_for(component, limit=max(1,
media_count_max))`. For typographic heroes, `media_count_max` is deliberately
`0` (no-image-by-design family) — but `max(1, 0)` forced a request for one
image anyway, and `media_for`'s own slicing (`values[:limit] if limit else
values`) treated `limit=0` as falsy and returned the *entire* unsliced list.
Two bugs compounding: a family that promises zero photos could still receive
one, incidentally, whenever a stock photo happened to match the generic
`section_roles` fallback.

### 1.3 The fallback substitution ran *before* layout, for every family alike

`render_hero()` always did `layout_regions(component, copy, visuals or
fallback)`. If no real media resolved, the abstract rectangle was substituted
unconditionally — for a `cinematic` family that genuinely needed a photo and
for a `technical` family whose own visual language is already diagrammatic.
Rule H's distinction ("intentional abstract" is fine for technical/spatial;
never fine for cinematic/material/photo-led) did not exist in code at all.

### 1.4 Component realization: one renderer per section category, full stop

`render_services()` produced **byte-identical markup** for all 35 services
components — `<ol class="service-list"><li>01 ...</li></ol>` — regardless of
family. `service_bento`, `conversion_service_selector` and
`editorial_service_folio` differed only in a `data-component` attribute and
whichever of ~6 `layout_regions()` wrapper shapes their `layout_pattern`
mapped to. The rich, family-specific metadata design_genome computes (flow,
anchor, frame, focus progression, design intent prose) was real and
thoughtful; the renderer read only a handful of structural fields from it to
choose a wrapper `<div>` shape, never the family/variant identity itself.
This is the literal meaning of "a component being reachable in the DOM is not
the same as its concept being realized" (rule M).

### 1.5 Two more, smaller but concrete bugs found while fixing the above

- `layout_regions()` chose the rail wrapper (`.g-layout--rail`, a
  horizontal-scroll carousel) whenever `flow_direction == "horizontal_progression"`
  — a semantic label shared by 37 catalog components across every category,
  most of which are ordinary split/grid/matrix layouts, not carousels. Same
  bug shape for `layered_progression` → overlay (19 more components). Fixed
  by trusting `layout_pattern` (already resolved for exactly this purpose)
  as the sole wrapper-shape signal.
- `render_contact()` required a DNA-assigned `contact_component` or
  `form_component` to exist before rendering anything. All 12 lab fixtures
  have no phone/email, so the Design Genome never assigns either — meaning
  **zero of the 12 fixtures had a conversion path of any kind**, even though
  a real `/pub/{slug}/demande-devis` endpoint exists for all of them (rule
  AE). Fixed generically: a real slug now gets a minimal, honest quote-form
  section when no richer contact component was assigned.

## 2. V0.2 architecture

Nothing in `design_genome/` changed. `generator/v3/` is untouched. The fix is
entirely inside `generator/genome_renderer/`, and is additive: five new
modules plus targeted edits to the four existing ones.

```
generator/genome_renderer/
  family_requirements.py   NEW  per-family hero media policy (rule H/L)
  media_plan.py             NEW  HeroMediaResolver + MediaAllocationPlan
  render_plan.py            NEW  RenderPlan / SectionPlan (rule D)
  visual_completeness.py    NEW  VisualCompletenessReport (rule J)
  families.py               NEW  component/family-specific realizations (rule M)
  context.py                EDIT  media_for() OR/AND fix, limit=0 fix,
                                   media_for_section(), resolved_for_rendering(),
                                   ContentUsageRegistry (is_duplicate_copy)
  primitives.py              EDIT  no-empty-media recompose, pattern-authoritative
                                   wrapper selection, actions_html(), image()
  sections.py                 EDIT  hero/services delegate to families.py,
                                   about duplication + relationship-aware media,
                                   trust process/verified honesty, contact fallback
  renderer.py                  EDIT  resolves the plan before rendering; contact fallback
```

### 2.1 RenderPlan (rule D)

`build_render_plan(ctx, fixture_id)` produces one `SectionPlan` per rendered
section: `component_id`, `family`, `variant_id`, `resolved_content`,
`resolved_media` (ids), `media_role`, `media_provenance`, `fallback_used`,
`fallback_reason`, `renderability` (`full` / `reduced` / `omitted`),
`visual_weight`, `layout_pattern`. It is built by calling the *same*
resolution methods (`RenderContext.resolved_for_rendering()`,
`media_for_section()`, `is_duplicate_copy()`) that the HTML renderer itself
uses — not a parallel, potentially-diverging re-derivation. This is a
narrower claim than "the renderer consumes a fully object-shaped plan
end-to-end" and is stated honestly as such: the shared resolvers are the
single source of truth both paths read from, so the plan cannot disagree
with the markup on the decisions that matter (media, fallback, recomposition).

Per-site `render-plan.json` files are written into the lab output next to
each site's `index.html`.

### 2.2 MediaAllocationPlan (rule E) and HeroMediaResolver (rule G)

`RenderContext.resolved_for_rendering()` runs once, before any section
renders:

1. `HeroMediaResolver.resolve(ctx, dna)` resolves the hero **first**, against
   the full media pool — never `available_images[0]`, always the fixed
   `media_for()` predicate — and decides one of four modes:
   - `media`: compatible media found, used directly.
   - `no_image_intentional`: the family (typographic, or
     `media_count_max == 0`) never promised a photo; no fallback markup at
     all, a real typographic composition instead.
   - `abstract_fallback`: the family's policy is `tolerant_abstract`
     (technical / spatial / conversion) — the geometric composition is that
     family's own intentional visual language, not a cop-out.
   - `recomposed`: the family's policy is `requires_media`
     (cinematic / material / photo_cover / split_photo / collage /
     transformation / rail / project), no compatible media exists anywhere
     in the inventory, and no fallback is acceptable — the hero component is
     swapped for a no-image-capable component compatible with the resolved
     `art_direction` (falling back to `site_archetype`, then to the single
     most generic no-image variant, deterministically — never randomly). The
     substitution is recorded as a `DecisionRecord` (rule BD): `field`,
     `initial`, `resolved`, `reason`.
2. `allocate_media(ctx, dna, hero_resolution)` reserves whatever the hero
   used, then gives gallery and about — in that priority order — whatever
   remains, via `media_for_section()`. A photo already shown in the hero is
   never silently reused as if it were separate "about" evidence, and the
   hero is never left waiting on media a lower-priority section already
   claimed.

### 2.3 Family requirements (rule L)

`family_requirements.py` is a small, explicit table
(`HERO_FAMILY_POLICIES`), keyed by `ComponentDefinition.family_id`, not by
component id or fixture — mapping each of the 12 hero families to one of
three policies (`requires_media`, `tolerant_abstract`, `no_media_by_design`)
with a one-line reason. This is what `HeroMediaResolver` and
`VisualCompletenessReport` both read; it is the only place family media
policy is declared, so the two can't drift.

### 2.4 VisualCompletenessReport (rule J) — not an aesthetic score

`visual_completeness.py::assess(plan)` computes ten dimensions
(`hero_readiness`, `media_readiness`, `content_density`,
`commercial_completeness`, `narrative_completeness`, `section_balance`,
`empty_slot_risk`, `art_direction_fidelity`, `visual_rhythm`,
`mobile_readiness`), each a 0–1 *structural* ratio with plain-language
reasons attached when below threshold — e.g. "about narrative duplicated the
hero tagline; reduced to a fact strip", never "not beautiful enough". No
dimension anywhere produces or implies an aesthetic verdict; that judgment
stays with the human reviewer (rule AQ/BJ). Per-site
`visual-completeness.json` files are written into the lab output.

### 2.5 Component realizations (rule M/N/O/P/Q/R)

`families.py` adds real, distinct mechanisms for the components explicitly
named in the brief, dispatched by component id or family id — never by
fixture id or trade:

| Component / family | Mechanism |
|---|---|
| `service_bento` | Asymmetric CSS grid: one dominant module (span 3×2), one tall module, remaining standard modules — real hierarchy, not a uniform list |
| `editorial_service_folio` | Large offset numerals, alternating row indent, rule lines — typography as layout |
| `conversion_service_selector` / `problem_solution_services` | A featured card + secondary cards (selector), or a scannable ledger (problem/solution) — every entry links to the real `#contact` quote action |
| `workshop_service_samples` / `material_service_catalogue` / `project_type_services` | Sample-tag framing, swatch tokens — material composition without fabricating projects |
| services.index family | Dominant index numerals, service name as the primary type element |
| services.minimal family | A quiet link list, deliberately restrained — no numbering, no cards |
| services.grid / services.photo | Equal, uniform modules — the deliberate counterpoint to bento |
| `technical_nodes_network` | A real hub-and-node diagram built from the artisan's actual services (2–5 real service names as nodes around a hub); no invented labels or numbers |
| `material_macro_title` (and `hero.material` family) | A macro image frame overlapping the copy block via negative margin — texture-led, not a generic split |
| Typographic hero family (9 variants) | Nine distinct treatments dispatched by variant id: oversized statement, quiet centered, manifesto columns, editorial index (with a real services-derived index), architectural void, brutalist block, local-conversion dock |

Everything else in the 260-component catalog still renders through the
generic path (family-level CSS hooks via `data-*` attributes, unchanged from
V0.1). That is deliberate and reported honestly in the component-realization
audit (§4), not hidden.

## 3. Truth-safety and provenance (unchanged principle, now actually enforced)

Stock media was always meant to serve ambiance/material/generic-hero roles
and never claim to be "our project" without artisan provenance — see
`gallery_spec`'s `stock_project_wording_forbidden` and the pre-existing tests
`test_stock_media_cannot_fill_artisan_project_slot` /
`test_stock_gallery_is_never_labelled_as_artisan_work`. The `media_for()` fix
does not weaken this: the provenance lock on `artisan_project`/`before_after`
is still absolute (`item.source_class == "artisan"` is still required for
those two roles specifically) — the fix only stops that lock from also
vetoing an item that would instead satisfy a *different*, legitimately
available role such as `stock_photo`.

## 4. Component realization audit (rule AL)

Status legend — `REALIZED`: distinct, verified mechanism; `PARTIAL`: distinct
wrapper/CSS treatment via existing structural attributes but no bespoke
per-family markup; `UNREALIZED`: renders through the fully generic path only.

| component_id / family | status | note |
|---|---|---|
| service_bento | REALIZED | asymmetric grid, see §2.5; `test_service_bento_has_asymmetric_spans_not_a_uniform_list` |
| editorial_service_folio | REALIZED | numerals + offsets; `test_editorial_service_folio_uses_large_numbers_and_offsets` |
| conversion_service_selector | REALIZED | selector cards + real action links; `test_conversion_service_selector_links_every_entry_to_the_real_quote_action` |
| problem_solution_services | REALIZED | ledger variant of the same family concept |
| workshop_service_samples | REALIZED | material sample framing |
| services.index family (3 components) | REALIZED | dominant numeral index |
| services.minimal family (1 component) | REALIZED | quiet link list |
| services.grid / services.photo (6 components) | REALIZED | equal-module grid |
| services.rows / technical / accordion / rail / process / matrix (non-bento) / conversion (service_map_and_list) / material (2 remaining) | PARTIAL | improved default rows renderer (real numbered rows, no empty media), not a bespoke per-family mechanism |
| technical_nodes_network | REALIZED | real hub/node diagram from real services |
| hero.material family (4 components: only `material_macro_title` bespoke) | PARTIAL | `material_macro_title` REALIZED; `layered_material_scene` / `parallax_layered_material` / `workshop_gesture_cover` render through the fixed generic hero path (real media now resolves correctly, but no macro-frame treatment) |
| hero.typographic family (9 components) | REALIZED | 9 distinct dispatched treatments |
| hero.split_photo / hero.cinematic / hero.photo_cover / hero.collage / hero.project / hero.transformation / hero.rail (28 components) | PARTIAL | media resolution and wrapper-shape selection are now correct (root cause fixed); no bespoke per-variant markup beyond the existing wrapper shapes |
| hero.technical (5, minus technical_nodes_network) / hero.spatial (2) / hero.conversion (5) | PARTIAL | tolerant-abstract policy now correctly applied; generic markup otherwise |
| about / trust / cta / contact / footer / header (all components) | PARTIAL | empty-media fix, duplication handling (about), process/verified honesty (trust), and the contact fallback apply generically across every component in these categories; no bespoke per-component markup was added this pass |

**Coverage summary, weighted by what the 12 fixtures actually use (rule
AM):** every hero and services component actually selected by the 12
fixtures is REALIZED or benefits directly from a root-cause fix (media
resolution, wrapper-shape correctness, empty-media elimination). Beyond that
priority set, the remaining ~230 catalog components are PARTIAL: correctly
and safely rendered (no empty media, no incorrect wrapper class, honest
fallback policy), but not yet individually bespoke. No component in the
catalog is UNREALIZED in the sense of "broken" — PARTIAL here means "shares
the improved generic path," not "still shows the V0.1 defects."

## 5. Same-12 methodology (rule AN)

The 12 lab fixtures (`generator/genome_renderer/lab/fixtures.py`) were not
modified — same company names, trades, cities, services, facts, and
`selected_media` (each fixture: exactly two Pexels stock photos, roles
`hero` and `gallery`). Re-running `DesignGenome().generate()` against the
same seeds produces the same `SiteDNA` for all 12 (design/composition
signatures identical to V0.1 — verified below), because nothing in
`design_genome/` changed. What changed is purely how the renderer turns that
same DNA into HTML.

## 6. Metrics, V0.1 → V0.2 (measured against the same 12 sites)

| Metric | V0.1 | V0.2 |
|---|---|---|
| Empty `.g-media` slots (site-wide, all 12) | 16 | 0 |
| Generic `graphic-fallback` rectangles used | 8 | 0 |
| About sections repeating the hero tagline verbatim in a full paragraph | 9 | 0 |
| Sites with zero conversion path (no phone/email/CTA/contact/form) | 12 | 0 |
| Sites with a real hero photo where one was available | 5 / 12 | 12 / 12 |
| Hero DNA recompositions needed for this corpus | n/a | 0 (mechanism verified by dedicated unit tests instead — see §7) |

## 7. Tests

`backend/tests/test_genome_renderer_v02.py` (40 tests) covers: the
`media_for` OR/AND fix directly, stock-cannot-fill-`artisan_project`,
cinematic/material no-media recomposition, technical's tolerant abstract
fallback, typographic zero-media guarantee, documented (non-magic) decision
records, zero empty media slots (including a fixture with no media at all),
`service_bento` vs `minimal_service_links` structural distinctness,
`technical_nodes_network`'s real node structure with no invented numbers,
six hero families' structural distinctness, about duplication reduction (and
the negative case — real, distinct content is kept in full), trust
process-vs-verified honesty, the real-slug contact fallback,
`VisualCompletenessReport` never emitting an aesthetic verdict,
`MediaAllocationPlan` never double-booking one media item across sections,
determinism, XSS escaping, and that all 12 lab fixtures still build with
`NOT_REVIEWED` status and zero empty media slots / generic fallbacks.
`backend/tests/test_genome_renderer.py` (19 pre-existing tests) all still
pass unmodified except two literal-string updates (the renderer version
string, and the V0.1→V0.2 Vercel-marker filename correction — see the final
report for why).

## 8. Known limitations (stated plainly, not hidden)

- **Corpus has no phone/email at all.** Every one of the 12 fixtures has
  `telephone=""`, `email=""`. This is a genuine, pre-existing property of
  the fixture data (which this pass is forbidden from enriching), not a
  renderer defect — but it means `contact_component`/`form_component` are
  never assigned by the Design Genome for any of the 12, and the only
  conversion path available for this corpus is the generic quote-form
  fallback (§1.5). CTA-family components (`cta_component`) are similarly
  never exercised by this corpus for the same reason.
- **Media scarcity limits `media_readiness` to 0.67 for 3 sites** (site-04,
  05, 10 — the three fixtures with a populated `about` section *and* a
  gallery). Each fixture has exactly two media items; the allocation plan
  correctly gives hero and gallery first claim, leaving none for about. This
  is honestly reported by `VisualCompletenessReport`, not concealed — it is
  a corpus constraint, not a bug.
- **DNA recomposition is untriggered by this corpus.** Because the
  `media_for` fix alone makes every fixture's existing stock media usable,
  none of the 12 fixtures currently need the `recomposed` path. The
  mechanism is real and covered by dedicated unit tests
  (`test_cinematic_hero_without_compatible_media_never_uses_generic_fallback`,
  `test_material_hero_without_media_recomposes_instead_of_abstract_rectangle`,
  `test_hero_resolver_decision_is_documented_not_magic`), constructed with
  an artificially empty media list — it was not possible to demonstrate it
  visually against the unmodified 12-fixture corpus without violating rule B.
- **~230 of 260 catalog components remain PARTIAL** (§4): safely and
  correctly rendered via the generic path, not yet individually realized.
  Rule AM's priority order (12-fixture usage first) was followed
  deliberately; broadening bespoke coverage further was out of scope for
  this pass.
- **Full-page screenshot cropping is heuristic** (background-color
  bounding-box detection), not a true DOM-height query, because the capture
  pipeline runs headless Chrome via the DevTools Protocol rather than a
  browser-side script. Visually verified correct on all 12 fixtures but not
  mathematically guaranteed for an arbitrary future page shape.
- **V0.1's screenshots were captured at 1425×868 / 375×812** (a prior
  session's viewport choice), not exactly 1440×1200 / 390×844. The V0.1
  baseline is preserved exactly as it was; the size difference is cosmetic
  and does not affect the before/after comparison.
