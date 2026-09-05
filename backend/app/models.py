from datetime import datetime, date, timezone
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
    JSON,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import false as sql_false, true as sql_true

from app.database import Base

# Precision monetaire standard pour toute l'application : jamais de Float
# pour un montant (les erreurs d'arrondi binaire s'accumulent au fil des
# lectures/ecritures en base). 10 chiffres avant la virgule, 2 apres.
MONTANT = Numeric(10, 2)


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
    photo_profil_key = Column(String, nullable=True)

    @property
    def photo_profil_url(self):
        """URL API stable, sans exposer la cle de stockage interne."""
        return "/auth/me/photo-profil" if self.photo_profil_key else None

    # Presence en ligne : le site vitrine est livre par nous (pas de generateur
    # dans le SaaS), on garde juste un etat visible par l'artisan.
    site_url = Column(String, nullable=True)
    site_statut = Column(String, default="non_livre")  # non_livre, en_cours, livre

    onboarding_termine = Column(Boolean, default=False)

    # Delais du moteur de relance automatique, configurables par artisan (les
    # anciennes valeurs fixes 3/7/15 jours et 7 jours deviennent les defauts).
    relance_devis_j1 = Column(Integer, default=3)
    relance_devis_j2 = Column(Integer, default=7)
    relance_devis_j3 = Column(Integer, default=15)
    relance_facture_jours = Column(Integer, default=7)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, default="inactive")  # inactive, active, past_due, canceled
    plan = Column(String, default="gratuit")  # gratuit, essentiel, pro, business

    created_at = Column(DateTime(timezone=True), default=utcnow)

    clients = relationship("Client", back_populates="artisan", cascade="all, delete-orphan")
    avis = relationship("Avis", back_populates="artisan", cascade="all, delete-orphan")
    membres = relationship("Membre", back_populates="artisan", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="artisan", cascade="all, delete-orphan")
    devis = relationship("Devis", back_populates="artisan", cascade="all, delete-orphan")
    factures = relationship("Facture", back_populates="artisan", cascade="all, delete-orphan")
    chantiers = relationship("Chantier", back_populates="artisan", cascade="all, delete-orphan")
    conformites = relationship("ConformiteItem", back_populates="artisan", cascade="all, delete-orphan")
    taches = relationship("Tache", back_populates="artisan", cascade="all, delete-orphan")
    evenements = relationship("Evenement", back_populates="artisan", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="artisan", cascade="all, delete-orphan")
    prestations = relationship("Prestation", back_populates="artisan", cascade="all, delete-orphan")
    fournisseurs = relationship("Fournisseur", back_populates="artisan", cascade="all, delete-orphan")
    contrats = relationship("Contrat", back_populates="artisan", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="artisan", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="artisan", cascade="all, delete-orphan")
    site_medias = relationship("SiteMedia", back_populates="artisan", cascade="all, delete-orphan")
    site_media_usages = relationship("SiteMediaUsage", back_populates="artisan", cascade="all, delete-orphan")
    site_vitrine = relationship("SiteVitrine", back_populates="artisan", cascade="all, delete-orphan", uselist=False)


class AdminUser(Base):
    """Compte interne Suite Artisan, totalement separe des tenants artisans."""

    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nom = Column(String, nullable=False)
    actif = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)


