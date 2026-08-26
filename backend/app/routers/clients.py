import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Client, Devis, EmailLog, Facture, Chantier, Message
from app.schemas import ClientCreate, ClientOut, ClientResume, ClientUpdate, MessageCreate, MessageOut, PortailTokenOut, TimelineEntry

router = APIRouter(prefix="/clients", tags=["clients"])

# Duree de validite d'un lien de portail client avant de devoir en regenerer
# un (voir Client.token_portail_genere_le). Regenerer EST le mecanisme de
# revocation : un artisan qui souhaite couper l'acces le fait en un clic,
# sans etat "revoque" separe a gerer.
PORTAIL_VALIDITE_JOURS = 365


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
    archive: bool = False,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Par defaut, seuls les contacts actifs (non archives) sont renvoyes.
    Passer archive=true pour lister ceux qui ont ete "supprimes" (archives,
    voir supprimer_client) - rien n'est jamais perdu definitivement."""
    query = db.query(Client).filter(Client.artisan_id == artisan.id, Client.archive.is_(archive))
    if statut:
        query = query.filter(Client.statut == statut)
    return query.order_by(Client.created_at.desc()).all()


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def creer_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = Client(artisan_id=artisan.id, **payload.model_dump())
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
    """Archive le contact plutot que de le supprimer definitivement (section 44
    du cahier des charges V4) : il disparait des listes actives mais ses
    devis/factures/chantiers restent intacts (aucune cascade destructrice)."""
    client = _get_client_or_404(db, artisan, client_id)
    client.archive = True
    db.commit()


@router.post("/{client_id}/restaurer", response_model=ClientOut)
def restaurer_client(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = _get_client_or_404(db, artisan, client_id)
    client.archive = False
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}/resume", response_model=ClientResume)
def resume_client(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Chiffres cles de la fiche client (section CRM du cahier des charges V2) :
    valeur totale facturee, nombre de chantiers, dernier contact, impayes,
    date du dernier devis. Calcule a la volee, pas stocke."""
    client = _get_client_or_404(db, artisan, client_id)

    factures_list = db.query(Facture).filter(Facture.client_id == client.id).all()
    valeur_totale = sum(f.montant_ttc for f in factures_list)
    impayes = sum(f.montant_restant for f in factures_list if f.statut not in ("payee", "annulee"))

    nb_chantiers = db.query(Chantier).filter(Chantier.client_id == client.id).count()

    devis_list = db.query(Devis).filter(Devis.client_id == client.id).order_by(Devis.created_at.desc()).all()
    date_dernier_devis = devis_list[0].created_at if devis_list else None

    dates_contact = [client.created_at]
    for d in devis_list:
        dates_contact.extend(filter(None, [d.created_at, d.date_envoi, d.date_consultation, d.date_derniere_relance, d.date_signature]))
    for f in factures_list:
        dates_contact.extend(filter(None, [f.created_at, f.date_envoi]))
        dates_contact.extend(p.created_at for p in f.paiements)
    dernier_contact = max(dates_contact) if dates_contact else None

    return ClientResume(
        valeur_totale=round(float(valeur_totale), 2),
        nb_chantiers=nb_chantiers,
        dernier_contact=dernier_contact,
        impayes=round(float(impayes), 2),
        date_dernier_devis=date_dernier_devis,
    )


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

    # Historique reel des emails transactionnels (voir email_service.py) :
    # montre honnetement ce qui a ete envoye, echoue, ou jamais tente faute
    # de fournisseur configure - jamais un "envoye" qui ne serait pas reel.
    EMAIL_TYPE_LABELS = {
        "devis": "Devis envoye par email", "relance_devis": "Relance devis envoyee par email",
        "facture": "Facture envoyee par email", "relance_facture": "Relance facture envoyee par email",
        "paiement_recu": "Confirmation de paiement envoyee", "demande_avis": "Demande d'avis envoyee",
    }
    emails = db.query(EmailLog).filter(EmailLog.client_id == client.id).all()
    for log in emails:
        libelle_type = EMAIL_TYPE_LABELS.get(log.type, log.type)
        if log.statut == "envoye":
            label = libelle_type
        elif log.statut == "echec":
            label = f"{libelle_type} : echec d'envoi"
        elif log.statut == "non_configure":
            label = f"{libelle_type} : non envoye (fournisseur email non configure)"
        else:
            label = f"{libelle_type} : pas d'adresse email pour ce contact"
        entries.append(TimelineEntry(date=log.created_at, type=f"email_{log.statut}", label=label, reference_id=log.devis_id or log.facture_id))

    # SQLite ne conserve pas systematiquement l'info de fuseau horaire selon
    # le chemin d'ecriture (defaut ORM vs mise a jour directe) : on normalise
    # avant de trier pour ne jamais comparer un datetime naif a un aware.
    for m in client.messages:
        libelle = "Message recu du client" if m.expediteur == "client" else "Message envoye au client"
        entries.append(TimelineEntry(date=m.created_at, type="message", label=f"{libelle} : {m.texte[:80]}", reference_id=client.id))

    entries.sort(key=lambda e: e.date if e.date.tzinfo is not None else e.date.replace(tzinfo=timezone.utc))
    return entries


@router.post("/{client_id}/portail/generer", response_model=PortailTokenOut)
def generer_lien_portail(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Genere un NOUVEAU jeton de portail (remplace l'ancien, qui devient
    immediatement invalide - c'est le mecanisme de revocation)."""
    client = _get_client_or_404(db, artisan, client_id)
    client.token_portail = secrets.token_urlsafe(32)
    client.token_portail_genere_le = datetime.now(timezone.utc)
    db.commit()
    return PortailTokenOut(
        token_portail=client.token_portail, genere_le=client.token_portail_genere_le,
        expire_le=client.token_portail_genere_le + timedelta(days=PORTAIL_VALIDITE_JOURS),
    )


@router.get("/{client_id}/messages", response_model=list[MessageOut])
def lister_messages(
    client_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Consulter le fil marque les messages du client comme lus (signal de
    lecture reel, pas un simple compteur decoratif)."""
    client = _get_client_or_404(db, artisan, client_id)
    a_marquer = [m for m in client.messages if m.expediteur == "client" and not m.lu]
    for m in a_marquer:
        m.lu = True
    if a_marquer:
        db.commit()
    client = _get_client_or_404(db, artisan, client_id)
    return client.messages


@router.post("/{client_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def envoyer_message(
    client_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    client = _get_client_or_404(db, artisan, client_id)
    message = Message(artisan_id=artisan.id, client_id=client.id, expediteur="artisan", texte=payload.texte, lu=True)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
