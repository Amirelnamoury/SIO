"""Outil en ligne de commande pour renseigner le site vitrine livre a un
artisan (le site est fabrique et livre par nous, pas par l'artisan lui-meme -
voir generator/. Ce script sert juste a informer le SaaS que le site existe).

Usage :
    python manage_site.py livrer dupont@example.com https://plomberie-dupont.fr
    python manage_site.py en-cours dupont@example.com
    python manage_site.py statut dupont@example.com
"""

import sys

from app.database import SessionLocal
from app.models import Artisan


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("livrer", "en-cours", "statut"):
        print(__doc__)
        sys.exit(1)

    action, email = sys.argv[1], sys.argv[2]
    db = SessionLocal()
    try:
        artisan = db.query(Artisan).filter(Artisan.email == email).first()
        if artisan is None:
            print(f"Aucun artisan trouve avec l'email {email}")
            sys.exit(1)

        if action == "statut":
            url_affichee = artisan.site_url or "pas d'URL"
            print(f"{artisan.nom_entreprise} : {artisan.site_statut} ({url_affichee})")
            return

        if action == "livrer":
            if len(sys.argv) != 4:
                print("Usage : python manage_site.py livrer <email> <url>")
                sys.exit(1)
            artisan.site_statut = "livre"
            artisan.site_url = sys.argv[3]
        elif action == "en-cours":
            artisan.site_statut = "en_cours"

        db.commit()
        print(f"OK : site de {artisan.nom_entreprise} -> {artisan.site_statut} ({artisan.site_url or '-'})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
