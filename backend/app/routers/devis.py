from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan, require_active_subscription
from app.models import Artisan, Client, Devis, LigneDevis
from app.pdf import generate_devis_pdf
from app.schemas import DevisCreate, DevisOut, DevisUpdate

router = APIRouter(prefix="/devis", tags=["devis"])

# Cycle de relance : depuis quel statut, et combien de jours apres l'envoi
# la relance suivante devient due. Une fois "relance_j15" atteint, il n'y a
# plus de relance automatique : l'artisan doit marquer signe/perdu a la main.
STATUT_SUIVANT = {"envoye": "relance_j3", "consulte": "relance_j3", "relance_j3": "relance_j7", "relance_j7": "relance_j15"}
JOURS_SEUIL = {"envoye": 3, "consulte": 3, "relance_j3": 7, "relance_j7": 15}


def relance_due(devis: Devis) -> bool:
    if devis.statut not in JOURS_SEUIL or devis.date_envoi is None:
        return False
    echeance = devis.date_envoi + timedelta(days=JOURS_SEUIL[devis.statut])
    now = datetime.now(timezone.utc)
    if echeance.tzinfo is None:
        echeance = echeance.replace(tzinfo=timezone.utc)
    return now >= echeance


def _get_devis_or_404(db: Session, artisan: Artisan, devis_id: int) -> Devis:
    devis = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client))
        .filter(Devis.id == devis_id, Devis.artisan_id == artisan.id)
        .first()
    )
    if devis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
    return devis


def _to_out(devis: Devis) -> DevisOut:
    return DevisOut(
        id=devis.id, artisan_id=devis.artisan_id, client_id=devis.client_id,
        client_nom=devis.client.nom, numero=devis.numero, titre=devis.titre,
        description=devis.description, taux_tva=devis.taux_tva,
        acompte_pourcentage=devis.acompte_pourcentage, montant_ht=devis.montant_ht,
        montant_ttc=devis.montant_ttc, statut=devis.statut, date_envoi=devis.date_envoi,
        date_consultation=devis.date_consultation, date_derniere_relance=devis.date_derniere_relance,
        date_signature=devis.date_signature, nb_relances=devis.nb_relances, source=devis.source,
        created_at=devis.created_at, lignes=devis.lignes,
    )


def _generer_numero(db: Session, artisan: Artisan) -> str:
    annee = datetime.now().year
    count = db.query(Devis).filter(Devis.artisan_id == artisan.id).count()
    return f"DEV-{annee}-{count + 1:04d}"


def _resoudre_client(db: Session, artisan: Artisan, payload: DevisCreate) -> Client:
    if payload.client_id is not None:
        client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
        return client
    if payload.nouveau_client is not None:
        client = Client(artisan_id=artisan.id, source="manuel", **payload.nouveau_client.model_dump())
        db.add(client)
        db.flush()
        return client
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Indiquez client_id (client existant) ou nouveau_client (creation a la volee)",
    )


@router.get("", response_model=list[DevisOut])
def lister_devis(
    statut: Optional[str] = None,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    query = db.query(Devis).options(joinedload(Devis.lignes), joinedload(Devis.client)).filter(Devis.artisan_id == artisan.id)
    if statut:
        query = query.filter(Devis.statut == statut)
    if client_id:
        query = query.filter(Devis.client_id == client_id)
    return [_to_out(d) for d in query.order_by(Devis.created_at.desc()).all()]


@router.get("/a-relancer", response_model=list[DevisOut])
def devis_a_relancer(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Devis dont la prochaine relance (J+3 / J+7 / J+15) est due aujourd'hui."""
    candidats = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL.keys()))
        .all()
    )
    return [_to_out(d) for d in candidats if relance_due(d)]


