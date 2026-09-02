"""CoherenceReport: does the resolved plan still speak one visual language?

V0.2's only fidelity check was local to the hero ("does it have media").
Site-11 shows why that is not enough: a `cinematic_luxury` direction with a
now-correct, media-led hero can still carry a `technical_expertise_about`
section whose own traits (`technical`, `information_dense`) are the ones the
Design Genome's own data already scores as antagonistic to `cinematic`
(`TRAIT_PAIR_AFFINITY[frozenset({"cinematic","information_dense"})] == -0.24`
in `component_relationships.py`). That penalty is real and already existed;
it was just never read outside of `DesignGenome`'s own generation-time
scoring, and generation-time scoring only ever compares *adjacent* sections
in the page, which dilutes a hero-vs-distant-section clash to nearly nothing
(measured: 0.96 for the full adjacent sequence on site-11, vs. 0.50 for the
direct hero/about pair -- see the V0.2.1 doc for the numbers).

This module adds no new compatibility data. It re-reads the same
`compatible_directions` / `compatible_archetypes` / `incompatible_components`
/ trait metadata design_genome already maintains, from a different angle:
against the *final resolved* plan (post hero-recomposition, post
about-reduction), and hero-anchored (not adjacency-only), so a clash between
non-adjacent sections is not silently averaged away. This is a report, not a
gate that redesigns anything -- see rule 26/27 of the brief: detection is
the priority for this pass, not automatic repair.
"""

from __future__ import annotations

from dataclasses import dataclass

from generator.design_genome.archetypes import ARCHETYPES
from generator.design_genome.component_relationships import component_pair_affinity, sequence_affinity
from generator.design_genome.data.components import ALL_COMPONENTS
from generator.design_genome.models import ComponentDefinition


_TENSION_THRESHOLD = 0.55
_INCOMPATIBLE_THRESHOLD = 0.35


@dataclass(frozen=True)
class SectionCoherence:
    section: str
    component_id: str
    family: str
    status: str  # "compatible" | "neutral" | "tension" | "incompatible"
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CoherenceDimension:
    score: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoherenceReport:
    fixture_id: str
    site_archetype: str
    art_direction: str
    page_silhouette: str
    sections: tuple[SectionCoherence, ...]
    direction_component_alignment: CoherenceDimension
    hero_anchor_consistency: CoherenceDimension
    sequence_transition_consistency: CoherenceDimension
    visual_weight_progression: CoherenceDimension
    layout_pattern_variety: CoherenceDimension
    media_language_consistency: CoherenceDimension
    commercial_flow_consistency: CoherenceDimension
    overall_score: float
    overall_status: str  # "coherent" | "warning" | "tension" | "incompatible"
    overall_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        dims = (
            "direction_component_alignment", "hero_anchor_consistency",
            "sequence_transition_consistency", "visual_weight_progression",
            "layout_pattern_variety", "media_language_consistency",
            "commercial_flow_consistency",
        )
        return {
            "fixture_id": self.fixture_id,
            "site_archetype": self.site_archetype,
            "art_direction": self.art_direction,
            "page_silhouette": self.page_silhouette,
            "sections": [
                {"section": s.section, "component_id": s.component_id, "family": s.family,
                 "status": s.status, "reasons": list(s.reasons)}
                for s in self.sections
            ],
            **{name: {"score": getattr(self, name).score, "reasons": list(getattr(self, name).reasons)} for name in dims},
            "overall_score": self.overall_score,
            "overall_status": self.overall_status,
            "overall_reasons": list(self.overall_reasons),
        }


def _direction_status(component: ComponentDefinition, art_direction: str, archetype_id: str) -> tuple[str, tuple[str, ...]]:
    """Mirrors compatibility.py's own soft direction/archetype scoring
    (+0.16 direction match, +0.18 archetype match, -0.05/-0.06 miss when the
    component *does* declare preferences) -- not duplicated logic, the same
    read of the same two fields, applied post-hoc to an already-resolved
    component instead of during candidate scoring.
    """
    direction_hit = art_direction in component.compatible_directions
    archetype_hit = archetype_id in component.compatible_archetypes
    if direction_hit or archetype_hit:
        reasons = []
        if direction_hit:
            reasons.append(f"declares_compatible_direction:{art_direction}")
        if archetype_hit:
            reasons.append(f"declares_compatible_archetype:{archetype_id}")
        return "compatible", tuple(reasons)
    if not component.compatible_directions and not component.compatible_archetypes:
        return "neutral", ("no_declared_direction_or_archetype_preference",)
    return "tension", (
        f"declares_other_directions:{','.join(sorted(component.compatible_directions)) or 'none'}",
        f"declares_other_archetypes:{','.join(sorted(component.compatible_archetypes)) or 'none'}",
    )


