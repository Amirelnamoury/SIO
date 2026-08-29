import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.deps import (
    PLAN_ORDRE,
    plan_allows,
    require_active_subscription,
    require_equipe_admin,
    require_plan,
)


MINIMUMS = {
    "factures": "essentiel",
    "paiements": "essentiel",
    "chantiers": "essentiel",
    "conformite": "essentiel",
    "statistiques": "essentiel",
    "relance_factures": "essentiel",
    "relance_devis": "pro",
    "automatisations": "pro",
    "contrats": "pro",
    "equipe": "business",
}


def artisan(plan: str, subscription_status: str = "inactive") -> SimpleNamespace:
    return SimpleNamespace(plan=plan, subscription_status=subscription_status)


class EntitlementMatrixTests(unittest.TestCase):
    def test_complete_plan_matrix(self):
        for plan in PLAN_ORDRE:
            for feature, minimum in MINIMUMS.items():
                with self.subTest(plan=plan, feature=feature):
                    expected = PLAN_ORDRE.index(plan) >= PLAN_ORDRE.index(minimum)
                    self.assertEqual(plan_allows(plan, minimum), expected)

    def test_essentiel_dependency_uses_authenticated_plan(self):
        self.assertEqual(require_active_subscription(artisan("essentiel")), artisan("essentiel"))
        with self.assertRaises(HTTPException) as error:
            require_active_subscription(artisan("gratuit", "active"))
        self.assertEqual(error.exception.status_code, 402)

    def test_pro_dependency_is_hierarchical(self):
        require_pro = require_plan("pro")
        for plan in ("pro", "business"):
            with self.subTest(plan=plan):
                self.assertEqual(require_pro(artisan(plan)), artisan(plan))
        for plan in ("gratuit", "essentiel"):
            with self.subTest(plan=plan), self.assertRaises(HTTPException):
                require_pro(artisan(plan))

    def test_business_team_gate_uses_plan_and_role(self):
        owner = SimpleNamespace(artisan=artisan("business"), role="proprietaire")
        self.assertIs(require_equipe_admin(owner), owner)
        with self.assertRaises(HTTPException) as plan_error:
            require_equipe_admin(SimpleNamespace(artisan=artisan("pro"), role="proprietaire"))
        self.assertEqual(plan_error.exception.status_code, 402)
        with self.assertRaises(HTTPException) as role_error:
            require_equipe_admin(SimpleNamespace(artisan=artisan("business"), role="salarie"))
        self.assertEqual(role_error.exception.status_code, 403)

    def test_unknown_plans_are_rejected(self):
        self.assertFalse(plan_allows("inconnu", "essentiel"))
        self.assertFalse(plan_allows("business", "inconnu"))


if __name__ == "__main__":
    unittest.main()
