from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models import Artisan, Contrat, Facture
from app.routers.contrats import _ajouter_mois
from app.scheduler import _traiter_contrats


def _artisan(client: TestClient, plan: str, prefix: str) -> tuple[dict, int]:
    email = f"{prefix}-{uuid4().hex}@e2e-test.fr"
    inscription = client.post("/auth/register", json={
        "nom_entreprise": prefix,
        "metier": "plombier",
        "email": email,
        "password": "TestPass123!",
    })
    assert inscription.status_code == 201, inscription.text
    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.email == email).one()
        artisan.plan = plan
        artisan.subscription_status = "inactive"
        db.commit()
        artisan_id = artisan.id
    finally:
        db.close()
    return {"Authorization": f"Bearer {inscription.json()['access_token']}"}, artisan_id


def _client(client: TestClient, headers: dict, prefix: str, *, avec_email: bool = True) -> dict:
    payload = {"nom": f"Client {prefix}"}
    if avec_email:
        payload["email"] = f"client-{uuid4().hex}@e2e-test.fr"
    response = client.post("/clients", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _creer_contrat(
    client: TestClient,
    headers: dict,
    client_id: int,
    *,
    titre: str = "Entretien chaudière",
    montant_ht: float = 120,
    taux_tva: float = 10,
    frequence: str = "mensuel",
    prochaine_echeance: str = "2026-01-31",
):
    return client.post("/contrats", headers=headers, json={
        "client_id": client_id,
        "titre": titre,
        "montant_ht": montant_ht,
        "taux_tva": taux_tva,
        "frequence": frequence,
        "prochaine_echeance": prochaine_echeance,
    })


def _run() -> SimpleNamespace:
    return SimpleNamespace(
        nb_contrats_factures=0,
        nb_emails_envoyes=0,
        nb_emails_non_configures=0,
        nb_erreurs=0,
    )


def test_crud_contrats_respecte_les_plans_et_les_validations():
    with TestClient(app) as client:
        for plan in ("gratuit", "essentiel"):
            headers, _ = _artisan(client, plan, f"contrat-refus-{plan}")
            assert client.get("/contrats", headers=headers).status_code == 402

        for plan in ("pro", "business"):
            headers, _ = _artisan(client, plan, f"contrat-crud-{plan}")
            contact = _client(client, headers, plan)
            creation = _creer_contrat(client, headers, contact["id"])
            assert creation.status_code == 201, creation.text
            contrat_id = creation.json()["id"]

            liste = client.get("/contrats", headers=headers)
            assert liste.status_code == 200, liste.text
            assert [item["id"] for item in liste.json()] == [contrat_id]

            modification = client.patch(f"/contrats/{contrat_id}", headers=headers, json={
                "titre": "Maintenance annuelle",
                "montant_ht": 240,
                "taux_tva": 20,
                "frequence": "annuel",
                "prochaine_echeance": "2027-02-28",
            })
            assert modification.status_code == 200, modification.text
            assert modification.json()["titre"] == "Maintenance annuelle"
            assert modification.json()["montant_ht"] == 240
            assert modification.json()["frequence"] == "annuel"

            suppression = client.delete(f"/contrats/{contrat_id}", headers=headers)
            assert suppression.status_code == 204, suppression.text
            assert client.get("/contrats", headers=headers).json() == []

        headers, _ = _artisan(client, "pro", "contrat-validation")
        contact = _client(client, headers, "validation")
        for overrides in (
            {"titre": "   "},
            {"montant_ht": 0},
            {"montant_ht": -1},
            {"taux_tva": -1},
            {"taux_tva": 101},
            {"frequence": "hebdomadaire"},
        ):
            payload = {
                "client_id": contact["id"],
                "titre": "Valide",
                "montant_ht": 100,
                "taux_tva": 20,
                "frequence": "mensuel",
                "prochaine_echeance": "2026-09-01",
                **overrides,
            }
            refus = client.post("/contrats", headers=headers, json=payload)
            assert refus.status_code == 422, refus.text


def test_isolation_tenant_sur_toutes_les_mutations_de_contrat():
    with TestClient(app) as client:
        artisan_a, _ = _artisan(client, "pro", "contrat-tenant-a")
        artisan_b, _ = _artisan(client, "business", "contrat-tenant-b")
        contact_b = _client(client, artisan_b, "tenant-b")
        contrat_b = _creer_contrat(client, artisan_b, contact_b["id"])
        assert contrat_b.status_code == 201, contrat_b.text
        contrat_id = contrat_b.json()["id"]

        assert client.get("/contrats", headers=artisan_a).json() == []
        assert client.patch(f"/contrats/{contrat_id}", headers=artisan_a, json={"titre": "Intrusion"}).status_code == 404
        assert client.post(f"/contrats/{contrat_id}/generer", headers=artisan_a).status_code == 404
        assert client.delete(f"/contrats/{contrat_id}", headers=artisan_a).status_code == 404
        assert len(client.get("/contrats", headers=artisan_b).json()) == 1


def test_generation_manuelle_cree_une_facture_honnete_et_avance_echeance(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", None)
    with TestClient(app) as client:
        headers, artisan_id = _artisan(client, "pro", "contrat-generation")
        contact = _client(client, headers, "generation")
        creation = _creer_contrat(
            client,
            headers,
            contact["id"],
            montant_ht=900,
            taux_tva=20,
            prochaine_echeance="2026-01-31",
        )
        assert creation.status_code == 201, creation.text
        contrat_id = creation.json()["id"]

        generation = client.post(f"/contrats/{contrat_id}/generer", headers=headers)
        assert generation.status_code == 200, generation.text
        resultat = generation.json()
        assert resultat["nb_factures_generees"] == 1
        assert resultat["prochaine_echeance"] == "2026-02-28"
        assert resultat["email_statut"] == "non_configure"
        assert resultat["facture_statut"] == "brouillon"
        assert "Facture générée" in resultat["message"]
        assert "n'a pas été envoyé" in resultat["message"]

        db = SessionLocal()
        try:
            factures = db.query(Facture).filter(
                Facture.artisan_id == artisan_id,
                Facture.contrat_id == contrat_id,
            ).all()
            assert len(factures) == 1
            facture = factures[0]
            assert facture.id == resultat["facture_id"]
            assert facture.numero == resultat["facture_numero"]
            assert facture.statut == "brouillon"
            assert facture.date_envoi is None
            assert float(facture.montant_ht) == 900
            assert float(facture.montant_ttc) == 1080
            assert float(facture.taux_tva) == 20
            assert facture.contrat_id == contrat_id
            assert len(facture.lignes) == 1
        finally:
            db.close()

        factures_api = client.get("/factures", headers=headers)
        assert factures_api.status_code == 200, factures_api.text
        facture_api = next(item for item in factures_api.json() if item["id"] == resultat["facture_id"])
        assert facture_api["contrat_id"] == contrat_id


def test_contrat_inactif_ne_peut_pas_generer_meme_manuellement():
    with TestClient(app) as client:
        headers, _ = _artisan(client, "pro", "contrat-inactif")
        contact = _client(client, headers, "inactif")
        creation = _creer_contrat(client, headers, contact["id"])
        contrat_id = creation.json()["id"]
        assert client.patch(f"/contrats/{contrat_id}", headers=headers, json={"statut": "suspendu"}).status_code == 200
        refus = client.post(f"/contrats/{contrat_id}/generer", headers=headers)
        assert refus.status_code == 400, refus.text


def test_scheduler_pro_genere_une_seule_facture_par_echeance_et_ignore_essentiel(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", None)
    with TestClient(app) as client:
        headers_pro, artisan_pro_id = _artisan(client, "pro", "contrat-scheduler-pro")
        contact_pro = _client(client, headers_pro, "scheduler-pro")
        creation_pro = _creer_contrat(
            client,
            headers_pro,
            contact_pro["id"],
            prochaine_echeance=date.today().isoformat(),
        )
        contrat_pro_id = creation_pro.json()["id"]
        creation_suspendue = _creer_contrat(
            client,
            headers_pro,
            contact_pro["id"],
            titre="Contrat suspendu",
            prochaine_echeance=date.today().isoformat(),
        )
        contrat_suspendu_id = creation_suspendue.json()["id"]
        suspension = client.patch(
            f"/contrats/{contrat_suspendu_id}",
            headers=headers_pro,
            json={"statut": "suspendu"},
        )
        assert suspension.status_code == 200, suspension.text

        headers_essentiel, artisan_essentiel_id = _artisan(client, "pro", "contrat-scheduler-essentiel")
        contact_essentiel = _client(client, headers_essentiel, "scheduler-essentiel")
        creation_essentiel = _creer_contrat(
            client,
            headers_essentiel,
            contact_essentiel["id"],
            prochaine_echeance=date.today().isoformat(),
        )
        contrat_essentiel_id = creation_essentiel.json()["id"]

        db = SessionLocal()
        try:
            artisan_pro = db.query(Artisan).filter(Artisan.id == artisan_pro_id).one()
            artisan_essentiel = db.query(Artisan).filter(Artisan.id == artisan_essentiel_id).one()
            artisan_essentiel.plan = "essentiel"
            db.commit()

            run_pro = _run()
            _traiter_contrats(db, artisan_pro, run_pro)
            assert run_pro.nb_contrats_factures == 1
            assert run_pro.nb_emails_non_configures == 1
            assert db.query(Facture).filter(Facture.contrat_id == contrat_pro_id).count() == 1
            assert db.query(Facture).filter(Facture.contrat_id == contrat_suspendu_id).count() == 0

            _traiter_contrats(db, artisan_pro, run_pro)
            assert run_pro.nb_contrats_factures == 1
            assert db.query(Facture).filter(Facture.contrat_id == contrat_pro_id).count() == 1

            run_essentiel = _run()
            _traiter_contrats(db, artisan_essentiel, run_essentiel)
            assert run_essentiel.nb_contrats_factures == 0
            assert db.query(Facture).filter(Facture.contrat_id == contrat_essentiel_id).count() == 0
        finally:
            db.close()


def test_calcul_echeances_preserve_les_fins_de_mois_et_les_frequences():
    assert _ajouter_mois(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert _ajouter_mois(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert _ajouter_mois(date(2024, 2, 29), 1) == date(2024, 3, 31)
    assert _ajouter_mois(date(2026, 8, 31), 3) == date(2026, 11, 30)
    assert _ajouter_mois(date(2024, 2, 29), 12) == date(2025, 2, 28)
