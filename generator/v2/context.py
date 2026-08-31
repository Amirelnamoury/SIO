"""Validated rendering context for the V2 site generator."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from ..design_registry import (
    ABOUT_VARIANTS,
    CTA_VARIANTS,
    DESIGN_ENGINE_VERSION,
    DESIGN_FAMILIES,
    FONT_PAIR_IDS,
    FOOTER_VARIANTS,
    GALLERY_VARIANTS,
    HEADER_VARIANTS,
    HERO_VARIANTS,
    IMAGE_TREATMENTS,
    PALETTE_SLOTS,
    RADIUS_STYLES,
    REVIEWS_VARIANTS,
    SERVICES_VARIANTS,
    SPACING_STYLES,
)
from ..themes import get_theme


PROFILE_VALUES = {
    "design_family": set(DESIGN_FAMILIES),
    "header_variant": set(HEADER_VARIANTS),
    "hero_variant": set(HERO_VARIANTS),
    "services_variant": set(SERVICES_VARIANTS),
    "gallery_variant": set(GALLERY_VARIANTS),
    "about_variant": set(ABOUT_VARIANTS),
    "reviews_variant": set(REVIEWS_VARIANTS),
    "cta_variant": set(CTA_VARIANTS),
    "footer_variant": set(FOOTER_VARIANTS),
    "palette": set(PALETTE_SLOTS),
    "font_pair": set(FONT_PAIR_IDS),
    "radius_style": set(RADIUS_STYLES),
    "spacing_style": set(SPACING_STYLES),
    "image_treatment": set(IMAGE_TREATMENTS),
}


def _major(version: object) -> int | None:
    if not isinstance(version, str) or not version.startswith("v"):
        return None
    try:
        return int(version[1:].split(".", 1)[0])
    except ValueError:
        return None


def is_compatible_design_profile(profile: object) -> bool:
    """Central compatibility gate; renderers never compare versions themselves."""
    if not isinstance(profile, dict) or _major(profile.get("design_engine_version")) != _major(DESIGN_ENGINE_VERSION):
        return False
    if any(profile.get(key) not in values for key, values in PROFILE_VALUES.items()):
        return False
    order = profile.get("section_order")
    return isinstance(order, list) and bool(order) and all(isinstance(item, str) for item in order)


def safe_url(value: object) -> str:
    value = str(value or "").strip()
    if not value or any(char in value for char in ('"', "'", "<", ">", "\n", "\r")):
        return ""
    parsed = urlsplit(value)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return ""
    if not parsed.scheme and parsed.netloc:
        return ""
    if not parsed.scheme and not value.startswith("/"):
        return ""
    return html.escape(value, quote=True)


@dataclass(frozen=True)
class SiteContext:
    data: dict[str, Any]
    profile: dict[str, Any]
    plain: dict[str, Any]
    media: dict[str, tuple[dict[str, Any], ...]]
    logo: dict[str, Any] | None
    theme: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SiteContext":
        profile = payload.get("design_profile")
        if not is_compatible_design_profile(profile):
            raise ValueError("Profil de design V2 incompatible")

        was_escaped = bool(payload.get("_content_escaped"))

        def plain_value(value: object) -> str:
            text = str(value or "").strip()
            return html.unescape(text) if was_escaped else text

        plain = {
            key: plain_value(payload.get(key))
            for key in (
                "nom_entreprise", "metier", "slug", "ville", "code_postal",
                "telephone", "email", "adresse", "siret",
                "assurance_decennale_nom", "tagline", "url_publique",
            )
        }
        plain["services"] = [plain_value(item) for item in payload.get("services") or [] if plain_value(item)]
        plain["stats"] = [
            {"valeur": plain_value(item.get("valeur")), "label": plain_value(item.get("label"))}
            for item in payload.get("stats") or []
            if plain_value(item.get("valeur")) and plain_value(item.get("label"))
        ]
        plain["avis"] = [
            {
                "note": max(1, min(5, int(item.get("note") or 1))),
                "commentaire": plain_value(item.get("commentaire")),
                "nom_auteur": plain_value(item.get("nom_auteur")),
            }
            for item in payload.get("avis") or []
            if plain_value(item.get("commentaire"))
        ]
        plain["process_steps"] = [plain_value(item) for item in payload.get("process_steps") or [] if plain_value(item)]
        plain["reasons"] = [plain_value(item) for item in payload.get("reasons") or [] if plain_value(item)]

        grouped: dict[str, list[dict[str, Any]]] = {}
        for selected in payload.get("selected_media") or []:
            if not isinstance(selected, dict) or selected.get("source") == "fallback":
                continue
            url = safe_url(selected.get("content_url"))
            usage = str(selected.get("usage") or "")
            if not url or not usage:
                continue
            item = dict(selected)
            item["content_url"] = url
            item["alt_text"] = plain_value(selected.get("alt_text"))
            grouped.setdefault(usage, []).append(item)
        for items in grouped.values():
            items.sort(key=lambda item: (int(item.get("position") or 0), str(item.get("media_id") or "")))

        logo = payload.get("logo") if isinstance(payload.get("logo"), dict) else None
        if logo:
            logo = dict(logo)
            logo["content_url"] = safe_url(logo.get("content_url"))
            logo["alt_text"] = plain_value(logo.get("alt_text"))
            if not logo["content_url"]:
                logo = None

        return cls(
            data=payload,
            profile=dict(profile),
            plain=plain,
            media={key: tuple(value) for key, value in grouped.items()},
            logo=logo,
            theme=get_theme(plain["metier"]),
        )

    def text(self, key: str) -> str:
        return html.escape(str(self.plain.get(key) or ""), quote=True)

    def items(self, key: str) -> list[Any]:
        return list(self.plain.get(key) or [])

    def selected(self, usage: str) -> tuple[dict[str, Any], ...]:
        return self.media.get(usage, ())

    def image_alt(self, item: dict[str, Any], fallback: str) -> str:
        return html.escape(str(item.get("alt_text") or fallback), quote=True)

    @property
    def business_name(self) -> str:
        return self.text("nom_entreprise")

    @property
    def trade_label(self) -> str:
        return html.escape(str(self.theme.get("label") or self.plain["metier"]), quote=True)

    @property
    def location(self) -> str:
        values = [self.plain.get("ville"), self.plain.get("code_postal")]
        return html.escape(" ".join(str(value) for value in values if value), quote=True)

    @property
    def phone_href(self) -> str:
        return "".join(char for char in str(self.plain.get("telephone") or "") if char.isdigit() or char == "+")

    def media_dimensions(self, item: dict[str, Any]) -> str:
        width, height = item.get("largeur"), item.get("hauteur")
        if isinstance(width, int) and width > 0 and isinstance(height, int) and height > 0:
            return f' width="{width}" height="{height}"'
        return ""
