"""Lecture du media profile d'un site vitrine (logo, photos, selections)."""
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Artisan, SiteMedia, SiteMediaSelection, SiteVitrine
from app.site_media_service import media_to_dict


def selection_to_dict(selection, *, admin_artisan_id: int | None = None) -> dict:
    result = {
        "id": selection.id,
        "usage": selection.usage,
        "position": selection.position,
        "source": selection.source,
        "site_media_id": selection.site_media_id,
        "library_media_id": selection.library_media_id,
        "media_id": None,
        "categorie": None,
        "credit": None,
        "content_url": None,
        "thumbnail_url": None,
        "largeur": None,
        "hauteur": None,
        "alt_text": None,
        "provider": None,
        "photographer": None,
        "source_url": None,
    }
    if selection.source == "artisan" and selection.site_media is not None:
        media = media_to_dict(selection.site_media, admin_artisan_id=admin_artisan_id)
        result.update(
            media_id=str(selection.site_media.id),
            categorie=selection.site_media.categorie,
            content_url=media["content_url"],
            thumbnail_url=media["thumbnail_url"],
            largeur=selection.site_media.largeur,
            hauteur=selection.site_media.hauteur,
            alt_text=selection.site_media.alt_text,
        )
    elif selection.source == "bibliotheque" and selection.library_media is not None:
        library = selection.library_media
        prefix = "/site-media/library" if admin_artisan_id is None else f"/admin/api/artisans/{admin_artisan_id}/site/media/library"
        result.update(
            media_id=library.media_id,
            categorie=library.sous_categorie,
            credit=library.credit,
            provider=library.provider or library.source_nom,
            photographer=library.photographer,
            source_url=library.source_url,
            content_url=f"{prefix}/{library.id}/content?variant=web",
            thumbnail_url=f"{prefix}/{library.id}/content?variant=thumbnail",
            largeur=library.largeur,
            hauteur=library.hauteur,
        )
    return result


def media_profile_dict(db: Session, artisan: Artisan, site: SiteVitrine | None, *, admin: bool = False) -> dict:
    photos = db.query(SiteMedia).filter(
        SiteMedia.artisan_id == artisan.id,
        SiteMedia.type_media == "photo",
        SiteMedia.actif.is_(True),
    ).all()
    logo = db.query(SiteMedia).filter(
        SiteMedia.artisan_id == artisan.id,
        SiteMedia.type_media == "logo",
        SiteMedia.actif.is_(True),
    ).first()
    selections = [] if site is None else db.query(SiteMediaSelection).filter(
        SiteMediaSelection.site_vitrine_id == site.id
    ).order_by(SiteMediaSelection.usage, SiteMediaSelection.position).all()
    return {
        "selections": [selection_to_dict(s, admin_artisan_id=artisan.id if admin else None) for s in selections],
        "has_logo": logo is not None,
        "artisan_photo_count": len(photos),
        "has_gallery": any(s.usage == "gallery" and s.source != "fallback" for s in selections),
        "has_before_after": any(photo.categorie == "avant" for photo in photos) and any(photo.categorie == "apres" for photo in photos),
    }


def media_overview_dict(db: Session, artisan: Artisan, *, admin: bool = False) -> dict:
    medias = db.query(SiteMedia).filter(SiteMedia.artisan_id == artisan.id).order_by(
        SiteMedia.type_media, SiteMedia.ordre, SiteMedia.id
    ).all()
    logo = next((media for media in medias if media.type_media == "logo"), None)
    photos = [media for media in medias if media.type_media == "photo"]
    admin_id = artisan.id if admin else None
    return {
        "logo": media_to_dict(logo, admin_artisan_id=admin_id) if logo else None,
        "photos": [media_to_dict(media, admin_artisan_id=admin_id) for media in photos],
        "profile": media_profile_dict(db, artisan, artisan.site_vitrine, admin=admin),
        "max_photos": settings.site_media_max_photos,
    }
