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

from generator.design_registry import DESIGN_ENGINE_VERSION, DESIGN_FAMILIES
from generator.site_generator import generate_site
from generator.v2.styles import BASE_CSS
from tests.site_v2_fixtures import TEST_SITE_V2_FIXTURES, profile


def fixture(index=0):
    return deepcopy(TEST_SITE_V2_FIXTURES[index])


def render(data=None):
    return generate_site(data if data is not None else fixture(), "http://localhost:8000")


# Le jeu historique des 9 fixtures (site_v2_fixtures.py) n'a que 2 sites sans
# photo (technique, architecture) - le brief Lot 3.1 en voulait 3, sur 3
# familles differentes. On NE modifie PAS les 9 fixtures historiques (elles
# servent de non-regression), on ajoute une fixture de VALIDATION dediee,
# ici uniquement, pour une troisieme famille : "signature" est la famille la
# plus dependante du photographique ("haut de gamme, magazine,
# photographique") - c'est donc le cas le plus exigeant pour verifier que le
# fallback sans photo reste credible et premium.
FIXTURE_SIGNATURE_SANS_PHOTO = {
    "nom_entreprise": "FIXTURE TEST - Maison Verrière",
    "metier": "peintre", "slug": "fixture-signature-sans-photo", "ville": "Lyon", "code_postal": "69006",
    "telephone": "04 00 00 00 10", "email": "verriere@example.test",
    "tagline": "Peinture décorative et finitions haut de gamme pour intérieurs d'exception",
    "services": ["Décoration murale sur mesure", "Laques et boiseries", "Patines et effets de matière"],
    "avis": [{"note": 5, "commentaire": "Un rendu magnifique, tres au dela de nos attentes.", "nom_auteur": "Client fixture E"}],
    "assurance_decennale_nom": "Assureur fixture E",
    "selected_media": [],  # aucune photo, aucun logo : cas le plus exigeant pour la famille "signature"
    "design_profile": profile(
        "signature", "centered", "editorial", "editorial", "featured", "editorial", "featured", "split", "map",
        ["hero", "about", "services", "reviews", "cta", "contact"],
        "palette-1", "poppins-inter", "soft", "spacious", "flat", "fixture-signature-sans-photo",
    ),
}
assert FIXTURE_SIGNATURE_SANS_PHOTO["design_profile"]["design_engine_version"] == DESIGN_ENGINE_VERSION


def test_les_grilles_avec_image_ont_min_width_zero_contre_le_blowout_mobile():
    """Lot 3.1b - bug reel trouve en inspection visuelle : sans min-width:0,
    un <img> avec de grands attributs width/height HTML (cas normal pour eviter
    le layout shift) qui n'a pas encore charge (ou echoue a charger) force sa
    grille parente a rester a sa taille intrinseque au lieu de 1fr, ce qui
    casse tout le mobile (grid blowout, confirme via Playwright : la grille
    passait de 1fr a 1400px). Verifie que la regle corrective est presente
    pour toutes les grilles susceptibles de contenir une image."""
    for selector in (
        ".hero-columns > *", ".hero-asymmetric-grid > *", ".hero-card-stage > *",
        ".about-layout > *", ".featured-layout > *",
    ):
        assert f"{selector}" in BASE_CSS
    assert re.search(r"\.hero-columns > \*,[^{]*\{\s*min-width:\s*0;", BASE_CSS)


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


def test_image_flat_reste_neutre_alors_que_les_3_autres_traitements_modifient_le_rendu():
    """'flat' doit rester le traitement neutre (aucun filtre/ombre imposee sur
    l'image) : c'est ce contraste qui rend perceptible que duotone/framed/
    overlay font vraiment quelque chose, pas un choix arbitraire (brief
    section 13). Une regle CSS qui cible '.image-flat img' avec un filter ou
    un box-shadow serait un signe que 'flat' n'est plus neutre."""
    flat_rules = re.findall(r"\.image-flat img\s*\{([^}]*)\}", BASE_CSS)
    assert all("filter" not in rule and "box-shadow" not in rule for rule in flat_rules)
    assert re.search(r"\.image-duotone img\s*\{[^}]*filter:", BASE_CSS)
    assert re.search(r"\.image-overlay img\s*\{[^}]*box-shadow:\s*inset", BASE_CSS)
    assert re.search(r"\.image-framed img\s*\{[^}]*border:", BASE_CSS)


def test_traitements_image_ne_produisent_jamais_de_contenu_invente():
    output = render(fixture(1))
    forbidden = ("Devis gratuit", "intervention rapide", "années d'expérience")
    assert all(text not in output for text in forbidden)


def test_troisieme_cas_sans_photo_signature_reste_premium_sans_placeholder():
    """Complete les 2 cas sans photo du jeu historique (technique, architecture)
    avec un 3e, sur la famille la plus dependante du photographique - voir
    FIXTURE_SIGNATURE_SANS_PHOTO ci-dessus. Aucune image, aucun logo, aucun
    contenu invente ; le fallback doit rester celui, premium, de la famille."""
    output = render(deepcopy(FIXTURE_SIGNATURE_SANS_PHOTO))
    assert "family-signature" in output
    assert "hero-fallback" in output
    assert "about-monogram" in output
    assert "<img" not in output.split("<main", 1)[1].split("</main>", 1)[0]  # aucune image en contenu principal
    forbidden = ("Devis gratuit", "intervention rapide", "années d'expérience", "certifié", "sous 48h")
    assert all(text not in output for text in forbidden)


def test_les_3_cas_sans_photo_couvrent_3_familles_differentes():
    familles_sans_photo = {
        item["design_profile"]["design_family"]
        for item in TEST_SITE_V2_FIXTURES
        if not item.get("selected_media")
    }
    familles_sans_photo.add(FIXTURE_SIGNATURE_SANS_PHOTO["design_profile"]["design_family"])
    assert len(familles_sans_photo) >= 3


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
