"""OCR service for receipt and invoice images using Tesseract + OpenCV."""

import re
import logging
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


def preprocess_image(image_path: str):
    """Apply OpenCV preprocessing for better OCR accuracy."""
    if not OCR_AVAILABLE:
        raise RuntimeError("OpenCV not installed. Run: pip install opencv-python-headless pytesseract")
    
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    thresh = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return cleaned


def extract_text_from_image(image_path: str) -> tuple[str, float]:
    """Extract text from image using Tesseract OCR."""
    if not OCR_AVAILABLE:
        return "", 0.0
    
    try:
        processed = preprocess_image(image_path)
        ocr_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in ocr_data["conf"] if int(c) > 0]
        avg_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
        text = pytesseract.image_to_string(processed)
        return text.strip(), avg_confidence
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
        
        if not receipt_date:
            receipt_date = parse_date(line)
        
        total_match = re.search(
            r"(?:total|grand\s*total|amount\s*due|net\s*amount|balance\s*due)[:\s]*[\$₹€£]?\s*([\d,]+\.?\d{0,2})",
            line, re.IGNORECASE
        )
        if total_match:
            try:
                receipt_total = float(total_match.group(1).replace(",", ""))
            except ValueError:
                pass
        
        if not receipt_counterparty and len(line) > 3:
            from_match = re.match(r"(?:from|bill\s*to|invoice\s*from|vendor)[:\s]*(.*)", line, re.IGNORECASE)
            if from_match:
                receipt_counterparty = from_match.group(1).strip()[:255]
            elif not receipt_date and not total_match and len(line) > 5:
                receipt_counterparty = line[:255]
        
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
        
        results.append({
            "date": receipt_date or datetime.now(),
            "amount": -abs(final_amount),
            "counterparty": receipt_counterparty,
            "category": category,
            "confidence": min(base_confidence, 1.0),
            "raw_text": text[:1000],
            "source": "ocr",
        })
    
    return results
