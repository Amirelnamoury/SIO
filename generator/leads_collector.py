"""Script de collecte de leads : trouve les artisans BTP actifs d'un
departement via l'API publique et gratuite recherche-entreprises.api.gouv.fr
(basee sur SIRENE), puis (optionnellement) verifie via Google Custom Search
s'ils ont deja un site web, pour ne prospecter que ceux qui n'en ont pas.

L'API SIRENE n'a pas de champ "site web" : on croise donc avec une recherche
web et on exclut les domaines d'annuaires (pagesjaunes, societe.com, etc.)
des resultats, qui ne comptent pas comme un vrai site.

Usage :
    python leads_collector.py --departement 92 --metiers plombier,electricien --output leads.csv
    python leads_collector.py --departement 92 --metiers macon --check-site --output leads.csv
"""

import argparse
import csv
import os
import sys
import time

import requests

RECHERCHE_ENTREPRISES_URL = "https://recherche-entreprises.api.gouv.fr/search"
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Codes NAF (Nomenclature d'Activites Francaise) par metier, tels que
# demandes dans le brief.
CODES_NAF_PAR_METIER = {
    "plombier": ["43.22A", "43.22B"],
    "electricien": ["43.21A", "43.21B"],
    "macon": ["43.99C"],
    "peintre": ["43.34Z"],
}

# Domaines d'annuaires / reseaux sociaux a exclure : un artisan qui n'apparait
# QUE sur ces sites n'a pas de site web a lui.
DOMAINES_ANNUAIRES = {
    "pagesjaunes.fr", "societe.com", "verif.com", "pappers.fr",
    "facebook.com", "instagram.com", "linkedin.com", "infogreffe.fr",
    "manageo.fr", "kompass.com", "houzz.fr", "leboncoin.fr",
    "google.com", "goodli.fr", "hubside.fr", "societe.fr", "bing.com",
    "yelp.fr", "batiactu.com", "annuaire-entreprises.data.gouv.fr",
    "immatriculation.io", "corporama.com", "tel.local.fr",
}

# On evite de prospecter les entreprises trop grosses : ce ne sont pas des
# "artisans" au sens du brief.
CATEGORIES_EXCLUES = {"ETI", "GE"}


def rechercher_entreprises(departement: str, code_naf: str, max_resultats: int = 100) -> list[dict]:
    """Interroge recherche-entreprises.api.gouv.fr pour un departement et un
    code NAF donnes, avec pagination (25 resultats max par page)."""
    resultats = []
    page = 1
    per_page = 25
    while len(resultats) < max_resultats:
        params = {
            "activite_principale": code_naf,
            "departement": departement,
            "etat_administratif": "A",  # actives uniquement
            "per_page": per_page,
            "page": page,
        }
        response = requests.get(RECHERCHE_ENTREPRISES_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        page_resultats = data.get("results", [])
        if not page_resultats:
            break
        resultats.extend(page_resultats)

        if page >= data.get("total_pages", page):
            break
        page += 1
        time.sleep(0.2)  # eviter de bombarder l'API publique

    return resultats[:max_resultats]


def _etablissement_du_departement(entreprise: dict, departement: str) -> dict:
    """Une entreprise peut avoir plusieurs etablissements ; on prend celui
    qui correspond au departement recherche (matching_etablissements)."""
    for etab in entreprise.get("matching_etablissements", []):
        if (etab.get("code_postal") or "").startswith(departement):
            return etab
    return entreprise.get("siege", {})


def formater_lead(entreprise: dict, departement: str, metier: str) -> dict:
    etab = _etablissement_du_departement(entreprise, departement)
    return {
        "siren": entreprise.get("siren"),
        "siret": etab.get("siret"),
        "nom": entreprise.get("nom_commercial") or entreprise.get("nom_complet"),
        "metier": metier,
        "code_naf": entreprise.get("activite_principale"),
        "adresse": etab.get("adresse"),
        "code_postal": etab.get("code_postal"),
        "ville": etab.get("libelle_commune"),
        "date_creation": entreprise.get("date_creation"),
        "categorie_entreprise": entreprise.get("categorie_entreprise"),
        "site_web_detecte": None,  # rempli si --check-site est active
    }


def a_deja_un_site(nom_entreprise: str, ville: str, api_key: str, cse_id: str) -> bool | None:
    """Cherche l'entreprise sur Google (via Custom Search API) et regarde si
    un resultat pointe vers un vrai site (pas un annuaire). Renvoie None si
    la verification n'a pas pu etre faite (cles absentes ou erreur API)."""
    if not api_key or not cse_id:
        return None

    params = {
        "key": api_key,
        "cx": cse_id,
        "q": f'"{nom_entreprise}" {ville}',
        "num": 5,
    }
    try:
        response = requests.get(GOOGLE_CSE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return None

    data = response.json()
    for item in data.get("items", []):
        domaine = (item.get("displayLink") or "").lower().replace("www.", "")
        if not any(domaine == d or domaine.endswith("." + d) for d in DOMAINES_ANNUAIRES):
            return True
    return False


def collecter_leads(
    departement: str,
    metiers: list[str],
    max_par_metier: int = 100,
    check_site: bool = False,
    google_api_key: str | None = None,
    google_cse_id: str | None = None,
    exclure_grandes_entreprises: bool = True,
) -> list[dict]:
    leads = []

    for metier in metiers:
        codes_naf = CODES_NAF_PAR_METIER.get(metier)
        if not codes_naf:
            print(f"[!] Metier inconnu, ignore : {metier}", file=sys.stderr)
            continue

        for code_naf in codes_naf:
            print(f"-> Recherche {metier} ({code_naf}) dans le departement {departement}...")
            entreprises = rechercher_entreprises(departement, code_naf, max_resultats=max_par_metier)

            for entreprise in entreprises:
                if exclure_grandes_entreprises and entreprise.get("categorie_entreprise") in CATEGORIES_EXCLUES:
                    continue

                lead = formater_lead(entreprise, departement, metier)

                if check_site:
                    lead["site_web_detecte"] = a_deja_un_site(
                        lead["nom"], lead["ville"] or "", google_api_key, google_cse_id
                    )
                    time.sleep(0.3)  # respecter le quota Google CSE (100 requetes/jour gratuit)

                leads.append(lead)

    return leads


def ecrire_csv(leads: list[dict], output_path: str) -> None:
    if not leads:
        print("Aucun lead a ecrire.")
        return
    colonnes = list(leads[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colonnes)
        writer.writeheader()
        writer.writerows(leads)


def main():
    parser = argparse.ArgumentParser(description="Collecte des leads d'artisans BTP via l'API SIRENE")
    parser.add_argument("--departement", default="92", help="Code departement (ex: 92 pour Hauts-de-Seine)")
    parser.add_argument(
        "--metiers", default="plombier,electricien,macon,peintre",
        help="Liste de metiers separes par des virgules parmi : " + ", ".join(CODES_NAF_PAR_METIER.keys()),
    )
    parser.add_argument("--max-par-metier", type=int, default=100, help="Nombre max de resultats par metier")
    parser.add_argument(
        "--check-site", action="store_true",
        help="Verifie via Google Custom Search si l'artisan a deja un site (necessite GOOGLE_API_KEY et GOOGLE_CSE_ID)",
    )
    parser.add_argument("--output", default="leads.csv", help="Fichier CSV de sortie")
    args = parser.parse_args()

    metiers = [m.strip() for m in args.metiers.split(",") if m.strip()]

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID")
    if args.check_site and not (google_api_key and google_cse_id):
        print(
            "[!] --check-site demande mais GOOGLE_API_KEY / GOOGLE_CSE_ID ne sont pas definies. "
            "La verification de site web sera desactivee (colonne site_web_detecte = vide).",
            file=sys.stderr,
        )

    leads = collecter_leads(
        departement=args.departement,
        metiers=metiers,
        max_par_metier=args.max_par_metier,
        check_site=args.check_site,
        google_api_key=google_api_key,
        google_cse_id=google_cse_id,
    )

    ecrire_csv(leads, args.output)

    sans_site = sum(1 for l in leads if l["site_web_detecte"] is False)
    print(f"\n{len(leads)} leads collectes -> {args.output}")
    if args.check_site:
        print(f"{sans_site} d'entre eux semblent ne pas avoir de site web (site_web_detecte = False).")


if __name__ == "__main__":
    main()
