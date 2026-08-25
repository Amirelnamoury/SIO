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
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id: str | None = None

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

    class Config:
        env_file = ".env"


settings = Settings()
