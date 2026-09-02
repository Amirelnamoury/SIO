from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


SITE_MEDIA_TYPES = {"logo", "photo"}
SITE_MEDIA_CATEGORIES = {"realisation", "chantier", "equipe", "atelier", "vehicule", "avant", "apres", "autre"}
SITE_MEDIA_USAGES = {"hero", "gallery", "about", "featured_project", "before_after"}


class SiteMediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int
    site_vitrine_id: Optional[int] = None
    type_media: str
    categorie: Optional[str] = None
    nom_original: str
    mime_type: str
    taille_octets: int
    largeur: Optional[int] = None
    hauteur: Optional[int] = None
    ordre: int
    actif: bool
    source: str
    alt_text: Optional[str] = None
    checksum: Optional[str] = None
    created_at: datetime
    content_url: str
    thumbnail_url: str


class SiteMediaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categorie: Optional[str] = None
    ordre: Optional[int] = Field(default=None, ge=0)
    actif: Optional[bool] = None
    alt_text: Optional[str] = None

    @field_validator("categorie")
    @classmethod
    def categorie_valide(cls, value: Optional[str]):
        if value is not None and value not in SITE_MEDIA_CATEGORIES:
            raise ValueError(f"categorie doit etre l'une de : {sorted(SITE_MEDIA_CATEGORIES)}")
        return value

    @field_validator("alt_text")
    @classmethod
    def alt_text_valide(cls, value: Optional[str]):
        if value is None:
            return None
        value = value.strip()
        if len(value) > 180:
            raise ValueError("Le texte alternatif ne peut pas depasser 180 caracteres")
        return value or None


class SiteMediaOrderIn(BaseModel):
    media_ids: list[int] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def ids_uniques(self):
        if len(self.media_ids) != len(set(self.media_ids)):
            raise ValueError("Chaque media ne peut apparaitre qu'une fois")
        return self


class SiteMediaSelectionOut(BaseModel):
    id: int
    usage: str
    position: int
    source: str
    site_media_id: Optional[int] = None
    library_media_id: Optional[int] = None
    media_id: Optional[str] = None
    categorie: Optional[str] = None
    credit: Optional[str] = None
    content_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    largeur: Optional[int] = None
    hauteur: Optional[int] = None
    alt_text: Optional[str] = None
    provider: Optional[str] = None
    photographer: Optional[str] = None
    source_url: Optional[str] = None


class SiteMediaProfileOut(BaseModel):
    selections: list[SiteMediaSelectionOut] = Field(default_factory=list)
    has_logo: bool = False
    artisan_photo_count: int = 0
    has_gallery: bool = False
    has_before_after: bool = False


class SiteMediaOverviewOut(BaseModel):
    logo: Optional[SiteMediaOut] = None
    photos: list[SiteMediaOut] = Field(default_factory=list)
    profile: SiteMediaProfileOut = Field(default_factory=SiteMediaProfileOut)
    max_photos: int
