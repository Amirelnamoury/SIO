"""Validation de configuration au demarrage (section Production Readiness).

Extrait de main.py pour rester testable sans avoir a importer toute
l'application (qui execute des effets de bord au chargement, comme
Base.metadata.create_all). Une seule fonction, appelee une fois au demarrage :
si elle leve, le process ne demarre pas - jamais de configuration dangereuse
qui tourne quand meme avec un simple warning en production.
"""
from __future__ import annotations

from app.config import Settings

DEFAULT_JWT_SECRET = "dev-secret-change-me-in-production"
DEFAULT_ADMIN_PASSWORD = "change-me-with-a-long-random-password"

_S3_CHAMPS_REQUIS = (
    "s3_endpoint_url",
    "s3_access_key_id",
    "s3_secret_access_key",
    "s3_bucket_name",
)


def valider_configuration(settings: Settings) -> None:
    """Leve RuntimeError si la configuration est manifestement dangereuse.

    Deux signaux independants declenchent les verifications strictes :
    - APP_ENV=production (signal explicite, couvre toutes les verifications) ;
    - DATABASE_URL non-sqlite avec le JWT_SECRET de dev par defaut (signal
      implicite deja present avant cette passe : un deploiement pointant vers
      une vraie base sans avoir change le secret est presume serieux, meme
      sans avoir pense a poser APP_ENV=production).
    Ne fait rien en developpement normal (sqlite + APP_ENV par defaut).
    """
    est_prod_explicite = settings.app_env == "production"
    est_prod_implicite = not settings.database_url.startswith("sqlite")

    if not est_prod_explicite and not est_prod_implicite:
        return

    erreurs: list[str] = []

    if settings.jwt_secret == DEFAULT_JWT_SECRET:
        erreurs.append(
            "JWT_SECRET utilise encore la valeur de developpement par defaut. "
            "Definissez un vrai secret avant de demarrer en production."
        )

    if est_prod_explicite and settings.database_url.startswith("sqlite"):
        erreurs.append(
            "APP_ENV=production mais DATABASE_URL pointe vers SQLite. "
            "Configurez une base Postgres pour un deploiement de production."
        )

    if est_prod_explicite and not settings.app_base_url.startswith("https://"):
        erreurs.append(
            f"APP_ENV=production mais APP_BASE_URL n'est pas en HTTPS ({settings.app_base_url!r}). "
            "Configurez une adresse publique en https:// avant de demarrer en production."
        )

    if settings.storage_backend == "s3":
        manquants = [
            champ.upper() for champ in _S3_CHAMPS_REQUIS
            if not getattr(settings, champ)
        ]
        if manquants:
            erreurs.append(
                "STORAGE_BACKEND=s3 mais des parametres obligatoires manquent : "
                + ", ".join(manquants) + ". Aucun fallback silencieux vers le disque local."
            )
    elif settings.storage_backend != "local":
        erreurs.append(
            f"STORAGE_BACKEND doit etre 'local' ou 's3', pas {settings.storage_backend!r}."
        )

    if est_prod_explicite and settings.admin_password == DEFAULT_ADMIN_PASSWORD:
        erreurs.append(
            "ADMIN_PASSWORD utilise encore le mot de passe de demonstration par defaut. "
            "Definissez un vrai mot de passe avant de demarrer en production."
        )

    if est_prod_explicite and not settings.admin_cookie_secure:
        erreurs.append(
            "APP_ENV=production mais ADMIN_COOKIE_SECURE=false. "
            "Le cookie de session Admin doit etre Secure en production (HTTPS)."
        )

    if erreurs:
        raise RuntimeError(
            "Configuration de production invalide :\n- " + "\n- ".join(erreurs)
        )
