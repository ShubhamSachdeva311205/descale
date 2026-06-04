"""sRGB <-> linear-RGB conversions.

Image-scaling algorithms average pixel values, and that averaging is only
physically correct in *linear* light. Operating directly on gamma-encoded sRGB
values produces the wrong result (and a visibly wrong attack). Every step of the
adversarial solve therefore happens in linear space; we convert in at the start
and out at the very end.

All functions take/return float arrays normalised to [0, 1].
"""

import numpy as np


def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    """Convert gamma-encoded sRGB in [0,1] to linear RGB in [0,1]."""
    srgb = np.asarray(srgb, dtype=np.float64)
    return np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        ((srgb + 0.055) / 1.055) ** 2.4,
    )


def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """Convert linear RGB in [0,1] back to gamma-encoded sRGB in [0,1]."""
    linear = np.clip(np.asarray(linear, dtype=np.float64), 0.0, 1.0)
    return np.where(
        linear <= 0.0031308,
        linear * 12.92,
        1.055 * (linear ** (1.0 / 2.4)) - 0.055,
    )


def to_float(image_u8: np.ndarray) -> np.ndarray:
    """uint8 [0,255] -> float [0,1]."""
    return np.asarray(image_u8, dtype=np.float64) / 255.0


def to_uint8(image_f: np.ndarray) -> np.ndarray:
    """float [0,1] -> uint8 [0,255] with rounding + clipping."""
    return np.clip(np.round(np.asarray(image_f) * 255.0), 0, 255).astype(np.uint8)
