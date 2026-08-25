"""Genere un mini-site vitrine HTML autonome (CSS + JS inline, aucune
dependance externe a part une police Google Fonts) pour un artisan donne.

Le formulaire de devis du site appelle directement l'API publique du SaaS
(POST /pub/{slug}/demande-devis) : pas de mailto, la demande arrive
directement dans le tableau de bord de l'artisan.

Usage :
    from site_generator import generate_site
    artisan = {
        "nom_entreprise": "Plomberie Dupont",
        "metier": "plombier",
        "slug": "plomberie-dupont",
        "ville": "Boulogne-Billancourt",
        "code_postal": "92100",
        "telephone": "06 01 02 03 04",
        "email": "contact@plomberie-dupont.fr",
        "siret": "123 456 789 00012",
        "assurance_decennale_nom": "AXA",
    }
    generate_site(artisan, api_base_url="https://api.suite-artisan.fr", output_path="site.html")
"""

from pathlib import Path

from themes import GOOGLE_FONTS, get_theme

# Sections "pourquoi nous choisir" : identiques pour tous les metiers, seul
# le style visuel change (couleurs/police du theme).
POURQUOI_NOUS_CHOISIR = [
    ("\U0001F6E1️", "Assurance decennale", "Tous nos chantiers sont couverts, en toute tranquillite."),
    ("\U0001F4C4", "Devis gratuit", "Un devis clair et detaille, sans engagement, sous 48h."),
    ("⏱️", "Reactivite", "Intervention rapide, y compris en urgence."),
]

CSS_TEMPLATE = """
:root {
  --primary: __PRIMARY__;
  --primary-dark: __PRIMARY_DARK__;
  --secondary: __SECONDARY__;
  --accent: __ACCENT__;
  --background: __BACKGROUND__;
  --text: __TEXT__;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: __FONT__;
  color: var(--text);
  background: var(--background);
  line-height: 1.6;
}
a { color: inherit; }
.container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }

header.site-header {
  position: sticky; top: 0; z-index: 10;
  background: var(--primary);
  color: #fff;
  box-shadow: 0 2px 10px rgba(0,0,0,0.15);
}
header.site-header .container {
  display: flex; align-items: center; justify-content: space-between;
  padding-top: 14px; padding-bottom: 14px;
}
.logo { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.25rem; }
.logo .icon { font-size: 1.6rem; }
.header-phone {
  background: var(--secondary);
  color: var(--primary-dark);
  padding: 8px 18px;
  border-radius: 999px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.hero {
  __HERO_BACKGROUND__
  color: __HERO_TEXT_COLOR__;
  padding: 80px 0 70px;
  text-align: center;
}
.hero .icon-large { font-size: 4rem; display: block; margin-bottom: 12px; }
.hero h1 { font-size: 2.4rem; margin-bottom: 14px; }
.hero p.tagline { font-size: 1.2rem; opacity: 0.92; max-width: 640px; margin: 0 auto 10px; }
.hero p.zone { font-size: 1rem; opacity: 0.85; margin-bottom: 28px; }
.btn-cta {
  display: inline-block;
  background: var(--accent);
  color: #fff;
  padding: 14px 32px;
  border-radius: 999px;
  font-weight: 700;
  text-decoration: none;
  font-size: 1.05rem;
  box-shadow: 0 6px 18px rgba(0,0,0,0.2);
  transition: transform 0.15s ease;
}
.btn-cta:hover { transform: translateY(-2px); }

section { padding: 64px 0; }
section h2 {
  text-align: center;
  font-size: 1.9rem;
  margin-bottom: 40px;
  color: var(--primary-dark);
}

.services-grid, .pourquoi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
}
.card {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.06);
  border-left: 4px solid var(--primary);
  border-radius: 10px;
  padding: 22px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.card h3 { font-size: 1.05rem; margin-bottom: 6px; color: var(--primary-dark); }
.card .emoji { font-size: 1.8rem; display: block; margin-bottom: 10px; }

section.pourquoi { background: var(--secondary); background-opacity: 0.15; }
.pourquoi-card { text-align: center; }
.pourquoi-card .emoji { font-size: 2.2rem; display: block; margin-bottom: 10px; }
.pourquoi-card h3 { color: var(--primary-dark); margin-bottom: 6px; }

section.devis { background: #fff; }
.devis-box {
  max-width: 560px; margin: 0 auto;
  background: var(--background);
  border-radius: 14px;
  padding: 32px;
  border: 1px solid rgba(0,0,0,0.06);
}
.devis-box label { display: block; font-weight: 600; margin: 14px 0 6px; font-size: 0.92rem; }
.devis-box input, .devis-box textarea {
  width: 100%;
  padding: 11px 14px;
  border-radius: 8px;
  border: 1px solid rgba(0,0,0,0.15);
  font-family: inherit;
  font-size: 0.98rem;
}
.devis-box textarea { min-height: 100px; resize: vertical; }
.devis-box button {
  margin-top: 22px;
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 999px;
  background: var(--primary);
  color: #fff;
  font-weight: 700;
  font-size: 1.02rem;
  cursor: pointer;
}
.devis-box button:disabled { opacity: 0.6; cursor: not-allowed; }
.form-message { margin-top: 16px; padding: 12px 14px; border-radius: 8px; font-size: 0.95rem; display: none; }
.form-message.success { display: block; background: #e7f7ee; color: #1e7e42; }
.form-message.error { display: block; background: #fdeaea; color: #b02a2a; }

footer.site-footer {
  background: var(--primary-dark);
  color: rgba(255,255,255,0.85);
  padding: 32px 0;
  font-size: 0.88rem;
  text-align: center;
}
footer.site-footer p { margin: 4px 0; }

@media (max-width: 640px) {
  .hero h1 { font-size: 1.8rem; }
  header.site-header .container { flex-direction: column; gap: 10px; }
}
"""

