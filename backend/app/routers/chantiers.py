import secrets
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_active_subscription
from app import email_service
from app.models import Artisan, Chantier, ChantierNote, Client, Depense, Devis, Document, Facture, Fournisseur, HeureTravail, LigneFacture, Membre, Tache
from app.pdf import generate_chantier_report_pdf
from app.routers.factures import _generer_numero as _generer_numero_facture
from app.routers.factures import _to_out as _facture_to_out
from app.config import settings
from app.schemas import (
    ChantierCreate,
    ChantierNoteCreate,
    ChantierNoteOut,
    ChantierOut,
    ChantierUpdate,
    CloturerChantierIn,
    CloturerChantierOut,
    DepenseCreate,
    DepenseOut,
    HeureTravailCreate,
    HeureTravailOut,
    PreparerChantierIn,
    PreparerChantierOut,
)

router = APIRouter(prefix="/chantiers", tags=["chantiers"])

# Checklist de preparation standard (section "Preparation" du cahier des
# charges) : reutilise le modele Tache existant plutot que d'inventer une
# nouvelle table de checklist - une checklist EST une liste de taches.
CHECKLIST_PREPARATION = [
    "Confirmer la date avec le client",
    "Organiser l'equipe pour le chantier",
    "Verifier les materiaux necessaires",
    "Verifier les outils necessaires",
    "Verifier l'acces au chantier",
    "Reunir les documents necessaires (assurance, autorisations...)",
]


def _get_chantier_or_404(db: Session, artisan: Artisan, chantier_id: int) -> Chantier:
    chantier = (
        db.query(Chantier)
        .options(joinedload(Chantier.notes), joinedload(Chantier.depenses).joinedload(Depense.fournisseur), joinedload(Chantier.heures), joinedload(Chantier.client), joinedload(Chantier.factures), joinedload(Chantier.taches))
        .filter(Chantier.id == chantier_id, Chantier.artisan_id == artisan.id)
        .first()
    )
    if chantier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chantier introuvable")
    return chantier


def _to_out(chantier: Chantier) -> ChantierOut:
    return ChantierOut(
        id=chantier.id, artisan_id=chantier.artisan_id, client_id=chantier.client_id,
        client_nom=chantier.client.nom, devis_id=chantier.devis_id, titre=chantier.titre,
        adresse=chantier.adresse, statut=chantier.statut, date_debut=chantier.date_debut,
        date_fin_prevue=chantier.date_fin_prevue, budget=chantier.budget,
        total_depenses=chantier.total_depenses, total_heures=chantier.total_heures,
        cout_main_oeuvre=chantier.cout_main_oeuvre, marge_estimee=chantier.marge_estimee,
        montant_facture=chantier.montant_facture, montant_encaisse=chantier.montant_encaisse,
        marge_reelle=chantier.marge_reelle, progression=chantier.progression,
        date_reception=chantier.date_reception, reserves=chantier.reserves,
        created_at=chantier.created_at, notes=chantier.notes, depenses=chantier.depenses,
        heures=sorted(chantier.heures, key=lambda h: h.date_travail, reverse=True),
        taches=sorted(chantier.taches, key=lambda t: t.id),
    )


