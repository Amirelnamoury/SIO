import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.scheduler import _traiter_conformite, _traiter_factures


def artisan(plan: str, subscription_status: str = "active") -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        plan=plan,
        subscription_status=subscription_status,
        email="artisan@example.test",
    )


def automation_run() -> SimpleNamespace:
    return SimpleNamespace(
        nb_factures_relancees=0,
        nb_alertes_conformite=0,
        nb_emails_envoyes=0,
        nb_emails_non_configures=0,
        nb_erreurs=0,
    )


class SchedulerPlanTests(unittest.TestCase):
    @patch("app.scheduler.email_service.send_relance_facture")
    def test_essentiel_does_not_run_automatic_invoice_reminders(self, send_email):
        db = MagicMock()

        _traiter_factures(db, artisan("essentiel"), automation_run())

        db.query.assert_not_called()
        send_email.assert_not_called()

    @patch("app.scheduler._tentative_recente", return_value=False)
    @patch("app.scheduler.relance_facture_due", return_value=True)
    @patch("app.scheduler.email_service.send_relance_facture")
    def test_pro_runs_automatic_invoice_reminders(self, send_email, _due, _recent):
        facture = SimpleNamespace(id=8, token="facture-token", date_derniere_relance=None, nb_relances=0)
        query = MagicMock()
        query.options.return_value = query
        query.filter.return_value = query
        query.all.return_value = [facture]
        db = MagicMock()
        db.query.return_value = query
        send_email.return_value = SimpleNamespace(statut="envoye")
        run = automation_run()

        _traiter_factures(db, artisan("pro"), run)

        send_email.assert_called_once()
        self.assertEqual(facture.nb_relances, 1)
        self.assertEqual(run.nb_factures_relancees, 1)

    @patch("app.scheduler.email_service.send_conformite_alerte")
    def test_gratuit_does_not_run_automatic_compliance_alerts(self, send_email):
        db = MagicMock()

        _traiter_conformite(db, artisan("gratuit"), automation_run())

        db.query.assert_not_called()
        send_email.assert_not_called()

    @patch("app.scheduler._tentative_recente", return_value=False)
    @patch("app.scheduler.email_service.send_conformite_alerte")
    def test_essentiel_runs_automatic_compliance_alerts(self, send_email, _recent):
        item = SimpleNamespace(id=5, libelle="Assurance decennale", date_expiration=date.today() + timedelta(days=5))
        query = MagicMock()
        query.filter.return_value = query
        query.all.return_value = [item]
        query.first.return_value = None
        db = MagicMock()
        db.query.return_value = query
        send_email.return_value = SimpleNamespace(statut="envoye")
        run = automation_run()

        _traiter_conformite(db, artisan("essentiel"), run)

        send_email.assert_called_once()
        self.assertEqual(run.nb_alertes_conformite, 1)


if __name__ == "__main__":
    unittest.main()
