from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

METIERS_VALIDES = {"plombier", "electricien", "macon", "peintre", "general"}
CLIENT_STATUTS = {
    "nouveau", "contacte", "qualification", "visite_prevue",
    "devis_a_faire", "devis_envoye", "negociation", "gagne", "perdu",
}
DEVIS_STATUTS = {
    "nouveau", "envoye", "consulte", "relance_j3", "relance_j7", "relance_j15",
    "signe", "perdu", "expire",
}
FACTURE_TYPES = {"standard", "acompte", "situation", "finale", "avoir"}
FACTURE_STATUTS = {"brouillon", "envoyee", "partiellement_payee", "payee", "en_retard", "annulee"}
CHANTIER_STATUTS = {"a_preparer", "planifie", "en_cours", "en_pause", "termine", "facture", "paye"}
CHANTIER_PHASES = {"avant", "pendant", "apres"}
CONFORMITE_TYPES = {"assurance_decennale", "qualibat", "rge", "autre"}
TACHE_PRIORITES = {"basse", "normale", "haute", "urgente"}
EVENEMENT_TYPES = {"rdv", "visite", "intervention", "autre"}
PAIEMENT_MOYENS = {"virement", "cheque", "especes", "cb", "autre"}
DOCUMENT_TYPES = {"contrat", "attestation", "assurance", "photo", "plan", "administratif", "autre"}
CLIENT_SOURCES = {
    "manuel", "site_vitrine", "google", "recommandation",
    "telephone", "facebook", "instagram", "ancien_client", "autre",
}


# ---------- Artisan (tenant) ----------

class ArtisanCreate(BaseModel):
    nom_entreprise: str
    metier: str
    email: EmailStr
    password: str
    telephone: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    siret: Optional[str] = None
    assurance_decennale_nom: Optional[str] = None
    slug: Optional[str] = None

    @field_validator("metier")
    @classmethod
    def metier_valide(cls, v):
        if v not in METIERS_VALIDES:
            raise ValueError(f"metier doit etre l'un de : {sorted(METIERS_VALIDES)}")
        return v

    @field_validator("password")
    @classmethod
    def password_min_longueur(cls, v):
        if len(v) < 8:
            raise ValueError("le mot de passe doit faire au moins 8 caracteres")
        return v


class ArtisanLogin(BaseModel):
    email: EmailStr
    password: str


class ArtisanUpdate(BaseModel):
    nom_entreprise: Optional[str] = None
    telephone: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    adresse: Optional[str] = None
    siret: Optional[str] = None
    assurance_decennale_nom: Optional[str] = None
    logo_url: Optional[str] = None
    onboarding_termine: Optional[bool] = None


class ArtisanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    nom_entreprise: str
    metier: str
    email: EmailStr
    telephone: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    adresse: Optional[str] = None
    siret: Optional[str] = None
    assurance_decennale_nom: Optional[str] = None
    logo_url: Optional[str] = None
    site_url: Optional[str] = None
    site_statut: str
    onboarding_termine: bool
    subscription_status: str
    plan: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    artisan: ArtisanOut


# ---------- Client (prospect / client, meme entite) ----------

