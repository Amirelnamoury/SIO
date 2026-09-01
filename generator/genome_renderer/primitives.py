"""DOM primitives that materialize renderer-visible blueprint decisions."""

from __future__ import annotations

import html

from generator.design_genome.models import ComponentDefinition


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
    """Compose regions from structural metadata, never from component identity."""
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
    if pattern in {"rail", "horizontal_rail"} or flow == "horizontal_progression":
        return f'<div class="g-layout g-layout--rail"><div class="g-copy">{copy}</div><div class="g-media g-rail">{media}</div>{extra}</div>'
    if pattern in {"overlay", "full_bleed"} or flow == "layered_progression":
        return f'<div class="g-layout g-layout--overlay"><div class="g-media">{media}</div><div class="g-copy">{copy}</div>{extra}</div>'
    if pattern in {"typographic", "rows", "timeline", "stack"} and not media:
        return f'<div class="g-layout g-layout--{pattern}"><div class="g-copy">{copy}</div>{extra}</div>'
    order = "media-first" if spec.mobile_spec.get("priority_anchor") == "media_first" or flow == "reverse_axis" else "copy-first"
    return f'<div class="g-layout g-layout--split g-layout--{order}"><div class="g-copy">{copy}</div><div class="g-media">{media}</div>{extra}</div>'