class SiteVitrine(Base):
    """Etat d'exploitation d'un site livre par Suite Artisan.

    Les coordonnees et informations metier restent sur Artisan. Seules la
    configuration propre au rendu et les metadonnees de livraison vivent ici.
    """

    __tablename__ = "sites_vitrines"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), unique=True, nullable=False, index=True)
    statut = Column(String, nullable=False, default="brouillon")
    domaine = Column(String, nullable=True)
    url_publique = Column(String, nullable=True)
    storage_key = Column(String, nullable=True)
    config = Column(JSON, nullable=False, default=dict)
    # Historique du moteur de generation automatique de site (V3, puis Design
    # Genome), retire depuis : ces trois colonnes ne sont plus ecrites ni lues
    # par aucun runtime actif. Conservees telles quelles
    # (aucune migration destructive) pour ne pas perdre l'historique des
    # sites deja generes/publies avant le retrait du moteur.
    design_profile = Column(JSON, nullable=True)
    design_preferences = Column(JSON, nullable=True)
    candidate_design_profile = Column(JSON, nullable=True)
    date_generation = Column(DateTime(timezone=True), nullable=True)
    date_publication = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    artisan = relationship("Artisan", back_populates="site_vitrine")
    medias = relationship("SiteMedia", back_populates="site_vitrine")
    media_selections = relationship("SiteMediaSelection", back_populates="site_vitrine", cascade="all, delete-orphan")
    media_usages = relationship("SiteMediaUsage", back_populates="site_vitrine", cascade="all, delete-orphan")


class SiteMedia(Base):
    """Logo ou photo reelle fournie par un artisan pour son site vitrine."""

    __tablename__ = "site_medias"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    site_vitrine_id = Column(Integer, ForeignKey("sites_vitrines.id"), nullable=True, index=True)
    type_media = Column(String, nullable=False, index=True)  # logo, photo
    categorie = Column(String, nullable=True, index=True)
    storage_key = Column(String, nullable=False, unique=True)
    thumbnail_key = Column(String, nullable=False, unique=True)
    nom_original = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    taille_octets = Column(Integer, nullable=False)
    largeur = Column(Integer, nullable=True)
    hauteur = Column(Integer, nullable=True)
    ordre = Column(Integer, nullable=False, default=0)
    actif = Column(Boolean, nullable=False, default=True, server_default=sql_true())
    source = Column(String, nullable=False, default="artisan")
    alt_text = Column(String, nullable=True)
    checksum = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    artisan = relationship("Artisan", back_populates="site_medias")
    site_vitrine = relationship("SiteVitrine", back_populates="medias")
    selections = relationship("SiteMediaSelection", back_populates="site_media")


class SiteMediaLibrary(Base):
    """Registre global de medias de secours dont la licence est connue."""

    __tablename__ = "site_media_library"

    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(String, unique=True, nullable=False, index=True)
    metier = Column(String, nullable=False, index=True)
    sous_categorie = Column(String, nullable=False, index=True)
    storage_key = Column(String, nullable=False, unique=True)
    thumbnail_key = Column(String, nullable=True, unique=True)
    mime_type = Column(String, nullable=False, default="image/webp")
    largeur = Column(Integer, nullable=True)
    hauteur = Column(Integer, nullable=True)
    orientation = Column(String, nullable=False, default="paysage")
    usage_recommande = Column(JSON, nullable=False, default=list)
    licence = Column(String, nullable=False)
    source_nom = Column(String, nullable=False)
    credit = Column(String, nullable=True)
    provider = Column(String, nullable=True, index=True)
    provider_asset_id = Column(String, nullable=True, index=True)
    photographer = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    provider_url = Column(String, nullable=True)
    query = Column(String, nullable=True)
    licence_metadata = Column(JSON, nullable=True)
    times_used = Column(Integer, nullable=False, default=0, server_default="0")
    last_used_at = Column(DateTime(timezone=True), nullable=True, index=True)
    actif = Column(Boolean, nullable=False, default=True, server_default=sql_true())
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    selections = relationship("SiteMediaSelection", back_populates="library_media")
    usages = relationship("SiteMediaUsage", back_populates="library_media")


