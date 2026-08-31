"""Selection et persistance du media profile d'un site vitrine."""
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Artisan,
    SiteMedia,
    SiteMediaLibrary,
    SiteMediaSelection,
    SiteMediaUsage,
    SiteVitrine,
    utcnow,
)
from app.site_media_service import media_to_dict
from app.site_media_provider_service import acquire_external_media
from generator.media_selector import MEDIA_USAGES, select_site_media


def _artisan_media_payload(media: SiteMedia) -> dict:
    return {
        "id": media.id,
        "type_media": media.type_media,
        "categorie": media.categorie,
        "ordre": media.ordre,
        "actif": media.actif,
    }


def _library_media_payload(media: SiteMediaLibrary) -> dict:
    return {
        "id": media.id,
        "media_id": media.media_id,
        "metier": media.metier,
        "usage_recommande": media.usage_recommande or [],
        "actif": media.actif,
        "times_used": media.times_used,
    }


def ensure_media_profile(db: Session, artisan: Artisan, site: SiteVitrine) -> list[SiteMediaSelection]:
    existing = db.query(SiteMediaSelection).filter(
        SiteMediaSelection.site_vitrine_id == site.id
    ).order_by(SiteMediaSelection.usage, SiteMediaSelection.position).all()
    if existing:
        return existing

    if str((site.design_profile or {}).get("design_engine_version") or "").startswith("v3"):
        acquire_external_media(db, artisan, site.design_profile or {})

    artisan_media = db.query(SiteMedia).filter(
        SiteMedia.artisan_id == artisan.id,
        SiteMedia.type_media == "photo",
        SiteMedia.actif.is_(True),
    ).order_by(SiteMedia.ordre, SiteMedia.id).all()
    library_media = db.query(SiteMediaLibrary).filter(SiteMediaLibrary.actif.is_(True)).all()
    usage_history = db.query(SiteMediaUsage).order_by(SiteMediaUsage.selected_at.desc()).limit(settings.site_media_recent_usage_window).all()
    choices = select_site_media(
        {"artisan_id": artisan.id, "slug": artisan.slug, "metier": artisan.metier},
        [_artisan_media_payload(media) for media in artisan_media],
        [_library_media_payload(media) for media in library_media],
        [{"library_media_id": item.library_media_id, "usage": item.usage} for item in usage_history],
    )

    selections = []
    for choice in choices:
        selection = SiteMediaSelection(site_vitrine_id=site.id, **choice)
        db.add(selection)
        selections.append(selection)
        if choice["source"] == "bibliotheque":
            library = db.query(SiteMediaLibrary).filter(SiteMediaLibrary.id == choice["library_media_id"]).first()
            if library is not None:
                library.times_used = (library.times_used or 0) + 1
                library.last_used_at = utcnow()
            db.add(SiteMediaUsage(
                artisan_id=artisan.id,
                site_vitrine_id=site.id,
                library_media_id=choice["library_media_id"],
                usage=choice["usage"],
            ))
    db.commit()
    for selection in selections:
        db.refresh(selection)
    return selections


def set_media_selection(
    db: Session,
    artisan: Artisan,
    site: SiteVitrine,
    *,
    usage: str,
    position: int,
    source: str,
    site_media_id: int | None,
    library_media_id: int | None,
) -> SiteMediaSelection:
    if usage not in MEDIA_USAGES:
        raise ValueError("Usage media invalide")
    if source == "artisan":
        media = db.query(SiteMedia).filter(
            SiteMedia.id == site_media_id,
            SiteMedia.artisan_id == artisan.id,
            SiteMedia.type_media == "photo",
            SiteMedia.actif.is_(True),
        ).first()
        if media is None:
            raise LookupError("Photo artisan introuvable")
    elif source == "bibliotheque":
        media = db.query(SiteMediaLibrary).filter(
            SiteMediaLibrary.id == library_media_id,
            SiteMediaLibrary.actif.is_(True),
        ).first()
        if media is None:
            raise LookupError("Media de bibliotheque introuvable")
    elif source != "fallback":
        raise ValueError("Source media invalide")

    selection = db.query(SiteMediaSelection).filter(
        SiteMediaSelection.site_vitrine_id == site.id,
        SiteMediaSelection.usage == usage,
        SiteMediaSelection.position == position,
    ).first()
    if selection is None:
        selection = SiteMediaSelection(site_vitrine_id=site.id, usage=usage, position=position)
        db.add(selection)
    selection.source = source
    selection.site_media_id = site_media_id
    selection.library_media_id = library_media_id
    if source == "bibliotheque":
        db.add(SiteMediaUsage(
            artisan_id=artisan.id,
            site_vitrine_id=site.id,
            library_media_id=library_media_id,
            usage=usage,
        ))
    db.commit()
    db.refresh(selection)
    return selection


def remove_media_selection(db: Session, artisan: Artisan, site: SiteVitrine, selection_id: int) -> None:
    selection = db.query(SiteMediaSelection).filter(
        SiteMediaSelection.id == selection_id,
        SiteMediaSelection.site_vitrine_id == site.id,
    ).first()
    if selection is None or site.artisan_id != artisan.id:
        raise LookupError("Selection media introuvable")
    db.delete(selection)
    db.commit()


def selection_to_dict(selection: SiteMediaSelection, *, admin_artisan_id: int | None = None) -> dict:
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
