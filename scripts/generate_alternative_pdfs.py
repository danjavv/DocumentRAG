#!/usr/bin/env python3
"""
Generate alternative PDF layouts for Purchase Orders, Invoices, and GRNs
This creates different visual styles and formats from the original PDFs
"""

import json
from pathlib import Path
from datetime import datetime
import random

# Install reportlab if needed
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Frame, PageTemplate, KeepTogether
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
except ImportError:
    print("Installing reportlab...")
    import subprocess
    subprocess.check_call(["pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Frame, PageTemplate, KeepTogether
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# Paths
DATA_DIR = Path("data/synthetic")
PDF_DIR = DATA_DIR / "pdfs_alternative"
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Base styles
styles = getSampleStyleSheet()

# ==================== LAYOUT 1: MODERN MINIMALIST ====================

def create_modern_po_pdf(po_data: dict, output_path: str):
    """Modern minimalist Purchase Order - clean, lots of white space, no borders"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=1*inch, bottomMargin=1*inch,
                           leftMargin=1*inch, rightMargin=1*inch)
    story = []

    # Modern minimal title
    title_style = ParagraphStyle(
        'ModernTitle',
        fontSize=32,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=5,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontSize=10,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=30,
        fontName='Helvetica',
        alignment=TA_LEFT
    )

    header_style = ParagraphStyle(
        'ModernHeader',
        fontSize=8,
        textColor=colors.HexColor('#95A5A6'),
        fontName='Helvetica',
        spaceBefore=2,
        spaceAfter=2
    )

    value_style = ParagraphStyle(
        'ModernValue',
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
        fontName='Helvetica-Bold',
        spaceBefore=2,
        spaceAfter=10
    )

    # Title
    story.append(Paragraph("Purchase Order", title_style))
    story.append(Paragraph(po_data['po_number'], subtitle_style))
    story.append(Spacer(1, 0.3*inch))

    # Two-column layout for details
    left_column = []
    left_column.append(Paragraph("VENDOR", header_style))
    left_column.append(Paragraph(po_data['vendor_name'], value_style))
    left_column.append(Paragraph("BUYER", header_style))
    left_column.append(Paragraph(po_data['buyer_name'], value_style))
    left_column.append(Paragraph("DEPARTMENT", header_style))
    left_column.append(Paragraph(po_data['department'], value_style))

    right_column = []
    right_column.append(Paragraph("ORDER DATE", header_style))
    right_column.append(Paragraph(po_data['po_date'], value_style))
    right_column.append(Paragraph("DELIVERY DATE", header_style))
    right_column.append(Paragraph(po_data['delivery_date'], value_style))
    right_column.append(Paragraph("CURRENCY", header_style))
    right_column.append(Paragraph(po_data['currency'], value_style))

    # Create two-column table
    info_data = [[left_column, right_column]]
    info_table = Table(info_data, colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))

    # Delivery address
    story.append(Paragraph("DELIVERY ADDRESS", header_style))
    story.append(Paragraph(po_data['delivery_address'], value_style))
    story.append(Spacer(1, 0.3*inch))

    # Minimal line separator
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#ECF0F1')))
    story.append(Spacer(1, 0.2*inch))

    # Items header
    story.append(Paragraph("ORDER ITEMS", header_style))
    story.append(Spacer(1, 0.15*inch))

    # Items table - minimal style, no grid
    items_data = [[
        Paragraph("<b>ITEM</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'))),
        Paragraph("<b>DESCRIPTION</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'))),
        Paragraph("<b>QTY</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_RIGHT)),
        Paragraph("<b>PRICE</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_RIGHT)),
        Paragraph("<b>TOTAL</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_RIGHT))
    ]]

    item_style = ParagraphStyle('ItemText', fontSize=10, textColor=colors.HexColor('#2C3E50'))
    for item in po_data['line_items']:
        items_data.append([
            Paragraph(item['item_code'], item_style),
            Paragraph(item['description'], item_style),
            Paragraph(str(item['quantity']), ParagraphStyle('ItemNum', parent=item_style, alignment=TA_RIGHT)),
            Paragraph(f"${item['unit_price']:.2f}", ParagraphStyle('ItemNum', parent=item_style, alignment=TA_RIGHT)),
            Paragraph(f"${item['total']:.2f}", ParagraphStyle('ItemNum', parent=item_style, alignment=TA_RIGHT))
        ])

    items_table = Table(items_data, colWidths=[0.8*inch, 2.6*inch, 0.6*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))

    # Totals - right aligned, minimal
    totals_data = [
        ['', '', '', Paragraph("Subtotal", header_style), Paragraph(f"${po_data['subtotal']:.2f}", value_style)],
        ['', '', '', Paragraph("Tax", header_style), Paragraph(f"${po_data['tax']:.2f}", value_style)],
        ['', '', '', Paragraph("TOTAL", ParagraphStyle('TotalLabel', fontSize=11, textColor=colors.HexColor('#2C3E50'), fontName='Helvetica-Bold')),
         Paragraph(f"${po_data['total_amount']:.2f}", ParagraphStyle('TotalValue', fontSize=16, textColor=colors.HexColor('#2C3E50'), fontName='Helvetica-Bold'))]
    ]

    totals_table = Table(totals_data, colWidths=[0.8*inch, 2.6*inch, 0.6*inch, 1*inch, 1*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (3, 2), (-1, 2), 1, colors.HexColor('#2C3E50')),
        ('TOPPADDING', (0, 0), (-1, 1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 4),
        ('TOPPADDING', (0, 2), (-1, 2), 10),
    ]))
    story.append(totals_table)

    doc.build(story)


def create_modern_invoice_pdf(invoice_data: dict, output_path: str):
    """Modern minimalist Invoice"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=1*inch, bottomMargin=1*inch,
                           leftMargin=1*inch, rightMargin=1*inch)
    story = []

    # Styles
    title_style = ParagraphStyle('ModernTitle', fontSize=32, textColor=colors.HexColor('#E74C3C'),
                                 spaceAfter=5, fontName='Helvetica-Bold', alignment=TA_LEFT)
    subtitle_style = ParagraphStyle('Subtitle', fontSize=10, textColor=colors.HexColor('#95A5A6'),
                                   spaceAfter=30, fontName='Helvetica', alignment=TA_LEFT)
    header_style = ParagraphStyle('ModernHeader', fontSize=8, textColor=colors.HexColor('#95A5A6'),
                                 fontName='Helvetica', spaceBefore=2, spaceAfter=2)
    value_style = ParagraphStyle('ModernValue', fontSize=11, textColor=colors.HexColor('#2C3E50'),
                                fontName='Helvetica-Bold', spaceBefore=2, spaceAfter=10)

    # Title
    story.append(Paragraph("Invoice", title_style))
    story.append(Paragraph(invoice_data['invoice_number'], subtitle_style))
    story.append(Spacer(1, 0.3*inch))

    # Vendor and billing info in two columns
    left_column = []
    left_column.append(Paragraph("FROM", header_style))
    left_column.append(Paragraph(invoice_data['vendor_name'], value_style))
    left_column.append(Paragraph("PAYMENT TERMS", header_style))
    left_column.append(Paragraph(invoice_data['payment_terms'], value_style))

    right_column = []
    right_column.append(Paragraph("INVOICE DATE", header_style))
    right_column.append(Paragraph(invoice_data['invoice_date'], value_style))
    right_column.append(Paragraph("DUE DATE", header_style))
    right_column.append(Paragraph(invoice_data['due_date'], value_style))
    right_column.append(Paragraph("PO REFERENCE", header_style))
    right_column.append(Paragraph(invoice_data['po_reference'], value_style))

    info_data = [[left_column, right_column]]
    info_table = Table(info_data, colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))

    # Separator
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#ECF0F1')))
    story.append(Spacer(1, 0.2*inch))

    # Items
    story.append(Paragraph("INVOICE ITEMS", header_style))
    story.append(Spacer(1, 0.15*inch))

    items_data = [[
        Paragraph("<b>ITEM</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'))),
        Paragraph("<b>DESCRIPTION</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'))),
        Paragraph("<b>QTY</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_RIGHT)),
        Paragraph("<b>PRICE</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_RIGHT)),
        Paragraph("<b>TOTAL</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_RIGHT))
    ]]

    item_style = ParagraphStyle('ItemText', fontSize=10, textColor=colors.HexColor('#2C3E50'))
    for item in invoice_data['line_items']:
        items_data.append([
            Paragraph(item['item_code'], item_style),
            Paragraph(item['description'], item_style),
            Paragraph(str(item['quantity']), ParagraphStyle('ItemNum', parent=item_style, alignment=TA_RIGHT)),
            Paragraph(f"${item['unit_price']:.2f}", ParagraphStyle('ItemNum', parent=item_style, alignment=TA_RIGHT)),
            Paragraph(f"${item['total']:.2f}", ParagraphStyle('ItemNum', parent=item_style, alignment=TA_RIGHT))
        ])

    items_table = Table(items_data, colWidths=[0.8*inch, 2.6*inch, 0.6*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))

    # Totals with accent color
    totals_data = [
        ['', '', '', Paragraph("Subtotal", header_style), Paragraph(f"${invoice_data['subtotal']:.2f}", value_style)],
        ['', '', '', Paragraph("Tax", header_style), Paragraph(f"${invoice_data['tax']:.2f}", value_style)],
        ['', '', '', Paragraph("AMOUNT DUE", ParagraphStyle('TotalLabel', fontSize=11, textColor=colors.HexColor('#E74C3C'), fontName='Helvetica-Bold')),
         Paragraph(f"${invoice_data['total_amount']:.2f}", ParagraphStyle('TotalValue', fontSize=16, textColor=colors.HexColor('#E74C3C'), fontName='Helvetica-Bold'))]
    ]

    totals_table = Table(totals_data, colWidths=[0.8*inch, 2.6*inch, 0.6*inch, 1*inch, 1*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (3, 2), (-1, 2), 1, colors.HexColor('#E74C3C')),
        ('TOPPADDING', (0, 0), (-1, 1), 4),
        ('TOPPADDING', (0, 2), (-1, 2), 10),
    ]))
    story.append(totals_table)

    doc.build(story)


def create_modern_grn_pdf(grn_data: dict, output_path: str):
    """Modern minimalist GRN"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=1*inch, bottomMargin=1*inch,
                           leftMargin=1*inch, rightMargin=1*inch)
    story = []

    # Styles
    title_style = ParagraphStyle('ModernTitle', fontSize=32, textColor=colors.HexColor('#27AE60'),
                                 spaceAfter=5, fontName='Helvetica-Bold', alignment=TA_LEFT)
    subtitle_style = ParagraphStyle('Subtitle', fontSize=10, textColor=colors.HexColor('#95A5A6'),
                                   spaceAfter=30, fontName='Helvetica', alignment=TA_LEFT)
    header_style = ParagraphStyle('ModernHeader', fontSize=8, textColor=colors.HexColor('#95A5A6'),
                                 fontName='Helvetica', spaceBefore=2, spaceAfter=2)
    value_style = ParagraphStyle('ModernValue', fontSize=11, textColor=colors.HexColor('#2C3E50'),
                                fontName='Helvetica-Bold', spaceBefore=2, spaceAfter=10)

    # Title
    story.append(Paragraph("Goods Received", title_style))
    story.append(Paragraph(grn_data['grn_number'], subtitle_style))
    story.append(Spacer(1, 0.3*inch))

    # Info layout
    left_column = []
    left_column.append(Paragraph("VENDOR", header_style))
    left_column.append(Paragraph(grn_data['vendor_name'], value_style))
    left_column.append(Paragraph("RECEIVED BY", header_style))
    left_column.append(Paragraph(grn_data['received_by'], value_style))

    right_column = []
    right_column.append(Paragraph("RECEIPT DATE", header_style))
    right_column.append(Paragraph(grn_data['grn_date'], value_style))
    right_column.append(Paragraph("PO REFERENCE", header_style))
    right_column.append(Paragraph(grn_data['po_reference'], value_style))
    right_column.append(Paragraph("WAREHOUSE", header_style))
    right_column.append(Paragraph(grn_data['warehouse'], value_style))

    info_data = [[left_column, right_column]]
    info_table = Table(info_data, colWidths=[3.25*inch, 3.25*inch])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))

    # Separator
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#ECF0F1')))
    story.append(Spacer(1, 0.2*inch))

    # Items
    story.append(Paragraph("RECEIVED ITEMS", header_style))
    story.append(Spacer(1, 0.15*inch))

    items_data = [[
        Paragraph("<b>ITEM</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'))),
        Paragraph("<b>DESCRIPTION</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'))),
        Paragraph("<b>RECEIVED</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_CENTER)),
        Paragraph("<b>REJECTED</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_CENTER)),
        Paragraph("<b>STATUS</b>", ParagraphStyle('ItemHeader', fontSize=9, textColor=colors.HexColor('#7F8C8D'), alignment=TA_CENTER))
    ]]

    item_style = ParagraphStyle('ItemText', fontSize=10, textColor=colors.HexColor('#2C3E50'))
    for item in grn_data['line_items']:
        status_color = '#27AE60' if item['quantity_rejected'] == 0 else '#E74C3C'
        status_text = 'OK' if item['quantity_rejected'] == 0 else 'Issue'
        items_data.append([
            Paragraph(item['item_code'], item_style),
            Paragraph(item['description'], item_style),
            Paragraph(str(item['quantity_received']), ParagraphStyle('ItemNum', parent=item_style, alignment=TA_CENTER)),
            Paragraph(str(item['quantity_rejected']), ParagraphStyle('ItemNum', parent=item_style, alignment=TA_CENTER)),
            Paragraph(f"<font color='{status_color}'><b>{status_text}</b></font>", ParagraphStyle('Status', parent=item_style, alignment=TA_CENTER))
        ])

    items_table = Table(items_data, colWidths=[0.8*inch, 2.8*inch, 1*inch, 1*inch, 0.9*inch])
    items_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#BDC3C7')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)

    doc.build(story)


# ==================== LAYOUT 2: CLASSIC BORDERED ====================

def create_classic_po_pdf(po_data: dict, output_path: str):
    """Classic bordered Purchase Order - traditional business style"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Classic styles
    title_style = ParagraphStyle('ClassicTitle', fontSize=20, textColor=colors.black,
                                 spaceAfter=5, fontName='Times-Bold', alignment=TA_CENTER)

    # Header box with border
    header_data = [[
        Paragraph("<b>PURCHASE ORDER</b>", ParagraphStyle('BoxTitle', fontSize=16, fontName='Times-Bold', alignment=TA_CENTER))
    ]]
    header_table = Table(header_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F0F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))

    # Company info box
    company_data = [[
        Paragraph("<b>ISSUED BY:</b><br/>Global Procurement Systems Inc.<br/>1234 Business Avenue<br/>New York, NY 10001<br/>Tel: (555) 123-4567",
                 ParagraphStyle('ClassicText', fontSize=10, fontName='Times-Roman'))
    ]]
    company_table = Table(company_data, colWidths=[7*inch])
    company_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(company_table)
    story.append(Spacer(1, 0.15*inch))

    # PO details in bordered table
    detail_data = [
        [Paragraph("<b>PO Number:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['po_number'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Date:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['po_date'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
        [Paragraph("<b>Vendor:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['vendor_name'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Vendor ID:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['vendor_id'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
        [Paragraph("<b>Buyer:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['buyer_name'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Department:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['department'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
        [Paragraph("<b>Delivery Date:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['delivery_date'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Currency:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(po_data['currency'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
    ]

    detail_table = Table(detail_data, colWidths=[1.3*inch, 2*inch, 1.2*inch, 2.5*inch])
    detail_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8E8E8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#E8E8E8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.15*inch))

    # Delivery address
    delivery_data = [[
        Paragraph(f"<b>Delivery Address:</b><br/>{po_data['delivery_address']}",
                 ParagraphStyle('Address', fontSize=10, fontName='Times-Roman'))
    ]]
    delivery_table = Table(delivery_data, colWidths=[7*inch])
    delivery_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(delivery_table)
    story.append(Spacer(1, 0.2*inch))

    # Line items with full borders
    items_data = [[
        Paragraph("<b>Item Code</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Description</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Qty</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Unit Price</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Total</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER))
    ]]

    for item in po_data['line_items']:
        items_data.append([
            Paragraph(item['item_code'], ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman')),
            Paragraph(item['description'], ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman')),
            Paragraph(str(item['quantity']), ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_CENTER)),
            Paragraph(f"${item['unit_price']:.2f}", ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_RIGHT)),
            Paragraph(f"${item['total']:.2f}", ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_RIGHT))
        ])

    items_table = Table(items_data, colWidths=[1*inch, 2.7*inch, 0.8*inch, 1.2*inch, 1.3*inch])
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.1*inch))

    # Totals in bordered table
    totals_data = [
        ['', '', '', Paragraph("<b>Subtotal:</b>", ParagraphStyle('TotalLabel', fontSize=10, fontName='Times-Bold', alignment=TA_RIGHT)),
         Paragraph(f"${po_data['subtotal']:.2f}", ParagraphStyle('TotalValue', fontSize=10, fontName='Times-Roman', alignment=TA_RIGHT))],
        ['', '', '', Paragraph("<b>Tax:</b>", ParagraphStyle('TotalLabel', fontSize=10, fontName='Times-Bold', alignment=TA_RIGHT)),
         Paragraph(f"${po_data['tax']:.2f}", ParagraphStyle('TotalValue', fontSize=10, fontName='Times-Roman', alignment=TA_RIGHT))],
        ['', '', '', Paragraph("<b>GRAND TOTAL:</b>", ParagraphStyle('GrandTotal', fontSize=11, fontName='Times-Bold', alignment=TA_RIGHT)),
         Paragraph(f"<b>${po_data['total_amount']:.2f}</b>", ParagraphStyle('GrandTotalValue', fontSize=11, fontName='Times-Bold', alignment=TA_RIGHT))]
    ]

    totals_table = Table(totals_data, colWidths=[1*inch, 2.7*inch, 0.8*inch, 1.2*inch, 1.3*inch])
    totals_table.setStyle(TableStyle([
        ('BOX', (3, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (3, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (3, 2), (-1, 2), colors.HexColor('#FFE699')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)

    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer_data = [[
        Paragraph("<i>Terms & Conditions: This purchase order is subject to our standard terms and conditions. "
                 "Please acknowledge receipt and confirm delivery schedule within 24 hours.</i>",
                 ParagraphStyle('Footer', fontSize=8, fontName='Times-Italic'))
    ]]
    footer_table = Table(footer_data, colWidths=[7*inch])
    footer_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(footer_table)

    doc.build(story)


def create_classic_invoice_pdf(invoice_data: dict, output_path: str):
    """Classic bordered Invoice"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Header box
    header_data = [[
        Paragraph("<b>TAX INVOICE</b>", ParagraphStyle('BoxTitle', fontSize=18, fontName='Times-Bold', alignment=TA_CENTER))
    ]]
    header_table = Table(header_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF4E6')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))

    # Vendor info
    vendor_data = [[
        Paragraph(f"<b>FROM:</b><br/>{invoice_data['vendor_name']}<br/>Vendor ID: {invoice_data['vendor_id']}",
                 ParagraphStyle('VendorText', fontSize=10, fontName='Times-Roman'))
    ]]
    vendor_table = Table(vendor_data, colWidths=[7*inch])
    vendor_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFACD')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(vendor_table)
    story.append(Spacer(1, 0.15*inch))

    # Invoice details
    detail_data = [
        [Paragraph("<b>Invoice Number:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(invoice_data['invoice_number'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Invoice Date:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(invoice_data['invoice_date'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
        [Paragraph("<b>PO Reference:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(invoice_data['po_reference'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Due Date:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(invoice_data['due_date'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
        [Paragraph("<b>Payment Terms:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(invoice_data['payment_terms'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Currency:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(invoice_data['currency'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
    ]

    detail_table = Table(detail_data, colWidths=[1.3*inch, 2*inch, 1.2*inch, 2.5*inch])
    detail_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFE4B5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#FFE4B5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.2*inch))

    # Line items
    items_data = [[
        Paragraph("<b>Item Code</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Description</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Qty</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Unit Price</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Amount</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER))
    ]]

    for item in invoice_data['line_items']:
        items_data.append([
            Paragraph(item['item_code'], ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman')),
            Paragraph(item['description'], ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman')),
            Paragraph(str(item['quantity']), ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_CENTER)),
            Paragraph(f"${item['unit_price']:.2f}", ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_RIGHT)),
            Paragraph(f"${item['total']:.2f}", ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_RIGHT))
        ])

    items_table = Table(items_data, colWidths=[1*inch, 2.7*inch, 0.8*inch, 1.2*inch, 1.3*inch])
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFD700')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.1*inch))

    # Totals
    totals_data = [
        ['', '', '', Paragraph("<b>Subtotal:</b>", ParagraphStyle('TotalLabel', fontSize=10, fontName='Times-Bold', alignment=TA_RIGHT)),
         Paragraph(f"${invoice_data['subtotal']:.2f}", ParagraphStyle('TotalValue', fontSize=10, fontName='Times-Roman', alignment=TA_RIGHT))],
        ['', '', '', Paragraph("<b>Tax:</b>", ParagraphStyle('TotalLabel', fontSize=10, fontName='Times-Bold', alignment=TA_RIGHT)),
         Paragraph(f"${invoice_data['tax']:.2f}", ParagraphStyle('TotalValue', fontSize=10, fontName='Times-Roman', alignment=TA_RIGHT))],
        ['', '', '', Paragraph("<b>AMOUNT DUE:</b>", ParagraphStyle('GrandTotal', fontSize=12, fontName='Times-Bold', alignment=TA_RIGHT)),
         Paragraph(f"<b>${invoice_data['total_amount']:.2f}</b>", ParagraphStyle('GrandTotalValue', fontSize=12, fontName='Times-Bold', alignment=TA_RIGHT))]
    ]

    totals_table = Table(totals_data, colWidths=[1*inch, 2.7*inch, 0.8*inch, 1.2*inch, 1.3*inch])
    totals_table.setStyle(TableStyle([
        ('BOX', (3, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (3, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (3, 2), (-1, 2), colors.HexColor('#FFD700')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)

    # Payment info
    story.append(Spacer(1, 0.3*inch))
    payment_data = [[
        Paragraph(f"<b>Payment Instructions:</b><br/>Please remit payment by {invoice_data['due_date']}.<br/>"
                 "Bank Account: 12345-67890 | Routing: 123456789<br/>"
                 "Reference: " + invoice_data['invoice_number'],
                 ParagraphStyle('Payment', fontSize=9, fontName='Times-Roman'))
    ]]
    payment_table = Table(payment_data, colWidths=[7*inch])
    payment_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF9E6')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(payment_table)

    doc.build(story)


def create_classic_grn_pdf(grn_data: dict, output_path: str):
    """Classic bordered GRN"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Header
    header_data = [[
        Paragraph("<b>GOODS RECEIPT NOTE</b>", ParagraphStyle('BoxTitle', fontSize=18, fontName='Times-Bold', alignment=TA_CENTER))
    ]]
    header_table = Table(header_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))

    # Company info
    company_data = [[
        Paragraph("<b>RECEIVED AT:</b><br/>Global Procurement Systems Inc.<br/>Warehouse Operations<br/>1234 Business Avenue<br/>New York, NY 10001",
                 ParagraphStyle('CompanyText', fontSize=10, fontName='Times-Roman'))
    ]]
    company_table = Table(company_data, colWidths=[7*inch])
    company_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#C8E6C9')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(company_table)
    story.append(Spacer(1, 0.15*inch))

    # GRN details
    detail_data = [
        [Paragraph("<b>GRN Number:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(grn_data['grn_number'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Date:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(grn_data['grn_date'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
        [Paragraph("<b>PO Reference:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(grn_data['po_reference'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Vendor:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(grn_data['vendor_name'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
        [Paragraph("<b>Received By:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(grn_data['received_by'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman')),
         Paragraph("<b>Warehouse:</b>", ParagraphStyle('Label', fontSize=10, fontName='Times-Bold')),
         Paragraph(grn_data['warehouse'], ParagraphStyle('Value', fontSize=10, fontName='Times-Roman'))],
    ]

    detail_table = Table(detail_data, colWidths=[1.3*inch, 2*inch, 1.2*inch, 2.5*inch])
    detail_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#A5D6A7')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#A5D6A7')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 0.2*inch))

    # Line items
    items_data = [[
        Paragraph("<b>Item Code</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Description</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Received</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Rejected</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER)),
        Paragraph("<b>Condition</b>", ParagraphStyle('TableHeader', fontSize=10, fontName='Times-Bold', alignment=TA_CENTER))
    ]]

    for item in grn_data['line_items']:
        condition_text = item['condition']
        bg_color = colors.HexColor('#C8E6C9') if item['quantity_rejected'] == 0 else colors.HexColor('#FFCDD2')
        items_data.append([
            Paragraph(item['item_code'], ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman')),
            Paragraph(item['description'], ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman')),
            Paragraph(str(item['quantity_received']), ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_CENTER)),
            Paragraph(str(item['quantity_rejected']), ParagraphStyle('TableCell', fontSize=9, fontName='Times-Roman', alignment=TA_CENTER)),
            Paragraph(f"<b>{condition_text}</b>", ParagraphStyle('TableCell', fontSize=9, fontName='Times-Bold', alignment=TA_CENTER))
        ])

    items_table = Table(items_data, colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#81C784')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)

    # Signature section
    story.append(Spacer(1, 0.3*inch))
    sig_data = [
        [Paragraph("<b>Authorized Signatures:</b>", ParagraphStyle('SigHeader', fontSize=11, fontName='Times-Bold'))],
        [''],
        [Paragraph("Received By: _________________________   Date: _____________", ParagraphStyle('Sig', fontSize=10, fontName='Times-Roman'))],
        [''],
        [Paragraph("Verified By: _________________________   Date: _____________", ParagraphStyle('Sig', fontSize=10, fontName='Times-Roman'))],
        [''],
        [Paragraph("Warehouse Manager: __________________   Date: _____________", ParagraphStyle('Sig', fontSize=10, fontName='Times-Roman'))],
    ]

    sig_table = Table(sig_data, colWidths=[7*inch])
    sig_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sig_table)

    doc.build(story)


# ==================== LAYOUT 3: COLORFUL CREATIVE ====================

def create_creative_po_pdf(po_data: dict, output_path: str):
    """Creative colorful Purchase Order with modern asymmetric design"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Colorful accent color
    accent_color = colors.HexColor('#6366F1')  # Indigo

    # Creative title with colored background strip
    title_data = [[
        Paragraph("<b>PURCHASE ORDER</b>", ParagraphStyle('CreativeTitle', fontSize=24,
                 textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT))
    ]]
    title_table = Table(title_data, colWidths=[7*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.15*inch))

    # PO number in accent box
    po_num_data = [[
        Paragraph(f"<b>PO: {po_data['po_number']}</b>",
                 ParagraphStyle('PONum', fontSize=14, textColor=accent_color, fontName='Helvetica-Bold'))
    ]]
    po_num_table = Table(po_num_data, colWidths=[7*inch])
    po_num_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EEF2FF')),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTBORDER', (0, 0), (0, -1), 4, accent_color),
    ]))
    story.append(po_num_table)
    story.append(Spacer(1, 0.2*inch))

    # Info cards side by side
    label_style = ParagraphStyle('Label', fontSize=8, textColor=accent_color, fontName='Helvetica-Bold',
                                 spaceAfter=4, textTransform='uppercase')
    value_style = ParagraphStyle('Value', fontSize=11, textColor=colors.HexColor('#1F2937'),
                                 fontName='Helvetica', spaceAfter=12)

    # Left column
    left_info = [
        [Paragraph("VENDOR", label_style)],
        [Paragraph(po_data['vendor_name'], value_style)],
        [Paragraph("BUYER", label_style)],
        [Paragraph(po_data['buyer_name'], value_style)],
        [Paragraph("DEPARTMENT", label_style)],
        [Paragraph(po_data['department'], value_style)],
    ]

    left_table = Table(left_info, colWidths=[3.2*inch])
    left_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTBORDER', (0, 0), (0, -1), 3, colors.HexColor('#A5B4FC')),
    ]))

    # Right column
    right_info = [
        [Paragraph("ORDER DATE", label_style)],
        [Paragraph(po_data['po_date'], value_style)],
        [Paragraph("DELIVERY DATE", label_style)],
        [Paragraph(po_data['delivery_date'], value_style)],
        [Paragraph("CURRENCY", label_style)],
        [Paragraph(po_data['currency'], value_style)],
    ]

    right_table = Table(right_info, colWidths=[3.2*inch])
    right_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTBORDER', (0, 0), (0, -1), 3, colors.HexColor('#A5B4FC')),
    ]))

    # Combine columns
    info_container = Table([[left_table, right_table]], colWidths=[3.4*inch, 3.4*inch], spaceBefore=0, spaceAfter=0)
    story.append(info_container)
    story.append(Spacer(1, 0.15*inch))

    # Delivery address card
    delivery_card = [[
        Paragraph("DELIVERY ADDRESS", label_style),
    ], [
        Paragraph(po_data['delivery_address'], value_style)
    ]]

    delivery_table = Table(delivery_card, colWidths=[7*inch])
    delivery_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTBORDER', (0, 0), (0, -1), 3, colors.HexColor('#A5B4FC')),
    ]))
    story.append(delivery_table)
    story.append(Spacer(1, 0.25*inch))

    # Items section header
    items_header = [[
        Paragraph("ORDER ITEMS", ParagraphStyle('SectionHeader', fontSize=12, textColor=accent_color,
                 fontName='Helvetica-Bold'))
    ]]
    items_header_table = Table(items_header, colWidths=[7*inch])
    items_header_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 2, accent_color),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_header_table)
    story.append(Spacer(1, 0.1*inch))

    # Items table with alternating colors
    items_data = [[
        Paragraph("<b>ITEM</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph("<b>DESCRIPTION</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph("<b>QTY</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("<b>PRICE</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph("<b>TOTAL</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT))
    ]]

    cell_style = ParagraphStyle('CellText', fontSize=9, textColor=colors.HexColor('#374151'), fontName='Helvetica')
    for i, item in enumerate(po_data['line_items']):
        items_data.append([
            Paragraph(item['item_code'], cell_style),
            Paragraph(item['description'], cell_style),
            Paragraph(str(item['quantity']), ParagraphStyle('CellNum', parent=cell_style, alignment=TA_CENTER)),
            Paragraph(f"${item['unit_price']:.2f}", ParagraphStyle('CellNum', parent=cell_style, alignment=TA_RIGHT)),
            Paragraph(f"${item['total']:.2f}", ParagraphStyle('CellNum', parent=cell_style, alignment=TA_RIGHT))
        ])

    items_table = Table(items_data, colWidths=[0.9*inch, 2.8*inch, 0.7*inch, 1.2*inch, 1.4*inch])

    # Apply alternating row colors
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Alternating row colors
    for i in range(1, len(items_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F9FAFB')))
        else:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))

    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))

    # Totals with accent
    total_label_style = ParagraphStyle('TotalLabel', fontSize=10, textColor=colors.HexColor('#6B7280'),
                                       fontName='Helvetica', alignment=TA_RIGHT)
    total_value_style = ParagraphStyle('TotalValue', fontSize=10, textColor=colors.HexColor('#1F2937'),
                                       fontName='Helvetica-Bold', alignment=TA_RIGHT)
    grand_total_style = ParagraphStyle('GrandTotal', fontSize=16, textColor=colors.white,
                                       fontName='Helvetica-Bold', alignment=TA_RIGHT)

    totals_data = [
        ['', '', '', Paragraph("Subtotal:", total_label_style),
         Paragraph(f"${po_data['subtotal']:.2f}", total_value_style)],
        ['', '', '', Paragraph("Tax:", total_label_style),
         Paragraph(f"${po_data['tax']:.2f}", total_value_style)],
        ['', '', '', Paragraph("TOTAL", ParagraphStyle('GTLabel', fontSize=12, textColor=colors.white,
                              fontName='Helvetica-Bold', alignment=TA_RIGHT)),
         Paragraph(f"${po_data['total_amount']:.2f}", grand_total_style)]
    ]

    totals_table = Table(totals_data, colWidths=[0.9*inch, 2.8*inch, 0.7*inch, 1.2*inch, 1.4*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 6),
        ('TOPPADDING', (0, 2), (-1, 2), 12),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 12),
        ('BACKGROUND', (3, 2), (-1, 2), accent_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(totals_table)

    doc.build(story)


def create_creative_invoice_pdf(invoice_data: dict, output_path: str):
    """Creative colorful Invoice"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Colorful accent
    accent_color = colors.HexColor('#EC4899')  # Pink

    # Title
    title_data = [[
        Paragraph("<b>INVOICE</b>", ParagraphStyle('CreativeTitle', fontSize=26,
                 textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT))
    ]]
    title_table = Table(title_data, colWidths=[7*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.15*inch))

    # Invoice number
    inv_num_data = [[
        Paragraph(f"<b>{invoice_data['invoice_number']}</b>",
                 ParagraphStyle('InvNum', fontSize=14, textColor=accent_color, fontName='Helvetica-Bold'))
    ]]
    inv_num_table = Table(inv_num_data, colWidths=[7*inch])
    inv_num_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDF2F8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTBORDER', (0, 0), (0, -1), 4, accent_color),
    ]))
    story.append(inv_num_table)
    story.append(Spacer(1, 0.2*inch))

    # Info cards
    label_style = ParagraphStyle('Label', fontSize=8, textColor=accent_color, fontName='Helvetica-Bold',
                                 spaceAfter=4)
    value_style = ParagraphStyle('Value', fontSize=11, textColor=colors.HexColor('#1F2937'),
                                 fontName='Helvetica', spaceAfter=12)

    left_info = [
        [Paragraph("FROM", label_style)],
        [Paragraph(invoice_data['vendor_name'], value_style)],
        [Paragraph("PAYMENT TERMS", label_style)],
        [Paragraph(invoice_data['payment_terms'], value_style)],
    ]
    left_table = Table(left_info, colWidths=[3.2*inch])
    left_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDF2F8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTBORDER', (0, 0), (0, -1), 3, colors.HexColor('#F9A8D4')),
    ]))

    right_info = [
        [Paragraph("INVOICE DATE", label_style)],
        [Paragraph(invoice_data['invoice_date'], value_style)],
        [Paragraph("DUE DATE", label_style)],
        [Paragraph(invoice_data['due_date'], value_style)],
        [Paragraph("PO REFERENCE", label_style)],
        [Paragraph(invoice_data['po_reference'], value_style)],
    ]
    right_table = Table(right_info, colWidths=[3.2*inch])
    right_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDF2F8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTBORDER', (0, 0), (0, -1), 3, colors.HexColor('#F9A8D4')),
    ]))

    info_container = Table([[left_table, right_table]], colWidths=[3.4*inch, 3.4*inch])
    story.append(info_container)
    story.append(Spacer(1, 0.25*inch))

    # Items section
    items_header = [[
        Paragraph("INVOICE ITEMS", ParagraphStyle('SectionHeader', fontSize=12, textColor=accent_color,
                 fontName='Helvetica-Bold'))
    ]]
    items_header_table = Table(items_header, colWidths=[7*inch])
    items_header_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 2, accent_color),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_header_table)
    story.append(Spacer(1, 0.1*inch))

    # Items table
    items_data = [[
        Paragraph("<b>ITEM</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph("<b>DESCRIPTION</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph("<b>QTY</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("<b>PRICE</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph("<b>TOTAL</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT))
    ]]

    cell_style = ParagraphStyle('CellText', fontSize=9, textColor=colors.HexColor('#374151'), fontName='Helvetica')
    for item in invoice_data['line_items']:
        items_data.append([
            Paragraph(item['item_code'], cell_style),
            Paragraph(item['description'], cell_style),
            Paragraph(str(item['quantity']), ParagraphStyle('CellNum', parent=cell_style, alignment=TA_CENTER)),
            Paragraph(f"${item['unit_price']:.2f}", ParagraphStyle('CellNum', parent=cell_style, alignment=TA_RIGHT)),
            Paragraph(f"${item['total']:.2f}", ParagraphStyle('CellNum', parent=cell_style, alignment=TA_RIGHT))
        ])

    items_table = Table(items_data, colWidths=[0.9*inch, 2.8*inch, 0.7*inch, 1.2*inch, 1.4*inch])

    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    for i in range(1, len(items_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FDF2F8')))

    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))

    # Totals
    totals_data = [
        ['', '', '', Paragraph("Subtotal:", ParagraphStyle('TL', fontSize=10, alignment=TA_RIGHT)),
         Paragraph(f"${invoice_data['subtotal']:.2f}", ParagraphStyle('TV', fontSize=10, fontName='Helvetica-Bold', alignment=TA_RIGHT))],
        ['', '', '', Paragraph("Tax:", ParagraphStyle('TL', fontSize=10, alignment=TA_RIGHT)),
         Paragraph(f"${invoice_data['tax']:.2f}", ParagraphStyle('TV', fontSize=10, fontName='Helvetica-Bold', alignment=TA_RIGHT))],
        ['', '', '', Paragraph("AMOUNT DUE", ParagraphStyle('GTL', fontSize=12, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
         Paragraph(f"${invoice_data['total_amount']:.2f}", ParagraphStyle('GTV', fontSize=16, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT))]
    ]

    totals_table = Table(totals_data, colWidths=[0.9*inch, 2.8*inch, 0.7*inch, 1.2*inch, 1.4*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 6),
        ('TOPPADDING', (0, 2), (-1, 2), 12),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 12),
        ('BACKGROUND', (3, 2), (-1, 2), accent_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(totals_table)

    doc.build(story)


def create_creative_grn_pdf(grn_data: dict, output_path: str):
    """Creative colorful GRN"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Accent color
    accent_color = colors.HexColor('#10B981')  # Green

    # Title
    title_data = [[
        Paragraph("<b>GOODS RECEIVED</b>", ParagraphStyle('CreativeTitle', fontSize=24,
                 textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT))
    ]]
    title_table = Table(title_data, colWidths=[7*inch])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.15*inch))

    # GRN number
    grn_num_data = [[
        Paragraph(f"<b>GRN: {grn_data['grn_number']}</b>",
                 ParagraphStyle('GRNNum', fontSize=14, textColor=accent_color, fontName='Helvetica-Bold'))
    ]]
    grn_num_table = Table(grn_num_data, colWidths=[7*inch])
    grn_num_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTBORDER', (0, 0), (0, -1), 4, accent_color),
    ]))
    story.append(grn_num_table)
    story.append(Spacer(1, 0.2*inch))

    # Info cards
    label_style = ParagraphStyle('Label', fontSize=8, textColor=accent_color, fontName='Helvetica-Bold',
                                 spaceAfter=4)
    value_style = ParagraphStyle('Value', fontSize=11, textColor=colors.HexColor('#1F2937'),
                                 fontName='Helvetica', spaceAfter=12)

    left_info = [
        [Paragraph("VENDOR", label_style)],
        [Paragraph(grn_data['vendor_name'], value_style)],
        [Paragraph("RECEIVED BY", label_style)],
        [Paragraph(grn_data['received_by'], value_style)],
    ]
    left_table = Table(left_info, colWidths=[3.2*inch])
    left_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTBORDER', (0, 0), (0, -1), 3, colors.HexColor('#86EFAC')),
    ]))

    right_info = [
        [Paragraph("RECEIPT DATE", label_style)],
        [Paragraph(grn_data['grn_date'], value_style)],
        [Paragraph("PO REFERENCE", label_style)],
        [Paragraph(grn_data['po_reference'], value_style)],
        [Paragraph("WAREHOUSE", label_style)],
        [Paragraph(grn_data['warehouse'], value_style)],
    ]
    right_table = Table(right_info, colWidths=[3.2*inch])
    right_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ECFDF5')),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTBORDER', (0, 0), (0, -1), 3, colors.HexColor('#86EFAC')),
    ]))

    info_container = Table([[left_table, right_table]], colWidths=[3.4*inch, 3.4*inch])
    story.append(info_container)
    story.append(Spacer(1, 0.25*inch))

    # Items section
    items_header = [[
        Paragraph("RECEIVED ITEMS", ParagraphStyle('SectionHeader', fontSize=12, textColor=accent_color,
                 fontName='Helvetica-Bold'))
    ]]
    items_header_table = Table(items_header, colWidths=[7*inch])
    items_header_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 2, accent_color),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_header_table)
    story.append(Spacer(1, 0.1*inch))

    # Items table
    items_data = [[
        Paragraph("<b>ITEM</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph("<b>DESCRIPTION</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph("<b>RCV</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("<b>REJ</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("<b>STATUS</b>", ParagraphStyle('TableHeader', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER))
    ]]

    cell_style = ParagraphStyle('CellText', fontSize=9, textColor=colors.HexColor('#374151'), fontName='Helvetica')
    for item in grn_data['line_items']:
        if item['quantity_rejected'] == 0:
            status = Paragraph("<font color='#10B981'><b>✓ OK</b></font>", ParagraphStyle('Status', parent=cell_style, alignment=TA_CENTER))
        else:
            status = Paragraph("<font color='#EF4444'><b>✗ Issue</b></font>", ParagraphStyle('Status', parent=cell_style, alignment=TA_CENTER))

        items_data.append([
            Paragraph(item['item_code'], cell_style),
            Paragraph(item['description'], cell_style),
            Paragraph(str(item['quantity_received']), ParagraphStyle('CellNum', parent=cell_style, alignment=TA_CENTER)),
            Paragraph(str(item['quantity_rejected']), ParagraphStyle('CellNum', parent=cell_style, alignment=TA_CENTER)),
            status
        ])

    items_table = Table(items_data, colWidths=[0.9*inch, 2.8*inch, 0.8*inch, 0.8*inch, 1.7*inch])

    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), accent_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    for i in range(1, len(items_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ECFDF5')))

    items_table.setStyle(TableStyle(table_style))
    story.append(items_table)

    doc.build(story)


# ==================== MAIN GENERATION FUNCTION ====================

def generate_all_alternative_pdfs():
    """Generate all alternative PDF layouts"""
    print("\n" + "="*80)
    print("🎨 ALTERNATIVE PDF LAYOUT GENERATION")
    print("="*80)

    # Load JSON data
    print("\n📂 Loading JSON data...")
    with open(DATA_DIR / "purchase_orders.json", "r") as f:
        pos = json.load(f)
    print(f"   ✓ Loaded {len(pos)} Purchase Orders")

    with open(DATA_DIR / "invoices.json", "r") as f:
        invoices = json.load(f)
    print(f"   ✓ Loaded {len(invoices)} Invoices")

    with open(DATA_DIR / "grns.json", "r") as f:
        grns = json.load(f)
    print(f"   ✓ Loaded {len(grns)} Goods Received Notes")

    # Randomly assign layouts to documents
    layouts = ['modern', 'classic', 'creative']

    print("\n🎨 Generating PDFs with different layouts...")
    print("   • Modern Minimalist: Clean, lots of white space")
    print("   • Classic Bordered: Traditional business style")
    print("   • Creative Colorful: Modern with accent colors")
    print("\n" + "-"*80)

    # Generate POs with different layouts
    print("\n🔄 Generating Purchase Order PDFs...")
    for i, po in enumerate(pos, 1):
        layout = random.choice(layouts)
        filename = f"{po['po_number']}_{layout}.pdf"
        output_path = PDF_DIR / filename

        if layout == 'modern':
            create_modern_po_pdf(po, str(output_path))
        elif layout == 'classic':
            create_classic_po_pdf(po, str(output_path))
        else:  # creative
            create_creative_po_pdf(po, str(output_path))

        if i % 10 == 0:
            print(f"   ✓ Generated {i}/{len(pos)} POs...")
    print(f"   ✅ Completed {len(pos)} Purchase Order PDFs")

    # Generate Invoices
    print("\n🔄 Generating Invoice PDFs...")
    for i, invoice in enumerate(invoices, 1):
        layout = random.choice(layouts)
        filename = f"{invoice['invoice_number']}_{layout}.pdf"
        output_path = PDF_DIR / filename

        if layout == 'modern':
            create_modern_invoice_pdf(invoice, str(output_path))
        elif layout == 'classic':
            create_classic_invoice_pdf(invoice, str(output_path))
        else:  # creative
            create_creative_invoice_pdf(invoice, str(output_path))

        if i % 10 == 0:
            print(f"   ✓ Generated {i}/{len(invoices)} Invoices...")
    print(f"   ✅ Completed {len(invoices)} Invoice PDFs")

    # Generate GRNs
    print("\n🔄 Generating GRN PDFs...")
    for i, grn in enumerate(grns, 1):
        layout = random.choice(layouts)
        filename = f"{grn['grn_number']}_{layout}.pdf"
        output_path = PDF_DIR / filename

        if layout == 'modern':
            create_modern_grn_pdf(grn, str(output_path))
        elif layout == 'classic':
            create_classic_grn_pdf(grn, str(output_path))
        else:  # creative
            create_creative_grn_pdf(grn, str(output_path))

        if i % 10 == 0:
            print(f"   ✓ Generated {i}/{len(grns)} GRNs...")
    print(f"   ✅ Completed {len(grns)} GRN PDFs")

    # Statistics
    total_docs = len(pos) + len(invoices) + len(grns)
    print("\n" + "="*80)
    print(f"✅ ALTERNATIVE PDF GENERATION COMPLETE!")
    print("="*80)
    print(f"\n📁 Output Directory: {PDF_DIR}")
    print(f"📊 Total PDFs Generated: {total_docs}")
    print(f"\n   • Purchase Orders: {len(pos)} files")
    print(f"   • Invoices: {len(invoices)} files")
    print(f"   • Goods Received Notes: {len(grns)} files")

    # File size
    import os
    total_size = sum(os.path.getsize(PDF_DIR / f) for f in os.listdir(PDF_DIR) if f.endswith('.pdf'))
    print(f"\n💾 Total Size: {total_size / (1024*1024):.2f} MB")

    # Sample files
    print(f"\n📋 Sample Files Generated:")
    sample_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])[:6]
    for filename in sample_files:
        filepath = PDF_DIR / filename
        size = os.path.getsize(filepath) / 1024
        print(f"   • {filename} ({size:.1f} KB)")

    print("\n" + "="*80)
    print("🎉 Ready for demo with diverse PDF layouts!")
    print("="*80)
    print(f"\n💡 Next Steps:")
    print(f"   1. View samples: open {PDF_DIR}/")
    print(f"   2. Compare layouts - each document has a random layout")
    print(f"   3. Test AI extraction on these varied formats")
    print(f"   4. Demonstrates handling of diverse real-world PDFs")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║          ALTERNATIVE PDF LAYOUT GENERATOR                                ║
║                                                                          ║
║   Creating diverse PDF formats to simulate real-world variety           ║
║                                                                          ║
║   Layouts:                                                               ║
║   • Modern Minimalist - Clean, spacious, minimal borders                ║
║   • Classic Bordered - Traditional business with full borders           ║
║   • Creative Colorful - Modern design with accent colors                ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")

    generate_all_alternative_pdfs()
