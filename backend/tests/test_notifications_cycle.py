"""Le cycle d'une notification : la lire, la reporter, la retrouver.

Le centre de notifications melange deux natures, et c'est assume : des
evenements PERSISTANTS (table notifications, marquables comme lus) et des
alertes CALCULEES a chaque appel - devis a relancer, facture impayee,
conformite qui expire.

Ce que le contrat ne disait pas, et que ces tests fixent :

  - un evenement marque lu disparaissait POUR TOUJOURS. Aucun moyen d'y
    revenir, ni de verifier ce qu'on avait deja traite ;
  - une alerte calculee n'a pas d'identifiant propre : rien ne permettait de
    dire « je m'en occupe jeudi, ne me le remontre pas d'ici la ».

Et ce qui ne doit PAS changer : reporter n'efface rien. La facture reste en
retard, l'alerte reparait le jour dit.
"""
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Artisan, Facture, Notification


def _compte(client: TestClient, prefixe: str) -> tuple[dict, int]:
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
        artisan_id = artisan.id
    finally:
        db.close()
    return {"Authorization": f"Bearer {inscription.json()['access_token']}"}, artisan_id


def _facture_en_retard(client: TestClient, headers: dict) -> int:
    contact = client.post("/clients", headers=headers, json={"nom": f"Client {uuid4().hex[:6]}"})
    facture = client.post("/factures", headers=headers, json={
        "client_id": contact.json()["id"], "taux_tva": 20,
        "date_echeance": (date.today() - timedelta(days=20)).isoformat(),
        "lignes": [{"description": "Prestation", "quantite": 1, "prix_unitaire_ht": 500}],
    })
    assert facture.status_code == 201, facture.text
    facture_id = facture.json()["id"]
    # Une facture nait « brouillon », et un brouillon ne declenche aucune
    # alerte - c'est voulu. On la sort de cet etat directement en base : ce
    # test porte sur le cycle des notifications, pas sur celui d'une facture.
    db = SessionLocal()
    try:
        db.query(Facture).filter(Facture.id == facture_id).update({"statut": "en_retard"})
        db.commit()
    finally:
        db.close()
    return facture_id


def _alertes(client: TestClient, headers: dict, historique: bool = False) -> list:
    reponse = client.get("/notifications", headers=headers, params={"historique": str(historique).lower()})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def test_une_facture_en_retard_est_reportable_et_revient_le_jour_dit():
    with TestClient(app) as client:
        headers, _ = _compte(client, "notif-report")
        facture_id = _facture_en_retard(client, headers)

        avant = [n for n in _alertes(client, headers) if n["type"] == "facture_relance"]
        assert len(avant) == 1, "la facture en retard doit apparaitre"
        assert avant[0]["reportable"] is True, "le front n'a pas a rededuire ce qui est reportable"
        assert avant[0]["reportee_jusqu_au"] is None

        # On la repousse a la semaine prochaine.
        jeudi = date.today() + timedelta(days=7)
        report = client.post("/notifications/reporter", headers=headers, json={
            "type": "facture_relance", "reference_id": facture_id, "jusqu_au": jeudi.isoformat(),
        })
        assert report.status_code == 204, report.text

        courant = [n for n in _alertes(client, headers) if n["type"] == "facture_relance"]
        assert courant == [], "reportee, elle quitte le flux courant"

        # MAIS ELLE N'A PAS DISPARU : l'historique la montre, avec sa date.
        histo = [n for n in _alertes(client, headers, historique=True) if n["type"] == "facture_relance"]
        assert len(histo) == 1, "reporter n'efface pas : la facture est toujours en retard"
        assert histo[0]["reportee_jusqu_au"] == jeudi.isoformat()


def test_reporter_a_une_date_passee_est_refuse():
    # Sinon « reporter » deviendrait « masquer », ce qui n'est pas la meme chose.
    with TestClient(app) as client:
        headers, _ = _compte(client, "notif-passe")
        facture_id = _facture_en_retard(client, headers)
        for quand in (date.today(), date.today() - timedelta(days=1)):
            reponse = client.post("/notifications/reporter", headers=headers, json={
                "type": "facture_relance", "reference_id": facture_id, "jusqu_au": quand.isoformat(),
            })
            assert reponse.status_code == 422, reponse.text


