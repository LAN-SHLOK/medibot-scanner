from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import os
from datetime import datetime

# ==========================================
# 🎨 CYBERPUNK THEME COLORS
# ==========================================
CYBER_DARK = colors.HexColor("#020617")  # Deep Slate Background
CYBER_PANEL = colors.HexColor("#0f172a") # Lighter Panel
CYBER_BLUE = colors.HexColor("#06b6d4")  # Cyan Neon
CYBER_PINK = colors.HexColor("#db2777")  # Pink Neon
CYBER_TEXT = colors.HexColor("#e2e8f0")  # White/Grey Text
CYBER_DIM = colors.HexColor("#94a3b8")   # Dim Text

def draw_background(c, doc):
    """Draws the dark cyberpunk background on every page"""
    c.saveState()
    c.setFillColor(CYBER_DARK)
    c.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
    
    # Add Top & Bottom Neon Bars
    c.setLineWidth(4)
    c.setStrokeColor(CYBER_BLUE)
    c.line(0, A4[1] - 50, A4[0], A4[1] - 50)  # Top Bar
    
    c.setStrokeColor(CYBER_PINK)
    c.line(0, 50, A4[0], 50)  # Bottom Bar
    
    # Grid Effect
    c.setStrokeColor(colors.Color(1, 1, 1, alpha=0.05))
    c.setLineWidth(1)
    for i in range(0, int(A4[1]), 40):
        c.line(0, i, A4[0], i)
        
    # Footer Text
    c.setFont("Helvetica", 8)
    c.setFillColor(CYBER_DIM)
    c.drawCentredString(A4[0]/2, 30, "MEDIBOT AI • OFFICIAL DIAGNOSTIC REPORT • CONFIDENTIAL")
    c.restoreState()

def generate_official_pdf(verdict_data, lab_data=None, prescription_data=None, heatmap_path=None):
    """
    Generates a Cyberpunk-themed medical report.
    verdict_data: dict {'verdict', 'summary', 'severity_score'}
    lab_data: dict {'clinical_analysis': []}
    prescription_data: string (raw AI text) or list of dicts
    heatmap_path: Local path to the heatmap image
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=50, leftMargin=50, 
        topMargin=80, bottomMargin=80
    )

    styles = getSampleStyleSheet()
    
    # --- STYLES ---
    title_style = ParagraphStyle('CyberTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, textColor=CYBER_BLUE, alignment=TA_CENTER, spaceAfter=20)
    heading_style = ParagraphStyle('CyberHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=CYBER_PINK, spaceBefore=15, spaceAfter=10)
    text_style = ParagraphStyle('CyberText', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=CYBER_TEXT, leading=14)

    # Verdict Color Logic
    sev = verdict_data.get("severity_score", 1)
    v_color = colors.red if sev >= 4 else (colors.orange if sev == 3 else (colors.yellow if sev == 2 else colors.green))

    verdict_style = ParagraphStyle('VerdictBox', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=v_color, backColor=CYBER_PANEL, borderPadding=10, borderColor=v_color, borderWidth=1, alignment=TA_CENTER)

    elements = []

    # 1. HEADER
    elements.append(Paragraph("MEDIBOT AI DIAGNOSTICS", title_style))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d %b %Y, %H:%M')}", text_style))
    elements.append(Spacer(1, 20))

    # 2. DIAGNOSTIC VERDICT
    v_text = f"PRIMARY DIAGNOSIS: {verdict_data.get('verdict', 'UNKNOWN').upper()}"
    elements.append(Paragraph(v_text, verdict_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"SEVERITY TIER: {sev}/4", text_style))
    elements.append(Paragraph(f"SUMMARY: {verdict_data.get('summary', 'No summary available.')}", text_style))
    elements.append(Spacer(1, 20))

    # 3. VISUAL ANALYSIS (Heatmap)
    if heatmap_path and os.path.exists(heatmap_path):
        elements.append(Paragraph("VISUAL ATTENTION ANALYSIS", heading_style))
        try:
            img = Image(heatmap_path, width=4*inch, height=3*inch)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 10))
            elements.append(Paragraph("[ AI GENERATED ATTENTION MAP ]", 
                                     ParagraphStyle('Caption', parent=text_style, alignment=TA_CENTER, textColor=CYBER_BLUE, fontSize=8)))
        except Exception as e:
            elements.append(Paragraph(f"Image Load Error: {str(e)}", text_style))
        elements.append(Spacer(1, 20))

    # 4. CLINICAL MARKERS TABLE
    if lab_data and "clinical_analysis" in lab_data:
        elements.append(Paragraph("CLINICAL MARKERS", heading_style))
        data = [['MARKER', 'VALUE', 'STATUS']]
        for item in lab_data["clinical_analysis"]:
            tier = item.get("Tier", 1)
            status = "CRITICAL" if tier == 4 else ("Abnormal" if tier == 3 else "Normal")
            data.append([str(item.get("Marker", "")), str(item.get("Value", "")), status])

        table = Table(data, colWidths=[200, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), CYBER_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), CYBER_DARK),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), CYBER_PANEL),
            ('TEXTCOLOR', (0, 1), (-1, -1), CYBER_TEXT),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

    # 5. 💊 MEDICATION LEDGER (Prescription)
    if prescription_data:
        elements.append(Paragraph("OFFICIAL MEDICATION RECORD", heading_style))
        
        # Style for raw handwriting extraction box
        raw_box_style = ParagraphStyle(
            'RawBox',
            parent=text_style,
            backColor=CYBER_PANEL,
            borderPadding=15,
            borderColor=CYBER_PINK,
            borderWidth=1,
            leading=16,
            fontName='Helvetica-Bold'
        )

        if isinstance(prescription_data, str):
            # Preserves formatting from doc_to_text.py extraction
            formatted_raw_text = prescription_data.replace('\n', '<br/>')
            elements.append(Paragraph(f"<b>SCAN CAPTURE (RAW DATA):</b><br/><br/>{formatted_raw_text}", raw_box_style))
        else:
            # Table logic for structured medicine data
            p_rows = [['MEDICINE', 'DOSAGE', 'INSTRUCTIONS']]
            for med in prescription_data:
                p_rows.append([
                    Paragraph(str(med.get('medicine', 'N/A')), text_style),
                    str(med.get('dosage', 'PRN')),
                    Paragraph(str(med.get('instructions', med.get('timing', 'N/A'))), text_style)
                ])
            p_table = Table(p_rows, colWidths=[150, 80, 170])
            p_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), CYBER_PINK),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), CYBER_PANEL),
                ('TEXTCOLOR', (0, 1), (-1, -1), CYBER_TEXT),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(1,1,1, alpha=0.1)),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(p_table)
        elements.append(Spacer(1, 20))

    # 6. DISCLAIMER
    elements.append(Spacer(1, 30))
    disclaimer = "DISCLAIMER: This report is generated by an AI system (MediBot). It is intended for informational and triage purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed physician."
    elements.append(Paragraph(disclaimer, ParagraphStyle('Disclaimer', parent=text_style, fontSize=7, textColor=CYBER_DIM, alignment=TA_CENTER)))

    # Build PDF
    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
    
    buffer.seek(0)
    return buffer.read()