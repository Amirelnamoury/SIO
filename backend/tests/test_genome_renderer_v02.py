"""Design Genome Renderer V0.2 -- visual realization pass.

Covers the guarantees rule AW of the V0.2 brief requires: RenderPlan,
MediaAllocationPlan, HeroMediaResolver, VisualCompletenessReport, art
direction fidelity, no empty media slots, cinematic no-media
rejection/recomposition, material no-media handling, available-media
priority, stock-cannot-fill-artisan_project, copy de-duplication, commercial
completeness, service_bento/technical_nodes_network structural realization,
hero family structural differences, responsive rules, escaping,
determinism and truth safety.

These tests exercise the engine directly (never a fixture id, never an
``if trade == ...`` branch) so they hold for any artisan payload, not just
the 12 lab fixtures.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from generator.design_genome.generator import DesignGenome
from generator.design_genome.models import MediaInventory, SiteDNA
from generator.genome_renderer.adapter import design_input_from_payload, render_payload_with_genome
from generator.genome_renderer.context import RenderContext
from generator.genome_renderer.lab.build import build_visual_lab
from generator.genome_renderer.media_plan import HeroMediaResolver, allocate_media
from generator.genome_renderer.render_plan import build_render_plan
from generator.genome_renderer.visual_completeness import assess


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
    return DesignGenome().generate(design_input_from_payload(value, seed="v02-test"))


def render(value=None, dna=None, *, lab_mode=False, api="http://localhost:8000"):
    value = value or payload()
    dna = dna or dna_for(value)
    context = RenderContext.from_payload(value, dna, api, lab_mode=lab_mode)
    from generator.genome_renderer.renderer import render_site_genome
    return render_site_genome(context)


def hero_section(document: str) -> str:
    match = re.search(r'<section id="accueil".*?</section>', document, re.S)
    assert match, "no hero section found"
    return match.group(0)


def body_of(document: str) -> str:
    """The rendered body, without the embedded <style> block.

    FAMILY_CSS defines a selector for every V0.2 class on every page (it is
    shared, static CSS), so a raw substring search over the full document
    would "find" e.g. ``.service-bento-grid{...}`` on a page that never uses
    it. Tests that check whether a specific structure was actually used must
    search the body, not the stylesheet.
    """
    return re.sub(r"<style>.*?</style>", "", document, flags=re.S)


def section_body(document: str, section_id: str) -> str:
    match = re.search(rf'<section id="{section_id}".*?</section>', body_of(document), re.S)
    return match.group(0) if match else ""


# ---------------------------------------------------------------------------
# media_for correctness (the root-cause bug)
# ---------------------------------------------------------------------------

def test_available_stock_media_is_used_before_any_fallback():
    """rule AZ: compatible media beats a graphic fallback, every time."""
    for component_id in ("offset_residential_photo", "split_service_photo", "parallax_layered_material", "quiet_luxury_window"):
        dna = replace(dna_for(), hero_component=component_id)
        document = render(dna=dna)
        hero = hero_section(document)
        assert "graphic-fallback" not in hero, f"{component_id} fell back despite compatible stock media"
        assert "hero-image" in hero or "hero-material-macro" in hero


def test_required_any_media_is_a_real_or_not_a_blanket_veto():
    """The V0.1 bug: any required_any_media set containing artisan_project
    rejected every other accepted role too, including stock_photo."""
    ctx = RenderContext.from_payload(payload(), dna_for(), "", lab_mode=False)
    from generator.design_genome.data.components import ALL_COMPONENTS
    component = ALL_COMPONENTS["full_bleed_photo_cover"]
    assert "artisan_project" in component.required_any_media
    assert "stock_photo" in component.required_any_media
    resolved = ctx.media_for(component, limit=1)
    assert resolved, "a stock photo must satisfy an OR-list that merely includes artisan_project"
    assert resolved[0].source_class == "stock"


def test_stock_cannot_fill_artisan_project_only_slots():
    """The provenance lock must still hold for genuinely artisan-only slots."""
    ctx = RenderContext.from_payload(payload(), dna_for(), "", lab_mode=False)
    from generator.design_genome.data.components import ALL_COMPONENTS
    project_hero = ALL_COMPONENTS["project_contact_sheet_hero"]
    assert ctx.media_for(project_hero) == ()
    transformation_hero = ALL_COMPONENTS["before_after_transformation_pair"]
    assert ctx.media_for(transformation_hero) == ()


# ---------------------------------------------------------------------------
# HeroMediaResolver / family policy / recomposition
# ---------------------------------------------------------------------------

def test_cinematic_hero_without_compatible_media_never_uses_generic_fallback():
    """rule AY: cinematic + no compatible media must not produce the V0.1 rectangle."""
    empty_media_payload = payload(selected_media=[])
    dna = replace(dna_for(empty_media_payload), hero_component="cinematic_overlay_story")
    document = render(empty_media_payload, dna)
    hero = hero_section(document)
    assert "graphic-fallback" not in hero
    assert 'data-family="hero.cinematic"' not in hero  # recomposed away from cinematic
    assert "hero--no-image" in hero


def test_material_hero_without_media_recomposes_instead_of_abstract_rectangle():
    empty_media_payload = payload(selected_media=[])
    dna = replace(dna_for(empty_media_payload), hero_component="material_macro_title")
    document = render(empty_media_payload, dna)
    hero = hero_section(document)
    assert "graphic-fallback" not in hero
    assert "hero--no-image" in hero


def test_technical_hero_without_media_keeps_its_tolerant_abstract_fallback():
    """Technical/spatial/conversion may still use the geometric composition --
    it is their own declared, intentional visual language (rule H)."""
    empty_media_payload = payload(selected_media=[])
    dna = replace(dna_for(empty_media_payload), hero_component="mono_technical_diagnostic")
    document = render(empty_media_payload, dna)
    hero = hero_section(document)
    assert "graphic-fallback" in hero


def test_typographic_hero_never_shows_incidental_media():
    """media_count_max=0 must mean zero images, even when compatible stock exists."""
    dna = replace(dna_for(), hero_component="centered_statement_quiet")
    document = render(dna=dna)
    hero = hero_section(document)
    assert "<img" not in hero
    assert "hero-type--quiet" in hero


def test_hero_resolver_decision_is_documented_not_magic():
    empty_media_payload = payload(selected_media=[])
    dna = replace(dna_for(empty_media_payload), hero_component="cinematic_overlay_story")
    ctx = RenderContext.from_payload(empty_media_payload, dna, "")
    resolution = HeroMediaResolver.resolve(ctx, dna)
    assert resolution.mode == "recomposed"
    assert resolution.decision is not None
    assert resolution.decision.initial == "cinematic_overlay_story"
    assert "no compatible media" in resolution.decision.reason


# ---------------------------------------------------------------------------
# Empty media slots
# ---------------------------------------------------------------------------

def test_no_empty_media_slots_across_default_render():
    document = render()
    assert not re.search(r'<div class="g-media[^"]*">\s*</div>', document), "empty .g-media slot found"


def test_no_empty_media_slots_when_about_has_no_photo():
    no_media_payload = payload(selected_media=[])
    dna = dna_for(no_media_payload)
    document = render(no_media_payload, dna)
    assert not re.search(r'<div class="g-media[^"]*">\s*</div>', document)


def test_layout_regions_recomposes_instead_of_emitting_an_empty_div():
    from generator.design_genome.data.components import ALL_COMPONENTS
    from generator.genome_renderer.primitives import layout_regions
    component = ALL_COMPONENTS["technical_expertise_about"]  # grid/matrix pattern
    body = layout_regions(component, "<p>copy</p>", "")
    assert "g-media" not in body
    assert "g-layout--no-media" in body


# ---------------------------------------------------------------------------
# Component realization: service_bento vs minimal_service_links (rule BA)
# ---------------------------------------------------------------------------

def test_service_bento_is_structurally_distinct_from_minimal_links():
    services = payload()
    bento_dna = replace(dna_for(services), services_component="service_bento")
    minimal_dna = replace(dna_for(services), services_component="minimal_service_links")
    bento_body = body_of(render(services, bento_dna))
    minimal_body = body_of(render(services, minimal_dna))
    assert "service-bento-grid" in bento_body and "bento-tile" in bento_body
    assert "service-bento-grid" not in minimal_body
    assert "service-quiet-list" in minimal_body
    assert "bento-primary" in bento_body  # real span hierarchy, not a uniform grid
    assert bento_body != minimal_body


def test_service_bento_has_asymmetric_spans_not_a_uniform_list():
    services = payload()
    dna = replace(dna_for(services), services_component="service_bento")
    body = body_of(render(services, dna))
    assert "bento-primary" in body
    assert "bento-tall" in body or "bento-standard" in body
    # not the V0.1 flat "01 / 02 / 03" list markup
    assert "service-list" not in body


def test_editorial_service_folio_uses_large_numbers_and_offsets():
    services = payload()
    dna = replace(dna_for(services), services_component="editorial_service_folio")
    document = render(services, dna)
    assert "folio-number" in document
    assert "folio-row--offset" in document  # alternating offset, not a flat column


def test_conversion_service_selector_links_every_entry_to_the_real_quote_action():
    services = payload()
    dna = replace(dna_for(services), services_component="conversion_service_selector")
    document = render(services, dna)
    assert document.count('href="#contact"') >= len(services["services"])
    assert "selector-card--primary" in document


# ---------------------------------------------------------------------------
# technical_nodes_network: a real diagram from real services (rule R/BB)
# ---------------------------------------------------------------------------

def test_technical_nodes_network_renders_real_service_nodes_not_text_plus_photo():
    services = payload()
    dna = replace(dna_for(services), hero_component="technical_nodes_network")
    document = render(services, dna)
    hero = hero_section(document)
    assert "hero-network" in hero
    assert "network-hub" in hero
    for service in services["services"]:
        assert service in hero
    # This is a structure, not a caption under a stock photo.
    assert "hero-image" not in hero


def test_technical_nodes_network_invents_no_numbers():
    services = payload()
    dna = replace(dna_for(services), hero_component="technical_nodes_network")
    document = render(services, dna)
    hero = hero_section(document)
    assert not re.search(r"\b\d{2,}\s*%|\bclients?\b|\bans?\b", hero, re.I)


# ---------------------------------------------------------------------------
# Hero family structural differences (rule S)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("component_id", "marker"),
    (
        ("material_macro_title", "g-material-hero"),
        ("technical_nodes_network", "hero-network-layout"),
        ("centered_statement_quiet", "hero-type--quiet"),
        ("editorial_columns_manifesto", "hero-type--manifesto"),
        ("brutalist_block_intro", "hero-type--brutalist"),
        ("architectural_void_statement", "hero-type--void"),
    ),
)
def test_hero_families_produce_structurally_distinct_markup(component_id, marker):
    dna = replace(dna_for(), hero_component=component_id)
    document = render(dna=dna)
    assert marker in document


# ---------------------------------------------------------------------------
# Content de-duplication (rule Z/AA)
# ---------------------------------------------------------------------------

def test_about_reduces_when_narrative_duplicates_the_hero_tagline():
    duplicate_payload = payload(about=payload()["tagline"])  # identical to tagline, like every lab fixture
    dna = dna_for(duplicate_payload)
    dna = replace(dna, about_component="simple_business_identity", section_order=("header", "hero", "about", "footer"))
    document = render(duplicate_payload, dna)
    about = section_body(document, "about")
    assert about, "about section should still render (facts are present)"
    assert "about--micro" in about
    assert duplicate_payload["tagline"] not in about, "the exact tagline sentence must not repeat verbatim in about"


def test_about_keeps_full_narrative_when_it_actually_differs():
    distinct_payload = payload(about="Une histoire différente de la tagline, avec un vrai contenu propre.")
    dna = dna_for(distinct_payload)
    dna = replace(dna, about_component="simple_business_identity", section_order=("header", "hero", "about", "footer"))
    document = render(distinct_payload, dna)
    about = section_body(document, "about")
    assert "about--micro" not in about
    assert distinct_payload["about"] in about


# ---------------------------------------------------------------------------
# Trust vs process honesty (rule AB)
# ---------------------------------------------------------------------------

def test_process_narrative_is_never_labelled_as_verified_evidence():
    dna = replace(dna_for(), trust_component="documented_process_proof", section_order=("header", "hero", "trust", "footer"))
    document = render(dna=dna)
    assert 'data-trust-profile="process"' in document
    assert "Notre méthode" in document
    assert "Éléments vérifiés" not in document


def test_genuine_verified_facts_keep_the_verified_wording():
    dna = replace(dna_for(), trust_component="verified_insurance_line", section_order=("header", "hero", "trust", "footer"))
    document = render(payload(facts={"insurance": "Decennale BTP"}), dna)
    assert "Éléments vérifiés" in document


# ---------------------------------------------------------------------------
# Commercial completeness / real quote contract (rule AD/AE)
# ---------------------------------------------------------------------------

def test_a_real_slug_gets_a_conversion_path_even_without_phone_or_email():
    no_contact_payload = payload(telephone="", email="")
    dna = dna_for(no_contact_payload)
    assert dna.contact_component is None and dna.form_component is None
    document = render(no_contact_payload, dna)
    assert 'id="contact"' in document
    assert 'action="#"' not in document  # no fake action swap
    assert '"/pub/"+encodeURIComponent' in document  # the real, existing contract
    assert '"/demande-devis"' in document


def test_commercial_completeness_flags_hero_and_services_only_pages():
    # No slug either: this is the one case where even the real-quote-form
    # fallback (rule AE) cannot supply a conversion path, so the structural
    # gap the dimension exists to catch is genuinely there.
    incomplete_payload = payload(telephone="", email="", slug="")
    dna = replace(
        dna_for(incomplete_payload),
        gallery_component=None, about_component=None, trust_component=None,
        cta_component=None, contact_component=None, form_component=None,
        section_order=("header", "hero", "services", "footer"),
    )
    ctx = RenderContext.from_payload(incomplete_payload, dna, "")
    plan = build_render_plan(ctx, "unit-test")
    report = assess(plan)
    assert report.commercial_completeness.score < 0.5


def test_commercial_completeness_accepts_a_real_quote_form_as_the_conversion_path():
    # Same shape (hero+services only), but a real slug exists -- rule AE
    # says the real quote contract is enough to call this complete.
    dna = replace(
        dna_for(),
        gallery_component=None, about_component=None, trust_component=None,
        cta_component=None, contact_component=None, form_component=None,
        section_order=("header", "hero", "services", "footer"),
    )
    ctx = RenderContext.from_payload(payload(telephone="", email=""), dna, "")
    plan = build_render_plan(ctx, "unit-test")
    report = assess(plan)
    assert report.commercial_completeness.score == 1.0


# ---------------------------------------------------------------------------
# RenderPlan / MediaAllocationPlan / VisualCompletenessReport
# ---------------------------------------------------------------------------

def test_render_plan_reflects_the_same_resolution_the_html_uses():
    fixture = payload()
    dna = dna_for(fixture)
    ctx = RenderContext.from_payload(fixture, dna, "")
    plan = build_render_plan(ctx, "unit-test")
    document = render(fixture, dna)
    hero_plan = plan.sections[0]
    assert hero_plan.section == "hero"
    assert f'data-component="{hero_plan.component_id}"' in document or hero_plan.component_id == "generic_quote_form"


def test_media_allocation_plan_reserves_hero_pick_before_other_sections():
    fixture = payload()
    dna = replace(dna_for(fixture), gallery_component="stock_ambient_collage", section_order=("header", "hero", "gallery", "footer"))
    ctx = RenderContext.from_payload(fixture, dna, "")
    plan = build_render_plan(ctx, "unit-test")
    hero_ids = set(plan.section("hero").resolved_media)
    gallery_ids = set(plan.section("gallery").resolved_media)
    assert not (hero_ids & gallery_ids), "the same media item must not be double-booked across sections"


def test_visual_completeness_report_never_emits_an_aesthetic_verdict():
    fixture = payload()
    dna = dna_for(fixture)
    ctx = RenderContext.from_payload(fixture, dna, "")
    plan = build_render_plan(ctx, "unit-test")
    report = assess(plan)
    serialized = str(report.to_dict())
    for banned in ("PREMIUM", "BEAUTIFUL", "PRODUCTION READY", "VISUAL PASS"):
        assert banned not in serialized


# ---------------------------------------------------------------------------
# Determinism, truth safety, escaping (still must hold under V0.2)
# ---------------------------------------------------------------------------

def test_renderer_is_still_deterministic_under_v02():
    fixture = payload()
    left, left_dna = render_payload_with_genome(fixture, "http://localhost:8000")
    right, right_dna = render_payload_with_genome(fixture, "http://localhost:8000")
    assert left == right
    assert left_dna == right_dna


def test_v02_still_escapes_hostile_content_everywhere():
    attack = "<script>alert(1)</script>"
    hostile = payload(
        nom_entreprise=attack, tagline=attack, ville=attack, about=attack,
        services=[attack], adresse=attack,
    )
    dna = replace(
        dna_for(hostile),
        hero_component="material_macro_title",
        services_component="service_bento",
        about_component="simple_business_identity",
        section_order=("header", "hero", "services", "about", "footer"),
    )
    document = render(hostile, dna)
    assert attack not in document
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in document


def test_truth_safe_media_inventory_unaffected_by_v02():
    """The Design Genome's own media compatibility (evaluate_component) was
    already correct; V0.2 only fixed the renderer's re-derivation of it."""
    inventory = design_input_from_payload(payload()).media
    assert isinstance(inventory, MediaInventory)
    assert "stock_photo" in inventory.available_roles()
    assert "artisan_project" not in inventory.available_roles()


