from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models  # noqa: F401  (necessaire pour que les tables soient enregistrees)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # a restreindre en prod aux domaines des sites vitrines + du dashboard
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
