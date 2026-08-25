"""Genere un devis PDF style pour un artisan BTP, avec les mentions legales
francaises obligatoires : TVA (10% renovation / 20% neuf, ou franchise en
base), acompte, validite 3 mois, assurance decennale.

Usage :
    from devis_pdf import generate_devis_pdf
    artisan = {
        "nom_entreprise": "Plomberie Dupont", "metier": "plombier",
        "adresse": "12 rue de Paris", "code_postal": "92100", "ville": "Boulogne-Billancourt",
        "telephone": "06 01 02 03 04", "email": "contact@plomberie-dupont.fr",
        "siret": "123 456 789 00012", "assurance_decennale_nom": "AXA",
    }
    devis = {
        "numero": "DEV-2026-0001",
        "client_nom": "Mme Petit", "client_adresse": "5 avenue Foch, 92100 Boulogne",
        "lignes": [
            {"description": "Remplacement chauffe-eau 200L", "quantite": 1, "unite": "forfait", "prix_unitaire_ht": 650},
            {"description": "Main d'oeuvre pose", "quantite": 3, "unite": "heure", "prix_unitaire_ht": 50},
        ],
        "taux_tva": 10,
        "acompte_pourcentage": 30,
    }
    generate_devis_pdf(devis, artisan, "devis.pdf")
"""

import calendar
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

from themes import get_theme


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _euros(montant: float) -> str:
    return f"{montant:,.2f} €".replace(",", " ").replace(".", ",")


def _build_lignes(devis: dict) -> list[dict]:
    if devis.get("lignes"):
        return devis["lignes"]
    return [
        {
            "description": devis.get("description") or "Prestation",
            "quantite": 1,
            "unite": "forfait",
            "prix_unitaire_ht": devis.get("montant_ht") or 0,
        }
    ]