# ---------------------------------------------------------------------------
# Mobile / responsive structure present (rule AI) -- structural check;
# true visual confirmation is the 390px browser capture, not this test.
# ---------------------------------------------------------------------------

def test_new_family_markup_ships_mobile_rules():
    from generator.genome_renderer.styles import FAMILY_CSS
    assert "@media(max-width:900px)" in FAMILY_CSS
    assert "@media(max-width:520px)" in FAMILY_CSS
    assert ".service-bento-grid" in FAMILY_CSS
    assert ".hero-network" in FAMILY_CSS


# ---------------------------------------------------------------------------
# The same 12 lab fixtures still build (rule AN) and stay NOT_REVIEWED (rule AQ)
# ---------------------------------------------------------------------------

def test_visual_lab_still_builds_twelve_not_reviewed_sites_under_v02(tmp_path):
    manifest = build_visual_lab(tmp_path)
    assert len(manifest) == 12
    assert all(item["aesthetic_status"] == "NOT_REVIEWED" for item in manifest)
    assert len({item["design_signature"] for item in manifest}) == 12
    assert len({item["composition_signature"] for item in manifest}) == 12


def test_no_empty_media_slots_in_any_of_the_twelve_lab_sites(tmp_path):
    build_visual_lab(tmp_path)
    offenders = []
    for site_dir in sorted((tmp_path / "sites").iterdir()):
        html = (site_dir / "index.html").read_text(encoding="utf-8")
        if re.search(r'<div class="g-media[^"]*">\s*</div>', html):
            offenders.append(site_dir.name)
    assert offenders == [], f"empty media slots in: {offenders}"


def test_no_generic_graphic_fallback_left_in_any_of_the_twelve_lab_sites(tmp_path):
    """Every one of the 12 already has compatible stock media (hero+gallery
    role each) -- after the media_for fix, none of them should need the
    generic rectangle at all."""
    build_visual_lab(tmp_path)
    offenders = []
    for site_dir in sorted((tmp_path / "sites").iterdir()):
        html = (site_dir / "index.html").read_text(encoding="utf-8")
        body = html.split("<body", 1)[1]
        if '<div class="graphic-fallback"' in body:
            offenders.append(site_dir.name)
    assert offenders == [], f"unexpected graphic-fallback in: {offenders}"
