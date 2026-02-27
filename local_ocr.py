"""
local_ocr.py — Offline prescription OCR
----------------------------------------
Pipeline:
  1. Preprocess  — deskew, denoise, enhance contrast
  2. Detect      — Surya finds every text line / bounding box
  3. Recognise   — TrOCR-large-handwritten reads each crop
  4. Assemble    — join lines preserving reading order

Dependencies:
    pip install surya-ocr transformers torch torchvision Pillow opencv-python-headless

Models downloaded on first run (~1.5 GB total):
  • vikp/surya_det2            (line detection)
  • microsoft/trocr-large-handwritten  (recognition)

Public API
----------
    from local_ocr import extract_text
    text = extract_text(pil_image)          # returns plain string
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1.  PRE-PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def preprocess(image: Image.Image) -> Image.Image:
    """
    Return a cleaner grayscale image that is easier to OCR.
    Steps: convert → deskew → denoise → sharpen → binarise (adaptive threshold).
    """
    # --- RGB / RGBA → grayscale numpy array ---
    img = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # --- Deskew ---
    gray = _deskew(gray)

    # --- Denoise (non-local means, conservative to keep thin strokes) ---
    gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # --- Adaptive threshold (handles uneven lighting / shadows on prescriptions) ---
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,   # neighbourhood size — larger = handles bigger shadows
        C=10,           # constant subtracted from mean
    )

    # Back to PIL for the rest of the pipeline
    pil = Image.fromarray(binary).convert("RGB")

    # --- Mild sharpening pass ---
    pil = pil.filter(ImageFilter.SHARPEN)

    # --- Contrast boost (helps faint ink) ---
    pil = ImageEnhance.Contrast(pil).enhance(1.4)

    return pil


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Rotate the image so text lines are horizontal."""
    # Threshold → find text pixels
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return gray  # not enough pixels to estimate angle
    angle = cv2.minAreaRect(coords)[-1]
    # minAreaRect returns angles in [-90, 0); correct to [-45, 45)
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.5:          # skip tiny corrections (avoids blur)
        return gray
    (h, w) = gray.shape
    centre = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(centre, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    return rotated


# ─────────────────────────────────────────────────────────────────────────────
# 2.  LINE DETECTION  (Surya)
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_surya():
    """
    Load Surya detection model once and cache in memory.
    Handles both old API (<=0.4) and new API (>=0.5).
    """
    logger.info("Loading Surya detection model (first run only)…")
    try:
        # New API (surya >= 0.5) — single DetectionPredictor class
        from surya.detection import DetectionPredictor
        predictor = DetectionPredictor()
        return ("new", predictor)
    except ImportError:
        pass

    try:
        # Mid API — load_model / load_processor style
        from surya.model.detection.model import load_model as load_det_model
        from surya.model.detection.processor import load_processor as load_det_processor
        return ("mid", load_det_model(), load_det_processor())
    except ImportError:
        pass

    raise ImportError(
        "Could not load Surya detection. "
        "Try: pip install -U surya-ocr"
    )


def detect_lines(image: Image.Image) -> list[Image.Image]:
    """
    Return a list of PIL image crops, one per detected text line,
    sorted top-to-bottom then left-to-right.
    """
    surya = _load_surya()
    api   = surya[0]

    if api == "new":
        predictor = surya[1]
        [result]  = predictor([image])
    else:
        # mid / old API
        from surya.detection import batch_text_detection
        _, model, processor = surya
        [result] = batch_text_detection([image], model, processor)

    w, h = image.size
    crops: list[tuple[int, int, Image.Image]] = []  # (y_top, x_left, crop)

    for line in result.bboxes:
        x1, y1, x2, y2 = (
            max(0, int(line.bbox[0])),
            max(0, int(line.bbox[1])),
            min(w, int(line.bbox[2])),
            min(h, int(line.bbox[3])),
        )
        if x2 <= x1 or y2 <= y1:
            continue

        # Add small vertical padding so ascenders/descenders aren't clipped
        pad = max(4, int((y2 - y1) * 0.08))
        y1p = max(0, y1 - pad)
        y2p = min(h, y2 + pad)

        crop = image.crop((x1, y1p, x2, y2p))
        crops.append((y1, x1, crop))

    # Sort: primary = row (y), secondary = column (x)
    crops.sort(key=lambda t: (t[0], t[1]))
    return [c for _, _, c in crops]


# ─────────────────────────────────────────────────────────────────────────────
# 3.  RECOGNITION  (TrOCR-large-handwritten)
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_trocr():
    """Load TrOCR processor + model once and cache in memory."""
    logger.info("Loading TrOCR-large-handwritten (first run only, ~1.3 GB)…")
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-handwritten")
    model     = VisionEncoderDecoderModel.from_pretrained(
        "microsoft/trocr-large-handwritten"
    )
    model.eval()
    return processor, model


def recognise_lines(crops: list[Image.Image]) -> list[str]:
    """
    Run TrOCR on each crop and return the recognised strings.
    Processes in small batches to stay within CPU memory.
    """
    import torch
    processor, model = _load_trocr()

    results: list[str] = []
    batch_size = 4  # conservative for CPU RAM

    for i in range(0, len(crops), batch_size):
        batch = crops[i : i + batch_size]
        # TrOCR expects RGB PIL images
        batch_rgb = [c.convert("RGB") for c in batch]

        pixel_values = processor(
            images=batch_rgb, return_tensors="pt"
        ).pixel_values

        with torch.no_grad():
            generated = model.generate(
                pixel_values,
                max_new_tokens=128,
                num_beams=4,          # beam search for better accuracy on CPU
                early_stopping=True,
            )

        batch_text = processor.batch_decode(generated, skip_special_tokens=True)
        results.extend(batch_text)
        logger.debug("Recognised batch %d/%d", i // batch_size + 1,
                     -(-len(crops) // batch_size))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 4.  FALLBACK — pure Tesseract (no deep-learning deps required)
# ─────────────────────────────────────────────────────────────────────────────

def _tesseract_fallback(image: Image.Image) -> str:
    """
    Simple Tesseract fallback used when Surya / TrOCR are unavailable.

    Install Tesseract first:
      Windows : https://github.com/UB-Mannheim/tesseract/wiki  (run the .exe installer)
      Mac     : brew install tesseract
      Linux   : sudo apt install tesseract-ocr
    Then: pip install pytesseract
    """
    import sys
    import pytesseract  # type: ignore

    # Windows — point pytesseract at the default install location if not in PATH
    if sys.platform == "win32":
        import os
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        if not any(os.path.isfile(p) for p in candidates):
            raise RuntimeError(
                "Tesseract not found on Windows.\n"
                "Download and install from: "
                "https://github.com/UB-Mannheim/tesseract/wiki\n"
                "Then re-run the script."
            )
        for p in candidates:
            if os.path.isfile(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break

    config = r"--oem 3 --psm 6"   # OEM 3 = LSTM; PSM 6 = assume uniform block
    return pytesseract.image_to_string(image, config=config).strip()


# ─────────────────────────────────────────────────────────────────────────────
# 5.  PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def extract_text(image: Image.Image, *, use_fallback: bool = False) -> str:
    """
    Extract all text from a prescription image.

    Parameters
    ----------
    image        : PIL Image (any mode/size — preprocessing handles it)
    use_fallback : force Tesseract even if Surya + TrOCR are available

    Returns
    -------
    Plain string with newline-separated text lines in reading order.
    Empty string if nothing was detected.
    """
    if use_fallback:
        logger.info("Using Tesseract fallback as requested.")
        processed = preprocess(image)
        return _tesseract_fallback(processed)

    try:
        logger.info("Step 1/3 — preprocessing…")
        processed = preprocess(image)

        logger.info("Step 2/3 — detecting text lines with Surya…")
        crops = detect_lines(processed)

        if not crops:
            logger.warning("Surya found no text lines. Falling back to Tesseract.")
            return _tesseract_fallback(processed)

        logger.info("Step 3/3 — recognising %d lines with TrOCR…", len(crops))
        lines = recognise_lines(crops)

        text = "\n".join(line for line in lines if line.strip())
        logger.info("Done. Extracted %d characters.", len(text))
        return text

    except ImportError as exc:
        logger.warning("Deep-learning deps missing (%s). Falling back to Tesseract.", exc)
        return _tesseract_fallback(preprocess(image))


# ─────────────────────────────────────────────────────────────────────────────
# CLI  — python local_ocr.py path/to/image.jpg
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python local_ocr.py <image_path>")
        sys.exit(1)

    img = Image.open(sys.argv[1])
    print("\n── Extracted text ──────────────────────────")
    print(extract_text(img))
    print("────────────────────────────────────────────")
