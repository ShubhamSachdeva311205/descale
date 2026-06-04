"""Post-attack analysis: perceptual quality + attack-success validation.

Two questions a user asks after generating a payload:
  1. "Is the change actually invisible?"  -> perceptual metrics (SSIM, PSNR, ΔE).
  2. "Will a model actually read the hidden text?" -> OCR on the downscaled image.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Optional

import numpy as np


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return float(10.0 * np.log10(255.0**2 / mse))


def ssim(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    try:
        from skimage.metrics import structural_similarity
        return float(structural_similarity(a, b, channel_axis=-1))
    except Exception:
        return None


def delta_e(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    """Mean CIEDE2000 colour difference (perceptual). Lower = closer."""
    try:
        from skimage.color import rgb2lab, deltaE_ciede2000
        lab_a = rgb2lab(a.astype(np.float64) / 255.0)
        lab_b = rgb2lab(b.astype(np.float64) / 255.0)
        return float(np.mean(deltaE_ciede2000(lab_a, lab_b)))
    except Exception:
        return None


def perceptual_metrics(decoy: np.ndarray, adversarial: np.ndarray) -> dict:
    """How visible is the perturbation between decoy and adversarial?"""
    diff = np.abs(decoy.astype(np.int16) - adversarial.astype(np.int16))
    return {
        "ssim": ssim(decoy, adversarial),
        "psnr": psnr(decoy, adversarial),
        "delta_e": delta_e(decoy, adversarial),
        "max_delta": float(diff.max()),
        "mean_delta": float(diff.mean()),
        "pct_pixels_changed": float(np.mean(diff.max(axis=-1) > 8) * 100.0),
    }


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def ocr_text(image: np.ndarray) -> Optional[str]:
    """Read text from an image with Tesseract, if available.

    Tries pytesseract first; falls back to invoking the `tesseract` CLI with an
    explicit temp file (robust to unusual TMPDIR setups where pytesseract's
    own temp file isn't reachable by the subprocess)."""
    from PIL import Image as _Image
    try:
        import pytesseract
        txt = pytesseract.image_to_string(_Image.fromarray(image))
        if txt.strip():
            return txt.strip()
    except Exception:
        pass

    # CLI fallback
    import os
    import subprocess
    import tempfile
    from shutil import which
    if which("tesseract") is None:
        return None
    fd, path = tempfile.mkstemp(suffix=".png", dir=os.getcwd())
    try:
        os.close(fd)
        _Image.fromarray(image).save(path)
        out = subprocess.run(
            ["tesseract", path, "stdout"], capture_output=True, text=True, timeout=30
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None
    finally:
        if os.path.exists(path):
            os.remove(path)


def attack_success(downscaled: np.ndarray, target_text: str) -> dict:
    """Did the hidden text actually surface after downscaling? Uses OCR +
    fuzzy string similarity against the intended target text."""
    extracted = ocr_text(downscaled)
    if extracted is None:
        return {"available": False, "extracted": None, "similarity": None, "success": None}
    ratio = SequenceMatcher(None, _normalize(extracted), _normalize(target_text)).ratio()
    return {
        "available": True,
        "extracted": extracted,
        "similarity": round(ratio, 3),
        "success": ratio >= 0.6,
    }
