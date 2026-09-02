"""Section 28 du brief Production Readiness (Admin / Site Vitrine).

Note de contexte : au moment ou l'audit initial de cette mission a ete fait,
aucun sous-systeme Admin n'existait dans ce depot - ce constat a change en
cours de tache : un travail concurrent sur la meme branche (rebase sur
81a14eb, voir le rapport final) a introduit backend/app/routers/admin.py,
backend/app/admin_service.py et le modele SiteVitrine. Ces tests verifient
donc l'integration reelle plutot qu'un constat d'absence devenu obsolete.

Le moteur de generation automatique de site (et son mecanisme de preview HTML
en cache, base sur ce meme Storage abstrait) a ete retire depuis : les tests
qui ne verifiaient que ce mecanisme de preview ont ete retires avec lui. Ceux
qui restent ici verifient des invariants Admin qui ne dependent pas du moteur
retire.
"""
import inspect

from app.models import Artisan
from app.routers.dashboard import obtenir_dashboard


def test_artisan_a_bien_un_champ_site_statut_sans_plan_minimum():
    # Le champ existe sur le modele et n'est associe a aucune dependance
    # require_plan/require_active_subscription dans dashboard.py : verifie en
    # inspectant reellement la signature de obtenir_dashboard() plutot que de
    # le supposer. Le Site Vitrine reste disponible avec le plan Gratuit.
    assert hasattr(Artisan, "site_statut")
    assert hasattr(Artisan, "site_url")
    source = inspect.getsource(obtenir_dashboard)
    assert "require_plan" not in source
    assert "require_active_subscription" not in source


def test_admin_router_existe_et_est_enregistre():
    from app.main import app
    from app.routers import admin

    assert admin.router is not None
    routes_admin = [r for r in app.routes if getattr(r, "path", "").startswith("/admin")]
    assert len(routes_admin) > 0


def test_admin_cookie_secure_est_bien_le_reglage_lu_par_le_router():
    """ADMIN_COOKIE_SECURE (section 16 du brief) controle reellement le flag
    Secure du cookie de session admin - verifie par inspection du code plutot
    que suppose, puisque c'est settings.admin_cookie_secure qui est valide en
    production dans startup_checks.py (voir test_startup_checks.py)."""
    from app.routers import admin as admin_router

    source = inspect.getsource(admin_router)
    assert "settings.admin_cookie_secure" in source
