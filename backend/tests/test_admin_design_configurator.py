"""Lot 4 : configurateur Admin des sites vitrines V2 (preferences, alternative
de design, comparaison, adoption). Voir app/admin_service.py (generate_design_
candidate / adopt_design_candidate / abandon_design_candidate) et
generator/design_selector.py::select_candidate_design_profile.

Invariant central teste partout ici : le design_profile actif ("current")
n'est JAMAIS modifie tant que l'Admin n'a pas explicitement adopte une
alternative - et l'adoption ne publie jamais automatiquement le site.
"""
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import AdminUser, Artisan, SiteVitrine
from app.security import create_access_token
from generator.design_registry import DESIGN_FAMILIES
from generator.v3.grammar import ART_DIRECTIONS


def _admin_headers() -> dict:
    db = SessionLocal()
    try:
        suffixe = uuid4().hex
        admin_row = AdminUser(
            email=f"design-config-admin-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            nom="Admin Configurateur",
            actif=True,
        )
        db.add(admin_row)
        db.commit()
        db.refresh(admin_row)
        admin_id = admin_row.id
    finally:
        db.close()
    return {"Authorization": f"Bearer {create_access_token(admin_id, 'admin')}"}


def _creer_artisan(metier: str = "plombier") -> int:
    suffixe = uuid4().hex
    db = SessionLocal()
    try:
        artisan = Artisan(
            slug=f"design-config-{suffixe}",
            nom_entreprise=f"Design Config {suffixe}",
            metier=metier,
            email=f"design-config-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
            ville="Lyon",
        )
        db.add(artisan)
        db.commit()
        db.refresh(artisan)
        return artisan.id
    finally:
        db.close()


def _site(artisan_id: int) -> SiteVitrine:
    db = SessionLocal()
    try:
        return db.query(SiteVitrine).filter(SiteVitrine.artisan_id == artisan_id).first()
    finally:
        db.close()


# ---------- Lecture / etat initial ----------

def test_site_sans_candidate_expose_un_etat_honnete():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        gen = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        assert gen.status_code == 200, gen.text
        data = gen.json()
        assert data["candidate_design_profile"] is None
        assert data["candidate_preview_disponible"] is False
        assert data["design_preferences"]["engine_version"] == "v3"
        assert data["design_profile"]["art_direction"] in ART_DIRECTIONS
        assert isinstance(data["sections_disponibles"], list) and len(data["sections_disponibles"]) >= 8


def test_generer_candidate_avant_toute_preview_est_refuse():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        resp = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        assert resp.status_code == 409


# ---------- Creation de candidate ----------

def test_candidate_est_reellement_differente_du_current():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        gen = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers).json()
        current_signature = gen["design_profile"]["design_signature"]
        cand = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        assert cand.status_code == 200, cand.text
        body = cand.json()
        assert body["profile"]["design_signature"] != current_signature
        assert body["distinct"] is True


def test_preference_famille_est_respectee():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        cand = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"preferred_family": "signature"}, headers=headers,
        )
        assert cand.status_code == 200
        assert cand.json()["profile"]["design_family"] == "signature"


def test_garder_la_meme_famille_donne_une_structure_differente():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        gen = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers).json()
        current = gen["design_profile"]
        cand = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"keep_current_family": True}, headers=headers,
        ).json()
        assert cand["profile"]["art_direction"] == current["art_direction"]
        axes = ("header_system", "hero_system", "page_silhouette", "services_composition", "project_showcase")
        assert any(cand["profile"][axe] != current[axe] for axe in axes)


def test_famille_inconnue_est_rejetee_sans_toucher_a_rien():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        resp = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"preferred_family": "pas-une-famille"}, headers=headers,
        )
        assert resp.status_code == 422
        detail = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers).json()
        assert detail["candidate_design_profile"] is None


def test_overrides_avances_appliques_et_valides():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        cand = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"overrides": {"palette": "palette-2", "hero_variant": "fullscreen"}}, headers=headers,
        )
        assert cand.status_code == 200
        profile = cand.json()["profile"]
        assert profile["palette"] == "palette-2" and profile["hero_variant"] == "fullscreen"


def test_override_valeur_invalide_est_rejete():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        resp = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"overrides": {"hero_variant": "pas-un-variant"}}, headers=headers,
        )
        assert resp.status_code == 422


def test_override_champ_inconnu_est_rejete():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        resp = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"overrides": {"design_family": "impact"}}, headers=headers,
        )
        assert resp.status_code == 422


# ---------- Persistance ----------

def test_candidate_survit_au_refresh():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        cand = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers).json()
        # Nouvelle requete independante (simule un refresh de page)
        refreshed = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers).json()
        assert refreshed["candidate_design_profile"] == cand["profile"]
        assert refreshed["candidate_preview_disponible"] is True


