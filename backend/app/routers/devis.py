import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app import email_service
from app.config import settings
from app.database import get_db
from app.deps import get_current_artisan, require_plan
from app.models import Artisan, Client, Devis, EmailLog, LigneDevis
from app.numerotation import generer_numero
from app.pdf import generate_devis_pdf
from app.schemas import DevisCreate, DevisOut, DevisUpdate, RelanceDevisOut


def _nouveau_token() -> str:
    return secrets.token_urlsafe(24)

router = APIRouter(prefix="/devis", tags=["devis"])

# Cycle de relance : depuis quel statut, et combien de jours apres l'envoi
# la relance suivante devient due. Une fois "relance_j15" atteint, il n'y a
# plus de relance automatique : l'artisan doit marquer signe/perdu a la main.
# Les statuts eligibles a une relance sont fixes ; les delais (j1/j2/j3) sont
# configurables par artisan (voir Artisan.relance_devis_j1/j2/j3).
STATUT_SUIVANT = {"envoye": "relance_j3", "consulte": "relance_j3", "relance_j3": "relance_j7", "relance_j7": "relance_j15"}
JOURS_SEUIL_STATUTS = ("envoye", "consulte", "relance_j3", "relance_j7")
DELAI_RELANCE_MANUELLE_HEURES = 20

# Source unique (V5 section 10) : dashboard.py et analytics.py importent
# cette constante plutot que de la redefinir chacun de leur cote - deux
# copies identiques aujourd'hui auraient pu diverger silencieusement au
# prochain changement et faire afficher un pipeline different au tableau
# de bord et dans les statistiques pour les memes donnees.
DEVIS_STATUTS_FINAUX = ("signe", "perdu", "expire")


def _palier_relance(statut: str) -> int:
    return {"envoye": 1, "consulte": 1, "relance_j3": 2, "relance_j7": 3}.get(statut, 1)


def _jours_seuil(artisan: Artisan) -> dict:
    return {
        "envoye": artisan.relance_devis_j1, "consulte": artisan.relance_devis_j1,
        "relance_j3": artisan.relance_devis_j2, "relance_j7": artisan.relance_devis_j3,
    }


def relance_due(devis: Devis, artisan: Artisan) -> bool:
    seuils = _jours_seuil(artisan)
    if devis.statut not in seuils or devis.date_envoi is None:
        return False
    echeance = devis.date_envoi + timedelta(days=seuils[devis.statut])
    now = datetime.now(timezone.utc)
    if echeance.tzinfo is None:
        echeance = echeance.replace(tzinfo=timezone.utc)
    return now >= echeance


def _get_devis_or_404(db: Session, artisan: Artisan, devis_id: int, *, for_update: bool = False) -> Devis:
    query = db.query(Devis).filter(Devis.id == devis_id, Devis.artisan_id == artisan.id)
    if for_update:
        query = query.with_for_update()
    else:
        query = query.options(joinedload(Devis.lignes), joinedload(Devis.client))
    devis = query.first()
    if devis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
    return devis


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _derniere_tentative_relance(db: Session, devis: Devis) -> datetime | None:
    log = (
        db.query(EmailLog)
        .filter(
            EmailLog.artisan_id == devis.artisan_id,
            EmailLog.type == "relance_devis",
            EmailLog.devis_id == devis.id,
        )
        .order_by(EmailLog.created_at.desc())
        .first()
    )
    dates = [_as_utc(devis.date_derniere_relance), _as_utc(log.created_at) if log else None]
    return max((value for value in dates if value is not None), default=None)


def relance_manuelle_disponible_le(db: Session, devis: Devis) -> datetime | None:
    derniere_tentative = _derniere_tentative_relance(db, devis)
    if derniere_tentative is None:
        return None
    return derniere_tentative + timedelta(hours=DELAI_RELANCE_MANUELLE_HEURES)


def _to_out(devis: Devis, db: Session | None = None) -> DevisOut:
    disponible_le = relance_manuelle_disponible_le(db, devis) if db is not None else None
    relance_possible = not devis.archive and devis.statut in STATUT_SUIVANT and (
        disponible_le is None or datetime.now(timezone.utc) >= disponible_le
    )
    return DevisOut(
        id=devis.id, artisan_id=devis.artisan_id, client_id=devis.client_id,
        client_nom=devis.client.nom, numero=devis.numero, titre=devis.titre,
        description=devis.description, taux_tva=devis.taux_tva,
        acompte_pourcentage=devis.acompte_pourcentage, remise_pourcentage=devis.remise_pourcentage,
        montant_ht_brut=devis.montant_ht_brut, remise_montant=devis.remise_montant,
        montant_ht=devis.montant_ht,
        montant_ttc=devis.montant_ttc, statut=devis.statut, date_envoi=devis.date_envoi,
        date_consultation=devis.date_consultation, date_derniere_relance=devis.date_derniere_relance,
        date_signature=devis.date_signature, nom_signataire=devis.nom_signataire,
        nb_relances=devis.nb_relances, source=devis.source, token=devis.token,
        relance_manuelle_possible=relance_possible,
        relance_manuelle_disponible_le=disponible_le,
        created_at=devis.created_at, lignes=devis.lignes,
    )


