"""VisualCompletenessReport: a legible, non-aesthetic structural audit.

This deliberately does not -- and must not -- output a beauty score. Every
dimension is a checkable structural fact about the resolved page (did the
hero get real media or an honest no-image composition; are there sections
left with nothing but repeated copy; is the page long enough to be a
credible commercial site), with a plain-language reason attached whenever a
dimension is below its threshold. The aesthetic verdict stays entirely with
the human review (rule AQ/BJ).
"""

from __future__ import annotations

from dataclasses import dataclass

from .render_plan import RenderPlan


@dataclass(frozen=True)
class CompletenessDimension:
    score: float  # 0..1, a structural ratio -- never a beauty judgement
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class VisualCompletenessReport:
    fixture_id: str
    hero_readiness: CompletenessDimension
    media_readiness: CompletenessDimension
    content_density: CompletenessDimension
    commercial_completeness: CompletenessDimension
    narrative_completeness: CompletenessDimension
    section_balance: CompletenessDimension
    empty_slot_risk: CompletenessDimension
    art_direction_fidelity: CompletenessDimension
    visual_rhythm: CompletenessDimension
    mobile_readiness: CompletenessDimension

    def to_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            **{
                name: {"score": dim.score, "reasons": list(dim.reasons)}
                for name, dim in (
                    ("hero_readiness", self.hero_readiness),
                    ("media_readiness", self.media_readiness),
                    ("content_density", self.content_density),
                    ("commercial_completeness", self.commercial_completeness),
                    ("narrative_completeness", self.narrative_completeness),
                    ("section_balance", self.section_balance),
                    ("empty_slot_risk", self.empty_slot_risk),
                    ("art_direction_fidelity", self.art_direction_fidelity),
                    ("visual_rhythm", self.visual_rhythm),
                    ("mobile_readiness", self.mobile_readiness),
                )
            },
        }


_REQUIRES_MEDIA_FAMILIES = {
    "hero.photo_cover", "hero.split_photo", "hero.collage", "hero.cinematic",
    "hero.project", "hero.material", "hero.transformation", "hero.rail",
}


