from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Artisan, Client, Devis
from app.schemas import ClientPublicCreate, DevisAccepterIn, DevisPublicOut

router = APIRouter(prefix="/pub", tags=["public"])

DEVIS_STATUTS_CLOTURES = ("signe", "perdu", "expire")


def _get_devis_public_or_404(db: Session, token: str) -> Devis:
    devis = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client), joinedload(Devis.artisan))
        .filter(Devis.token == token)
        .first()
    )
    if devis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
    return devis


def _to_public_out(devis: Devis) -> DevisPublicOut:
    return DevisPublicOut(
        numero=devis.numero, titre=devis.titre, description=devis.description,
        client_nom=devis.client.nom, taux_tva=devis.taux_tva,
        acompte_pourcentage=devis.acompte_pourcentage, remise_pourcentage=devis.remise_pourcentage,
        montant_ht_brut=devis.montant_ht_brut, remise_montant=devis.remise_montant,
        montant_ht=devis.montant_ht, montant_ttc=devis.montant_ttc,
        statut=devis.statut, date_signature=devis.date_signature, nom_signataire=devis.nom_signataire,
        lignes=devis.lignes,
        artisan_nom_entreprise=devis.artisan.nom_entreprise, artisan_telephone=devis.artisan.telephone,
        artisan_email=devis.artisan.email, artisan_adresse=devis.artisan.adresse,
        artisan_siret=devis.artisan.siret, artisan_assurance_decennale_nom=devis.artisan.assurance_decennale_nom,
    )


@router.post("/{slug}/demande-devis", status_code=status.HTTP_201_CREATED)
def demande_devis(
    slug: str,
    payload: ClientPublicCreate,
    db: Session = Depends(get_db),
):
    """Endpoint PUBLIC (pas d'authentification) appele par le formulaire du
    site vitrine de l'artisan. Un visiteur qui demande un devis devient un
    PROSPECT dans le pipeline commercial de l'artisan (pas un devis direct :
    c'est l'artisan qui qualifie puis chiffre). Identifie l'artisan par son slug."""
    artisan = db.query(Artisan).filter(Artisan.slug == slug).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan introuvable")

    client = Client(
        artisan_id=artisan.id,
        nom=payload.nom,
        email=payload.email,
        telephone=payload.telephone,
        notes=payload.message,
        statut="nouveau",
        source="site_vitrine",
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return {"message": "Demande envoyee avec succes", "client_id": client.id}


@router.get("/devis/{token}", response_model=DevisPublicOut)
def voir_devis_public(token: str, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : ce que le client voit en ouvrant le lien de son
    devis (envoye par l'artisan, pas par email automatique - on n'a pas
    d'envoi transactionnel). Marque le devis "consulte" au passage, ce qui
    alimente le cycle de relance existant cote artisan."""
    devis = _get_devis_public_or_404(db, token)
    if devis.statut == "envoye":
        devis.statut = "consulte"
        devis.date_consultation = datetime.now(timezone.utc)
        db.commit()
        devis = _get_devis_public_or_404(db, token)
    return _to_public_out(devis)


@router.post("/devis/{token}/accepter", response_model=DevisPublicOut)
def accepter_devis_public(token: str, payload: DevisAccepterIn, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : le client accepte le devis en tapant son nom (la
    mention "bon pour accord" est deja sur le PDF/la page). Ce n'est pas une
    signature electronique qualifiee au sens juridique, mais une acceptation
    tracee (nom + date), ce qui est deja mieux que le statut "signe" pose a
    la main par l'artisan sans aucune confirmation du client."""
    devis = _get_devis_public_or_404(db, token)
    if devis.statut == "signe":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce devis a deja ete accepte")
    if devis.statut in ("perdu", "expire"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce devis n'est plus disponible")
    if not payload.nom_signataire.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Merci d'indiquer votre nom")

    devis.statut = "signe"
    devis.date_signature = datetime.now(timezone.utc)
    devis.nom_signataire = payload.nom_signataire.strip()
    devis.client.statut = "gagne"
    db.commit()
    devis = _get_devis_public_or_404(db, token)
    return _to_public_out(devis)
