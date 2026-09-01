"""Escaped content and provenance-aware media for Genome rendering."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit

from generator.design_genome.models import ComponentDefinition, SiteDNA


TRADE_LABELS = {
    "plombier": "Plomberie",
    "peintre": "Peinture",
    "macon": "Maçonnerie",
    "electricien": "Électricité",
    "menuisier": "Menuiserie",
    "renovateur": "Rénovation",
}


def media_source_class(payload: Mapping[str, Any]) -> str:
    source = str(payload.get("source") or "").lower()
    provider = str(payload.get("provider") or "").lower()
    if source in {"bibliotheque", "library"}:
        source = provider or "stock"
    if source in {"stock", "pexels", "pixabay"}:
        return "stock"
    return source


def media_semantic_role(payload: Mapping[str, Any]) -> str:
    usage = str(payload.get("role") or payload.get("usage") or "ambient")
    category = str(payload.get("categorie") or payload.get("category") or "")
    if media_source_class(payload) != "artisan":
        return usage
    if usage == "before_after" or category in {"avant", "apres"}:
        return "before_after"
    if usage in {"gallery", "featured_project"} and category in {"realisation", "chantier"}:
        return "artisan_project"
    return usage


def safe_url(value: object) -> str:
    text = str(value or "").strip()
    if not text or any(char in text for char in ('"', "'", "<", ">", "\n", "\r")):
        return ""
    parsed = urlsplit(text)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return ""
    if parsed.scheme and not parsed.netloc:
        return ""
    return html.escape(text, quote=True)


@dataclass(frozen=True)
class RenderMedia:
    id: str
    url: str
    role: str
    source: str
    alt: str
    width: int | None = None
    height: int | None = None
    credit: str = ""
    source_url: str = ""
    synthetic_fixture: bool = False

    @property
    def source_class(self) -> str:
        return self.source

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, synthetic_fixture: bool) -> "RenderMedia | None":
        url = safe_url(payload.get("content_url") or payload.get("url"))
        if not url:
            return None
        width = payload.get("largeur", payload.get("width"))
        height = payload.get("hauteur", payload.get("height"))
        return cls(
            id=str(payload.get("media_id") or payload.get("id") or url),
            url=url,
            role=media_semantic_role(payload),
            source=media_source_class(payload),
            alt=str(payload.get("alt_text") or payload.get("alt") or "").strip(),
            width=width if isinstance(width, int) and width > 0 else None,
            height=height if isinstance(height, int) and height > 0 else None,
            credit=str(payload.get("credit") or payload.get("photographer") or "").strip(),
            source_url=str(payload.get("source_url") or "").strip(),
            synthetic_fixture=synthetic_fixture,
        )


@dataclass(frozen=True)
class RenderContext:
    dna: SiteDNA
    content: Mapping[str, Any]
    facts: Mapping[str, Any]
    media: tuple[RenderMedia, ...]
    api_base_url: str
    lab_mode: bool = False
    synthetic_fixture: bool = False

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        dna: SiteDNA,
        api_base_url: str = "",
        *,
        lab_mode: bool = False,
    ) -> "RenderContext":
        synthetic = bool(payload.get("synthetic_fixture"))
        if synthetic and not lab_mode:
            raise ValueError("Synthetic fixtures are restricted to the visual lab")
        was_escaped = bool(payload.get("_content_escaped"))

        def plain(value: object) -> str:
            text = str(value or "").strip()
            return html.unescape(text) if was_escaped else text

        content: dict[str, Any] = {
            key: plain(payload.get(key))
            for key in (
                "nom_entreprise", "metier", "slug", "ville", "code_postal",
                "telephone", "email", "adresse", "siret", "tagline", "about",
                "assurance_decennale_nom", "url_publique",
            )
        }
        content["services"] = tuple(plain(item) for item in payload.get("services") or () if plain(item))
        content["process_steps"] = tuple(plain(item) for item in payload.get("process_steps") or () if plain(item))

        def normalize_fact(value: Any) -> Any:
            if isinstance(value, Mapping):
                return {key: normalize_fact(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return tuple(normalize_fact(item) for item in value)
            return plain(value) if isinstance(value, str) else value

        raw_facts = normalize_fact(dict(payload.get("facts") or {}))
        if content["telephone"]:
            raw_facts.setdefault("phone", content["telephone"])
        if content["email"]:
            raw_facts.setdefault("email", content["email"])
        if content["assurance_decennale_nom"]:
            raw_facts.setdefault("insurance", content["assurance_decennale_nom"])
        if content["process_steps"]:
            raw_facts.setdefault("process", content["process_steps"])
        for key, source in (("reviews", "avis"), ("statistics", "stats"), ("certifications", "certifications")):
            values = normalize_fact(payload.get(source) or raw_facts.get(key) or ())
            raw_facts[key] = tuple(values) if isinstance(values, (list, tuple)) else values

        media_items = []
        for selected in payload.get("selected_media") or payload.get("media") or ():
            if not isinstance(selected, Mapping) or selected.get("source") == "fallback":
                continue
            item = RenderMedia.from_mapping(selected, synthetic_fixture=synthetic)
            if item:
                media_items.append(item)
        logo = payload.get("logo")
        if isinstance(logo, Mapping):
            logo_item = RenderMedia.from_mapping({**logo, "role": "logo"}, synthetic_fixture=synthetic)
            if logo_item:
                media_items.append(logo_item)

        return cls(
            dna=dna,
            content=content,
            facts=raw_facts,
            media=tuple(media_items),
            api_base_url=api_base_url.rstrip("/"),
            lab_mode=lab_mode,
            synthetic_fixture=synthetic,
        )

    def plain(self, key: str) -> str:
        return str(self.content.get(key) or "")

    def text(self, key: str) -> str:
        return html.escape(self.plain(key), quote=True)

    def list(self, key: str) -> tuple[Any, ...]:
        value = self.content.get(key) or ()
        return tuple(value) if isinstance(value, (list, tuple)) else ()

    def fact(self, key: str) -> Any:
        return self.facts.get(key)

    @property
    def business_name(self) -> str:
        return self.text("nom_entreprise")

    @property
    def trade_label(self) -> str:
        return html.escape(TRADE_LABELS.get(self.plain("metier"), self.plain("metier") or "Artisan"), quote=True)

    @property
    def location(self) -> str:
        value = " ".join(item for item in (self.plain("ville"), self.plain("code_postal")) if item)
        return html.escape(value, quote=True)

    @property
    def phone_href(self) -> str:
        return "".join(char for char in self.plain("telephone") if char.isdigit() or char == "+")

    @property
    def has_lead_flow(self) -> bool:
        return bool(self.plain("slug") and self.api_base_url and not self.lab_mode)

    def media_for(self, component: ComponentDefinition, *, limit: int | None = None) -> tuple[RenderMedia, ...]:
        required_roles = set(component.required_media) | set(component.required_any_media)
        allowed_sources = set(component.allowed_media_sources)
        section_roles = {component.category, "ambient"}
        if component.category == "hero":
            section_roles |= {"hero", "landscape", "portrait"}
        elif component.category == "gallery":
            section_roles |= {"gallery", "landscape", "portrait", "artisan_project", "before_after"}
        elif component.category == "about":
            section_roles |= {"about", "portrait"}

        values: list[RenderMedia] = []
        seen: set[str] = set()
        for item in self.media:
            if item.id in seen or item.role == "logo":
                continue
            if item.source_class not in allowed_sources:
                continue
            if "artisan_project" in required_roles and not (item.role == "artisan_project" and item.source_class == "artisan"):
                continue
            if "before_after" in required_roles and not (item.role == "before_after" and item.source_class == "artisan"):
                continue
            if required_roles and not ({item.role, f"{item.source_class}_photo"} & required_roles):
                if not ("stock_photo" in required_roles and item.source_class == "stock"):
                    continue
            elif not required_roles and item.role not in section_roles:
                continue
            seen.add(item.id)
            values.append(item)
        return tuple(values[:limit] if limit else values)

    def logo(self) -> RenderMedia | None:
        return next((item for item in self.media if item.role == "logo"), None)
