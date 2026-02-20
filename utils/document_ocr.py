import pytesseract
from PIL import Image
import cv2
import numpy as np
import os

# IMPORTANT: Replace with your actual Tesseract installation path if on Windows
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_doc(image_path):
    """
    Lightweight OCR function optimized for low-spec laptops.
    Works by cleaning the image first to improve accuracy.
    """
    try:
        # 1. Load the image
        image = cv2.imread(image_path)
        if image is None:
            return "Error: Could not load image."

        # 2. Pre-processing for better accuracy
        # Convert to grayscale to reduce complexity
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to make text pop
        # (Converts image to strictly Black and White)
        _, cleaned = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 3. Perform OCR
        # PSM 6: Assumes a single uniform block of text
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(cleaned, config=custom_config)

        return text.strip()
    except Exception as e:
        return f"OCR Error: {str(e)}"