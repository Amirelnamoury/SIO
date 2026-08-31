"""Pexels/Pixabay adapters with normalized failures and no secret logging."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any

import requests


class ProviderError(RuntimeError):
    pass


class ProviderRateLimited(ProviderError):
    pass


class ProviderUnavailable(ProviderError):
    pass


@dataclass(frozen=True)
class ImageAsset:
    provider: str
    asset_id: str
    download_url: str
    source_url: str
    provider_url: str
    photographer: str | None
    width: int
    height: int
    licence: str
    attribution: str

    def to_dict(self) -> dict:
        return asdict(self)


class ImageProvider(ABC):
    name = "provider"

    def __init__(self, api_key: str | None, *, session: requests.Session | None = None, timeout: float = 8.0):
        self.api_key = (api_key or "").strip()
        self.session = session or requests.Session()
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def healthcheck(self) -> bool:
        return self.configured

    @abstractmethod
    def search(self, query: str, *, orientation: str = "landscape", per_page: int = 12) -> list[ImageAsset]:
        raise NotImplementedError

    def get_asset(self, asset: ImageAsset) -> bytes:
        try:
            response = self.session.get(asset.download_url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ProviderUnavailable(f"{self.name} download unavailable") from exc
        if response.status_code == 429:
            raise ProviderRateLimited(f"{self.name} rate limited")
        if response.status_code != 200:
            raise ProviderUnavailable(f"{self.name} download HTTP {response.status_code}")
        return response.content

    def attribution(self, asset: ImageAsset) -> dict:
        return {"source": asset.provider, "photographer": asset.photographer, "source_url": asset.source_url, "text": asset.attribution}

    @staticmethod
    def _json(response, provider: str) -> dict[str, Any]:
        if response.status_code == 429:
            raise ProviderRateLimited(f"{provider} rate limited")
        if response.status_code != 200:
            raise ProviderUnavailable(f"{provider} HTTP {response.status_code}")
        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            raise ProviderUnavailable(f"{provider} invalid JSON") from exc
        if not isinstance(payload, dict):
            raise ProviderUnavailable(f"{provider} invalid response")
        return payload


class PexelsProvider(ImageProvider):
    name = "pexels"
    api_url = "https://api.pexels.com/v1/search"

    def search(self, query: str, *, orientation: str = "landscape", per_page: int = 12) -> list[ImageAsset]:
        if not self.configured:
            return []
        try:
            response = self.session.get(self.api_url, headers={"Authorization": self.api_key}, params={"query": query, "orientation": orientation, "per_page": per_page}, timeout=self.timeout)
        except requests.Timeout as exc:
            raise ProviderUnavailable("pexels timeout") from exc
        except requests.RequestException as exc:
            raise ProviderUnavailable("pexels unavailable") from exc
        payload = self._json(response, self.name)
        photos = payload.get("photos")
        if not isinstance(photos, list):
            raise ProviderUnavailable("pexels invalid photos payload")
        assets = []
        for item in photos:
            try:
                src = item["src"]
                assets.append(ImageAsset("pexels", str(item["id"]), src.get("large2x") or src["large"], item["url"], "https://www.pexels.com", item.get("photographer"), int(item["width"]), int(item["height"]), "Pexels License", f'Photo: {item.get("photographer") or "Pexels"} / Pexels'))
            except (KeyError, TypeError, ValueError):
                continue
        return assets


class PixabayProvider(ImageProvider):
    name = "pixabay"
    api_url = "https://pixabay.com/api/"

    def search(self, query: str, *, orientation: str = "horizontal", per_page: int = 12) -> list[ImageAsset]:
        if not self.configured:
            return []
        orientation = "horizontal" if orientation == "landscape" else orientation
        try:
            response = self.session.get(self.api_url, params={"key": self.api_key, "q": query, "orientation": orientation, "per_page": max(3, per_page), "image_type": "photo", "safesearch": "true"}, timeout=self.timeout)
        except requests.Timeout as exc:
            raise ProviderUnavailable("pixabay timeout") from exc
        except requests.RequestException as exc:
            raise ProviderUnavailable("pixabay unavailable") from exc
        payload = self._json(response, self.name)
        hits = payload.get("hits")
        if not isinstance(hits, list):
            raise ProviderUnavailable("pixabay invalid hits payload")
        assets = []
        for item in hits:
            try:
                assets.append(ImageAsset("pixabay", str(item["id"]), item.get("largeImageURL") or item["webformatURL"], item["pageURL"], "https://pixabay.com", item.get("user"), int(item.get("imageWidth") or 0), int(item.get("imageHeight") or 0), "Pixabay Content License", f'Image: {item.get("user") or "Pixabay"} / Pixabay'))
            except (KeyError, TypeError, ValueError):
                continue
        return assets


def search_with_fallback(providers: list[ImageProvider], query: str, *, orientation: str = "landscape", per_page: int = 12) -> tuple[list[ImageAsset], list[str]]:
    failures = []
    for provider in providers:
        try:
            assets = provider.search(query, orientation=orientation, per_page=per_page)
            if assets:
                return assets, failures
        except ProviderError as exc:
            failures.append(f"{provider.name}: {exc}")
    return [], failures
