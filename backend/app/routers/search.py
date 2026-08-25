from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Chantier, Client, Devis, Facture
from app.schemas import SearchResult

router = APIRouter(tags=["recherche"])

LIMITE_PAR_TYPE = 5


@router.get("/search", response_model=list[SearchResult])
def rechercher(
    q: str,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Recherche globale (Ctrl+K) : clients/prospects, devis, factures, chantiers."""
    if not q or len(q.strip()) < 2:
        return []
    terme = f"%{q.strip()}%"
    resultats: list[SearchResult] = []

    clients = (
        db.query(Client)
        .filter(Client.artisan_id == artisan.id)
        .filter((Client.nom.ilike(terme)) | (Client.email.ilike(terme)) | (Client.telephone.ilike(terme)))
        .limit(LIMITE_PAR_TYPE)
        .all()
    )
    for c in clients:
        resultats.append(SearchResult(type="client", id=c.id, label=c.nom, sublabel=c.telephone or c.email or ""))

    devis_list = (
        db.query(Devis)
        .filter(Devis.artisan_id == artisan.id)
        .filter((Devis.numero.ilike(terme)) | (Devis.titre.ilike(terme)))
        .limit(LIMITE_PAR_TYPE)
        .all()
    )
    for d in devis_list:
        resultats.append(SearchResult(type="devis", id=d.id, label=d.numero or f"Devis #{d.id}", sublabel=d.titre or ""))

    factures = (
        db.query(Facture)
        .filter(Facture.artisan_id == artisan.id, Facture.numero.ilike(terme))
        .limit(LIMITE_PAR_TYPE)
        .all()
    )
    for f in factures:
        resultats.append(SearchResult(type="facture", id=f.id, label=f.numero, sublabel=f.type))

    chantiers = (
        db.query(Chantier)
        .filter(Chantier.artisan_id == artisan.id, Chantier.titre.ilike(terme))
        .limit(LIMITE_PAR_TYPE)
        .all()
    )
    for c in chantiers:
        resultats.append(SearchResult(type="chantier", id=c.id, label=c.titre, sublabel=c.adresse or ""))

    return resultats