HERO_BACKGROUNDS = {
    "wave": (
        "background: linear-gradient(160deg, var(--primary) 0%, var(--primary-dark) 100%);",
        "#fff",
    ),
    "bolt": (
        "background: repeating-linear-gradient(115deg, var(--primary) 0px, var(--primary) 40px, "
        "#111 40px, #111 80px); background-color: var(--primary);",
        "var(--secondary)",
    ),
    "brick": (
        "background: repeating-linear-gradient(0deg, var(--primary) 0px, var(--primary) 38px, "
        "var(--primary-dark) 38px, var(--primary-dark) 42px);",
        "#fff",
    ),
    "palette": (
        "background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);",
        "#fff",
    ),
    "plain": (
        "background: linear-gradient(160deg, var(--primary) 0%, var(--primary-dark) 100%);",
        "#fff",
    ),
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__NOM_ENTREPRISE__ - __METIER_LABEL__ a __VILLE__</title>
<meta name="description" content="__NOM_ENTREPRISE__, __METIER_LABEL__ a __VILLE__ et environs. Devis gratuit sous 48h.">
__GOOGLE_FONT_LINK__
<style>
__CSS__
</style>
</head>
<body>

<header class="site-header">
  <div class="container">
    <div class="logo"><span class="icon">__ICON__</span> __NOM_ENTREPRISE__</div>
    <a class="header-phone" href="tel:__TELEPHONE_HREF__">\U0001F4DE __TELEPHONE__</a>
  </div>
</header>

<section class="hero">
  <div class="container">
    <span class="icon-large">__ICON__</span>
    <h1>__NOM_ENTREPRISE__</h1>
    <p class="tagline">__TAGLINE__</p>
    <p class="zone">Intervention a __VILLE__ (__CODE_POSTAL__) et dans les environs</p>
    <a class="btn-cta" href="#devis">Demander un devis gratuit</a>
  </div>
</section>

<section id="services">
  <div class="container">
    <h2>Nos prestations</h2>
    <div class="services-grid">
      __SERVICES_CARDS__
    </div>
  </div>
</section>

<section class="pourquoi">
  <div class="container">
    <h2>Pourquoi nous choisir</h2>
    <div class="pourquoi-grid">
      __POURQUOI_CARDS__
    </div>
  </div>
</section>

<section class="devis" id="devis">
  <div class="container">
    <h2>Demander un devis gratuit</h2>
    <div class="devis-box">
      <form id="devis-form">
        <label for="client_nom">Nom et prenom *</label>
        <input type="text" id="client_nom" name="client_nom" required>

        <label for="client_telephone">Telephone</label>
        <input type="tel" id="client_telephone" name="client_telephone">

        <label for="client_email">Email</label>
        <input type="email" id="client_email" name="client_email">

        <label for="description">Decrivez votre projet</label>
        <textarea id="description" name="description" placeholder="Ex: fuite d'eau sous l'evier de la cuisine..."></textarea>

        <button type="submit" id="devis-submit">Envoyer ma demande</button>
      </form>
      <div class="form-message" id="form-message"></div>
    </div>
  </div>
</section>

<footer class="site-footer">
  <div class="container">
    <p>__NOM_ENTREPRISE__ &mdash; __ADRESSE_LIGNE__</p>
    <p>SIRET __SIRET__ &mdash; Assurance decennale : __ASSURANCE_DECENNALE__</p>
    <p>&copy; __ANNEE__ __NOM_ENTREPRISE__. Tous droits reserves.</p>
  </div>
</footer>

<script>
(function () {
  var API_BASE = "__API_BASE__";
  var SLUG = "__SLUG__";
  var form = document.getElementById("devis-form");
  var messageBox = document.getElementById("form-message");
  var submitBtn = document.getElementById("devis-submit");

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    submitBtn.disabled = true;
    submitBtn.textContent = "Envoi en cours...";
    messageBox.className = "form-message";

    var payload = {
      client_nom: document.getElementById("client_nom").value,
      client_telephone: document.getElementById("client_telephone").value || null,
      client_email: document.getElementById("client_email").value || null,
      description: document.getElementById("description").value || null
    };

    fetch(API_BASE + "/pub/" + SLUG + "/demande-devis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function (response) {
        if (!response.ok) { throw new Error("Erreur serveur"); }
        return response.json();
      })
      .then(function () {
        messageBox.textContent = "Merci ! Votre demande a bien ete envoyee, nous vous recontactons rapidement.";
        messageBox.className = "form-message success";
        form.reset();
      })
      .catch(function () {
        messageBox.textContent = "Une erreur est survenue. Merci de nous appeler directement au __TELEPHONE__.";
        messageBox.className = "form-message error";
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = "Envoyer ma demande";
      });
  });
})();
</script>

