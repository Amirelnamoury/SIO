from __future__ import annotations

from dataclasses import replace
import re
from pathlib import Path

import pytest

from generator.design_genome.data.color_systems import COLOR_SYSTEMS
from generator.design_genome.generator import DesignGenome
from generator.design_genome.models import SiteDNA
from generator.genome_renderer import RenderContext, render_payload_with_genome, render_site_genome
from generator.genome_renderer.adapter import design_input_from_payload
from generator.genome_renderer.lab.build import build_visual_lab
from generator.site_generator import generate_site, generate_site_genome_experimental


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
        "services": ["Installation sanitaire", "Rénovation de salle de bain"],
        "facts": {"process": ("Échange", "Préparation", "Réalisation")},
        "selected_media": [
            {
                "id": "stock-1",
                "url": "/assets/plomberie.webp",
                "role": "hero",
                "source": "pexels",
                "credit": "Photo Pexels",
                "source_url": "https://www.pexels.com/photo/10473013/",
                "alt": "Détail de robinetterie",
            }
        ],
    }
    value.update(overrides)
    return value


def dna_for(value=None) -> SiteDNA:
    value = value or payload()
    return DesignGenome().generate(design_input_from_payload(value, seed="renderer-test"))


def render(value=None, dna=None, *, lab_mode=False, api="http://localhost:8000"):
    value = value or payload()
    dna = dna or dna_for(value)
    context = RenderContext.from_payload(value, dna, api, lab_mode=lab_mode)
    return render_site_genome(context)


def without_style(document: str) -> str:
    return re.sub(r"<style>.*?</style>", "<style></style>", document, flags=re.S)


def test_renderer_is_deterministic_and_emits_one_accessible_document():
    source = payload()
    left, left_dna = render_payload_with_genome(source, "http://localhost:8000")
    right, right_dna = render_payload_with_genome(source, "http://localhost:8000")
    assert left == right
    assert left_dna == right_dna
    assert '<html lang="fr">' in left
    assert left.count("<h1>") == 1
    assert 'href="#contenu"' in left
    assert ":focus-visible" in left


@pytest.mark.parametrize(
    ("component_id", "marker"),
    (
        ("full_bleed_photo_cover", '<div class="g-cover">'),
        ("centered_image_frame", '<div class="g-centered-frame">'),
        ("panorama_architectural", '<div class="g-panorama">'),
        ("lighting_atmosphere_cover", '<div class="g-atmosphere">'),
    ),
)
def test_hero_blueprints_materialize_distinct_dom(component_id, marker):
    dna = replace(dna_for(), hero_component=component_id)
    document = render(dna=dna)
    assert marker in document


def test_same_header_family_explicit_variants_change_dom_structure():
    dna = dna_for()
    classic = render(dna=replace(dna, header_component="classic_brand_left"))
    split = render(dna=replace(dna, header_component="split_navigation"))
    assert "header-linear" in classic
    assert "header-split-brand-axis" in split
    assert classic != split


def test_palette_ablation_keeps_dom_and_changes_css_tokens():
    dna = dna_for()
    other_color = next(key for key in COLOR_SYSTEMS if key != dna.color_system)
    original = render(dna=dna)
    changed = render(dna=replace(dna, color_system=other_color))
    assert without_style(original) == without_style(changed)
    assert re.search(r":root\{[^}]+\}", original).group() != re.search(r":root\{[^}]+\}", changed).group()


def test_dna_systems_are_exposed_as_concrete_tokens_and_responsive_rules():
    document = render()
    for token in (
        "--color-canvas", "--font-display", "--content-max", "--grid-columns",
        "--space-section", "--radius", "--border-width", "--motion-duration",
    ):
        assert token in document
    assert "@media(max-width:900px)" in document
    assert "@media(max-width:520px)" in document
    assert "@media(prefers-reduced-motion:reduce)" in document
    assert 'data-spatial-rendering="' in document
    assert "WebGL" not in document


def test_section_order_follows_site_dna_and_dead_navigation_links_are_omitted():
    dna = replace(
        dna_for(),
        services_component="editorial_service_rows",
        about_component="simple_business_identity",
        gallery_component=None,
        trust_component=None,
        cta_component=None,
        contact_component="quote_first_contact",
        form_component="single_column_quote_form",
        section_order=("header", "about", "services", "gallery", "contact", "footer"),
    )
    document = render(dna=dna)
    assert document.index('id="about"') < document.index('id="services"') < document.index('id="contact"')
    assert 'href="#gallery"' not in document
    assert 'href="#contact"' in document


def test_stock_media_cannot_fill_artisan_project_slot():
    dna = replace(
        dna_for(),
        gallery_component="artisan_project_grid",
        section_order=("header", "hero", "gallery", "footer"),
    )
    document = render(dna=dna)
    assert 'id="gallery"' not in document
    assert "Notre réalisation" not in document
    assert "Projet sélectionné" not in document


def test_stock_gallery_is_never_labelled_as_artisan_work():
    source = payload(selected_media=[{
        "id": "stock-gallery",
        "url": "/assets/matiere.webp",
        "role": "gallery",
        "source": "pexels",
        "credit": "Photo Pexels",
        "alt": "Matière et ambiance",
    }])
    dna = replace(
        dna_for(source),
        gallery_component="stock_ambient_collage",
        section_order=("header", "hero", "gallery", "footer"),
    )
    document = render(source, dna)
    assert 'data-media-provenance="stock-ambient"' in document
    assert "Inspirations et matières" in document
    assert ">Réalisations<" not in document


