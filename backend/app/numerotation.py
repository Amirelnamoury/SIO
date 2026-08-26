from datetime import datetime

from sqlalchemy import insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import NumeroSequence


def generer_numero(db: Session, artisan_id: int, type_document: str, prefixe: str) -> str:
    """Genere un numero sequentiel par artisan/type/annee (ex: DEV-2026-0001),
    en resistant a la creation concurrente de deux documents (V5 section 5).

    Contrairement a un simple `count = db.query(...).count(); return count + 1`,
    l'incrementation ici est un UPDATE atomique sur une ligne de compteur
    dediee : deux requetes concurrentes ne peuvent jamais lire puis ecrire le
    meme numero, la seconde attend le verrou pose par la premiere. La ligne
    de compteur est creee au premier document de chaque annee (une seule
    fois, la contrainte d'unicite protege contre une double creation
    concurrente au tout premier document)."""
    annee = datetime.now().year

    resultat = db.execute(
        update(NumeroSequence)
        .where(
            NumeroSequence.artisan_id == artisan_id,
            NumeroSequence.type_document == type_document,
            NumeroSequence.annee == annee,
        )
        .values(dernier_numero=NumeroSequence.dernier_numero + 1)
        .returning(NumeroSequence.dernier_numero)
    )
    ligne = resultat.first()

    if ligne is None:
        try:
            with db.begin_nested():
                db.execute(
                    insert(NumeroSequence).values(
                        artisan_id=artisan_id, type_document=type_document, annee=annee, dernier_numero=1,
                    )
                )
            numero = 1
        except IntegrityError:
            # Une autre requete a cree la ligne de compteur entre notre UPDATE
            # (qui n'a rien trouve) et notre INSERT : elle existe desormais,
            # on peut incrementer normalement.
            resultat = db.execute(
                update(NumeroSequence)
                .where(
                    NumeroSequence.artisan_id == artisan_id,
                    NumeroSequence.type_document == type_document,
                    NumeroSequence.annee == annee,
                )
                .values(dernier_numero=NumeroSequence.dernier_numero + 1)
                .returning(NumeroSequence.dernier_numero)
            )
            numero = resultat.first()[0]
    else:
        numero = ligne[0]

    return f"{prefixe}-{annee}-{numero:04d}"
