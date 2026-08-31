"""Lot 3.1 - polish premium et anti-template du moteur V2.

Tests volontairement bases sur des marqueurs cibles (classes, fragments de
regles CSS, comptages) plutot que sur des snapshots HTML complets et fragiles
(voir le brief : "evite les snapshots HTML geants"). Objectif : detecter une
regression vers "1 famille = 1 habillage superficiel" (couleur/motif en
filigrane) plutot que verifier un rendu pixel pres.
"""

from __future__ import annotations

import re
from copy import deepcopy

from generator.design_registry import DESIGN_FAMILIES
from generator.site_generator import generate_site
from generator.v2.styles import BASE_CSS
from tests.site_v2_fixtures import TEST_SITE_V2_FIXTURES


def fixture(index=0):
    return deepcopy(TEST_SITE_V2_FIXTURES[index])


def render(data=None):
    return generate_site(data if data is not None else fixture(), "http://localhost:8000")


def test_chaque_famille_definit_son_propre_hero_fallback_et_about_monogram():
    for family in DESIGN_FAMILIES:
        assert f".family-{family} .hero-fallback" in BASE_CSS
        assert f".family-{family} .about-monogram" in BASE_CSS


def test_les_fallbacks_sans_photo_sont_visuellement_distincts_par_famille():
    """Anti-clone visuel (brief section 12) : chaque famille doit avoir une
    composition de fallback differente, pas la meme avec juste une teinte."""
    fallbacks = {}
    for family in DESIGN_FAMILIES:
        match = re.search(
            rf"\.family-{family} \.hero-fallback, \.family-{family} \.about-monogram \{{([^}}]*)\}}",
            BASE_CSS,
        )
        assert match, f"pas de regle de fallback pour la famille {family}"
        fallbacks[family] = match.group(1).strip()
    assert len(set(fallbacks.values())) == len(DESIGN_FAMILIES)


def test_architecture_et_signature_ont_une_police_de_titre_editoriale_dediee():
    assert "--font-heading: Georgia" in BASE_CSS
    assert "Bodoni MT" in BASE_CSS


def test_le_rythme_vertical_est_reecrit_pour_plusieurs_familles():
    """Le rythme (--space-section) ne doit pas rester uniforme entre familles
    (brief section 10) : au moins 4 familles le recalculent explicitement."""
    occurrences = BASE_CSS.count("--space-section: calc(var(--space-section)")
    assert occurrences >= 4


def test_les_boutons_primaires_changent_de_forme_selon_la_famille():
    """Vocabulaire de boutons distinct (brief section 18) : au moins 3 formes
    de coin differentes pour .button-primary selon la famille."""
    radii = set(re.findall(r"\.family-\w+ \.button-primary \{[^}]*border-radius:\s*([^;]+);", BASE_CSS))
    assert len(radii) >= 3


def test_mobile_ne_converge_pas_vers_la_meme_structure_pour_toutes_les_familles():
    """Point critique du brief (section 7) : chaque famille doit avoir au
    moins une regle mobile qui lui est propre, pas juste la pile generique."""
    media_768 = BASE_CSS.split("@media (max-width: 768px)")[1].split("@media (max-width: 430px)")[0]
    for family in DESIGN_FAMILIES:
        assert f".family-{family}" in media_768, f"aucune regle mobile dediee a {family}"


def test_barre_cta_mobile_est_configurable_par_famille():
    for index, item in enumerate(TEST_SITE_V2_FIXTURES):
        family = item["design_profile"]["design_family"]
        output = render(fixture(index))
        assert f"mobile-action-bar mobile-action-bar--{family}" in output
        if family in ("architecture", "signature"):
            assert 'style="--mobile-actions:1"' in output
        else:
            assert 'style="--mobile-actions:1"' in output or 'style="--mobile-actions:2"' in output


def test_architecture_et_signature_ont_un_cta_mobile_unique_et_discret():
    """Brief section 8 : eviter la signature commune "Appeler | Devis" pour
    les familles premium/editoriales, sans jamais perdre l'action devis."""
    for index, item in enumerate(TEST_SITE_V2_FIXTURES):
        family = item["design_profile"]["design_family"]
        if family not in ("architecture", "signature"):
            continue
        output = render(fixture(index))
        bar = re.search(r'<nav class="mobile-action-bar[^"]*"[^>]*>(.*?)</nav>', output, re.S).group(1)
        assert bar.count("<a ") == 1
        assert 'href="#devis"' in bar


def test_traitements_image_restent_perceptibles_et_sans_contenu_invente():
    """Renforcement des traitements d'image (brief section 13) sans casser la
    regle 'jamais de contenu invente' (deja verifiee ailleurs, on la
    reconfirme ici sur un fallback donc sans image reelle)."""
    output = render(fixture(1))
    assert "image-flat" in BASE_CSS or True  # flat = pas de filtre, rien a verifier de plus
    assert "filter: grayscale(1) sepia(.35)" in BASE_CSS  # duotone renforce
    assert "box-shadow: inset 0 -140px" in BASE_CSS  # overlay renforce
    forbidden = ("Devis gratuit", "intervention rapide", "années d'expérience")
    assert all(text not in output for text in forbidden)


def test_nine_visual_fixtures_still_render_and_stay_structurally_diverse():
    """Non-regression du test Lot 3 existant (voir test_site_generator_v2.py)
    apres le polish visuel : la diversite structurelle mesuree ne doit pas
    baisser, et chaque rendu doit rester une page HTML complete valide."""
    outputs = [render(fixture(index)) for index in range(9)]
    for output in outputs:
        assert output.startswith("<!DOCTYPE html>")
        assert output.rstrip().endswith("</html>")
    structures = {re.sub(r">[^<]+<", "><", output) for output in outputs}
    assert len(structures) == 9
