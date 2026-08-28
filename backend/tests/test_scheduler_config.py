"""Verifie SCHEDULER_ENABLED et l'absence de double demarrage evident dans un
meme process (section Production Readiness). La logique metier des
automatisations (frontieres de plan) n'est pas touchee par cette section et
reste couverte par e2e/scenario12_plans_tarifaires.mjs (matrice complete,
execution HTTP reelle) - pas dupliquee ici en detail d'implementation."""
from unittest.mock import MagicMock, patch

import app.scheduler as scheduler_module


def test_start_scheduler_est_idempotent():
    """Deux appels dans le meme process ne demarrent qu'une seule fois le
    BackgroundScheduler sous-jacent (protection deja presente dans
    scheduler.py via le global _scheduler, verifiee ici explicitement)."""
    scheduler_module._scheduler = None
    try:
        with patch("app.scheduler.BackgroundScheduler") as FakeScheduler:
            instance = MagicMock()
            FakeScheduler.return_value = instance

            premier = scheduler_module.start_scheduler()
            second = scheduler_module.start_scheduler()

            assert premier is second
            FakeScheduler.assert_called_once()
            instance.start.assert_called_once()
    finally:
        scheduler_module.stop_scheduler()
        scheduler_module._scheduler = None


def test_scheduler_enabled_true_demarre_le_scheduler(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module.settings, "scheduler_enabled", True)
    start_mock = MagicMock()
    stop_mock = MagicMock()
    monkeypatch.setattr("app.scheduler.start_scheduler", start_mock)
    monkeypatch.setattr("app.scheduler.stop_scheduler", stop_mock)

    import asyncio

    async def _run():
        async with main_module.lifespan(main_module.app):
            pass

    asyncio.run(_run())
    start_mock.assert_called_once()
    stop_mock.assert_called_once()


def test_scheduler_enabled_false_ne_demarre_rien(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module.settings, "scheduler_enabled", False)
    start_mock = MagicMock()
    stop_mock = MagicMock()
    monkeypatch.setattr("app.scheduler.start_scheduler", start_mock)
    monkeypatch.setattr("app.scheduler.stop_scheduler", stop_mock)

    import asyncio

    async def _run():
        async with main_module.lifespan(main_module.app):
            pass

    asyncio.run(_run())
    start_mock.assert_not_called()
    stop_mock.assert_not_called()