@router.get("", response_model=list[ChantierOut])
def lister_chantiers(
    archive: bool = False,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantiers = (
        db.query(Chantier)
        .options(joinedload(Chantier.notes), joinedload(Chantier.depenses).joinedload(Depense.fournisseur), joinedload(Chantier.heures), joinedload(Chantier.client), joinedload(Chantier.factures), joinedload(Chantier.taches))
        .filter(Chantier.artisan_id == artisan.id, Chantier.archive.is_(archive))
        .order_by(Chantier.created_at.desc())
        .all()
    )
    return [_to_out(c) for c in chantiers]


@router.post("", response_model=ChantierOut, status_code=status.HTTP_201_CREATED)
def creer_chantier(
    payload: ChantierCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    client = db.query(Client).filter(Client.id == payload.client_id, Client.artisan_id == artisan.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    chantier = Chantier(artisan_id=artisan.id, **payload.model_dump())
    db.add(chantier)
    db.commit()
    chantier = _get_chantier_or_404(db, artisan, chantier.id)
    return _to_out(chantier)


@router.post("/depuis-devis/{devis_id}", response_model=PreparerChantierOut, status_code=status.HTTP_201_CREATED)
def preparer_chantier_depuis_devis(
    devis_id: int,
    payload: PreparerChantierIn,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """"Tout preparer" : transforme un devis signe en chantier reellement
    pret a demarrer - pas juste une redirection vers un formulaire vide.
    Cree le chantier, l'acompte facture (si prevu au devis) et la checklist
    de preparation (taches). Le planning affiche deja automatiquement les
    chantiers a leur date_debut (voir /planning), inutile de dupliquer."""
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seul un devis signe peut etre prepare en chantier")
    if db.query(Chantier).filter(Chantier.devis_id == devis.id, Chantier.artisan_id == artisan.id).first() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un chantier existe deja pour ce devis")

    chantier = Chantier(
        artisan_id=artisan.id, client_id=devis.client_id, devis_id=devis.id,
        titre=devis.titre or f"Chantier - {devis.numero or devis.id}",
        adresse=payload.adresse or devis.client.adresse,
        statut="planifie" if payload.date_debut else "a_preparer",
        date_debut=payload.date_debut,
        budget=payload.budget if payload.budget is not None else devis.montant_ht,
    )
    db.add(chantier)
    db.flush()

    facture_acompte = None
    if payload.creer_acompte and devis.acompte_pourcentage and devis.montant_ht:
        montant_acompte_ht = round(float(devis.montant_ht) * float(devis.acompte_pourcentage) / 100, 2)
        if montant_acompte_ht > 0:
            facture = Facture(
                artisan_id=artisan.id, client_id=devis.client_id, devis_id=devis.id, chantier_id=chantier.id,
                type="acompte", taux_tva=devis.taux_tva, statut="brouillon",
                numero=_generer_numero_facture(db, artisan), token=secrets.token_urlsafe(24),
            )
            db.add(facture)
            db.flush()
            db.add(LigneFacture(
                facture_id=facture.id, ordre=0,
                description=f"Acompte {float(devis.acompte_pourcentage):g}% - {devis.titre or devis.numero or ''}".strip(" -"),
                quantite=1, unite="forfait", prix_unitaire_ht=montant_acompte_ht,
            ))
            db.commit()
            facture_acompte = facture

    nb_taches = 0
    if payload.creer_checklist:
        for libelle in CHECKLIST_PREPARATION:
            db.add(Tache(
                artisan_id=artisan.id, client_id=devis.client_id, chantier_id=chantier.id,
                titre=libelle, priorite="normale", statut="a_faire",
                echeance=payload.date_debut - timedelta(days=2) if payload.date_debut else None,
            ))
            nb_taches += 1
        db.commit()

    if devis.client.statut != "gagne":
        devis.client.statut = "gagne"
        db.commit()

    chantier = _get_chantier_or_404(db, artisan, chantier.id)
    if facture_acompte is not None:
        facture_acompte = db.query(Facture).options(
            joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client),
        ).filter(Facture.id == facture_acompte.id, Facture.artisan_id == artisan.id).first()

    return PreparerChantierOut(
        chantier=_to_out(chantier),
        facture_acompte=_facture_to_out(facture_acompte) if facture_acompte else None,
        nb_taches_creees=nb_taches,
    )


@router.get("/{chantier_id}", response_model=ChantierOut)
def obtenir_chantier(
    chantier_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    return _to_out(_get_chantier_or_404(db, artisan, chantier_id))


@router.patch("/{chantier_id}", response_model=ChantierOut)
def modifier_chantier(
    chantier_id: int,
    payload: ChantierUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(chantier, field, value)
    db.commit()
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    return _to_out(chantier)


@router.delete("/{chantier_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_chantier(
    chantier_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Archive le chantier plutot que de le supprimer definitivement
    (section 44) : conserve depenses, heures et factures liees."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    chantier.archive = True
    db.commit()


@router.post("/{chantier_id}/restaurer", response_model=ChantierOut)
def restaurer_chantier(
    chantier_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    chantier.archive = False
    db.commit()
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    return _to_out(chantier)


@router.post("/{chantier_id}/notes", response_model=ChantierNoteOut, status_code=status.HTTP_201_CREATED)
def ajouter_note(
    chantier_id: int,
    payload: ChantierNoteCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Ajoute une note/photo de compte-rendu (avant/pendant/apres) a un chantier."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    note = ChantierNote(chantier_id=chantier.id, **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.post("/{chantier_id}/depenses", response_model=DepenseOut, status_code=status.HTTP_201_CREATED)
def ajouter_depense(
    chantier_id: int,
    payload: DepenseCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Ajoute une depense (materiaux, sous-traitance...) pour suivre la marge du chantier."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    if payload.fournisseur_id is not None:
        fournisseur = db.query(Fournisseur).filter(Fournisseur.id == payload.fournisseur_id, Fournisseur.artisan_id == artisan.id).first()
        if fournisseur is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fournisseur introuvable")
    depense = Depense(chantier_id=chantier.id, **payload.model_dump())
    db.add(depense)
    db.commit()
    db.refresh(depense)
    return depense


@router.post("/{chantier_id}/heures", response_model=HeureTravailOut, status_code=status.HTTP_201_CREATED)
def ajouter_heures(
    chantier_id: int,
    payload: HeureTravailCreate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Enregistre des heures de main d'oeuvre sur un chantier (section 16 :
    suivi simple, pas de pointeuse). Alimente Chantier.total_heures et
    Chantier.cout_main_oeuvre, donc la marge reelle/estimee."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    if payload.membre_id is not None:
        membre = db.query(Membre).filter(Membre.id == payload.membre_id, Membre.artisan_id == artisan.id).first()
        if membre is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membre introuvable")
    heure = HeureTravail(chantier_id=chantier.id, **payload.model_dump())
    db.add(heure)
    db.commit()
    db.refresh(heure)
    return heure


@router.delete("/{chantier_id}/heures/{heure_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_heures(
    chantier_id: int,
    heure_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    heure = db.query(HeureTravail).filter(HeureTravail.id == heure_id, HeureTravail.chantier_id == chantier.id).first()
    if heure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entree d'heures introuvable")
    db.delete(heure)
    db.commit()


@router.post("/{chantier_id}/cloturer", response_model=CloturerChantierOut)
def cloturer_chantier(
    chantier_id: int,
    payload: CloturerChantierIn,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """"Cloturer" un chantier termine : facture finale calculee a partir du
    solde reellement du (jamais devine si on n'a aucune reference fiable),
    demande d'avis reelle, tache de suivi. Chaque action est honnete sur ce
    qu'elle a reussi a faire (voir *_email_statut, *_raison_absence)."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    if chantier.statut != "termine":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seul un chantier marque termine peut etre cloture")

    client = db.query(Client).filter(Client.id == chantier.client_id, Client.artisan_id == artisan.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    devis = None
    if chantier.devis_id:
        devis = (
            db.query(Devis)
            .options(joinedload(Devis.lignes))
            .filter(Devis.id == chantier.devis_id, Devis.artisan_id == artisan.id)
            .first()
        )
        if devis is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Devis introuvable")
        if devis.client_id != client.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Le devis du chantier ne correspond pas a son client")

    facture_finale = None
    facture_finale_email_statut = None
    facture_finale_raison_absence = None

    if payload.generer_facture_finale:
        montant_total = None
        if devis is not None and devis.montant_ttc is not None:
            montant_total = float(devis.montant_ttc)
        elif chantier.budget is not None:
            montant_total = float(chantier.budget)

        if montant_total is None:
            facture_finale_raison_absence = "Aucun montant de reference (devis signe ou budget renseigne) pour calculer le solde"
        else:
            # Attention : Chantier.montant_facture exclut volontairement les
            # factures "brouillon" (ce n'est pas encore un CA reel pour le
            # tableau de bord). Ici on veut l'inverse : une facture d'acompte
            # encore en brouillon (ex: creee par "Tout preparer" et jamais
            # envoyee) represente quand meme un montant deja engage envers le
            # client - l'ignorer doublerait la facturation du chantier.
            factures_du_chantier = db.query(Facture).filter(
                Facture.chantier_id == chantier.id,
                Facture.artisan_id == artisan.id,
            ).all()
            deja_facture = round(sum(float(f.montant_ttc or 0) for f in factures_du_chantier if f.statut != "annulee"), 2)
            reste_ttc = round(montant_total - deja_facture, 2)
            if reste_ttc <= 0:
                facture_finale_raison_absence = "Ce chantier est deja entierement facture"
            else:
                taux_tva = float(devis.taux_tva) if devis is not None else 10.0
                reste_ht = round(reste_ttc / (1 + taux_tva / 100), 2)
                facture = Facture(
                    artisan_id=artisan.id, client_id=chantier.client_id, devis_id=chantier.devis_id, chantier_id=chantier.id,
                    type="finale", taux_tva=taux_tva, statut="envoyee",
                    numero=_generer_numero_facture(db, artisan), token=secrets.token_urlsafe(24),
                    date_echeance=date.today() + timedelta(days=30), date_envoi=datetime.now(timezone.utc),
                )
                db.add(facture)
                db.flush()
                db.add(LigneFacture(
                    facture_id=facture.id, ordre=0, description=f"Solde final - {chantier.titre}",
                    quantite=1, unite="forfait", prix_unitaire_ht=reste_ht,
                ))
                db.commit()
                facture = db.query(Facture).options(
                    joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client),
                ).filter(Facture.id == facture.id, Facture.artisan_id == artisan.id).first()
                url = f"{settings.app_base_url}/facture-public.html?t={facture.token}"
                log = email_service.send_facture(db, facture, artisan, url)
                facture_finale_email_statut = log.statut
                facture_finale = facture

    avis_demande = False
    avis_email_statut = None
    if payload.demander_avis:
        if client.token_avis is None:
            client.token_avis = secrets.token_urlsafe(24)
            db.commit()
        avis_url = f"{settings.app_base_url}/avis-public.html?t={client.token_avis}"
        log = email_service.send_demande_avis(db, artisan, client, avis_url)
        avis_demande = True
        avis_email_statut = log.statut

    db.add(Tache(
        artisan_id=artisan.id, client_id=chantier.client_id, chantier_id=chantier.id,
        titre=f"Suivi chantier '{chantier.titre}' - verifier la satisfaction client",
        priorite="normale", statut="a_faire", echeance=date.today() + timedelta(days=30),
    ))

    if facture_finale is not None:
        chantier.statut = "facture"
    db.commit()

    chantier = _get_chantier_or_404(db, artisan, chantier.id)
    return CloturerChantierOut(
        chantier=_to_out(chantier),
        facture_finale=_facture_to_out(facture_finale) if facture_finale else None,
        facture_finale_email_statut=facture_finale_email_statut,
        facture_finale_raison_absence=facture_finale_raison_absence,
        avis_demande=avis_demande, avis_email_statut=avis_email_statut,
        tache_suivi_creee=True,
    )


@router.get("/{chantier_id}/rapport-pdf")
def telecharger_rapport_chantier(
    chantier_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(require_active_subscription),
):
    """Genere reellement le rapport de chantier (pas de simulation) :
    donnees, journal et photos reellement uploadees pour ce chantier."""
    chantier = _get_chantier_or_404(db, artisan, chantier_id)
    photos = (
        db.query(Document)
        .filter(Document.chantier_id == chantier.id, Document.type == "photo", Document.chemin_fichier.isnot(None))
        .order_by(Document.created_at)
        .all()
    )
    pdf_bytes = generate_chantier_report_pdf(chantier, artisan, photos)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="rapport-{chantier.titre}.pdf"'},
    )
