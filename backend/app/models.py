from datetime import datetime, date, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Artisan(Base):
    """Un compte = un artisan = un tenant. Toutes les autres tables ont une
    colonne artisan_id pour isoler les donnees de chaque artisan."""

    __tablename__ = "artisans"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    nom_entreprise = Column(String, nullable=False)
    metier = Column(String, nullable=False)  # plombier, electricien, macon, peintre, general
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    ville = Column(String, nullable=True)
    code_postal = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    siret = Column(String, nullable=True)
    assurance_decennale_nom = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)

    # Presence en ligne : le site vitrine est livre par nous (pas de generateur
    # dans le SaaS), on garde juste un etat visible par l'artisan.
    site_url = Column(String, nullable=True)
    site_statut = Column(String, default="non_livre")  # non_livre, en_cours, livre

    onboarding_termine = Column(Boolean, default=False)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, default="inactive")  # inactive, active, past_due, canceled
    plan = Column(String, default="gratuit")  # gratuit, essentiel, pro, business

    created_at = Column(DateTime(timezone=True), default=utcnow)

    clients = relationship("Client", back_populates="artisan", cascade="all, delete-orphan")
    devis = relationship("Devis", back_populates="artisan", cascade="all, delete-orphan")
    factures = relationship("Facture", back_populates="artisan", cascade="all, delete-orphan")
    chantiers = relationship("Chantier", back_populates="artisan", cascade="all, delete-orphan")
    conformites = relationship("ConformiteItem", back_populates="artisan", cascade="all, delete-orphan")
    taches = relationship("Tache", back_populates="artisan", cascade="all, delete-orphan")
    evenements = relationship("Evenement", back_populates="artisan", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="artisan", cascade="all, delete-orphan")


# Pipeline commercial : de la premiere demande jusqu'a la signature (ou la perte).
CLIENT_STATUTS = [
    "nouveau", "contacte", "qualification", "visite_prevue",
    "devis_a_faire", "devis_envoye", "negociation", "gagne", "perdu",
]


