"""Translate a design profile into centralized CSS custom properties."""

from __future__ import annotations

from ..design_registry import FONT_PAIRS, palette_slot_index
from ..themes import get_palette
from .context import SiteContext


SYSTEM_FONT_PAIRS = {
    "poppins-inter": ("Arial Black, Arial, sans-serif", "Inter, Arial, sans-serif"),
    "archivo-inter": ("Arial Narrow, Arial, sans-serif", "Inter, Arial, sans-serif"),
    "fredoka-inter": ("Trebuchet MS, Arial, sans-serif", "Inter, Arial, sans-serif"),
    "rajdhani-inter": ("Bahnschrift, Arial Narrow, sans-serif", "Segoe UI, Arial, sans-serif"),
}

RADIUS_TOKENS = {
    "sharp": ("0", "0", "0"),
    "soft": ("2px", "4px", "6px"),
    "rounded": ("3px", "6px", "8px"),
    "pill": ("4px", "8px", "8px"),
}

SPACING_TOKENS = {
    "compact": ("56px", "20px", "1120px"),
    "comfortable": ("76px", "28px", "1160px"),
    "spacious": ("104px", "38px", "1220px"),
}


def _hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _contrast_text(background: str) -> str:
    red, green, blue = _hex_rgb(background)
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    return "#151515" if luminance > 0.56 else "#ffffff"


def design_tokens(ctx: SiteContext) -> str:
    palette_index = palette_slot_index(ctx.profile["palette"])
    palette = get_palette(ctx.plain["metier"], {**ctx.data, "variante_couleur": palette_index})
    heading, body = SYSTEM_FONT_PAIRS.get(ctx.profile["font_pair"], SYSTEM_FONT_PAIRS[FONT_PAIRS[0]["id"]])
    radius_sm, radius_md, radius_lg = RADIUS_TOKENS[ctx.profile["radius_style"]]
    section_space, gap, max_width = SPACING_TOKENS[ctx.profile["spacing_style"]]
    return f"""
:root {{
  --color-primary: {palette['primary']};
  --color-primary-dark: {palette['primary_dark']};
  --color-secondary: {palette['secondary']};
  --color-accent: {palette['accent']};
  --color-background: {palette['background']};
  --color-surface: #ffffff;
  --color-text: {palette['text']};
  --color-muted: #5d6268;
  --color-on-primary: {_contrast_text(palette['primary'])};
  --color-on-accent: {_contrast_text(palette['accent'])};
  --font-heading: {heading};
  --font-body: {body};
  --radius-sm: {radius_sm};
  --radius-md: {radius_md};
  --radius-lg: {radius_lg};
  --space-section: {section_space};
  --space-gap: {gap};
  --container: {max_width};
}}"""
