# Design Genome Renderer V0.2.1 — Resolved Plan & Coherence Gate

Status: engineering documentation for a still-experimental renderer. V3
remains the production engine. Nothing here is an aesthetic verdict; every
V0.2.1 lab output stays `NOT_REVIEWED`.

## 1. The bug: RenderPlan and HTML could disagree

V0.2 introduced `RenderPlan` as a reporting artifact built by
`build_render_plan(ctx)`, and had `render_site_genome(ctx)` separately
resolve hero media, walk `ctx.dna.section_order`, and render each section.
Both paths called into the same low-level methods (`media_for`,
`is_duplicate_copy`), which made most of them agree by construction. One
piece of state did not: **which literal copy had already been shown**.

`render_site_genome`'s loop mutated `ctx.used_copy` *while rendering*,
immediately after the hero section produced output:

```python
if section == "hero" and ctx.plain("tagline"):
    ctx = ctx.with_copy_used(ctx.plain("tagline"))
```

`build_render_plan` never replayed this. It called
`ctx.is_duplicate_copy(narrative)` for "about" against a context whose
`used_copy` was still empty, because plan-building did not walk sections in
render order accumulating the same state the renderer accumulated. Confirmed
on site-11:

```
RenderPlan (V0.2):  about.renderability = "full"
Actual HTML (V0.2): <section id="about" class="... about--micro">
```

The plan and the artifact it was supposed to describe disagreed. Any
consumer trusting the plan (a Figma import, a QA script, a human reading
`render-plan.json` instead of opening the page) would have been shown a
lie.

## 2. The fix: one resolution pass, one state, one consumer

`build_render_plan(ctx)` (`render_plan.py`) is now the **only** place that
makes a structural decision. It resolves hero media (with recomposition
authority), allocates the remaining media pool, and then walks
`dna.section_order` **in the exact order sections will render**, threading
one explicit, private state object (`_PlanState.used_copy`) through the
walk. "About" checks duplication against that state at the point in the
walk where it actually sits -- not against a snapshot from before the hero
"happened". Contact's real-slug fallback (rule AE) is resolved in the same
walk, not bolted onto the renderer afterward.

`render_site_genome(ctx, plan=None)` (`renderer.py`) now takes an optional,
already-built plan (building one internally if none is given) and
**materializes markup from it**. It does not call `is_duplicate_copy`,
`media_for`, or any hero-recomposition logic itself anymore -- those methods
were removed from `RenderContext` entirely (`resolved_for_rendering`,
`media_for_section`, `is_duplicate_copy`, `with_copy_used`). Every section
renderer in `sections.py` changed signature from `render_x(ctx)` to
`render_x(ctx, section_plan)` and reads `section_plan.renderability` /
`.resolved_mode` / `.resolved_media` instead of recomputing them.

```
Raw SiteDNA + RenderContext
        |
        v
  resolve hero (media + recomposition)      -- HeroMediaResolver
        v
  allocate media across sections            -- allocate_media
        v
  walk sections in render order,            -- build_render_plan's loop,
  threading content-usage state                _PlanState
        v
  resolve the contact fallback
        v
  evaluate coherence over the RESOLVED       -- coherence.build_coherence_report
  (post-recomposition, post-reduction)
  component sequence
        v
      RenderPlan  (sections + coherence)
        v
  render_site_genome(ctx, plan) materializes markup -- no further decisions
```

The lab (`lab/build.py`) builds the plan once per fixture and passes that
exact object to both `render_site_genome` (for the HTML) and every JSON
export (`render-plan.json`, `visual-completeness.json`,
`coherence-report.json`) -- not three separate calls that happen to be
deterministic. "The plan rendered" and "the plan reported" are the same
Python object.

## 3. SectionPlan, extended

```
section, component_id, family, variant_id
renderability            "full" | "reduced" | "omitted"
resolved_mode            hero: "media" | "diagram" | "no_image_intentional"
                                | "abstract_fallback" | "recomposed"
                          about: "narrative" | "fact_strip" | "none"
                          everything else: "standard"
resolved_content          structural flags (has_tagline, has_facts, service_count, ...)
resolved_media             media ids actually placed in the DOM
content_usage              literal copy THIS section consumes (feeds later duplicate checks)
media_role, media_provenance
fallback_used, fallback_reason
visual_weight, layout_pattern
coherence_status, coherence_reasons   -- attached after CoherenceReport runs
```

`resolved_mode="diagram"` is new and exists for an honest reason (§5.1):
`technical_nodes_network` can have `HeroMediaResolver` find real compatible
media (mode would otherwise read "media") while its bespoke realization
(a node/service diagram) never places that media in the DOM. Reporting
"media" there would have made `VisualCompletenessReport`'s empty-slot check
see a photo slot that was never promised.

