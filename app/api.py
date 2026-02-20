# from fastapi import FastAPI, File, UploadFile, Response
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# import shutil
# import os
# import uuid

# # --- IMPORT ALL ENGINES ---
# from core.ai_vision import get_brain as get_vision_brain
# from core.doc_to_text import convert_any_to_text
# from core.handwriting import get_handwriting_brain
# from core.lab_parser import extract_all_details
# from core.integrator import generate_master_verdict
# from core.report_generator import generate_official_pdf
# from core.magic_lens import get_magic_lens

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# vision_brain = get_vision_brain()
# handwriting_brain = get_handwriting_brain()
# magic_lens = get_magic_lens()

# os.makedirs("outputs/heatmaps", exist_ok=True)
# os.makedirs("outputs/reports", exist_ok=True)
# os.makedirs("temp", exist_ok=True)

# @app.get("/favicon.ico", include_in_schema=False)
# async def favicon():
#     return Response(status_code=204)

# # 🟢 DATA FORMATTER FOR FRONTEND TABLE
# def format_report_data(vision_result=None, lab_data=None):
#     table_data = []
    
#     # 1. LAB DATA
#     if lab_data and "clinical_analysis" in lab_data:
#         for item in lab_data["clinical_analysis"]:
#             tier = item.get("Tier", 1)
#             status = "Normal"
#             if tier == 4: status = "🚨 Critical"
#             elif tier == 3: status = "⚠️ Abnormal"
#             elif tier == 2: status = "⚠️ Borderline"
            
#             table_data.append({
#                 "label": item.get("Marker", "Unknown"),
#                 "value": str(item.get("Value", "--")),
#                 "status": status,
#                 "is_abnormal": tier >= 2
#             })

#     # 2. VISION DATA
#     elif vision_result:
#         findings = vision_result.get("findings", {})
#         triage = vision_result.get("triage", 1)
#         status = "Normal"
#         if triage >= 3: status = "🚨 Abnormal"
        
#         table_data.append({"label": "Condition", "value": vision_result.get("label", "Unknown"), "status": status, "is_abnormal": triage >= 2})
#         table_data.append({"label": "Confidence", "value": findings.get("confidence", "--"), "status": "Info", "is_abnormal": False})
#         table_data.append({"label": "Modality", "value": vision_result.get("modality", "Scan"), "status": "Info", "is_abnormal": False})

#     return table_data

# @app.post("/analyze")
# async def analyze_file(file: UploadFile = File(...)):
#     print(f"📥 Received: {file.filename}")
#     scan_id = str(uuid.uuid4())[:8]
#     file_ext = os.path.splitext(file.filename)[1].lower()
#     temp_path = f"temp/{scan_id}{file_ext}"

#     with open(temp_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     result = {}
#     master_verdict = {}
#     lab_data = None
#     vision_result = None
#     heatmap_local_path = None
#     prescription_text = None 
    
#     # --- ROUTING ---
#     if file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".dcm", ".webp"]:
#         vision_result = vision_brain.analyze_image(temp_path)
        
#         # 🟢 HANDWRITTEN / DOCUMENT PROCESSING
#         if vision_result.get("modality") in ["Handwritten", "Document"]:
#             if vision_result.get("modality") == "Handwritten":
#                 text_content = handwriting_brain.read_handwriting(temp_path)
#             else:
#                 _, _, text_content = convert_any_to_text(temp_path)

#             # 🚨 SELECTIVE RAW DATA: Only trigger if specifically a Prescription
#             # We look for "Rx", "Sig", or the AI's own label
#             is_prescription = vision_result.get("label") == "Prescription" or any(kw in text_content for kw in ["Rx", "Sig", "Dispense"])
            
#             if is_prescription:
#                 prescription_text = text_content
            
#             # Everyone still goes through lab_parser to find any numerical markers
#             lab_data = extract_all_details(text_content)
#             master_verdict = generate_master_verdict(vision_result, lab_data)
            
#         elif vision_result.get("triage") == 0:
#             master_verdict = generate_master_verdict(vision_result, None)
#         else:
#             # MEDICAL SCAN (X-Ray/CT/MRI)
#             master_verdict = generate_master_verdict(vision_result, None)
#             if vision_result.get("triage", 0) >= 2:
#                 heatmap_local_path = f"outputs/heatmaps/overlay_{scan_id}.jpg"
#                 lens_result = magic_lens.generate_heatmap(temp_path, vision_result, heatmap_local_path)
#                 if lens_result.get("status") == "success":
#                     result["heatmap_url"] = f"http://127.0.0.1:8000/{heatmap_local_path}"

