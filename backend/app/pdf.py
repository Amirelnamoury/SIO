"""Generation de PDF (devis et factures) directement depuis le SaaS, sans
passer par le generateur de site (Partie 1) qui reste reserve a la
fabrication du site vitrine livre au client. Palette neutre coherente avec
le tableau de bord (pas liee au metier de l'artisan, contrairement aux
sites vitrine generes)."""

import calendar
import io
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Artisan, Devis, Facture

PRIMARY = HexColor("#1e293b")
PRIMARY_DARK = HexColor("#0f172a")


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _euros(montant: float) -> str:
    return f"{montant:,.2f} EUR".replace(",", " ").replace(".", ",")


def _styles():
    base = getSampleStyleSheet()["Normal"]
    return {
        "small": ParagraphStyle("small", parent=base, fontSize=8.5, leading=12, textColor=colors.HexColor("#444444")),
        "company": ParagraphStyle("company", parent=base, fontSize=15, leading=18, textColor=PRIMARY_DARK, fontName="Helvetica-Bold"),
        "title": ParagraphStyle("title", parent=base, fontSize=22, leading=26, textColor=PRIMARY, fontName="Helvetica-Bold", alignment=TA_RIGHT),
        "meta": ParagraphStyle("meta", parent=base, fontSize=9.5, leading=14, alignment=TA_RIGHT),
        "section": ParagraphStyle("section", parent=base, fontSize=10, leading=14, spaceBefore=6, spaceAfter=4, fontName="Helvetica-Bold", textColor=PRIMARY_DARK),
        "normal": base,
        "signature": ParagraphStyle("signature", parent=base, fontSize=9.5, leading=14),
    }


def _artisan_header(artisan: Artisan, styles) -> list:
    adresse = f"{artisan.adresse or ''}<br/>{artisan.code_postal or ''} {artisan.ville or ''}"
    return [
        Paragraph(artisan.nom_entreprise, styles["company"]),
        Paragraph(adresse, styles["small"]),
        Paragraph(f"Tel : {artisan.telephone or '-'}", styles["small"]),
        Paragraph(f"Email : {artisan.email}", styles["small"]),
        Paragraph(f"SIRET : {artisan.siret or '-'}", styles["small"]),
    ]


def _lignes_table(lignes: list, styles) -> Table:
    header = ["Description", "Qte", "Unite", "PU HT", "Total HT"]
    rows = [header]
    for ligne in lignes:
        rows.append([
            Paragraph(ligne.description, styles["normal"]),
            str(ligne.quantite), ligne.unite,
            _euros(ligne.prix_unitaire_ht), _euros(ligne.total_ht),
        ])
    table = Table(rows, colWidths=[7.5 * cm, 1.7 * cm, 2 * cm, 2.7 * cm, 2.9 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _signature_block(nom_entreprise: str, styles) -> Table:
    table = Table(
        [[
            Paragraph("Le client<br/>(date, signature precedee de \"Bon pour accord\")", styles["signature"]),
            Paragraph(f"{nom_entreprise}<br/>(cachet, signature)", styles["signature"]),
        ]],
        colWidths=[8.5 * cm, 8.5 * cm],
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 40),
        ("LINEABOVE", (0, 0), (0, 0), 0.5, colors.grey),
        ("LINEABOVE", (1, 0), (1, 0), 0.5, colors.grey),
    ]))
    return table


