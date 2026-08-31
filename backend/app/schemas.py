from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, model_validator

METIERS_VALIDES = {"plombier", "electricien", "macon", "peintre", "menuisier", "renovateur", "general"}
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


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_min_longueur(cls, v):
        if len(v) < 8:
            raise ValueError("le nouveau mot de passe doit faire au moins 8 caracteres")
        return v


class ArtisanUpdate(BaseModel):
    nom_entreprise: Optional[str] = None
    metier: Optional[str] = None
    telephone: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    adresse: Optional[str] = None
    siret: Optional[str] = None
    assurance_decennale_nom: Optional[str] = None
    logo_url: Optional[str] = None
    onboarding_termine: Optional[bool] = None
    relance_devis_j1: Optional[int] = None
    relance_devis_j2: Optional[int] = None
    relance_devis_j3: Optional[int] = None
    relance_facture_jours: Optional[int] = None

    @field_validator("metier")
    @classmethod
    def metier_valide(cls, v):
        if v is not None and v not in METIERS_VALIDES:
            raise ValueError(f"metier doit etre l'un de : {sorted(METIERS_VALIDES)}")
        return v

    @model_validator(mode="after")
    def delais_relance_valides(self):
        valeurs = [self.relance_devis_j1, self.relance_devis_j2, self.relance_devis_j3]
        if any(v is not None for v in valeurs):
            if any(v is None for v in valeurs):
                raise ValueError("Les 3 delais de relance devis doivent etre fournis ensemble")
            if not (0 < valeurs[0] < valeurs[1] < valeurs[2]):
                raise ValueError("Les delais de relance devis doivent etre croissants (ex: 3, 7, 15)")
        if self.relance_facture_jours is not None and self.relance_facture_jours <= 0:
            raise ValueError("Le delai de relance facture doit etre positif")
        return self


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
    relance_devis_j1: int
    relance_devis_j2: int
    relance_devis_j3: int
    relance_facture_jours: int
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    artisan: ArtisanOut


# ---------- Equipe (membres) ----------

MEMBRE_ROLES = {"administrateur", "salarie"}


class MembreCreate(BaseModel):
    nom: str
    email: EmailStr
    password: str
    role: str = "salarie"

    @field_validator("password")
    @classmethod
    def password_valide(cls, v):
        if len(v) < 8:
            raise ValueError("Le mot de passe doit faire au moins 8 caracteres")
        return v

    @field_validator("role")
    @classmethod
    def role_valide(cls, v):
        if v not in MEMBRE_ROLES:
            raise ValueError(f"role doit etre l'un de : {sorted(MEMBRE_ROLES)}")
        return v


class MembreUpdate(BaseModel):
    nom: Optional[str] = None
    role: Optional[str] = None
    actif: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def role_valide(cls, v):
        if v is not None and v not in MEMBRE_ROLES:
            raise ValueError(f"role doit etre l'un de : {sorted(MEMBRE_ROLES)}")
        return v


class MembreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    nom: str
    email: EmailStr
    role: str
    actif: bool
    created_at: datetime


class MoiOut(BaseModel):
    role: str  # proprietaire, administrateur, salarie
    nom: str
    email: EmailStr
    membre_id: Optional[int] = None


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
    token_avis: Optional[str] = None
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
    relance_manuelle_possible: bool = False
    relance_manuelle_disponible_le: Optional[datetime] = None
    created_at: datetime
    lignes: list[LigneDevisOut] = []


class RelanceDevisOut(DevisOut):
    email_statut: str
    message: str


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
    montant: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
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
    contrat_id: Optional[int] = None
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
    token: Optional[str] = None
    created_at: datetime
    lignes: list[LigneFactureOut] = []
    paiements: list[PaiementOut] = []


class PaiementPublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    montant: float
    date_paiement: date
    moyen: str


