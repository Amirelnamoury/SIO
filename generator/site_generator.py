"""Single runtime entry point for Site Vitrine generation.

V3 is the only active engine. Historical profiles remain persisted for
display/migration workflows, but this module never renders or converts them.
"""

from __future__ import annotations

from pathlib import Path

from .v3 import is_compatible_design_profile, render_site_v3


class SiteGenerationError(ValueError):
    """Controlled failure raised when the V3 pipeline cannot render a site."""


def generate_site(artisan: dict, api_base_url: str, output_path: str | None = None) -> str:
    """Render one static site with V3, without any V2 or legacy fallback."""
    if not is_compatible_design_profile(artisan.get("design_profile")):
        raise SiteGenerationError(
            "Un profil de design V3 valide est requis; aucun fallback V2 ou legacy n'est disponible."
        )

    try:
        generated_html = render_site_v3(artisan, api_base_url)
    except SiteGenerationError:
        raise
    except Exception as exc:
        raise SiteGenerationError(f"La generation V3 a echoue: {exc}") from exc

    if output_path:
        Path(output_path).write_text(generated_html, encoding="utf-8")
    return generated_html


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Genere un site vitrine V3")
    parser.add_argument("artisan_json", help="Chemin vers un fichier JSON decrivant l'artisan")
    parser.add_argument("--api-base", default="http://localhost:8000", help="URL de base de l'API Suite Artisan")
    parser.add_argument("--output", default="site.html", help="Fichier HTML de sortie")
    args = parser.parse_args()

    with open(args.artisan_json, encoding="utf-8") as source:
        artisan_data = json.load(source)

    generate_site(artisan_data, api_base_url=args.api_base, output_path=args.output)
    print(f"Site V3 genere : {args.output}")