## 4. Two more plan/HTML divergences found by this pass's own tests

Writing the plan/HTML consistency tests (§7) surfaced two more real
instances of the exact defect this release exists to close -- both in code
written during V0.2, both invisible until something actually compared the
plan against the rendered markup byte-for-byte:

### 4.1 `technical_nodes_network` claimed media it never displays

`render_technical_network_hero` builds a node diagram from the artisan's
real services and never reads its `media` argument. The V0.2 plan still
reported `resolved_media=[<id>]` whenever compatible media existed, because
`_resolve_hero` used `hero_resolution.media` unconditionally. Fixed by
`family_requirements.NO_MEDIA_CONSUMED_HERO_IDS` -- a single, explicit,
component-id-keyed set consulted by `_resolve_hero` (not a fixture check):
when a component is in that set, `resolved_media` is forced to `()`
regardless of what was found compatible, and `resolved_mode` becomes
`"diagram"` rather than `"media"`.

### 4.2 The material hero family under-reported its own limit

`render_material_hero` only ever places one macro image
(`media[:1]`), but the `hero.material` family's own blueprint declares
`media_count_max=3`. On fixtures where two stock photos both matched the
family's `stock_photo` OR-alternative (site-04, site-05, site-10),
`HeroMediaResolver` correctly resolved two compatible items, and V0.2's plan
claimed the hero used both -- while the actual hero only ever shows the
first. Fixed by `family_requirements.HERO_MEDIA_DISPLAY_LIMIT_BY_FAMILY`
(`{"hero.material": 1}`), applied in `_resolve_hero` before the plan is
built.

**This fix was not cosmetic.** The extra photo `hero.material` was
silently over-reserving is now freed back into `MediaAllocationPlan` for
gallery/about (`allocate_media` now takes the hero's *actual* consumed ids,
not everything `HeroMediaResolver` merely found). Concretely: site-04's
gallery was **entirely omitted** in the V0.2 artifact (`resolved_media: []`,
confirmed against the preserved `sites-v0.2/site-04/render-plan.json`) --
its only candidate photo was reserved by a hero that was never going to
show it. In V0.2.1 that photo reaches the gallery and the section renders.
Same effect on site-05 and site-10.

## 5. CoherenceReport: does the resolved plan read as one visual language

### 5.1 Why hero fidelity alone was not enough

V0.2's `art_direction_fidelity` was "hero has media → 1.0". Site-11 shows
why that is insufficient: `cinematic_luxury` + a now-correct, media-led
`hero.cinematic` component, sitting next to `technical_expertise_about`
(traits `technical`, `information_dense`). The Design Genome's own
`component_relationships.TRAIT_PAIR_AFFINITY` table already scores that
trait pair at **-0.24** -- this is not a new judgement, it already existed,
generation-time, in `DesignGenome`'s own candidate scoring. It was just
never read anywhere else, and generation-time scoring only ever compares
**adjacent** sections in the page
(`component_relationships.sequence_affinity`), which dilutes a
hero-vs-distant-section clash almost to nothing: the full adjacent sequence
for site-11 scores **0.96**, while the *direct* hero/about pair -- three
positions apart in the page -- scores **0.50**.

### 5.2 What CoherenceReport actually computes

`coherence.py` adds no new compatibility data. It re-reads
`compatible_directions`, `compatible_archetypes`, `incompatible_components`
and the existing trait-pair table, from a different angle: against the
**final resolved** plan (post-recomposition, post-reduction -- rule 25), and
**hero-anchored**, not adjacency-only, so a non-adjacent clash is not
averaged away.

| Dimension | What it reads | Source |
|---|---|---|
| `direction_component_alignment` | per-section `compatible_directions`/`compatible_archetypes` membership | mirrors `compatibility.py`'s own soft scoring, applied post-hoc |
| `hero_anchor_consistency` | `component_pair_affinity(hero, X)` for every other rendered section, worst pair kept | **new use** of an existing function -- the one that actually catches site-11 |
| `sequence_transition_consistency` | `sequence_affinity()` over the resolved sequence, verbatim | reused wholesale, rule 24 |
| `visual_weight_progression` | runs of 3+ consecutive `visual_weight>=4` sections | new, simple, explained |
| `layout_pattern_variety` | repeated `layout_pattern` count | same signal `VisualCompletenessReport.visual_rhythm` already used |
| `media_language_consistency` | multiple high-weight, media-dependent sections competing | new, simple, explained |
| `commercial_flow_consistency` | archetype's own `conversion_intensity` vs. whether the page closes on a conversion-led section | uses the archetype's own declared field, no new threshold invented |