class SiteMediaProviderCache(Base):
    """Short-lived normalized provider search results; never stores API keys."""

    __tablename__ = "site_media_provider_cache"
    __table_args__ = (UniqueConstraint("provider", "query_key", name="uq_site_media_provider_cache_query"),)

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False, index=True)
    query_key = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class SiteMediaSelection(Base):
    """Media profile persistant d'un site, stable entre deux generations."""

    __tablename__ = "site_media_selections"
    __table_args__ = (
        UniqueConstraint("site_vitrine_id", "usage", "position", name="uq_site_media_selection_usage_position"),
        CheckConstraint(
            "(source = 'artisan' AND site_media_id IS NOT NULL AND library_media_id IS NULL) OR "
            "(source = 'bibliotheque' AND library_media_id IS NOT NULL AND site_media_id IS NULL) OR "
            "(source = 'fallback' AND site_media_id IS NULL AND library_media_id IS NULL)",
            name="ck_site_media_selection_source",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    site_vitrine_id = Column(Integer, ForeignKey("sites_vitrines.id"), nullable=False, index=True)
    usage = Column(String, nullable=False, index=True)
    position = Column(Integer, nullable=False, default=0)
    source = Column(String, nullable=False)
    site_media_id = Column(Integer, ForeignKey("site_medias.id"), nullable=True, index=True)
    library_media_id = Column(Integer, ForeignKey("site_media_library.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    site_vitrine = relationship("SiteVitrine", back_populates="media_selections")
    site_media = relationship("SiteMedia", back_populates="selections")
    library_media = relationship("SiteMediaLibrary", back_populates="selections")


class SiteMediaUsage(Base):
    """Historique borne consulte par l'anti-repetition de la bibliotheque."""

    __tablename__ = "site_media_usages"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    site_vitrine_id = Column(Integer, ForeignKey("sites_vitrines.id"), nullable=False, index=True)
    library_media_id = Column(Integer, ForeignKey("site_media_library.id"), nullable=False, index=True)
    usage = Column(String, nullable=False, index=True)
    selected_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    artisan = relationship("Artisan", back_populates="site_media_usages")
    site_vitrine = relationship("SiteVitrine", back_populates="media_usages")
    library_media = relationship("SiteMediaLibrary", back_populates="usages")


# Pipeline commercial : de la premiere demande jusqu'a la signature (ou la perte).
CLIENT_STATUTS = [
    "nouveau", "contacte", "qualification", "visite_prevue",
    "devis_a_faire", "devis_envoye", "negociation", "gagne", "perdu",
]

CLIENT_SOURCES = [
    "manuel", "site_vitrine", "google", "recommandation",
    "telephone", "facebook", "instagram", "ancien_client", "autre",
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
    source = Column(String, default="manuel")  # voir CLIENT_SOURCES

    # Pilotage du pipeline commercial (section CRM du cahier des charges V2).
    montant_estime = Column(MONTANT, nullable=True)
    probabilite = Column(Integer, nullable=True)  # 0-100
    prochaine_action = Column(String, nullable=True)

    # Jeton public pour demander un avis a ce client (voir Avis). Genere a la
    # demande, jamais expose autrement que dans ce lien.
    token_avis = Column(String, unique=True, index=True, nullable=True)

    # Jeton du portail client (espace limite : devis, factures, chantiers,
    # documents, messages - jamais les donnees d'un autre client). Regenerer
    # le jeton EST le mecanisme de revocation (l'ancien jeton ne correspond
    # plus a rien) ; l'expiration se calcule a partir de la date de generation
    # (voir PORTAIL_VALIDITE_JOURS dans routers/clients.py).
    token_portail = Column(String, unique=True, index=True, nullable=True)
    token_portail_genere_le = Column(DateTime(timezone=True), nullable=True)

    # Archivage plutot que suppression definitive (section 44 du cahier des
    # charges V4) : "Supprimer" un client n'efface plus rien, il disparait
    # juste des listes actives. Ses devis/factures/chantiers restent
    # intacts - jamais de perte de donnees financieres ou historiques.
    archive = Column(Boolean, nullable=False, default=False, server_default=sql_false())

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    artisan = relationship("Artisan", back_populates="clients")
    devis = relationship("Devis", back_populates="client", cascade="all, delete-orphan")
    factures = relationship("Facture", back_populates="client", cascade="all, delete-orphan")
    chantiers = relationship("Chantier", back_populates="client")
    taches = relationship("Tache", back_populates="client")
    avis = relationship("Avis", back_populates="client", cascade="all, delete-orphan")
    contrats = relationship("Contrat", back_populates="client", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="client", cascade="all, delete-orphan", order_by="Message.created_at")
    notifications = relationship("Notification", back_populates="client", cascade="all, delete-orphan")


class Devis(Base):
    __tablename__ = "devis"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)

    numero = Column(String, nullable=True)
    titre = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    taux_tva = Column(MONTANT, default=10.0)  # 10 = renovation, 20 = neuf
    acompte_pourcentage = Column(MONTANT, default=30.0)
    remise_pourcentage = Column(MONTANT, nullable=True)

    # nouveau -> envoye -> consulte -> relance_j3 -> relance_j7 -> relance_j15 -> signe / perdu / expire
    statut = Column(String, default="nouveau", index=True)

    date_envoi = Column(DateTime(timezone=True), nullable=True)
    date_consultation = Column(DateTime(timezone=True), nullable=True)
    date_derniere_relance = Column(DateTime(timezone=True), nullable=True)
    nb_relances = Column(Integer, default=0)
    date_signature = Column(DateTime(timezone=True), nullable=True)
    nom_signataire = Column(String, nullable=True)

    # Jeton oppaque pour le lien public de consultation/signature (envoye au
    # client par l'artisan). Genere a la creation, jamais expose autrement
    # que dans ce lien : ne pas confondre avec l'id, sequentiel et devinable.
    token = Column(String, unique=True, index=True, nullable=True)

    source = Column(String, default="manuel")  # manuel ou site_vitrine

    # Archivage plutot que suppression definitive (section 44) : un devis
    # supprime par l'artisan disparait des listes actives mais reste en base
    # (historique commercial, references depuis un chantier/une facture).
    archive = Column(Boolean, nullable=False, default=False, server_default=sql_false())

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="devis")
    client = relationship("Client", back_populates="devis")
    lignes = relationship("LigneDevis", back_populates="devis", cascade="all, delete-orphan", order_by="LigneDevis.ordre")
    factures = relationship("Facture", back_populates="devis")

    @property
    def montant_ht_brut(self):
        if not self.lignes:
            return None
        return round(sum(l.quantite * l.prix_unitaire_ht for l in self.lignes), 2)

    @property
    def remise_montant(self):
        brut = self.montant_ht_brut
        if brut is None or not self.remise_pourcentage:
            return None
        return round(brut * self.remise_pourcentage / 100, 2)

    @property
    def montant_ht(self):
        brut = self.montant_ht_brut
        if brut is None:
            return None
        remise = self.remise_montant or 0
        return round(brut - remise, 2)

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
    quantite = Column(MONTANT, default=1.0)
    unite = Column(String, default="u")
    prix_unitaire_ht = Column(MONTANT, nullable=False)
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
    contrat_id = Column(Integer, ForeignKey("contrats.id"), nullable=True, index=True)

    numero = Column(String, nullable=False)
    type = Column(String, default="standard")
    taux_tva = Column(MONTANT, default=10.0)

    # brouillon -> envoyee -> (partiellement_payee) -> payee / en_retard / annulee
    statut = Column(String, default="brouillon", index=True)

    date_emission = Column(Date, default=date.today)
    date_echeance = Column(Date, nullable=True)
    date_envoi = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)

    date_derniere_relance = Column(DateTime(timezone=True), nullable=True)
    nb_relances = Column(Integer, default=0)

    # Jeton public de consultation (meme logique que Devis.token) : genere a
    # la creation, permet au client d'ouvrir sa facture sans compte.
    token = Column(String, unique=True, index=True, nullable=True)

    # Archivage plutot que suppression definitive (section 44) : jamais
    # perdre une facture, meme retiree des listes actives.
    archive = Column(Boolean, nullable=False, default=False, server_default=sql_false())

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="factures")
    client = relationship("Client", back_populates="factures")
    devis = relationship("Devis", back_populates="factures")
    chantier = relationship("Chantier", back_populates="factures")
    contrat = relationship("Contrat", back_populates="factures")
    lignes = relationship("LigneFacture", back_populates="facture", cascade="all, delete-orphan", order_by="LigneFacture.ordre")
    paiements = relationship("Paiement", back_populates="facture", cascade="all, delete-orphan")

    @property
    def montant_ht(self):
        # Decimal, jamais float (voir MONTANT en tete de fichier) : une
        # facture sans ligne doit rester du meme type que le cas normal,
        # sinon montant_ttc (float * Decimal) plante juste en dessous.
        if not self.lignes:
            return Decimal("0.00")
        return round(sum(l.quantite * l.prix_unitaire_ht for l in self.lignes), 2)

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
    quantite = Column(MONTANT, default=1.0)
    unite = Column(String, default="u")
    prix_unitaire_ht = Column(MONTANT, nullable=False)
    ordre = Column(Integer, default=0)

    facture = relationship("Facture", back_populates="lignes")

    @property
    def total_ht(self):
        return round(self.quantite * self.prix_unitaire_ht, 2)


class Paiement(Base):
    __tablename__ = "paiements"

    id = Column(Integer, primary_key=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=False, index=True)

    montant = Column(MONTANT, nullable=False)
    date_paiement = Column(Date, default=date.today)
    moyen = Column(String, default="virement")  # virement, cheque, especes, cb, autre
    reference = Column(String, nullable=True)  # n° de cheque, reference de virement...
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
    budget = Column(MONTANT, nullable=True)

    # Reception : constatee reellement par l'artisan (jamais deduite automatiquement).
    date_reception = Column(Date, nullable=True)
    reserves = Column(Text, nullable=True)

    # Archivage plutot que suppression definitive (section 44) : garde
    # l'historique de chantier (depenses, heures, factures liees).
    archive = Column(Boolean, nullable=False, default=False, server_default=sql_false())

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="chantiers")
    client = relationship("Client", back_populates="chantiers")
    notes = relationship("ChantierNote", back_populates="chantier", cascade="all, delete-orphan")
    taches = relationship("Tache", back_populates="chantier")
    factures = relationship("Facture", back_populates="chantier")
    depenses = relationship("Depense", back_populates="chantier", cascade="all, delete-orphan")
    heures = relationship("HeureTravail", back_populates="chantier", cascade="all, delete-orphan")

    @property
    def total_depenses(self):
        return round(sum(d.montant for d in self.depenses), 2)

    @property
    def total_heures(self):
        if not self.heures:
            return None
        return round(float(sum(h.duree_heures for h in self.heures)), 2)

    @property
    def cout_main_oeuvre(self):
        """Cout reel de main d'oeuvre = somme des (heures x taux horaire) des
        entrees qui ont un taux renseigne. None si aucune entree n'a de taux
        (rien a calculer), jamais une estimation inventee sur les entrees qui
        n'en ont pas."""
        couts = [h.cout for h in self.heures if h.cout is not None]
        if not couts:
            return None
        return round(sum(couts), 2)

    @property
    def _cout_total_engage(self):
        """Depenses materiaux/sous-traitance + main d'oeuvre reelle (quand
        connue) : base commune pour marge_estimee et marge_reelle."""
        total = self.total_depenses
        if self.cout_main_oeuvre is not None:
            total += self.cout_main_oeuvre
        return total

    @property
    def marge_estimee(self):
        """Marge par rapport au budget prevu (avant meme d'avoir facture quoi que ce soit)."""
        if self.budget is None:
            return None
        return round(self.budget - self._cout_total_engage, 2)

    @property
    def _factures_actives(self):
        return [f for f in self.factures if f.statut not in ("brouillon", "annulee")]

    @property
    def montant_facture(self):
        """Total reellement facture au client (hors brouillons/factures annulees)."""
        actives = self._factures_actives
        if not actives:
            return None
        return round(sum(f.montant_ttc or 0 for f in actives), 2)

    @property
    def montant_encaisse(self):
        actives = self._factures_actives
        if not actives:
            return None
        return round(sum(f.montant_paye for f in actives), 2)

    @property
    def marge_reelle(self):
        """Marge reelle : ce qui a ete facture moins les couts engages (depenses
        + main d'oeuvre reelle quand elle est renseignee). Contrairement a
        marge_estimee (basee sur le budget previsionnel), reflete l'argent
        effectivement engage sur le chantier."""
        facture = self.montant_facture
        if facture is None:
            return None
        return round(facture - self._cout_total_engage, 2)

    @property
    def progression(self):
        """Avancement reel du chantier = part des taches liees (checklist de
        preparation + taches ajoutees ensuite) marquees faites. Jamais de
        pourcentage invente : None tant qu'aucune tache n'est liee."""
        if self.statut in ("termine", "facture", "paye"):
            return 100
        taches = self.taches
        if not taches:
            return None
        faites = sum(1 for t in taches if t.statut == "faite")
        return round(faites / len(taches) * 100)


