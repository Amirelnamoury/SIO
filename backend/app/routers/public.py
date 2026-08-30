from datetime import datetime, timedelta, timezone
import logging
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app import email_service
from app.database import get_db
from app.models import Artisan, Avis, Chantier, Client, Devis, Document, Facture, Message, Notification
from app.rate_limit import rate_limiter
from app.routers.clients import PORTAIL_VALIDITE_JOURS
from app.schemas import (
    AvisPublicIn,
    AvisPublicSiteOut,
    AvisPublicStatutOut,
    ClientPublicCreate,
    DevisAccepterIn,
    DevisPublicOut,
    FacturePublicOut,
    MessageCreate,
    MessageOut,
    PortailChantierOut,
    PortailClientOut,
    PortailDevisOut,
    PortailFactureOut,
    PortailPhotoOut,
)
from app.storage import get_storage

router = APIRouter(prefix="/pub", tags=["public"])
logger = logging.getLogger("suite_artisan.public")

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


@router.post("/{slug}/demande-devis", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter(5, 60))])
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
    db.flush()
    notification = Notification(
        artisan_id=artisan.id,
        client_id=client.id,
        type="nouvelle_demande_devis",
        titre="Nouvelle demande de devis",
        message=f"{client.nom} vient d'envoyer une demande depuis votre site vitrine.",
        view="prospects",
        lu=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(client)

    # Le prospect et sa notification sont deja durablement enregistres. Une
    # panne du fournisseur email ne doit jamais pouvoir annuler la demande.
    try:
        email_service.send_nouvelle_demande_devis(db, artisan, client)
    except Exception:
        db.rollback()
        logger.exception(
            "La demande %s est conservee, mais la tentative d'email a echoue de facon inattendue",
            client.id,
        )
    return {"message": "Demande envoyee avec succes", "client_id": client.id}


@router.get("/{slug}/avis", response_model=list[AvisPublicSiteOut], dependencies=[Depends(rate_limiter(30, 60))])
def avis_publies_pour_site(slug: str, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : avis que l'artisan a explicitement choisi de
    publier sur son site vitrine (voir PATCH /avis/{id}). Consomme par
    generator/site_generator.py au moment de fabriquer le site - jamais
    d'avis invente, uniquement ceux reellement soumis et valides."""
    artisan = db.query(Artisan).filter(Artisan.slug == slug).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artisan introuvable")
    avis_list = (
        db.query(Avis)
        .options(joinedload(Avis.client))
        .filter(Avis.artisan_id == artisan.id, Avis.publie_site.is_(True))
        .order_by(Avis.created_at.desc())
        .all()
    )
    return [
        AvisPublicSiteOut(note=a.note, commentaire=a.commentaire, nom_auteur=a.nom_auteur or (a.client.nom if a.client else None))
        for a in avis_list
    ]


@router.get("/devis/{token}", response_model=DevisPublicOut, dependencies=[Depends(rate_limiter(30, 60))])
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


@router.post("/devis/{token}/accepter", response_model=DevisPublicOut, dependencies=[Depends(rate_limiter(10, 60))])
def accepter_devis_public(token: str, payload: DevisAccepterIn, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : le client accepte le devis en tapant son nom (la
    mention "bon pour accord" est deja sur le PDF/la page). Ce n'est pas une
    signature electronique qualifiee au sens juridique, mais une acceptation
    tracee (nom + date), ce qui est deja mieux que le statut "signe" pose a
    la main par l'artisan sans aucune confirmation du client."""
    devis = _get_devis_public_or_404(db, token)
    if devis.statut == "signe":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce devis a déjà été accepté")
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


@router.get("/facture/{token}", response_model=FacturePublicOut, dependencies=[Depends(rate_limiter(30, 60))])
def voir_facture_public(token: str, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : ce que le client voit en ouvrant le lien de sa
    facture (envoye par l'artisan ou par une relance automatique)."""
    facture = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client), joinedload(Facture.artisan))
        .filter(Facture.token == token)
        .first()
    )
    if facture is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facture introuvable")
    return FacturePublicOut(
        numero=facture.numero, type=facture.type, client_nom=facture.client.nom,
        taux_tva=facture.taux_tva, statut=facture.statut, montant_ht=facture.montant_ht,
        montant_ttc=facture.montant_ttc, montant_paye=facture.montant_paye,
        montant_restant=facture.montant_restant, est_en_retard=facture.est_en_retard,
        date_emission=facture.date_emission, date_echeance=facture.date_echeance,
        lignes=facture.lignes, paiements=facture.paiements,
        artisan_nom_entreprise=facture.artisan.nom_entreprise, artisan_telephone=facture.artisan.telephone,
        artisan_email=facture.artisan.email, artisan_siret=facture.artisan.siret,
    )


def _get_client_avis_or_404(db: Session, token: str) -> Client:
    client = (
        db.query(Client)
        .options(joinedload(Client.artisan))
        .filter(Client.token_avis == token)
        .first()
    )
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lien invalide")
    return client


@router.get("/avis/{token}", response_model=AvisPublicStatutOut, dependencies=[Depends(rate_limiter(30, 60))])
def voir_demande_avis(token: str, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : page que le client ouvre pour laisser un avis."""
    client = _get_client_avis_or_404(db, token)
    deja_soumis = db.query(Avis).filter(Avis.client_id == client.id, Avis.source == "lien_public").first() is not None
    return AvisPublicStatutOut(
        artisan_nom_entreprise=client.artisan.nom_entreprise, client_nom=client.nom, deja_soumis=deja_soumis,
    )


@router.post("/avis/{token}", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter(3, 60))])
def soumettre_avis_public(token: str, payload: AvisPublicIn, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : soumission reelle de l'avis par le client. Un seul
    avis par lien de demande (pas de spam ni de doublon accidentel)."""
    client = _get_client_avis_or_404(db, token)
    deja_soumis = db.query(Avis).filter(Avis.client_id == client.id, Avis.source == "lien_public").first() is not None
    if deja_soumis:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un avis a déjà été transmis pour ce lien")

    avis = Avis(
        artisan_id=client.artisan_id, client_id=client.id, note=payload.note,
        commentaire=payload.commentaire, nom_auteur=client.nom, source="lien_public",
    )
    db.add(avis)
    db.commit()
    return {"message": "Avis transmis avec succes"}


def _get_client_portail_or_404(db: Session, token: str) -> Client:
    """Resout et valide un jeton de portail : introuvable OU expire renvoient
    la meme erreur 404 generique (jamais d'indice permettant de distinguer
    "jeton inexistant" de "jeton expire" a un attaquant qui devine)."""
    client = (
        db.query(Client)
        .options(joinedload(Client.artisan))
        .filter(Client.token_portail == token)
        .first()
    )
    if client is None or client.token_portail_genere_le is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lien invalide")
    genere_le = client.token_portail_genere_le
    if genere_le.tzinfo is None:
        genere_le = genere_le.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - genere_le > timedelta(days=PORTAIL_VALIDITE_JOURS):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lien invalide")
    return client


@router.get("/portail/{token}", response_model=PortailClientOut, dependencies=[Depends(rate_limiter(30, 60))])
def voir_portail_client(token: str, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : espace limite du client (jamais les donnees d'un
    autre client, jamais les infos internes de l'artisan - marges, notes,
    autres prospects...). Tout est filtre explicitement par client_id."""
    client = _get_client_portail_or_404(db, token)

    devis_list = db.query(Devis).filter(
        Devis.client_id == client.id,
        Devis.artisan_id == client.artisan_id,
    ).order_by(Devis.created_at.desc()).all()
    factures_list = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(
            Facture.client_id == client.id,
            Facture.artisan_id == client.artisan_id,
            Facture.statut != "brouillon",
        )
        .order_by(Facture.created_at.desc())
        .all()
    )
    chantiers_list = (
        db.query(Chantier)
        .options(joinedload(Chantier.taches))
        .filter(Chantier.client_id == client.id, Chantier.artisan_id == client.artisan_id)
        .order_by(Chantier.created_at.desc())
        .all()
    )
    chantiers_out = []
    for c in chantiers_list:
        photos = (
            db.query(Document)
            .filter(
                Document.chantier_id == c.id,
                Document.artisan_id == client.artisan_id,
                Document.type == "photo",
                Document.chemin_fichier.isnot(None),
                Document.archive.is_(False),
            )
            .order_by(Document.created_at)
            .all()
        )
        chantiers_out.append(PortailChantierOut(
            titre=c.titre, statut=c.statut, date_debut=c.date_debut, date_fin_prevue=c.date_fin_prevue,
            progression=c.progression, photos=[PortailPhotoOut(id=p.id, nom=p.nom) for p in photos],
        ))

    messages = db.query(Message).filter(
        Message.client_id == client.id,
        Message.artisan_id == client.artisan_id,
    ).order_by(Message.created_at).all()

    return PortailClientOut(
        artisan_nom_entreprise=client.artisan.nom_entreprise, artisan_telephone=client.artisan.telephone,
        artisan_email=client.artisan.email, client_nom=client.nom,
        devis=[
            PortailDevisOut(numero=d.numero, titre=d.titre, statut=d.statut, montant_ttc=d.montant_ttc, date_signature=d.date_signature, token=d.token)
            for d in devis_list
        ],
        factures=[
            PortailFactureOut(
                numero=f.numero, statut=f.statut, montant_ttc=f.montant_ttc, montant_restant=f.montant_restant,
                est_en_retard=f.est_en_retard, date_echeance=f.date_echeance, token=f.token,
            )
            for f in factures_list
        ],
        chantiers=chantiers_out,
        messages=messages,
    )


@router.post("/portail/{token}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limiter(10, 60))])
def envoyer_message_portail(token: str, payload: MessageCreate, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : le client envoie un message a l'artisan depuis son
    portail. Marque non lu jusqu'a ce que l'artisan ouvre le fil (voir
    GET /clients/{id}/messages cote authentifie)."""
    client = _get_client_portail_or_404(db, token)
    if not payload.texte.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le message ne peut pas etre vide")
    message = Message(artisan_id=client.artisan_id, client_id=client.id, expediteur="client", texte=payload.texte.strip()[:2000], lu=False)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/portail/{token}/photos/{document_id}", dependencies=[Depends(rate_limiter(60, 60))])
def voir_photo_portail(token: str, document_id: int, db: Session = Depends(get_db)):
    """Endpoint PUBLIC : sert une photo de chantier, apres avoir verifie
    qu'elle appartient bien a un chantier de CE client (jamais la photo d'un
    autre client, meme en devinant un id)."""
    client = _get_client_portail_or_404(db, token)
    document = (
        db.query(Document)
        .join(Chantier, Document.chantier_id == Chantier.id)
        .filter(
            Document.id == document_id,
            Document.artisan_id == client.artisan_id,
            Document.type == "photo",
            Document.archive.is_(False),
            Chantier.client_id == client.id,
            Chantier.artisan_id == client.artisan_id,
        )
        .first()
    )
    if document is None or not document.chemin_fichier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")
    contenu = get_storage().read(document.chemin_fichier)
    if contenu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo introuvable")
    nom_fichier = document.nom_original or document.nom
    type_mime = mimetypes.guess_type(nom_fichier)[0] or "application/octet-stream"
    return Response(content=contenu, media_type=type_mime)
