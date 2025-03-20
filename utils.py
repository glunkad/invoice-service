from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime


def generate_pdf(booking_data: dict) -> str:
    pdf_path = f"invoice_{booking_data['booking_id']}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        name="Title",
        fontSize=16,
        textColor=colors.darkred,
        spaceAfter=12,
        alignment=1
    )
    normal_style = styles["Normal"]
    subtitle_style = ParagraphStyle(
        name="Subtitle",
        fontSize=14,
        textColor=colors.black,
        spaceAfter=8,
        alignment=0
    )

    elements = []

    # Header Section
    elements.extend([
        Paragraph("Booking Confirmation", title_style),
        Paragraph(f"Booking ID: {booking_data['booking_id']}", normal_style),
        Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style),
        Spacer(1, 12)
    ])

    # Trip Overview Table
    check_in = datetime.fromisoformat(booking_data['check_in'])
    check_out = datetime.fromisoformat(booking_data['check_out'])

    elements.append(Paragraph("🏡 Trip Overview", subtitle_style))
    trip_data = [
        ["Guest:", booking_data['guest_name']],
        ["Property:", booking_data['property_name']],
        ["Location:", f"<a href='{booking_data['location']}'>View Map</a>"],
        ["Guests:", str(booking_data['guest_count'])],
        ["Check-in:", check_in.strftime('%B %d, %Y %I:%M %p')],
        ["Check-out:", check_out.strftime('%B %d, %Y %I:%M %p')]
    ]
    trip_table = Table(trip_data, colWidths=[150, 300])
    trip_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.extend([trip_table, Spacer(1, 12)])

    # Payment Details Table
    remaining = booking_data['total_amount'] - booking_data['amount_paid']
    elements.append(Paragraph("💳 Payment Details", subtitle_style))
    payment_data = [
        ["Total Amount:", f"${booking_data['total_amount']:,.2f}"],
        ["Amount Paid:", f"${booking_data['amount_paid']:,.2f}"],
        ["Remaining Balance:", f"${remaining:,.2f}"]
    ]
    payment_table = Table(payment_data, colWidths=[150, 300])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.extend([payment_table, Spacer(1, 12)])

    # Host and Cancellation Policy
    elements.extend([
        Paragraph("👤 Host", subtitle_style),
        Paragraph(booking_data['host_name'], normal_style),
        Spacer(1, 12),
        Paragraph("❗ Cancellation Policy", subtitle_style),
        Paragraph(booking_data['cancellation_policy'], normal_style)
    ])

    # Build PDF
    doc.build(elements)
    return pdf_path