def test_preferences_persistent_et_sont_validees():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        resp = client.patch(
            f"/admin/api/artisans/{artisan_id}/site/design/preferences",
            json={"preferred_family": "technique", "density": "spacious"}, headers=headers,
        )
        assert resp.status_code == 200
        refreshed = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers).json()
        preferences = refreshed["design_preferences"]
        assert preferences["preferred_family"] == "technique"
        assert preferences["density"] == "spacious"

        bad = client.patch(
            f"/admin/api/artisans/{artisan_id}/site/design/preferences",
            json={"density": "pas-une-densite"}, headers=headers,
        )
        assert bad.status_code == 422


# ---------- Regenerate ----------

def test_regenerer_sans_candidate_est_refuse():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        resp = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate/regenerate", json={}, headers=headers)
        assert resp.status_code == 409


def test_regenerer_produit_une_candidate_differente_de_la_precedente():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        first = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"preferred_family": "impact"}, headers=headers,
        ).json()
        second = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate/regenerate",
            json={"preferred_family": "impact"}, headers=headers,
        ).json()
        assert second["profile"]["design_signature"] != first["profile"]["design_signature"]
        assert second["profile"]["design_family"] == "impact"


# ---------- Abandon ----------

def test_abandon_supprime_la_candidate_sans_toucher_au_current():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        gen = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers).json()
        current = gen["design_profile"]
        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        abandon = client.delete(f"/admin/api/artisans/{artisan_id}/site/design/candidate", headers=headers)
        assert abandon.status_code == 200
        body = abandon.json()
        assert body["candidate_design_profile"] is None
        assert body["candidate_preview_disponible"] is False
        assert body["design_profile"] == current

        preview_candidate = client.get(f"/admin/api/artisans/{artisan_id}/site/preview/candidate", headers=headers)
        assert preview_candidate.status_code == 404


# ---------- Adoption ----------

def test_current_inchange_avant_adopt():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        gen = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers).json()
        current_before = gen["design_profile"]
        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={"preferred_family": "signature"}, headers=headers)
        still = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers).json()
        assert still["design_profile"] == current_before


def test_adopt_remplace_current_et_vide_la_candidate():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        cand = client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"preferred_family": "signature"}, headers=headers,
        ).json()
        adopt = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate/adopt", headers=headers)
        assert adopt.status_code == 200, adopt.text
        body = adopt.json()
        assert body["design_profile"] == cand["profile"]
        assert body["candidate_design_profile"] is None
        assert body["candidate_preview_disponible"] is False

        preview = client.get(f"/admin/api/artisans/{artisan_id}/site/preview", headers=headers)
        assert 'family-signature' in preview.text

        preview_candidate = client.get(f"/admin/api/artisans/{artisan_id}/site/preview/candidate", headers=headers)
        assert preview_candidate.status_code == 404


def test_adopter_sans_candidate_est_refuse():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        resp = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate/adopt", headers=headers)
        assert resp.status_code == 409


def test_adopter_un_site_deja_pret_ne_le_publie_jamais_et_le_repasse_en_validation():
    """Point critique du brief (sections 17-18) : adopter une alternative sur
    un site deja "pret" ne doit jamais le publier automatiquement, et doit le
    faire repasser par un etat necessitant re-validation (ici : "genere",
    exactement comme n'importe quelle regeneration - voir admin_site_update)."""
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        ready = client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)
        assert ready.status_code == 200
        assert ready.json()["statut"] == "pret"

        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        adopt = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate/adopt", headers=headers)
        assert adopt.status_code == 200
        assert adopt.json()["statut"] == "genere"  # jamais "publie", jamais laisse "pret" sans re-validation


def test_adopter_un_site_publie_ne_change_jamais_le_statut_publie_directement():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        client.post(f"/admin/api/artisans/{artisan_id}/site/ready", headers=headers)
        publish = client.patch(
            f"/admin/api/artisans/{artisan_id}/site",
            json={"domaine": "artisan-test-lot4.fr", "url_publique": "https://artisan-test-lot4.fr"},
            headers=headers,
        )
        assert publish.status_code == 200
        published = client.post(f"/admin/api/artisans/{artisan_id}/site/publish", headers=headers)
        assert published.status_code == 200
        assert published.json()["statut"] == "publie"
        published_profile = published.json()["design_profile"]

        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={"preferred_family": "technique"}, headers=headers)
        # Le site publie reste inchange tant que l'alternative n'est pas adoptee.
        still_published = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers).json()
        assert still_published["statut"] == "publie"
        assert still_published["design_profile"] == published_profile

        adopt = client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate/adopt", headers=headers)
        assert adopt.status_code == 200
        assert adopt.json()["statut"] != "publie"  # jamais republie automatiquement
        assert adopt.json()["design_profile"]["design_family"] == "technique"