def generate_devis_pdf(devis: dict, artisan: dict, output_path: str) -> str:
    theme = get_theme(artisan.get("metier", "general"))
    primary = HexColor(theme["primary"])
    primary_dark = HexColor(theme["primary_dark"])

    date_emission = devis.get("date_emission") or date.today()
    if isinstance(date_emission, str):
        date_emission = date.fromisoformat(date_emission)
    date_validite = add_months(date_emission, 3)

    if devis.get("numero"):
        numero = devis["numero"]
    elif isinstance(devis.get("id"), int):
        numero = f"DEV-{date_emission.year}-{devis['id']:04d}"
    else:
        numero = f"DEV-{date_emission.strftime('%Y%m%d')}"

    lignes = _build_lignes(devis)
    total_ht = sum(l["quantite"] * l["prix_unitaire_ht"] for l in lignes)

    franchise_tva = artisan.get("franchise_tva", False)
    taux_tva = 0 if franchise_tva else devis.get("taux_tva", 10)
    montant_tva = round(total_ht * taux_tva / 100, 2)
    total_ttc = round(total_ht + montant_tva, 2)

    acompte_pct = devis.get("acompte_pourcentage", 30)
    montant_acompte = round(total_ttc * acompte_pct / 100, 2)

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_small = ParagraphStyle("small", parent=style_normal, fontSize=8.5, leading=12, textColor=colors.HexColor("#444444"))
    style_company = ParagraphStyle("company", parent=style_normal, fontSize=15, leading=18, textColor=primary_dark, fontName="Helvetica-Bold")
    style_title = ParagraphStyle("title", parent=style_normal, fontSize=22, leading=26, textColor=primary, fontName="Helvetica-Bold", alignment=TA_RIGHT)
    style_meta = ParagraphStyle("meta", parent=style_normal, fontSize=9.5, leading=14, alignment=TA_RIGHT)
    style_section = ParagraphStyle("section", parent=style_normal, fontSize=10, leading=14, spaceBefore=6, spaceAfter=4, fontName="Helvetica-Bold", textColor=primary_dark)
    style_signature = ParagraphStyle("signature", parent=style_normal, fontSize=9.5, leading=14)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        title=f"Devis {numero}",
    )

    elements = []

    # --- En-tete : coordonnees artisan (gauche) / DEVIS + numero + dates (droite) ---
    adresse_artisan = f"{artisan.get('adresse', '')}<br/>{artisan.get('code_postal', '')} {artisan.get('ville', '')}"
    left_block = [
        Paragraph(artisan["nom_entreprise"], style_company),
        Paragraph(adresse_artisan, style_small),
        Paragraph(f"Tel : {artisan.get('telephone', '-')}", style_small),
        Paragraph(f"Email : {artisan.get('email', '-')}", style_small),
        Paragraph(f"SIRET : {artisan.get('siret', '-')}", style_small),
    ]
    right_block = [
        Paragraph("DEVIS", style_title),
        Paragraph(f"N&deg; {numero}", style_meta),
        Paragraph(f"Date d'emission : {date_emission.strftime('%d/%m/%Y')}", style_meta),
        Paragraph(f"Valable jusqu'au : {date_validite.strftime('%d/%m/%Y')}", style_meta),
    ]

    header_table = Table([[left_block, right_block]], colWidths=[10 * cm, 7 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 2, primary),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 16))

    # --- Bloc client ---
    elements.append(Paragraph("Devis etabli pour :", style_section))
    client_lines = [devis.get("client_nom", "")]
    if devis.get("client_adresse"):
        client_lines.append(devis["client_adresse"])
    if devis.get("client_telephone"):
        client_lines.append(f"Tel : {devis['client_telephone']}")
    if devis.get("client_email"):
        client_lines.append(f"Email : {devis['client_email']}")
    elements.append(Paragraph("<br/>".join(client_lines), style_normal))
    elements.append(Spacer(1, 18))

    # --- Tableau des prestations ---
    table_header = ["Description", "Qte", "Unite", "PU HT", "Total HT"]
    table_rows = [table_header]
    for ligne in lignes:
        total_ligne = ligne["quantite"] * ligne["prix_unitaire_ht"]
        table_rows.append([
            Paragraph(ligne["description"], style_normal),
            str(ligne["quantite"]),
            ligne.get("unite", "u"),
            _euros(ligne["prix_unitaire_ht"]),
            _euros(total_ligne),
        ])

    lignes_table = Table(table_rows, colWidths=[7.5 * cm, 1.7 * cm, 2 * cm, 2.7 * cm, 2.9 * cm])
    lignes_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
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
    elements.append(lignes_table)
    elements.append(Spacer(1, 16))

    # --- Totaux ---
    tva_label = "TVA non applicable (art. 293 B du CGI)" if franchise_tva else f"TVA ({taux_tva:.0f}%)"
    totaux_rows = [
        ["Total HT", _euros(total_ht)],
        [tva_label, _euros(montant_tva)],
        ["Total TTC", _euros(total_ttc)],
        [f"Acompte a la commande ({acompte_pct:.0f}%)", _euros(montant_acompte)],
    ]
    totaux_table = Table(totaux_rows, colWidths=[11.9 * cm, 3 * cm])
    totaux_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 2), (-1, 2), 12),
        ("LINEABOVE", (0, 2), (-1, 2), 1, primary_dark),
        ("TEXTCOLOR", (0, 2), (-1, 2), primary_dark),
    ]))
    elements.append(totaux_table)
    elements.append(Spacer(1, 22))

    # --- Mentions legales obligatoires ---
    elements.append(Paragraph("Mentions legales", style_section))
    assurance = artisan.get("assurance_decennale_nom") or "nous consulter"
    mentions = [
        f"Devis valable 3 mois a compter de sa date d'emission, soit jusqu'au {date_validite.strftime('%d/%m/%Y')}.",
        f"Acompte de {acompte_pct:.0f}% a la signature du present devis, solde exigible a la fin des travaux.",
        (
            "TVA non applicable, article 293 B du Code general des impots (franchise en base de TVA)."
            if franchise_tva else
            (
                f"TVA au taux reduit de 10% applicable aux travaux de renovation de logements acheves depuis plus "
                f"de 2 ans (article 279-0 bis du CGI)."
                if taux_tva == 10 else
                f"TVA au taux normal de 20% (travaux de construction neuve ou non eligibles au taux reduit)."
            )
        ),
        (
            f"L'entreprise {artisan['nom_entreprise']} est couverte par une assurance de responsabilite civile "
            f"decennale souscrite aupres de {assurance}, conformement a l'article L241-1 du Code des assurances."
        ),
        "En cas de litige non resolu directement, le client consommateur peut recourir gratuitement a un mediateur de la consommation.",
        "Bon pour accord : la signature de ce devis, precedee de la mention manuscrite \"Bon pour accord\", vaut acceptation ferme et definitive du present devis.",
    ]
    for mention in mentions:
        elements.append(Paragraph(f"&bull; {mention}", style_small))
        elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 28))

    # --- Signatures ---
    signature_table = Table(
        [[
            Paragraph("Le client<br/>(date, signature precedee de \"Bon pour accord\")", style_signature),
            Paragraph(f"{artisan['nom_entreprise']}<br/>(cachet, signature)", style_signature),
        ]],
        colWidths=[8.5 * cm, 8.5 * cm],
    )
    signature_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 40),
        ("LINEABOVE", (0, 0), (0, 0), 0.5, colors.grey),
        ("LINEABOVE", (1, 0), (1, 0), 0.5, colors.grey),
    ]))
    elements.append(signature_table)

    doc.build(elements)
    return output_path


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Genere un devis PDF pour un artisan")
    parser.add_argument("artisan_json", help="Fichier JSON avec les infos de l'artisan")
    parser.add_argument("devis_json", help="Fichier JSON avec les infos du devis")
    parser.add_argument("--output", default="devis.pdf", help="Fichier PDF de sortie")
    args = parser.parse_args()

    with open(args.artisan_json, encoding="utf-8") as f:
        artisan_data = json.load(f)
    with open(args.devis_json, encoding="utf-8") as f:
        devis_data = json.load(f)

    generate_devis_pdf(devis_data, artisan_data, args.output)
    print(f"Devis genere : {args.output}")
