"""Validated and escaped rendering context for V3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..v2.context import SiteContext as V2SiteContext
from .grammar import DESIGN_ENGINE_VERSION, PROFILE_VALUES


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


@dataclass(frozen=True)
class SiteContext(V2SiteContext):
    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "SiteContext":
        profile = payload.get("design_profile")
        if not is_compatible_design_profile(profile):
            raise ValueError("Profil de design V3 incompatible")
        adapted = dict(payload)
        # Reuse the mature escaping/media parser without weakening either
        # version gate: feed it a temporary valid V2 profile, then restore V3.
        adapted["design_profile"] = {
            "design_family": "architecture", "header_variant": "minimal", "hero_variant": "editorial",
            "services_variant": "editorial", "gallery_variant": "featured", "about_variant": "editorial",
            "reviews_variant": "minimal", "cta_variant": "minimal", "footer_variant": "simple",
            "section_order": ["hero", "services", "contact"], "palette": "palette-1",
            "font_pair": "archivo-inter", "radius_style": "sharp", "spacing_style": "spacious",
            "image_treatment": "flat", "design_engine_version": "v2.0", "design_signature": "v3-context-adapter",
        }
        base = V2SiteContext.from_payload(adapted)
        return cls(data=payload, profile=dict(profile), plain=base.plain, media=base.media, logo=base.logo, theme=base.theme)
