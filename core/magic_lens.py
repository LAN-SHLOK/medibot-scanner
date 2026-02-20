import os
import cv2
import numpy as np
from PIL import Image

class MagicLensAI:
    def __init__(self):
        print("🧬 MagicLens initialized (Organic Mode)")

    def generate_abnormality_mask(self, gray):
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        edges = cv2.Canny(gray, 100, 200)
        lap = np.abs(cv2.Laplacian(gray, cv2.CV_64F))
        mask = np.zeros_like(gray, dtype=np.float32)
        mask[edges > 0] += 0.3
        mask[lap > np.mean(lap)*2] += 0.7 
        mask = cv2.GaussianBlur(mask, (61, 61), 0)
        if np.max(mask) > 0: mask /= np.max(mask)
        return mask

    def generate_heatmap(self, image_path, analysis, save_path):
        # 🟢 FIX: Use 'triage' correctly (not 'severity')
        triage = analysis.get("triage", 0)
        
        # Only generate for Abnormal (2+) scans
        if triage < 2: 
            return {"status": "skipped", "message": "Normal study"}
        if analysis.get("modality") == "Document":
            return {"status": "skipped", "message": "Document detected"}

        try:
            pil_img = Image.open(image_path).convert("L")
            img_gray = np.array(pil_img)
            img_color = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)

            mask = self.generate_abnormality_mask(img_gray)
            mask[mask < 0.35] = 0 

            heatmap = cv2.applyColorMap(np.uint8(mask * 255), cv2.COLORMAP_JET)
            overlay = cv2.addWeighted(img_color, 0.7, heatmap, 0.3, 0)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            cv2.imwrite(save_path, overlay)

            return {"status": "success", "overlay_path": save_path}

        except Exception as e:
            return {"status": "error", "message": str(e)}

_lens = None
def get_magic_lens():
    global _lens
    if _lens is None: _lens = MagicLensAI()
    return _lens