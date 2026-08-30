"""
Hachage de mot de passe et JWT.

IMPORTANT : on utilise le paquet `bcrypt` directement (bcrypt.hashpw / bcrypt.checkpw)
et PAS `passlib`. La combinaison passlib + bcrypt>=4.1 casse avec l'erreur
"password cannot be longer than 72 bytes" a cause d'un bug de detection de
version de passlib (passlib regarde bcrypt.__about__.__version__, qui n'existe
plus dans les versions recentes de bcrypt). En appelant bcrypt directement on
evite ce piege.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

# bcrypt tronque de toute facon a 72 octets : on le fait nous-memes explicitement
# pour ne jamais laisser une erreur surprenante remonter a l'utilisateur.
BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject_id: int, subject_type: str = "artisan", expires_minutes: int | None = None) -> str:
    """subject_type distingue une connexion proprietaire ("artisan") d'une
    connexion membre d'equipe ("membre") ou d'un compte interne ("admin").
    Seuls artisan et membre partagent les donnees d'une entreprise."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes if expires_minutes is None else expires_minutes
    )
    payload = {"sub": str(subject_id), "typ": subject_type, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> tuple[int, str] | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        # "typ" absent = jeton emis avant l'introduction des membres d'equipe :
        # on suppose "artisan" pour rester compatible avec les sessions en cours.
        return int(payload["sub"]), payload.get("typ", "artisan")
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
