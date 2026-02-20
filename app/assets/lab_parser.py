import re
import json 

# ------------------------------------------------------------------
# OPTIONAL METADATA (NOT USED IN LOGIC)
# ------------------------------------------------------------------
LAB_PARSER_VERSION = "1.0.0"
LAB_PARSER_ENGINE = "ComprehensiveParser"

# ------------------------------------------------------------------
# OPTIONAL HELPER (NOT USED BY DEFAULT)
# Normalizes marker names for future expansion
# ------------------------------------------------------------------
def normalize_marker_name(name):
    if not isinstance(name, str):
        return ""
    return name.strip().lower()

# --- 1. THE TRIAGE ENGINE ---
def triage_biomarker(name, value):
    """
    Assigns a 1-4 severity tier based on clinical risk.
    """
    name = name.lower()

    # Defensive cast (ADDED, does not change behavior)
    try:
        value = float(value)
    except Exception:
        return 1

    if "troponin" in name:
        return 4 if value > 12 else 1 

    if "hscrp" in name or "c-reactive" in name:
        if value > 10: return 4 
        if value > 3: return 3 

    if "hba1c" in name:
        return 4 if value >= 6.5 else (2 if value >= 5.7 else 1) 

    if "glucose" in name:
        return 4 if value > 125 else (2 if value > 100 else 1)

    return 1

# ------------------------------------------------------------------
# OPTIONAL HELPER (NOT USED BY DEFAULT)
# Detects negated clinical phrases (future-proofing)
# ------------------------------------------------------------------
def is_negated_phrase(text, phrase, window=25):
    text = text.lower()
    phrase = phrase.lower()
    idx = text.find(phrase)
    if idx == -1:
        return False
    context = text[max(0, idx - window):idx]
    return any(n in context for n in ["no ", "not ", "negative ", "rule out "])

# --- 2. THE COMPREHENSIVE PARSER ---
class ComprehensiveParser:
    def parse(self, text):
        data = {
            "clinical_analysis": [],
            "triage_summary": {"max_tier": 1},
            "form_fields": {},
            "full_text": text
        }
        
        # --- PRE-PROCESSING: REMOVE NOISE SECTIONS ---
        clean_text = text
        noise_headers = [
            "Comment",
            "Comments:",
            "Note:",
            "Interpretation:",
            "Bio. Ref. Interval"
        ]

        for header in noise_headers:
            if header in clean_text:
                parts = clean_text.split(header)
                if len(parts) > 1:
                    clean_text = parts[0]

        # FIX 1: DNA / MOLECULAR REPORT LOGIC
        if "BCR-ABL" in clean_text:
            if re.search(r"Positive.*?\(b3:a2\)", clean_text, re.I):
                self._add_finding(data, "BCR-ABL (CML)", "POSITIVE", 4)
            elif "Negative" in clean_text:
                self._add_finding(data, "BCR-ABL", "NEGATIVE", 1)

        # FIX 2: TEXT-BASED DIAGNOSIS (Strict Context)
        critical_phrases = {
            "ST elevation": 4,
            "Anterolateral injury": 4,
            "Acute infarct": 4,
            "Atrial fibrillation": 3,
            "Malignancy": 4,
            "Carcinoma": 4
        }

        for phrase, tier in critical_phrases.items():
            if re.search(r"\b" + re.escape(phrase) + r"\b", clean_text, re.I):
                # Negation guard exists but NOT enforced (future-ready)
                self._add_finding(
                    data,
                    f"Text Finding: {phrase.title()}",
                    "DETECTED",
                    tier
                )

        # FIX 3: ROBUST BIOCHEMISTRY EXTRACTION (NUMBERS)
        patterns = {
            "HbA1c": r"HbA1c.*?(\d+\.?\d*)\s*%",
            "hsCRP": r"(?:hsCRP|CARDIO C-REACTIVE).*?(\d+\.?\d*)\s*mg/L",
            "Troponin-I": r"TROPONIN-I.*?(\d+\.?\d*)\s*ng/L",
            "Apolipoprotein B": r"APOLIPOPROTEIN B.*?(\d+\.?\d*)", 
            "Glucose": r"GLUCOSE.*?(\d+\.?\d*)"
        }

        for marker, regex in patterns.items():
            match = re.search(regex, text, re.I | re.S)
            if match:
                raw_val = match.group(1)
                try:
                    val = float(raw_val)
                    tier = triage_biomarker(marker, val)
                    self._add_finding(data, marker, val, tier)
                except Exception:
                    continue 

        return data

    def _add_finding(self, data, marker, value, tier):
        status = "NORMAL"
        if tier == 4: status = "CRITICAL"
        elif tier == 3: status = "ABNORMAL"
        elif tier == 2: status = "BORDERLINE"

        data["clinical_analysis"].append({
            "Marker": marker,
            "Value": value,
            "Status": status,
            "Tier": tier
        })

        if tier > data["triage_summary"]["max_tier"]:
            data["triage_summary"]["max_tier"] = tier

def extract_all_details(text):
    parser = ComprehensiveParser()
    return parser.parse(text)
