import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.startup_checks import valider_configuration
from app import models  # noqa: F401  (necessaire pour que les tables soient enregistrees)

# Logs vers stdout/stderr (pas de fichier, pas de plateforme externe) : c'est
# l'attente standard d'un environnement de deploiement conteneurise, qui
# collecte les logs process par process plutot que par fichier.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("suite_artisan")

# Refuse de demarrer sur une configuration manifestement dangereuse (secret de
# dev en production, SQLite en production, S3 demande mais incomplet...) -
# voir app/startup_checks.py pour le detail de chaque verification.
valider_configuration(settings)

logger.info(
    "Demarrage Suite Artisan - environnement=%s, base=%s, storage=%s, scheduler=%s",
    settings.app_env,
    "sqlite" if settings.database_url.startswith("sqlite") else "postgresql",
    settings.storage_backend,
    "enabled" if settings.scheduler_enabled else "disabled",
)

from app.routers import (
    admin,
    analytics,
    automation,
    auth,
    avis,
    chantiers,
    clients,
    conformite,
    contrats,
    dashboard,
    devis,
    documents,
    equipe,
    factures,
    fournisseurs,
    notifications,
    planning,
    prestations,
    public,
    search,
    site_media,
    stripe_router,
    taches,
)

# Filet de securite pour le developpement local (cree les tables manquantes
# sur une base neuve). Ne gere PAS les evolutions de schema d'une base
# existante (ajout de colonne, etc.) : c'est le role d'Alembic desormais
# (voir backend/migrations/). Conditionne au mode developpement : en
# production, le schema doit etre gere exclusivement par
# "alembic upgrade head" (voir docs/PRODUCTION.md), jamais par cet appel -
# meme si create_all() est idempotent (ne touche jamais les tables deja
# existantes), executer les deux mecanismes en parallele en production
# n'apporte rien et ajoute une source de confusion en cas de derive du schema.
if settings.app_env == "production":
    logger.info("APP_ENV=production : schema gere par Alembic uniquement (create_all() non execute).")
else:
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.admin_service import ensure_bootstrap_admin
    from app.scheduler import start_scheduler, stop_scheduler

    db = SessionLocal()
    try:
        try:
            ensure_bootstrap_admin(db)
        except Exception:
            # Le serveur doit rester joignable pour que /ready expose l'indisponibilite
            # de la base sans divulguer les details techniques de la connexion.
            logger.error("Initialisation du compte Admin impossible : base de donnees indisponible")
    finally:
        db.close()

    if settings.scheduler_enabled:
        logger.info("Scheduler enabled")
        start_scheduler()
    else:
        logger.info("Scheduler disabled")
    yield
    if settings.scheduler_enabled:
        stop_scheduler()


app = FastAPI(title="Suite Artisan API", version="0.1.0", lifespan=lifespan)

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
    # allow_credentials=True n'a de sens qu'avec des cookies de session : le
    # frontend n'utilise jamais credentials:'include' (auth par header Bearer
    # uniquement). Combine a allow_origins=["*"] ce serait de toute facon une
    # config CORS invalide (rejetee par le navigateur) : on ne l'active donc
    # que si des origines precises sont configurees.
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Les HTTPException levees volontairement dans les routers portent deja un
    # message clair pour l'utilisateur (ex: "Client introuvable") : on les
    # laisse passer telles quelles, juste normalisees en JSON {"detail": ...}.
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Donnees invalides. Verifiez les champs du formulaire."})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Regle section 41 (cahier des charges V4) : aucune erreur technique brute
    # ne doit atteindre l'utilisateur. Le detail complet (type, message, trace)
    # part dans les logs serveur pour le diagnostic ; l'utilisateur ne voit
    # qu'un message actionnable.
    logger.exception("Erreur non geree sur %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur inattendue s'est produite. Reessayez. Si le probleme persiste, contactez le support."},
    )

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(clients.router)
app.include_router(devis.router)
app.include_router(factures.router)
app.include_router(chantiers.router)
app.include_router(conformite.router)
app.include_router(fournisseurs.router)
app.include_router(contrats.router)
app.include_router(taches.router)
app.include_router(planning.router)
app.include_router(documents.router)
app.include_router(prestations.router)
app.include_router(avis.router)
app.include_router(equipe.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(automation.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(site_media.router)
app.include_router(public.router)
app.include_router(stripe_router.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "suite-artisan-api"}


@app.get("/health")
def health_check():
    """Healthcheck processus : repond des que le serveur HTTP tourne, sans
    toucher a la DB ni au storage. Pour un hebergeur qui veut juste savoir si
    le process est vivant avant de router du trafic dessus."""
    return {"status": "ok"}


@app.get("/ready")
def readiness_check():
    """Readiness : verifie que la DB repond reellement (SELECT 1, jamais
    d'ecriture). N'interroge jamais le storage S3/R2 - un healthcheck qui
    ferait un appel reseau externe a chaque probe serait lui-meme une source
    d'indisponibilite. Ne renvoie jamais le detail technique de l'erreur
    (DATABASE_URL, message d'exception...) : juste un statut, le detail part
    dans les logs serveur."""
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        logger.exception("Readiness check : la base de donnees ne repond pas")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}
