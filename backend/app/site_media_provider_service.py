"""Acquire licensed V3 imagery during Admin generation, never public runtime."""

from __future__ import annotations

from datetime import timedelta
from hashlib import sha256
from io import BytesIO
import logging

from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.media_processing import MediaValidationError, process_site_image
from app.models import Artisan, SiteMediaLibrary, SiteMediaProviderCache, utcnow
from app.storage import get_storage
from generator.v3.media.providers import ImageAsset, ImageProvider, PexelsProvider, PixabayProvider, ProviderError
from generator.v3.media.query_profiles import build_query_profile

logger = logging.getLogger("suite_artisan.site_media.providers")


def _query_key(query: str, orientation: str, per_page: int) -> str:
    return sha256(f"{query.strip().lower()}|{orientation}|{per_page}".encode("utf-8")).hexdigest()


def _asset_from_dict(value: dict) -> ImageAsset | None:
    try:
        return ImageAsset(**value)
    except (TypeError, ValueError):
        return None


def _cached_search(db: Session, provider: ImageProvider, query: str, orientation: str, per_page: int) -> list[ImageAsset]:
    key = _query_key(query, orientation, per_page)
    cached = db.query(SiteMediaProviderCache).filter(
        SiteMediaProviderCache.provider == provider.name,
        SiteMediaProviderCache.query_key == key,
        SiteMediaProviderCache.expires_at > utcnow(),
    ).first()
    if cached:
        return [asset for item in cached.payload for asset in [_asset_from_dict(item)] if asset is not None]
    assets = provider.search(query, orientation=orientation, per_page=per_page)
    expires = utcnow() + timedelta(hours=settings.site_media_provider_cache_ttl_hours)
    stale = db.query(SiteMediaProviderCache).filter(SiteMediaProviderCache.provider == provider.name, SiteMediaProviderCache.query_key == key).first()
    payload = [asset.to_dict() for asset in assets]
    if stale:
        stale.payload = payload
        stale.expires_at = expires
    else:
        db.add(SiteMediaProviderCache(provider=provider.name, query_key=key, payload=payload, expires_at=expires))
    db.commit()
    return assets


def _search(db: Session, providers: list[ImageProvider], query: str, orientation: str, per_page: int) -> list[ImageAsset]:
    for provider in providers:
        if not provider.configured:
            continue
        try:
            assets = _cached_search(db, provider, query, orientation, per_page)
        except ProviderError as exc:
            logger.warning("Provider image %s indisponible: %s", provider.name, exc)
            continue
        if assets:
            return assets
    return []


def _format(content: bytes) -> tuple[str, str]:
    with Image.open(BytesIO(content)) as source:
        actual = str(source.format or "").upper()
    values = {"JPEG": ("asset.jpg", "image/jpeg"), "PNG": ("asset.png", "image/png"), "WEBP": ("asset.webp", "image/webp")}
    if actual not in values:
        raise MediaValidationError("Format provider non pris en charge")
    return values[actual]


def _provider_for(asset: ImageAsset) -> ImageProvider:
    if asset.provider == "pexels":
        return PexelsProvider(settings.pexels_api_key, timeout=settings.site_media_provider_timeout_seconds)
    return PixabayProvider(settings.pixabay_api_key, timeout=settings.site_media_provider_timeout_seconds)


def _persist_asset(db: Session, artisan: Artisan, asset: ImageAsset, query: str, usage: str) -> SiteMediaLibrary | None:
    existing = db.query(SiteMediaLibrary).filter(SiteMediaLibrary.provider == asset.provider, SiteMediaLibrary.provider_asset_id == asset.asset_id).first()
    if existing:
        usages = list(existing.usage_recommande or [])
        if usage not in usages:
            existing.usage_recommande = usages + [usage]
            db.commit()
        return existing
    try:
        content = _provider_for(asset).get_asset(asset)
        filename, mime = _format(content)
        processed = process_site_image(content, filename, mime)
    except (ProviderError, MediaValidationError, OSError) as exc:
        logger.warning("Asset %s/%s ignore: %s", asset.provider, asset.asset_id, exc)
        return None
    base = f"site-media-library/{asset.provider}/{asset.asset_id}"
    storage_key, thumbnail_key = f"{base}.webp", f"{base}-thumb.webp"
    storage = get_storage()
    storage.save(storage_key, processed.web)
    storage.save(thumbnail_key, processed.thumbnail)
    media = SiteMediaLibrary(
        media_id=f"{asset.provider}:{asset.asset_id}", metier=artisan.metier,
        sous_categorie=usage, storage_key=storage_key, thumbnail_key=thumbnail_key,
        mime_type=processed.mime_type, largeur=processed.width, hauteur=processed.height,
        orientation="paysage" if processed.width >= processed.height else "portrait",
        usage_recommande=[usage], licence=asset.licence, source_nom=asset.provider.title(),
        credit=asset.attribution, provider=asset.provider, provider_asset_id=asset.asset_id,
        photographer=asset.photographer, source_url=asset.source_url, provider_url=asset.provider_url,
        query=query, licence_metadata={"licence": asset.licence, "provider": asset.provider},
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def acquire_external_media(db: Session, artisan: Artisan, profile: dict) -> dict:
    """Populate the shared library just enough for one V3 profile."""
    providers: list[ImageProvider] = [
        PexelsProvider(settings.pexels_api_key, timeout=settings.site_media_provider_timeout_seconds),
        PixabayProvider(settings.pixabay_api_key, timeout=settings.site_media_provider_timeout_seconds),
    ]
    if not any(provider.configured for provider in providers):
        return {"status": "non_configure", "downloaded": 0}
    existing_count = db.query(SiteMediaLibrary).filter(SiteMediaLibrary.metier == artisan.metier, SiteMediaLibrary.actif.is_(True)).count()
    if existing_count >= 9:
        return {"status": "library_ready", "downloaded": 0}
    downloaded = 0
    seen: set[tuple[str, str]] = set()
    for usage, target in (("hero", 3), ("gallery", 6), ("about", 2)):
        query_profile = build_query_profile(artisan.metier, profile, usage)
        query = query_profile.queries[(artisan.id + len(usage)) % len(query_profile.queries)]
        assets = _search(db, providers, query, query_profile.orientation, settings.site_media_provider_results_per_query)
        added_for_usage = 0
        for asset in assets:
            key = (asset.provider, asset.asset_id)
            if key in seen:
                continue
            seen.add(key)
            if _persist_asset(db, artisan, asset, query, usage):
                downloaded += 1
                added_for_usage += 1
            if added_for_usage >= target:
                break
    return {"status": "ok" if downloaded else "no_result", "downloaded": downloaded}
