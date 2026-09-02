"""DOM primitives that materialize renderer-visible blueprint decisions."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from generator.design_genome.models import ComponentDefinition

if TYPE_CHECKING:
    from .context import RenderContext, RenderMedia


def image(asset: "RenderMedia", fallback_alt: str, *, eager: bool = False, class_name: str = "") -> str:
    dimensions = f' width="{asset.width}" height="{asset.height}"' if asset.width and asset.height else ""
    loading = "eager" if eager else "lazy"
    priority = ' fetchpriority="high"' if eager else ""
    alt = html.escape(asset.alt or fallback_alt, quote=True)
    return (
        f'<img class="{html.escape(class_name, quote=True)}" src="{asset.url}" alt="{alt}"'
        f'{dimensions} loading="{loading}" decoding="async"{priority}>'
    )


def actions_html(ctx: "RenderContext") -> str:
    """Shared conversion actions (quote link / phone / email).

    Lives here (not in ``sections.py``) so both the generic section
    renderers and the family-specific ones in ``families.py`` can use it
    without an import cycle.
    """
    values = []
    if ctx.plain("slug") and (ctx.dna.contact_component or ctx.dna.form_component):
        values.append('<a class="button button-primary" href="#contact">Parler du projet</a>')
    if ctx.phone_href:
        values.append(f'<a class="button button-secondary" href="tel:{ctx.phone_href}">Appeler</a>')
    elif ctx.plain("email"):
        values.append(f'<a class="button button-secondary" href="mailto:{ctx.text("email")}">Écrire</a>')
    return f'<div class="actions">{"".join(values)}</div>' if values else ""


def component_attributes(component: ComponentDefinition) -> str:
    spec = component.blueprint_spec
    values = {
        "component": component.id,
        "family": component.family_id,
        "variant": component.variant_id,
        "layout": spec.layout_model,
        "pattern": spec.layout_pattern,
        "edge": spec.edge_behavior,
        "flow": spec.desktop_spec.get("flow_direction", "natural_sequence"),
        "anchor": spec.desktop_spec.get("alignment_anchor", "content_start"),
        "frame": spec.desktop_spec.get("frame_behavior", "unframed"),
        "collapse": spec.mobile_spec.get("collapse_strategy", "linear_stack"),
        "priority": spec.mobile_spec.get("priority_anchor", "content_first"),
    }
    return " ".join(f'data-{key}="{html.escape(str(value), quote=True)}"' for key, value in values.items())


def layout_regions(component: ComponentDefinition, copy: str, media: str = "", extra: str = "") -> str:
    """Compose regions from structural metadata, never from component identity.

    An empty media string always recomposes to a copy-only layout instead of
    emitting a hollow ``<div class="g-media"></div>``. A blueprint promising
    a media region is not evidence that one rendered; only real markup is.
    """
    if not media:
        pattern_hint = component.blueprint_spec.layout_pattern
        return f'<div class="g-layout g-layout--{html.escape(pattern_hint, quote=True)} g-layout--no-media"><div class="g-copy">{copy}</div>{extra}</div>'

    spec = component.blueprint_spec
    media_position = spec.media_spec.get("media_position") or spec.desktop_spec.get("media_position") or "supporting"
    pattern = spec.layout_pattern
    flow = spec.desktop_spec.get("flow_direction")

    if media_position == "full_bleed_background":
        return f'<div class="g-cover"><div class="g-media g-media--backdrop">{media}</div><div class="g-copy g-copy--overlay">{copy}</div>{extra}</div>'
    if media_position == "centered_frame":
        return f'<div class="g-centered-frame"><figure class="g-frame">{media}</figure><div class="g-copy g-copy--separate">{copy}</div>{extra}</div>'
    if media_position == "wide_horizon_band":
        return f'<div class="g-panorama"><figure class="g-panorama-band">{media}</figure><div class="g-copy g-copy--boundary">{copy}</div>{extra}</div>'
    if media_position == "atmospheric_background":
        return f'<div class="g-atmosphere"><div class="g-atmosphere-media">{media}</div><div class="g-atmosphere-copy">{copy}</div>{extra}</div>'
    if pattern in {"grid", "matrix", "masonry", "asymmetric"}:
        return f'<div class="g-layout g-layout--{pattern}"><div class="g-copy">{copy}</div><div class="g-media">{media}</div>{extra}</div>'
    # `layout_pattern` (resolved once, deliberately, per component -- see
    # LAYOUT_PATTERNS/HERO_BLUEPRINT_SEMANTICS) is the authoritative layout
    # signal. `flow_direction` alone used to be treated as an alternative
    # trigger for the rail/overlay wrapper ("horizontal_progression" simply
    # describes left-to-right reading order and is shared by dozens of
    # split/grid/matrix/rows components; it does not mean "this is a
    # scrolling carousel"). That silently forced 37 unrelated components
    # (e.g. split_service_photo) into the horizontal-rail treatment, and 19
    # more into the overlay treatment -- confirmed against the catalog, not
    # a one-off. Pattern alone decides now; flow still drives the `data-flow`
    # attribute and finer CSS (component_attributes), just not the wrapper shape.
    if pattern in {"rail", "horizontal_rail"}:
        return f'<div class="g-layout g-layout--rail"><div class="g-copy">{copy}</div><div class="g-media g-rail">{media}</div>{extra}</div>'
    if pattern in {"overlay", "full_bleed"}:
        return f'<div class="g-layout g-layout--overlay"><div class="g-media">{media}</div><div class="g-copy">{copy}</div>{extra}</div>'
    order = "media-first" if spec.mobile_spec.get("priority_anchor") == "media_first" or flow == "reverse_axis" else "copy-first"
    return f'<div class="g-layout g-layout--split g-layout--{order}"><div class="g-copy">{copy}</div><div class="g-media">{media}</div>{extra}</div>'