class ClientCreate(BaseModel):
    nom: str
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    societe: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    notes: Optional[str] = None
    statut: str = "nouveau"
    source: str = "manuel"
    montant_estime: Optional[float] = None
    probabilite: Optional[int] = None
    prochaine_action: Optional[str] = None

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v not in CLIENT_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(CLIENT_STATUTS)}")
        return v

    @field_validator("source")
    @classmethod
    def source_valide(cls, v):
        if v not in CLIENT_SOURCES:
            raise ValueError(f"source doit etre l'une de : {sorted(CLIENT_SOURCES)}")
        return v

    @field_validator("probabilite")
    @classmethod
    def probabilite_valide(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("probabilite doit etre entre 0 et 100")
        return v


class ClientUpdate(BaseModel):
    nom: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    societe: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    notes: Optional[str] = None
    statut: Optional[str] = None
    source: Optional[str] = None
    montant_estime: Optional[float] = None
    probabilite: Optional[int] = None
    prochaine_action: Optional[str] = None

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v is not None and v not in CLIENT_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(CLIENT_STATUTS)}")
        return v

    @field_validator("source")
    @classmethod
    def source_valide(cls, v):
        if v is not None and v not in CLIENT_SOURCES:
            raise ValueError(f"source doit etre l'une de : {sorted(CLIENT_SOURCES)}")
        return v

    @field_validator("probabilite")
    @classmethod
    def probabilite_valide(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("probabilite doit etre entre 0 et 100")
        return v


class ClientPublicCreate(BaseModel):
    """Ce que le formulaire du site vitrine envoie (creation d'un prospect)."""

    nom: str
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    message: Optional[str] = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    nom: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    societe: Optional[str] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    notes: Optional[str] = None
    statut: str
    source: str
    montant_estime: Optional[float] = None
    probabilite: Optional[int] = None
    prochaine_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ClientResume(BaseModel):
    valeur_totale: float
    nb_chantiers: int
    dernier_contact: Optional[datetime] = None
    impayes: float
    date_dernier_devis: Optional[datetime] = None


class TimelineEntry(BaseModel):
    date: datetime
    type: str  # devis_cree, devis_envoye, devis_signe, facture_envoyee, paiement_recu, chantier_demarre, ...
    label: str
    reference_id: Optional[int] = None


# ---------- Devis ----------

class LigneDevisIn(BaseModel):
    description: str
    quantite: float = 1.0
    unite: str = "u"
    prix_unitaire_ht: float


class LigneDevisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    quantite: float
    unite: str
    prix_unitaire_ht: float
    ordre: int
    total_ht: float


class DevisCreate(BaseModel):
    client_id: Optional[int] = None
    nouveau_client: Optional[ClientCreate] = None  # cree le client a la volee si client_id absent
    titre: Optional[str] = None
    description: Optional[str] = None
    taux_tva: float = 10.0
    acompte_pourcentage: float = 30.0
    remise_pourcentage: Optional[float] = None
    lignes: list[LigneDevisIn] = []

    @field_validator("taux_tva")
    @classmethod
    def tva_valide(cls, v):
        if v not in (10.0, 20.0):
            raise ValueError("taux_tva doit etre 10 (renovation) ou 20 (neuf)")
        return v

    @field_validator("remise_pourcentage")
    @classmethod
    def remise_valide(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("remise_pourcentage doit etre entre 0 et 100")
        return v


class DevisUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    taux_tva: Optional[float] = None
    acompte_pourcentage: Optional[float] = None
    remise_pourcentage: Optional[float] = None
    statut: Optional[str] = None
    lignes: Optional[list[LigneDevisIn]] = None  # si fourni, remplace toutes les lignes

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v is not None and v not in DEVIS_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(DEVIS_STATUTS)}")
        return v

    @field_validator("remise_pourcentage")
    @classmethod
    def remise_valide(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("remise_pourcentage doit etre entre 0 et 100")
        return v


class DevisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_id: int
    client_nom: str
    numero: Optional[str] = None
    titre: Optional[str] = None
    description: Optional[str] = None
    taux_tva: float
    acompte_pourcentage: float
    remise_pourcentage: Optional[float] = None
    montant_ht_brut: Optional[float] = None
    remise_montant: Optional[float] = None
    montant_ht: Optional[float] = None
    montant_ttc: Optional[float] = None
    statut: str
    date_envoi: Optional[datetime] = None
    date_consultation: Optional[datetime] = None
    date_derniere_relance: Optional[datetime] = None
    date_signature: Optional[datetime] = None
    nom_signataire: Optional[str] = None
    nb_relances: int
    source: str
    token: Optional[str] = None
    created_at: datetime
    lignes: list[LigneDevisOut] = []


class DevisAccepterIn(BaseModel):
    nom_signataire: str


class DevisPublicOut(BaseModel):
    """Ce que voit le client sur le lien public du devis. Pas d'ids
    internes, pas de donnees d'un autre artisan."""
    model_config = ConfigDict(from_attributes=True)

    numero: Optional[str] = None
    titre: Optional[str] = None
    description: Optional[str] = None
    client_nom: str
    taux_tva: float
    acompte_pourcentage: float
    remise_pourcentage: Optional[float] = None
    montant_ht_brut: Optional[float] = None
    remise_montant: Optional[float] = None
    montant_ht: Optional[float] = None
    montant_ttc: Optional[float] = None
    statut: str
    date_signature: Optional[datetime] = None
    nom_signataire: Optional[str] = None
    lignes: list[LigneDevisOut] = []
    artisan_nom_entreprise: str
    artisan_telephone: Optional[str] = None
    artisan_email: str
    artisan_adresse: Optional[str] = None
    artisan_siret: Optional[str] = None
    artisan_assurance_decennale_nom: Optional[str] = None


# ---------- Facture ----------

class LigneFactureIn(BaseModel):
    description: str
    quantite: float = 1.0
    unite: str = "u"
    prix_unitaire_ht: float


class LigneFactureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    quantite: float
    unite: str
    prix_unitaire_ht: float
    ordre: int
    total_ht: float


class FactureCreate(BaseModel):
    client_id: int
    devis_id: Optional[int] = None
    chantier_id: Optional[int] = None
    type: str = "standard"
    taux_tva: float = 10.0
    date_echeance: Optional[date] = None
    notes: Optional[str] = None
    lignes: list[LigneFactureIn] = []

    @field_validator("type")
    @classmethod
    def type_valide(cls, v):
        if v not in FACTURE_TYPES:
            raise ValueError(f"type doit etre l'un de : {sorted(FACTURE_TYPES)}")
        return v


class FactureUpdate(BaseModel):
    statut: Optional[str] = None
    date_echeance: Optional[date] = None
    notes: Optional[str] = None
    lignes: Optional[list[LigneFactureIn]] = None

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v is not None and v not in FACTURE_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(FACTURE_STATUTS)}")
        return v


class PaiementCreate(BaseModel):
    montant: float
    date_paiement: date
    moyen: str = "virement"
    reference: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("moyen")
    @classmethod
    def moyen_valide(cls, v):
        if v not in PAIEMENT_MOYENS:
            raise ValueError(f"moyen doit etre l'un de : {sorted(PAIEMENT_MOYENS)}")
        return v


class PaiementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    facture_id: int
    montant: float
    date_paiement: date
    moyen: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class FactureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_id: int
    client_nom: str
    devis_id: Optional[int] = None
    chantier_id: Optional[int] = None
    numero: str
    type: str
    taux_tva: float
    statut: str
    montant_ht: float
    montant_ttc: float
    montant_paye: float
    montant_restant: float
    est_en_retard: bool
    date_emission: date
    date_echeance: Optional[date] = None
    date_envoi: Optional[datetime] = None
    notes: Optional[str] = None
    date_derniere_relance: Optional[datetime] = None
    nb_relances: int = 0
    created_at: datetime
    lignes: list[LigneFactureOut] = []
    paiements: list[PaiementOut] = []


# ---------- Chantiers ----------

class ChantierCreate(BaseModel):
    client_id: int
    devis_id: Optional[int] = None
    titre: str
    adresse: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin_prevue: Optional[date] = None
    budget: Optional[float] = None


class ChantierUpdate(BaseModel):
    titre: Optional[str] = None
    adresse: Optional[str] = None
    statut: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin_prevue: Optional[date] = None
    budget: Optional[float] = None

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v is not None and v not in CHANTIER_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(CHANTIER_STATUTS)}")
        return v


