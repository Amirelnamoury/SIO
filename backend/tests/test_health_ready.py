"""Verifie /health et /ready (section Production Readiness)."""
from fastapi.testclient import TestClient

from app.main import app


def test_health_repond_ok():
    with TestClient(app) as client:
        res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ready_repond_ok_quand_la_db_repond():
    with TestClient(app) as client:
        res = client.get("/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ready_ne_fuite_aucune_info_sensible_meme_en_erreur(monkeypatch):
    """Simule une DB indisponible : /ready doit repondre 503 avec un message
    generique, jamais le detail technique (message d'exception, DATABASE_URL...)."""
    import app.main as main_module

    class _SessionQuiEchoue:
        def execute(self, *a, **kw):
            raise RuntimeError("connection refused: host=secret-db-host user=admin password=hunter2")

        def close(self):
            pass

    monkeypatch.setattr(main_module, "SessionLocal", lambda: _SessionQuiEchoue())

    with TestClient(app) as client:
        res = client.get("/ready")

    assert res.status_code == 503
    assert res.json() == {"status": "unavailable"}
    corps = res.text
    assert "hunter2" not in corps
    assert "secret-db-host" not in corps
    assert "connection refused" not in corps


def test_health_racine_toujours_presente():
    with TestClient(app) as client:
        res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
