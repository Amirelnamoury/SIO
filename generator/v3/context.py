"""Validated and escaped rendering context for the V3 site generator."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from .grammar import DESIGN_ENGINE_VERSION, PROFILE_VALUES

TRADE_LABELS = {
    "plombier": "Plombier",
    "electricien": "Électricien",
    "macon": "Maçon",
    "peintre": "Peintre",
    "menuisier": "Menuisier",
    "renovateur": "Entreprise de rénovation",
    "general": "Artisan du BTP",
}


def _major(value: object) -> int | None:
    try:
        return int(str(value).lstrip("v").split(".", 1)[0])
    except (TypeError, ValueError):
        return None


def is_compatible_design_profile(profile: object) -> bool:
    return bool(
        isinstance(profile, dict)
        and _major(profile.get("design_engine_version")) == _major(DESIGN_ENGINE_VERSION)
        and all(profile.get(axis) in values for axis, values in PROFILE_VALUES.items())
        and isinstance(profile.get("design_signature"), str)
        and bool(profile.get("design_signature"))
    )


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
            raise ValueError("Profil de design V3 incompatible")

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
            theme={"label": TRADE_LABELS.get(plain["metier"], TRADE_LABELS["general"])},
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
