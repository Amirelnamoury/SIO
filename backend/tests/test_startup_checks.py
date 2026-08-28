"""Verifie que le demarrage refuse une configuration de production dangereuse
(section Production Readiness). Construit des Settings() directement plutot
que de manipuler des variables d'environnement + reimporter app.main : plus
rapide, et evite les effets de bord (create_all, logging) au chargement.
"""
import pytest

from app.config import Settings
from app.startup_checks import valider_configuration

PROD_OK = dict(
    app_env="production",
    jwt_secret="un-vrai-secret-de-production-suffisamment-long",
    database_url="postgresql://user:password@host:5432/suite_artisan",
    app_base_url="https://app.suite-artisan.example",
    admin_cookie_secure=True,
)


def test_dev_par_defaut_ne_leve_pas():
    valider_configuration(Settings())


def test_production_refuse_le_secret_jwt_par_defaut():
    s = Settings(**{**PROD_OK, "jwt_secret": "dev-secret-change-me-in-production"})
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        valider_configuration(s)


def test_production_refuse_sqlite():
    s = Settings(**{**PROD_OK, "database_url": "sqlite:///./suite_artisan.db"})
    with pytest.raises(RuntimeError, match="SQLite"):
        valider_configuration(s)


def test_secret_par_defaut_avec_base_non_sqlite_leve_meme_sans_app_env_explicite():
    # Signal implicite (deja present avant cette passe) : une DATABASE_URL
    # non-sqlite avec le secret de dev doit rester bloquee meme si APP_ENV
    # n'a pas ete positionne a "production" explicitement. jwt_secret precise
    # explicitement (et non omis) : conftest.py definit JWT_SECRET dans
    # l'environnement pour le reste de la suite, ce qui masquerait sinon la
    # vraie valeur par defaut de Settings.
    s = Settings(
        database_url="postgresql://user:password@host:5432/db",
        jwt_secret="dev-secret-change-me-in-production",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        valider_configuration(s)


def test_production_refuse_app_base_url_non_https():
    s = Settings(**{**PROD_OK, "app_base_url": "http://app.suite-artisan.example"})
    with pytest.raises(RuntimeError, match="HTTPS"):
        valider_configuration(s)


def test_production_refuse_storage_s3_incomplet():
    s = Settings(**{**PROD_OK, "storage_backend": "s3"})
    with pytest.raises(RuntimeError, match="STORAGE_BACKEND=s3"):
        valider_configuration(s)


def test_production_accepte_storage_s3_complet():
    s = Settings(
        **PROD_OK,
        storage_backend="s3",
        s3_endpoint_url="https://abc123.r2.cloudflarestorage.com",
        s3_access_key_id="AKIAEXEMPLE",
        s3_secret_access_key="secret-exemple",
        s3_bucket_name="suite-artisan-documents",
    )
    valider_configuration(s)  # ne doit rien lever


def test_production_valide_complete_ne_leve_pas():
    valider_configuration(Settings(**PROD_OK))


def test_production_refuse_mot_de_passe_admin_de_demo():
    s = Settings(**{**PROD_OK, "admin_password": "change-me-with-a-long-random-password"})
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        valider_configuration(s)


def test_production_accepte_un_vrai_mot_de_passe_admin():
    s = Settings(**{**PROD_OK, "admin_password": "un-mot-de-passe-admin-reel-et-long"})
    valider_configuration(s)  # ne doit rien lever


def test_production_refuse_cookie_admin_non_secure():
    s = Settings(**{**PROD_OK, "admin_cookie_secure": False})
    with pytest.raises(RuntimeError, match="ADMIN_COOKIE_SECURE"):
        valider_configuration(s)