def _generer_numero(db: Session, artisan: Artisan) -> str:
    return generer_numero(db, artisan.id, "devis", "DEV")


def _resoudre_client(db: Session, artisan: Artisan, payload: DevisCreate) -> Client:
    if payload.client_id is not None:
        client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
        return client
    if payload.nouveau_client is not None:
        client = Client(artisan_id=artisan.id, **payload.nouveau_client.model_dump())
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
    archive: bool = False,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    query = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.archive.is_(archive))
    )
    if statut:
        query = query.filter(Devis.statut == statut)
    if client_id:
        query = query.filter(Devis.client_id == client_id)
    return [_to_out(d, db) for d in query.order_by(Devis.created_at.desc()).all()]


@router.get("/a-relancer", response_model=list[DevisOut])
def devis_a_relancer(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Devis dont la prochaine relance (J+3 / J+7 / J+15) est due aujourd'hui."""
    candidats = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL_STATUTS))
        .all()
    )
    return [_to_out(d, db) for d in candidats if relance_due(d, artisan)]


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
        acompte_pourcentage=payload.acompte_pourcentage, remise_pourcentage=payload.remise_pourcentage,
        numero=numero, token=_nouveau_token(),
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
        acompte_pourcentage=original.acompte_pourcentage, remise_pourcentage=original.remise_pourcentage,
        numero=numero, token=_nouveau_token(),
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


@router.post("/{devis_id}/relancer", response_model=RelanceDevisOut)
def relancer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_plan("essentiel")),
):
    """Envoie une relance manuelle Essentiel+ sans modifier le cycle Pro automatique."""
    devis = _get_devis_or_404(db, artisan, devis_id, for_update=True)
    if devis.archive or devis.statut not in STATUT_SUIVANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pas de relance possible depuis le statut '{devis.statut}'",
        )
    disponible_le = relance_manuelle_disponible_le(db, devis)
    if disponible_le is not None and datetime.now(timezone.utc) < disponible_le:
        secondes = max(1, int((disponible_le - datetime.now(timezone.utc)).total_seconds()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Une relance vient déjà d'être tentée pour ce devis. Réessayez plus tard.",
            headers={"Retry-After": str(secondes)},
        )

    if not devis.token:
        devis.token = _nouveau_token()
        db.flush()
    statut_initial = devis.statut
    url = f"{settings.app_base_url.rstrip('/')}/devis-public.html?t={devis.token}"
    log = email_service.send_relance_devis(db, devis, artisan, url, _palier_relance(statut_initial))

    messages = {
        "envoye": "Relance envoyée par email.",
        "non_configure": "Relance non envoyée : le service email n'est pas configuré.",
        "sans_destinataire": "Relance non envoyée : ce client n'a pas d'adresse email.",
        "echec": "Relance non envoyée : le fournisseur email a refusé ou interrompu l'envoi.",
    }
    if log.statut == "envoye":
        devis.statut = STATUT_SUIVANT[statut_initial]
        devis.date_derniere_relance = datetime.now(timezone.utc)
        devis.nb_relances += 1
        db.commit()

    devis = _get_devis_or_404(db, artisan, devis_id)
    devis_out = _to_out(devis, db)
    return RelanceDevisOut(
        **devis_out.model_dump(),
        email_statut=log.statut,
        message=messages.get(log.statut, "Tentative de relance enregistrée."),
    )


@router.delete("/{devis_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Archive le devis plutot que de le supprimer definitivement (section 44) :
    disparait des listes actives, reste consultable en base (historique
    commercial, references depuis un chantier/une facture)."""
    devis = _get_devis_or_404(db, artisan, devis_id)
    devis.archive = True
    db.commit()


@router.post("/{devis_id}/restaurer", response_model=DevisOut)
def restaurer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    devis = _get_devis_or_404(db, artisan, devis_id)
    devis.archive = False
    db.commit()
    devis = _get_devis_or_404(db, artisan, devis_id)
    return _to_out(devis)