class FacturePublicOut(BaseModel):
    """Ce que voit le client sur le lien public de sa facture. Pas d'ids
    internes, pas de donnees d'un autre artisan (meme principe que DevisPublicOut)."""
    model_config = ConfigDict(from_attributes=True)

    numero: str
    type: str
    client_nom: str
    taux_tva: float
    statut: str
    montant_ht: float
    montant_ttc: float
    montant_paye: float
    montant_restant: float
    est_en_retard: bool
    date_emission: date
    date_echeance: Optional[date] = None
    lignes: list[LigneFactureOut] = []
    paiements: list[PaiementPublicOut] = []
    artisan_nom_entreprise: str
    artisan_telephone: Optional[str] = None
    artisan_email: str
    artisan_siret: Optional[str] = None


# ---------- Chantiers ----------

class ChantierCreate(BaseModel):
    client_id: int
    devis_id: Optional[int] = None
    titre: str
    adresse: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin_prevue: Optional[date] = None
    budget: Optional[float] = None

    @field_validator("budget")
    @classmethod
    def budget_valide(cls, v):
        if v is not None and v < 0:
            raise ValueError("Le budget doit etre positif ou nul.")
        return v


class ChantierUpdate(BaseModel):
    client_id: Optional[int] = None
    titre: Optional[str] = None
    adresse: Optional[str] = None
    statut: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin_prevue: Optional[date] = None
    budget: Optional[float] = None
    date_reception: Optional[date] = None
    reserves: Optional[str] = None

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v is not None and v not in CHANTIER_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(CHANTIER_STATUTS)}")
        return v

    @field_validator("budget")
    @classmethod
    def budget_valide(cls, v):
        if v is not None and v < 0:
            raise ValueError("Le budget doit etre positif ou nul.")
        return v


class DepenseCreate(BaseModel):
    libelle: str
    montant: float
    date_depense: date
    fournisseur_id: Optional[int] = None

    @field_validator("montant")
    @classmethod
    def montant_positif(cls, v):
        if v <= 0:
            raise ValueError("Le montant doit etre superieur a 0.")
        return v