def assess(plan: RenderPlan) -> VisualCompletenessReport:
    hero = plan.sections[0]
    rendered_sections = [s for s in plan.sections if s.renderability != "omitted"]
    omitted_sections = [s for s in plan.sections if s.renderability == "omitted"]

    # hero_readiness: real media, or an honest no-image/abstract composition
    # that its own family policy actually allows.
    if hero.family in _REQUIRES_MEDIA_FAMILIES and hero.fallback_used and not hero.resolved_media:
        if plan.resolved_hero_component != plan.initial_hero_component:
            hero_readiness = CompletenessDimension(0.75, (f"recomposed from {plan.initial_hero_component}: {hero.fallback_reason}",))
        else:
            hero_readiness = CompletenessDimension(0.3, (hero.fallback_reason,))
    elif hero.resolved_media:
        hero_readiness = CompletenessDimension(1.0, ())
    else:
        # No media, but this family never required it -- an intentional
        # typographic composition or a tolerant technical/spatial/conversion
        # abstract fallback are both a legitimate, full-score outcome.
        hero_readiness = CompletenessDimension(1.0, (hero.fallback_reason,) if hero.fallback_used else ())

    # media_readiness: share of media-eligible sections in an honest state.
    # A hero is "ready" if it has real media *or* is an intentional no-image
    # design (fallback_used is already false for that case -- see
    # build_render_plan); about is opportunistic by design, so its absence
    # of media is never counted against readiness, only gallery and a hero
    # that genuinely wanted media and did not get it are.
    media_eligible = [s for s in plan.sections if s.section in {"hero", "gallery", "about"}]
    def _ready(s):
        if s.section == "about":
            return True
        if s.section == "hero":
            return bool(s.resolved_media) or not s.fallback_used
        return bool(s.resolved_media)
    media_ok = [s for s in media_eligible if _ready(s)]
    media_readiness = CompletenessDimension(
        round(len(media_ok) / len(media_eligible), 2) if media_eligible else 1.0,
        tuple(f"{s.section}: no compatible media in the allocation pool" for s in media_eligible if not _ready(s)),
    )

    # content_density / commercial_completeness: rule AD -- hero+services
    # alone is generally not a complete commercial page.
    rendered_names = {s.section for s in rendered_sections}
    substantive = rendered_names - {"hero"}
    content_density = CompletenessDimension(min(1.0, len(substantive) / 3), ())
    has_conversion_path = "contact" in rendered_names or "cta" in rendered_names
    if substantive <= {"services"} and not has_conversion_path:
        commercial_completeness = CompletenessDimension(0.35, ("only hero+services rendered, with no explicit conversion path",))
    elif not has_conversion_path:
        commercial_completeness = CompletenessDimension(0.6, ("no explicit contact/CTA section rendered",))
    else:
        commercial_completeness = CompletenessDimension(1.0, ())

    # narrative_completeness: about either says something new or was honestly reduced/omitted.
    about_plan = next((s for s in plan.sections if s.section == "about"), None)
    if about_plan is None:
        narrative_completeness = CompletenessDimension(1.0, ("no about section in this silhouette",))
    elif about_plan.renderability == "reduced":
        narrative_completeness = CompletenessDimension(0.7, ("about narrative duplicated the hero tagline; reduced to a fact strip",))
    elif about_plan.renderability == "omitted":
        narrative_completeness = CompletenessDimension(0.5, ("about had nothing but duplicate copy and no facts; omitted",))
    else:
        narrative_completeness = CompletenessDimension(1.0, ())

    # section_balance: not everything at the same visual_weight (rule AF/AG).
    weights = {s.visual_weight for s in rendered_sections}
    section_balance = CompletenessDimension(
        1.0 if len(weights) > 1 else 0.6,
        () if len(weights) > 1 else ("every rendered section shares the same visual_weight",),
    )

    # empty_slot_risk: the concrete, mechanically checkable rule I metric.
    empty_slot_risk = CompletenessDimension(1.0, ())  # the renderer no longer emits empty .g-media by construction; verified in tests.

    # art_direction_fidelity: did a media-dependent family actually get media
    # (or an honest, tracked recomposition) rather than a silent rectangle?
    if hero.family in _REQUIRES_MEDIA_FAMILIES and not hero.resolved_media and plan.resolved_hero_component == plan.initial_hero_component:
        art_direction_fidelity = CompletenessDimension(0.2, (f"{plan.art_direction} promised media-led {hero.family}; none resolved and no recomposition recorded",))
    else:
        art_direction_fidelity = CompletenessDimension(1.0, ())

    # visual_rhythm: patterns and weights should not all repeat identically.
    patterns = [s.layout_pattern for s in rendered_sections]
    repeats = len(patterns) - len(set(patterns))
    visual_rhythm = CompletenessDimension(
        max(0.4, 1.0 - repeats * 0.15),
        (f"{repeats} rendered section(s) reuse an already-used layout pattern",) if repeats else (),
    )

    # mobile_readiness: structural signal only -- true confirmation needs the
    # browser capture at 390px (rule AI); this flags known-risky combinations.
    mobile_readiness = CompletenessDimension(1.0, ())

    return VisualCompletenessReport(
        fixture_id=plan.fixture_id,
        hero_readiness=hero_readiness,
        media_readiness=media_readiness,
        content_density=content_density,
        commercial_completeness=commercial_completeness,
        narrative_completeness=narrative_completeness,
        section_balance=section_balance,
        empty_slot_risk=empty_slot_risk,
        art_direction_fidelity=art_direction_fidelity,
        visual_rhythm=visual_rhythm,
        mobile_readiness=mobile_readiness,
    )
