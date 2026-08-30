"""Couche d'envoi d'emails transactionnels. Fournisseur : Resend (API HTTP
simple, pas de SDK). Si RESEND_API_KEY n'est pas defini, aucun email n'est
envoye, mais chaque tentative est journalisee avec un statut clair
("non_configure") - jamais de faux "email envoye" (voir EMAIL_LOG_STATUTS).

Pour changer de fournisseur plus tard : seule _send_raw() doit changer,
toute la couche au-dessus (send_devis, send_facture...) reste identique.
"""
import logging
import time

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import EmailLog
from app import email_templates as tpl

logger = logging.getLogger("suite_artisan.email")


def is_configured() -> bool:
    return bool(settings.resend_api_key)


def _log(
    db: Session, *, artisan_id: int, type_: str, destinataire: str | None, objet: str | None,
    statut: str, erreur: str | None = None, provider_id: str | None = None,
    client_id: int | None = None, devis_id: int | None = None, facture_id: int | None = None,
) -> EmailLog:
    entry = EmailLog(
        artisan_id=artisan_id, client_id=client_id, devis_id=devis_id, facture_id=facture_id,
        type=type_, destinataire=destinataire, objet=objet, statut=statut, erreur=erreur, provider_id=provider_id,
    )
    db.add(entry)
    db.commit()
    return entry


# Un blip reseau ou une erreur 5xx cote fournisseur est generalement
# transitoire : une seule retentative rapide avant d'abandonner. Volontai-
# rement borne (1 retry, timeout reduit) pour ne jamais bloquer une requete
# utilisateur synchrone (ex: "Envoyer le devis") plus de ~20s au pire.
_MAX_TENTATIVES = 2
_TIMEOUT_PAR_TENTATIVE = 10.0
_PAUSE_ENTRE_TENTATIVES = 0.5


def _send_raw(destinataire: str, objet: str, html: str) -> tuple[bool, str | None, str | None]:
    """Retourne (succes, provider_id, erreur). Ne leve jamais : toute panne
    reseau ou refus du fournisseur est capturee et remontee proprement."""
    derniere_erreur = None
    for tentative in range(1, _MAX_TENTATIVES + 1):
        try:
            resp = httpx.post(
                settings.resend_api_url,
                headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
                json={
                    "from": f"{settings.email_from_nom} <{settings.email_from}>",
                    "to": [destinataire],
                    "subject": objet,
                    "html": html,
                },
                timeout=_TIMEOUT_PAR_TENTATIVE,
            )
            if resp.status_code >= 500:
                derniere_erreur = f"HTTP {resp.status_code} : {resp.text[:300]}"
            elif resp.status_code >= 400:
                # Erreur client (ex: destinataire invalide) : jamais transitoire,
                # inutile de retenter.
                return False, None, f"HTTP {resp.status_code} : {resp.text[:300]}"
            else:
                data = resp.json()
                return True, data.get("id"), None
        except httpx.HTTPError as exc:
            derniere_erreur = f"Erreur reseau : {exc}"

        if tentative < _MAX_TENTATIVES:
            logger.info("Tentative %d/%d d'envoi echouee (%s), nouvel essai...", tentative, _MAX_TENTATIVES, derniere_erreur)
            time.sleep(_PAUSE_ENTRE_TENTATIVES)

    return False, None, derniere_erreur


def _envoyer(
    db: Session, artisan, client, type_: str, objet: str, html: str,
    devis_id: int | None = None, facture_id: int | None = None,
) -> EmailLog:
    destinataire = client.email if client else None
    if not destinataire:
        return _log(
            db, artisan_id=artisan.id, type_=type_, destinataire=None, objet=objet, statut="sans_destinataire",
            client_id=client.id if client else None, devis_id=devis_id, facture_id=facture_id,
        )
    if not is_configured():
        logger.info("Email '%s' non envoye (fournisseur non configure) : destinataire=%s objet=%s", type_, destinataire, objet)
        return _log(
            db, artisan_id=artisan.id, type_=type_, destinataire=destinataire, objet=objet, statut="non_configure",
            client_id=client.id if client else None, devis_id=devis_id, facture_id=facture_id,
        )

    succes, provider_id, erreur = _send_raw(destinataire, objet, html)
    statut = "envoye" if succes else "echec"
    if not succes:
        logger.warning("Echec envoi email '%s' a %s : %s", type_, destinataire, erreur)
    return _log(
        db, artisan_id=artisan.id, type_=type_, destinataire=destinataire, objet=objet, statut=statut,
        erreur=erreur, provider_id=provider_id, client_id=client.id if client else None,
        devis_id=devis_id, facture_id=facture_id,
    )


