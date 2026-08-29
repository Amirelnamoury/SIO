from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Chantier, Client, Evenement, Tache
from app.schemas import EvenementCreate, EvenementOut, EvenementUpdate, PlanningItem

router = APIRouter(tags=["planning"])


def _get_evenement_or_404(db: Session, artisan: Artisan, evenement_id: int) -> Evenement:
    evenement = db.query(Evenement).filter(Evenement.id == evenement_id, Evenement.artisan_id == artisan.id).first()
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evenement introuvable")
    return evenement


def _verifier_proprietaire(db: Session, artisan: Artisan, client_id: int | None, chantier_id: int | None) -> None:
    """Meme principe que taches.py : un evenement rattache a un client/
    chantier doit appartenir a l'artisan qui le cree."""
    if client_id is not None and db.query(Client).filter(Client.id == client_id, Client.artisan_id == artisan.id).first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    if chantier_id is not None and db.query(Chantier).filter(Chantier.id == chantier_id, Chantier.artisan_id == artisan.id).first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chantier introuvable")


@router.get("/evenements", response_model=list[EvenementOut])
def lister_evenements(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    return db.query(Evenement).filter(Evenement.artisan_id == artisan.id).order_by(Evenement.date_debut).all()


@router.post("/evenements", response_model=EvenementOut, status_code=status.HTTP_201_CREATED)
def creer_evenement(
    payload: EvenementCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    _verifier_proprietaire(db, artisan, payload.client_id, payload.chantier_id)
    evenement = Evenement(artisan_id=artisan.id, **payload.model_dump())
    db.add(evenement)
    db.commit()
    db.refresh(evenement)
    return evenement


@router.patch("/evenements/{evenement_id}", response_model=EvenementOut)
def modifier_evenement(
    evenement_id: int,
    payload: EvenementUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    evenement = _get_evenement_or_404(db, artisan, evenement_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(evenement, field, value)
    db.commit()
    db.refresh(evenement)
    return evenement


@router.delete("/evenements/{evenement_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_evenement(
    evenement_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    evenement = _get_evenement_or_404(db, artisan, evenement_id)
    db.delete(evenement)
    db.commit()


@router.get("/planning", response_model=list[PlanningItem])
def obtenir_planning(
    debut: date,
    fin: date,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Vue planning unifiee sur une periode : rendez-vous/visites/interventions
    (evenements), echeances de taches et dates de debut de chantier. Calcule a
    la volee plutot que duplique dans une table a part."""
    debut_dt = datetime.combine(debut, time.min, tzinfo=timezone.utc)
    fin_dt = datetime.combine(fin, time.max, tzinfo=timezone.utc)

    items: list[PlanningItem] = []

    evenements = (
        db.query(Evenement)
        .filter(Evenement.artisan_id == artisan.id, Evenement.date_debut >= debut_dt, Evenement.date_debut <= fin_dt)
        .all()
    )
    for e in evenements:
        items.append(PlanningItem(
            date=e.date_debut, type=e.type, titre=e.titre,
            reference_id=e.id, client_id=e.client_id, chantier_id=e.chantier_id, lieu=e.lieu,
        ))

    taches = (
        db.query(Tache)
        .filter(Tache.artisan_id == artisan.id, Tache.statut == "a_faire",
                 Tache.echeance >= debut, Tache.echeance <= fin)
        .all()
    )
    for t in taches:
        items.append(PlanningItem(
            date=datetime.combine(t.echeance, time(9, 0), tzinfo=timezone.utc), type="tache", titre=t.titre,
            reference_id=t.id, client_id=t.client_id, chantier_id=t.chantier_id,
        ))

    chantiers = (
        db.query(Chantier)
        .filter(Chantier.artisan_id == artisan.id, Chantier.date_debut >= debut, Chantier.date_debut <= fin)
        .all()
    )
    for c in chantiers:
        items.append(PlanningItem(
            date=datetime.combine(c.date_debut, time(8, 0), tzinfo=timezone.utc), type="chantier_debut",
            titre=f"Début chantier : {c.titre}", reference_id=c.id, client_id=c.client_id, chantier_id=c.id,
        ))

    def _sort_key(item: PlanningItem) -> datetime:
        # SQLite ne conserve pas le fuseau horaire : une date relue depuis la
        # base peut revenir "naive" alors que les dates qu'on construit ici
        # sont "aware". On uniformise pour eviter un TypeError a la comparaison.
        d = item.date
        return d if d.tzinfo is not None else d.replace(tzinfo=timezone.utc)

    items.sort(key=_sort_key)
    return items