class Depense(Base):
    """Une depense de chantier (materiaux, sous-traitance...) pour suivre la marge."""

    __tablename__ = "depenses"

    id = Column(Integer, primary_key=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False, index=True)
    fournisseur_id = Column(Integer, ForeignKey("fournisseurs.id"), nullable=True, index=True)

    libelle = Column(String, nullable=False)
    montant = Column(MONTANT, nullable=False)
    date_depense = Column(Date, default=date.today)

    chantier = relationship("Chantier", back_populates="depenses")
    fournisseur = relationship("Fournisseur", back_populates="depenses")

    @property
    def fournisseur_nom(self):
        return self.fournisseur.nom if self.fournisseur_id and self.fournisseur else None


class HeureTravail(Base):
    """Une plage d'heures travaillees par un intervenant (l'artisan lui-meme,
    un membre de l'equipe ou un sous-traitant sans compte) sur un chantier :
    alimente le cout de main d'oeuvre reel et la rentabilite (voir
    Chantier.cout_main_oeuvre). Volontairement simple - pas de pointeuse, pas
    de gestion RH, juste "combien d'heures et pour quel cout ce chantier
    consomme reellement"."""

    __tablename__ = "heures_travail"

    id = Column(Integer, primary_key=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=False, index=True)
    membre_id = Column(Integer, ForeignKey("membres.id"), nullable=True, index=True)

    # Toujours renseigne (denormalise depuis le membre au moment de la saisie
    # si membre_id est fourni) : reste lisible meme si le membre est plus tard
    # retire de l'equipe, et permet de saisir un intervenant sans compte
    # (l'artisan lui-meme, un sous-traitant).
    nom_intervenant = Column(String, nullable=False)
    date_travail = Column(Date, default=date.today)
    duree_heures = Column(Numeric(6, 2), nullable=False)
    # Cout horaire charge (optionnel) : sans lui, les heures sont quand meme
    # comptabilisees (total_heures) mais aucun cout n'est invente.
    taux_horaire = Column(MONTANT, nullable=True)
    note = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    chantier = relationship("Chantier", back_populates="heures")
    membre = relationship("Membre")

    @property
    def cout(self):
        if self.taux_horaire is None:
            return None
        # Reste en Decimal (comme MONTANT partout ailleurs) pour pouvoir
        # s'additionner sans conversion avec total_depenses/budget/facture
        # dans Chantier._cout_total_engage.
        return round(self.duree_heures * self.taux_horaire, 2)


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


