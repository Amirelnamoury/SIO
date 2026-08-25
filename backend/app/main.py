import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401  (necessaire pour que les tables soient enregistrees)

logger = logging.getLogger("suite_artisan")

_DEFAULT_JWT_SECRET = "dev-secret-change-me-in-production"
if settings.jwt_secret == _DEFAULT_JWT_SECRET:
    if settings.database_url.startswith("sqlite"):
        logger.warning(
            "JWT_SECRET n'est pas configure (valeur de developpement utilisee). "
            "A definir avant tout deploiement reel."
        )
    else:
        # Base de donnees non-sqlite = deploiement qui se veut serieux (Postgres...).
        # Continuer avec le secret de dev par defaut permettrait a n'importe qui
        # de forger un token valide pour n'importe quel compte : on refuse de demarrer.
        raise RuntimeError(
            "JWT_SECRET utilise encore la valeur de developpement par defaut alors que "
            "DATABASE_URL pointe vers une base non-sqlite. Definissez un vrai secret "
            "(JWT_SECRET dans l'environnement) avant de demarrer."
        )
from app.routers import (
    analytics,
    auth,
    chantiers,
    clients,
    conformite,
    dashboard,
    devis,
    documents,
    factures,
    planning,
    public,
    search,
    stripe_router,
    taches,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Suite Artisan API", version="0.1.0")

_cors_origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # IMPORTANT si CORS_ORIGINS est restreint en prod : les formulaires publics
    # (/pub/*, appeles depuis les sites vitrines livres aux artisans, sur des
    # domaines qu'on ne connait pas a l'avance) ont besoin d'etre appelables
    # depuis n'importe quelle origine. Soit garder CORS_ORIGINS="*" (defaut,
    # le seul cout est que le dashboard n'est plus le seul appelant autorise -
    # sans grande consequence tant que l'auth reste par token en en-tete, pas
    # par cookie), soit ajouter explicitement chaque domaine de site vitrine
    # livre a la liste.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(devis.router)
app.include_router(factures.router)
app.include_router(chantiers.router)
app.include_router(conformite.router)
app.include_router(taches.router)
app.include_router(planning.router)
app.include_router(documents.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(public.router)
app.include_router(stripe_router.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "suite-artisan-api"}
