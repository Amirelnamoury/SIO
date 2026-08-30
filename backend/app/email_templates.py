"""Templates email centralises (Jinja2). Un seul layout de base, un template
par type de message : c'est ici qu'on personnalise le ton/contenu des
communications transactionnelles, pas eparpille dans les routers."""

from jinja2 import Environment, BaseLoader, select_autoescape

_env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html"]))

_LAYOUT = """
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f4f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f4f0;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e2da;">
        <tr><td style="background:#16213e;padding:24px 32px;">
          <span style="color:#ffffff;font-weight:800;font-size:1.1rem;">{{ artisan_nom }}</span>
        </td></tr>
        <tr><td style="padding:32px;">
          {{ contenu | safe }}
        </td></tr>
        <tr><td style="padding:20px 32px;background:#f9f8f5;border-top:1px solid #e5e2da;">
          <p style="margin:0;font-size:0.78rem;color:#8a8578;line-height:1.5;">
            {{ artisan_nom }}{% if artisan_telephone %} &middot; {{ artisan_telephone }}{% endif %}{% if artisan_email %} &middot; {{ artisan_email }}{% endif %}
            {% if artisan_siret %}<br>SIRET {{ artisan_siret }}{% endif %}
          </p>
          <p style="margin:8px 0 0;font-size:0.72rem;color:#b0aa9a;">Envoye via Suite Artisan</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

_BTN = (
    '<a href="{url}" style="display:inline-block;background:#c1440e;color:#ffffff;text-decoration:none;'
    'font-weight:700;padding:13px 28px;border-radius:9px;margin-top:18px;">{label}</a>'
)


def _render(contenu: str, artisan) -> str:
    return _env.from_string(_LAYOUT).render(
        contenu=contenu, artisan_nom=artisan.nom_entreprise,
        artisan_telephone=artisan.telephone, artisan_email=artisan.email, artisan_siret=artisan.siret,
    )


def _fmt_euro(montant) -> str:
    if montant is None:
        return "-"
    return f"{montant:,.2f} €".replace(",", " ").replace(".", ",")


def devis_email(devis, artisan, client, url: str) -> tuple[str, str]:
    objet = f"Votre devis {devis.numero or ''} — {artisan.nom_entreprise}"
    contenu = f"""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour {client.nom},</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      {artisan.nom_entreprise} vous a etabli un devis{' pour "' + devis.titre + '"' if devis.titre else ''}.
    </p>
    <p style="font-size:1.4rem;font-weight:800;color:#16213e;margin:20px 0 4px;">{_fmt_euro(devis.montant_ttc)} <span style="font-size:0.8rem;font-weight:500;color:#8a8578;">TTC</span></p>
    {_BTN.format(url=url, label="Consulter le devis")}
    <p style="font-size:0.85rem;color:#8a8578;margin-top:24px;">Vous pouvez consulter le detail et donner votre accord directement en ligne.</p>
    """
    return objet, _render(contenu, artisan)


def relance_devis_email(devis, artisan, client, url: str, palier: int) -> tuple[str, str]:
    objet = f"Toujours interesse par notre devis {devis.numero or ''} ?"
    ton = "Petit rappel amical" if palier == 1 else ("Nous revenons vers vous" if palier == 2 else "Derniere relance")
    contenu = f"""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour {client.nom},</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      {ton} au sujet du devis{' "' + devis.titre + '"' if devis.titre else ''} que {artisan.nom_entreprise} vous a transmis.
      N'hesitez pas a nous contacter si vous avez des questions.
    </p>
    {_BTN.format(url=url, label="Revoir le devis")}
    """
    return objet, _render(contenu, artisan)


def facture_email(facture, artisan, client, url: str) -> tuple[str, str]:
    objet = f"Votre facture {facture.numero} — {artisan.nom_entreprise}"
    contenu = f"""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour {client.nom},</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">Voici votre facture {facture.numero}.</p>
    <p style="font-size:1.4rem;font-weight:800;color:#16213e;margin:20px 0 4px;">{_fmt_euro(facture.montant_ttc)} <span style="font-size:0.8rem;font-weight:500;color:#8a8578;">TTC</span></p>
    {f'<p style="font-size:0.85rem;color:#8a8578;">Echeance : {facture.date_echeance.strftime("%d/%m/%Y")}</p>' if facture.date_echeance else ''}
    {_BTN.format(url=url, label="Consulter la facture")}
    """
    return objet, _render(contenu, artisan)


def relance_facture_email(facture, artisan, client, url: str) -> tuple[str, str]:
    objet = f"Facture {facture.numero} — solde restant a regler"
    contenu = f"""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour {client.nom},</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      Sauf erreur de notre part, la facture {facture.numero} reste a regler pour un montant de
      <strong>{_fmt_euro(facture.montant_restant)}</strong>. Merci de bien vouloir regulariser cela.
    </p>
    {_BTN.format(url=url, label="Voir la facture")}
    """
    return objet, _render(contenu, artisan)


def paiement_recu_email(paiement, facture, artisan, client) -> tuple[str, str]:
    objet = f"Confirmation de paiement — facture {facture.numero}"
    contenu = f"""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour {client.nom},</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      Nous confirmons la bonne reception de votre paiement de <strong>{_fmt_euro(paiement.montant)}</strong>
      pour la facture {facture.numero}. Merci !
    </p>
    {f'<p style="font-size:0.85rem;color:#8a8578;">Reste a payer : {_fmt_euro(facture.montant_restant)}</p>' if facture.montant_restant > 0 else '<p style="font-size:0.85rem;color:#3a7d44;">Facture integralement reglee.</p>'}
    """
    return objet, _render(contenu, artisan)


def demande_avis_email(artisan, client, url: str) -> tuple[str, str]:
    objet = f"Votre avis compte pour {artisan.nom_entreprise}"
    contenu = f"""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour {client.nom},</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      Merci de faire confiance a {artisan.nom_entreprise}. Votre avis nous aide beaucoup :
      pourriez-vous prendre une minute pour le partager ?
    </p>
    {_BTN.format(url=url, label="Laisser un avis")}
    """
    return objet, _render(contenu, artisan)


def nouvelle_demande_devis_email(artisan, prospect) -> tuple[str, str]:
    objet = "Nouvelle demande de devis depuis votre site — Suite Artisan"
    contenu = _env.from_string("""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour {{ artisan_nom }},</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      Vous venez de recevoir une nouvelle demande de devis depuis votre site vitrine.
    </p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.7;">
      <strong>Nom :</strong> {{ prospect_nom }}<br>
      <strong>Email :</strong> {{ prospect_email or "Non renseigne" }}<br>
      <strong>Telephone :</strong> {{ prospect_telephone or "Non renseigne" }}
    </p>
    {% if prospect_message %}
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      <strong>Message :</strong><br>{{ prospect_message }}
    </p>
    {% endif %}
    <p style="font-size:0.85rem;color:#8a8578;">Retrouvez cette demande dans Suite Artisan.</p>
    """).render(
        artisan_nom=artisan.nom_entreprise,
        prospect_nom=prospect.nom,
        prospect_email=prospect.email,
        prospect_telephone=prospect.telephone,
        prospect_message=prospect.notes,
    )
    return objet, _render(contenu, artisan)


def conformite_alerte_email(artisan, item) -> tuple[str, str]:
    jours = (item.date_expiration - __import__("datetime").date.today()).days
    urgence = "a deja expire" if jours < 0 else f"expire dans {jours} jours"
    objet = f"A verifier : {item.libelle} {urgence}"
    contenu = f"""
    <p style="font-size:0.95rem;color:#2a2a28;">Bonjour,</p>
    <p style="font-size:0.95rem;color:#2a2a28;line-height:1.6;">
      Un element de conformite merite votre attention : <strong>{item.libelle}</strong> {urgence}
      ({item.date_expiration.strftime('%d/%m/%Y')}).
    </p>
    <p style="font-size:0.85rem;color:#8a8578;">Pensez a le mettre a jour dans Suite Artisan des que possible.</p>
    """
    return objet, _render(contenu, artisan)
