"""Les interventions rattachees a un chantier.

`Evenement.chantier_id` existait depuis l'origine, mais aucune route ne
permettait de demander « les interventions de CE chantier » : /planning repond
par PERIODE. La fiche de chantier n'avait donc aucun moyen honnete de les
afficher - il aurait fallu telecharger le planning entier et filtrer cote
client, exactement ce que l'audit reproche ailleurs.

Ce test verifie surtout ce qui compte pour une route nouvelle : l'isolation.
Un chantier d'un autre compte doit donner 404, et jamais une liste vide qui
laisserait croire qu'il n'y a rien.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Artisan


def _compte(client: TestClient, prefixe: str) -> dict:
    email = f"{prefixe}-{uuid4().hex}@e2e-test.fr"
    inscription = client.post("/auth/register", json={
        "nom_entreprise": prefixe, "metier": "plombier",
        "email": email, "password": "TestPass123!",
    })
    assert inscription.status_code == 201, inscription.text
    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.email == email).one()
        artisan.plan = "pro"
        artisan.subscription_status = "active"
        db.commit()
    finally:
        db.close()
    return {"Authorization": f"Bearer {inscription.json()['access_token']}"}


def _chantier(client: TestClient, headers: dict) -> int:
    contact = client.post("/clients", headers=headers, json={"nom": f"Client {uuid4().hex[:6]}"})
    assert contact.status_code == 201, contact.text
    chantier = client.post("/chantiers", headers=headers, json={
        "client_id": contact.json()["id"], "titre": "Villa", "budget": 10000,
    })
    assert chantier.status_code == 201, chantier.text
    return chantier.json()["id"]


def _evenement(client: TestClient, headers: dict, titre: str, chantier_id=None, jours=0) -> int:
    quand = datetime.now(timezone.utc) + timedelta(days=jours)
    reponse = client.post("/evenements", headers=headers, json={
        "titre": titre, "type": "intervention",
        "date_debut": quand.isoformat(), "chantier_id": chantier_id,
    })
    assert reponse.status_code == 201, reponse.text
    return reponse.json()["id"]


def test_seules_les_interventions_du_chantier_sont_renvoyees():
    with TestClient(app) as client:
        headers = _compte(client, "interv")
        chantier_id = _chantier(client, headers)
        autre_chantier = _chantier(client, headers)

        _evenement(client, headers, "Pose des menuiseries", chantier_id, jours=2)
        _evenement(client, headers, "Metre initial", chantier_id, jours=-30)
        _evenement(client, headers, "Sur l'autre chantier", autre_chantier)
        _evenement(client, headers, "Sans chantier", None)

        reponse = client.get(f"/chantiers/{chantier_id}/interventions", headers=headers)
        assert reponse.status_code == 200, reponse.text
        titres = [e["titre"] for e in reponse.json()]
        assert titres == ["Pose des menuiseries", "Metre initial"], (
            "seules les interventions de ce chantier, la plus recente d'abord"
        )

        # La periode n'entre pas en jeu : un evenement d'il y a un mois compte
        # autant qu'un rendez-vous de la semaine prochaine. C'est justement ce
        # que /planning ne permettait pas de demander.
        assert "Metre initial" in titres


def test_un_chantier_sans_intervention_repond_une_liste_vide():
    with TestClient(app) as client:
        headers = _compte(client, "interv-vide")
        chantier_id = _chantier(client, headers)
        reponse = client.get(f"/chantiers/{chantier_id}/interventions", headers=headers)
        assert reponse.status_code == 200
        assert reponse.json() == []


def test_le_chantier_d_un_autre_compte_donne_404():
    # Le point qui compte pour une route nouvelle. Une liste vide laisserait
    # croire que le chantier existe et n'a rien ; 404 dit qu'il n'est pas a
    # vous - et ne revele pas non plus qu'il existe ailleurs.
    with TestClient(app) as client:
        moi = _compte(client, "interv-moi")
        autrui = _compte(client, "interv-autrui")
        chantier_autrui = _chantier(client, autrui)
        _evenement(client, autrui, "Confidentiel", chantier_autrui)

        reponse = client.get(f"/chantiers/{chantier_autrui}/interventions", headers=moi)
        assert reponse.status_code == 404, reponse.text


def test_sans_jeton_la_route_refuse():
    with TestClient(app) as client:
        headers = _compte(client, "interv-anon")
        chantier_id = _chantier(client, headers)
        assert client.get(f"/chantiers/{chantier_id}/interventions").status_code in (401, 403)
