"""
PDF Export Module.
Generates comprehensive trip reports with expenses, balances, and settlement plans.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from collections import defaultdict

def group_expenses_by_day(expenses):
    """
    Groups expenses by date.
    
    Args:
        expenses: List of expense objects
        
    Returns:
        List of tuples: [(date_str, day_display, [expenses])]
    """
    grouped = defaultdict(list)
    
    for expense in expenses:
        if expense.date:
            day_key = expense.date.strftime("%Y-%m-%d")
            grouped[day_key].append(expense)
    
    # Sort by date and create display format
    result = []
    for day_key in sorted(grouped.keys()):
        date_obj = datetime.strptime(day_key, "%Y-%m-%d")
        day_display = date_obj.strftime("%A, %B %d, %Y")
        result.append((day_key, day_display, grouped[day_key]))
    
    return result


def generate_trip_pdf(group, expenses, balances, settlements, place_tags, filepath):
    """
    Generates comprehensive trip PDF with all details.
    
    Args:
        group: Group object with name and members
        expenses: List of expenses
        balances: Member balances dict {member_id: amount}
        settlements: Simplified debts list [(payer_id, receiver_id, amount)]
        place_tags: Dict {expense_id: PlaceTag}
        filepath: Output PDF path
    """
    doc = SimpleDocTemplate(filepath, pagesize=A4, 
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003449'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#00A6A6'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    day_heading_style = ParagraphStyle(
        'DayHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#003449'),
        spaceAfter=8,
        spaceBefore=16
    )
    
    # Title
    story.append(Paragraph(f"🏖️ {group.name.upper()}", title_style))
    
    # Trip summary
    if expenses:
        start_date = min(exp.date for exp in expenses if exp.date).strftime("%B %d, %Y")
        end_date = max(exp.date for exp in expenses if exp.date).strftime("%B %d, %Y")
        story.append(Paragraph(f"{start_date} - {end_date}", styles['Normal']))
    
    story.append(Spacer(1, 0.5*cm))
    
    # Summary statistics
    total_spent = sum(exp.amount for exp in expenses)
    summary_data = [
        ['Total Spent:', f'Rs. {total_spent:,.2f}'],
        ['Members:', str(len(group.members))],
        ['Transactions:', str(len(expenses))]
    ]
    
    summary_table = Table(summary_data, colWidths=[4*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1A2B3C')),
    ]))
    story.append(summary_table)
    
    story.append(Spacer(1, 1*cm))
    story.append(PageBreak())
    
    # Day-wise expenses
    story.append(Paragraph("DAILY EXPENSES", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    daily_expenses = group_expenses_by_day(expenses)
    member_map = {m.id: m.member_name for m in group.members}
    
    for day_key, day_display, day_expenses in daily_expenses:
        # Day header
        story.append(Paragraph(f"📅 {day_display}", day_heading_style))
        
        # Expense table for this day
        expense_data = [['Time', 'Description', 'Place', 'Amount', 'Paid By']]
        day_total = 0
        
        for expense in day_expenses:
            time_str = expense.date.strftime("%I:%M %p") if expense.date else "-"
            place_name = ""
            
            # Get place tag if exists
            if expense.id in place_tags:
                place_tag = place_tags[expense.id]
                if place_tag.latitude and place_tag.longitude:
                    maps_url = f"https://maps.google.com/?q={place_tag.latitude},{place_tag.longitude}"
                    place_name = f'{place_tag.name} <link href="{maps_url}">[Map]</link>'
                else:
                    place_name = place_tag.name
            else:
                place_name = "-"
            
            payer_name = member_map.get(expense.payer_member_id, "Unknown")
            
            expense_data.append([
                time_str,
                expense.description,
                Paragraph(place_name, styles['Normal']),
                f"Rs. {expense.amount:,.2f}",
                payer_name
            ])
            day_total += expense.amount
        
        # Add day total
        expense_data.append([
            '', '', '', f'Rs. {day_total:,.2f}', ''
        ])
        
        expense_table = Table(expense_data, colWidths=[2*cm, 4*cm, 4.5*cm, 2.5*cm, 2.5*cm])
        expense_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003449')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F5F5F5')]),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E0F7F7')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
        ]))
        
        story.append(expense_table)
        story.append(Spacer(1, 0.8*cm))
    
    # Page break before balances
    story.append(PageBreak())
    
    # Member Balances
    story.append(Paragraph("MEMBER BALANCES", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    balance_data = [['Member', 'Balance', 'Status']]
    for member in group.members:
        balance = balances.get(member.id, 0)
        if balance > 0.01:
            status = f"Should receive Rs. {balance:,.2f}"
            status_color = colors.HexColor('#10B981')
        elif balance < -0.01:
            status = f"Should pay Rs. {abs(balance):,.2f}"
            status_color = colors.HexColor('#EF4444')
        else:
            status = "Settled ✓"
            status_color = colors.HexColor('#6B7280')
        
        balance_data.append([
            member.member_name,
            f"Rs. {balance:,.2f}",
            status
        ])
    
    balance_table = Table(balance_data, colWidths=[5*cm, 3*cm, 6*cm])
    balance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00A6A6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(balance_table)
    story.append(Spacer(1, 1*cm))
    
    # Settlement Plan
    story.append(Paragraph("SETTLEMENT PLAN", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    if settlements:
        settlement_data = [['From', 'To', 'Amount']]
        for payer_id, receiver_id, amount in settlements:
            payer_name = member_map.get(payer_id, "Unknown")
            receiver_name = member_map.get(receiver_id, "Unknown")
            settlement_data.append([
                payer_name,
                receiver_name,
                f"Rs. {amount:,.2f}"
            ])
        
        settlement_table = Table(settlement_data, colWidths=[5*cm, 5*cm, 4*cm])
        settlement_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00A6A6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#E0F7F7'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(settlement_table)
    else:
        story.append(Paragraph("✓ All members are settled! No payments needed.", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 2*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    story.append(Paragraph("SplitJourney - Travel Together, Split Smart", footer_style))
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated: {filepath}")
