from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Artisan


def _artisan_essentiel(client: TestClient, prefix: str):
    email = f"{prefix.lower().replace(' ', '-')}-{uuid4().hex}@e2e-test.fr"
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
        artisan.plan = "essentiel"
        artisan.subscription_status = "inactive"
        db.commit()
    finally:
        db.close()
    return {"Authorization": f"Bearer {inscription.json()['access_token']}"}


def _client(client: TestClient, headers: dict, nom: str):
    response = client.post("/clients", headers=headers, json={"nom": nom})
    assert response.status_code == 201, response.text
    return response.json()


def test_edition_chantier_recalcul_planning_isolation_et_verrou_financier():
    with TestClient(app) as client:
        artisan_a = _artisan_essentiel(client, "Chantiers A")
        artisan_b = _artisan_essentiel(client, "Chantiers B")
        client_a1 = _client(client, artisan_a, "Client initial")
        client_a2 = _client(client, artisan_a, "Client final")
        client_b = _client(client, artisan_b, "Client autre artisan")

        creation = client.post("/chantiers", headers=artisan_a, json={
            "client_id": client_a1["id"], "titre": "Chantier avant édition",
            "adresse": "1 rue Initiale", "date_debut": "2026-08-30",
        })
        assert creation.status_code == 201, creation.text
        assert creation.json()["budget"] is None
        chantier_id = creation.json()["id"]

        edition = client.patch(f"/chantiers/{chantier_id}", headers=artisan_a, json={
            "client_id": client_a2["id"], "titre": "Chantier édité",
            "adresse": "2 rue Finale", "date_debut": "2026-08-31", "budget": 1500,
        })
        assert edition.status_code == 200, edition.text
        assert edition.json()["client_id"] == client_a2["id"]
        assert edition.json()["titre"] == "Chantier édité"
        assert edition.json()["adresse"] == "2 rue Finale"
        assert edition.json()["date_debut"] == "2026-08-31"
        assert edition.json()["budget"] == 1500

        client_hors_tenant = client.patch(
            f"/chantiers/{chantier_id}", headers=artisan_a, json={"client_id": client_b["id"]},
        )
        assert client_hors_tenant.status_code == 404

        planning = client.get(
            "/planning", headers=artisan_a, params={"debut": "2026-08-30", "fin": "2026-08-31"},
        )
        assert planning.status_code == 200, planning.text
        debut_chantier = [i for i in planning.json() if i["type"] == "chantier_debut"]
        assert len(debut_chantier) == 1
        assert debut_chantier[0]["reference_id"] == chantier_id
        assert debut_chantier[0]["chantier_id"] == chantier_id
        assert debut_chantier[0]["titre"] == "Début chantier : Chantier édité"
        assert debut_chantier[0]["date"].startswith("2026-08-31")

        planning_autre_tenant = client.get(
            "/planning", headers=artisan_b, params={"debut": "2026-08-30", "fin": "2026-08-31"},
        )
        assert planning_autre_tenant.status_code == 200
        assert all(i.get("chantier_id") != chantier_id for i in planning_autre_tenant.json())

        evenement = client.post("/evenements", headers=artisan_a, json={
            "titre": "Rendez-vous conservé", "type": "rdv", "date_debut": "2026-08-31T10:00:00Z",
            "client_id": client_a2["id"], "chantier_id": chantier_id,
        })
        assert evenement.status_code == 201, evenement.text
        planning = client.get(
            "/planning", headers=artisan_a, params={"debut": "2026-08-31", "fin": "2026-08-31"},
        )
        assert any(i["type"] == "rdv" and i["reference_id"] == evenement.json()["id"] for i in planning.json())

        depense = client.post(f"/chantiers/{chantier_id}/depenses", headers=artisan_a, json={
            "libelle": "Matériaux initiaux", "montant": 3000, "date_depense": "2026-08-30",
        })
        assert depense.status_code == 201, depense.text
        depense_id = depense.json()["id"]
        depense_editee = client.patch(
            f"/chantiers/{chantier_id}/depenses/{depense_id}", headers=artisan_a,
            json={"libelle": "Matériaux corrigés", "montant": 300, "date_depense": "2026-08-31"},
        )
        assert depense_editee.status_code == 200, depense_editee.text
        assert depense_editee.json()["montant"] == 300

        heure = client.post(f"/chantiers/{chantier_id}/heures", headers=artisan_a, json={
            "nom_intervenant": "Artisan", "date_travail": "2026-08-30",
            "duree_heures": 1, "taux_horaire": 35, "note": "Préparation",
        })
        assert heure.status_code == 201, heure.text
        heure_id = heure.json()["id"]
        heure_editee = client.patch(
            f"/chantiers/{chantier_id}/heures/{heure_id}", headers=artisan_a,
            json={"duree_heures": 2, "date_travail": "2026-08-31", "note": "Pose"},
        )
        assert heure_editee.status_code == 200, heure_editee.text
        assert heure_editee.json()["duree_heures"] == 2
        assert heure_editee.json()["cout"] == 70

        recalcule = client.get(f"/chantiers/{chantier_id}", headers=artisan_a)
        assert recalcule.status_code == 200, recalcule.text
        assert recalcule.json()["total_depenses"] == 300
        assert recalcule.json()["total_heures"] == 2
        assert recalcule.json()["cout_main_oeuvre"] == 70
        assert recalcule.json()["marge_estimee"] == 1130

        for url, payload in (
            (f"/chantiers/{chantier_id}", {"titre": "Intrusion"}),
            (f"/chantiers/{chantier_id}/depenses/{depense_id}", {"montant": 1}),
            (f"/chantiers/{chantier_id}/heures/{heure_id}", {"duree_heures": 1}),
        ):
            interdit = client.patch(url, headers=artisan_b, json=payload)
            assert interdit.status_code == 404, interdit.text

        rapport = client.get(f"/chantiers/{chantier_id}/rapport-pdf", headers=artisan_a)
        assert rapport.status_code == 200, rapport.text
        assert rapport.headers["content-type"] == "application/pdf"
        assert rapport.content.startswith(b"%PDF")

        termine = client.patch(f"/chantiers/{chantier_id}", headers=artisan_a, json={"statut": "termine"})
        assert termine.status_code == 200, termine.text
        assert termine.json()["progression"] == 100

        cloture = client.post(f"/chantiers/{chantier_id}/cloturer", headers=artisan_a, json={
            "generer_facture_finale": True, "demander_avis": False,
        })
        assert cloture.status_code == 200, cloture.text
        assert cloture.json()["facture_finale"] is not None
        assert cloture.json()["chantier"]["statut"] == "facture"
        assert cloture.json()["chantier"]["progression"] == 100
        assert cloture.json()["chantier"]["finances_verrouillees"] is True
        assert any(t["statut"] == "a_faire" for t in cloture.json()["chantier"]["taches"])

        message_verrou = "Les données financières d'un chantier facturé sont verrouillées."
        mutations_financieres = (
            client.patch(f"/chantiers/{chantier_id}", headers=artisan_a, json={"budget": 1600}),
            client.patch(f"/chantiers/{chantier_id}", headers=artisan_a, json={"client_id": client_a1["id"]}),
            client.patch(f"/chantiers/{chantier_id}/depenses/{depense_id}", headers=artisan_a, json={"montant": 200}),
            client.post(f"/chantiers/{chantier_id}/depenses", headers=artisan_a, json={
                "libelle": "Après facture", "montant": 10, "date_depense": "2026-09-01",
            }),
            client.patch(f"/chantiers/{chantier_id}/heures/{heure_id}", headers=artisan_a, json={"duree_heures": 3}),
            client.post(f"/chantiers/{chantier_id}/heures", headers=artisan_a, json={
                "nom_intervenant": "Artisan", "date_travail": "2026-09-01", "duree_heures": 1,
            }),
            client.delete(f"/chantiers/{chantier_id}/heures/{heure_id}", headers=artisan_a),
        )
        for refus in mutations_financieres:
            assert refus.status_code == 400, refus.text
            assert refus.json()["detail"] == message_verrou

        edition_non_financiere = client.patch(f"/chantiers/{chantier_id}", headers=artisan_a, json={
            "titre": "Chantier facturé archivé", "adresse": "3 rue Archives", "date_debut": "2026-09-01",
        })
        assert edition_non_financiere.status_code == 200, edition_non_financiere.text
        assert edition_non_financiere.json()["budget"] == 1500
        assert edition_non_financiere.json()["total_depenses"] == 300
        assert edition_non_financiere.json()["total_heures"] == 2
        assert edition_non_financiere.json()["progression"] == 100