def test_reporter_deux_fois_deplace_l_echeance():
    with TestClient(app) as client:
        headers, _ = _compte(client, "notif-deux-fois")
        facture_id = _facture_en_retard(client, headers)
        for jours in (3, 10):
            quand = date.today() + timedelta(days=jours)
            assert client.post("/notifications/reporter", headers=headers, json={
                "type": "facture_relance", "reference_id": facture_id, "jusqu_au": quand.isoformat(),
            }).status_code == 204
        histo = [n for n in _alertes(client, headers, historique=True) if n["type"] == "facture_relance"]
        assert len(histo) == 1, "un seul report par alerte, pas deux lignes"
        assert histo[0]["reportee_jusqu_au"] == (date.today() + timedelta(days=10)).isoformat()


def test_annuler_un_report_ramene_l_alerte():
    with TestClient(app) as client:
        headers, _ = _compte(client, "notif-annule")
        facture_id = _facture_en_retard(client, headers)
        client.post("/notifications/reporter", headers=headers, json={
            "type": "facture_relance", "reference_id": facture_id,
            "jusqu_au": (date.today() + timedelta(days=5)).isoformat(),
        })
        assert [n for n in _alertes(client, headers) if n["type"] == "facture_relance"] == []

        retour = client.delete(f"/notifications/reporter/facture_relance/{facture_id}", headers=headers)
        assert retour.status_code == 204, retour.text
        assert len([n for n in _alertes(client, headers) if n["type"] == "facture_relance"]) == 1

        # Annuler un report qui n'existe pas doit le dire.
        assert client.delete(f"/notifications/reporter/facture_relance/{facture_id}", headers=headers).status_code == 404
        assert client.delete(f"/notifications/reporter/inconnu/{facture_id}", headers=headers).status_code == 404


def test_un_evenement_lu_reste_consultable_dans_l_historique():
    with TestClient(app) as client:
        headers, artisan_id = _compte(client, "notif-histo")
        db = SessionLocal()
        try:
            db.add(Notification(
                artisan_id=artisan_id, type="nouvelle_demande_devis",
                titre="Nouvelle demande depuis le site", message="Roussel",
                view="prospects", lu=False, created_at=datetime.now(timezone.utc),
            ))
            db.commit()
            notification_id = db.query(Notification).filter(Notification.artisan_id == artisan_id).one().id
        finally:
            db.close()

        assert any(n["notification_id"] == notification_id for n in _alertes(client, headers))
        assert client.patch(f"/notifications/{notification_id}/lire", headers=headers).status_code == 204

        assert not any(n["notification_id"] == notification_id for n in _alertes(client, headers)), (
            "une fois lu, l'evenement quitte le flux courant"
        )
        histo = [n for n in _alertes(client, headers, historique=True) if n["notification_id"] == notification_id]
        assert len(histo) == 1, "mais il reste consultable - il disparaissait pour toujours"
        assert histo[0]["lu"] is True


def test_le_report_est_propre_a_chaque_compte():
    with TestClient(app) as client:
        moi, _ = _compte(client, "notif-moi")
        autrui, _ = _compte(client, "notif-autrui")
        ma_facture = _facture_en_retard(client, moi)
        sa_facture = _facture_en_retard(client, autrui)

        client.post("/notifications/reporter", headers=moi, json={
            "type": "facture_relance", "reference_id": ma_facture,
            "jusqu_au": (date.today() + timedelta(days=7)).isoformat(),
        })
        # Mon report ne doit pas masquer l'alerte de quelqu'un d'autre, meme
        # si les identifiants se croisent d'un compte a l'autre.
        assert len([n for n in _alertes(client, autrui) if n["type"] == "facture_relance"]) == 1
        assert sa_facture is not None
