"""Site Vitrine V2 - Lot 1 : fondations du moteur de design (design_profile
persistant, registre de variantes, anti-clonage, compatibilite ancien site).

Voir generator/design_registry.py, generator/design_selector.py,
app/design_schemas.py, app/admin_service.py::ensure_design_profile.
"""
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Artisan, SiteVitrine
from app.security import create_access_token
from generator.design_registry import (
    ABOUT_VARIANTS,
    CTA_VARIANTS,
    DESIGN_FAMILIES,
    FONT_PAIR_IDS,
    FOOTER_VARIANTS,
    GALLERY_VARIANTS,
    HEADER_VARIANTS,
    HERO_VARIANTS,
    IMAGE_TREATMENTS,
    PALETTE_SLOTS,
    RADIUS_STYLES,
    REVIEWS_VARIANTS,
    SECTION_CATALOG,
    SERVICES_VARIANTS,
    SPACING_STYLES,
    resolve_visible_sections,
)
from generator.design_selector import build_design_signature, select_design_profile, similarity_score


def _admin_headers() -> tuple[dict, int]:
    """Cree un admin de test et renvoie (headers, admin_id)."""
    db = SessionLocal()
    try:
        suffixe = uuid4().hex
        from app.models import AdminUser
        admin_row = AdminUser(
            email=f"design-engine-admin-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            nom="Admin Design Engine",
            actif=True,
        )
        db.add(admin_row)
        db.commit()
        db.refresh(admin_row)
        admin_id = admin_row.id
    finally:
        db.close()
    return {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}, admin_id


def _creer_artisan(metier: str = "plombier") -> int:
    suffixe = uuid4().hex
    db = SessionLocal()
    try:
        artisan = Artisan(
            slug=f"design-engine-{suffixe}",
            nom_entreprise=f"Design Engine {suffixe}",
            metier=metier,
            email=f"design-engine-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
        )
        db.add(artisan)
        db.commit()
        db.refresh(artisan)
        return artisan.id
    finally:
        db.close()


# ---------- A. Persistance : regenerer ne change pas le profil ----------

def test_regenerer_la_preview_reutilise_exactement_le_meme_design_profile():
    headers, _ = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        premiere = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert premiere.status_code == 200, premiere.text
        profil_1 = premiere.json()["design_profile"]
        assert profil_1 is not None

        deuxieme = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert deuxieme.status_code == 200, deuxieme.text
        profil_2 = deuxieme.json()["design_profile"]

        assert profil_1 == profil_2, "regenerer la preview ne doit jamais changer le design_profile deja persiste"

        # Confirme aussi via une lecture independante (GET, pas de generation).
        lecture = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers)
        assert lecture.status_code == 200, lecture.text
        assert lecture.json()["design_profile"] == profil_1


# ---------- B. Diversite : plusieurs artisans successifs ----------

def test_trois_artisans_successifs_du_meme_metier_ne_recoivent_pas_tous_le_meme_profil():
    headers, _ = _admin_headers()
    ids = [_creer_artisan("plombier") for _ in range(3)]
    profils = []
    with TestClient(app) as client:
        for artisan_id in ids:
            res = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
            assert res.status_code == 200, res.text
            profils.append(res.json()["design_profile"])

    signatures = {p["design_signature"] for p in profils}
    assert len(signatures) > 1, f"3 artisans successifs ne doivent pas tous recevoir la meme signature : {signatures}"

    familles = {p["design_family"] for p in profils}
    assert len(familles) > 1 or len({p["palette"] for p in profils}) > 1, (
        "au moins la famille ou la palette doit varier entre 3 artisans successifs"
    )


def test_selecteur_pur_evite_les_profils_trop_similaires():
    """Test unitaire (sans DB/HTTP) de l'algorithme d'anti-clonage lui-meme :
    deterministe, testable independamment de l'API."""
    existants = []
    profils = []
    for i in range(5):
        artisan = {"slug": f"artisan-{i}"}
        profil = select_design_profile(artisan, existants)
        profils.append(profil)
        existants.append(profil)

    # Aucune paire ne doit avoir un score de similarite >= au seuil retenu
    # par le selecteur (verifie la garantie, pas juste un echantillon).
    from generator.design_selector import SIMILARITY_THRESHOLD
    for i in range(len(profils)):
        for j in range(i + 1, len(profils)):
            score = similarity_score(profils[i], profils[j])
            assert score < SIMILARITY_THRESHOLD, (
                f"profils {i} et {j} trop similaires (score={score}) : {profils[i]['design_signature']} vs {profils[j]['design_signature']}"
            )


# ---------- C. Validation : toutes les valeurs viennent des registres ----------

