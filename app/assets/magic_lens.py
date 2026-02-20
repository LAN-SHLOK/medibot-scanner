import torch
from torchvision import models, transforms
from PIL import Image
import numpy as np
import cv2
import os
import traceback

class MagicLensAI:
    def __init__(self):
        self.device = torch.device("cpu")
        print(f"⚙️ Magic Lens initialized on: {self.device}")

        try:
            # We use DenseNet121 as a visualizer. 
            # ideally, this should share weights with your main model, 
            # but for now, we will force it to look at the right spot by cropping.
            self.model = models.densenet121(
                weights=models.DenseNet121_Weights.DEFAULT
            )
            self.model.eval()
            self.model.to(self.device)

            self.preprocess = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                ),
            ])
            self.ai_ready = True
        except Exception as e:
            print(f"⚠️ AI Load Error: {e}")
            self.ai_ready = False

    # --- 🟢 NEW: DUPLICATE SMART CROP LOGIC ---
    # (This ensures the heatmap logic sees exactly what the diagnosis logic saw)
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

            # Crop and return
            return pil_image.crop((x, y, x+w, y+h))
        except:
            return pil_image

    def should_show_disclaimer(self, scan_data=None, final_verdict=None):
        if not scan_data: return True 
        scan_type = scan_data.get("scan_type", "").lower()
        scan_conf = scan_data.get("scan_confidence", 0)
        label = scan_data.get("label", "").lower()
        label_conf = scan_data.get("confidence", 0)

        if any(k in scan_type for k in ["document", "non-medical", "text", "photo"]): return True
        if scan_conf < 0.60: return True
        if label_conf < 0.45: return True
        if label in ["unknown", "uncertain", "abnormal"]: return True
        if final_verdict:
            verdict_text = final_verdict.get("verdict", "").lower()
            if verdict_text.startswith("⚠️"): return True
        return False

    def generate_heatmap(self, image_path, triage_value=1, save_path="outputs/overlay_output.jpg", scan_data=None, final_verdict=None):
        try:
            if not self.ai_ready:
                return {"status": "error", "message": "AI Model not loaded."}

            # 1. Load Image
            try:
                img_pil = Image.open(image_path).convert("RGB")
            except Exception:
                return {"status": "error", "message": "Invalid image file."}

            # 2. 🟢 APPLY SMART CROP (The Fix)
            # This forces the heatmap to generate on the FILM, not the WALL.
            img_pil = self.smart_crop_film(img_pil)

            # Convert crop to CV2 for final overlay
            img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

            # Auto brightness (CLAHE is better for medical, but simple scaling works too)
            if np.mean(img_cv) < 50:
                img_cv = cv2.convertScaleAbs(img_cv, alpha=1.5, beta=20)

            # 3. AI Processing
            input_tensor = self.preprocess(img_pil).unsqueeze(0).to(self.device)
            target_layer = self.model.features.norm5

            activations = []
            gradients = []

            def forward_hook(module, input, output):
                activations.append(output)
                output.register_hook(lambda grad: gradients.append(grad))

            handle = target_layer.register_forward_hook(forward_hook)
            try:
                output = self.model(input_tensor)
                target_category = output.argmax(dim=1)
                self.model.zero_grad()
                output[0, target_category].backward()
            finally:
                handle.remove()

            if not gradients or not activations:
                return {"status": "error", "message": "Grad-CAM failed."}

            grad = gradients[0].detach().numpy()[0]
            act = activations[0].detach().numpy()[0]
            weights = np.mean(grad, axis=(1, 2))

            cam = np.zeros(act.shape[1:], dtype=np.float32)
            for i, w in enumerate(weights):
                cam += w * act[i]

            cam = np.maximum(cam, 0)
            if np.max(cam) > 0:
                cam /= np.max(cam)

            # Resize CAM to match the CROPPED image size
            cam = cv2.resize(cam, (img_pil.width, img_pil.height))
            cam[cam < 0.2] = 0  

            try: triage_value = int(triage_value)
            except: triage_value = 1

            if triage_value >= 3:
                colormap = cv2.COLORMAP_JET
                alpha = 0.5
            else:
                colormap = cv2.COLORMAP_VIRIDIS
                alpha = 0.35

            heatmap = cv2.applyColorMap(np.uint8(255 * cam), colormap)
            overlay = cv2.addWeighted(img_cv, 1 - alpha, heatmap, alpha, 0)

            if self.should_show_disclaimer(scan_data, final_verdict):
                h, w, _ = overlay.shape
                text = "AI ATTENTION MAP"
                font_scale = max(0.6, w / 1200.0)
                cv2.putText(overlay, text, (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2, cv2.LINE_AA)

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            cv2.imwrite(save_path, overlay)

            return {
                "status": "success", 
                "overlay_path": save_path, 
                "score": int(min(10, triage_value * 2.5)), 
                "description": "AI Visualization generated."
            }

        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

_lens = None
def get_magic_lens():
    global _lens
    if _lens is None:
        _lens = MagicLensAI()
    return _lens