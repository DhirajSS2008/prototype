"""TrOCR handwritten text recognition service using Microsoft's Vision Transformer."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model cache
_processor = None
_model = None
_model_loaded = False
TROCR_AVAILABLE = False

try:
    import torch
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    from PIL import Image
    TROCR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"TrOCR dependencies not available: {e}. Install transformers, torch, Pillow.")


def _load_model():
    """Lazy-load the TrOCR model on first use."""
    global _processor, _model, _model_loaded
    if _model_loaded:
        return _processor, _model
    
    if not TROCR_AVAILABLE:
        _model_loaded = True
        return None, None
    
    try:
        logger.info("Loading TrOCR handwritten model (first load may download ~1GB)...")
        _processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
        _model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
        _model.eval()
        logger.info("TrOCR model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load TrOCR model: {e}")
        _processor, _model = None, None
    
    _model_loaded = True
    return _processor, _model


def _run_trocr_on_image(image_path: str, use_preprocessed: bool = False) -> tuple[str, float]:
    """Run TrOCR on an image and return (text, confidence).
    
    If use_preprocessed=True, applies OpenCV preprocessing first.
    """
    processor, model = _load_model()
    if processor is None or model is None:
        return "", 0.0
    
    try:
        from PIL import Image as PILImage
        import torch
        
        if use_preprocessed:
            # Apply OpenCV preprocessing then convert back to PIL
            try:
                import cv2
                import numpy as np
                img = cv2.imread(image_path)
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                    thresh = cv2.adaptiveThreshold(
                        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                        cv2.THRESH_BINARY, 11, 2
                    )
                    pil_image = PILImage.fromarray(thresh).convert("RGB")
                else:
                    pil_image = PILImage.open(image_path).convert("RGB")
            except Exception:
                pil_image = PILImage.open(image_path).convert("RGB")
        else:
            pil_image = PILImage.open(image_path).convert("RGB")
        
        # Process with TrOCR
        pixel_values = processor(images=pil_image, return_tensors="pt").pixel_values
        
        with torch.no_grad():
            outputs = model.generate(
                pixel_values,
                max_length=512,
                output_scores=True,
                return_dict_in_generate=True,
            )
        
        # Decode text
        generated_ids = outputs.sequences
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Compute confidence from token probabilities
        if hasattr(outputs, 'scores') and outputs.scores:
            all_probs = []
            for score in outputs.scores:
                probs = torch.softmax(score, dim=-1)
                max_prob = probs.max(dim=-1).values.item()
                all_probs.append(max_prob)
            confidence = sum(all_probs) / len(all_probs) if all_probs else 0.0
        else:
            confidence = 0.5  # Default if scores not available
        
        return text.strip(), confidence
    
    except Exception as e:
        logger.error(f"TrOCR inference error: {e}")
        return "", 0.0


def extract_handwritten_text(image_path: str) -> tuple[str, float]:
    """Extract text from a handwritten image using TrOCR.
    
    Runs both preprocessed and raw image through the model,
    picks the result with higher confidence.
    
    Returns (text, confidence_score).
    """
    if not TROCR_AVAILABLE:
        logger.warning("TrOCR not available — falling back to empty result")
        return "", 0.0
    
    # Run on raw image
    raw_text, raw_conf = _run_trocr_on_image(image_path, use_preprocessed=False)
    
    # Run on preprocessed image
    proc_text, proc_conf = _run_trocr_on_image(image_path, use_preprocessed=True)
    
    # Pick the one with higher confidence
    if proc_conf > raw_conf and proc_text:
        logger.info(f"TrOCR: Using preprocessed result (conf={proc_conf:.2f} vs raw={raw_conf:.2f})")
        return proc_text, proc_conf
    else:
        logger.info(f"TrOCR: Using raw result (conf={raw_conf:.2f} vs proc={proc_conf:.2f})")
        return raw_text, raw_conf


def is_handwritten(image_path: str) -> bool:
    """Detect if an image is likely handwritten using edge density heuristics.
    
    Handwritten text tends to have more irregular edge patterns and
    lower variance in the Laplacian compared to printed text.
    """
    try:
        import cv2
        import numpy as np
        
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return False
        
        # Compute Laplacian variance (measure of edge sharpness)
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        lap_var = laplacian.var()
        
        # Compute horizontal projection profile regularity
        # Printed text has very regular line spacing
        binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        h_proj = np.sum(binary, axis=1)
        non_zero = h_proj[h_proj > 0]
        
        if len(non_zero) < 5:
            return False
        
        # Coefficient of variation in horizontal projections
        cv_coeff = np.std(non_zero) / (np.mean(non_zero) + 1e-6)
        
        # Heuristic thresholds:
        # - Lower Laplacian variance → smoother edges → likely handwritten
        # - Higher CV coefficient → irregular distribution → likely handwritten
        is_hw = lap_var < 500 and cv_coeff > 0.8
        
        logger.info(f"Handwriting detection: lap_var={lap_var:.1f}, cv_coeff={cv_coeff:.2f}, is_handwritten={is_hw}")
        return is_hw
    
    except Exception as e:
        logger.warning(f"Handwriting detection error: {e}")
        return False