@router.post("", response_model=DevisOut, status_code=status.HTTP_201_CREATED)
def creer_devis(
    payload: DevisCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = _resoudre_client(db, artisan, payload)
    numero = _generer_numero(db, artisan)

    devis = Devis(
        artisan_id=artisan.id, client_id=client.id, statut="nouveau", source="manuel",
        titre=payload.titre, description=payload.description, taux_tva=payload.taux_tva,
        acompte_pourcentage=payload.acompte_pourcentage, numero=numero,
    )
    db.add(devis)
    db.flush()

    for i, ligne in enumerate(payload.lignes):
        db.add(LigneDevis(devis_id=devis.id, ordre=i, **ligne.model_dump()))

    db.commit()
    devis = _get_devis_or_404(db, artisan, devis.id)
    return _to_out(devis)


@router.post("/{devis_id}/dupliquer", response_model=DevisOut, status_code=status.HTTP_201_CREATED)
def dupliquer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Cree un nouveau devis 'nouveau' en reprenant client, titre et lignes."""
    original = _get_devis_or_404(db, artisan, devis_id)
    numero = _generer_numero(db, artisan)

    copie = Devis(
        artisan_id=artisan.id, client_id=original.client_id, statut="nouveau", source="manuel",
        titre=original.titre, description=original.description, taux_tva=original.taux_tva,
        acompte_pourcentage=original.acompte_pourcentage, numero=numero,
    )
    db.add(copie)
    db.flush()
    for i, ligne in enumerate(original.lignes):
        db.add(LigneDevis(
            devis_id=copie.id, ordre=i, description=ligne.description,
            quantite=ligne.quantite, unite=ligne.unite, prix_unitaire_ht=ligne.prix_unitaire_ht,
        ))
    db.commit()
    copie = _get_devis_or_404(db, artisan, copie.id)
    return _to_out(copie)


@router.get("/{devis_id}", response_model=DevisOut)
def obtenir_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    return _to_out(_get_devis_or_404(db, artisan, devis_id))


@router.get("/{devis_id}/pdf")
def telecharger_devis_pdf(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    devis = _get_devis_or_404(db, artisan, devis_id)
    if not devis.lignes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ajoutez au moins une ligne avant de generer le PDF")
    pdf_bytes = generate_devis_pdf(devis, artisan)
    numero = devis.numero or f"devis-{devis.id}"
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{numero}.pdf"'},
    )


@router.patch("/{devis_id}", response_model=DevisOut)
def modifier_devis(
    devis_id: int,
    payload: DevisUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    devis = _get_devis_or_404(db, artisan, devis_id)
    updates = payload.model_dump(exclude_unset=True, exclude={"lignes"})
    for field, value in updates.items():
        setattr(devis, field, value)

    if payload.statut == "signe":
        devis.date_signature = datetime.now(timezone.utc)
        devis.client.statut = "gagne"
    elif payload.statut == "perdu":
        devis.client.statut = "perdu"

    if payload.lignes is not None:
        db.query(LigneDevis).filter(LigneDevis.devis_id == devis.id).delete()
        for i, ligne in enumerate(payload.lignes):
            db.add(LigneDevis(devis_id=devis.id, ordre=i, **ligne.model_dump()))

    db.commit()
    devis = _get_devis_or_404(db, artisan, devis_id)
    return _to_out(devis)


@router.post("/{devis_id}/envoyer", response_model=DevisOut)
def envoyer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Marque le devis comme envoye au client : demarre le cycle de relance."""
    devis = _get_devis_or_404(db, artisan, devis_id)
    if devis.montant_ht is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ajoutez au moins une ligne avant l'envoi")
    devis.statut = "envoye"
    devis.date_envoi = datetime.now(timezone.utc)
    if devis.client.statut in ("nouveau", "contacte", "qualification", "visite_prevue", "devis_a_faire"):
        devis.client.statut = "devis_envoye"
    db.commit()
    devis = _get_devis_or_404(db, artisan, devis_id)
    return _to_out(devis)


@router.post("/{devis_id}/relancer", response_model=DevisOut)
def relancer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Passe le devis a l'etape de relance suivante (envoye -> J+3 -> J+7 -> J+15).
    Fonction payante : necessite un abonnement actif."""
    devis = _get_devis_or_404(db, artisan, devis_id)
    if devis.statut not in STATUT_SUIVANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pas de relance possible depuis le statut '{devis.statut}'",
        )
    devis.statut = STATUT_SUIVANT[devis.statut]
    devis.date_derniere_relance = datetime.now(timezone.utc)
    devis.nb_relances += 1
    db.commit()
    devis = _get_devis_or_404(db, artisan, devis_id)
    return _to_out(devis)


@router.delete("/{devis_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    devis = _get_devis_or_404(db, artisan, devis_id)
    db.delete(devis)
    db.commit()
