"""Stockage et remplacement atomique de la photo de profil d'un compte artisan."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.media_processing import process_site_image
from app.models import Artisan
from app.storage import get_storage


logger = logging.getLogger("suite_artisan.profile_photo")


def save_profile_photo(
    db: Session,
    artisan: Artisan,
    *,
    content: bytes,
    filename: str,
    declared_mime: str | None,
) -> Artisan:
    processed = process_site_image(content, filename, declared_mime)
    storage = get_storage()
    new_key = f"artisans/{artisan.id}/profile/{uuid.uuid4().hex}.webp"
    storage.save(new_key, processed.thumbnail)

    old_key = artisan.photo_profil_key
    artisan.photo_profil_key = new_key
    try:
        db.commit()
        db.refresh(artisan)
    except Exception:
        db.rollback()
        storage.delete(new_key)
        raise

    if old_key:
        try:
            storage.delete(old_key)
        except Exception:
            logger.exception("Impossible de supprimer l'ancienne photo de profil %s", old_key)
    return artisan


def delete_profile_photo(db: Session, artisan: Artisan) -> None:
    old_key = artisan.photo_profil_key
    if not old_key:
        raise LookupError("Photo de profil introuvable")
    artisan.photo_profil_key = None
    db.commit()
    try:
        get_storage().delete(old_key)
    except Exception:
        logger.exception("Impossible de supprimer la photo de profil %s", old_key)


def read_profile_photo(artisan: Artisan) -> bytes | None:
    if not artisan.photo_profil_key:
        return None
    return get_storage().read(artisan.photo_profil_key)
