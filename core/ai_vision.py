import torch
import open_clip
import numpy as np
import cv2
import json
import os
from PIL import Image
from transformers import AutoTokenizer

class MedicalVisionBrain:
    def __init__(self):
        print("⚡ Initializing Medical Vision Brain...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = 'hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224'
        
        try:
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract")
            print("✅ AI Model Loaded Successfully")
        except Exception as e:
            print(f"❌ AI Load Error: {e}")
            raise e

        # Load Knowledge Base
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        self.kb_path = os.path.join(project_root, "Medical_AI_Knowledge_Base")
        if not os.path.exists(self.kb_path): self.kb_path = os.path.join(base_dir, "Medical_AI_Knowledge_Base")

        self.body_parts_map = []       
        self.conditions_db = {}        
        self.severity_map = {}         
        self.ultrasound_list = []
        self.dermoscopy_list = []
        self.load_knowledge_base()

    def load_knowledge_base(self):
        if not os.path.exists(self.kb_path): return
        json_files = [f for f in os.listdir(self.kb_path) if f.endswith('.json')]
        for filename in json_files:
            try:
                with open(os.path.join(self.kb_path, filename), 'r', encoding='utf-8') as f:
                    self._parse_json_data(json.load(f))
            except: pass

    def _parse_json_data(self, data):
        if "Radiology" in data:
            for modality, regions in data["Radiology"].items():
                clean_mod = modality.replace("Radiology_", "").replace("_", " ")
                for region, diseases in regions.items():
                    context_key = f"{clean_mod} of {region}"
                    self.body_parts_map.append(context_key)
                    self.conditions_db[context_key] = [d["name"] for d in diseases]
                    for d in diseases: self.severity_map[d["name"].lower()] = d["severity"]
                    if "Ultrasound" in modality: self.ultrasound_list.extend([d["name"] for d in diseases])
        elif "Dermatology" in data:
            if "Dermoscopy" in data["Dermatology"]:
                for region, lesions in data["Dermatology"]["Dermoscopy"].items():
                    for l in lesions:
                        self.dermoscopy_list.append(l["name"])
                        self.severity_map[l["name"].lower()] = l["severity"]

    def _get_probs(self, image, label_list):
        if not label_list: return [0.0]
        if image.mode != 'RGB': image = image.convert('RGB')
        
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        inputs = self.tokenizer(label_list, padding=True, truncation=True, max_length=77, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(inputs["input_ids"])
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            text_probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            
        return text_probs[0].tolist()

    def smart_crop_film(self, pil_image):
        try:
            img_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 50, 200)
            contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours: return pil_image
            c = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(c)
            if w < 100 or h < 100: return pil_image
            return pil_image.crop((x, y, x+w, y+h))
        except: return pil_image

    def analyze_image(self, image_path):
        try:
            original_image = Image.open(image_path).convert("RGB")
        except:
            return {"label": "Error", "triage": 0, "modality": "Invalid", "findings": {"assessment": "File Error"}}
        
        # --- 1. STRICT GATEKEEPER ---
        allowed_types = [
            "Medical X-Ray Scan", "Computed Tomography (CT) Scan", "MRI Scan", 
            "Medical Ultrasound", "Dermoscopy Skin Lesion", 
            "Medical Lab Report Document"
        ]
        rejected_types = [
            "Anime Character", "Cartoon", "Selfie", "Face Photo", 
            "Outdoor Landscape", "Car", "Animal", "Food", "Screenshot", "Random Object"
        ]
        
        all_checks = allowed_types + rejected_types
        probs = self._get_probs(original_image, all_checks)
        best_idx = probs.index(max(probs))
        detected_type = all_checks[best_idx]
        confidence = max(probs)

        # REJECTION LOGIC
        if detected_type in rejected_types:
            print(f"❌ REJECTED: Detected {detected_type}")
            return {
                "label": "Non-Medical Image",
                "triage": 0, 
                "modality": "Invalid",
                "findings": {"assessment": "Rejected", "reason": f"Image identified as {detected_type}"}
            }
        
        if confidence < 0.35:
            return {
                "label": "Unclear Image",
                "triage": 0,
                "modality": "Invalid",
                "findings": {"assessment": "Rejected", "reason": "Low confidence match."}
            }

        # Document Routing
        if "Lab Report" in detected_type:
             return {"label": "Lab Report", "triage": 1, "modality": "Document", "findings": {"assessment": "OCR Required"}}

        # --- 2. DIAGNOSIS ---
        analysis_image = self.smart_crop_film(original_image)
        
        final_diagnosis_list = []
        scan_type_label = detected_type

        if "Ultrasound" in detected_type:
            final_diagnosis_list = self.ultrasound_list
        elif "Dermoscopy" in detected_type:
            final_diagnosis_list = self.dermoscopy_list
        else:
            mod_key = detected_type.split()[0] if " " in detected_type else detected_type
            filtered_contexts = [k for k in self.body_parts_map if mod_key in k]
            if not filtered_contexts: filtered_contexts = self.body_parts_map
            
            part_probs = self._get_probs(analysis_image, filtered_contexts)
            scan_type_label = filtered_contexts[part_probs.index(max(part_probs))]
            final_diagnosis_list = self.conditions_db.get(scan_type_label, ["Normal", "Abnormal"])

        diag_probs = self._get_probs(analysis_image, final_diagnosis_list)
        best_condition = final_diagnosis_list[diag_probs.index(max(diag_probs))]
        
        # 🟢 REALISM FIX: Calculate confidence with a clamp
        raw_conf = max(diag_probs) * 100
        if raw_conf > 99.5:
            diag_conf = 99.4  # Never allow 100%
        else:
            diag_conf = round(raw_conf, 1)

        triage_score = self.severity_map.get(best_condition.lower(), 1)
        danger_keywords = ["fracture", "cancer", "tumor", "pneumothorax", "hemorrhage", "infarction"]
        if any(d in best_condition.lower() for d in danger_keywords) and triage_score < 3:
            triage_score = 3

        return {
            "label": best_condition,
            "triage": triage_score,
            "scan_type": scan_type_label,
            "modality": detected_type,
            "findings": {"confidence": f"{diag_conf}%", "assessment": "Abnormal" if triage_score > 1 else "Normal"}
        }

_brain = None
def get_brain():
    global _brain
    if _brain is None: _brain = MedicalVisionBrain()
    return _brain