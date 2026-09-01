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


def _mix(left: str, right: str, ratio: float) -> str:
    a = tuple(round(channel * 255) for channel in _rgb(left))
    b = tuple(round(channel * 255) for channel in _rgb(right))
    values = tuple(round(x * (1 - ratio) + y * ratio) for x, y in zip(a, b))
    return "#" + "".join(f"{value:02x}" for value in values)


def _text_on(background: str) -> str:
    return "#111111" if contrast_ratio("#111111", background) >= contrast_ratio("#ffffff", background) else "#ffffff"


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

FAMILY_METADATA = {
    "architectural_neutral": ("limestone, paper and graphite", "neutral", "quiet precise", "canvas-led", "single functional accent", "flat mineral layers", "hairline structural", "architectural natural", ("understated_architecture", "neo_grotesk"), ("minimal_architecture", "architectural_contracting"), ("playful saturation",)),
    "limestone": ("cut limestone and lime plaster", "warm", "soft editorial", "light material field", "muted mineral accent", "tonal plaster surfaces", "low-contrast material rules", "warm natural", ("serif_sans", "transitional_serif"), ("premium_residential", "heritage_craft"), ("neon technical imagery",)),
    "concrete_graphite": ("concrete, steel and graphite", "cool", "firm technical", "graphite anchors", "steel signal", "dense mineral surfaces", "strong measured rules", "cool documentary", ("swiss_grotesk", "technical_mono"), ("technical_expert", "industrial_specialist"), ("soft romantic serif overload",)),
    "warm_craft": ("clay, leather and workshop wood", "warm", "tactile balanced", "warm canvas", "earth accent", "layered craft materials", "subtle hand-built divisions", "documentary warm", ("humanist_sans", "heritage_serif"), ("warm_artisan", "documentary_craft"), ("cold spatial diagrams",)),
    "linen_clay": ("linen, chalk and fired clay", "warm", "soft residential", "linen canvas", "clay highlight", "soft tonal surfaces", "restrained warm rules", "soft residential", ("soft_humanist", "editorial_serif"), ("premium_residential", "family_business"), ("industrial warning graphics",)),
    "terracotta": ("terracotta and mineral pigment", "warm", "expressive grounded", "light mineral field", "terracotta action", "pigment-led surfaces", "earth-toned boundaries", "sunlit material", ("humanist_sans", "display_serif"), ("peintre", "material_led"), ("blue-heavy technical systems",)),
    "wood_walnut": ("walnut, oak and workshop shadow", "warm", "deep craft", "wood-toned field", "joinery accent", "grain-inspired tonal surfaces", "joinery-like lines", "tactile low saturation", ("heritage_serif", "warm_grotesk"), ("high_end_craft", "heritage_craft"), ("glossy corporate blue",)),
    "copper_brass": ("aged brass and brushed copper", "warm", "luminous luxury", "dark-light metal contrast", "metallic accent used sparingly", "matte metal surfaces", "fine engraved rules", "warm directional light", ("luxury_serif", "serif_sans"), ("quiet_luxury", "high_end_craft"), ("multiple competing gold accents",)),
    "technical_navy": ("navy enamel and technical drawings", "cool", "high technical", "navy structure", "blue diagnostic signal", "controlled technical panels", "blueprint rules", "cool precise", ("technical_mono", "swiss_grotesk"), ("technical_expert", "spatial_technical"), ("warm heritage storytelling",)),
    "steel_cyan": ("stainless steel and cyan instrumentation", "cool", "clear diagnostic", "cool neutral field", "cyan information accent", "clean instrument surfaces", "precise cool borders", "bright technical", ("engineering_sans", "technical_mono"), ("technical_expert", "industrial_specialist"), ("cinematic warm luxury",)),
    "electrical_blue": ("electrical schematics and cobalt enamel", "cool", "signal contrast", "clean technical field", "cobalt action", "high-clarity surfaces", "functional signal lines", "architectural lighting", ("technical_mono", "engineering_sans"), ("technical_expert", "conversion_first_local"), ("decorative pastel collage",)),
    "luxury_ivory": ("ivory paper and honed stone", "warm", "quiet high contrast", "ivory field", "stone-gold accent", "large calm surfaces", "rare refined rules", "soft editorial", ("luxury_serif", "high_contrast_editorial"), ("quiet_luxury", "premium_residential"), ("dense bento grids",)),
    "ink_champagne": ("black ink and champagne metal", "warm-neutral", "editorial dramatic", "ink-led structure", "champagne detail", "paper and ink planes", "fine editorial lines", "low-saturation cinematic", ("high_contrast_editorial", "serif_sans"), ("editorial_studio", "luxury_renovation"), ("high-frequency utility UI",)),
    "burgundy_luxury": ("burgundy textile and dark timber", "warm", "rich restrained", "soft pale field", "burgundy emphasis", "textile-toned surfaces", "tonal dark-red rules", "warm cinematic", ("cinematic_serif", "transitional_serif"), ("luxury_renovation", "premium_residential"), ("construction warning orange",)),
    "forest_cream": ("forest paint and natural cream", "balanced-warm", "organic calm", "cream field", "forest action", "natural painted surfaces", "botanical dark rules", "natural documentary", ("humanist_sans", "heritage_serif"), ("warm_artisan", "family_business"), ("electric neon accents",)),
    "french_blue": ("painted joinery and French blue pigment", "cool-balanced", "residential clear", "pale blue-grey field", "French blue emphasis", "painted architectural surfaces", "blue-grey dividers", "soft daylight", ("transitional_serif", "local_contemporary"), ("premium_residential", "peintre"), ("black-yellow industrial language",)),
    "sage_local": ("sage paint and local stone", "warm-balanced", "approachable calm", "soft sage field", "leaf-dark action", "domestic matte surfaces", "soft local boundaries", "natural local", ("local_contemporary", "soft_humanist"), ("family_business", "warm_artisan"), ("brutalist density",)),
    "construction_orange": ("site signage and raw aggregate", "warm-signal", "direct high contrast", "neutral work surface", "orange action only", "practical durable surfaces", "strong construction lines", "documentary site", ("construction_grotesk", "condensed_grotesk"), ("conversion_first_local", "industrial_specialist"), ("quiet luxury serif",)),
    "signal_yellow": ("safety marking and technical labels", "warm-signal", "urgent legible", "high-clarity field", "yellow signal with dark text", "functional flat surfaces", "black signal rules", "technical documentary", ("engineering_sans", "industrial_condensed"), ("local_emergency_service", "technical_expert"), ("large yellow decorative fields",)),
    "high_contrast_monochrome": ("ink, paper and photographic contact sheets", "neutral", "maximum graphic", "black-white structure", "single monochrome reversal", "flat paper-like surfaces", "strong black rules", "monochrome or natural", ("brutalist_sans", "understated_architecture"), ("minimal_architecture", "editorial_studio"), ("multiple weak grey accents",)),
}


