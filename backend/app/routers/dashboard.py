from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_artisan
from app.models import Artisan, Chantier, Client, ConformiteItem, Devis, Evenement, Facture, Paiement, Tache
from app.routers.chantiers import _to_out as chantier_to_out
from app.routers.conformite import SEUIL_ALERTE_JOURS, _to_out as conformite_to_out
from app.routers.devis import DEVIS_STATUTS_FINAUX, JOURS_SEUIL_STATUTS, relance_due, _to_out as devis_to_out
from app.routers.factures import _to_out as facture_to_out
from app.schemas import (
    ActivationOut,
    DashboardAujourdhui,
    DashboardCommercial,
    DashboardFinances,
    DashboardOut,
    DashboardPresenceSite,
    RecommandationOut,
    SanteEntrepriseOut,
    SousScoreOut,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DEVIS_STATUTS_EN_ATTENTE = ("envoye", "consulte", "relance_j3", "relance_j7", "relance_j15")


@router.get("", response_model=DashboardOut)
def obtenir_dashboard(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    aujourdhui = date.today()
    maintenant = datetime.now(timezone.utc)
    il_y_a_7j = maintenant - timedelta(days=7)
    il_y_a_30j = maintenant - timedelta(days=30)
    debut_mois = date(aujourdhui.year, aujourdhui.month, 1)
    debut_annee = date(aujourdhui.year, 1, 1)

    # ---------- Aujourd'hui ----------
    taches_jour = (
        db.query(Tache)
        .filter(Tache.artisan_id == artisan.id, Tache.statut == "a_faire", Tache.echeance == aujourdhui)
        .all()
    )
    evenements_jour = (
        db.query(Evenement)
        .filter(
            Evenement.artisan_id == artisan.id,
            Evenement.date_debut >= datetime.combine(aujourdhui, datetime.min.time(), tzinfo=timezone.utc),
            Evenement.date_debut < datetime.combine(aujourdhui + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
        )
        .all()
    )
    devis_candidats = (
        db.query(Devis)
        .options(joinedload(Devis.lignes), joinedload(Devis.client))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL_STATUTS))
        .all()
    )
    devis_a_relancer = [devis_to_out(d) for d in devis_candidats if relance_due(d, artisan)]

    factures_ouvertes = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements), joinedload(Facture.client))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.notin_(("brouillon", "annulee", "payee")))
        .all()
    )
    factures_en_retard = [facture_to_out(f) for f in factures_ouvertes if f.est_en_retard]

    chantiers_bientot = (
        db.query(Chantier)
        .options(joinedload(Chantier.notes), joinedload(Chantier.depenses), joinedload(Chantier.client), joinedload(Chantier.factures), joinedload(Chantier.taches))
        .filter(
            Chantier.artisan_id == artisan.id, Chantier.statut.in_(("a_preparer", "planifie")),
            Chantier.date_debut.isnot(None), Chantier.date_debut >= aujourdhui, Chantier.date_debut <= aujourdhui + timedelta(days=7),
        )
        .order_by(Chantier.date_debut)
        .all()
    )

    aujourdhui_out = DashboardAujourdhui(
        taches=taches_jour, evenements=evenements_jour,
        devis_a_relancer=devis_a_relancer, factures_en_retard=factures_en_retard,
        chantiers_a_venir=[chantier_to_out(c) for c in chantiers_bientot],
    )

    # ---------- Commercial ----------
    nouveaux_prospects_7j = (
        db.query(Client)
        .filter(Client.artisan_id == artisan.id, Client.created_at >= il_y_a_7j)
        .count()
    )
    devis_en_attente = (
        db.query(Devis)
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(DEVIS_STATUTS_EN_ATTENTE))
        .count()
    )
    devis_acceptes_30j = (
        db.query(Devis)
        .filter(Devis.artisan_id == artisan.id, Devis.statut == "signe", Devis.date_signature >= il_y_a_30j)
        .count()
    )
    devis_decides = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut.in_(DEVIS_STATUTS_FINAUX)).count()
    devis_signes_total = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut == "signe").count()
    taux_transformation = round((devis_signes_total / devis_decides) * 100, 1) if devis_decides else 0.0

    devis_ouverts = (
        db.query(Devis)
        .options(joinedload(Devis.lignes))
        .filter(Devis.artisan_id == artisan.id, Devis.statut.notin_(DEVIS_STATUTS_FINAUX))
        .all()
    )
    valeur_pipeline = round(sum(d.montant_ttc or 0 for d in devis_ouverts), 2)

    commercial_out = DashboardCommercial(
        nouveaux_prospects_7j=nouveaux_prospects_7j, devis_en_attente=devis_en_attente,
        devis_acceptes_30j=devis_acceptes_30j, taux_transformation=taux_transformation,
        valeur_pipeline=valeur_pipeline,
    )

    # ---------- Finances ----------
    def somme_paiements(depuis: date) -> float:
        montants = (
            db.query(Paiement.montant)
            .join(Facture, Paiement.facture_id == Facture.id)
            .filter(Facture.artisan_id == artisan.id, Paiement.date_paiement >= depuis)
            .all()
        )
        return round(sum(m[0] for m in montants), 2)

    ca_mois = somme_paiements(debut_mois)
    ca_annee = somme_paiements(debut_annee)

    factures_actives = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.in_(("envoyee", "partiellement_payee", "en_retard")))
        .all()
    )
    a_encaisser = round(sum(f.montant_restant for f in factures_actives), 2)
    montant_en_retard = round(sum(f.montant_restant for f in factures_actives if f.est_en_retard), 2)

    paiements_recents = (
        db.query(Paiement)
        .join(Facture, Paiement.facture_id == Facture.id)
        .filter(Facture.artisan_id == artisan.id)
        .order_by(Paiement.created_at.desc())
        .limit(5)
        .all()
    )

    finances_out = DashboardFinances(
        ca_mois=ca_mois, ca_annee=ca_annee, a_encaisser=a_encaisser,
        montant_en_retard=montant_en_retard, paiements_recents=paiements_recents,
    )

    # ---------- Alertes conformite ----------
    seuil = aujourdhui + timedelta(days=SEUIL_ALERTE_JOURS)
    conformite_items = (
        db.query(ConformiteItem)
        .filter(ConformiteItem.artisan_id == artisan.id, ConformiteItem.date_expiration < seuil)
        .all()
    )

    # ---------- Presence en ligne (site vitrine livre par nous, pas de constructeur) ----------
    clients_site = db.query(Client).filter(Client.artisan_id == artisan.id, Client.source == "site_vitrine").all()
    nb_demandes_total = len(clients_site)
    # SQLite ne conserve pas systematiquement le fuseau horaire selon le
    # chemin d'ecriture : on normalise avant de comparer (meme pattern que
    # clients.py/planning.py).
    nb_demandes_30j = sum(
        1 for c in clients_site
        if (c.created_at if c.created_at.tzinfo is not None else c.created_at.replace(tzinfo=timezone.utc)) >= il_y_a_30j
    )
    nb_clients_gagnes_site = sum(1 for c in clients_site if c.statut == "gagne")
    montants_site = (
        db.query(Paiement.montant)
        .join(Facture, Paiement.facture_id == Facture.id)
        .filter(Facture.client_id.in_([c.id for c in clients_site]))
        .all()
    ) if clients_site else []
    ca_genere_site = round(sum(float(m[0]) for m in montants_site), 2)
    taux_conversion_site = round(nb_clients_gagnes_site / nb_demandes_total * 100, 1) if nb_demandes_total else None

    presence_site = DashboardPresenceSite(
        statut=artisan.site_statut, url=artisan.site_url,
        nb_demandes_total=nb_demandes_total, nb_demandes_30j=nb_demandes_30j,
        nb_clients_gagnes=nb_clients_gagnes_site, ca_genere=ca_genere_site,
        taux_conversion=taux_conversion_site,
    )

    return DashboardOut(
        aujourdhui=aujourdhui_out, commercial=commercial_out, finances=finances_out,
        alertes_conformite=[conformite_to_out(i) for i in conformite_items],
        presence_site=presence_site,
    )


