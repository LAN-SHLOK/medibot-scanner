# core/handwriting.py
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch

# ------------------------------------------------------------------
# OPTIONAL METADATA (NOT USED IN LOGIC)
# ------------------------------------------------------------------
HANDWRITING_ENGINE_VERSION = "1.0.0"
HANDWRITING_MODEL_NAME = "microsoft/trocr-small-handwritten"

class HandwritingBrain:
    def __init__(self):
        print("Loading Handwriting AI (TrOCR)...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        try:
            self.processor = TrOCRProcessor.from_pretrained(
                'microsoft/trocr-small-handwritten'
            )
            self.model = VisionEncoderDecoderModel.from_pretrained(
                'microsoft/trocr-small-handwritten'
            ).to(self.device)
            self.ai_ready = True
        except Exception as e:
            print(f"⚠️ Handwriting AI Load Error: {e}")
            self.ai_ready = False

    def read_handwriting(self, image_path):
        # --------------------------------------------------------------
        # SAFETY: Model availability check (ADDED)
        # --------------------------------------------------------------
        if not self.ai_ready:
            return ""

        # --------------------------------------------------------------
        # SAFETY: Image load guard (ADDED)
        # --------------------------------------------------------------
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception:
            return ""

        pixel_values = self.processor(
            images=image,
            return_tensors="pt"
        ).pixel_values.to(self.device)

        # --------------------------------------------------------------
        # SAFETY: No-grad inference (ADDED)
        # --------------------------------------------------------------
        with torch.no_grad():
            generated_ids = self.model.generate(
                pixel_values
                # Optional future cap:
                # max_length=128
            )

        generated_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0]

        return generated_text

_hand_brain = None
def get_handwriting_brain():
    global _hand_brain
    if _hand_brain is None:
        _hand_brain = HandwritingBrain()
    return _hand_brain
