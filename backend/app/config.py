from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import EmailStr


class Settings(BaseSettings):
    # Signal explicite d'environnement, verifie au demarrage (voir
    # app/startup_checks.py) pour refuser une configuration manifestement
    # dangereuse en production plutot que de demarrer quand meme. Literal (pas
    # un simple str) : toute valeur autre que "development"/"production"
    # (faute de frappe, "staging", chaine vide...) fait echouer la
    # construction de Settings() elle-meme des le chargement du module, avec
    # un message explicite listant les valeurs acceptees - pas besoin d'une
    # verification separee, Pydantic la fait a la source.
    app_env: Literal["development", "production"] = "development"

    # SQLite par defaut (zero config). En prod, definir DATABASE_URL vers Postgres,
    # ex: postgresql://user:password@host:5432/dbname
    database_url: str = "sqlite:///./suite_artisan.db"

    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 jours

    # Compte interne Admin Suite Artisan. Au premier demarrage, si les deux
    # valeurs sont definies, le compte est cree en base sans exposer de route
    # d'inscription admin. Le cookie Secure doit etre active en production.
    admin_email: EmailStr | None = None
    admin_password: str | None = None
    admin_name: str = "Administrateur Suite Artisan"
    admin_cookie_secure: bool = False

    # Stripe est optionnel : si les cles ne sont pas configurees, les endpoints
    # /stripe/* renvoient une erreur claire au lieu de faire planter l'appli.
    # Un prix Stripe distinct par plan payant (voir PLANS_PAYANTS dans
    # stripe_router.py) : stripe_price_id reste le nom historique, utilise
    # pour le plan "essentiel" (compatibilite avec les deploiements existants
    # qui n'avaient qu'un seul prix).
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id: str | None = None
    stripe_price_id_pro: str | None = None
    stripe_price_id_business: str | None = None

    # Adresse publique du frontend, utilisee pour les redirections apres paiement Stripe.
    app_base_url: str = "http://localhost:8080"

    # Dossier de stockage des documents uploades (chemin relatif au dossier backend/),
    # utilise quand storage_backend="local".
    uploads_dir: str = "uploads"
    max_upload_mo: int = 15
    site_media_max_upload_mo: int = 12
    site_media_max_photos: int = 20
    site_media_max_source_pixels: int = 40_000_000
    site_media_max_source_dimension: int = 12_000
    site_media_web_max_dimension: int = 2_400
    site_media_thumbnail_max_dimension: int = 480

    # Backend de stockage des fichiers (voir app/storage.py) : "local" (disque,
    # par defaut) ou "s3" (objet, compatible AWS S3 et Cloudflare R2 via un
    # endpoint custom). Aucun fallback silencieux : si "s3" est demande sans
    # les parametres requis, le demarrage echoue plutot que d'ecrire sur le
    # disque local a l'insu de l'operateur (voir startup_checks.py).
    storage_backend: str = "local"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket_name: str | None = None
    s3_region: str = "auto"

    # Origines autorisees a appeler l'API (CORS), separees par des virgules.
    # "*" par defaut pour ne rien casser en dev. A restreindre en prod aux
    # domaines reels du dashboard (les sites vitrines n'appellent que /pub/*,
    # qui reste ouvert separement, voir main.py).
    cors_origins: str = "*"

    # Emails transactionnels (devis, relances, factures...) via l'API HTTP de
    # Resend (pas de SDK requis, juste httpx). Optionnel : si resend_api_key
    # n'est pas defini, EmailService n'envoie rien mais journalise chaque
    # tentative avec un statut "non_configure" clair (jamais de faux succes).
    resend_api_key: str | None = None
    resend_api_url: str = "https://api.resend.com/emails"
    email_from: str = "onboarding@resend.dev"
    email_from_nom: str = "Suite Artisan"

    # Frequence du cycle d'automatisation (relances devis/factures, alertes
    # conformite...). Tourne en tache de fond des le demarrage du serveur,
    # independamment de toute connexion utilisateur.
    automation_interval_minutes: int = 60

    # Demarre (ou non) le scheduler APScheduler dans CE process (voir
    # app/scheduler.py). Actif par defaut pour ne rien changer au comportement
    # mono-instance existant. En production multi-instance, ne l'activer que
    # sur UN SEUL process/instance choisi - APScheduler ne se coordonne pas
    # lui-meme entre plusieurs process (le verrou consultatif Postgres dans
    # scheduler.py protege le contenu d'un cycle, pas le fait d'en lancer
    # plusieurs en parallele sur des schedules differents).
    scheduler_enabled: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