class Prestation(Base):
    """Une ligne de catalogue reutilisable (bibliotheque de prestations),
    pour ne pas ressaisir les memes descriptions/prix a chaque devis."""

    __tablename__ = "prestations"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)

    description = Column(String, nullable=False)
    categorie = Column(String, nullable=True)
    unite = Column(String, default="u")
    prix_unitaire_ht = Column(MONTANT, nullable=False)
    taux_tva = Column(MONTANT, default=10.0)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="prestations")


class Document(Base):
    """Un document rattache a un client/chantier/devis/facture. Soit un
    fichier reellement uploade et stocke sur disque (chemin_fichier), soit
    un lien externe (url) — l'un des deux est toujours renseigne."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    chantier_id = Column(Integer, ForeignKey("chantiers.id"), nullable=True, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=True, index=True)

    nom = Column(String, nullable=False)
    type = Column(String, default="autre")  # contrat, attestation, assurance, photo, plan, administratif, autre
    url = Column(String, nullable=True)
    chemin_fichier = Column(String, nullable=True)
    nom_original = Column(String, nullable=True)
    taille_octets = Column(Integer, nullable=True)
    archive = Column(Boolean, nullable=False, default=False, server_default=sql_false())

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="documents")


class Avis(Base):
    """Un avis client, soit saisi a la main par l'artisan (recu par telephone,
    Google, en personne...), soit soumis par le client lui-meme via le lien
    public genere depuis sa fiche (voir Client.token_avis)."""

    __tablename__ = "avis"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)

    note = Column(Integer, nullable=False)  # 1 a 5
    commentaire = Column(Text, nullable=True)
    nom_auteur = Column(String, nullable=True)  # si pas de client lie, ou avis externe
    source = Column(String, default="manuel")  # manuel, lien_public

    # L'artisan choisit explicitement quels avis apparaissent sur son site
    # vitrine (voir GET /pub/{slug}/avis, consomme par le site livre a l'artisan).
    # Jamais publie par defaut : c'est une decision de l'artisan, pas la notre.
    publie_site = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="avis")
    client = relationship("Client", back_populates="avis")


MEMBRE_ROLES = ["administrateur", "salarie"]


class Membre(Base):
    """Un membre de l'equipe d'un artisan (fonction payante Business) :
    connexion propre (email/mot de passe), mais toutes les donnees restent
    scopees sur l'artisan (l'entreprise), pas sur le membre. Un
    "administrateur" peut gerer l'equipe, un "salarie" non."""

    __tablename__ = "membres"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)

    nom = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="salarie")  # voir MEMBRE_ROLES
    actif = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="membres")