def test_admin_library_pexels_selection_is_normalized_as_stock_media():
    source = payload(selected_media=[{
        "media_id": "pexels-10473013",
        "content_url": "/admin/api/artisans/5/site/media/library/2/content?variant=web",
        "usage": "gallery",
        "source": "bibliotheque",
        "provider": "pexels",
        "credit": "Photo Pexels",
        "alt_text": "Matière et ambiance",
    }])
    inventory = design_input_from_payload(source).media
    assert inventory.stock_photos == 1
    dna = replace(
        dna_for(source),
        gallery_component="stock_ambient_collage",
        section_order=("header", "hero", "gallery", "footer"),
    )
    document = render(source, dna)
    assert 'id="gallery"' in document
    assert 'data-media-provenance="stock-ambient"' in document


def test_verified_artisan_project_selection_can_fill_project_slot():
    source = payload(selected_media=[{
        "media_id": "artisan-42",
        "content_url": "/admin/api/artisans/5/site/media/42/content?variant=web",
        "usage": "gallery",
        "source": "artisan",
        "categorie": "realisation",
        "alt_text": "Réalisation documentée",
    }])
    inventory = design_input_from_payload(source).media
    assert inventory.project_photos == 1
    dna = replace(
        dna_for(source),
        gallery_component="artisan_project_grid",
        section_order=("header", "hero", "gallery", "footer"),
    )
    document = render(source, dna)
    assert 'data-media-provenance="artisan"' in document
    assert ">Réalisations<" in document


def test_missing_truth_data_never_creates_reviews_stats_certifications_or_phone():
    source = payload(telephone="", email="", facts={}, avis=[], stats=[], certifications=[])
    dna = replace(
        dna_for(source),
        trust_component="verified_review_excerpt",
        contact_component="minimal_contact",
        section_order=("header", "hero", "trust", "contact", "footer"),
    )
    document = render(source, dna)
    assert 'id="trust"' not in document
    assert "testimonial" not in document.lower()
    assert "certification" not in document.lower()
    assert 'href="tel:' not in document


def test_artisan_content_is_escaped_across_sections_and_media():
    attack = "<script>alert(1)</script>"
    source = payload(
        nom_entreprise=attack,
        tagline=attack,
        ville=attack,
        about=attack,
        services=[attack],
        adresse=attack,
        avis=[{"commentaire": attack, "nom_auteur": attack}],
        selected_media=[{"id": "x", "url": "/x.webp", "role": "hero", "source": "pexels", "alt": attack}],
    )
    dna = replace(
        dna_for(source),
        services_component="editorial_service_rows",
        about_component="simple_business_identity",
        trust_component="verified_review_excerpt",
        contact_component="minimal_contact",
        section_order=("header", "hero", "services", "about", "trust", "contact", "footer"),
    )
    document = render(source, dna)
    assert attack not in document
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in document


def test_lead_form_uses_existing_public_endpoint_and_no_unconditional_success():
    document = render()
    assert '"/pub/"+encodeURIComponent' in document
    assert '"/demande-devis"' in document
    success = document.index("Merci, votre demande a bien été envoyée.")
    ok_check = document.index("if(!response.ok)throw new Error()")
    assert success > ok_check


def test_synthetic_fixture_is_rejected_outside_visual_lab():
    source = payload(synthetic_fixture=True)
    dna = dna_for(source)
    with pytest.raises(ValueError, match="visual lab"):
        RenderContext.from_payload(source, dna)
    document = render(source, dna, lab_mode=True, api="")
    assert 'data-synthetic-form="true"' in document
    assert "demande-devis" not in document


def test_visual_lab_builds_twelve_portable_not_reviewed_sites(tmp_path: Path):
    manifest = build_visual_lab(tmp_path)
    assert len(manifest) == 12
    assert len({item["design_signature"] for item in manifest}) == 12
    assert len({item["composition_signature"] for item in manifest}) == 12
    assert all(item["aesthetic_status"] == "NOT_REVIEWED" for item in manifest)
    assert all((tmp_path / "sites" / item["fixture_id"] / "index.html").is_file() for item in manifest)
    assert (tmp_path / "review" / "manifest.json").is_file()
    assert (tmp_path / "vercel.json").is_file()
    # V0.2 marker carries the correct tool attribution (Claude Code, not the
    # V0.1 session's Codex); see lab/build.py.
    assert (tmp_path / "VERCEL_PREVIEW_NOT_DEPLOYED_BY_CLAUDE_CODE").is_file()


def test_v3_entry_point_remains_default_and_genome_is_explicit(monkeypatch):
    monkeypatch.setattr("generator.site_generator.is_compatible_design_profile", lambda value: True)
    monkeypatch.setattr("generator.site_generator.render_site_v3", lambda value, api: "<p>V3 runtime</p>")
    assert generate_site({"design_profile": {}}, "") == "<p>V3 runtime</p>"
    experimental = generate_site_genome_experimental(payload(), "http://localhost:8000")
    assert 'data-renderer="design-genome-renderer-0.2.1"' in experimental
    assert "V3 runtime" not in experimental