class DepenseCreate(BaseModel):
    libelle: str
    montant: float
    date_depense: date


class DepenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chantier_id: int
    libelle: str
    montant: float
    date_depense: date


class ChantierNoteCreate(BaseModel):
    phase: str
    texte: Optional[str] = None
    photo_url: Optional[str] = None

    @field_validator("phase")
    @classmethod
    def phase_valide(cls, v):
        if v not in CHANTIER_PHASES:
            raise ValueError(f"phase doit etre l'une de : {sorted(CHANTIER_PHASES)}")
        return v


class ChantierNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chantier_id: int
    phase: str
    texte: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime


class ChantierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_id: int
    client_nom: str
    devis_id: Optional[int] = None
    titre: str
    adresse: Optional[str] = None
    statut: str
    date_debut: Optional[date] = None
    date_fin_prevue: Optional[date] = None
    budget: Optional[float] = None
    total_depenses: float
    marge_estimee: Optional[float] = None
    created_at: datetime
    notes: list[ChantierNoteOut] = []
    depenses: list[DepenseOut] = []


# ---------- Conformite ----------

class ConformiteCreate(BaseModel):
    type: str
    libelle: str
    date_expiration: date
    document_url: Optional[str] = None

    @field_validator("type")
    @classmethod
    def type_valide(cls, v):
        if v not in CONFORMITE_TYPES:
            raise ValueError(f"type doit etre l'un de : {sorted(CONFORMITE_TYPES)}")
        return v


class ConformiteUpdate(BaseModel):
    libelle: Optional[str] = None
    date_expiration: Optional[date] = None
    document_url: Optional[str] = None


class ConformiteOut(BaseModel):
    id: int
    artisan_id: int
    type: str
    libelle: str
    date_expiration: date
    document_url: Optional[str] = None
    created_at: datetime
    alerte: bool = False
    jours_restants: Optional[int] = None


# ---------- Taches ----------

class TacheCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    priorite: str = "normale"
    echeance: Optional[date] = None
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None

    @field_validator("priorite")
    @classmethod
    def priorite_valide(cls, v):
        if v not in TACHE_PRIORITES:
            raise ValueError(f"priorite doit etre l'une de : {sorted(TACHE_PRIORITES)}")
        return v


class TacheUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    priorite: Optional[str] = None
    echeance: Optional[date] = None
    statut: Optional[str] = None


class TacheOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None
    titre: str
    description: Optional[str] = None
    priorite: str
    echeance: Optional[date] = None
    statut: str
    created_at: datetime


