from collections import defaultdict
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.site_generator import generate_site
from generator.v3.context import is_compatible_design_profile
from generator.v3.grammar import PAGE_SILHOUETTES, PROFILE_VALUES
from generator.v3.selector import select_design_grammar

from tests.site_v3_fixtures import SITE_V3_FIXTURES


def render(item):
    return generate_site(item, "http://localhost:8000")


def test_18_fixtures_couvrent_six_metiers_et_trois_sites_chacun():
    groups = defaultdict(list)
    for item in SITE_V3_FIXTURES:
        groups[item["metier"]].append(item)
    assert len(SITE_V3_FIXTURES) == 18
    assert set(map(len, groups.values())) == {3}


def test_chaque_groupe_a_silhouette_hero_typo_et_traitement_distincts():
    groups = defaultdict(list)
    for item in SITE_V3_FIXTURES:
        groups[item["metier"]].append(item["design_profile"])
    for profiles in groups.values():
        for axis in ("page_silhouette", "hero_system", "image_treatment"):
            assert len({profile[axis] for profile in profiles}) == 3, axis
        visual_type_combinations = {(profile["typography_system"], profile["services_composition"]) for profile in profiles}
        assert len(visual_type_combinations) == 3


def test_profils_valides_sur_les_20_axes_et_rendus_structurels():
    for item in SITE_V3_FIXTURES:
        profile = item["design_profile"]
        assert is_compatible_design_profile(profile)
        assert all(profile[axis] in values for axis, values in PROFILE_VALUES.items())
        html = render(item)
        assert 'data-design-engine="v3.0"' in html
        assert f'hero-{profile["hero_system"]}' in html
        assert f'silhouette-{profile["page_silhouette"]}' in html
        assert "prefers-reduced-motion:reduce" in html
        assert "réponse en 24h" not in html.lower()
        assert "clients satisfaits" not in html.lower()


def test_zero_photo_logo_avis_stats_certification_reste_complet_et_honnete():
    item = dict(SITE_V3_FIXTURES[0])
    item.update({"telephone": "", "ville": "", "code_postal": "", "selected_media": [], "stats": [], "avis": [], "assurance_decennale_nom": "", "siret": ""})
    html = render(item)
    assert "visual-fallback" in html
    assert "Assurance décennale" not in html
    assert "Avis publiés" not in html
    assert 'id="devis-form"' in html


def test_services_supportent_zero_un_deux_six_et_plus():
    for count in (0, 1, 2, 6, 9):
        item = dict(SITE_V3_FIXTURES[1])
        item["services"] = [f"Service {index}" for index in range(count)]
        html = render(item)
        assert ("data-section=\"services\"" in html) is (count > 0)


def test_cross_metier_ne_partage_pas_une_signature_clone():
    pairs = (("peintre", "menuisier"), ("plombier", "electricien"), ("macon", "renovateur"))
    by_trade = defaultdict(list)
    for item in SITE_V3_FIXTURES:
        by_trade[item["metier"]].append(item["design_profile"])
    for left, right in pairs:
        assert {p["design_signature"] for p in by_trade[left]}.isdisjoint({p["design_signature"] for p in by_trade[right]})
        assert {p["page_silhouette"] for p in by_trade[left]} != {p["page_silhouette"] for p in by_trade[right]}


def test_selection_est_stable_pour_une_meme_graine():
    artisan = {"slug": "stable-v3", "metier": "peintre"}
    first, _ = select_design_grammar(artisan, [])
    second, _ = select_design_grammar(artisan, [])
    assert first == second
    assert first["page_silhouette"] in PAGE_SILHOUETTES