class DepenseUpdate(BaseModel):
    libelle: Optional[str] = None
    montant: Optional[float] = None
    date_depense: Optional[date] = None
    fournisseur_id: Optional[int] = None

    @field_validator("montant")
    @classmethod
    def montant_positif(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Le montant doit etre superieur a 0.")
        return v


class DepenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chantier_id: int
    libelle: str
    montant: float
    date_depense: date
    fournisseur_id: Optional[int] = None
    fournisseur_nom: Optional[str] = None


class HeureTravailCreate(BaseModel):
    nom_intervenant: str
    membre_id: Optional[int] = None
    date_travail: date
    duree_heures: float
    taux_horaire: Optional[float] = None
    note: Optional[str] = None

    @field_validator("duree_heures")
    @classmethod
    def duree_positive(cls, v):
        if v <= 0:
            raise ValueError("La duree doit etre superieure a 0.")
        return v


class HeureTravailUpdate(BaseModel):
    nom_intervenant: Optional[str] = None
    membre_id: Optional[int] = None
    date_travail: Optional[date] = None
    duree_heures: Optional[float] = None
    taux_horaire: Optional[float] = None
    note: Optional[str] = None

    @field_validator("duree_heures")
    @classmethod
    def duree_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("La duree doit etre superieure a 0.")
        return v

    @field_validator("taux_horaire")
    @classmethod
    def taux_positif(cls, v):
        if v is not None and v < 0:
            raise ValueError("Le taux horaire doit etre positif ou nul.")
        return v


class HeureTravailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chantier_id: int
    membre_id: Optional[int] = None
    nom_intervenant: str
    date_travail: date
    duree_heures: float
    taux_horaire: Optional[float] = None
    cout: Optional[float] = None
    note: Optional[str] = None


FOURNISSEUR_CATEGORIES = {"materiaux", "sous_traitance", "outillage", "autre"}


class FournisseurCreate(BaseModel):
    nom: str
    categorie: str = "autre"
    contact_nom: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("categorie")
    @classmethod
    def categorie_valide(cls, v):
        if v not in FOURNISSEUR_CATEGORIES:
            raise ValueError(f"categorie doit etre l'une de : {sorted(FOURNISSEUR_CATEGORIES)}")
        return v


class FournisseurUpdate(BaseModel):
    nom: Optional[str] = None
    categorie: Optional[str] = None
    contact_nom: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("categorie")
    @classmethod
    def categorie_valide(cls, v):
        if v is not None and v not in FOURNISSEUR_CATEGORIES:
            raise ValueError(f"categorie doit etre l'une de : {sorted(FOURNISSEUR_CATEGORIES)}")
        return v


class FournisseurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    categorie: str
    contact_nom: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    adresse: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    total_achats: float = 0.0


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
    total_heures: Optional[float] = None
    cout_main_oeuvre: Optional[float] = None
    marge_estimee: Optional[float] = None
    montant_facture: Optional[float] = None
    montant_encaisse: Optional[float] = None
    marge_reelle: Optional[float] = None
    progression: Optional[int] = None
    finances_verrouillees: bool = False
    date_reception: Optional[date] = None
    reserves: Optional[str] = None
    created_at: datetime
    notes: list[ChantierNoteOut] = []
    depenses: list[DepenseOut] = []
    heures: list[HeureTravailOut] = []
    taches: "list[TacheOut]" = []


# ---------- Workflows (devis signe -> chantier, chantier termine -> cloture) ----------

class PreparerChantierIn(BaseModel):
    adresse: Optional[str] = None
    date_debut: Optional[date] = None
    budget: Optional[float] = None
    creer_acompte: bool = True
    creer_checklist: bool = True


class PreparerChantierOut(BaseModel):
    chantier: ChantierOut
    facture_acompte: Optional[FactureOut] = None
    nb_taches_creees: int = 0


class CloturerChantierIn(BaseModel):
    generer_facture_finale: bool = True
    demander_avis: bool = True


class CloturerChantierOut(BaseModel):
    chantier: ChantierOut
    facture_finale: Optional[FactureOut] = None
    facture_finale_email_statut: Optional[str] = None
    facture_finale_raison_absence: Optional[str] = None
    avis_demande: bool = False
    avis_email_statut: Optional[str] = None
    tache_suivi_creee: bool = False


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


ChantierOut.model_rebuild()


# ---------- Planning ----------

def _naive_vers_utc(v):
    """SQLite ne conserve pas le fuseau horaire des colonnes
    DateTime(timezone=True) : une valeur relue depuis la base revient
    "naive" (tzinfo=None) alors qu'elle represente en realite un instant
    UTC (seule convention temporelle du backend - le frontend convertit
    toujours vers UTC avant l'envoi, voir planningLocalToUtcIso() dans
    app.js). Sans ce correctif, l'API renvoyait ces dates sans marqueur de
    fuseau ("Z"/"+00:00"), et le frontend les reinterpretait dans le fuseau
    AMBIANT du navigateur au lieu d'UTC - d'ou un decalage silencieux a
    l'affichage. PostgreSQL (production) renvoie deja des datetime "aware" :
    ce correctif ne fait rien dans ce cas (fonctionne donc dans les deux
    environnements)."""
    if isinstance(v, datetime) and v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v


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

    @field_validator("date_debut", "date_fin", mode="before")
    @classmethod
    def _dates_toujours_utc(cls, v):
        return _naive_vers_utc(v)


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
    url: Optional[str] = None
    nom_original: Optional[str] = None
    taille_octets: Optional[int] = None
    archive: bool = False
    created_at: datetime


# ---------- Planning (agrege evenements + echeances de taches/chantiers) ----------

class PlanningItem(BaseModel):
    date: datetime
    type: str  # rdv, visite, intervention, autre, tache, chantier_debut, chantier_fin
    titre: str
    reference_id: Optional[int] = None
    client_id: Optional[int] = None
    chantier_id: Optional[int] = None
    lieu: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def _date_toujours_utc(cls, v):
        return _naive_vers_utc(v)


# ---------- Dashboard ----------

class DashboardAujourdhui(BaseModel):
    taches: list[TacheOut] = []
    evenements: list[EvenementOut] = []
    devis_a_relancer: list[DevisOut] = []
    factures_en_retard: list[FactureOut] = []
    chantiers_a_venir: list[ChantierOut] = []


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
    nb_clients_gagnes: int = 0
    ca_genere: float = 0.0
    taux_conversion: Optional[float] = None  # None si aucune demande recue (rien a diviser honnetement)


class DashboardOut(BaseModel):
    aujourdhui: DashboardAujourdhui
    commercial: DashboardCommercial
    finances: DashboardFinances
    alertes_conformite: list[ConformiteOut] = []
    presence_site: DashboardPresenceSite


# ---------- Recommandations & sante entreprise ----------

class RecommandationOut(BaseModel):
    message: str
    urgence: str  # haute, moyenne, basse
    view: str
    reference_id: Optional[int] = None


class SousScoreOut(BaseModel):
    label: str
    valeur: Optional[int] = None  # 0-100, None si pas assez de donnees pour juger honnetement
    raison_absence: Optional[str] = None


class SanteEntrepriseOut(BaseModel):
    score_global: Optional[int] = None
    raison_absence_globale: Optional[str] = None
    commercial: SousScoreOut
    tresorerie: SousScoreOut
    chantiers: SousScoreOut
    conformite: SousScoreOut
    organisation: SousScoreOut


class ActivationOut(BaseModel):
    """Suivi d'activation (section 30/31 du cahier des charges V4) : chaque
    etape est deduite de donnees reellement presentes, jamais d'un flag
    fabrique - un artisan qui a un vrai client a coche "premier_client",
    point final."""
    entreprise_configuree: bool
    premier_client: bool
    premier_devis: bool
    premier_devis_envoye: bool
    premier_chantier: bool
    premiere_facture: bool
    entierement_active: bool


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


class AnalyticsSource(BaseModel):
    source: str
    nb_clients: int
    nb_gagnes: int
    ca: float


class FunnelEtapeOut(BaseModel):
    etape: str
    nb: int


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
    sources_acquisition: list[AnalyticsSource] = []
    funnel_site: list[FunnelEtapeOut] = []


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


# ---------- Avis clients ----------

class AvisCreate(BaseModel):
    client_id: Optional[int] = None
    note: int
    commentaire: Optional[str] = None
    nom_auteur: Optional[str] = None

    @field_validator("note")
    @classmethod
    def note_valide(cls, v):
        if v not in (1, 2, 3, 4, 5):
            raise ValueError("note doit etre comprise entre 1 et 5")
        return v


class AvisPublicIn(BaseModel):
    note: int
    commentaire: Optional[str] = None

    @field_validator("note")
    @classmethod
    def note_valide(cls, v):
        if v not in (1, 2, 3, 4, 5):
            raise ValueError("note doit etre comprise entre 1 et 5")
        return v


class AvisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_id: Optional[int] = None
    client_nom: Optional[str] = None
    note: int
    commentaire: Optional[str] = None
    nom_auteur: Optional[str] = None
    source: str
    publie_site: bool = False
    created_at: datetime


class AvisUpdate(BaseModel):
    publie_site: bool


class AvisPublicSiteOut(BaseModel):
    note: int
    commentaire: Optional[str] = None
    nom_auteur: Optional[str] = None


class DemandeAvisOut(BaseModel):
    token_avis: str


class PortailTokenOut(BaseModel):
    token_portail: str
    genere_le: datetime
    expire_le: datetime


class AvisPublicStatutOut(BaseModel):
    artisan_nom_entreprise: str
    client_nom: str
    deja_soumis: bool


# ---------- Messages (communication artisan <-> client via le portail) ----------

class MessageCreate(BaseModel):
    texte: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expediteur: str
    texte: str
    lu: bool
    created_at: datetime


# ---------- Portail client (espace limite : jamais les donnees d'un autre client) ----------

class PortailDevisOut(BaseModel):
    numero: Optional[str] = None
    titre: Optional[str] = None
    statut: str
    montant_ttc: float
    date_signature: Optional[datetime] = None
    token: Optional[str] = None


class PortailFactureOut(BaseModel):
    numero: str
    statut: str
    montant_ttc: float
    montant_restant: float
    est_en_retard: bool
    date_echeance: Optional[date] = None
    token: Optional[str] = None


class PortailPhotoOut(BaseModel):
    id: int
    nom: str


class PortailChantierOut(BaseModel):
    titre: str
    statut: str
    date_debut: Optional[date] = None
    date_fin_prevue: Optional[date] = None
    progression: Optional[int] = None
    photos: list[PortailPhotoOut] = []


class PortailClientOut(BaseModel):
    artisan_nom_entreprise: str
    artisan_telephone: Optional[str] = None
    artisan_email: Optional[str] = None
    client_nom: str
    devis: list[PortailDevisOut] = []
    factures: list[PortailFactureOut] = []
    chantiers: list[PortailChantierOut] = []
    messages: list[MessageOut] = []


# ---------- Notifications (centre de notifications) ----------

class NotificationOut(BaseModel):
    type: str  # devis_relance, facture_relance, conformite, nouvelle_demande_devis
    id: int
    notification_id: Optional[int] = None
    client_id: Optional[int] = None
    titre: str
    sous_titre: Optional[str] = None
    urgent: bool
    date: datetime
    view: str
    lu: bool = False


# ---------- Automatisation (emails + observabilite du scheduler) ----------

class EmailLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: Optional[int] = None
    devis_id: Optional[int] = None
    facture_id: Optional[int] = None
    type: str
    destinataire: Optional[str] = None
    objet: Optional[str] = None
    statut: str
    erreur: Optional[str] = None
    created_at: datetime


class AutomationStatutOut(BaseModel):
    email_configure: bool
    fournisseur: str
    intervalle_minutes: int
    derniere_execution: Optional[datetime] = None
    derniere_execution_resume: Optional[str] = None
    prochaine_execution_estimee: Optional[datetime] = None


# ---------- Contrats recurrents (maintenance/entretien -> facturation automatique) ----------

CONTRAT_FREQUENCES = {"mensuel", "trimestriel", "annuel"}
CONTRAT_STATUTS = {"actif", "suspendu", "resilie"}


class ContratCreate(BaseModel):
    client_id: int
    titre: str = Field(min_length=1)
    montant_ht: float = Field(gt=0)
    taux_tva: float = Field(default=10.0, ge=0, le=100)
    frequence: str
    prochaine_echeance: date

    @field_validator("titre")
    @classmethod
    def titre_non_vide(cls, v):
        if not v.strip():
            raise ValueError("titre ne peut pas être vide")
        return v.strip()

    @field_validator("frequence")
    @classmethod
    def frequence_valide(cls, v):
        if v not in CONTRAT_FREQUENCES:
            raise ValueError(f"frequence doit etre l'une de : {sorted(CONTRAT_FREQUENCES)}")
        return v


class ContratUpdate(BaseModel):
    titre: Optional[str] = Field(default=None, min_length=1)
    montant_ht: Optional[float] = Field(default=None, gt=0)
    taux_tva: Optional[float] = Field(default=None, ge=0, le=100)
    frequence: Optional[str] = None
    statut: Optional[str] = None
    prochaine_echeance: Optional[date] = None

    @field_validator("titre")
    @classmethod
    def titre_non_vide(cls, v):
        if v is not None and not v.strip():
            raise ValueError("titre ne peut pas être vide")
        return v.strip() if v is not None else v

    @field_validator("frequence")
    @classmethod
    def frequence_valide(cls, v):
        if v is not None and v not in CONTRAT_FREQUENCES:
            raise ValueError(f"frequence doit etre l'une de : {sorted(CONTRAT_FREQUENCES)}")
        return v

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v is not None and v not in CONTRAT_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(CONTRAT_STATUTS)}")
        return v


class ContratOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    client_nom: str
    titre: str
    montant_ht: float
    taux_tva: float
    frequence: str
    statut: str
    prochaine_echeance: date
    derniere_generation: Optional[date] = None
    nb_factures_generees: int = 0
    created_at: datetime


class GenerationContratOut(ContratOut):
    facture_id: int
    facture_numero: str
    facture_statut: str
    email_statut: str
    message: str
