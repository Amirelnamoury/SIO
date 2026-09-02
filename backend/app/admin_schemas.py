from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

from app.schemas import METIERS_VALIDES
from app.site_media_schemas import SiteMediaOverviewOut, SiteMediaProfileOut


SITE_STATUTS = {"brouillon", "genere", "pret", "publie"}


class AdminLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class AdminIdentityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nom: str


class AdminTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminIdentityOut


class AdminDashboardOut(BaseModel):
    artisans_total: int
    artisans_actifs: int
    plans: dict[str, int]
    sites_total: int
    sites_brouillon: int
    sites_generes: int
    sites_prets: int
    sites_publies: int


class SiteStat(BaseModel):
    valeur: str
    label: str

    @field_validator("valeur", "label")
    @classmethod
    def texte_court(cls, value: str):
        value = value.strip()
        if not value or len(value) > 80:
            raise ValueError("Chaque statistique doit contenir un texte de 1 a 80 caracteres")
        return value


class SiteVitrineUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domaine: Optional[str] = None
    url_publique: Optional[HttpUrl] = None
    tagline: Optional[str] = None
    services: Optional[list[str]] = None
    stats: Optional[list[SiteStat]] = None

    @field_validator("domaine")
    @classmethod
    def domaine_valide(cls, value: Optional[str]):
        if value is None:
            return None
        value = value.strip().lower().rstrip(".")
        if not value:
            return None
        if len(value) > 253 or "/" in value or ":" in value or " " in value or "." not in value:
            raise ValueError("Domaine invalide (exemple attendu : artisan.fr)")
        labels = value.split(".")
        if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") or not label.replace("-", "").isalnum() for label in labels):
            raise ValueError("Domaine invalide")
        return value

    @field_validator("tagline")
    @classmethod
    def tagline_valide(cls, value: Optional[str]):
        if value is None:
            return None
        value = value.strip()
        if len(value) > 180:
            raise ValueError("La tagline ne peut pas depasser 180 caracteres")
        return value or None

    @field_validator("services")
    @classmethod
    def services_valides(cls, value: Optional[list[str]]):
        if value is None:
            return None
        if not 1 <= len(value) <= 12:
            raise ValueError("Le site doit contenir entre 1 et 12 prestations")
        nettoyes = [service.strip() for service in value]
        if any(not service or len(service) > 120 for service in nettoyes):
            raise ValueError("Chaque prestation doit contenir entre 1 et 120 caracteres")
        return nettoyes

    @field_validator("stats")
    @classmethod
    def stats_valides(cls, value: Optional[list[SiteStat]]):
        if value is not None and len(value) > 4:
            raise ValueError("Le site accepte au maximum 4 statistiques")
        return value

class AdminArtisanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom_entreprise: Optional[str] = None
    metier: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    adresse: Optional[str] = None
    siret: Optional[str] = None
    assurance_decennale_nom: Optional[str] = None

    @field_validator("nom_entreprise")
    @classmethod
    def nom_valide(cls, value: Optional[str]):
        if value is None:
            return None
        value = value.strip()
        if not value or len(value) > 160:
            raise ValueError("Le nom de l'entreprise est invalide")
        return value

    @field_validator("metier")
    @classmethod
    def metier_valide(cls, value: Optional[str]):
        if value is not None and value not in METIERS_VALIDES:
            raise ValueError(f"metier doit etre l'un de : {sorted(METIERS_VALIDES)}")
        return value


class SiteVitrineOut(BaseModel):
    id: Optional[int] = None
    artisan_id: int
    statut: str
    domaine: Optional[str] = None
    url_publique: Optional[str] = None
    config: dict
    media_profile: SiteMediaProfileOut = Field(default_factory=SiteMediaProfileOut)
    date_generation: Optional[datetime] = None
    date_publication: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    content_warnings: list[str] = Field(default_factory=list)


class AdminArtisanListItem(BaseModel):
    id: int
    nom_entreprise: str
    metier: str
    ville: Optional[str] = None
    email: EmailStr
    plan: str
    subscription_status: str
    slug: str
    site_statut: str
    domaine: Optional[str] = None
    url_publique: Optional[str] = None
    created_at: datetime
    # Signal "a traiter" (refonte Admin) - calcule a partir de donnees reelles
    # uniquement (aucun etat invente) : voir _query_artisans dans admin.py.
    media_manquant: bool = False


class AdminArtisanDetail(BaseModel):
    id: int
    nom_entreprise: str
    metier: str
    email: EmailStr
    telephone: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    adresse: Optional[str] = None
    siret: Optional[str] = None
    assurance_decennale_nom: Optional[str] = None
    plan: str
    subscription_status: str
    slug: str
    created_at: datetime
    clients_total: int
    devis_total: int
    factures_total: int
    site: SiteVitrineOut
    media: SiteMediaOverviewOut


class AdminArtisanListOut(BaseModel):
    items: list[AdminArtisanListItem]
    total: int


class AdminSiteListOut(BaseModel):
    items: list[AdminArtisanListItem]
    total: int
