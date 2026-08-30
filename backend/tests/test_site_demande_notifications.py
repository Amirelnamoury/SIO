from uuid import uuid4

from fastapi.testclient import TestClient

from app import email_service
from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models import Artisan, Client, EmailLog, Notification
from app.security import create_access_token


def _creer_artisan(nom: str) -> dict:
    suffixe = uuid4().hex
    db = SessionLocal()
    try:
        artisan = Artisan(
            slug=f"{nom.lower().replace(' ', '-')}-{suffixe}",
            nom_entreprise=nom,
            metier="plombier",
            email=f"{nom.lower().replace(' ', '-')}-{suffixe}@e2e-test.fr",
            password_hash="non-utilise",
        )
        db.add(artisan)
        db.commit()
        db.refresh(artisan)
        return {
            "id": artisan.id,
            "slug": artisan.slug,
            "email": artisan.email,
            "headers": {"Authorization": f"Bearer {create_access_token(artisan.id)}"},
        }
    finally:
        db.close()


def _assert_demande_conservee(artisan_id: int, client_id: int) -> tuple[Client, Notification]:
    db = SessionLocal()
    try:
        prospect = db.query(Client).filter(Client.id == client_id, Client.artisan_id == artisan_id).one()
        notification = (
            db.query(Notification)
            .filter(Notification.client_id == client_id, Notification.artisan_id == artisan_id)
            .one()
        )
        db.expunge(prospect)
        db.expunge(notification)
        return prospect, notification
    finally:
        db.close()


def test_demande_reelle_cree_prospect_notification_et_email_du_bon_tenant(monkeypatch):
    artisan_a = _creer_artisan("Artisan Site A")
    artisan_b = _creer_artisan("Artisan Site B")
    envois = []
    monkeypatch.setattr(settings, "resend_api_key", "cle-test-non-reelle")

    def faux_envoi(destinataire, objet, html):
        envois.append((destinataire, objet, html))
        return True, "email-test-123", None

    monkeypatch.setattr(email_service, "_send_raw", faux_envoi)

    with TestClient(app) as client:
        response = client.post(
            f"/pub/{artisan_a['slug']}/demande-devis",
            json={
                "nom": "Test Site Reel",
                "email": "prospect@example.fr",
                "telephone": "0601020304",
                "message": "Remplacement complet de la salle de bain",
            },
        )
        assert response.status_code == 201, response.text
        client_id = response.json()["client_id"]

        notifications_a = client.get("/notifications", headers=artisan_a["headers"])
        notifications_b = client.get("/notifications", headers=artisan_b["headers"])
        assert notifications_a.status_code == 200, notifications_a.text
        assert notifications_b.status_code == 200, notifications_b.text

        notification_api = next(n for n in notifications_a.json() if n["client_id"] == client_id)
        assert notification_api["type"] == "nouvelle_demande_devis"
        assert notification_api["titre"] == "Nouvelle demande de devis"
        assert "Test Site Reel" in notification_api["sous_titre"]
        assert notification_api["lu"] is False
        assert all(n.get("client_id") != client_id for n in notifications_b.json())

        lecture_interdite = client.patch(
            f"/notifications/{notification_api['notification_id']}/lire",
            headers=artisan_b["headers"],
        )
        assert lecture_interdite.status_code == 404
        lecture = client.patch(
            f"/notifications/{notification_api['notification_id']}/lire",
            headers=artisan_a["headers"],
        )
        assert lecture.status_code == 204
        apres_lecture = client.get("/notifications", headers=artisan_a["headers"])
        assert all(n.get("client_id") != client_id for n in apres_lecture.json())

    prospect, notification = _assert_demande_conservee(artisan_a["id"], client_id)
    assert prospect.statut == "nouveau"
    assert prospect.source == "site_vitrine"
    assert prospect.nom == "Test Site Reel"
    assert prospect.email == "prospect@example.fr"
    assert prospect.telephone == "0601020304"
    assert prospect.notes == "Remplacement complet de la salle de bain"
    assert notification.lu is True

    db = SessionLocal()
    try:
        assert db.query(Client).filter(Client.artisan_id == artisan_b["id"]).count() == 0
        assert db.query(Notification).filter(Notification.artisan_id == artisan_b["id"]).count() == 0
        log = (
            db.query(EmailLog)
            .filter(EmailLog.client_id == client_id, EmailLog.type == "nouvelle_demande_devis")
            .one()
        )
        assert log.artisan_id == artisan_a["id"]
        assert log.destinataire == artisan_a["email"]
        assert log.statut == "envoye"
        assert log.provider_id == "email-test-123"
    finally:
        db.close()

    assert len(envois) == 1
    assert envois[0][0] == artisan_a["email"]
    assert artisan_b["email"] not in envois[0][2]
    assert "Test Site Reel" in envois[0][2]