def _fmt_euro(montant) -> str:
    return f"{montant:,.2f} €".replace(",", " ").replace(".", ",")


SOURCE_LABELS = {
    "manuel": "Ajoute manuellement",
    "site_vitrine": "Site vitrine",
    "google": "Google",
    "recommandation": "Recommandation",
    "telephone": "Telephone",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "ancien_client": "Ancien client",
    "autre": "Autre",
}


@router.get("/recommandations", response_model=list[RecommandationOut])
def obtenir_recommandations(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Recommandations metier generees a partir de donnees reelles (jamais de valeurs inventees)."""
    aujourdhui = date.today()
    recommandations: list[RecommandationOut] = []

    # ---------- Devis stagnants (envoyes depuis plus de 7 jours, toujours sans reponse) ----------
    seuil_devis = datetime.now(timezone.utc) - timedelta(days=7)
    devis_en_attente_reponse = (
        db.query(Devis)
        .filter(Devis.artisan_id == artisan.id, Devis.statut.in_(JOURS_SEUIL_STATUTS), Devis.date_envoi.isnot(None))
        .all()
    )

    def _aware(dt):
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    nb_stagnants = sum(1 for d in devis_en_attente_reponse if _aware(d.date_envoi) <= seuil_devis)
    if nb_stagnants:
        recommandations.append(RecommandationOut(
            message=f"Vous avez {nb_stagnants} devis sans reponse depuis plus de 7 jours.",
            urgence="moyenne", view="devis",
        ))

    # ---------- Chantiers en depassement de budget ----------
    chantiers_actifs = (
        db.query(Chantier)
        .options(joinedload(Chantier.depenses))
        .filter(Chantier.artisan_id == artisan.id, Chantier.statut.in_(("en_cours", "en_pause")), Chantier.budget.isnot(None))
        .all()
    )
    for c in chantiers_actifs:
        budget = float(c.budget or 0)
        if budget <= 0:
            continue
        total_depenses = sum(float(d.montant or 0) for d in c.depenses)
        if total_depenses > budget:
            pct = round((total_depenses / budget - 1) * 100)
            recommandations.append(RecommandationOut(
                message=f"Le chantier '{c.titre}' depasse actuellement son budget de {pct}%.",
                urgence="haute", view="chantiers", reference_id=c.id,
            ))

    # ---------- Factures en retard ----------
    factures_actives = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.in_(("envoyee", "partiellement_payee", "en_retard")))
        .all()
    )
    nb_en_retard = sum(1 for f in factures_actives if f.est_en_retard)
    if nb_en_retard:
        recommandations.append(RecommandationOut(
            message=f"Vous avez {nb_en_retard} facture{'s' if nb_en_retard > 1 else ''} en retard de paiement.",
            urgence="haute", view="factures",
        ))

    # ---------- Conformite (expiree ou proche de l'expiration) ----------
    seuil_conformite = aujourdhui + timedelta(days=SEUIL_ALERTE_JOURS)
    items_conformite = (
        db.query(ConformiteItem)
        .filter(ConformiteItem.artisan_id == artisan.id, ConformiteItem.date_expiration < seuil_conformite)
        .all()
    )
    for item in items_conformite:
        jours = (item.date_expiration - aujourdhui).days
        if jours < 0:
            recommandations.append(RecommandationOut(
                message=f"Votre document '{item.libelle}' a expire.",
                urgence="haute", view="entreprise",
            ))
        else:
            recommandations.append(RecommandationOut(
                message=f"Votre document '{item.libelle}' arrive a expiration dans {jours} jour{'s' if jours > 1 else ''}.",
                urgence="haute" if jours < 7 else "moyenne", view="entreprise",
            ))

    # ---------- Meilleur canal d'acquisition du mois (fonctionnalite reservee aux comptes actifs) ----------
    if artisan.subscription_status == "active":
        debut_mois = date(aujourdhui.year, aujourdhui.month, 1)
        clients_tous = db.query(Client).filter(Client.artisan_id == artisan.id).all()
        paiements_par_client = defaultdict(Decimal)
        paiements_rows = (
            db.query(Facture.client_id, Paiement.montant)
            .join(Paiement, Paiement.facture_id == Facture.id)
            .filter(Facture.artisan_id == artisan.id, Paiement.date_paiement >= debut_mois)
            .all()
        )
        for client_id, montant in paiements_rows:
            paiements_par_client[client_id] += montant
        ca_par_source = defaultdict(Decimal)
        for c in clients_tous:
            if c.id in paiements_par_client:
                ca_par_source[c.source] += paiements_par_client[c.id]
        if ca_par_source:
            meilleure_source, meilleur_ca = max(ca_par_source.items(), key=lambda kv: kv[1])
            label = SOURCE_LABELS.get(meilleure_source, meilleure_source)
            recommandations.append(RecommandationOut(
                message=f"Votre meilleur canal d'acquisition ce mois-ci est '{label}' ({_fmt_euro(float(meilleur_ca))} de CA genere).",
                urgence="basse", view="statistiques",
            ))

    return recommandations


@router.get("/sante", response_model=SanteEntrepriseOut)
def obtenir_sante_entreprise(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Score de sante de l'entreprise, calcule uniquement a partir de donnees reelles.

    Chaque sous-score exige un minimum de donnees pour etre calcule ; en dessous
    de ce seuil, on renvoie une raison honnete plutot qu'un chiffre invente.
    """
    aujourdhui = date.today()

    # ---------- Commercial : taux de transformation des devis decides ----------
    devis_decides = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut.in_(DEVIS_STATUTS_FINAUX)).count()
    if devis_decides >= 3:
        devis_signes = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut == "signe").count()
        commercial = SousScoreOut(label="Commercial", valeur=round(devis_signes / devis_decides * 100))
    else:
        commercial = SousScoreOut(label="Commercial", raison_absence="Pas assez de devis decides pour juger (minimum 3)")

    # ---------- Tresorerie : part du montant a encaisser qui n'est pas en retard ----------
    factures_actives = (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(Facture.artisan_id == artisan.id, Facture.statut.in_(("envoyee", "partiellement_payee", "en_retard")))
        .all()
    )
    a_encaisser = round(sum(f.montant_restant for f in factures_actives), 2)
    en_retard = round(sum(f.montant_restant for f in factures_actives if f.est_en_retard), 2)
    nb_factures_total = db.query(Facture).filter(Facture.artisan_id == artisan.id, Facture.statut != "brouillon").count()
    if a_encaisser > 0:
        tresorerie = SousScoreOut(label="Tresorerie", valeur=max(0, round(100 - (en_retard / a_encaisser * 100))))
    elif nb_factures_total > 0:
        tresorerie = SousScoreOut(label="Tresorerie", valeur=100)
    else:
        tresorerie = SousScoreOut(label="Tresorerie", raison_absence="Aucune facture pour le moment")

    # ---------- Chantiers : part des chantiers budgetes qui restent dans leur budget ----------
    chantiers_avec_budget = (
        db.query(Chantier)
        .options(joinedload(Chantier.depenses))
        .filter(Chantier.artisan_id == artisan.id, Chantier.budget.isnot(None))
        .all()
    )
    if chantiers_avec_budget:
        dans_budget = sum(
            1 for c in chantiers_avec_budget
            if sum(float(d.montant or 0) for d in c.depenses) <= float(c.budget or 0)
        )
        chantiers_score = SousScoreOut(label="Chantiers", valeur=round(dans_budget / len(chantiers_avec_budget) * 100))
    else:
        chantiers_score = SousScoreOut(label="Chantiers", raison_absence="Aucun chantier avec budget renseigne")

    # ---------- Conformite : penalite par element expire ou proche de l'expiration ----------
    items_conformite = db.query(ConformiteItem).filter(ConformiteItem.artisan_id == artisan.id).all()
    if items_conformite:
        seuil = aujourdhui + timedelta(days=SEUIL_ALERTE_JOURS)
        nb_alertes = sum(1 for i in items_conformite if i.date_expiration < seuil)
        conformite = SousScoreOut(label="Conformite", valeur=max(0, 100 - nb_alertes * 25))
    else:
        conformite = SousScoreOut(label="Conformite", raison_absence="Aucune information de conformite enregistree")

    # ---------- Organisation : part des taches avec echeance qui ne sont pas en retard ----------
    taches_avec_echeance = db.query(Tache).filter(Tache.artisan_id == artisan.id, Tache.echeance.isnot(None)).all()
    if taches_avec_echeance:
        nb_en_retard_taches = sum(1 for t in taches_avec_echeance if t.statut != "faite" and t.echeance < aujourdhui)
        organisation = SousScoreOut(
            label="Organisation",
            valeur=max(0, round(100 - (nb_en_retard_taches / len(taches_avec_echeance) * 100))),
        )
    else:
        organisation = SousScoreOut(label="Organisation", raison_absence="Aucune tache avec echeance pour le moment")

    sous_scores = [commercial, tresorerie, chantiers_score, conformite, organisation]
    valeurs = [s.valeur for s in sous_scores if s.valeur is not None]
    if valeurs:
        score_global = round(sum(valeurs) / len(valeurs))
        raison_absence_globale = None
    else:
        score_global = None
        raison_absence_globale = "Pas encore assez de donnees pour calculer un score global"

    return SanteEntrepriseOut(
        score_global=score_global, raison_absence_globale=raison_absence_globale,
        commercial=commercial, tresorerie=tresorerie, chantiers=chantiers_score,
        conformite=conformite, organisation=organisation,
    )


