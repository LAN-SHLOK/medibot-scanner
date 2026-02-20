import os, sys, re, fitz
import numpy as np
import pytesseract
import cv2
from pathlib import Path
from typing import List, Tuple
from pdf2image import convert_from_path
from PIL import Image

# ------------------------------------------------------------------
# OPTIONAL METADATA (NOT USED IN LOGIC)
# ------------------------------------------------------------------
OCR_ENGINE_VERSION = "1.0.0"
OCR_ENGINE_NAME = "MixedPDFTextExtractor"

# ... [Keep your path variables] ...
POPPLER_PATH = r"C:\poppler\Library\bin\poppler-25.11.0\Library\bin"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ------------------------------------------------------------------
def is_gibberish(text: str, threshold: float = 0.30) -> bool:
    if not text.strip():
        return True
    non_readable = len(re.findall(r'[^\x20-\x7E\s]', text)) 
    ratio = non_readable / max(len(text), 1)  # SAFE DIVISION (ADDED)
    return ratio > threshold

# ------------------------------------------------------------------
def preprocess_image(pil_img: Image.Image) -> Image.Image:
    try:
        img = np.array(pil_img.convert('RGB'))
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        th = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15, 10
        )
        return Image.fromarray(th)
    except Exception as e:
        print(f"Preprocessing Warning: {e}")
        return pil_img

# ------------------------------------------------------------------
def extract_text_from_pdf_with_mixed_strategy(path: Path) -> Tuple[str, float]:
    try:
        doc = fitz.open(str(path))

        native_text = "\n\n".join(
            [page.get_text("text").strip()
             for page in doc
             if page.get_text("text").strip()]
        )

        if len(native_text) > 50 and not is_gibberish(native_text):
            return native_text, 0.99

        print(f"OCR Triggered for {path.name}...")

        images = convert_from_path(
            str(path),
            dpi=300,
            poppler_path=POPPLER_PATH
        )

        all_texts = []

        # OPTIONAL SAFETY LIMIT (NOT ENFORCED)
        # for img in images[:10]:  # Uncomment if needed
        for img in images:
            prep = preprocess_image(img)
            txt = pytesseract.image_to_string(prep)
            all_texts.append(txt)

        return "\n\n".join(all_texts), 0.85

    except Exception as e:
        return f"OCR Error: {str(e)}", 0.0

# ------------------------------------------------------------------
def convert_any_to_text(filepath: str) -> Tuple[str, float, str]:
    p = Path(filepath)
    suffix = p.suffix.lower()

    if suffix == '.pdf':
        text, conf = extract_text_from_pdf_with_mixed_strategy(p)

    elif suffix in ['.jpg', '.jpeg', '.png', '.webp']:
        try:  # SAFE IMAGE LOAD (ADDED)
            img = Image.open(p)
            text = pytesseract.image_to_string(preprocess_image(img))
            conf = 0.90
        except Exception as e:
            text = f"OCR Image Error: {e}"
            conf = 0.0

    else:
        text, conf = "Unsupported format", 0.0

    return str(p), conf, text
