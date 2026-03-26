<<<<<<< HEAD
"""OCR service for receipt and invoice images using Tesseract + OpenCV.

Pipeline: Grayscale → Gaussian Blur → Adaptive Threshold → Morphological Ops → Deskew → Tesseract.
For handwritten receipts, delegates to TrOCR Vision Transformer.
"""

import re
import logging
import math
=======
"""OCR service for receipt and invoice images using Tesseract + OpenCV."""

import re
import logging
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Graceful imports for OCR dependencies
try:
    import cv2
    import numpy as np
    import pytesseract
    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    logger.warning(f"OCR dependencies not available: {e}. Install opencv-python-headless and pytesseract.")

from services.pdf_service import parse_date, parse_amount, categorize_transaction


<<<<<<< HEAD
def _deskew(image):
    """Correct skew/tilt in a binary image using minAreaRect on contours."""
    coords = np.column_stack(np.where(image > 0))
    if len(coords) < 10:
        return image
    
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    
    # Normalize angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Only deskew if angle is significant but not extreme
    if abs(angle) < 0.5 or abs(angle) > 45:
        return image
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def preprocess_image(image_path: str):
    """Apply full OpenCV preprocessing pipeline for OCR accuracy.
    
    Steps:
    1. Grayscale conversion
    2. Gaussian blur for noise removal
    3. Adaptive thresholding for contrast enhancement
    4. Morphological operations to clean broken characters
    5. Deskewing to correct tilted scans
    """
=======
def preprocess_image(image_path: str):
    """Apply OpenCV preprocessing for better OCR accuracy."""
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    if not OCR_AVAILABLE:
        raise RuntimeError("OpenCV not installed. Run: pip install opencv-python-headless pytesseract")
    
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
<<<<<<< HEAD
    # 1. Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Gaussian blur for noise removal
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. Adaptive thresholding for contrast enhancement
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # 4. Morphological operations — close gaps in broken characters
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Additional morphological pass: dilate then erode to connect strokes
    kernel_dilate = np.ones((1, 1), np.uint8)
    cleaned = cv2.dilate(cleaned, kernel_dilate, iterations=1)
    cleaned = cv2.erode(cleaned, kernel_dilate, iterations=1)
    
    # 5. Deskewing to correct tilted scans
    cleaned = _deskew(cleaned)
    
=======
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    return cleaned


def extract_text_from_image(image_path: str) -> tuple[str, float]:
<<<<<<< HEAD
    """Extract text from image using Tesseract OCR (with handwriting fallback).
    
    Detects whether the image is handwritten. If so, uses TrOCR.
    Otherwise uses the full Tesseract pipeline.
    """
=======
    """Extract text from image using Tesseract OCR."""
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    if not OCR_AVAILABLE:
        return "", 0.0
    
    try:
<<<<<<< HEAD
        # Check if handwritten — if TrOCR is available, delegate
        try:
            from services.trocr_service import is_handwritten, extract_handwritten_text, TROCR_AVAILABLE
            if TROCR_AVAILABLE and is_handwritten(image_path):
                logger.info("Handwritten receipt detected — using TrOCR")
                text, confidence = extract_handwritten_text(image_path)
                if text:
                    return text, confidence
                logger.info("TrOCR returned empty — falling back to Tesseract")
        except Exception as e:
            logger.warning(f"TrOCR check failed, falling back to Tesseract: {e}")
        
        # Standard Tesseract pipeline
        processed = preprocess_image(image_path)
        
        # Get per-word confidence data
        ocr_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in ocr_data["conf"] if int(c) > 0]
        avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
        
        # Get full text
        text = pytesseract.image_to_string(processed)
        return text.strip(), avg_confidence
    
=======
        processed = preprocess_image(image_path)
        ocr_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in ocr_data["conf"] if int(c) > 0]
        avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
        text = pytesseract.image_to_string(processed)
        return text.strip(), avg_confidence
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return "", 0.0


def extract_transactions_from_image(file_path: str) -> list[dict]:
    """Extract transaction data from a receipt or invoice image."""
    if not OCR_AVAILABLE:
        logger.warning("OCR not available — returning empty results for image upload")
        return []
    
    text, ocr_confidence = extract_text_from_image(file_path)
    if not text:
        return []
    
    results = []
    lines = text.split("\n")
    
    receipt_date = None
    receipt_total = None
    receipt_counterparty = None
    item_amounts = []
    
    for line in lines:
        line = line.strip()
        if len(line) < 3:
            continue
        
<<<<<<< HEAD
        # Try to find date
        if not receipt_date:
            receipt_date = parse_date(line)
        
        # Try to find total amount
=======
        if not receipt_date:
            receipt_date = parse_date(line)
        
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        total_match = re.search(
            r"(?:total|grand\s*total|amount\s*due|net\s*amount|balance\s*due)[:\s]*[\$₹€£]?\s*([\d,]+\.?\d{0,2})",
            line, re.IGNORECASE
        )
        if total_match:
            try:
                receipt_total = float(total_match.group(1).replace(",", ""))
            except ValueError:
                pass
        
<<<<<<< HEAD
        # Try to find counterparty
=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        if not receipt_counterparty and len(line) > 3:
            from_match = re.match(r"(?:from|bill\s*to|invoice\s*from|vendor)[:\s]*(.*)", line, re.IGNORECASE)
            if from_match:
                receipt_counterparty = from_match.group(1).strip()[:255]
            elif not receipt_date and not total_match and len(line) > 5:
                receipt_counterparty = line[:255]
        
<<<<<<< HEAD
        # Collect individual amounts
=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        amount = parse_amount(line)
        if amount and not total_match:
            item_amounts.append(amount)
    
    final_amount = receipt_total or (sum(item_amounts) if item_amounts else None)
    
    if final_amount:
        category = categorize_transaction(text)
        base_confidence = ocr_confidence * 0.7
        if receipt_date:
            base_confidence += 0.1
        if receipt_counterparty:
            base_confidence += 0.1
        if category != "Other":
            base_confidence += 0.1
        
<<<<<<< HEAD
        needs_review = base_confidence < 0.7
        
=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
        results.append({
            "date": receipt_date or datetime.now(),
            "amount": -abs(final_amount),
            "counterparty": receipt_counterparty,
            "category": category,
            "confidence": min(base_confidence, 1.0),
<<<<<<< HEAD
            "needs_review": needs_review,
=======
>>>>>>> 8a260015108003b30586cdffc9a5d14ec1407d73
            "raw_text": text[:1000],
            "source": "ocr",
        })
    
    return results