@router.get("/activation", response_model=ActivationOut)
def obtenir_activation(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    """Checklist de progression (section 30) : chaque etape est un fait
    reellement constate en base, jamais un flag qu'on coche a la main.
    Se reduit/disparait naturellement cote frontend une fois entierement_active."""
    entreprise_configuree = bool(artisan.nom_entreprise) and bool(artisan.telephone) and bool(artisan.logo_url)
    premier_client = db.query(Client).filter(Client.artisan_id == artisan.id).first() is not None
    premier_devis = db.query(Devis).filter(Devis.artisan_id == artisan.id).first() is not None
    premier_devis_envoye = db.query(Devis).filter(Devis.artisan_id == artisan.id, Devis.statut != "nouveau").first() is not None
    premier_chantier = db.query(Chantier).filter(Chantier.artisan_id == artisan.id).first() is not None
    premiere_facture = db.query(Facture).filter(Facture.artisan_id == artisan.id).first() is not None

    return ActivationOut(
        entreprise_configuree=entreprise_configuree,
        premier_client=premier_client,
        premier_devis=premier_devis,
        premier_devis_envoye=premier_devis_envoye,
        premier_chantier=premier_chantier,
        premiere_facture=premiere_facture,
        entierement_active=all([
            entreprise_configuree, premier_client, premier_devis,
            premier_devis_envoye, premier_chantier, premiere_facture,
        ]),
    )