# ---------- Preview candidate : isolation ----------

def test_preview_candidate_est_isolee_de_la_preview_current():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        gen = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers).json()
        current_direction = gen["design_profile"]["art_direction"]
        autre_direction = next(value for value in ART_DIRECTIONS if value != current_direction)
        client.post(
            f"/admin/api/artisans/{artisan_id}/site/design/candidate",
            json={"engine_version": "v3", "preferred_direction": autre_direction}, headers=headers,
        )
        current_preview = client.get(f"/admin/api/artisans/{artisan_id}/site/preview", headers=headers)
        candidate_preview = client.get(f"/admin/api/artisans/{artisan_id}/site/preview/candidate", headers=headers)
        assert f'direction-{current_direction}' in current_preview.text
        assert f'direction-{autre_direction}' in candidate_preview.text
        assert current_preview.text != candidate_preview.text


def test_preview_candidate_sans_admin_est_refusee():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        sans_auth = client.get(f"/admin/api/artisans/{artisan_id}/site/preview/candidate")
        assert sans_auth.status_code == 401


def test_preview_candidate_cross_tenant_avec_token_de_preview_est_refusee():
    """Un jeton de preview limite a un artisan ne doit jamais donner acces a
    la candidate d'un AUTRE artisan (isolation multi-tenant, brief section 46)."""
    headers = _admin_headers()
    artisan_a = _creer_artisan()
    artisan_b = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_a}/site/generate", headers=headers)
        client.post(f"/admin/api/artisans/{artisan_a}/site/design/candidate", json={}, headers=headers)
        client.post(f"/admin/api/artisans/{artisan_b}/site/generate", headers=headers)
        client.post(f"/admin/api/artisans/{artisan_b}/site/design/candidate", json={}, headers=headers)

        session = client.post(f"/admin/api/artisans/{artisan_a}/site/preview-session/candidate", headers=headers)
        assert session.status_code == 200
        token = session.json()["url"].split("token=")[1].split("&")[0]

        client.cookies.clear()
        acces_a = client.get(f"/admin/api/artisans/{artisan_a}/site/preview/open?token={token}&candidate=1", follow_redirects=False)
        assert acces_a.status_code in (200, 303)

        acces_b = client.get(
            f"/admin/api/artisans/{artisan_b}/site/preview/candidate",
            cookies=client.cookies,
        )
        assert acces_b.status_code == 403


def test_preview_candidate_ne_cree_jamais_de_vrai_prospect():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        slug = client.get(f"/admin/api/artisans/{artisan_id}", headers=headers).json()["slug"]
        sink = client.post(
            f"/admin/preview-api/pub/{slug}/demande-devis",
            json={"nom": "Faux Client", "message": "Test"},
            headers=headers,
        )
        assert sink.status_code == 200
        assert "aucune demande" in sink.json()["detail"].lower()


def test_aucun_contenu_invente_dans_la_candidate():
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers)
        client.post(f"/admin/api/artisans/{artisan_id}/site/design/candidate", json={}, headers=headers)
        preview = client.get(f"/admin/api/artisans/{artisan_id}/site/preview/candidate", headers=headers)
        # "intervention rapide" fait deliberement partie de la tagline par
        # defaut du theme plombier (generator/themes.py) - contenu produit
        # existant, pas invente par ce lot. On verifie ici l'absence de
        # contenu invente PAR le configurateur (faux avis/experience/certif).
        forbidden = ("Devis gratuit", "années d'expérience", "certifié RGE")
        assert all(text not in preview.text for text in forbidden)


# ---------- Compatibilite ancien site ----------

def test_site_ancien_sans_candidate_ni_preference_reste_lisible():
    """Un SiteVitrine cree avant ce lot (candidate_design_profile et
    design_preferences NULL en base) doit continuer a fonctionner sans
    aucun recalcul non demande (backward compatibility, brief section 36)."""
    headers = _admin_headers()
    artisan_id = _creer_artisan()
    with TestClient(app) as client:
        gen = client.post(f"/admin/api/artisans/{artisan_id}/site/generate", headers=headers).json()

    db = SessionLocal()
    try:
        site = db.query(SiteVitrine).filter(SiteVitrine.artisan_id == artisan_id).first()
        site.design_preferences = None
        db.commit()
        db.refresh(site)
        assert site.candidate_design_profile is None
        assert site.design_preferences is None
        original_profile = dict(site.design_profile)
    finally:
        db.close()

    with TestClient(app) as client:
        refreshed = client.get(f"/admin/api/artisans/{artisan_id}/site", headers=headers)
        assert refreshed.status_code == 200
        body = refreshed.json()
        assert body["design_profile"] == original_profile
        assert body["candidate_design_profile"] is None
        assert body["design_preferences"] is None