def generate_devis_pdf(devis: Devis, artisan: Artisan) -> bytes:
    styles = _styles()
    date_emission = devis.created_at.date()
    date_validite = _add_months(date_emission, 3)
    numero = devis.numero or f"DEV-{date_emission.year}-{devis.id:04d}"

    montant_ht = devis.montant_ht or 0.0
    montant_tva = round(montant_ht * devis.taux_tva / 100, 2)
    montant_ttc = round(montant_ht + montant_tva, 2)
    montant_acompte = round(montant_ttc * devis.acompte_pourcentage / 100, 2)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        title=f"Devis {numero}",
    )
    elements = []

    right_block = [
        Paragraph("DEVIS", styles["title"]),
        Paragraph(f"N&deg; {numero}", styles["meta"]),
        Paragraph(f"Date d'emission : {date_emission.strftime('%d/%m/%Y')}", styles["meta"]),
        Paragraph(f"Valable jusqu'au : {date_validite.strftime('%d/%m/%Y')}", styles["meta"]),
    ]
    header_table = Table([[_artisan_header(artisan, styles), right_block]], colWidths=[10 * cm, 7 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 2, PRIMARY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Devis etabli pour :", styles["section"]))
    client_lines = [devis.client.nom]
    if devis.client.adresse:
        client_lines.append(devis.client.adresse)
    if devis.client.telephone:
        client_lines.append(f"Tel : {devis.client.telephone}")
    if devis.client.email:
        client_lines.append(f"Email : {devis.client.email}")
    elements.append(Paragraph("<br/>".join(client_lines), styles["normal"]))
    elements.append(Spacer(1, 18))

    if devis.titre:
        elements.append(Paragraph(devis.titre, styles["section"]))
    elements.append(_lignes_table(devis.lignes, styles))
    elements.append(Spacer(1, 16))

    totaux_rows = [
        ["Total HT", _euros(montant_ht)],
        [f"TVA ({devis.taux_tva:.0f}%)", _euros(montant_tva)],
        ["Total TTC", _euros(montant_ttc)],
        [f"Acompte a la commande ({devis.acompte_pourcentage:.0f}%)", _euros(montant_acompte)],
    ]
    totaux_table = Table(totaux_rows, colWidths=[11.9 * cm, 3 * cm])
    totaux_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 2), (-1, 2), 12),
        ("LINEABOVE", (0, 2), (-1, 2), 1, PRIMARY_DARK),
        ("TEXTCOLOR", (0, 2), (-1, 2), PRIMARY_DARK),
    ]))
    elements.append(totaux_table)
    elements.append(Spacer(1, 22))

    elements.append(Paragraph("Mentions legales", styles["section"]))
    assurance = artisan.assurance_decennale_nom or "nous consulter"
    mentions = [
        f"Devis valable 3 mois a compter de sa date d'emission, soit jusqu'au {date_validite.strftime('%d/%m/%Y')}.",
        f"Acompte de {devis.acompte_pourcentage:.0f}% a la signature du present devis, solde exigible a la fin des travaux.",
        (
            f"TVA au taux reduit de 10% applicable aux travaux de renovation de logements acheves depuis plus de 2 "
            f"ans (article 279-0 bis du CGI)."
            if devis.taux_tva == 10 else
            "TVA au taux normal de 20% (travaux de construction neuve ou non eligibles au taux reduit)."
        ),
        (
            f"L'entreprise {artisan.nom_entreprise} est couverte par une assurance de responsabilite civile "
            f"decennale souscrite aupres de {assurance}, conformement a l'article L241-1 du Code des assurances."
        ),
        "En cas de litige non resolu directement, le client consommateur peut recourir gratuitement a un mediateur de la consommation.",
        "Bon pour accord : la signature de ce devis, precedee de la mention manuscrite \"Bon pour accord\", vaut acceptation ferme et definitive du present devis.",
    ]
    for mention in mentions:
        elements.append(Paragraph(f"&bull; {mention}", styles["small"]))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 28))
    elements.append(_signature_block(artisan.nom_entreprise, styles))

    doc.build(elements)
    return buffer.getvalue()


def generate_facture_pdf(facture: Facture, artisan: Artisan) -> bytes:
    styles = _styles()

    montant_tva = round(facture.montant_ht * facture.taux_tva / 100, 2)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        title=f"Facture {facture.numero}",
    )
    elements = []

    right_block = [
        Paragraph("FACTURE", styles["title"]),
        Paragraph(f"N&deg; {facture.numero}", styles["meta"]),
        Paragraph(f"Date d'emission : {facture.date_emission.strftime('%d/%m/%Y')}", styles["meta"]),
    ]
    if facture.date_echeance:
        right_block.append(Paragraph(f"Echeance : {facture.date_echeance.strftime('%d/%m/%Y')}", styles["meta"]))

    header_table = Table([[_artisan_header(artisan, styles), right_block]], colWidths=[10 * cm, 7 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 2, PRIMARY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Facture adressee a :", styles["section"]))
    client_lines = [facture.client.nom]
    if facture.client.adresse:
        client_lines.append(facture.client.adresse)
    if facture.client.email:
        client_lines.append(f"Email : {facture.client.email}")
    elements.append(Paragraph("<br/>".join(client_lines), styles["normal"]))
    elements.append(Spacer(1, 18))

    elements.append(_lignes_table(facture.lignes, styles))
    elements.append(Spacer(1, 16))

    totaux_rows = [
        ["Total HT", _euros(facture.montant_ht)],
        [f"TVA ({facture.taux_tva:.0f}%)", _euros(montant_tva)],
        ["Total TTC", _euros(facture.montant_ttc)],
    ]
    if facture.montant_paye > 0:
        totaux_rows.append(["Deja regle", _euros(facture.montant_paye)])
        totaux_rows.append(["Reste a payer", _euros(facture.montant_restant)])

    totaux_table = Table(totaux_rows, colWidths=[11.9 * cm, 3 * cm])
    style_cmds = [
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 2), (-1, 2), 12),
        ("LINEABOVE", (0, 2), (-1, 2), 1, PRIMARY_DARK),
        ("TEXTCOLOR", (0, 2), (-1, 2), PRIMARY_DARK),
    ]
    if facture.montant_paye > 0:
        style_cmds.append(("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"))
        style_cmds.append(("TEXTCOLOR", (0, 4), (-1, 4), colors.HexColor("#b91c1c")))
    totaux_table.setStyle(TableStyle(style_cmds))
    elements.append(totaux_table)
    elements.append(Spacer(1, 22))

    elements.append(Paragraph("Mentions legales", styles["section"]))
    mentions = [
        "Pas d'escompte pour paiement anticipe.",
        "En cas de retard de paiement, une indemnite forfaitaire pour frais de recouvrement de 40 EUR est due de "
        "plein droit (articles L441-10 et D441-5 du Code de commerce), ainsi que des penalites de retard au taux de "
        "3 fois le taux d'interet legal.",
    ]
    if facture.devis_id:
        mentions.insert(0, f"Facture etablie a partir du devis signe correspondant.")
    for mention in mentions:
        elements.append(Paragraph(f"&bull; {mention}", styles["small"]))
        elements.append(Spacer(1, 3))

    doc.build(elements)
    return buffer.getvalue()
