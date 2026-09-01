"""Forty semantic color systems with accessibility and affinity metadata."""

from __future__ import annotations

from ..models import ColorSystem


def _rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


def contrast_ratio(left: str, right: str) -> float:
    def luminance(color: str) -> float:
        channels = [channel / 12.92 if channel <= .04045 else ((channel + .055) / 1.055) ** 2.4 for channel in _rgb(color)]
        return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]

    bright, dark = sorted((luminance(left), luminance(right)), reverse=True)
    return round((bright + .05) / (dark + .05), 2)


FAMILIES = (
    ("architectural_neutral", "#f4f3f0", "#181817", "#50504c", "#b9b7b0", .45, .72, .72, .42, .42, .42),
    ("limestone", "#f3efe5", "#24211c", "#83745d", "#c6ad84", .72, .72, .32, .70, .44, .38),
    ("concrete_graphite", "#ececeb", "#171819", "#4d555b", "#a8b0b5", .28, .52, .88, .38, .48, .55),
    ("warm_craft", "#f5eee4", "#261f1a", "#8a5a38", "#c58a59", .88, .55, .22, .96, .48, .45),
    ("linen_clay", "#f7f1e8", "#2a211d", "#9a6655", "#d3a68f", .86, .65, .20, .82, .42, .36),
    ("terracotta", "#f8eee9", "#2c1d18", "#aa4e35", "#d88964", .92, .48, .22, .78, .58, .70),
    ("wood_walnut", "#f0e9df", "#221a16", "#6f4934", "#b58b62", .90, .60, .25, .98, .40, .38),
    ("copper_brass", "#f5eee5", "#241d17", "#8d5b32", "#c49a54", .82, .84, .38, .82, .52, .54),
    ("technical_navy", "#eef3f8", "#101923", "#174a7a", "#2f83c8", .22, .58, .98, .18, .82, .70),
    ("steel_cyan", "#edf5f6", "#111d20", "#287887", "#45b6c5", .18, .45, .96, .25, .84, .72),
    ("electrical_blue", "#eff4ff", "#10172a", "#2157b8", "#54a2ff", .15, .44, .98, .16, .95, .82),
    ("luxury_ivory", "#faf6ed", "#211d17", "#6f604d", "#b89a67", .74, .98, .18, .58, .36, .34),
    ("ink_champagne", "#f6f0e5", "#151412", "#3c352e", "#d1b47b", .66, .98, .46, .50, .45, .42),
    ("burgundy_luxury", "#f8f0f1", "#28151a", "#741f36", "#bd7181", .72, .94, .28, .48, .48, .58),
    ("forest_cream", "#f3f3e8", "#182019", "#315c3a", "#91ae78", .62, .75, .52, .74, .40, .45),
    ("french_blue", "#f1f4f8", "#161d28", "#315a82", "#8daec9", .32, .72, .86, .32, .62, .54),
    ("sage_local", "#f3f5ee", "#1c231c", "#547258", "#a1b28d", .66, .48, .45, .76, .58, .52),
    ("construction_orange", "#fff3e8", "#271b12", "#b84d11", "#ef8b32", .84, .30, .70, .40, .98, .96),
    ("signal_yellow", "#fff9df", "#1d1c16", "#7a5c00", "#f2c617", .78, .22, .80, .32, 1.0, .98),
    ("high_contrast_monochrome", "#ffffff", "#0a0a0a", "#1e1e1e", "#bdbdbd", .30, .70, .78, .25, .80, .82),
)


def _tokens(light: str, dark: str, brand: str, accent: str, mode: str) -> dict[str, str]:
    if mode == "light":
        return {
            "canvas": light, "canvas_alt": "#eeeeea", "surface": "#ffffff", "surface_raised": "#ffffff",
            "surface_inverse": dark, "text_primary": "#171717", "text_secondary": "#3f3f3f",
            "text_muted": "#606060", "text_inverse": "#ffffff", "border_soft": "#d8d8d4",
            "border_default": "#a6a6a0", "border_strong": "#565650", "brand": brand,
            "brand_hover": dark, "brand_active": "#000000", "accent": accent,
            "accent_secondary": "#7f8d8d", "focus": "#005fcc", "success": "#18794e",
            "warning": "#8a5a00", "danger": "#b42318",
        }
    return {
        "canvas": dark, "canvas_alt": "#242424", "surface": "#1e1e1e", "surface_raised": "#292929",
        "surface_inverse": light, "text_primary": "#f7f7f5", "text_secondary": "#d2d2ce",
        "text_muted": "#aaaaa5", "text_inverse": "#171717", "border_soft": "#3f3f3d",
        "border_default": "#686864", "border_strong": "#b7b7b0", "brand": accent,
        "brand_hover": "#ffffff", "brand_active": light, "accent": brand,
        "accent_secondary": "#95a4a4", "focus": "#78b7ff", "success": "#5dd39e",
        "warning": "#ffd166", "danger": "#ff7b72",
    }


def _typography(luxury: float, technical: float, craft: float) -> tuple[str, ...]:
    if luxury >= .8:
        return ("high_contrast_editorial", "quiet_luxury_serif", "architectural_serif_sans")
    if technical >= .8:
        return ("technical_mono_grotesk", "industrial_condensed", "swiss_information")
    if craft >= .8:
        return ("humanist_workshop", "heritage_serif", "warm_grotesk")
    return ("neo_grotesk_clarity", "understated_architecture", "local_contemporary")


COLOR_SYSTEMS: dict[str, ColorSystem] = {}
for family, light, dark, brand, accent, warmth, luxury, technical, craft, conversion, _signal in FAMILIES:
    scores = {"plombier": technical, "electricien": max(technical, conversion), "macon": max(technical, craft), "peintre": max(warmth, luxury), "menuisier": craft, "renovateur": luxury}
    for mode in ("light", "dark"):
        tokens = _tokens(light, dark, brand, accent, mode)
        system_id = f"{family}_{mode}"
        COLOR_SYSTEMS[system_id] = ColorSystem(
            id=system_id,
            family=family,
            mode=mode,
            tokens=tokens,
            contrast_score=min(
                contrast_ratio(tokens["text_primary"], tokens["canvas"]),
                contrast_ratio(tokens["text_inverse"], tokens["surface_inverse"]),
            ),
            warmth_score=warmth,
            luxury_score=luxury,
            technical_score=technical,
            craft_score=craft,
            conversion_score=conversion,
            trade_affinities=scores,
            compatible_typography=_typography(luxury, technical, craft),
            compatible_image_strategies=("natural", "documentary", "material") if warmth >= .6 else ("architectural", "technical", "monochrome"),
            incompatible_traits=frozenset({"playful"}) if luxury >= .8 else frozenset(),
        )


assert len(COLOR_SYSTEMS) == 40
