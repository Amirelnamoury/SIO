"""Thirty restrained typography systems with responsive type rules."""

from ..models import TypographySystem


SPECS = (
    ("neo_grotesk_clarity", "neo_grotesk", "Arial", "Arial", "Arial", "Arial", "neutral clear conversion", .45, .25, .62, .35, .85, .96),
    ("swiss_information", "swiss_grotesk", "Helvetica Neue", "Helvetica Neue", "Arial", "ui-monospace", "technical grid precise", .62, .32, .88, .20, .72, .96),
    ("geometric_residential", "geometric_sans", "Avenir Next", "Avenir Next", "Arial", "Avenir Next", "minimal residential calm", .52, .55, .45, .52, .68, .93),
    ("humanist_workshop", "humanist_sans", "Gill Sans", "Gill Sans", "Trebuchet MS", "Georgia", "warm craft tactile", .48, .42, .28, .92, .54, .94),
    ("industrial_condensed", "industrial_condensed", "Arial Narrow", "Arial Narrow", "Arial", "ui-monospace", "industrial bold technical", .35, .25, .95, .18, .82, .88),
    ("editorial_residential", "editorial_serif", "Georgia", "Georgia", "Arial", "Georgia", "editorial residential elegant", .96, .78, .25, .65, .38, .91),
    ("quiet_luxury_serif", "luxury_serif", "Bodoni 72", "Bodoni 72", "Helvetica Neue", "Bodoni 72", "luxurious quiet high_contrast", .94, .98, .12, .42, .26, .86),
    ("transitional_trust", "transitional_serif", "Charter", "Charter", "Arial", "Charter", "trust institutional readable", .72, .62, .38, .58, .55, .98),
    ("structural_slab", "slab", "Rockwell", "Rockwell", "Arial", "Rockwell", "structural material bold", .40, .32, .70, .66, .75, .91),
    ("technical_mono_grotesk", "technical_mono", "ui-monospace", "Arial", "Arial", "ui-monospace", "technical diagrammatic precise", .42, .30, .98, .18, .66, .94),
    ("mono_accent_local", "mono_accent", "Arial", "Arial", "Arial", "Courier New", "local technical accent", .38, .20, .76, .34, .78, .95),
    ("display_sans_statement", "display_sans", "Arial Black", "Arial", "Arial", "Arial Black", "bold statement conversion", .40, .35, .62, .28, .94, .88),
    ("display_serif_material", "display_serif", "Georgia", "Georgia", "Verdana", "Georgia", "material editorial tactile", .91, .76, .18, .82, .32, .89),
    ("architectural_serif_sans", "serif_sans", "Times New Roman", "Times New Roman", "Arial", "Arial", "architectural elegant editorial", .88, .84, .38, .44, .34, .93),
    ("condensed_grotesk_signal", "condensed_grotesk", "Arial Narrow", "Arial Narrow", "Helvetica Neue", "Arial", "signal conversion compact", .36, .22, .78, .20, .96, .90),
    ("mono_grotesk_blueprint", "mono_grotesk", "Courier New", "Helvetica Neue", "Arial", "Courier New", "blueprint spatial technical", .45, .32, 1.0, .12, .58, .92),
    ("high_contrast_editorial", "high_contrast_editorial", "Bodoni 72", "Georgia", "Helvetica Neue", "Bodoni 72", "editorial luxurious dramatic", 1.0, .96, .10, .38, .24, .84),
    ("understated_architecture", "understated_architecture", "Helvetica Neue", "Helvetica Neue", "Arial", "Times New Roman", "minimal architectural quiet", .78, .72, .58, .28, .32, .98),
    ("local_contemporary", "local_contemporary", "Trebuchet MS", "Trebuchet MS", "Arial", "Georgia", "local warm approachable", .42, .25, .30, .72, .82, .97),
    ("warm_grotesk", "warm_grotesk", "Verdana", "Verdana", "Arial", "Georgia", "warm craft readable", .46, .38, .24, .88, .62, .98),
    ("gallery_neutral", "gallery_sans", "Helvetica Neue", "Helvetica Neue", "Arial", "Arial", "gallery neutral visual_led", .68, .62, .46, .25, .30, .98),
    ("heritage_serif", "heritage_serif", "Palatino", "Palatino", "Arial", "Palatino", "heritage craft editorial", .88, .72, .18, .92, .28, .94),
    ("construction_grotesk", "construction_grotesk", "Arial", "Arial Black", "Arial", "Arial Narrow", "construction strong practical", .30, .18, .82, .44, .92, .94),
    ("lighting_modernist", "modernist_sans", "Futura", "Futura", "Arial", "Courier New", "lighting modern technical", .64, .68, .78, .24, .52, .90),
    ("soft_residential", "soft_humanist", "Trebuchet MS", "Trebuchet MS", "Verdana", "Georgia", "residential warm calm", .52, .58, .22, .78, .52, .98),
    ("brutalist_index", "brutalist_sans", "Arial Black", "Arial Narrow", "Arial", "Courier New", "brutal index bold", .48, .24, .72, .22, .76, .86),
    ("cinematic_serif", "cinematic_serif", "Baskerville", "Baskerville", "Helvetica Neue", "Baskerville", "cinematic luxurious story_led", .96, .94, .12, .48, .24, .88),
    ("documentary_humanist", "documentary_sans", "Gill Sans", "Gill Sans", "Arial", "Georgia", "documentary human warm", .62, .42, .28, .86, .44, .96),
    ("material_slab_sans", "slab_sans", "Rockwell", "Rockwell", "Arial", "Arial Narrow", "material craft structural", .54, .38, .58, .84, .52, .92),
    ("precision_engineering", "engineering_sans", "DIN Condensed", "Arial Narrow", "Arial", "ui-monospace", "precision engineering technical", .38, .22, 1.0, .16, .72, .94),
)


