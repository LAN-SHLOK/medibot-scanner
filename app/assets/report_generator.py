from fpdf import FPDF
import datetime
import re

# ------------------------------------------------------------------
# OPTIONAL METADATA (NOT USED IN LOGIC — FOR FUTURE AUDIT / VERSIONING)
# ------------------------------------------------------------------
REPORT_GENERATOR_VERSION = "1.0.0"
REPORT_GENERATED_BY = "MediBot Pro AI"

# --- HELPER: REMOVE EMOJIS FOR PDF COMPATIBILITY ---
def clean_text(text):
    """
    Removes emojis and special characters that crash FPDF (Latin-1).
    Replaces common issues like smart quotes.
    """
    if not isinstance(text, str): 
        return str(text)
    
    # 1. Remove Emojis (Regex for range of emoji characters)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # 2. Replace Smart Quotes/Dashes
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    return text.strip()

# ------------------------------------------------------------------
# OPTIONAL HELPER (NOT USED BY DEFAULT)
# For future-proof verdict keyword matching
# ------------------------------------------------------------------
def normalize_verdict_text(verdict_text):
    """
    Normalizes verdict text for keyword matching.
    Currently unused — provided for future extensions.
    """
    if not verdict_text:
        return ""
    return clean_text(verdict_text).upper()

# ------------------------------------------------------------------
# OPTIONAL HELPER (NOT USED BY DEFAULT)
# Prevents long values from breaking table layout
# ------------------------------------------------------------------
def safe_truncate(text, limit=35):
    """
    Safely truncates long strings.
    Not wired into logic — optional future use.
    """
    text = clean_text(text)
    return text if len(text) <= limit else text[:limit - 3] + "..."

class PDFReport(FPDF):
    def header(self):
        # Professional Header
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'MediBot Pro: AI Diagnostic Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Powered by Advanced AI Vision & Biochemical Analysis', 0, 1, 'C')
        self.line(10, 30, 200, 30)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(
            0,
            10,
            f'Page {self.page_no()} - Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}',
            0,
            0,
            'C'
        )

def generate_official_pdf(master_report, structured_data, filename="report.pdf"):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. FINAL VERDICT SECTION
    pdf.set_font("Arial", "B", 16)
    
    # Clean the verdict text (Remove 🚨/⚠️)
    verdict_text = clean_text(master_report.get('verdict', 'Unknown'))
    
    # Determine Color
    if "CRITICAL" in verdict_text or "HIGH" in verdict_text:
        pdf.set_text_color(255, 0, 0)  # Red
    elif "RISKY" in verdict_text or "ABNORMAL" in verdict_text:
        pdf.set_text_color(255, 165, 0)  # Orange
    else:
        pdf.set_text_color(0, 128, 0)  # Green

    pdf.cell(0, 10, f"FINAL VERDICT: {verdict_text}", 0, 1, 'C')
    
    pdf.set_text_color(0, 0, 0)  # Reset to black
    pdf.set_font("Arial", "", 12)
    
    # Clean the summary text
    summary_text = clean_text(master_report.get('summary', 'No summary available.'))
    summary_text = summary_text.replace("**", "")  # Remove markdown bolding
    
    pdf.multi_cell(0, 10, f"Summary: {summary_text}")
    pdf.ln(10)

    # 2. CLINICAL FINDINGS TABLE
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "Detailed Clinical Findings", 0, 1, 'L', fill=True)
    pdf.ln(5)

    # Headers
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 10, "Marker / Condition", 1)
    pdf.cell(40, 10, "Value / Type", 1)
    pdf.cell(70, 10, "Status / Triage", 1)
    pdf.ln()

    # Data Rows
    pdf.set_font("Arial", "", 10)
    
    # Add Lab Data (if any)
    for item in structured_data.get("clinical_analysis", []):
        marker = clean_text(str(item.get("Marker", "Unknown")))[:35]
        val = clean_text(str(item.get("Value", "N/A")))
        tier = item.get("Tier", 1)
        
        status_label = "Normal"
        if tier == 4:
            status_label = "CRITICAL (Tier 4)"
        elif tier == 3:
            status_label = "URGENT (Tier 3)"
        
        # Color code the rows for criticals
        if tier >= 3:
            pdf.set_text_color(200, 0, 0)
        else:
            pdf.set_text_color(0, 0, 0)
        
        pdf.cell(80, 10, marker, 1)
        pdf.cell(40, 10, val, 1)
        pdf.cell(70, 10, status_label, 1)
        pdf.ln()

    # Add Imaging Data if available
    img_label = clean_text(master_report.get('imaging_brief', 'None'))
    if img_label and img_label != "Unknown" and img_label != "None":
        pdf.set_text_color(0, 0, 128)  # Blue for imaging
        pdf.cell(80, 10, "IMAGING SCAN", 1)
        pdf.cell(40, 10, "AI Analysis", 1)
        pdf.cell(70, 10, img_label, 1)
        pdf.ln()

    # 3. DISCLAIMER
    pdf.ln(20)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        0,
        5,
        "DISCLAIMER: This report is generated by an AI Diagnostic Assistant. "
        "It is not a replacement for professional medical advice."
    )

    return pdf.output(dest='S').encode('latin-1')