class Client(Base):
    """Un prospect et un client sont la meme entite : seul le statut du
    pipeline change. Ca evite la ressaisie au moment ou un prospect signe."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)

    nom = Column(String, nullable=False)
    email = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    societe = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    code_postal = Column(String, nullable=True)
    ville = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    statut = Column(String, default="nouveau", index=True)
    source = Column(String, default="manuel")  # manuel, site_vitrine

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    artisan = relationship("Artisan", back_populates="clients")
    devis = relationship("Devis", back_populates="client", cascade="all, delete-orphan")
    factures = relationship("Facture", back_populates="client", cascade="all, delete-orphan")
    chantiers = relationship("Chantier", back_populates="client")
    taches = relationship("Tache", back_populates="client")


class Devis(Base):
    __tablename__ = "devis"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)

    numero = Column(String, nullable=True)
    titre = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    taux_tva = Column(Float, default=10.0)  # 10 = renovation, 20 = neuf
    acompte_pourcentage = Column(Float, default=30.0)

    # nouveau -> envoye -> consulte -> relance_j3 -> relance_j7 -> relance_j15 -> signe / perdu / expire
    statut = Column(String, default="nouveau", index=True)

    date_envoi = Column(DateTime(timezone=True), nullable=True)
    date_consultation = Column(DateTime(timezone=True), nullable=True)
    date_derniere_relance = Column(DateTime(timezone=True), nullable=True)
    nb_relances = Column(Integer, default=0)
    date_signature = Column(DateTime(timezone=True), nullable=True)

    source = Column(String, default="manuel")  # manuel ou site_vitrine

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="devis")
    client = relationship("Client", back_populates="devis")
    lignes = relationship("LigneDevis", back_populates="devis", cascade="all, delete-orphan", order_by="LigneDevis.ordre")
    factures = relationship("Facture", back_populates="devis")

    @property
    def montant_ht(self):
        if not self.lignes:
            return None
        return round(sum(l.quantite * l.prix_unitaire_ht for l in self.lignes), 2)

    @property
    def montant_ttc(self):
        montant_ht = self.montant_ht
        if montant_ht is None:
            return None
        return round(montant_ht * (1 + self.taux_tva / 100), 2)


class LigneDevis(Base):
    __tablename__ = "lignes_devis"

    id = Column(Integer, primary_key=True, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=False, index=True)

    description = Column(String, nullable=False)
    quantite = Column(Float, default=1.0)
    unite = Column(String, default="u")
    prix_unitaire_ht = Column(Float, nullable=False)
    ordre = Column(Integer, default=0)

    devis = relationship("Devis", back_populates="lignes")

    @property
    def total_ht(self):
        return round(self.quantite * self.prix_unitaire_ht, 2)


# Facture "standard" (un seul jet), "acompte" (a la signature), "situation"
# (paiement intermediaire pendant le chantier), "finale" (solde), "avoir" (remboursement).
FACTURE_TYPES = ["standard", "acompte", "situation", "finale", "avoir"]


class Facture(Base):
    __tablename__ = "factures"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True, index=True)

    numero = Column(String, nullable=False)
    type = Column(String, default="standard")
    taux_tva = Column(Float, default=10.0)

    # brouillon -> envoyee -> (partiellement_payee) -> payee / en_retard / annulee
    statut = Column(String, default="brouillon", index=True)

    date_emission = Column(Date, default=date.today)
    date_echeance = Column(Date, nullable=True)
    date_envoi = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="factures")
    client = relationship("Client", back_populates="factures")
    devis = relationship("Devis", back_populates="factures")
    chantier = relationship("Chantier", back_populates="factures")
    lignes = relationship("LigneFacture", back_populates="facture", cascade="all, delete-orphan", order_by="LigneFacture.ordre")
    paiements = relationship("Paiement", back_populates="facture", cascade="all, delete-orphan")

    @property
    def montant_ht(self):
        return round(sum(l.quantite * l.prix_unitaire_ht for l in self.lignes), 2) if self.lignes else 0.0

    @property
    def montant_ttc(self):
        return round(self.montant_ht * (1 + self.taux_tva / 100), 2)

    @property
    def montant_paye(self):
        return round(sum(p.montant for p in self.paiements), 2)

    @property
    def montant_restant(self):
        return round(self.montant_ttc - self.montant_paye, 2)

    @property
    def est_en_retard(self):
        if self.statut in ("payee", "annulee"):
            return False
        return bool(self.date_echeance) and self.date_echeance < date.today()


class LigneFacture(Base):
    __tablename__ = "lignes_facture"

    id = Column(Integer, primary_key=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=False, index=True)

    description = Column(String, nullable=False)
    quantite = Column(Float, default=1.0)
    unite = Column(String, default="u")
    prix_unitaire_ht = Column(Float, nullable=False)
    ordre = Column(Integer, default=0)

    facture = relationship("Facture", back_populates="lignes")

    @property
    def total_ht(self):
        return round(self.quantite * self.prix_unitaire_ht, 2)


class Paiement(Base):
    __tablename__ = "paiements"

    id = Column(Integer, primary_key=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=False, index=True)

    montant = Column(Float, nullable=False)
    date_paiement = Column(Date, default=date.today)
    moyen = Column(String, default="virement")  # virement, cheque, especes, cb, autre
    notes = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    facture = relationship("Facture", back_populates="paiements")


class Chantier(Base):
    __tablename__ = "chantiers"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=True, index=True)

    titre = Column(String, nullable=False)
    adresse = Column(String, nullable=True)
    # a_preparer -> planifie -> en_cours -> (en_pause) -> termine -> facture -> paye
    statut = Column(String, default="a_preparer", index=True)
    date_debut = Column(Date, nullable=True)
    date_fin_prevue = Column(Date, nullable=True)
    budget = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="chantiers")
    client = relationship("Client", back_populates="chantiers")
    notes = relationship("ChantierNote", back_populates="chantier", cascade="all, delete-orphan")
    taches = relationship("Tache", back_populates="chantier")
    factures = relationship("Facture", back_populates="chantier")
    depenses = relationship("Depense", back_populates="chantier", cascade="all, delete-orphan")

    @property
    def total_depenses(self):
        return round(sum(d.montant for d in self.depenses), 2)

    @property
    def marge_estimee(self):
        if self.budget is None:
            return None
        return round(self.budget - self.total_depenses, 2)


class Depense(Base):
    """Une depense de chantier (materiaux, sous-traitance...) pour suivre la marge."""

    __tablename__ = "depenses"

    id = Column(Integer, primary_key=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False, index=True)

    libelle = Column(String, nullable=False)
    montant = Column(Float, nullable=False)
    date_depense = Column(Date, default=date.today)

    chantier = relationship("Chantier", back_populates="depenses")


class ChantierNote(Base):
    """Compte-rendu de chantier : une note/photo horodatee, rattachee a une phase."""

    __tablename__ = "chantier_notes"

    id = Column(Integer, primary_key=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False, index=True)

    phase = Column(String, nullable=False)  # avant, pendant, apres
    texte = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    chantier = relationship("Chantier", back_populates="notes")


class ConformiteItem(Base):
    __tablename__ = "conformite_items"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)

    type = Column(String, nullable=False)  # assurance_decennale, qualibat, rge, autre
    libelle = Column(String, nullable=False)
    date_expiration = Column(Date, nullable=False)
    document_url = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="conformites")


TACHE_PRIORITES = ["basse", "normale", "haute", "urgente"]


class Tache(Base):
    __tablename__ = "taches"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True, index=True)

    titre = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priorite = Column(String, default="normale")
    echeance = Column(Date, nullable=True)
    statut = Column(String, default="a_faire")  # a_faire, faite

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="taches")
    client = relationship("Client", back_populates="taches")
    chantier = relationship("Chantier", back_populates="taches")


class Evenement(Base):
    """Un evenement du planning : rendez-vous, visite, intervention. Les
    chantiers et taches avec echeance apparaissent aussi dans le planning,
    mais sont calcules a la volee plutot que dupliques ici."""

    __tablename__ = "evenements"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True, index=True)

    titre = Column(String, nullable=False)
    type = Column(String, default="rdv")  # rdv, visite, intervention, autre
    date_debut = Column(DateTime(timezone=True), nullable=False)
    date_fin = Column(DateTime(timezone=True), nullable=True)
    lieu = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="evenements")


class Document(Base):
    """Un document rattache a un client/chantier/devis/facture. Stocke comme
    URL (pas d'upload binaire pour l'instant, coherent avec les photos de
    chantier qui fonctionnent deja ainsi)."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=True, index=True)

    nom = Column(String, nullable=False)
    type = Column(String, default="autre")  # contrat, attestation, assurance, photo, plan, administratif, autre
    url = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="documents")
