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

    @staticmethod
    def _role_matches(item: RenderMedia, role: str) -> bool:
        """Test one candidate against one accepted role, provenance included.

        This is the single place that decides whether an item satisfies a
        named role. ``artisan_project``/``before_after`` are provenance-locked
        (only a matching artisan-sourced item can ever satisfy them); they
        must never be treated as a blanket veto over items that satisfy a
        *different* accepted role -- see ``media_for`` below.
        """
        if role == "artisan_project":
            return item.role == "artisan_project" and item.source_class == "artisan"
        if role == "before_after":
            return item.role == "before_after" and item.source_class == "artisan"
        if role == "stock_photo":
            return item.source_class == "stock"
        if role == "artisan_photo":
            return item.source_class == "artisan" and item.role not in {"artisan_project", "before_after"}
        return item.role == role

    def _section_roles(self, component: ComponentDefinition) -> set[str]:
        section_roles = {component.category, "ambient"}
        if component.category == "hero":
            section_roles |= {"hero", "landscape", "portrait"}
        elif component.category == "gallery":
            section_roles |= {"gallery", "landscape", "portrait", "artisan_project", "before_after"}
        elif component.category == "about":
            # About may legitimately reuse ambient hero/gallery-role stock
            # photography (see about_spec's "stock_ambient_only" provenance);
            # the alternative is an empty media slot for no honest reason.
            section_roles |= {"about", "portrait", "hero", "gallery", "landscape"}
        return section_roles

    def media_for(
        self,
        component: ComponentDefinition,
        *,
        limit: int | None = None,
        pool: "tuple[RenderMedia, ...] | None" = None,
    ) -> tuple[RenderMedia, ...]:
        """Return the media this component is structurally allowed to show.

        ``required_media`` is an AND-style requirement (every listed role must
        be satisfied by the same candidate; in practice callers only ever list
        zero or one role there). ``required_any_media`` is an OR-style
        requirement: a candidate is accepted as soon as it satisfies *any one*
        of the listed roles. The two must stay independent -- merging them
        into a single set and testing membership (the V0.1 approach) silently
        turned every OR list that happened to include ``artisan_project`` into
        an impossible AND, rejecting perfectly compatible stock photos and
        forcing the graphic fallback even when real, allowed media existed.
        """
        required_all = set(component.required_media)
        required_any = set(component.required_any_media)
        allowed_sources = set(component.allowed_media_sources)
        section_roles = self._section_roles(component)
        candidates = self.media if pool is None else pool

        values: list[RenderMedia] = []
        seen: set[str] = set()
        for item in candidates:
            if item.id in seen or item.role == "logo":
                continue
            if item.source_class not in allowed_sources:
                continue
            if required_all and not all(self._role_matches(item, role) for role in required_all):
                continue
            if required_any and not any(self._role_matches(item, role) for role in required_any):
                continue
            if not required_all and not required_any and item.role not in section_roles:
                continue
            seen.add(item.id)
            values.append(item)
        # NOTE: `limit=0` must mean "zero items" (a family declaring
        # media_count_max=0, e.g. typographic), not "unlimited" -- Python
        # treats 0 as falsy, so this cannot be `values[:limit] if limit else
        # values` (that silently ignored an explicit zero).
        return tuple(values) if limit is None else tuple(values[:limit])

    def media_by_ids(self, ids: tuple[str, ...]) -> tuple[RenderMedia, ...]:
        """Hydrate already-decided media ids (from a resolved ``SectionPlan``)
        back into ``RenderMedia`` objects, preserving order.

        This is a lookup, not a decision: *which* ids a section gets was
        decided once, in ``render_plan.build_render_plan`` (rule 4 of the
        V0.2.1 brief -- no second place re-derives that choice). Renderers
        call this only to materialize markup from an id list they were
        already handed.
        """
        by_id = {item.id: item for item in self.media}
        return tuple(by_id[id_] for id_ in ids if id_ in by_id)

    def logo(self) -> RenderMedia | None:
        return next((item for item in self.media if item.role == "logo"), None)
