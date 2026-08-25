from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Client, Devis, Facture, Chantier
from app.schemas import ClientCreate, ClientOut, ClientUpdate, TimelineEntry

router = APIRouter(prefix="/clients", tags=["clients"])


def _get_client_or_404(db: Session, artisan: Artisan, client_id: int) -> Client:
    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.artisan_id == artisan.id)
        .first()
    )
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return client


@router.get("", response_model=list[ClientOut])
def lister_clients(
    statut: str | None = None,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    query = db.query(Client).filter(Client.artisan_id == artisan.id)
    if statut:
        query = query.filter(Client.statut == statut)
    return query.order_by(Client.created_at.desc()).all()


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def creer_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = Client(artisan_id=artisan.id, source="manuel", **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
def obtenir_client(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    return _get_client_or_404(db, artisan, client_id)


@router.patch("/{client_id}", response_model=ClientOut)
def modifier_client(
    client_id: int,
    payload: ClientUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = _get_client_or_404(db, artisan, client_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_client(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = _get_client_or_404(db, artisan, client_id)
    db.delete(client)
    db.commit()


@router.get("/{client_id}/timeline", response_model=list[TimelineEntry])
def timeline_client(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Reconstruit l'historique de la relation avec ce client a partir des
    devis/factures/chantiers existants (pas de table de log separee a
    maintenir : la timeline est toujours a jour par construction)."""
    client = _get_client_or_404(db, artisan, client_id)
    entries: list[TimelineEntry] = []

    entries.append(TimelineEntry(date=client.created_at, type="prospect_cree", label=f"Prospect cree ({client.source})"))

    devis_list = db.query(Devis).filter(Devis.client_id == client.id).all()
    for d in devis_list:
        entries.append(TimelineEntry(date=d.created_at, type="devis_cree", label=f"Devis #{d.id} cree", reference_id=d.id))
        if d.date_envoi:
            entries.append(TimelineEntry(date=d.date_envoi, type="devis_envoye", label=f"Devis #{d.id} envoye", reference_id=d.id))
        if d.date_consultation:
            entries.append(TimelineEntry(date=d.date_consultation, type="devis_consulte", label=f"Devis #{d.id} consulte", reference_id=d.id))
        if d.date_derniere_relance:
            entries.append(TimelineEntry(date=d.date_derniere_relance, type="devis_relance", label=f"Devis #{d.id} relance", reference_id=d.id))
        if d.date_signature:
            entries.append(TimelineEntry(date=d.date_signature, type="devis_signe", label=f"Devis #{d.id} signe", reference_id=d.id))

    factures_list = db.query(Facture).filter(Facture.client_id == client.id).all()
    for f in factures_list:
        entries.append(TimelineEntry(date=f.created_at, type="facture_creee", label=f"Facture {f.numero} creee", reference_id=f.id))
        if f.date_envoi:
            entries.append(TimelineEntry(date=f.date_envoi, type="facture_envoyee", label=f"Facture {f.numero} envoyee", reference_id=f.id))
        for p in f.paiements:
            entries.append(TimelineEntry(
                date=p.created_at, type="paiement_recu",
                label=f"Paiement de {p.montant} EUR recu sur {f.numero}", reference_id=f.id,
            ))

    chantiers_list = db.query(Chantier).filter(Chantier.client_id == client.id).all()
    for c in chantiers_list:
        entries.append(TimelineEntry(date=c.created_at, type="chantier_cree", label=f"Chantier '{c.titre}' cree", reference_id=c.id))

    entries.sort(key=lambda e: e.date)
    return entries