#     elif file_ext == ".pdf":
#         _, _, text_content = convert_any_to_text(temp_path)
        
#         # 🚨 SELECTIVE RAW DATA: Check if PDF is a prescription
#         # If it's a blood report, it won't have "Rx" or "Sig", so prescription_text stays None
#         if any(kw in text_content for kw in ["Rx", "Prescription", "Sig"]):
#             prescription_text = text_content
            
#         lab_data = extract_all_details(text_content)
#         doc_result = {"label": "PDF Report", "triage": lab_data["triage_summary"]["max_tier"], "modality": "PDF"}
#         master_verdict = generate_master_verdict(doc_result, lab_data)

#     # --- REPORT GENERATION ---
#     # Because prescription_text is only set for Rx files, 
#     # the "Medication Ledger" will only appear for prescriptions!
#     pdf_bytes = generate_official_pdf(
#         master_verdict, 
#         lab_data if lab_data else {}, 
#         prescription_data=prescription_text,
#         heatmap_path=heatmap_local_path
#     )
    
#     # ... rest of your response logic
    
#     report_filename = f"outputs/reports/report_{scan_id}.pdf"
#     with open(report_filename, "wb") as f: f.write(pdf_bytes)

#     if os.path.exists(temp_path): os.remove(temp_path)

#     formatted_data = format_report_data(vision_result, lab_data)

#     response = {
#         "verdict": master_verdict.get("verdict", "Unknown"),
#         "severity_score": master_verdict.get("severity_score", 0),
#         "summary": master_verdict.get("summary", "Analysis Complete"),
#         "report_url": f"http://127.0.0.1:8000/{report_filename}",
#         "report_data": formatted_data
#     }
    
#     if "heatmap_url" in result: 
#         response["heatmap_url"] = result["heatmap_url"]

#     return response

# app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
from fastapi import FastAPI, File, UploadFile, Response, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import sqlite3
import datetime

# --- IMPORT ALL ENGINES ---
from core.ai_vision import get_brain as get_vision_brain
from core.doc_to_text import convert_any_to_text
from core.handwriting import get_handwriting_brain
from core.lab_parser import extract_all_details
from core.integrator import generate_master_verdict
from core.report_generator import generate_official_pdf
from core.magic_lens import get_magic_lens

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vision_brain = get_vision_brain()
handwriting_brain = get_handwriting_brain()
magic_lens = get_magic_lens()

