"""Non-regression pour le bug "decalage d'heure dans le Planning" (voir
frontend/tests/planning-date.test.mjs et e2e/scenario13_planning_timezone.mjs
pour les pendants frontend/E2E de ce meme correctif).

Cause racine reelle : SQLite ne conserve pas le fuseau horaire des colonnes
DateTime(timezone=True) - une valeur relue depuis la base revient "naive"
(tzinfo=None) meme si elle represente en realite un instant UTC. Sans
correctif, FastAPI/Pydantic serialisait donc ces dates SANS marqueur de
fuseau ("Z"/"+00:00"), et le frontend (qui envoie deja un instant UTC
correctement converti) les reinterpretait ensuite dans le fuseau AMBIANT du
navigateur plutot qu'UTC - d'ou un decalage silencieux (ex: 09:00 saisi,
07:00 affiche en ete).

Ces tests utilisent une vraie base SQLite fichier (voir conftest.py, pas
":memory:") pour reproduire fidelement ce comportement, et verifient a la
fois la reponse HTTP ET la ligne brute SQLite - pas seulement un helper
unitaire."""
import sqlite3
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def _creer_artisan_et_se_connecter(client: TestClient, email: str) -> str:
    res = client.post("/auth/register", json={
        "nom_entreprise": "Test Planning TZ", "metier": "plombier",
        "email": email, "password": "TestPass123!",
    })
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def _chemin_sqlite() -> str:
    # DATABASE_URL est de la forme sqlite:///chemin/vers/test.db (voir
    # conftest.py) : on lit directement ce meme fichier, comme le ferait un
    # DBA inspectant la base en production.
    url = settings.database_url
    assert url.startswith("sqlite:///"), f"ce test suppose SQLite (URL actuelle : {url})"
    return url.removeprefix("sqlite:///")


