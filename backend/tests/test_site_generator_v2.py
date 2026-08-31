import json
import re
from copy import deepcopy

import pytest

from generator.design_registry import DESIGN_ENGINE_VERSION
from generator.site_generator import generate_site
from generator.v2.context import is_compatible_design_profile
from tests.site_v2_fixtures import TEST_SITE_V2_FIXTURES


def fixture(index=0):
    return deepcopy(TEST_SITE_V2_FIXTURES[index])


def render(data=None):
    return generate_site(data or fixture(), "http://localhost:8000")


@pytest.mark.parametrize("variant,marker", [
    ("classic", "header-classic-row"), ("minimal", "header-minimal-row"),
    ("centered", "header-brand-center"), ("compact", "header-compact-row"),
])
def test_a_header_variants_have_distinct_dom(variant, marker):
    data = fixture()
    data["design_profile"]["header_variant"] = variant
    assert marker in render(data)


@pytest.mark.parametrize("variant,marker", [
    ("fullscreen", "hero-overlay"), ("split", "hero-columns"),
    ("asymmetric", "hero-asymmetric-grid"), ("compact", "hero-compact-row"),
    ("editorial", "hero-editorial-layout"), ("card", "hero-card-stage"),
])
def test_b_hero_variants_have_distinct_dom(variant, marker):
    data = fixture()
    data["design_profile"]["hero_variant"] = variant
    assert marker in render(data)


@pytest.mark.parametrize("variant,marker", [
    ("cards", "service-item"), ("editorial", "service-editorial"),
    ("list", "<ol class=\"services-layout\">"), ("grid", "services-grid"),
    ("alternating", "service-alternating"),
])
def test_c_services_variants_have_distinct_dom(variant, marker):
    data = fixture()
    data["design_profile"]["services_variant"] = variant
    assert marker in render(data)


@pytest.mark.parametrize("variant", ["grid", "masonry", "featured", "horizontal"])
def test_d_gallery_variants_are_applied(variant):
    data = fixture()
    data["design_profile"]["gallery_variant"] = variant
    assert f'data-section="gallery" data-variant="{variant}"' in render(data)


@pytest.mark.parametrize("variant", ["classic", "editorial", "split", "compact"])
def test_e_about_variants_are_applied(variant):
    data = fixture()
    data["design_profile"]["about_variant"] = variant
    assert f'data-section="about" data-variant="{variant}"' in render(data)


@pytest.mark.parametrize("variant", ["cards", "featured", "minimal"])
def test_f_review_variants_are_applied(variant):
    data = fixture()
    data["design_profile"]["reviews_variant"] = variant
    assert f'data-section="reviews" data-variant="{variant}"' in render(data)


def test_g_section_order_controls_real_dom_after_filtering():
    data = fixture()
    data["design_profile"]["section_order"] = ["hero", "reviews", "services", "gallery", "about", "contact"]
    sections = re.findall(r'<section[^>]+data-section="([^"]+)"', render(data))
    assert sections == ["hero", "reviews", "services", "gallery", "about", "contact"]


def test_h_sections_without_data_are_omitted_and_no_content_is_invented():
    data = fixture(1)
    data.update({"ville": "", "adresse": "", "assurance_decennale_nom": "", "stats": [], "selected_media": [], "avis": []})
    data["design_profile"]["section_order"] = ["hero", "trust", "gallery", "reviews", "about", "process", "reasons", "services"]
    output = render(data)
    for section in ("trust", "gallery", "reviews", "about", "process", "reasons"):
        assert f'data-section="{section}"' not in output
    for invented in ("sous 48h", "en cours d'immatriculation", "Réactivité", "certifié"):
        assert invented not in output


def test_i_real_logo_and_j_typographic_fallback():
    with_logo = render(fixture())
    assert '/visual-assets/logo-1.webp' in with_logo and 'class="brand-logo"' in with_logo
    without = fixture(1)
    output = render(without)
    assert 'brand-wordmark' in output and without["nom_entreprise"] in output
    assert '<img class="brand-logo"' not in output


def test_k_selected_media_and_l_graphical_fallback():
    assert '/visual-assets/plomberie-1.webp' in render(fixture())
    output = render(fixture(1))
    assert 'hero-fallback' in output and '<img class="hero-image"' not in output


def test_m_only_real_reviews_and_n_only_configured_services():
    data = fixture()
    data["avis"] = [{"note": 4, "commentaire": "Avis unique fixture.", "nom_auteur": "Auteur fixture"}]
    data["services"] = ["Prestation unique fixture"]
    output = render(data)
    assert "Avis unique fixture." in output and "Client test A" not in output
    assert "Prestation unique fixture" in output and "Installation sanitaire" not in output


