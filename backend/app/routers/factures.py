from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Client, Devis, Facture, LigneFacture, Paiement
from app.schemas import FactureCreate, FactureOut, FactureUpdate, PaiementCreate, PaiementOut

router = APIRouter(prefix="/factures", tags=["factures"])


def _get_facture_or_404(db: Session, artisan: Artisan, facture_id: int) -> Facture:
    facture = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client))
        .filter(Facture.id == facture_id, Facture.artisan_id == artisan.id)
        .first()
    )
    if facture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facture introuvable")
    return facture


def _to_out(facture: Facture) -> FactureOut:
    return FactureOut(
        id=facture.id, artisan_id=facture.artisan_id, client_id=facture.client_id,
        client_nom=facture.client.nom, devis_id=facture.devis_id, chantier_id=facture.chantier_id,
        numero=facture.numero, type=facture.type, taux_tva=facture.taux_tva, statut=facture.statut,
        montant_ht=facture.montant_ht, montant_ttc=facture.montant_ttc, montant_paye=facture.montant_paye,
        montant_restant=facture.montant_restant, est_en_retard=facture.est_en_retard,
        date_emission=facture.date_emission, date_echeance=facture.date_echeance,
        date_envoi=facture.date_envoi, notes=facture.notes, created_at=facture.created_at,
        lignes=facture.lignes, paiements=facture.paiements,
    )


def _generer_numero(db: Session, artisan: Artisan) -> str:
    annee = datetime.now().year
    count = db.query(Facture).filter(Facture.artisan_id == artisan.id).count()
    return f"FAC-{annee}-{count + 1:04d}"


def _recalculer_statut(facture: Facture) -> None:
    """Deduit le statut de la facture a partir des paiements recus, sauf si
    elle est encore en brouillon ou annulee (etats manuels)."""
    if facture.statut in ("brouillon", "annulee"):
        return
    if facture.montant_restant <= 0:
        facture.statut = "payee"
    elif facture.montant_paye > 0:
        facture.statut = "partiellement_payee"
    elif facture.est_en_retard:
        facture.statut = "en_retard"
    else:
        facture.statut = "envoyee"


@router.get("", response_model=list[FactureOut])
def lister_factures(
    statut: Optional[str] = None,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    query = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client))
        .filter(Facture.artisan_id == artisan.id)
    )
    if statut:
        query = query.filter(Facture.statut == statut)
    if client_id:
        query = query.filter(Facture.client_id == client_id)
    factures = query.order_by(Facture.created_at.desc()).all()
    for f in factures:
        _recalculer_statut(f)
    db.commit()
    return [_to_out(f) for f in factures]


@router.post("", response_model=FactureOut, status_code=status.HTTP_201_CREATED)
def creer_facture(
    payload: FactureCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    if payload.devis_id is not None:
        devis = db.query(Devis).filter(Devis.id == payload.devis_id, Devis.artisan_id == artisan.id).first()
        if devis is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")

    numero = _generer_numero(db, artisan)
    facture = Facture(
        artisan_id=artisan.id, client_id=client.id, devis_id=payload.devis_id, chantier_id=payload.chantier_id,
        type=payload.type, taux_tva=payload.taux_tva, statut="brouillon", numero=numero,
        date_echeance=payload.date_echeance, notes=payload.notes,
    )
    db.add(facture)
    db.flush()

    for i, ligne in enumerate(payload.lignes):
        db.add(LigneFacture(facture_id=facture.id, ordre=i, **ligne.model_dump()))

    db.commit()
    facture = _get_facture_or_404(db, artisan, facture.id)
    return _to_out(facture)


@router.post("/depuis-devis/{devis_id}", response_model=FactureOut, status_code=status.HTTP_201_CREATED)
def creer_facture_depuis_devis(
    devis_id: int,
    type: str = "standard",
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Convertit un devis signe en facture : reprend le client et les lignes."""
    devis = (
        db.query(Devis)
        .options(joinedload(Devis.lignes))
        .filter(Devis.id == devis_id, Devis.artisan_id == artisan.id)
        .first()
    )
    if devis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
    if devis.statut != "signe":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seul un devis signe peut etre facture")

    numero = _generer_numero(db, artisan)
    facture = Facture(
        artisan_id=artisan.id, client_id=devis.client_id, devis_id=devis.id,
        type=type, taux_tva=devis.taux_tva, statut="brouillon", numero=numero,
        date_echeance=date.today() + timedelta(days=30),
    )
    db.add(facture)
    db.flush()

    for i, ligne in enumerate(devis.lignes):
        db.add(LigneFacture(
            facture_id=facture.id, ordre=i, description=ligne.description,
            quantite=ligne.quantite, unite=ligne.unite, prix_unitaire_ht=ligne.prix_unitaire_ht,
        ))

    db.commit()
    facture = _get_facture_or_404(db, artisan, facture.id)
    return _to_out(facture)


@router.get("/{facture_id}", response_model=FactureOut)
def obtenir_facture(
    facture_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    _recalculer_statut(facture)
    db.commit()
    return _to_out(facture)


@router.patch("/{facture_id}", response_model=FactureOut)
def modifier_facture(
    facture_id: int,
    payload: FactureUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    updates = payload.model_dump(exclude_unset=True, exclude={"lignes"})
    for field, value in updates.items():
        setattr(facture, field, value)
    if updates.get("statut") == "envoyee" and facture.date_envoi is None:
        facture.date_envoi = datetime.now(timezone.utc)

    if payload.lignes is not None:
        db.query(LigneFacture).filter(LigneFacture.facture_id == facture.id).delete()
        for i, ligne in enumerate(payload.lignes):
            db.add(LigneFacture(facture_id=facture.id, ordre=i, **ligne.model_dump()))

    db.commit()
    facture = _get_facture_or_404(db, artisan, facture_id)
    return _to_out(facture)


@router.delete("/{facture_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_facture(
    facture_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    db.delete(facture)
    db.commit()


@router.post("/{facture_id}/paiements", response_model=FactureOut, status_code=status.HTTP_201_CREATED)
def ajouter_paiement(
    facture_id: int,
    payload: PaiementCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    db.add(Paiement(facture_id=facture.id, **payload.model_dump()))
    db.commit()
    facture = _get_facture_or_404(db, artisan, facture_id)
    _recalculer_statut(facture)
    db.commit()
    facture = _get_facture_or_404(db, artisan, facture_id)
    return _to_out(facture)
