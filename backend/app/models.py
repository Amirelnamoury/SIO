from datetime import datetime, timezone

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
    siret = Column(String, nullable=True)
    assurance_decennale_nom = Column(String, nullable=True)

    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status = Column(String, default="inactive")  # inactive, active, past_due, canceled

    created_at = Column(DateTime(timezone=True), default=utcnow)

    devis = relationship("Devis", back_populates="artisan", cascade="all, delete-orphan")
    chantiers = relationship("Chantier", back_populates="artisan", cascade="all, delete-orphan")
    conformites = relationship("ConformiteItem", back_populates="artisan", cascade="all, delete-orphan")


class Devis(Base):
    __tablename__ = "devis"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)

    client_nom = Column(String, nullable=False)
    client_email = Column(String, nullable=True)
    client_telephone = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    montant_ht = Column(Float, nullable=True)
    taux_tva = Column(Float, default=10.0)  # 10 = renovation, 20 = neuf

    # nouveau -> envoye -> relance_j3 -> relance_j7 -> relance_j15 -> signe / perdu
    statut = Column(String, default="nouveau", index=True)

    date_envoi = Column(DateTime(timezone=True), nullable=True)
    date_derniere_relance = Column(DateTime(timezone=True), nullable=True)
    nb_relances = Column(Integer, default=0)

    source = Column(String, default="manuel")  # manuel ou site_vitrine

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="devis")

    @property
    def montant_ttc(self):
        if self.montant_ht is None:
            return None
        return round(self.montant_ht * (1 + self.taux_tva / 100), 2)


class Chantier(Base):
    __tablename__ = "chantiers"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id"), nullable=False, index=True)

    titre = Column(String, nullable=False)
    client_nom = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    statut = Column(String, default="en_cours")  # en_cours, termine
    date_debut = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    artisan = relationship("Artisan", back_populates="chantiers")
    notes = relationship("ChantierNote", back_populates="chantier", cascade="all, delete-orphan")


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