`overall_score` is a **weighted** average (`hero_anchor_consistency` and
`sequence_transition_consistency` count for more than the supplementary
dimensions) -- an unweighted average let one genuinely low
`hero_anchor_consistency` get diluted into a falsely comfortable overall
number by several dimensions that read near-1.0 on almost any page.
`overall_status` (`coherent` / `warning` / `tension` / `incompatible`) also
reacts to the *worst* single dimension, not only the average, so one bad
clash cannot hide behind five fine ones (rule 41).

**Per-section `status`** (`compatible` / `neutral` / `tension` /
`incompatible`) is a direct, unweighted read of that section's own
direction/archetype declarations, upgraded to `tension` when that specific
section is also the one driving a low `hero_anchor_consistency` score --
so the report points at the actual offending section, not just an
aggregate number.

### 5.3 No new/arbitrary compatibility system

Nothing in `coherence.py` inspects a fixture id, a trade, or invents a new
scoring table. Every number it produces traces back to a field
`design_genome` already defines (`compatible_directions`,
`compatible_archetypes`, `traits`, `TRAIT_PAIR_AFFINITY`,
`CATEGORY_TRANSITION_AFFINITY`, `visual_weight`, `layout_pattern`,
`conversion_intensity`) or a function it already ships
(`component_pair_affinity`, `sequence_affinity`). `generator/design_genome/`
has **zero modifications** in this pass.

### 5.4 No automatic repair

Per rule 26/27, this pass detects; it does not redesign. No DNA field is
changed based on a coherence score. The one place a *component* is already
substituted -- `HeroMediaResolver`'s recomposition when a media-dependent
family has no compatible media at all -- predates this pass (V0.2, rule K)
and is itself deterministic and metadata-driven (§2 of the V0.2 doc), never
`if score < threshold: pick something`.

## 6. VisualCompletenessReport: two dimensions made honest

### 6.1 `empty_slot_risk` (was a bare `1.0`)