# statuts possibles d'un EmailLog :
#   envoye          -> reellement transmis au fournisseur (Resend a accepte l'envoi)
#   echec           -> le fournisseur est configure mais l'envoi a echoue (reseau, refus...)
#   non_configure   -> pas de cle API : rien n'a ete envoye, on le dit clairement
#   sans_destinataire -> le destinataire n'a pas d'email renseigne
EMAIL_LOG_STATUTS = ["envoye", "echec", "non_configure", "sans_destinataire"]


class EmailLog(Base):
    """Trace de chaque email transactionnel tente (pas seulement les succes) :
    c'est la base de l'historique de communication visible dans la timeline
    client, et ca permet de ne jamais pretendre qu'un email est parti s'il
    ne l'est pas reellement (voir EMAIL_LOG_STATUTS)."""

    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=True, index=True)
    facture_id = Column(Integer, ForeignKey("factures.id"), nullable=True, index=True)

    type = Column(String, nullable=False)  # devis, relances, facture, paiement_recu, demande_avis, conformite_alerte, nouvelle_demande_devis
    destinataire = Column(String, nullable=True)
    objet = Column(String, nullable=True)
    statut = Column(String, nullable=False)  # voir EMAIL_LOG_STATUTS
    erreur = Column(Text, nullable=True)
    provider_id = Column(String, nullable=True)  # id renvoye par Resend, pour rapprochement/support

    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    artisan = relationship("Artisan", back_populates="email_logs")