def send_devis(db: Session, devis, artisan, url: str) -> EmailLog:
    objet, html = tpl.devis_email(devis, artisan, devis.client, url)
    return _envoyer(db, artisan, devis.client, "devis", objet, html, devis_id=devis.id)


def send_relance_devis(db: Session, devis, artisan, url: str, palier: int) -> EmailLog:
    objet, html = tpl.relance_devis_email(devis, artisan, devis.client, url, palier)
    return _envoyer(db, artisan, devis.client, "relance_devis", objet, html, devis_id=devis.id)


def send_facture(db: Session, facture, artisan, url: str) -> EmailLog:
    objet, html = tpl.facture_email(facture, artisan, facture.client, url)
    return _envoyer(db, artisan, facture.client, "facture", objet, html, facture_id=facture.id)


def send_relance_facture(db: Session, facture, artisan, url: str) -> EmailLog:
    objet, html = tpl.relance_facture_email(facture, artisan, facture.client, url)
    return _envoyer(db, artisan, facture.client, "relance_facture", objet, html, facture_id=facture.id)


def send_paiement_recu(db: Session, paiement, facture, artisan) -> EmailLog:
    objet, html = tpl.paiement_recu_email(paiement, facture, artisan, facture.client)
    return _envoyer(db, artisan, facture.client, "paiement_recu", objet, html, facture_id=facture.id)


def send_demande_avis(db: Session, artisan, client, url: str) -> EmailLog:
    objet, html = tpl.demande_avis_email(artisan, client, url)
    return _envoyer(db, artisan, client, "demande_avis", objet, html)


def send_nouvelle_demande_devis(db: Session, artisan, prospect) -> EmailLog:
    """Notifie l'artisan sans jamais confondre son adresse avec celle du prospect."""
    objet, html = tpl.nouvelle_demande_devis_email(artisan, prospect)
    destinataire = artisan.email
    log_args = {
        "artisan_id": artisan.id,
        "client_id": prospect.id,
        "type_": "nouvelle_demande_devis",
        "destinataire": destinataire,
        "objet": objet,
    }
    if not destinataire:
        return _log(db, **log_args, statut="sans_destinataire")
    if not is_configured():
        logger.info(
            "Email 'nouvelle_demande_devis' non envoye (fournisseur non configure) : destinataire=%s",
            destinataire,
        )
        return _log(db, **log_args, statut="non_configure")

    try:
        succes, provider_id, erreur = _send_raw(destinataire, objet, html)
    except Exception as exc:
        logger.exception("Echec inattendu de l'envoi de la nouvelle demande a %s", destinataire)
        return _log(db, **log_args, statut="echec", erreur=f"Erreur provider : {exc}"[:500])

    statut = "envoye" if succes else "echec"
    if not succes:
        logger.warning("Echec envoi nouvelle demande de devis a %s : %s", destinataire, erreur)
    return _log(db, **log_args, statut=statut, erreur=erreur, provider_id=provider_id)


def send_conformite_alerte(db: Session, artisan, item) -> EmailLog:
    """Notifie l'ARTISAN lui-meme (pas un client) : destinataire = son propre email."""
    objet, html = tpl.conformite_alerte_email(artisan, item)
    if not is_configured():
        return _log(db, artisan_id=artisan.id, type_="conformite_alerte", destinataire=artisan.email, objet=objet, statut="non_configure")
    succes, provider_id, erreur = _send_raw(artisan.email, objet, html)
    statut = "envoye" if succes else "echec"
    return _log(
        db, artisan_id=artisan.id, type_="conformite_alerte", destinataire=artisan.email, objet=objet,
        statut=statut, erreur=erreur, provider_id=provider_id,
    )
