"""Persistance des medias site et orchestration du Storage abstrait."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.media_processing import process_site_image
from app.models import Artisan, SiteMedia, SiteMediaSelection
from app.site_media_schemas import SITE_MEDIA_CATEGORIES
from app.storage import get_storage


logger = logging.getLogger("suite_artisan.site_media")


def media_storage_keys(artisan_id: int, type_media: str, identifier: str | None = None) -> tuple[str, str]:
    if artisan_id <= 0 or type_media not in ("logo", "photo"):
        raise ValueError("Parametres de cle media invalides")
    identifier = identifier or uuid.uuid4().hex
    folder = "logo" if type_media == "logo" else "photos"
    prefix = f"artisans/{artisan_id}/site/{folder}/{identifier}"
    return f"{prefix}.webp", f"{prefix}-thumb.webp"


def _delete_storage_keys(keys: tuple[str, str]) -> None:
    storage = get_storage()
    for key in keys:
        try:
            storage.delete(key)
        except Exception:
            logger.exception("Impossible de supprimer la cle media orpheline %s", key)


def save_uploaded_media(
    db: Session,
    artisan: Artisan,
    *,
    content: bytes,
    filename: str,
    declared_mime: str | None,
    type_media: str,
    categorie: str | None = None,
    alt_text: str | None = None,
) -> SiteMedia:
    if type_media not in ("logo", "photo"):
        raise ValueError("Type de media invalide")
    if type_media == "photo" and categorie not in SITE_MEDIA_CATEGORIES:
        raise ValueError("Categorie photo invalide")
    if alt_text is not None:
        alt_text = alt_text.strip() or None
        if alt_text and len(alt_text) > 180:
            raise ValueError("Le texte alternatif ne peut pas depasser 180 caracteres")
    if type_media == "photo":
        count = db.query(SiteMedia).filter(SiteMedia.artisan_id == artisan.id, SiteMedia.type_media == "photo").count()
        if count >= settings.site_media_max_photos:
            raise ValueError(f"Limite atteinte : {settings.site_media_max_photos} photos maximum")
    processed = process_site_image(content, filename, declared_mime)
    storage_key, thumbnail_key = media_storage_keys(artisan.id, type_media)
    storage = get_storage()
    storage.save(storage_key, processed.web)
    try:
        storage.save(thumbnail_key, processed.thumbnail)
    except Exception:
        storage.delete(storage_key)
        raise

    old_logo_keys: tuple[str, str] | None = None
    if type_media == "logo":
        old_logo = db.query(SiteMedia).filter(SiteMedia.artisan_id == artisan.id, SiteMedia.type_media == "logo").first()
        if old_logo is not None:
            old_logo_keys = (old_logo.storage_key, old_logo.thumbnail_key)
            db.delete(old_logo)
    next_order = 0
    if type_media == "photo":
        max_order = db.query(func.max(SiteMedia.ordre)).filter(
            SiteMedia.artisan_id == artisan.id, SiteMedia.type_media == "photo"
        ).scalar()
        next_order = 0 if max_order is None else max_order + 1
    media = SiteMedia(
        artisan_id=artisan.id,
        site_vitrine_id=artisan.site_vitrine.id if artisan.site_vitrine else None,
        type_media=type_media,
        categorie=categorie if type_media == "photo" else None,
        storage_key=storage_key,
        thumbnail_key=thumbnail_key,
        nom_original=filename,
        mime_type=processed.mime_type,
        taille_octets=len(processed.web),
        largeur=processed.width,
        hauteur=processed.height,
        ordre=next_order,
        actif=True,
        source="artisan",
        alt_text=alt_text,
        checksum=processed.checksum,
    )
    db.add(media)
    try:
        db.commit()
        db.refresh(media)
    except Exception:
        db.rollback()
        storage.delete(storage_key)
        storage.delete(thumbnail_key)
        raise
    if old_logo_keys is not None:
        _delete_storage_keys(old_logo_keys)
    return media


def delete_site_media(db: Session, media: SiteMedia) -> None:
    keys = (media.storage_key, media.thumbnail_key)
    db.query(SiteMediaSelection).filter(SiteMediaSelection.site_media_id == media.id).delete(synchronize_session=False)
    db.delete(media)
    db.commit()
    _delete_storage_keys(keys)


def reorder_photos(db: Session, artisan_id: int, media_ids: list[int]) -> list[SiteMedia]:
    all_photos = db.query(SiteMedia).filter(
        SiteMedia.artisan_id == artisan_id,
        SiteMedia.type_media == "photo",
    ).all()
    if {media.id for media in all_photos} != set(media_ids):
        raise LookupError("La liste doit contenir exactement toutes les photos de l'artisan")
    by_id = {media.id: media for media in all_photos}
    for position, media_id in enumerate(media_ids):
        by_id[media_id].ordre = position
    db.commit()
    return [by_id[media_id] for media_id in media_ids]


def media_to_dict(media: SiteMedia, *, admin_artisan_id: int | None = None) -> dict:
    if admin_artisan_id is None:
        base = f"/site-media/{media.id}/content"
    else:
        base = f"/admin/api/artisans/{admin_artisan_id}/site/media/{media.id}/content"
    return {
        "id": media.id,
        "artisan_id": media.artisan_id,
        "site_vitrine_id": media.site_vitrine_id,
        "type_media": media.type_media,
        "categorie": media.categorie,
        "nom_original": media.nom_original,
        "mime_type": media.mime_type,
        "taille_octets": media.taille_octets,
        "largeur": media.largeur,
        "hauteur": media.hauteur,
        "ordre": media.ordre,
        "actif": media.actif,
        "source": media.source,
        "alt_text": media.alt_text,
        "checksum": media.checksum,
        "created_at": media.created_at,
        "content_url": f"{base}?variant=web",
        "thumbnail_url": f"{base}?variant=thumbnail",
    }