class AutomationRun(Base):
    """Un passage du planificateur d'automatisation (voir scheduler.py).
    Sert a l'observabilite : on veut pouvoir repondre a "le job tourne-t-il
    vraiment ?" sans regarder les logs serveur bruts."""

    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    nb_devis_relances = Column(Integer, default=0)
    nb_factures_relancees = Column(Integer, default=0)
    nb_alertes_conformite = Column(Integer, default=0)
    nb_emails_envoyes = Column(Integer, default=0)
    nb_emails_non_configures = Column(Integer, default=0)
    nb_erreurs = Column(Integer, default=0)
    erreur = Column(Text, nullable=True)  # erreur fatale eventuelle qui a interrompu le cycle
    nb_contrats_factures = Column(Integer, default=0)


FOURNISSEUR_CATEGORIES = ["materiaux", "sous_traitance", "outillage", "autre"]


class Fournisseur(Base):
    """Une entreprise aupres de qui l'artisan achete (materiaux, sous-
    traitance, outillage...) - distinct d'un Client (a qui on vend).
    Un achat EST une Depense de chantier avec un fournisseur_id renseigne :
    pas de deuxieme table pour la meme notion."""

    __tablename__ = "fournisseurs"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)

    nom = Column(String, nullable=False)
    categorie = Column(String, default="autre")  # voir FOURNISSEUR_CATEGORIES
    contact_nom = Column(String, nullable=True)
    telephone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="fournisseurs")
    depenses = relationship("Depense", back_populates="fournisseur")

    @property
    def total_achats(self):
        return round(sum(float(d.montant or 0) for d in self.depenses), 2)