def test_date_debut_evenement_est_serialisee_avec_fuseau_explicite():
    """POST /evenements avec un instant UTC explicite ("Z") doit renvoyer
    une reponse dont date_debut porte AUSSI un marqueur de fuseau explicite -
    jamais une chaine "naive" ambigue, meme si SQLite a interne perdu le
    tzinfo au round-trip."""
    with TestClient(app) as client:
        token = _creer_artisan_et_se_connecter(client, "planning-tz-1@e2e-test.fr")
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post("/evenements", headers=headers, json={
            "titre": "TEST", "type": "rdv", "date_debut": "2026-08-29T07:00:00.000Z",
        })
        assert res.status_code == 201, res.text
        body = res.json()

        # La chaine doit etre non-ambigue : soit un "Z", soit un offset
        # explicite ("+00:00") - jamais une chaine sans aucun marqueur.
        date_debut_str = body["date_debut"]
        assert date_debut_str.endswith("Z") or "+" in date_debut_str[10:] or date_debut_str.endswith("00:00"), (
            f"date_debut doit porter un marqueur de fuseau explicite, recu : {date_debut_str!r}"
        )
        # Et l'instant represente doit rester exactement celui envoye (7h UTC).
        parsed = datetime.fromisoformat(date_debut_str.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None
        assert parsed.astimezone(timezone.utc) == datetime(2026, 8, 29, 7, 0, 0, tzinfo=timezone.utc), (
            f"l'instant UTC doit rester 2026-08-29T07:00:00Z, recu : {date_debut_str!r}"
        )


def test_planning_item_est_serialise_avec_fuseau_explicite():
    """GET /planning (utilise par le calendrier du frontend) doit renvoyer
    le meme comportement que EvenementOut : jamais de date naive."""
    with TestClient(app) as client:
        token = _creer_artisan_et_se_connecter(client, "planning-tz-2@e2e-test.fr")
        headers = {"Authorization": f"Bearer {token}"}

        client.post("/evenements", headers=headers, json={
            "titre": "TEST_PLANNING", "type": "rdv", "date_debut": "2026-08-29T07:00:00.000Z",
        })

        res = client.get("/planning?debut=2026-08-29&fin=2026-08-29", headers=headers)
        assert res.status_code == 200, res.text
        items = res.json()
        item = next(i for i in items if i["titre"] == "TEST_PLANNING")

        date_str = item["date"]
        assert date_str.endswith("Z") or "+" in date_str[10:], (
            f"PlanningItem.date doit porter un marqueur de fuseau explicite, recu : {date_str!r}"
        )
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        assert parsed.astimezone(timezone.utc) == datetime(2026, 8, 29, 7, 0, 0, tzinfo=timezone.utc)


def test_edition_evenement_preserve_le_fuseau_explicite():
    """PATCH /evenements/{id} (edition d'heure - le flux exact du bug
    signale) doit lui aussi renvoyer une date_debut non-ambigue, et la
    nouvelle valeur doit correspondre exactement a ce qui a ete envoye
    (aucune derive introduite par l'aller-retour SQLite)."""
    with TestClient(app) as client:
        token = _creer_artisan_et_se_connecter(client, "planning-tz-3@e2e-test.fr")
        headers = {"Authorization": f"Bearer {token}"}

        creation = client.post("/evenements", headers=headers, json={
            "titre": "TEST_EDIT", "type": "rdv", "date_debut": "2026-08-29T07:00:00.000Z",
        })
        evenement_id = creation.json()["id"]

        # 09:00 -> 10:00 heure de Paris (ete, UTC+2) = 08:00 UTC.
        edition = client.patch(f"/evenements/{evenement_id}", headers=headers, json={
            "date_debut": "2026-08-29T08:00:00.000Z",
        })
        assert edition.status_code == 200, edition.text
        date_str = edition.json()["date_debut"]
        assert date_str.endswith("Z") or "+" in date_str[10:], (
            f"apres edition, date_debut doit porter un marqueur de fuseau explicite, recu : {date_str!r}"
        )
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        assert parsed.astimezone(timezone.utc) == datetime(2026, 8, 29, 8, 0, 0, tzinfo=timezone.utc), (
            f"l'edition doit stocker exactement 08:00 UTC (10:00 Paris ete), recu : {date_str!r}"
        )

        # Relecture via GET /evenements : meme garantie, independant du
        # cache de l'objet retourne juste apres l'ecriture.
        relecture = client.get("/evenements", headers=headers)
        item = next(e for e in relecture.json() if e["id"] == evenement_id)
        parsed_relu = datetime.fromisoformat(item["date_debut"].replace("Z", "+00:00"))
        assert parsed_relu.tzinfo is not None
        assert parsed_relu.astimezone(timezone.utc) == datetime(2026, 8, 29, 8, 0, 0, tzinfo=timezone.utc)


def test_hiver_conserve_un_instant_utc_correct():
    """15/01/2026 08:00 UTC = 09:00 heure de Paris en hiver (CET, UTC+1) -
    verifie que le correctif n'est pas specifique a l'ete."""
    with TestClient(app) as client:
        token = _creer_artisan_et_se_connecter(client, "planning-tz-4@e2e-test.fr")
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post("/evenements", headers=headers, json={
            "titre": "TEST_HIVER", "type": "rdv", "date_debut": "2026-01-15T08:00:00.000Z",
        })
        assert res.status_code == 201, res.text
        parsed = datetime.fromisoformat(res.json()["date_debut"].replace("Z", "+00:00"))
        assert parsed.astimezone(timezone.utc) == datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)


def test_valeur_brute_sqlite_reste_correcte_apres_le_correctif():
    """Le correctif agit a la serialisation (Pydantic), jamais au stockage :
    verifie directement, en lisant la ligne SQLite, que la valeur brute
    persistee reste le texte UTC attendu (le correctif ne doit pas modifier
    ce qui est ecrit en base, seulement ce que l'API renvoie)."""
    with TestClient(app) as client:
        token = _creer_artisan_et_se_connecter(client, "planning-tz-5@e2e-test.fr")
        headers = {"Authorization": f"Bearer {token}"}
        res = client.post("/evenements", headers=headers, json={
            "titre": "TEST_SQLITE_BRUT", "type": "rdv", "date_debut": "2026-08-29T07:00:00.000Z",
        })
        evenement_id = res.json()["id"]

    conn = sqlite3.connect(_chemin_sqlite())
    try:
        cur = conn.cursor()
        cur.execute("SELECT date_debut, typeof(date_debut) FROM evenements WHERE id = ?", (evenement_id,))
        valeur_brute, type_sqlite = cur.fetchone()
    finally:
        conn.close()

    assert type_sqlite == "text", "SQLite n'a pas de type datetime natif : confirme le stockage en texte"
    assert valeur_brute.startswith("2026-08-29 07:00:00"), (
        f"la valeur brute stockee doit rester l'heure UTC (07:00), recu : {valeur_brute!r}"
    )
