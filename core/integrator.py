import json

def generate_master_verdict(scan_data, lab_data=None):
    # 1. Extract Scan Severity
    scan_triage = scan_data.get("triage", 1)
    scan_label = scan_data.get("label", "Unknown")
    
    # 🟢 FIX: Handle Rejected Images (Triage 0)
    if scan_triage == 0:
        return {
            "verdict": "⚠️ REJECTED / INVALID",
            "color": "gray",
            "severity_score": 0,
            "summary": "Image rejected. Please upload a valid medical scan or report.",
            "imaging_brief": "Non-Medical",
            "lab_brief": "N/A"
        }

    # 2. Extract Lab Severity
    lab_triage = 0
    if lab_data and isinstance(lab_data, dict):
        lab_triage = lab_data.get("triage_summary", {}).get("max_tier", 0)

    # 3. Determine Maximum Risk
    max_severity = max(scan_triage, lab_triage)

    # 4. Generate Verdict
    if max_severity >= 4:
        return {
            "verdict": "🚨 CRITICAL / EMERGENCY",
            "color": "red",
            "severity_score": 4,
            "summary": f"CRITICAL: {scan_label} detected. Immediate attention required.",
            "imaging_brief": scan_label,
            "lab_brief": "Critical"
        }
    elif max_severity == 3:
        return {
            "verdict": "🟠 ABNORMAL / URGENT",
            "color": "orange",
            "severity_score": 3,
            "summary": f"Abnormal findings detected: {scan_label}. Specialist review advised.",
            "imaging_brief": scan_label,
            "lab_brief": "Abnormal"
        }
    elif max_severity == 2:
        return {
            "verdict": "🟡 MONITOR",
            "color": "yellow",
            "severity_score": 2,
            "summary": f"Minor or chronic findings: {scan_label}. Routine follow-up.",
            "imaging_brief": scan_label,
            "lab_brief": "Mild"
        }
    else:
        return {
            "verdict": "🟢 STABLE / NORMAL",
            "color": "green",
            "severity_score": 1,
            "summary": f"No significant abnormalities detected ({scan_label}).",
            "imaging_brief": scan_label,
            "lab_brief": "Normal"
        }
def generate_safe_master_verdict(scan_data, lab_data=None):
    """Wrapper to prevent crashes on invalid data."""
    if not scan_data or scan_data.get("is_valid_study") is False:
        return {
            "verdict": "⚠️ INCONCLUSIVE",
            "color": "gray",
            "severity_score": 0,
            "summary": "Study invalid, unreadable, or non-medical.",
            "imaging_brief": "Invalid",
            "lab_brief": "N/A"
        }
    return generate_master_verdict(scan_data, lab_data)