# ---------- Planning ----------

class EvenementCreate(BaseModel):
    titre: str
    type: str = "rdv"
    date_debut: datetime
    date_fin: Optional[datetime] = None
    lieu: Optional[str] = None
    notes: Optional[str] = None
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None

    @field_validator("type")
    @classmethod
    def type_valide(cls, v):
        if v not in EVENEMENT_TYPES:
            raise ValueError(f"type doit etre l'un de : {sorted(EVENEMENT_TYPES)}")
        return v


class EvenementUpdate(BaseModel):
    titre: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    lieu: Optional[str] = None
    notes: Optional[str] = None


class EvenementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None
    titre: str
    type: str
    date_debut: datetime
    date_fin: Optional[datetime] = None
    lieu: Optional[str] = None
    notes: Optional[str] = None


# ---------- Documents ----------

class DocumentCreate(BaseModel):
    nom: str
    type: str = "autre"
    url: str
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None
    devis_id: Optional[int] = None
    facture_id: Optional[int] = None

    @field_validator("type")
    @classmethod
    def type_valide(cls, v):
        if v not in DOCUMENT_TYPES:
            raise ValueError(f"type doit etre l'un de : {sorted(DOCUMENT_TYPES)}")
        return v


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None
    devis_id: Optional[int] = None
    facture_id: Optional[int] = None
    nom: str
    type: str
    url: str
    created_at: datetime


# ---------- Planning (agrege evenements + echeances de taches/chantiers) ----------

class PlanningItem(BaseModel):
    date: datetime
    type: str  # rdv, visite, intervention, autre, tache, chantier_debut, chantier_fin
    titre: str
    reference_id: Optional[int] = None
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None


# ---------- Dashboard ----------

class DashboardAujourdhui(BaseModel):
    taches: list[TacheOut] = []
    evenements: list[EvenementOut] = []
    devis_a_relancer: list[DevisOut] = []
    factures_en_retard: list[FactureOut] = []


class DashboardCommercial(BaseModel):
    nouveaux_prospects_7j: int
    devis_en_attente: int
    devis_acceptes_30j: int
    taux_transformation: float  # % devis signes parmi les devis envoyes (tous statuts finaux confondus)
    valeur_pipeline: float


class DashboardFinances(BaseModel):
    ca_mois: float
    ca_annee: float
    a_encaisser: float
    montant_en_retard: float
    paiements_recents: list[PaiementOut] = []


class DashboardPresenceSite(BaseModel):
    statut: str  # non_livre, en_cours, livre
    url: Optional[str] = None
    nb_demandes_total: int
    nb_demandes_30j: int


class DashboardOut(BaseModel):
    aujourdhui: DashboardAujourdhui
    commercial: DashboardCommercial
    finances: DashboardFinances
    alertes_conformite: list[ConformiteOut] = []
    presence_site: DashboardPresenceSite


# ---------- Recherche globale ----------

class SearchResult(BaseModel):
    type: str  # client, devis, facture, chantier
    id: int
    label: str
    sublabel: str = ""


# ---------- Analytics ----------

class AnalyticsMois(BaseModel):
    mois: str  # "2026-08"
    ca: float


class AnalyticsOut(BaseModel):
    ca_par_mois: list[AnalyticsMois]
    nb_devis_total: int
    nb_devis_signes: int
    taux_acceptation: float
    panier_moyen: float
    delai_moyen_paiement_jours: Optional[float] = None
    nb_clients_acquis: int
    nb_clients_recurrents: int  # clients avec plus d'un devis signe
    montant_impayes: float
    valeur_pipeline: float


# ---------- Catalogue de prestations ----------

class PrestationCreate(BaseModel):
    description: str
    categorie: Optional[str] = None
    unite: str = "u"
    prix_unitaire_ht: float
    taux_tva: float = 10.0

    @field_validator("taux_tva")
    @classmethod
    def tva_valide(cls, v):
        if v not in (10.0, 20.0):
            raise ValueError("taux_tva doit etre 10 (renovation) ou 20 (neuf)")
        return v


class PrestationUpdate(BaseModel):
    description: Optional[str] = None
    categorie: Optional[str] = None
    unite: Optional[str] = None
    prix_unitaire_ht: Optional[float] = None
    taux_tva: Optional[float] = None

    @field_validator("taux_tva")
    @classmethod
    def tva_valide(cls, v):
        if v is not None and v not in (10.0, 20.0):
            raise ValueError("taux_tva doit etre 10 (renovation) ou 20 (neuf)")
        return v


class PrestationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    description: str
    categorie: Optional[str] = None
    unite: str
    prix_unitaire_ht: float
    taux_tva: float
    created_at: datetime