</body>
</html>
"""


def _service_card(service: str) -> str:
    return f'<div class="card"><span class="emoji">✓</span><h3>{service}</h3></div>'


def _pourquoi_card(emoji: str, title: str, text: str) -> str:
    return (
        f'<div class="card pourquoi-card"><span class="emoji">{emoji}</span>'
        f"<h3>{title}</h3><p>{text}</p></div>"
    )


def generate_site(artisan: dict, api_base_url: str, output_path: str | None = None) -> str:
    """Genere le HTML du mini-site pour un artisan. Ecrit le fichier si
    output_path est fourni, et renvoie toujours le HTML en string."""

    from datetime import date

    metier = artisan.get("metier", "general")
    theme = get_theme(metier)

    services = artisan.get("services") or theme["services"]
    hero_bg, hero_text_color = HERO_BACKGROUNDS.get(theme["hero_style"], HERO_BACKGROUNDS["plain"])

    google_font = GOOGLE_FONTS.get(theme["font"])
    font_link = ""
    if google_font:
        font_link = (
            f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            f'<link href="https://fonts.googleapis.com/css2?family={google_font}&display=swap" rel="stylesheet">'
        )

    css = CSS_TEMPLATE
    css = css.replace("__PRIMARY__", theme["primary"])
    css = css.replace("__PRIMARY_DARK__", theme["primary_dark"])
    css = css.replace("__SECONDARY__", theme["secondary"])
    css = css.replace("__ACCENT__", theme["accent"])
    css = css.replace("__BACKGROUND__", theme["background"])
    css = css.replace("__TEXT__", theme["text"])
    css = css.replace("__FONT__", theme["font"])
    css = css.replace("__HERO_BACKGROUND__", hero_bg)
    css = css.replace("__HERO_TEXT_COLOR__", hero_text_color)

    services_cards = "\n      ".join(_service_card(s) for s in services)
    pourquoi_cards = "\n      ".join(_pourquoi_card(e, t, d) for e, t, d in POURQUOI_NOUS_CHOISIR)

    telephone = artisan.get("telephone") or "Nous contacter"
    telephone_href = "".join(ch for ch in telephone if ch.isdigit() or ch == "+")

    adresse_ligne = artisan.get("adresse") or f"{artisan.get('ville', '')} ({artisan.get('code_postal', '')})"

    html = HTML_TEMPLATE
    html = html.replace("__CSS__", css)
    html = html.replace("__GOOGLE_FONT_LINK__", font_link)
    html = html.replace("__NOM_ENTREPRISE__", artisan["nom_entreprise"])
    html = html.replace("__METIER_LABEL__", theme["label"])
    html = html.replace("__ICON__", theme["icon"])
    html = html.replace("__TAGLINE__", artisan.get("tagline") or theme["tagline"])
    html = html.replace("__VILLE__", artisan.get("ville") or "")
    html = html.replace("__CODE_POSTAL__", artisan.get("code_postal") or "")
    html = html.replace("__TELEPHONE_HREF__", telephone_href)
    html = html.replace("__TELEPHONE__", telephone)
    html = html.replace("__SERVICES_CARDS__", services_cards)
    html = html.replace("__POURQUOI_CARDS__", pourquoi_cards)
    html = html.replace("__ADRESSE_LIGNE__", adresse_ligne)
    html = html.replace("__SIRET__", artisan.get("siret") or "en cours d'immatriculation")
    html = html.replace("__ASSURANCE_DECENNALE__", artisan.get("assurance_decennale_nom") or "nous consulter")
    html = html.replace("__ANNEE__", str(date.today().year))
    html = html.replace("__API_BASE__", api_base_url.rstrip("/"))
    html = html.replace("__SLUG__", artisan["slug"])

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")

    return html


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Genere le mini-site vitrine d'un artisan")
    parser.add_argument("artisan_json", help="Chemin vers un fichier JSON decrivant l'artisan")
    parser.add_argument("--api-base", default="http://localhost:8000", help="URL de base de l'API Suite Artisan")
    parser.add_argument("--output", default="site.html", help="Fichier HTML de sortie")
    args = parser.parse_args()

    with open(args.artisan_json, encoding="utf-8") as f:
        artisan_data = json.load(f)

    generate_site(artisan_data, api_base_url=args.api_base, output_path=args.output)
    print(f"Site genere : {args.output}")
