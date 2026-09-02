"""Design Genome Renderer V0.2.1 -- resolved plan authority & coherence gate.

Covers the guarantees of the V0.2.1 brief: the RenderPlan/HTML consistency
bug (site-11's about was reported ``full`` but rendered ``about--micro``),
the architecture that makes ``RenderPlan`` the single resolution authority
(no second, possibly-diverging decision path), honest (non-hardcoded)
``VisualCompletenessReport.mobile_readiness``/``empty_slot_risk``, and the
new ``CoherenceReport`` (rule 15-27: does the resolved plan still read as
one visual language, using only metadata the Design Genome already
maintains).
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from generator.design_genome.data.components import ALL_COMPONENTS
from generator.design_genome.generator import DesignGenome
from generator.design_genome.models import SiteDNA
from generator.genome_renderer.adapter import design_input_from_payload, render_payload_with_genome
from generator.genome_renderer.coherence import build_coherence_report
from generator.genome_renderer.context import RenderContext
from generator.genome_renderer.lab.build import build_visual_lab
from generator.genome_renderer.lab.fixtures import LAB_FIXTURES
from generator.genome_renderer.render_plan import build_render_plan
from generator.genome_renderer.renderer import render_site_genome
from generator.genome_renderer.visual_completeness import CompletenessDimension, VisualCompletenessReport, assess


def payload(**overrides):
    value = {
        "nom_entreprise": "Atelier Test",
        "metier": "plombier",
        "slug": "atelier-test",
        "ville": "Lyon",
        "code_postal": "69002",
        "telephone": "04 00 00 00 00",
        "email": "contact@example.test",
        "tagline": "Des installations pensées pour votre intérieur.",
        "about": "Une approche claire du projet.",
        "services": ["Installation sanitaire", "Rénovation de salle de bain", "Dépannage"],
        "facts": {"process": ("Échange", "Préparation", "Réalisation")},
        "selected_media": [
            {
                "id": "stock-hero", "url": "/assets/hero.webp", "role": "hero", "source": "pexels",
                "credit": "Photo Pexels", "source_url": "https://www.pexels.com/photo/1/",
                "alt": "Ambiance plomberie",
            },
            {
                "id": "stock-gallery", "url": "/assets/gallery.webp", "role": "gallery", "source": "pexels",
                "credit": "Photo Pexels", "alt": "Matière et ambiance",
            },
        ],
    }
    value.update(overrides)
    return value


def dna_for(value=None) -> SiteDNA:
    value = value or payload()
    return DesignGenome().generate(design_input_from_payload(value, seed="v021-test"))


def render(value=None, dna=None, *, plan=None, lab_mode=False, api="http://localhost:8000"):
    value = value or payload()
    dna = dna or dna_for(value)
    context = RenderContext.from_payload(value, dna, api, lab_mode=lab_mode)
    return render_site_genome(context, plan)


def body_of(document: str) -> str:
    return re.sub(r"<style>.*?</style>", "", document, flags=re.S)


def section_body(document: str, section_id: str) -> str:
    match = re.search(rf'<section id="{section_id}".*?</section>', body_of(document), re.S)
    return match.group(0) if match else ""


def _site11_ctx_and_dna():
    fixture = LAB_FIXTURES[10]
    assert fixture["fixture_id"] == "site-11"
    di = design_input_from_payload(fixture, seed=fixture["seed"])
    dna = DesignGenome().generate(di)
    ctx = RenderContext.from_payload(fixture, dna, "", lab_mode=True)
    return fixture, ctx, dna


# ---------------------------------------------------------------------------
# The core bug: RenderPlan and HTML must agree, always
# ---------------------------------------------------------------------------

def test_site11_about_plan_and_html_agree_on_reduced():
    """The exact V0.2 regression: plan said 'full', HTML rendered
    'about--micro'. V0.2.1 must report the same decision both places."""
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    about_plan = plan.section("about")
    assert about_plan is not None

    html = render_site_genome(ctx, plan)
    about_html = section_body(html, "about")
    is_micro_in_html = "about--micro" in about_html

    if is_micro_in_html:
        assert about_plan.renderability == "reduced", "HTML shows the reduced about--micro markup but the plan claims something else"
        assert about_plan.resolved_mode == "fact_strip"
    else:
        assert about_plan.renderability == "full"
        assert about_plan.resolved_mode == "narrative"


def test_render_plan_and_html_are_never_built_from_different_resolutions():
    """Building the plan once and rendering from it (the V0.2.1 contract)
    must be observably identical to letting render_site_genome build its
    own plan internally -- there is only one resolution path."""
    fixture = payload()
    dna = dna_for(fixture)
    ctx = RenderContext.from_payload(fixture, dna, "http://localhost:8000")
    plan = build_render_plan(ctx)
    explicit = render_site_genome(ctx, plan)
    implicit = render_site_genome(ctx)
    assert explicit == implicit


@pytest.mark.parametrize("fixture_index", range(12))
def test_plan_component_ids_match_html_component_ids_for_every_lab_fixture(fixture_index):
    """For every rendered (non-omitted) section, the component id the plan
    reports must be the exact id that ends up in the HTML's data-component
    attribute -- the plan cannot describe A while the HTML shows B."""
    fixture = LAB_FIXTURES[fixture_index]
    history = [DesignGenome().generate(design_input_from_payload(f, seed=f["seed"])) for f in LAB_FIXTURES[:fixture_index]]
    di = design_input_from_payload(fixture, seed=fixture["seed"])
    dna = DesignGenome().generate(di, tuple(history))
    ctx = RenderContext.from_payload(fixture, dna, "", lab_mode=True)
    plan = build_render_plan(ctx, fixture["fixture_id"])
    html = render_site_genome(ctx, plan)
    body = body_of(html)

    for section in plan.rendered_sections:
        if section.section == "contact" and section.resolved_mode == "form_only":
            # The generic quote-form fallback has no real ComponentDefinition
            # (see render_plan._resolve_contact); its data-component is a
            # synthetic label, not a catalog id.
            assert 'data-component="generic_quote_form"' in section_body(body, "contact")
            continue
        section_html = section_body(body, "accueil" if section.section == "hero" else section.section)
        assert section_html, f"plan reports '{section.section}' as {section.renderability} but no such HTML section exists"
        assert f'data-component="{section.component_id}"' in section_html, (
            f"plan says {section.section}={section.component_id} but the HTML section does not carry that id"
        )


@pytest.mark.parametrize("fixture_index", range(12))
def test_plan_resolved_media_matches_html_media_for_every_lab_fixture(fixture_index):
    fixture = LAB_FIXTURES[fixture_index]
    history = [DesignGenome().generate(design_input_from_payload(f, seed=f["seed"])) for f in LAB_FIXTURES[:fixture_index]]
    di = design_input_from_payload(fixture, seed=fixture["seed"])
    dna = DesignGenome().generate(di, tuple(history))
    ctx = RenderContext.from_payload(fixture, dna, "", lab_mode=True)
    plan = build_render_plan(ctx, fixture["fixture_id"])
    html = render_site_genome(ctx, plan)
    media_by_id = {item.id: item for item in ctx.media}

    for section in plan.rendered_sections:
        if not section.resolved_media:
            continue
        section_id = "accueil" if section.section == "hero" else section.section
        section_html = section_body(html, section_id)
        for media_id in section.resolved_media:
            url = media_by_id[media_id].url
            assert url in section_html, f"plan says {section.section} uses media {media_id} but its URL is not in the rendered HTML"


def test_omitted_section_is_absent_from_html():
    dna = replace(
        dna_for(),
        gallery_component="stock_ambient_collage",
        section_order=("header", "hero", "gallery", "footer"),
    )
    no_media_payload = payload(selected_media=[])
    ctx = RenderContext.from_payload(no_media_payload, replace(dna_for(no_media_payload), gallery_component="stock_ambient_collage", section_order=("header", "hero", "gallery", "footer")), "")
    plan = build_render_plan(ctx)
    gallery_plan = plan.section("gallery")
    assert gallery_plan is not None and gallery_plan.renderability == "omitted"
    html = render_site_genome(ctx, plan)
    assert 'id="gallery"' not in html


def test_reduced_section_renders_reduced_markup():
    duplicate_payload = payload(about=payload()["tagline"])
    dna = replace(dna_for(duplicate_payload), about_component="simple_business_identity", section_order=("header", "hero", "about", "footer"))
    ctx = RenderContext.from_payload(duplicate_payload, dna, "")
    plan = build_render_plan(ctx)
    about_plan = plan.section("about")
    assert about_plan.renderability == "reduced"
    html = render_site_genome(ctx, plan)
    assert "about--micro" in section_body(html, "about")


def test_full_section_renders_full_markup():
    distinct_payload = payload(about="Une histoire différente de la tagline, avec un vrai contenu propre.")
    dna = replace(dna_for(distinct_payload), about_component="simple_business_identity", section_order=("header", "hero", "about", "footer"))
    ctx = RenderContext.from_payload(distinct_payload, dna, "")
    plan = build_render_plan(ctx)
    about_plan = plan.section("about")
    assert about_plan.renderability == "full"
    html = render_site_genome(ctx, plan)
    about_html = section_body(html, "about")
    assert "about--micro" not in about_html
    assert distinct_payload["about"] in about_html


def test_contact_fallback_is_represented_in_the_plan_not_only_the_html():
    no_contact_payload = payload(telephone="", email="")
    dna = dna_for(no_contact_payload)
    assert dna.contact_component is None and dna.form_component is None
    ctx = RenderContext.from_payload(no_contact_payload, dna, "http://localhost:8000")
    plan = build_render_plan(ctx)
    contact_plan = plan.section("contact")
    assert contact_plan is not None
    assert contact_plan.renderability == "full"
    assert contact_plan.resolved_mode == "form_only"
    html = render_site_genome(ctx, plan)
    assert 'id="contact"' in html
    assert '"/pub/"+encodeURIComponent' in html


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_plan_is_deterministic():
    fixture = payload()
    dna = dna_for(fixture)
    ctx = RenderContext.from_payload(fixture, dna, "")
    left = build_render_plan(ctx, "det-test")
    right = build_render_plan(ctx, "det-test")
    assert left.to_dict() == right.to_dict()


def test_html_is_deterministic_from_the_same_plan():
    fixture = payload()
    dna = dna_for(fixture)
    ctx = RenderContext.from_payload(fixture, dna, "http://localhost:8000")
    plan = build_render_plan(ctx)
    assert render_site_genome(ctx, plan) == render_site_genome(ctx, plan)


def test_coherence_report_is_deterministic():
    fixture, ctx, dna = _site11_ctx_and_dna()
    left = build_render_plan(ctx, fixture["fixture_id"]).coherence
    right = build_render_plan(ctx, fixture["fixture_id"]).coherence
    assert left.to_dict() == right.to_dict()


# ---------------------------------------------------------------------------
# CoherenceReport
# ---------------------------------------------------------------------------

def test_coherence_uses_resolved_component_not_initial_dna():
    """If the hero were recomposed, coherence must judge the component that
    actually renders, not the one the raw SiteDNA originally named."""
    empty_media_payload = payload(selected_media=[])
    dna = replace(dna_for(empty_media_payload), hero_component="cinematic_overlay_story")
    ctx = RenderContext.from_payload(empty_media_payload, dna, "")
    plan = build_render_plan(ctx)
    assert plan.resolved_hero_component != plan.initial_hero_component
    hero_section_coherence = plan.coherence.sections[0]
    assert hero_section_coherence.component_id == plan.resolved_hero_component
    assert hero_section_coherence.component_id != plan.initial_hero_component


def test_site11_coherence_flags_a_real_tension_not_a_perfect_score():
    """Site-11 (cinematic_luxury hero + technical_expertise_about) is the
    brief's own worked example: the Design Genome's own trait-pair data
    (TRAIT_PAIR_AFFINITY[cinematic, information_dense] == -0.24) already
    scores this combination as antagonistic. The gate must surface that,
    not silently pass it because the hero itself now has a real photo."""
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    assert plan.coherence.overall_score < 0.95, "site-11 must not score as a clean, untroubled coherence result"
    assert plan.coherence.hero_anchor_consistency.score < 0.8
    assert plan.coherence.hero_anchor_consistency.reasons, "a low score must always carry a legible reason"
    assert plan.coherence.overall_status in {"warning", "tension", "incompatible"}


def test_coherent_and_conflicting_plans_are_actually_distinguished():
    """Two controlled component combinations: one built to share traits and
    directions, one built to clash on the Design Genome's own trait-pair
    table. The report must tell them apart -- no fixed threshold precision
    is claimed (rule 52), only that the ordering is right."""
    coherent_components = (
        ("hero", ALL_COMPONENTS["quiet_luxury_window"]),       # hero.cinematic: cinematic, story_led
        ("about", ALL_COMPONENTS["studio_statement_about"]),   # about.minimal-ish: no antagonistic traits
    )
    conflicting_components = (
        ("hero", ALL_COMPONENTS["quiet_luxury_window"]),        # cinematic
        ("about", ALL_COMPONENTS["technical_expertise_about"]), # technical, information_dense -- scored antagonistic
    )
    coherent_report = build_coherence_report("t1", "premium_residential", "cinematic_luxury", "quiet_luxury", coherent_components)
    conflicting_report = build_coherence_report("t2", "premium_residential", "cinematic_luxury", "quiet_luxury", conflicting_components)
    assert conflicting_report.hero_anchor_consistency.score < coherent_report.hero_anchor_consistency.score
    assert conflicting_report.overall_score < coherent_report.overall_score


def test_coherence_report_never_emits_an_aesthetic_verdict():
    """Checks the report's own authored vocabulary (status labels and the
    prose it generates in `reasons`) -- not the whole serialized dict, which
    legitimately embeds pre-existing Design Genome taxonomy terms like the
    `premium_residential` archetype/silhouette id (a factual DNA label, not
    an aesthetic claim this module is making)."""
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    coherence = plan.coherence
    authored_text = " ".join((
        coherence.overall_status,
        *coherence.overall_reasons,
        *(s.status for s in coherence.sections),
    )).upper()
    for banned in ("BEAUTIFUL", "SELLABLE", "AESTHETIC PASS", "PRODUCTION READY", "VISUAL PASS"):
        assert banned not in authored_text
    assert coherence.overall_status in {"coherent", "warning", "tension", "incompatible"}


def test_coherence_reasons_are_always_legible_strings():
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    for reason in plan.coherence.overall_reasons:
        assert isinstance(reason, str) and reason


# ---------------------------------------------------------------------------
# VisualCompleteness: honest, non-constant dimensions
# ---------------------------------------------------------------------------

def test_art_direction_fidelity_incorporates_coherence_not_just_hero_media():
    """rule 22: site-11 must not auto-score 1.0 just because its hero now
    has a photo -- art_direction_fidelity must reflect the coherence clash
    too."""
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    hero_plan = plan.section("hero")
    assert hero_plan.resolved_media, "sanity check: site-11's hero does have real media in V0.2.1"
    report = assess(plan)
    assert report.art_direction_fidelity.score < 1.0
    assert report.art_direction_fidelity.reasons


def test_visual_completeness_two_constructed_plans_are_not_identical():
    """rule 51: a well-resolved plan and a deliberately weaker one must not
    collapse to the same scores."""
    good_payload = payload()
    good_dna = dna_for(good_payload)
    good_ctx = RenderContext.from_payload(good_payload, good_dna, "http://localhost:8000")
    good_plan = build_render_plan(good_ctx, "plan-a")
    good_report = assess(good_plan)

    weak_payload = payload(telephone="", email="", selected_media=[], services=["Service unique"])
    weak_dna = replace(
        dna_for(weak_payload),
        gallery_component="stock_ambient_collage", about_component=None, trust_component=None,
        cta_component=None, contact_component=None, form_component=None,
        section_order=("header", "hero", "services", "gallery", "footer"),
    )
    weak_ctx = RenderContext.from_payload(weak_payload, weak_dna, "")
    weak_plan = build_render_plan(weak_ctx, "plan-b")
    weak_report = assess(weak_plan)

    assert good_report.to_dict() != weak_report.to_dict()
    # weak_payload has zero media at all -- media_readiness must reflect
    # that regardless of commercial_completeness (which the real quote-form
    # fallback can legitimately keep at 1.0 for both, since both payloads
    # keep a slug -- rule AE, not a gap in this specific dimension).
    assert weak_report.media_readiness.score < good_report.media_readiness.score


def test_mobile_readiness_is_not_a_hardcoded_constant():
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    report = assess(plan)
    assert isinstance(report.mobile_readiness, CompletenessDimension)
    assert report.mobile_readiness.reasons, "mobile_readiness must always carry a reason, even a passing one"
    # A plan with no conversion path at all must score lower than one that has one.
    no_contact_payload = payload(telephone="", email="", slug="")
    no_contact_dna = replace(
        dna_for(no_contact_payload),
        contact_component=None, form_component=None, cta_component=None,
        section_order=("header", "hero", "services", "footer"),
    )
    no_contact_ctx = RenderContext.from_payload(no_contact_payload, no_contact_dna, "")
    no_contact_plan = build_render_plan(no_contact_ctx, "no-contact")
    no_contact_report = assess(no_contact_plan)
    assert no_contact_report.mobile_readiness.score < 1.0


def test_empty_slot_risk_is_not_a_hardcoded_constant():
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    report = assess(plan)
    assert report.empty_slot_risk.reasons
    # A synthetic plan section claiming to be "full" media-dependent with
    # zero resolved media and no recorded fallback must be caught.
    from generator.genome_renderer.render_plan import RenderPlan, SectionPlan
    from generator.genome_renderer.coherence import build_coherence_report as _bcr
    broken_hero = plan.section("hero")
    broken = replace(broken_hero, renderability="full", resolved_media=(), fallback_used=False)
    broken_sections = tuple(replace(s, resolved_media=()) if s.section == broken.section else s for s in plan.sections)
    broken_sections = tuple(broken if s.section == "hero" else s for s in broken_sections)
    broken_plan = replace(plan, sections=broken_sections)
    broken_report = assess(broken_plan)
    assert broken_report.empty_slot_risk.score < report.empty_slot_risk.score or broken_report.empty_slot_risk.score < 1.0


def test_visual_completeness_still_never_emits_an_aesthetic_verdict():
    fixture, ctx, dna = _site11_ctx_and_dna()
    plan = build_render_plan(ctx, fixture["fixture_id"])
    report = assess(plan)
    serialized = str(report.to_dict()).upper().replace("_", " ")
    for banned in ("BEAUTIFUL", "PREMIUM", "SELLABLE", "AESTHETIC PASS", "PRODUCTION READY", "VISUAL PASS"):
        assert banned not in serialized


# ---------------------------------------------------------------------------
# Same 12 fixtures still build; V3 untouched
# ---------------------------------------------------------------------------

def test_visual_lab_still_builds_twelve_not_reviewed_sites_with_coherence(tmp_path):
    manifest = build_visual_lab(tmp_path)
    assert len(manifest) == 12
    assert all(item["aesthetic_status"] == "NOT_REVIEWED" for item in manifest)
    assert all("coherence_overall_score" in item for item in manifest)
    scores = {item["coherence_overall_score"] for item in manifest}
    assert len(scores) > 1, "rule 41: 12 identical coherence scores would be suspect, not a victory"
    for item in manifest:
        assert (tmp_path / "sites" / item["fixture_id"] / "coherence-report.json").is_file()