def test_email_non_configure_ne_perd_ni_prospect_ni_notification(monkeypatch):
    artisan = _creer_artisan("Artisan Sans Resend")
    monkeypatch.setattr(settings, "resend_api_key", None)
    monkeypatch.setattr(
        email_service,
        "_send_raw",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("Le provider ne doit pas etre appele")),
    )

    with TestClient(app) as client:
        response = client.post(
            f"/pub/{artisan['slug']}/demande-devis",
            json={"nom": "Prospect sans Resend", "message": "Besoin d'un devis"},
        )

    assert response.status_code == 201, response.text
    assert set(response.json()) == {"message", "client_id"}
    client_id = response.json()["client_id"]
    _assert_demande_conservee(artisan["id"], client_id)

    db = SessionLocal()
    try:
        log = db.query(EmailLog).filter(EmailLog.client_id == client_id).one()
        assert log.statut == "non_configure"
        assert log.destinataire == artisan["email"]
        assert log.provider_id is None
    finally:
        db.close()


def test_erreur_provider_est_journalisee_sans_perdre_la_demande(monkeypatch):
    artisan = _creer_artisan("Artisan Provider KO")
    monkeypatch.setattr(settings, "resend_api_key", "cle-test-non-reelle")
    monkeypatch.setattr(email_service, "_send_raw", lambda *_args: (False, None, "Timeout provider"))

    with TestClient(app) as client:
        response = client.post(
            f"/pub/{artisan['slug']}/demande-devis",
            json={"nom": "Prospect Provider KO", "email": "prospect-ko@example.fr"},
        )

    assert response.status_code == 201, response.text
    client_id = response.json()["client_id"]
    _assert_demande_conservee(artisan["id"], client_id)
    db = SessionLocal()
    try:
        log = db.query(EmailLog).filter(EmailLog.client_id == client_id).one()
        assert log.statut == "echec"
        assert log.erreur == "Timeout provider"
    finally:
        db.close()


def test_artisan_sans_adresse_email_conserve_la_demande(monkeypatch):
    artisan = _creer_artisan("Artisan Sans Email")
    db = SessionLocal()
    try:
        db.query(Artisan).filter(Artisan.id == artisan["id"]).update({Artisan.email: ""})
        db.commit()
    finally:
        db.close()
    monkeypatch.setattr(settings, "resend_api_key", "cle-test-non-reelle")
    monkeypatch.setattr(
        email_service,
        "_send_raw",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("Le provider ne doit pas etre appele")),
    )

    with TestClient(app) as client:
        response = client.post(
            f"/pub/{artisan['slug']}/demande-devis",
            json={"nom": "Prospect artisan sans email"},
        )

    assert response.status_code == 201, response.text
    client_id = response.json()["client_id"]
    _assert_demande_conservee(artisan["id"], client_id)
    db = SessionLocal()
    try:
        log = db.query(EmailLog).filter(EmailLog.client_id == client_id).one()
        assert log.statut == "sans_destinataire"
        assert log.destinataire == ""
    finally:
        db.close()


def test_exception_email_inattendue_ne_rollback_pas_la_demande(monkeypatch):
    artisan = _creer_artisan("Artisan Exception Email")

    def lever_exception(*_args, **_kwargs):
        raise RuntimeError("Panne inattendue simulee")

    monkeypatch.setattr(email_service, "send_nouvelle_demande_devis", lever_exception)
    with TestClient(app) as client:
        response = client.post(
            f"/pub/{artisan['slug']}/demande-devis",
            json={"nom": "Prospect toujours conserve"},
        )

    assert response.status_code == 201, response.text
    _assert_demande_conservee(artisan["id"], response.json()["client_id"])


def test_rate_limit_de_la_demande_site_reste_actif(monkeypatch):
    artisan = _creer_artisan("Artisan Rate Limit")
    monkeypatch.setattr(settings, "resend_api_key", None)

    with TestClient(app) as client:
        reponses = [
            client.post(
                f"/pub/{artisan['slug']}/demande-devis",
                json={"nom": f"Prospect limite {index}"},
            )
            for index in range(6)
        ]

    assert [response.status_code for response in reponses[:5]] == [201] * 5
    assert reponses[5].status_code == 429
