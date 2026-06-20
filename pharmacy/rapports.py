from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from django.http import HttpResponse
from datetime import date, datetime
from io import BytesIO

from .models import (
    Pharmacie, Medicament, LotStock, Vente, Inventaire, 
    BonCommande, Client
)


def _create_pdf_response(filename):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _header_style():
    styles = getSampleStyleSheet()
    title = ParagraphStyle("CustomTitle", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#1e40af"), spaceAfter=20)
    return styles, title


def rapport_stock(request):
    """Rapport complet du stock"""
    response = _create_pdf_response(f"rapport_stock_{date.today()}.pdf")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm)
    styles, title_style = _header_style()
    
    elements = []
    elements.append(Paragraph("RAPPORT DE STOCK", title_style))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    pharmacies = Pharmacie.objects.filter(actif=True)
    for pharm in pharmacies:
        elements.append(Paragraph(f"<b>{pharm.nom}</b> ({pharm.ville})", styles["Heading2"]))
        lots = LotStock.objects.filter(pharmacie=pharm, quantite__gt=0)
        
        if lots.exists():
            data = [["Medicament", "Lot", "Stock", "Expiration", "Prix"]]
            for lot in lots:
                data.append([
                    lot.medicament.nom,
                    lot.numero_lot,
                    str(lot.quantite),
                    lot.date_expiration.strftime("%d/%m/%Y"),
                    f"{lot.prix_achat} MAD",
                ])
            
            table = Table(data, colWidths=[5*cm, 3*cm, 2*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f3f4f6")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("<i>Aucun stock</i>", styles["Normal"]))
        
        elements.append(Spacer(1, 15))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def rapport_ventes(request):
    """Rapport des ventes"""
    response = _create_pdf_response(f"rapport_ventes_{date.today()}.pdf")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm)
    styles, title_style = _header_style()
    
    elements = []
    elements.append(Paragraph("RAPPORT DES VENTES", title_style))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    ventes = Vente.objects.filter(statut="validee").order_by("-date_vente")[:50]
    
    if ventes.exists():
        data = [["Code", "Pharmacie", "Client", "Date", "Montant TTC"]]
        total = 0
        for v in ventes:
            client_nom = f"{v.client.prenom} {v.client.nom}" if v.client else "Anonyme"
            data.append([
                v.code,
                v.pharmacie.nom if v.pharmacie else "-",
                client_nom,
                v.date_vente.strftime("%d/%m/%Y"),
                f"{v.total_ttc} MAD",
            ])
            total += float(v.total_ttc)
        
        data.append(["", "", "", "TOTAL", f"{total:.2f} MAD"])
        
        table = Table(data, colWidths=[2.5*cm, 4*cm, 4*cm, 2.5*cm, 3*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10b981")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (-3, -1), (-1, -1), colors.HexColor("#dcfce7")),
            ("FONTNAME", (-3, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("<i>Aucune vente</i>", styles["Normal"]))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def rapport_inventaire(request):
    """Rapport inventaires avec ecarts"""
    response = _create_pdf_response(f"rapport_inventaire_{date.today()}.pdf")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm)
    styles, title_style = _header_style()
    
    elements = []
    elements.append(Paragraph("RAPPORT D'INVENTAIRE", title_style))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    inventaires = Inventaire.objects.filter(statut="finalise").order_by("-date_creation")[:20]
    
    for inv in inventaires:
        pharm_nom = inv.pharmacie.nom if inv.pharmacie else "N/A"
        elements.append(Paragraph(f"<b>{inv.code}</b> - {pharm_nom}", styles["Heading3"]))
        
        lignes = inv.lignes.all()
        if lignes.exists():
            data = [["Medicament", "Systeme", "Reel", "Ecart"]]
            for l in lignes:
                ecart_str = f"+{l.ecart}" if l.ecart > 0 else str(l.ecart)
                data.append([
                    l.medicament.nom,
                    str(l.stock_systeme),
                    str(l.stock_reel),
                    ecart_str,
                ])
            
            table = Table(data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8b5cf6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]))
            elements.append(table)
        elements.append(Spacer(1, 15))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def facture_vente(request, vente_id):
    """Facture d'une vente specifique"""
    try:
        vente = Vente.objects.get(id=vente_id)
    except Vente.DoesNotExist:
        return HttpResponse("Vente introuvable", status=404)
    
    response = _create_pdf_response(f"facture_{vente.code}.pdf")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm)
    styles, title_style = _header_style()
    
    elements = []
    elements.append(Paragraph(f"FACTURE {vente.code}", title_style))
    elements.append(Paragraph(f"Date: {vente.date_vente.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    
    if vente.pharmacie:
        elements.append(Paragraph(f"<b>Pharmacie:</b> {vente.pharmacie.nom}", styles["Normal"]))
    if vente.client:
        elements.append(Paragraph(f"<b>Client:</b> {vente.client.prenom} {vente.client.nom}", styles["Normal"]))
    
    elements.append(Spacer(1, 20))
    
    data = [["Medicament", "Quantite", "Prix unit.", "Total"]]
    for l in vente.lignes.all():
        data.append([
            l.medicament.nom,
            str(l.quantite),
            f"{l.prix_unitaire} MAD",
            f"{l.total} MAD",
        ])
    
    data.append(["", "", "Total HT", f"{vente.total_ht} MAD"])
    data.append(["", "", "TVA", f"{vente.total_tva} MAD"])
    data.append(["", "", "Total TTC", f"{vente.total_ttc} MAD"])
    
    table = Table(data, colWidths=[6*cm, 2*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f59e0b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (-2, -1), (-1, -1), colors.HexColor("#fef3c7")),
        ("FONTNAME", (-2, -3), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(table)
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Mode de paiement:</b> {vente.mode_paiement}", styles["Normal"]))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def rapport_fefo(request):
    """Rapport FEFO - lots a risque expiration"""
    from datetime import timedelta
    response = _create_pdf_response(f"rapport_fefo_{date.today()}.pdf")
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm)
    styles, title_style = _header_style()
    
    elements = []
    elements.append(Paragraph("RAPPORT FEFO - LOTS PRIORITAIRES", title_style))
    elements.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    
    dans_90j = date.today() + timedelta(days=90)
    lots = LotStock.objects.filter(
        date_expiration__lte=dans_90j,
        quantite__gt=0
    ).order_by("date_expiration")
    
    if lots.exists():
        data = [["Medicament", "Lot", "Pharmacie", "Stock", "Expiration", "Jours"]]
        for lot in lots:
            jours = (lot.date_expiration - date.today()).days
            pharm = lot.pharmacie.nom if lot.pharmacie else "-"
            data.append([
                lot.medicament.nom,
                lot.numero_lot,
                pharm,
                str(lot.quantite),
                lot.date_expiration.strftime("%d/%m/%Y"),
                str(jours),
            ])
        
        table = Table(data, colWidths=[3.5*cm, 2.5*cm, 3.5*cm, 1.5*cm, 2.5*cm, 1.5*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ef4444")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("<i>Aucun lot a risque d'expiration</i>", styles["Normal"]))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