def test_design_profile_genere_respecte_toujours_le_registre():
    headers, _ = _admin_headers()
    artisan_id = _creer_artisan("macon")
    with TestClient(app) as client:
        res = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert res.status_code == 200, res.text
        p = res.json()["design_profile"]

    assert p["design_family"] in DESIGN_FAMILIES
    assert p["header_variant"] in HEADER_VARIANTS
    assert p["hero_variant"] in HERO_VARIANTS
    assert p["services_variant"] in SERVICES_VARIANTS
    assert p["gallery_variant"] in GALLERY_VARIANTS
    assert p["about_variant"] in ABOUT_VARIANTS
    assert p["reviews_variant"] in REVIEWS_VARIANTS
    assert p["cta_variant"] in CTA_VARIANTS
    assert p["footer_variant"] in FOOTER_VARIANTS
    assert p["palette"] in PALETTE_SLOTS
    assert p["font_pair"] in FONT_PAIR_IDS
    assert p["radius_style"] in RADIUS_STYLES
    assert p["spacing_style"] in SPACING_STYLES
    assert p["image_treatment"] in IMAGE_TREATMENTS
    assert all(section in SECTION_CATALOG for section in p["section_order"])
    assert p["section_order"][0] == "hero"
    assert p["design_signature"] == build_design_signature(p)


# ---------- D. Ancien site sans design_profile ----------

def test_ancien_site_sans_design_profile_reste_lisible_puis_recoit_un_profil_proprement():
    headers, _ = _admin_headers()
    artisan_id = _creer_artisan("electricien")

    # Simule un site cree AVANT ce lot (design_profile absent en base, comme
    # si la colonne venait d'etre ajoutee par la migration).
    db = SessionLocal()
    try:
        site = SiteVitrine(artisan_id=artisan_id, statut="genere", config={}, design_profile=None)
        db.add(site)
        db.commit()
    finally:
        db.close()

    with TestClient(app) as client:
        # 1. Toujours lisible malgre l'absence de design_profile.
        lecture = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers)
        assert lecture.status_code == 200, lecture.text
        assert lecture.json()["design_profile"] is None

        # 2. Toujours previsualisable (ne plante pas).
        generation = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert generation.status_code == 200, generation.text

        # 3. Recoit alors proprement un profil valide.
        assert generation.json()["design_profile"] is not None
        assert generation.json()["design_profile"]["design_family"] in DESIGN_FAMILIES


# ---------- E. Isolation tenant ----------

def test_generer_le_profil_dun_artisan_ne_touche_pas_un_autre_artisan():
    headers, _ = _admin_headers()
    artisan_a = _creer_artisan("peintre")
    artisan_b = _creer_artisan("peintre")

    with TestClient(app) as client:
        res_a = client.post(f"/admin/api/artisans/{artisan_a}/site/generate", headers=headers)
        assert res_a.status_code == 200, res_a.text

        avant_b = client.get(f"/admin/api/artisans/{artisan_b}/site", headers=headers)
        assert avant_b.status_code == 200, avant_b.text
        assert avant_b.json()["design_profile"] is None, "generer le site de A ne doit jamais creer un profil pour B"

        res_b = client.post(f"/admin/api/artisans/{artisan_b}/site/generate", headers=headers)
        assert res_b.status_code == 200, res_b.text

        apres_a = client.get(f"/admin/api/artisans/{artisan_a}/site", headers=headers)
        assert apres_a.json()["design_profile"] == res_a.json()["design_profile"], (
            "generer le site de B ne doit jamais modifier le profil deja persiste de A"
        )


# ---------- F. Aucune donnee fabriquee : omission de section ----------

def test_resolve_visible_sections_omet_les_sections_sans_donnees_reelles():
    section_order = ["hero", "trust", "services", "gallery", "reviews", "service_area", "cta"]

    aucune_donnee = {
        "services": False, "avis": False, "stats": False, "ville": False,
        "assurance_decennale_nom": False, "photos": False, "realisations": False,
        "photos_avant_apres": False,
    }
    visibles = resolve_visible_sections("trust_led", aucune_donnee)
    # "hero" et "cta" n'ont aucune exigence : toujours presents. Tout le
    # reste doit etre omis, jamais rempli avec des donnees inventees.
    assert "hero" in visibles
    assert "cta" in visibles
    assert "trust" not in visibles
    assert "services" not in visibles
    assert "gallery" not in visibles
    assert "reviews" not in visibles
    assert "service_area" not in visibles

    toutes_donnees = {
        "services": True, "avis": True, "stats": True, "ville": True,
        "assurance_decennale_nom": True, "photos": True, "realisations": True,
        "photos_avant_apres": True,
    }
    visibles_completes = resolve_visible_sections("trust_led", toutes_donnees)
    assert set(visibles_completes) == {"hero", "trust", "services", "featured_project", "about", "gallery", "reviews", "service_area", "cta"}
