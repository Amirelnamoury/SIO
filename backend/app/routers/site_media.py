from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_artisan
from app.media_processing import MediaValidationError
from app.models import Artisan, SiteMedia, SiteMediaLibrary, SiteMediaSelection
from app.site_media_schemas import (
    SITE_MEDIA_CATEGORIES,
    SiteMediaOrderIn,
    SiteMediaOut,
    SiteMediaOverviewOut,
    SiteMediaUpdate,
)
from app.site_media_selection_service import media_overview_dict
from app.site_media_service import delete_site_media, media_to_dict, reorder_photos, save_uploaded_media
from app.storage import get_storage


router = APIRouter(prefix="/site-media", tags=["site-media"])


def _media_or_404(db: Session, artisan_id: int, media_id: int) -> SiteMedia:
    media = db.query(SiteMedia).filter(SiteMedia.id == media_id, SiteMedia.artisan_id == artisan_id).first()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media introuvable")
    return media


async def _read_upload(file: UploadFile) -> tuple[bytes, str]:
    max_bytes = settings.site_media_max_upload_mo * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image trop volumineuse (maximum {settings.site_media_max_upload_mo} Mo)",
        )
    filename = (file.filename or "image").replace("\\", "/").split("/")[-1][:255]
    return content, filename


def _save_or_http_error(db: Session, artisan: Artisan, **kwargs) -> SiteMedia:
    try:
        return save_uploaded_media(db, artisan, **kwargs)
    except MediaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


def _image_response(content: bytes, *, cache_control: str = "private, max-age=300") -> Response:
    return Response(
        content=content,
        media_type="image/webp",
        headers={"Cache-Control": cache_control, "X-Content-Type-Options": "nosniff"},
    )


@router.get("", response_model=SiteMediaOverviewOut)
def list_site_media(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    return media_overview_dict(db, artisan)


@router.post("/logo", response_model=SiteMediaOut, status_code=status.HTTP_201_CREATED)
async def upload_logo(
    file: UploadFile = File(...),
    alt_text: str | None = Form(None),
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    content, filename = await _read_upload(file)
    media = _save_or_http_error(
        db,
        artisan,
        content=content,
        filename=filename,
        declared_mime=file.content_type,
        type_media="logo",
        alt_text=alt_text,
    )
    return media_to_dict(media)


@router.delete("/logo", status_code=status.HTTP_204_NO_CONTENT)
def delete_logo(
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    media = db.query(SiteMedia).filter(
        SiteMedia.artisan_id == artisan.id, SiteMedia.type_media == "logo"
    ).first()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Logo introuvable")
    delete_site_media(db, media)


@router.post("/photos", response_model=SiteMediaOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    categorie: str = Form("autre"),
    alt_text: str | None = Form(None),
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    if categorie not in SITE_MEDIA_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Categorie photo invalide")
    content, filename = await _read_upload(file)
    media = _save_or_http_error(
        db,
        artisan,
        content=content,
        filename=filename,
        declared_mime=file.content_type,
        type_media="photo",
        categorie=categorie,
        alt_text=alt_text,
    )
    return media_to_dict(media)


@router.put("/photos/order", response_model=list[SiteMediaOut])
def order_photos(
    payload: SiteMediaOrderIn,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    try:
        photos = reorder_photos(db, artisan.id, payload.media_ids)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [media_to_dict(media) for media in photos]


@router.patch("/{media_id}", response_model=SiteMediaOut)
def update_media(
    media_id: int,
    payload: SiteMediaUpdate,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    media = _media_or_404(db, artisan.id, media_id)
    updates = payload.model_dump(exclude_unset=True)
    if media.type_media == "logo" and "categorie" in updates:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Un logo n'a pas de categorie photo")
    if media.type_media == "photo" and updates.get("categorie", "autre") is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Une photo doit conserver une categorie")
    for field, value in updates.items():
        setattr(media, field, value)
    if updates.get("actif") is False:
        db.query(SiteMediaSelection).filter(SiteMediaSelection.site_media_id == media.id).delete(synchronize_session=False)
    db.commit()
    db.refresh(media)
    return media_to_dict(media)


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    media = _media_or_404(db, artisan.id, media_id)
    delete_site_media(db, media)


@router.get("/{media_id}/content")
def get_media_content(
    media_id: int,
    variant: str = Query(default="web", pattern="^(web|thumbnail)$"),
    db: Session = Depends(get_db),
    artisan: Artisan = Depends(get_current_artisan),
):
    media = _media_or_404(db, artisan.id, media_id)
    key = media.thumbnail_key if variant == "thumbnail" else media.storage_key
    content = get_storage().read(key)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier media introuvable")
    return _image_response(content)


@router.get("/library/{library_media_id}/content")
def get_library_media_content(
    library_media_id: int,
    variant: str = Query(default="web", pattern="^(web|thumbnail)$"),
    db: Session = Depends(get_db),
    _artisan: Artisan = Depends(get_current_artisan),
):
    media = db.query(SiteMediaLibrary).filter(
        SiteMediaLibrary.id == library_media_id, SiteMediaLibrary.actif.is_(True)
    ).first()
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media de bibliotheque introuvable")
    key = media.thumbnail_key if variant == "thumbnail" and media.thumbnail_key else media.storage_key
    content = get_storage().read(key)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier media introuvable")
    return _image_response(content)
