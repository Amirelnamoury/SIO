import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Artisan, Membre
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _resolve_subject(credentials: Optional[HTTPAuthorizationCredentials], db: Session):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Non authentifie")

    resultat = decode_access_token(credentials.credentials)
    if resultat is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expire")
    subject_id, subject_type = resultat

    if subject_type == "membre":
        membre = db.query(Membre).filter(Membre.id == subject_id).first()
        if membre is None or not membre.actif:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte introuvable ou desactive")
        artisan = db.query(Artisan).filter(Artisan.id == membre.artisan_id).first()
        if artisan is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Entreprise introuvable")
        return artisan, membre

    artisan = db.query(Artisan).filter(Artisan.id == subject_id).first()
    if artisan is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Artisan introuvable")
    return artisan, None


def get_current_artisan(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Artisan:
    """Extrait l'entreprise (tenant) courante depuis le token JWT, que la
    connexion soit celle du proprietaire ou d'un membre de son equipe.
    Toutes les routes protegees filtrent leurs requetes par artisan_id ==
    artisan.id, ce qui garantit l'isolation stricte entre tenants."""
    artisan, _membre = _resolve_subject(credentials, db)
    return artisan


@dataclass
class UtilisateurActif:
    """La personne precise qui agit (par opposition a get_current_artisan,
    qui donne toujours l'entreprise). Utilise uniquement la ou le role
    importe, ex: gestion de l'equipe."""

    artisan: Artisan
    membre: Optional[Membre]

    @property
    def role(self) -> str:
        return self.membre.role if self.membre is not None else "proprietaire"

    @property
    def nom(self) -> str:
        return self.membre.nom if self.membre is not None else self.artisan.nom_entreprise

    @property
    def email(self) -> str:
        return self.membre.email if self.membre is not None else self.artisan.email


def get_utilisateur_actif(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UtilisateurActif:
    artisan, membre = _resolve_subject(credentials, db)
    return UtilisateurActif(artisan=artisan, membre=membre)


def require_equipe_admin(
    utilisateur: UtilisateurActif = Depends(get_utilisateur_actif),
) -> UtilisateurActif:
    """Reserve a la gestion de l'equipe : le proprietaire ou un membre
    "administrateur", et seulement sur le plan Business (voir PLAN_ORDRE) -
    l'equipe multi-utilisateur est la fonction qui differencie Business des
    plans en-dessous."""
    plan_actuel = utilisateur.artisan.plan if utilisateur.artisan.plan in PLAN_ORDRE else "gratuit"
    if utilisateur.artisan.subscription_status != "active" or PLAN_ORDRE.index(plan_actuel) < PLAN_ORDRE.index("business"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="La gestion d'equipe fait partie du plan Business. Passez au plan Business pour la debloquer.",
        )
    if utilisateur.role not in ("proprietaire", "administrateur"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reserve aux administrateurs de l'equipe")
    return utilisateur


def require_active_subscription(
    artisan: Artisan = Depends(get_current_artisan),
) -> Artisan:
    """A utiliser sur les routes reservees aux fonctions payantes de Suite
    Artisan (chantiers, conformite, analytics...), quel que soit le plan
    tant qu'il est actif. La gestion des devis reste gratuite : c'est la
    porte d'entree qui donne envie de s'abonner, elle ne doit jamais etre
    verrouillee."""

    if artisan.subscription_status != "active":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Cette fonctionnalite fait partie de l'abonnement Suite Artisan. Abonnez-vous pour la debloquer.",
        )
    return artisan


# Hierarchie des 4 plans (section 28 du cahier des charges V4) : chaque plan
# inclut tout ce que le precedent debloque, plus une couche de valeur en
# plus. Volontairement seulement 2 frontieres au-dela de gratuit/payant
# (Pro pour l'automatisation, Business pour l'equipe) - pas une matrice de
# permissions elaboree, pour rester "simple a comprendre" comme demande.
PLAN_ORDRE = ["gratuit", "essentiel", "pro", "business"]
PLAN_LABELS = {"gratuit": "Gratuit", "essentiel": "Essentiel", "pro": "Pro", "business": "Business"}


def require_plan(plan_minimum: str):
    """Fabrique une dependance qui exige un abonnement actif ET un plan au
    moins egal a plan_minimum dans PLAN_ORDRE. Le message d'erreur nomme le
    plan requis (jamais juste "non autorise") pour que le paywall vende le
    palier suivant plutot que d'afficher une interdiction seche."""

    def _dependency(artisan: Artisan = Depends(require_active_subscription)) -> Artisan:
        plan_actuel = artisan.plan if artisan.plan in PLAN_ORDRE else "gratuit"
        if PLAN_ORDRE.index(plan_actuel) < PLAN_ORDRE.index(plan_minimum):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Cette fonctionnalite fait partie du plan {PLAN_LABELS[plan_minimum]}. Passez au plan {PLAN_LABELS[plan_minimum]} pour la debloquer.",
            )
        return artisan

    return _dependency


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "artisan"


def generate_unique_slug(db: Session, base_text: str) -> str:
    base_slug = slugify(base_text)
    slug = base_slug
    counter = 2
    while db.query(Artisan).filter(Artisan.slug == slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