def test_o_no_generic_business_claims_are_injected():
    output = render(fixture(6))
    forbidden = ("Devis gratuit", "intervention rapide", "années d'expérience", "Assurance décennale")
    assert all(text not in output for text in forbidden)


def test_p_user_content_is_escaped_in_html_attributes_and_json_ld():
    data = fixture(0)
    data["nom_entreprise"] = '<img src=x onerror="alert(1)"> & Associés'
    data["services"] = ['<script>alert("service")</script>']
    data["avis"] = [{"note": 5, "commentaire": "</script><script>alert(2)</script>", "nom_auteur": "<b>A</b>"}]
    data["design_profile"]["section_order"] = ["hero", "services", "reviews", "contact"]
    output = render(data)
    assert '<img src=x onerror=' not in output
    assert '<script>alert("service")</script>' not in output
    assert "&lt;script&gt;alert" in output
    assert "&amp;amp; Associés" not in output
    assert output.count('<script type="application/ld+json">') == 1


def test_q_json_ld_is_valid_and_contains_only_known_location_fields():
    data = fixture(2)
    output = render(data)
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', output, re.S)
    schema = json.loads(block.group(1))
    assert schema["@type"] == "LocalBusiness"
    assert schema["name"] == data["nom_entreprise"]
    assert schema["address"]["addressLocality"] == data["ville"]
    assert "aggregateRating" not in schema and "openingHours" not in schema and "geo" not in schema


def test_r_local_seo_uses_known_values_and_canonical_when_present():
    data = fixture(4)
    data["url_publique"] = "https://fixture.example.test"
    output = render(data)
    assert f'<title>{data["nom_entreprise"]} - Peintre à Bordeaux</title>' in output
    assert '<link rel="canonical" href="https://fixture.example.test">' in output
    assert '<meta property="og:title"' in output and '<meta name="robots" content="index,follow">' in output


def test_s_responsive_accessibility_and_form_contract_are_present():
    output = render()
    for breakpoint in ("1024px", "768px", "430px"):
        assert f"@media (max-width: {breakpoint})" in output
    assert "prefers-reduced-motion" in output
    assert '<html lang="fr">' in output and 'class="skip-link"' in output
    assert 'label for="client_nom"' in output and 'role="status"' in output
    assert 'API_BASE + "/pub/" + encodeURIComponent(SLUG) + "/demande-devis"' in output


def test_t_design_tokens_and_every_profile_axis_affect_output():
    data = fixture()
    output = render(data)
    for token in ("--color-primary:", "--font-heading:", "--radius-lg:", "--space-section:", "--container:"):
        assert token in output
    assert 'family-impact' in output and 'image-overlay' in output
    changed = fixture()
    changed["design_profile"].update({"palette": "palette-3", "font_pair": "rajdhani-inter", "radius_style": "rounded", "spacing_style": "spacious", "image_treatment": "framed"})
    assert render(changed) != output


def test_design_engine_compatibility_is_centralized_and_v1_remains_available():
    profile = fixture()["design_profile"]
    assert is_compatible_design_profile(profile)
    incompatible = {**profile, "design_engine_version": "v3.0"}
    assert not is_compatible_design_profile(incompatible)
    legacy = fixture(1)
    legacy.pop("design_profile")
    assert 'data-design-engine="v2.0"' not in render(legacy)


def test_nine_visual_fixtures_are_structurally_diverse_and_test_only():
    outputs = [render(fixture(index)) for index in range(9)]
    profiles = [item["design_profile"] for item in TEST_SITE_V2_FIXTURES]
    assert {item["metier"] for item in TEST_SITE_V2_FIXTURES} == {"plombier", "peintre", "macon"}
    assert all(item["nom_entreprise"].startswith("FIXTURE TEST") for item in TEST_SITE_V2_FIXTURES)
    assert len({profile["design_family"] for profile in profiles}) >= 6
    assert len({profile["hero_variant"] for profile in profiles}) >= 6
    assert len({profile["services_variant"] for profile in profiles}) >= 5
    assert len({tuple(profile["section_order"]) for profile in profiles}) == 9
    assert len({profile["palette"] for profile in profiles}) == 3
    assert len({profile["design_signature"] for profile in profiles}) == 9
    structures = {re.sub(r">[^<]+<", "><", output) for output in outputs}
    assert len(structures) == 9