TYPOGRAPHY_SYSTEMS = {}
LIMITED_FONTS = {"Bodoni 72", "Gill Sans", "Avenir Next", "DIN Condensed", "Futura", "Charter"}
SERIF_FONTS = {"Georgia", "Bodoni 72", "Times New Roman", "Charter", "Palatino", "Baskerville"}

for index, (system_id, category, display, heading, body, accent, traits, editorial, luxury, technical, warmth, conversion, readability) in enumerate(SPECS):
    if len(set((display, heading, body, accent))) > 3:
        accent = heading
    availability = "platform_limited" if display in LIMITED_FONTS or heading in LIMITED_FONTS else "system_safe"
    generic = "serif" if display in SERIF_FONTS else "sans-serif"
    fallback_stack = tuple(dict.fromkeys((display, heading, body, "Georgia" if generic == "serif" else "Arial", generic)))
    scale_bias = (index % 4) * .03
    hero_ceiling = 116 if editorial > .85 else 96 if luxury > .7 else 84 if technical > .75 else 88
    size_scale = (
        round(.76 + scale_bias / 3, 3), round(.88 + scale_bias / 3, 3), 1.0,
        round(1.22 + scale_bias, 3), round(1.56 + editorial * .12 + scale_bias, 3),
        round(2.05 + luxury * .22 + scale_bias, 3), round(2.82 + technical * .12 + editorial * .18, 3),
        round(3.75 + editorial * .55 + luxury * .35, 3),
    )
    line_heights = (
        round(1.0 + max(0, technical - .7) * .04, 3),
        round(1.10 + warmth * .08, 3),
        round(1.40 + readability * .16, 3),
        round(1.55 + readability * .15, 3),
    )
    uppercase_policy = "short_labels_only" if technical > .7 or conversion > .85 else "preserve_natural_case"
    personality = "editorial" if editorial > .8 else "technical" if technical > .8 else "warm" if warmth > .75 else "architectural_neutral"
    TYPOGRAPHY_SYSTEMS[system_id] = TypographySystem(
        id=system_id,
        category=category,
        display_family=display,
        heading_family=heading,
        body_family=body,
        accent_family=accent,
        weights=(400, 500, 700) if technical > .6 or conversion > .7 else (400, 500),
        size_scale=size_scale,
        line_height_scale=line_heights,
        letter_spacing_scale=(0.0,),
        case_behavior=uppercase_policy,
        max_title_width=14 if luxury > .8 else 20,
        hero_size_range=(44 if technical > .8 else 48, hero_ceiling),
        section_title_range=(28 if technical > .8 else 32, 58 if luxury > .8 else 64),
        body_measure=62 if editorial > .85 else 66 if readability > .95 else 72,
        mobile_scale=.60 if editorial > .9 else .66 if luxury > .8 else .72 if technical > .7 else .70,
        editorial_score=editorial,
        luxury_score=luxury,
        technical_score=technical,
        warmth_score=warmth,
        conversion_score=conversion,
        readability_score=readability,
        traits=frozenset(traits.split()),
        personality=personality,
        display_behavior="dramatic_short_lines" if editorial > .85 else "condensed_signal" if technical > .8 else "measured_identity",
        heading_behavior="compact_information" if technical > .75 else "editorial_chapters" if editorial > .75 else "clear_sections",
        body_behavior="dense_but_scannable" if technical > .75 else "long_form_readable" if editorial > .75 else "concise_readable",
        accent_behavior="mono_labels" if "mono" in category else "serif_contrast" if accent in SERIF_FONTS else "same_family_emphasis",
        title_proportions="narrow_tall" if "condensed" in category else "wide_editorial" if editorial > .8 else "balanced",
        uppercase_policy=uppercase_policy,
        numeric_style="tabular_lining" if technical > .65 or conversion > .8 else "proportional_lining",
        hero_wrapping_policy="two_to_four_intentional_lines" if editorial > .8 else "two_lines_preferred",
        section_wrapping="two_lines_max_mobile_three" if editorial > .7 else "two_lines_max",
        dense_mode_behavior="reduce_display_steps_and_preserve_body_measure",
        airy_mode_behavior="increase_space_and_measure_not_letter_spacing",
        availability=availability,
        fallback_stack=fallback_stack,
        max_font_count=len(set((display, heading, body, accent))),
    )


assert len(TYPOGRAPHY_SYSTEMS) == 30
