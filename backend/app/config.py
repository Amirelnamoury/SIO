from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SQLite par defaut (zero config). En prod, definir DATABASE_URL vers Postgres,
    # ex: postgresql://user:password@host:5432/dbname
    database_url: str = "sqlite:///./suite_artisan.db"

    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 jours

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

    # Dossier de stockage des documents uploades (chemin relatif au dossier backend/).
    uploads_dir: str = "uploads"
    max_upload_mo: int = 15

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

    class Config:
        env_file = ".env"


settings = Settings()
