import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_active_subscription
from app import email_service
from app.models import Artisan, Chantier, Client, Devis, Facture, LigneFacture, Paiement
from app.numerotation import generer_numero
from app.pdf import generate_facture_pdf
from app.schemas import FactureCreate, FactureOut, FactureUpdate, PaiementCreate, PaiementOut

router = APIRouter(prefix="/factures", tags=["factures"])


def _nouveau_token() -> str:
    return secrets.token_urlsafe(24)


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
        date_envoi=facture.date_envoi, notes=facture.notes,
        date_derniere_relance=facture.date_derniere_relance, nb_relances=facture.nb_relances,
        token=facture.token, created_at=facture.created_at,
        lignes=facture.lignes, paiements=facture.paiements,
    )


def relance_facture_due(facture: Facture, artisan: Artisan) -> bool:
    """Une facture merite une relance si elle est en retard de paiement,
    et soit jamais relancee, soit relancee il y a artisan.relance_facture_jours
    jours ou plus (rythme configurable tant que l'impaye n'est pas regularise)."""
    if not facture.est_en_retard:
        return False
    if facture.date_derniere_relance is None:
        return True
    derniere_relance = facture.date_derniere_relance
    now = datetime.now(timezone.utc)
    if derniere_relance.tzinfo is None:
        derniere_relance = derniere_relance.replace(tzinfo=timezone.utc)
    return (now - derniere_relance).days >= artisan.relance_facture_jours


def _generer_numero(db: Session, artisan: Artisan) -> str:
    return generer_numero(db, artisan.id, "facture", "FAC")


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
    archive: bool = False,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    query = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client))
        .filter(Facture.artisan_id == artisan.id, Facture.archive.is_(archive))
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


@router.get("/a-relancer", response_model=list[FactureOut])
def factures_a_relancer(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Factures impayees dont la prochaine relance est due (voir relance_facture_due)."""
    factures = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.notin_(("brouillon", "annulee", "payee")))
        .all()
    )
    for f in factures:
        _recalculer_statut(f)
    db.commit()
    return [_to_out(f) for f in factures if relance_facture_due(f, artisan)]


@router.post("/{facture_id}/relancer", response_model=FactureOut)
def relancer_facture(
    facture_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Enregistre qu'une relance a ete envoyee au client pour cette facture impayee."""
    facture = _get_facture_or_404(db, artisan, facture_id)
    if facture.montant_restant <= 0 or facture.statut in ("brouillon", "annulee"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette facture n'a pas d'impaye a relancer")
    facture.date_derniere_relance = datetime.now(timezone.utc)
    facture.nb_relances += 1
    db.commit()
    facture = _get_facture_or_404(db, artisan, facture_id)
    return _to_out(facture)


@router.post("", response_model=FactureOut, status_code=status.HTTP_201_CREATED)
def creer_facture(
    payload: FactureCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    devis = None
    if payload.devis_id is not None:
        devis = db.query(Devis).filter(Devis.id == payload.devis_id, Devis.artisan_id == artisan.id).first()
        if devis is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
        if devis.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le devis ne correspond pas au client de la facture")

    chantier = None
    if payload.chantier_id is not None:
        chantier = db.query(Chantier).filter(Chantier.id == payload.chantier_id, Chantier.artisan_id == artisan.id).first()
        if chantier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chantier introuvable")
        if chantier.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le chantier ne correspond pas au client de la facture")
        if devis is not None and chantier.devis_id is not None and chantier.devis_id != devis.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le chantier ne correspond pas au devis de la facture")

    numero = _generer_numero(db, artisan)
    facture = Facture(
        artisan_id=artisan.id, client_id=client.id, devis_id=payload.devis_id, chantier_id=payload.chantier_id,
        type=payload.type, taux_tva=payload.taux_tva, statut="brouillon", numero=numero,
        date_echeance=payload.date_echeance, notes=payload.notes, token=_nouveau_token(),
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
    artisan: Artisan = Depends(require_active_subscription),
):
    """Convertit un devis signe en facture : reprend le client et les lignes."""
    devis = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client))
        .filter(Devis.id == devis_id, Devis.artisan_id == artisan.id)
        .first()
    )
    if devis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
    if devis.client is None or devis.client.artisan_id != artisan.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    if devis.statut != "signe":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seul un devis signe peut etre facture")

    numero = _generer_numero(db, artisan)
    facture = Facture(
        artisan_id=artisan.id, client_id=devis.client_id, devis_id=devis.id,
        type=type, taux_tva=devis.taux_tva, statut="brouillon", numero=numero,
        date_echeance=date.today() + timedelta(days=30), token=_nouveau_token(),
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
    artisan: Artisan = Depends(require_active_subscription),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    _recalculer_statut(facture)
    db.commit()
    return _to_out(facture)


@router.get("/{facture_id}/pdf")
def telecharger_facture_pdf(
    facture_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    if not facture.lignes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette facture n'a pas de lignes")
    pdf_bytes = generate_facture_pdf(facture, artisan)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{facture.numero}.pdf"'},
    )


@router.patch("/{facture_id}", response_model=FactureOut)
def modifier_facture(
    facture_id: int,
    payload: FactureUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
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
    artisan: Artisan = Depends(require_active_subscription),
):
    """Archive la facture plutot que de la supprimer definitivement (section 44) :
    jamais de perte d'un document financier, meme retire des listes actives."""
    facture = _get_facture_or_404(db, artisan, facture_id)
    facture.archive = True
    db.commit()


@router.post("/{facture_id}/restaurer", response_model=FactureOut)
def restaurer_facture(
    facture_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    facture.archive = False
    db.commit()
    facture = _get_facture_or_404(db, artisan, facture_id)
    return _to_out(facture)


@router.post("/{facture_id}/paiements", response_model=FactureOut, status_code=status.HTTP_201_CREATED)
def ajouter_paiement(
    facture_id: int,
    payload: PaiementCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    facture = _get_facture_or_404(db, artisan, facture_id)
    paiement = Paiement(facture_id=facture.id, **payload.model_dump())
    db.add(paiement)
    db.commit()
    facture = _get_facture_or_404(db, artisan, facture_id)
    _recalculer_statut(facture)
    db.commit()
    facture = _get_facture_or_404(db, artisan, facture_id)

    email_service.send_paiement_recu(db, paiement, facture, artisan)

    return _to_out(facture)
