from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

METIERS_VALIDES = {"plombier", "electricien", "macon", "peintre", "general"}
DEVIS_STATUTS = {"nouveau", "envoye", "relance_j3", "relance_j7", "relance_j15", "signe", "perdu"}
CHANTIER_PHASES = {"avant", "pendant", "apres"}
CONFORMITE_TYPES = {"assurance_decennale", "qualibat", "rge", "autre"}


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
    slug: Optional[str] = None  # auto-genere depuis nom_entreprise si absent

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


class ArtisanOut(BaseModel):
    """Schema de SORTIE : ne contient jamais password_hash. Ne jamais renvoyer
    le modele SQLAlchemy Artisan directement dans une reponse JSON."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    nom_entreprise: str
    metier: str
    email: EmailStr
    telephone: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    siret: Optional[str] = None
    assurance_decennale_nom: Optional[str] = None
    subscription_status: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    artisan: ArtisanOut


# ---------- Devis ----------

class DevisCreate(BaseModel):
    client_nom: str
    client_email: Optional[EmailStr] = None
    client_telephone: Optional[str] = None
    description: Optional[str] = None
    montant_ht: Optional[float] = None
    taux_tva: float = 10.0

    @field_validator("taux_tva")
    @classmethod
    def tva_valide(cls, v):
        if v not in (10.0, 20.0):
            raise ValueError("taux_tva doit etre 10 (renovation) ou 20 (neuf)")
        return v


class DevisUpdate(BaseModel):
    client_nom: Optional[str] = None
    client_email: Optional[EmailStr] = None
    client_telephone: Optional[str] = None
    description: Optional[str] = None
    montant_ht: Optional[float] = None
    taux_tva: Optional[float] = None
    statut: Optional[str] = None

    @field_validator("statut")
    @classmethod
    def statut_valide(cls, v):
        if v is not None and v not in DEVIS_STATUTS:
            raise ValueError(f"statut doit etre l'un de : {sorted(DEVIS_STATUTS)}")
        return v


class DevisPublicCreate(BaseModel):
    """Ce que le formulaire du site vitrine envoie, sans authentification."""

    client_nom: str
    client_email: Optional[EmailStr] = None
    client_telephone: Optional[str] = None
    description: Optional[str] = None


class DevisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    client_nom: str
    client_email: Optional[str] = None
    client_telephone: Optional[str] = None
    description: Optional[str] = None
    montant_ht: Optional[float] = None
    taux_tva: float
    montant_ttc: Optional[float] = None
    statut: str
    date_envoi: Optional[datetime] = None
    date_derniere_relance: Optional[datetime] = None
    nb_relances: int
    source: str
    created_at: datetime


# ---------- Chantiers ----------

class ChantierCreate(BaseModel):
    titre: str
    client_nom: Optional[str] = None
    adresse: Optional[str] = None
    date_debut: Optional[date] = None


class ChantierUpdate(BaseModel):
    titre: Optional[str] = None
    client_nom: Optional[str] = None
    adresse: Optional[str] = None
    statut: Optional[str] = None
    date_debut: Optional[date] = None


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
    titre: str
    client_nom: Optional[str] = None
    adresse: Optional[str] = None
    statut: str
    date_debut: Optional[date] = None
    created_at: datetime
    notes: list[ChantierNoteOut] = []


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    type: str
    libelle: str
    date_expiration: date
    document_url: Optional[str] = None
    created_at: datetime
    alerte: bool = False
    jours_restants: Optional[int] = None