Now inspects the resolved plan directly: a gallery marked non-omitted with
zero `resolved_media`; a hero whose `resolved_mode` is `"media"` with zero
`resolved_media`; any rendered, non-fallback section whose component
declares `image_dependency >= 0.7` yet resolved with no media at all. When
none of these hold, the dimension is still `1.0` -- but the reason string
says *why* ("plan contains no section that is rendered with an
implied-but-unresolved media region"), not "the renderer is supposed to
guarantee this."

### 6.2 `mobile_readiness` (was a bare `1.0`)

Checks, per rendered section: does its `ComponentDefinition.blueprint_spec`
declare `collapse_strategy`/`priority_anchor` (real fields, verified rather
than assumed); does the hero declare a `mobile_media_behavior` when it
carries media; for the family-specific bespoke treatments that ship their
own responsive CSS (bento, network, material, selector, ...), does that CSS
class **actually appear** inside a `@media(max-width:900px)` block in the
real, shipped `FAMILY_CSS` string (a live check against the stylesheet, not
an assertion that a table is correct); and does a visible action path
(contact/cta) survive at all. All 12 lab fixtures currently score `1.0` on
this dimension -- see §8 for why that is reported plainly rather than
hidden, and `test_mobile_readiness_is_not_a_hardcoded_constant` for the
constructed counter-example that proves the dimension is not a constant.

### 6.3 `art_direction_fidelity` now incorporates coherence

```
media_component = 1.0, unless a requires-media family resolved with no
                  media and no recomposition (unchanged from V0.2)
coherence_component = CoherenceReport.hero_anchor_consistency.score
fidelity = media_component * 0.5 + coherence_component * 0.5
```

Site-11's hero now has real media (`media_component = 1.0`), but
`hero_anchor_consistency = 0.25` pulls `art_direction_fidelity` down to
`0.625` (from V0.2's automatic `1.0`) -- it can no longer pass just because
the hero has a photo (rule 22).

## 7. Plan/HTML consistency tests

`test_genome_renderer_v021.py` (backend/tests) adds, among others:

- `test_site11_about_plan_and_html_agree_on_reduced` -- the literal
  regression.
- `test_render_plan_and_html_are_never_built_from_different_resolutions` --
  an explicitly-built plan and `render_site_genome`'s own internal one
  produce byte-identical HTML.
- `test_plan_component_ids_match_html_component_ids_for_every_lab_fixture`
  and `test_plan_resolved_media_matches_html_media_for_every_lab_fixture`
  -- parametrized across all 12 lab fixtures; these two found §4.1 and §4.2
  before any human review did.
- `test_omitted_section_is_absent_from_html`,
  `test_reduced_section_renders_reduced_markup`,
  `test_full_section_renders_full_markup`.
- `test_contact_fallback_is_represented_in_the_plan_not_only_the_html`.
- Determinism: `test_plan_is_deterministic`,
  `test_html_is_deterministic_from_the_same_plan`,
  `test_coherence_report_is_deterministic`.
- Coherence: `test_coherence_uses_resolved_component_not_initial_dna`,
  `test_site11_coherence_flags_a_real_tension_not_a_perfect_score`,
  `test_coherent_and_conflicting_plans_are_actually_distinguished`,
  `test_coherence_report_never_emits_an_aesthetic_verdict`.
- VisualCompleteness: `test_art_direction_fidelity_incorporates_coherence...`,
  `test_visual_completeness_two_constructed_plans_are_not_identical`,
  `test_mobile_readiness_is_not_a_hardcoded_constant`,
  `test_empty_slot_risk_is_not_a_hardcoded_constant`.
- `test_visual_lab_still_builds_twelve_not_reviewed_sites_with_coherence`
  -- also asserts the 12 coherence scores are **not** all identical (rule
  41: uniform 1.0s across every fixture would be suspicious, not a win).

## 8. Metrics, V0.2 → V0.2.1

| Metric | V0.2 | V0.2.1 |
|---|---|---|
| Plan/HTML mismatches known | 1 confirmed (site-11 about) + 2 more found once this pass added systematic checks (technical_nodes_network media claim, material hero over-claim) | 0 (enforced by parametrized tests across all 12 fixtures, not spot-checked) |
| `VisualCompletenessReport` dimensions that were a bare constant | 2 (`empty_slot_risk`, `mobile_readiness`) | 0 |
| Sites with a gallery incorrectly omitted due to hero over-reserving media | 3 (site-04, 05, 10) | 0 |
| Coherence `overall_status` distribution across the 12 fixtures | not computed in V0.2 | 8 `coherent`, 3 `tension` (site-04, 05, 10 -- now that their gallery renders and exposes a real hero/gallery media-dominance clash), 1 `warning` (site-12); site-11 also `tension` |
| Sites where all completeness/coherence dimensions read exactly 1.0 | n/a | 0 of 12 -- every fixture has at least one dimension below 1.0 (see manifest.json) |

Site-11's own before/after, in full:

```
V0.2 RenderPlan claimed:   about.renderability = "full"
V0.2 HTML actually showed:  <section id="about" class="... about--micro">
V0.2.1: both now say:      about.renderability = "reduced",
                           about.resolved_mode = "fact_strip"
V0.2.1 CoherenceReport:    overall_score = 0.744, overall_status = "tension"
                           hero_anchor_consistency = 0.25
                           reason: hero(quiet_luxury_window) vs
                             about(technical_expertise_about): score=0.50,
                             trait_pair:cinematic+information_dense:-0.24,
                             technical_language_break; hero vs
                             gallery(portrait_landscape_dialogue): score=0.25,
                             adjacent_media_led_sections,
                             competing_image_dominance
art_direction_fidelity:    0.625 (was an automatic 1.0 in V0.2)
```

Site-11's rendered HTML is otherwise unchanged from V0.2 -- this pass is
instrumentation, not a redesign (rule 39/56). The about section was already
correctly reduced by the browser; V0.2.1 makes the *report* tell the truth
about that, and adds the coherence signal that explains *why* the page is
still not a fully faithful `cinematic_luxury` realization even with a
working hero photo.

## 9. Known limitations

- **`mobile_readiness` is `1.0` for all 12 current fixtures.** This is
  reported honestly rather than engineered to look more varied: none of the
  12 lack a declared `collapse_strategy`, none lack a conversion path (the
  V0.2 contact fallback guarantees one), and the bespoke components they use
  all have a verified `FAMILY_CSS` mobile rule. The dimension is
  demonstrably not a constant (§6.2, unit-tested with a counter-example) --
  it simply does not find a structural risk in this specific corpus. True
  mobile *appearance* still requires the browser captures and human review
  (rule 43); a `browser-validation.json` companion artifact was scoped as
  optional (rule 14) and was not added this pass to keep the change focused
  on the plan/coherence architecture.
- **Coherence thresholds are heuristic, not calibrated.** Rule 52
  explicitly does not ask for scientific precision -- only that a
  deliberately coherent combination and a deliberately conflicting one are
  told apart (tested). The exact boundary between `warning` and `tension`
  is a judgement call, documented in `coherence.py`, not derived from data.
- **No automatic repair.** A `tension`/`incompatible` result is reported,
  never silently fixed by swapping a component (rule 26/27); that decision
  stays human.
- **Component-realization scope is unchanged from V0.2** (rule 44): this
  pass did not add new bespoke family renderers.
- **`generator/v3/` and `generator/design_genome/` have zero diffs** in this
  pass -- confirmed via `git diff --stat`, not merely intended.
