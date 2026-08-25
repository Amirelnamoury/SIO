"""Petit outil en ligne de commande pour activer/desactiver l'abonnement
d'un artisan a la main, tant que Stripe n'est pas branche pour de vrai
(ex : un client paie par virement en attendant).

Usage :
    python manage_subscription.py activer dupont@example.com
    python manage_subscription.py desactiver dupont@example.com
    python manage_subscription.py statut dupont@example.com
"""

import sys

from app.database import SessionLocal
from app.models import Artisan


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("activer", "desactiver", "statut"):
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
            print(f"{artisan.nom_entreprise} ({artisan.email}) : {artisan.subscription_status}")
            return

        artisan.subscription_status = "active" if action == "activer" else "inactive"
        db.commit()
        print(f"OK : abonnement de {artisan.nom_entreprise} ({artisan.email}) -> {artisan.subscription_status}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