def _tokens(light: str, dark: str, brand: str, accent: str, mode: str) -> dict[str, str]:
    if mode == "light":
        canvas_alt = _mix(light, dark, .065)
        surface = _mix(light, "#ffffff", .62)
        surface_raised = _mix(light, "#ffffff", .82)
        text_primary = dark
        text_secondary = _mix(dark, light, .20)
        text_muted = _mix(dark, light, .31)
        brand_hover = _mix(brand, dark, .18)
        brand_active = _mix(brand, dark, .30)
        focus = accent if contrast_ratio(accent, light) >= 3 else dark
        return {
            "canvas": light, "canvas_alt": canvas_alt, "surface": surface, "surface_raised": surface_raised,
            "surface_inverse": dark, "text_primary": text_primary, "text_secondary": text_secondary,
            "text_muted": text_muted, "text_inverse": _text_on(dark), "border_soft": _mix(light, dark, .16),
            "border_default": _mix(light, dark, .34), "border_strong": _mix(light, dark, .68), "brand": brand,
            "brand_text": _text_on(brand), "brand_hover": brand_hover, "brand_hover_text": _text_on(brand_hover),
            "brand_active": brand_active, "brand_active_text": _text_on(brand_active), "accent": accent,
            "accent_secondary": _mix(accent, light, .36), "focus": focus, "success": "#18794e",
            "warning": "#8a5a00", "danger": "#b42318",
        }
    canvas_alt = _mix(dark, light, .09)
    surface = _mix(dark, light, .055)
    surface_raised = _mix(dark, light, .12)
    text_primary = light
    text_secondary = _mix(light, dark, .18)
    text_muted = _mix(light, dark, .30)
    brand_value = accent
    brand_hover = _mix(brand_value, light, .20)
    brand_active = _mix(brand_value, light, .32)
    focus = accent if contrast_ratio(accent, dark) >= 3 else light
    return {
        "canvas": dark, "canvas_alt": canvas_alt, "surface": surface, "surface_raised": surface_raised,
        "surface_inverse": light, "text_primary": text_primary, "text_secondary": text_secondary,
        "text_muted": text_muted, "text_inverse": _text_on(light), "border_soft": _mix(dark, light, .18),
        "border_default": _mix(dark, light, .34), "border_strong": _mix(dark, light, .70), "brand": brand_value,
        "brand_text": _text_on(brand_value), "brand_hover": brand_hover, "brand_hover_text": _text_on(brand_hover),
        "brand_active": brand_active, "brand_active_text": _text_on(brand_active), "accent": brand,
        "accent_secondary": _mix(brand, dark, .28), "focus": focus, "success": "#5dd39e",
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
    material, temperature, contrast_personality, dominant, accent_behavior, surface, border, image_treatment, type_categories, archetypes, bad = FAMILY_METADATA[family]
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
            material_inspiration=material,
            temperature=temperature,
            contrast_personality=contrast_personality,
            dominant_behavior=dominant,
            accent_behavior=accent_behavior,
            surface_philosophy=surface,
            border_philosophy=border,
            image_treatment_preference=image_treatment,
            recommended_typography_categories=type_categories,
            recommended_archetypes=archetypes,
            bad_combinations=bad,
        )


assert len(COLOR_SYSTEMS) == 40