def _classify(score: float, hard_failure: bool) -> str:
    if hard_failure:
        return "incompatible"
    if score < _INCOMPATIBLE_THRESHOLD:
        return "incompatible"
    if score < _TENSION_THRESHOLD:
        return "tension"
    return "compatible"


def build_coherence_report(
    fixture_id: str,
    site_archetype: str,
    art_direction: str,
    page_silhouette: str,
    resolved_components: tuple[tuple[str, ComponentDefinition], ...],
) -> CoherenceReport:
    """`resolved_components` is ``((section_name, component), ...)`` in
    render order, already post-recomposition/post-reduction -- i.e. exactly
    what will render, not the raw SiteDNA (rule 25).
    """
    archetype = ARCHETYPES.get(site_archetype)
    archetype_traits = archetype.traits if archetype else frozenset()
    components = tuple(component for _, component in resolved_components)

    # --- per-section direction/archetype alignment ---
    section_results: list[SectionCoherence] = []
    direction_scores = []
    for section_name, component in resolved_components:
        status, reasons = _direction_status(component, art_direction, site_archetype)
        section_results.append(SectionCoherence(section_name, component.id, component.family_id, status, reasons))
        direction_scores.append({"compatible": 1.0, "neutral": 0.85, "tension": 0.55}[status])
    direction_alignment = CoherenceDimension(
        round(sum(direction_scores) / len(direction_scores), 3) if direction_scores else 1.0,
        tuple(f"{s.section}:{s.status}" for s in section_results if s.status == "tension"),
    )

    # --- hero-anchored consistency: hero vs. EVERY other section, not just
    # its immediate neighbour. This is the check that actually catches
    # site-11 (see module docstring). ---
    hero_component = components[0] if resolved_components and resolved_components[0][0] == "hero" else None
    hero_reasons: list[str] = []
    worst_pair_score = 1.0
    hard_failure_seen = False
    if hero_component is not None:
        for section_name, component in resolved_components[1:]:
            result = component_pair_affinity(hero_component, component, archetype_traits)
            if result.hard_failure:
                hard_failure_seen = True
            if result.score < worst_pair_score:
                worst_pair_score = result.score
            if result.score < _TENSION_THRESHOLD or result.hard_failure:
                hero_reasons.append(
                    f"hero({hero_component.id}) vs {section_name}({component.id}): "
                    f"score={result.score} reasons={','.join(result.reasons)}"
                )
    hero_anchor = CoherenceDimension(
        round(worst_pair_score, 3) if hero_component is not None else 1.0,
        tuple(hero_reasons),
    )
    # Section-level status upgrade: a section that is individually "neutral"
    # against the direction (no stated preference either way) can still be
    # the specific one clashing with the hero -- reflect that instead of
    # silently keeping it "neutral".
    if hero_reasons:
        clashing_ids = {reason.split(" vs ")[1].split("(")[1].rstrip(")") for reason in hero_reasons}
        section_results = tuple(
            SectionCoherence(s.section, s.component_id, s.family, "tension" if s.component_id in clashing_ids and s.status != "incompatible" else s.status, s.reasons)
            for s in section_results
        )
    else:
        section_results = tuple(section_results)

    # --- sequence (adjacency) transition consistency -- reuses the existing
    # Design Genome pairwise/sequence scoring wholesale (rule 24). ---
    seq = sequence_affinity(components, archetype_traits)
    sequence_dim = CoherenceDimension(seq.score, seq.reasons)
    if seq.hard_failure:
        hard_failure_seen = True

    # --- visual weight progression: repeated runs of heavy sections back to
    # back read as a real "everything shouts" defect, not diversity. ---
    weight_reasons = []
    heavy_run = 0
    for component in components:
        if component.visual_weight >= 4:
            heavy_run += 1
            if heavy_run >= 3:
                weight_reasons.append(f"{heavy_run} consecutive heavy (visual_weight>=4) sections up to {component.id}")
        else:
            heavy_run = 0
    weight_dim = CoherenceDimension(max(0.5, 1.0 - 0.15 * len(weight_reasons)), tuple(weight_reasons))

    # --- layout pattern variety: not a beauty score, a repetition count. ---
    patterns = [c.blueprint_spec.layout_pattern for c in components]
    repeats = len(patterns) - len(set(patterns))
    pattern_dim = CoherenceDimension(
        max(0.4, 1.0 - repeats * 0.15),
        (f"{repeats} section(s) reuse an already-used layout_pattern",) if repeats else (),
    )

    # --- media language consistency: does provenance stay legible, or does
    # the page mix "artisan project" evidence with generic stock ambiance in
    # a way that would misrepresent one as the other. This mirrors the
    # existing truth-safety tests (stock cannot fill artisan_project) rather
    # than inventing a new rule -- it just reports the mix. ---
    media_dependent = [c for c in components if c.image_dependency >= 0.5]
    media_reasons = []
    if len(media_dependent) >= 2:
        weights = {c.visual_weight for c in media_dependent}
        if len(weights) == 1 and next(iter(weights)) >= 4:
            media_reasons.append("multiple high-visual-weight, media-dependent sections compete for the same attention")
    media_dim = CoherenceDimension(1.0 if not media_reasons else 0.75, tuple(media_reasons))

    # --- commercial flow: does a conversion-led archetype actually end with
    # an action-oriented component, using the archetype's own declared
    # conversion_intensity rather than a hardcoded threshold. ---
    flow_reasons = []
    if archetype and archetype.conversion_intensity >= 0.7:
        last_two = components[-2:] if len(components) >= 2 else components
        if not any(c.category in {"cta", "contact"} or "conversion_led" in c.traits for c in last_two):
            flow_reasons.append(
                f"archetype conversion_intensity={archetype.conversion_intensity} but the page does not close on a conversion-led section"
            )
    flow_dim = CoherenceDimension(1.0 if not flow_reasons else 0.7, tuple(flow_reasons))

    # hero_anchor_consistency, sequence and direction alignment are weighted
    # more heavily: they are the dimensions that actually encode "does this
    # read as one visual language" (rule 17). A flat unweighted average let
    # a genuinely low hero_anchor_consistency (a real, hero-vs-distant-
    # section clash) get diluted into a falsely comfortable overall score by
    # several supplementary dimensions that are near-1.0 on almost any page.
    weighted = (
        (direction_alignment, 1.0), (hero_anchor, 1.5), (sequence_dim, 1.0),
        (weight_dim, 0.5), (pattern_dim, 0.5), (media_dim, 0.5), (flow_dim, 0.5),
    )
    overall = round(sum(d.score * w for d, w in weighted) / sum(w for _, w in weighted), 3)
    worst = min(d.score for d, _ in weighted)
    # The overall label reacts to the worst dimension too, not only the
    # average -- one badly-clashing pair should not be hidden by five fine
    # ones (rule 41: "si les 12 sont tous exactement 1.0 partout, considère
    # cela comme suspect").
    if hard_failure_seen or overall < _INCOMPATIBLE_THRESHOLD:
        overall_status = "incompatible"
    elif overall < _TENSION_THRESHOLD or worst < 0.3:
        overall_status = "tension"
    elif overall < 0.85 or worst < 0.5:
        overall_status = "warning"
    else:
        overall_status = "coherent"
    dims = tuple(d for d, _ in weighted)
    overall_reasons = tuple(reason for dim in dims for reason in dim.reasons)

    return CoherenceReport(
        fixture_id=fixture_id,
        site_archetype=site_archetype,
        art_direction=art_direction,
        page_silhouette=page_silhouette,
        sections=section_results,
        direction_component_alignment=direction_alignment,
        hero_anchor_consistency=hero_anchor,
        sequence_transition_consistency=sequence_dim,
        visual_weight_progression=weight_dim,
        layout_pattern_variety=pattern_dim,
        media_language_consistency=media_dim,
        commercial_flow_consistency=flow_dim,
        overall_score=overall,
        overall_status=overall_status,
        overall_reasons=overall_reasons,
    )