CONTRAT_FREQUENCES = ["mensuel", "trimestriel", "annuel"]
CONTRAT_STATUTS = ["actif", "suspendu", "resilie"]


class Contrat(Base):
    """Un contrat recurrent (entretien, maintenance...) : le planificateur
    d'automatisation (scheduler.py) genere et envoie automatiquement une
    facture a chaque echeance, sans intervention manuelle - meme logique
    EVENT->WAIT->ACTION que les relances de devis/factures."""

    __tablename__ = "contrats"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)

    titre = Column(String, nullable=False)
    montant_ht = Column(MONTANT, nullable=False)
    taux_tva = Column(MONTANT, default=10.0)
    frequence = Column(String, nullable=False)  # voir CONTRAT_FREQUENCES
    statut = Column(String, default="actif")  # voir CONTRAT_STATUTS
    prochaine_echeance = Column(Date, nullable=False)
    derniere_generation = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="contrats")
    client = relationship("Client", back_populates="contrats")
    factures = relationship("Facture", back_populates="contrat")


EXPEDITEUR_TYPES = ["artisan", "client"]


class Message(Base):
    """Message echange entre l'artisan et un client via le portail client
    (section 'communication' du cahier des charges). Un message envoye par
    le client n'est pas lu par defaut ; l'artisan le voit dans son centre de
    notifications tant qu'il ne l'a pas ouvert."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)

    expediteur = Column(String, nullable=False)  # voir EXPEDITEUR_TYPES
    texte = Column(Text, nullable=False)
    lu = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="messages")
    client = relationship("Client", back_populates="messages")


class Notification(Base):
    """Evenement interne persistant destine a un artisan.

    Le centre de notifications calcule aussi certaines alertes metier a la
    volee. Cette table porte uniquement les evenements qui doivent survivre
    a la requete d'origine, comme une demande recue depuis un site vitrine.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)

    type = Column(String, nullable=False)
    titre = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    view = Column(String, nullable=False, default="notifications")
    lu = Column(Boolean, nullable=False, default=False, server_default=sql_false())
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    artisan = relationship("Artisan", back_populates="notifications")
    client = relationship("Client", back_populates="notifications")


class NumeroSequence(Base):
    """Compteur par artisan/type de document/annee, utilise pour generer des
    numeros de devis/factures reglementaires (DEV-2026-0001, FAC-2026-0001...).
    Ne jamais deriver un numero d'un simple COUNT(*) : deux creations
    concurrentes liraient le meme compte et produiraient le meme numero.
    L'incrementation se fait via un UPDATE ... SET dernier_numero =
    dernier_numero + 1 (voir app/numerotation.py), atomique par verrouillage
    de ligne sur SQLite comme sur PostgreSQL."""

    __tablename__ = "numero_sequences"
    __table_args__ = (UniqueConstraint("artisan_id", "type_document", "annee", name="uq_numero_sequence_artisan_type_annee"),)

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)
    type_document = Column(String, nullable=False)  # "devis" ou "facture"
    annee = Column(Integer, nullable=False)
    dernier_numero = Column(Integer, nullable=False, default=0)
