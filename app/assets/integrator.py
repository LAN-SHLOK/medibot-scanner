import json

# ------------------------------------------------------------------
# OPTIONAL METADATA (NOT USED IN LOGIC)
# ------------------------------------------------------------------
VERDICT_ENGINE_VERSION = "1.0.0"
VERDICT_ENGINE_NAME = "MasterVerdictEngine"

# ------------------------------------------------------------------
# OPTIONAL HELPER (NOT USED BY DEFAULT)
# Normalizes text for safer keyword matching
# ------------------------------------------------------------------
def normalize_text(text):
    if not isinstance(text, str):
        return ""
    return text.lower().strip()

# --- ROBUST NEGATION LOGIC ---
# Words that flip the meaning of a bad keyword
NEGATION_TERMS = ["no ", "not ", "negative ", "absent ", "free of ", "without ", "normal "]

def is_actually_critical(label, danger_words):
    """
    Smart check: Returns True ONLY if a danger word exists 
    AND is not immediately preceded by a negation.
    """
    label_lower = label.lower()
    
    for danger in danger_words:
        if danger in label_lower:
            is_negated = False
            for neg in NEGATION_TERMS:
                if neg in label_lower:
                    neg_index = label_lower.find(neg)
                    danger_index = label_lower.find(danger)
                    if neg_index > -1 and neg_index < danger_index:
                        if danger_index - neg_index < 25:
                            is_negated = True
                            break
            
            if not is_negated:
                return True
                
    return False

def generate_master_verdict(scan_data, lab_data):
    # 1. Start with a baseline
    verdict = "STABLE"
    color = "green"
    summary = "✅ No urgent findings detected."
    
    # 2. Extract Data
    scan_triage = scan_data.get('triage', 1)
    lab_triage = lab_data.get('triage_summary', {}).get('max_tier', 1)
    scan_label = scan_data.get('label', 'Unknown')

    # ------------------------------------------------------------------
    # OPTIONAL DEFENSIVE CAST (ADDED – does not change behavior)
    # ------------------------------------------------------------------
    try:
        scan_triage = int(scan_triage)
    except Exception:
        scan_triage = 1

    try:
        lab_triage = int(lab_triage)
    except Exception:
        lab_triage = 1
    
    # 3. CRITICAL OVERRIDE: Check for Danger Words (SMART CHECK)
    danger_words = [
        "metastatic", "tumor", "cancer", "hemorrhage",
        "fracture", "positive", "infarction", "torsion"
    ]
    
    if is_actually_critical(scan_label, danger_words):
        scan_triage = 4

    # 4. FIND SPECIFIC DISEASE NAME IN LAB REPORTS
    lab_critical_findings = []
    for item in lab_data.get("clinical_analysis", []):
        if item.get("Tier", 1) >= 3: 
            lab_critical_findings.append(item.get("Marker"))
        if item.get("Status") == "CRITICAL":
            lab_triage = 4

    # 5. Final Calculation
    max_severity = max(scan_triage, lab_triage)

    # 6. SILENT FAIL CHECK (Raw data without diagnosis)
    is_silent_ecg = (
        "ecg" in scan_label.lower() and 
        max_severity == 1 and 
        len(lab_critical_findings) == 0 and 
        "normal" not in lab_data.get("full_text", "").lower()
    )

    if is_silent_ecg:
        verdict = "⚠️ INCONCLUSIVE / RAW DATA"
        color = "yellow"
        summary = "Raw ECG detected without text diagnosis. Please consult a cardiologist."

    elif max_severity >= 4:
        verdict = "🚨 CRITICAL / EMERGENCY"
        color = "red"
        if lab_critical_findings:
            disease_names = ", ".join(lab_critical_findings)
            summary = f"CRITICAL: **{disease_names}** detected. Immediate medical attention required."
        elif "normal" not in scan_label.lower():
            summary = f"CRITICAL: **{scan_label}** detected. Immediate medical attention required."
        else:
            summary = "CRITICAL: High-risk abnormalities detected."

    elif max_severity == 3:
        verdict = "🟠 ABNORMAL / RISKY"
        color = "orange"
        summary = f"Significant findings ({scan_label}) detected. Specialist consultation advised."

    elif max_severity == 2:
        verdict = "🟡 MONITOR"
        color = "yellow"
        summary = "Minor deviations found. Routine follow-up recommended."

    return {
        "verdict": verdict,
        "color": color,
        "summary": summary,
        "imaging_brief": scan_label.title(),
        "lab_brief": (
            ", ".join(lab_critical_findings)
            if lab_critical_findings
            else ("Normal" if lab_triage == 1 else "Abnormalities Detected")
        )
    }

def generate_safe_master_verdict(scan_data, lab_data):
    """
    Safety wrapper that enforces study validity rules
    WITHOUT changing the core verdict logic.
    """

    # HARD SAFETY OVERRIDE (authoritative)
    if scan_data.get("is_valid_study") is False:
        return {
            "verdict": "⚠️ INCONCLUSIVE",
            "color": "yellow",
            "summary": (
                "Image quality or study context is insufficient for reliable AI interpretation. "
                "Radiologist review or repeat digital study required."
            ),
            "imaging_brief": "Inconclusive Study",
            "lab_brief": "Not evaluated"
        }

    # Otherwise, trust your existing perfect logic
    return generate_master_verdict(scan_data, lab_data)
