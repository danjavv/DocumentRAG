#!/usr/bin/env python3
"""
Generate professional PDF documents from JSON data
"""

import json
from pathlib import Path
from datetime import datetime

# Install reportlab if needed
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
except ImportError:
    print("Installing reportlab...")
    import subprocess
    subprocess.check_call(["pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Paths
DATA_DIR = Path("data/synthetic")
PDF_DIR = DATA_DIR / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Load styles
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

header_style = ParagraphStyle(
    'CustomHeader',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#555555'),
    fontName='Helvetica-Bold'
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#1a1a1a'),
    fontName='Helvetica'
)


def create_po_pdf(po_data: dict, output_path: str):
    """Generate PDF for Purchase Order"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Title
    title = Paragraph("<b>PURCHASE ORDER</b>", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))

    # Company header (fake company)
    company_info = f"""
    <b>GLOBAL PROCUREMENT SYSTEMS INC.</b><br/>
    1234 Business Avenue, Suite 500<br/>
    New York, NY 10001<br/>
    Phone: (555) 123-4567 | Email: procurement@gps.com
    """
    company = Paragraph(company_info, normal_style)
    story.append(company)
    story.append(Spacer(1, 0.3*inch))

    # PO Details in table
    po_info_data = [
        [Paragraph("<b>PO Number:</b>", header_style),
         Paragraph(po_data['po_number'], normal_style),
         Paragraph("<b>PO Date:</b>", header_style),
         Paragraph(po_data['po_date'], normal_style)],
        [Paragraph("<b>Vendor:</b>", header_style),
         Paragraph(po_data['vendor_name'], normal_style),
         Paragraph("<b>Vendor ID:</b>", header_style),
         Paragraph(po_data['vendor_id'], normal_style)],
        [Paragraph("<b>Buyer:</b>", header_style),
         Paragraph(po_data['buyer_name'], normal_style),
         Paragraph("<b>Department:</b>", header_style),
         Paragraph(po_data['department'], normal_style)],
        [Paragraph("<b>Delivery Date:</b>", header_style),
         Paragraph(po_data['delivery_date'], normal_style),
         Paragraph("<b>Currency:</b>", header_style),
         Paragraph(po_data['currency'], normal_style)]
    ]

    po_table = Table(po_info_data, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    po_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(po_table)
    story.append(Spacer(1, 0.3*inch))

    # Delivery Address
    delivery = Paragraph(f"<b>Delivery Address:</b><br/>{po_data['delivery_address']}", normal_style)
    story.append(delivery)
    story.append(Spacer(1, 0.3*inch))

    # Line Items Header
    story.append(Paragraph("<b>ORDER DETAILS</b>", header_style))
    story.append(Spacer(1, 0.1*inch))

    # Line Items Table
    items_header = [[
        Paragraph("<b>Item Code</b>", header_style),
        Paragraph("<b>Description</b>", header_style),
        Paragraph("<b>Qty</b>", header_style),
        Paragraph("<b>Unit Price</b>", header_style),
        Paragraph("<b>Total</b>", header_style)
    ]]

    items_data = []
    for item in po_data['line_items']:
        items_data.append([
            Paragraph(item['item_code'], normal_style),
            Paragraph(item['description'], normal_style),
            Paragraph(str(item['quantity']), normal_style),
            Paragraph(f"${item['unit_price']:.2f}", normal_style),
            Paragraph(f"${item['total']:.2f}", normal_style)
        ])

    items_table = Table(items_header + items_data,
                       colWidths=[1*inch, 2.8*inch, 0.6*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (4, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F2F2F2')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))

    # Totals Table
    totals_data = [
        ['', '', '', Paragraph("<b>Subtotal:</b>", header_style),
         Paragraph(f"${po_data['subtotal']:.2f}", normal_style)],
        ['', '', '', Paragraph("<b>Tax:</b>", header_style),
         Paragraph(f"${po_data['tax']:.2f}", normal_style)],
        ['', '', '', Paragraph("<b>TOTAL:</b>", header_style),
         Paragraph(f"<b>${po_data['total_amount']:.2f}</b>", header_style)]
    ]

    totals_table = Table(totals_data, colWidths=[1*inch, 2.8*inch, 0.6*inch, 1*inch, 1*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (3, 2), (-1, 2), 2, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(totals_table)

    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer = Paragraph(
        "<i>This is a legally binding purchase order. Please confirm receipt and expected delivery date.</i>",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
    )
    story.append(footer)

    doc.build(story)


def create_invoice_pdf(invoice_data: dict, output_path: str):
    """Generate PDF for Invoice"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Title
    title = Paragraph("<b>INVOICE</b>", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))

    # Vendor header
    vendor_info = f"""
    <b>{invoice_data['vendor_name']}</b><br/>
    Vendor ID: {invoice_data['vendor_id']}<br/>
    Date: {invoice_data['invoice_date']}
    """
    vendor = Paragraph(vendor_info, normal_style)
    story.append(vendor)
    story.append(Spacer(1, 0.3*inch))

    # Invoice Details
    inv_info_data = [
        [Paragraph("<b>Invoice Number:</b>", header_style),
         Paragraph(invoice_data['invoice_number'], normal_style),
         Paragraph("<b>Invoice Date:</b>", header_style),
         Paragraph(invoice_data['invoice_date'], normal_style)],
        [Paragraph("<b>PO Reference:</b>", header_style),
         Paragraph(invoice_data['po_reference'], normal_style),
         Paragraph("<b>Due Date:</b>", header_style),
         Paragraph(invoice_data['due_date'], normal_style)],
        [Paragraph("<b>Payment Terms:</b>", header_style),
         Paragraph(invoice_data['payment_terms'], normal_style),
         Paragraph("<b>Currency:</b>", header_style),
         Paragraph(invoice_data['currency'], normal_style)]
    ]

    inv_table = Table(inv_info_data, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    inv_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(inv_table)
    story.append(Spacer(1, 0.3*inch))

    # Bill To
    bill_to = Paragraph(
        "<b>Bill To:</b><br/>Global Procurement Systems Inc.<br/>1234 Business Avenue, Suite 500<br/>New York, NY 10001",
        normal_style
    )
    story.append(bill_to)
    story.append(Spacer(1, 0.3*inch))

    # Line Items Header
    story.append(Paragraph("<b>ITEMIZED CHARGES</b>", header_style))
    story.append(Spacer(1, 0.1*inch))

    # Line Items Table
    items_header = [[
        Paragraph("<b>Item Code</b>", header_style),
        Paragraph("<b>Description</b>", header_style),
        Paragraph("<b>Qty</b>", header_style),
        Paragraph("<b>Unit Price</b>", header_style),
        Paragraph("<b>Total</b>", header_style)
    ]]

    items_data = []
    for item in invoice_data['line_items']:
        items_data.append([
            Paragraph(item['item_code'], normal_style),
            Paragraph(item['description'], normal_style),
            Paragraph(str(item['quantity']), normal_style),
            Paragraph(f"${item['unit_price']:.2f}", normal_style),
            Paragraph(f"${item['total']:.2f}", normal_style)
        ])

    items_table = Table(items_header + items_data,
                       colWidths=[1*inch, 2.8*inch, 0.6*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (4, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF2CC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))

    # Totals Table
    totals_data = [
        ['', '', '', Paragraph("<b>Subtotal:</b>", header_style),
         Paragraph(f"${invoice_data['subtotal']:.2f}", normal_style)],
        ['', '', '', Paragraph("<b>Tax:</b>", header_style),
         Paragraph(f"${invoice_data['tax']:.2f}", normal_style)],
        ['', '', '', Paragraph("<b>AMOUNT DUE:</b>", header_style),
         Paragraph(f"<b>${invoice_data['total_amount']:.2f}</b>", header_style)]
    ]

    totals_table = Table(totals_data, colWidths=[1*inch, 2.8*inch, 0.6*inch, 1*inch, 1*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (3, 2), (-1, 2), 2, colors.black),
        ('BACKGROUND', (3, 2), (-1, 2), colors.HexColor('#FFFF00')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(totals_table)

    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer = Paragraph(
        f"<i>Payment due by {invoice_data['due_date']}. Please remit payment to: Bank Account #12345-67890</i>",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
    )
    story.append(footer)

    doc.build(story)


def create_grn_pdf(grn_data: dict, output_path: str):
    """Generate PDF for Goods Received Note"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []

    # Title
    title = Paragraph("<b>GOODS RECEIVED NOTE</b>", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))

    # Company header
    company_info = f"""
    <b>GLOBAL PROCUREMENT SYSTEMS INC.</b><br/>
    Warehouse Operations<br/>
    1234 Business Avenue, Suite 500<br/>
    New York, NY 10001
    """
    company = Paragraph(company_info, normal_style)
    story.append(company)
    story.append(Spacer(1, 0.3*inch))

    # GRN Details
    grn_info_data = [
        [Paragraph("<b>GRN Number:</b>", header_style),
         Paragraph(grn_data['grn_number'], normal_style),
         Paragraph("<b>GRN Date:</b>", header_style),
         Paragraph(grn_data['grn_date'], normal_style)],
        [Paragraph("<b>PO Reference:</b>", header_style),
         Paragraph(grn_data['po_reference'], normal_style),
         Paragraph("<b>Vendor:</b>", header_style),
         Paragraph(grn_data['vendor_name'], normal_style)],
        [Paragraph("<b>Received By:</b>", header_style),
         Paragraph(grn_data['received_by'], normal_style),
         Paragraph("<b>Warehouse:</b>", header_style),
         Paragraph(grn_data['warehouse'], normal_style)]
    ]

    grn_table = Table(grn_info_data, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    grn_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(grn_table)
    story.append(Spacer(1, 0.3*inch))

    # Receipt Details Header
    story.append(Paragraph("<b>RECEIPT DETAILS</b>", header_style))
    story.append(Spacer(1, 0.1*inch))

    # Line Items Table
    items_header = [[
        Paragraph("<b>Item Code</b>", header_style),
        Paragraph("<b>Description</b>", header_style),
        Paragraph("<b>Received</b>", header_style),
        Paragraph("<b>Rejected</b>", header_style),
        Paragraph("<b>Condition</b>", header_style)
    ]]

    items_data = []
    for item in grn_data['line_items']:
        # Color code condition
        condition_text = item['condition']
        if item['quantity_rejected'] > 0:
            condition_para = Paragraph(f"<font color='red'><b>{condition_text}</b></font>", normal_style)
        else:
            condition_para = Paragraph(f"<font color='green'><b>{condition_text}</b></font>", normal_style)

        items_data.append([
            Paragraph(item['item_code'], normal_style),
            Paragraph(item['description'], normal_style),
            Paragraph(str(item['quantity_received']), normal_style),
            Paragraph(str(item['quantity_rejected']), normal_style),
            condition_para
        ])

    items_table = Table(items_header + items_data,
                       colWidths=[1*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#548235')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (3, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E2EFDA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)

    # Signature Section
    story.append(Spacer(1, 0.5*inch))
    signature_data = [
        [Paragraph("<b>Received By:</b>", header_style),
         Paragraph("_________________________", normal_style),
         Paragraph("<b>Date:</b>", header_style),
         Paragraph("_____________", normal_style)],
        ['', '', '', ''],
        [Paragraph("<b>Verified By:</b>", header_style),
         Paragraph("_________________________", normal_style),
         Paragraph("<b>Date:</b>", header_style),
         Paragraph("_____________", normal_style)]
    ]

    sig_table = Table(signature_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1.5*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(sig_table)

    # Footer
    story.append(Spacer(1, 0.3*inch))
    footer = Paragraph(
        "<i>This document confirms receipt of goods as described above. Any discrepancies must be reported within 24 hours.</i>",
        ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)
    )
    story.append(footer)

    doc.build(story)


def generate_all_pdfs():
    """Generate PDFs for all JSON documents"""
    print("\n" + "="*70)
    print("📄 PDF DOCUMENT GENERATION")
    print("="*70)

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

    total_docs = len(pos) + len(invoices) + len(grns)
    print(f"\n📊 Total Documents to Generate: {total_docs}")
    print("\n" + "-"*70)

    # Generate Purchase Order PDFs
    print("\n🔄 Generating Purchase Order PDFs...")
    for i, po in enumerate(pos, 1):
        output_path = PDF_DIR / f"{po['po_number']}.pdf"
        create_po_pdf(po, str(output_path))
        if i % 10 == 0:
            print(f"   ✓ Generated {i}/{len(pos)} POs...")
    print(f"   ✅ Completed {len(pos)} Purchase Order PDFs")

    # Generate Invoice PDFs
    print("\n🔄 Generating Invoice PDFs...")
    for i, invoice in enumerate(invoices, 1):
        output_path = PDF_DIR / f"{invoice['invoice_number']}.pdf"
        create_invoice_pdf(invoice, str(output_path))
        if i % 10 == 0:
            print(f"   ✓ Generated {i}/{len(invoices)} Invoices...")
    print(f"   ✅ Completed {len(invoices)} Invoice PDFs")

    # Generate GRN PDFs
    print("\n🔄 Generating Goods Received Note PDFs...")
    for i, grn in enumerate(grns, 1):
        output_path = PDF_DIR / f"{grn['grn_number']}.pdf"
        create_grn_pdf(grn, str(output_path))
        if i % 10 == 0:
            print(f"   ✓ Generated {i}/{len(grns)} GRNs...")
    print(f"   ✅ Completed {len(grns)} GRN PDFs")

    print("\n" + "="*70)
    print(f"✅ PDF GENERATION COMPLETE!")
    print("="*70)
    print(f"\n📁 Output Directory: {PDF_DIR}")
    print(f"📊 Total PDFs Generated: {total_docs}")
    print(f"\n   • Purchase Orders: {len(pos)} files")
    print(f"   • Invoices: {len(invoices)} files")
    print(f"   • Goods Received Notes: {len(grns)} files")

    # Show file size
    import os
    total_size = sum(os.path.getsize(PDF_DIR / f) for f in os.listdir(PDF_DIR) if f.endswith('.pdf'))
    print(f"\n💾 Total Size: {total_size / (1024*1024):.2f} MB")

    # Sample files
    print(f"\n📋 Sample Files Generated:")
    sample_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])[:5]
    for filename in sample_files:
        filepath = PDF_DIR / filename
        size = os.path.getsize(filepath) / 1024
        print(f"   • {filename} ({size:.1f} KB)")

    print("\n" + "="*70)
    print("🎉 Ready to use for demo!")
    print("="*70)
    print(f"\n💡 Next Steps:")
    print(f"   1. Open PDFs: open {PDF_DIR}/")
    print(f"   2. View sample: open {PDF_DIR}/PO-2024-01001.pdf")
    print(f"   3. Upload to data lake (Google Drive, S3, etc.)")
    print(f"   4. Test AI extraction on these PDFs")


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║              PDF DOCUMENT GENERATOR FOR DEMO                      ║
║                                                                   ║
║   Creating professional-looking Purchase Orders, Invoices,       ║
║   and Goods Received Notes from JSON data                        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")

    generate_all_pdfs()