os.makedirs("outputs/heatmaps", exist_ok=True)
os.makedirs("outputs/reports", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# 🟢 DATABASE HELPER: Find the DB and Save Scan
def save_scan_to_db(user_id, scan_type, verdict, severity, report_url):
    """Saves the scan result to the database for history tracking."""
    db_path = "medibot.db" # Default local
    
    # Try to find the main DB in sibling folders if not here
    if not os.path.exists(db_path):
        # Look one level up for other project folders
        parent = os.path.dirname(os.getcwd())
        for root, dirs, files in os.walk(parent):
            if "medibot.db" in files:
                db_path = os.path.join(root, "medibot.db")
                break
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create Scans Table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                scan_type TEXT,
                verdict TEXT,
                severity INTEGER,
                report_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute(
            "INSERT INTO scans (user_id, scan_type, verdict, severity, report_url) VALUES (?, ?, ?, ?, ?)",
            (user_id, scan_type, verdict, severity, report_url)
        )
        
        conn.commit()
        conn.close()
        print(f"✅ Scan saved to DB ({db_path}) for User: {user_id}")
    except Exception as e:
        print(f"⚠️ Database Save Error: {e}")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

# 🟢 DATA FORMATTER FOR FRONTEND TABLE
def format_report_data(vision_result=None, lab_data=None):
    table_data = []
    
    # 1. LAB DATA
    if lab_data and "clinical_analysis" in lab_data:
        for item in lab_data["clinical_analysis"]:
            tier = item.get("Tier", 1)
            status = "Normal"
            if tier == 4: status = "🚨 Critical"
            elif tier == 3: status = "⚠️ Abnormal"
            elif tier == 2: status = "⚠️ Borderline"
            
            table_data.append({
                "label": item.get("Marker", "Unknown"),
                "value": str(item.get("Value", "--")),
                "status": status,
                "is_abnormal": tier >= 2
            })

    # 2. VISION DATA
    elif vision_result:
        findings = vision_result.get("findings", {})
        triage = vision_result.get("triage", 1)
        status = "Normal"
        if triage >= 3: status = "🚨 Abnormal"
        
        table_data.append({"label": "Condition", "value": vision_result.get("label", "Unknown"), "status": status, "is_abnormal": triage >= 2})
        table_data.append({"label": "Confidence", "value": findings.get("confidence", "--"), "status": "Info", "is_abnormal": False})
        table_data.append({"label": "Modality", "value": vision_result.get("modality", "Scan"), "status": "Info", "is_abnormal": False})

    return table_data

@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    user_id: str = Form(None)  # 🟢 ADDED: Accepts User ID from Frontend
):
    print(f"📥 Received: {file.filename} from User: {user_id}")
    scan_id = str(uuid.uuid4())[:8]
    file_ext = os.path.splitext(file.filename)[1].lower()
    temp_path = f"temp/{scan_id}{file_ext}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = {}
    master_verdict = {}
    lab_data = None
    vision_result = None
    heatmap_local_path = None
    prescription_text = None 
    
    # --- ROUTING ---
    if file_ext in [".jpg", ".jpeg", ".png", ".bmp", ".dcm", ".webp"]:
        vision_result = vision_brain.analyze_image(temp_path)
        
        # 🟢 HANDWRITTEN / DOCUMENT PROCESSING
        if vision_result.get("modality") in ["Handwritten", "Document"]:
            if vision_result.get("modality") == "Handwritten":
                text_content = handwriting_brain.read_handwriting(temp_path)
            else:
                _, _, text_content = convert_any_to_text(temp_path)

            # 🚨 SELECTIVE RAW DATA: Only trigger if specifically a Prescription
            # We look for "Rx", "Sig", or the AI's own label
            is_prescription = vision_result.get("label") == "Prescription" or any(kw in text_content for kw in ["Rx", "Sig", "Dispense"])
            
            if is_prescription:
                prescription_text = text_content
            
            # Everyone still goes through lab_parser to find any numerical markers
            lab_data = extract_all_details(text_content)
            master_verdict = generate_master_verdict(vision_result, lab_data)
            
        elif vision_result.get("triage") == 0:
            master_verdict = generate_master_verdict(vision_result, None)
        else:
            # MEDICAL SCAN (X-Ray/CT/MRI)
            master_verdict = generate_master_verdict(vision_result, None)
            if vision_result.get("triage", 0) >= 2:
                heatmap_local_path = f"outputs/heatmaps/overlay_{scan_id}.jpg"
                lens_result = magic_lens.generate_heatmap(temp_path, vision_result, heatmap_local_path)
                if lens_result.get("status") == "success":
                    result["heatmap_url"] = f"http://127.0.0.1:8000/{heatmap_local_path}"

    elif file_ext == ".pdf":
        _, _, text_content = convert_any_to_text(temp_path)
        
        # 🚨 SELECTIVE RAW DATA: Check if PDF is a prescription
        # If it's a blood report, it won't have "Rx" or "Sig", so prescription_text stays None
        if any(kw in text_content for kw in ["Rx", "Prescription", "Sig"]):
            prescription_text = text_content
            
        lab_data = extract_all_details(text_content)
        doc_result = {"label": "PDF Report", "triage": lab_data["triage_summary"]["max_tier"], "modality": "PDF"}
        master_verdict = generate_master_verdict(doc_result, lab_data)

    # --- REPORT GENERATION ---
    # Because prescription_text is only set for Rx files, 
    # the "Medication Ledger" will only appear for prescriptions!
    pdf_bytes = generate_official_pdf(
        master_verdict, 
        lab_data if lab_data else {}, 
        prescription_data=prescription_text,
        heatmap_path=heatmap_local_path
    )
    
    report_filename = f"outputs/reports/report_{scan_id}.pdf"
    with open(report_filename, "wb") as f: f.write(pdf_bytes)

    if os.path.exists(temp_path): os.remove(temp_path)

    formatted_data = format_report_data(vision_result, lab_data)
    
    final_report_url = f"http://127.0.0.1:8000/{report_filename}"

    # 🟢 SAVE TO DATABASE
    if user_id:
        scan_type = vision_result.get("modality", "Unknown") if vision_result else "PDF"
        save_scan_to_db(
            user_id, 
            scan_type, 
            master_verdict.get("verdict", "Unknown"), 
            master_verdict.get("severity_score", 0), 
            final_report_url
        )

    response = {
        "verdict": master_verdict.get("verdict", "Unknown"),
        "severity_score": master_verdict.get("severity_score", 0),
        "summary": master_verdict.get("summary", "Analysis Complete"),
        "report_url": final_report_url,
        "report_data": formatted_data
    }
    
    if "heatmap_url" in result: 
        response["heatmap_url"] = result["heatmap_url"]

    return response

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")