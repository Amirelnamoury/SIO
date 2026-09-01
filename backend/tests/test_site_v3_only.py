"""V3.1: V3 is the only executable Site Vitrine engine."""

from copy import deepcopy
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import generator.site_generator as site_generator
from generator.site_generator import SiteGenerationError, generate_site
from generator.v3.context import is_compatible_design_profile
from generator.v3.grammar import ART_DIRECTIONS, DESIGN_ENGINE_VERSION, PROFILE_VALUES
from generator.v3.selector import select_design_grammar
from tests.site_v3_fixtures import SITE_V3_FIXTURES


OLD_V2_PROFILE = {
    "design_family": "atelier",
    "header_variant": "classic",
    "hero_variant": "split",
    "services_variant": "cards",
    "gallery_variant": "grid",
    "about_variant": "classic",
    "reviews_variant": "cards",
    "cta_variant": "banner",
    "footer_variant": "simple",
    "section_order": ["hero", "services", "contact"],
    "palette": "palette-1",
    "font_pair": "poppins-inter",
    "radius_style": "soft",
    "spacing_style": "comfortable",
    "image_treatment": "flat",
    "design_engine_version": "v2.0",
    "design_signature": "historical-v2-profile",
}


def test_selector_cree_uniquement_des_profils_v3_sur_tous_les_axes():
    for direction in ART_DIRECTIONS:
        profile, _distinct = select_design_grammar(
            {"slug": f"artisan-{direction}", "metier": "renovateur"},
            [],
            direction=direction,
        )
        assert profile["design_engine_version"] == DESIGN_ENGINE_VERSION
        assert is_compatible_design_profile(profile)
        assert all(profile[axis] in values for axis, values in PROFILE_VALUES.items())


@pytest.mark.parametrize("profile", [None, OLD_V2_PROFILE, {"design_engine_version": "legacy"}])
def test_facade_refuse_v2_legacy_et_absence_de_profil(profile):
    payload = deepcopy(SITE_V3_FIXTURES[0])
    payload["design_profile"] = profile
    with pytest.raises(SiteGenerationError, match="aucun fallback V2 ou legacy"):
        generate_site(payload, "http://localhost:8000")


def test_panne_renderer_v3_remonte_une_erreur_controlee_sans_fallback(monkeypatch):
    payload = deepcopy(SITE_V3_FIXTURES[0])

    def fail(_payload, _api_base):
        raise RuntimeError("renderer indisponible")

    monkeypatch.setattr(site_generator, "render_site_v3", fail)
    with pytest.raises(SiteGenerationError, match="generation V3 a echoue"):
        generate_site(payload, "http://localhost:8000")


def test_rendu_v3_n_invente_aucune_preuve_absente():
    payload = deepcopy(SITE_V3_FIXTURES[0])
    payload.update({
        "assurance_decennale_nom": "",
        "stats": [],
        "avis": [],
        "process_steps": [],
        "reasons": [],
        "selected_media": [],
        "ville": "",
        "code_postal": "",
        "siret": "",
    })
    rendered = generate_site(payload, "http://localhost:8000").lower()
    forbidden = (
        "années d'expérience", "clients satisfaits", "certifié rge", "assurance décennale",
        "devis sous 48h", "intervention en urgence", "intervention rapide", "partenaires",
        "récompenses", "en cours d'immatriculation",
    )
    assert all(text not in rendered for text in forbidden)
    assert "visual-fallback" in rendered


def test_ecriture_fichier_n_arrive_qu_apres_un_rendu_v3_valide(tmp_path):
    output = tmp_path / "site.html"
    invalid = deepcopy(SITE_V3_FIXTURES[0])
    invalid["design_profile"] = OLD_V2_PROFILE
    with pytest.raises(SiteGenerationError):
        generate_site(invalid, "http://localhost:8000", str(output))
    assert not output.exists()

    generate_site(SITE_V3_FIXTURES[0], "http://localhost:8000", str(output))
    assert 'data-design-engine="v3.0"' in output.read_text(encoding="utf-8")
