"""Adversarial image-scaling payload generator.

Goal: produce an image that looks like the *decoy* at full resolution but, once a
target downscaler shrinks it, collapses into the *target* (text we want a
multi-modal model to read).

Because downscaling is linear (OUT = A @ IN @ Cᵀ, see downsamplers.py), finding
the input that yields a desired output is a linear least-squares problem with a
closed-form solution. For a residual R we want the smallest perturbation `delta`
to the decoy such that  A · delta · Cᵀ = R.  The minimum-Frobenius-norm solution
is separable:

    delta = A⁺ · R · G          with   A⁺ = Aᵀ (A Aᵀ)⁻¹ ,   G = (C Cᵀ)⁻¹ C

All of this happens in linear light. Optional luma masking + iterative refinement
concentrate the perturbation in dark regions so it stays imperceptible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .colorspace import srgb_to_linear, linear_to_srgb, to_float, to_uint8
from .downsamplers import resize_matrix, matrix_downsample


# Rec. 709 luma weights
_LUMA = np.array([0.2126, 0.7152, 0.0722])


@dataclass
class GenerationResult:
    image: np.ndarray          # adversarial decoy, uint8 RGB (H,W,3)
    preview: np.ndarray        # what the target downscaler sees, uint8 RGB
    max_delta: float           # largest per-pixel sRGB change (0-255)
    mean_delta: float          # mean absolute sRGB change (0-255)
    residual: float            # mean abs error vs target after downscale (0-255)


def _axis_pinvs(in_size: int, out_size: int, method: str, antialias: bool):
    """Return (A for one axis as out x in, and its right pseudo-inverse in x out)."""
    A = resize_matrix(in_size, out_size, method, antialias)   # out x in
    A_pinv = A.T @ np.linalg.inv(A @ A.T)                      # in x out
    return A, A_pinv


def luma_mask(decoy_u8: np.ndarray, dark_frac: float, softness: float = 0.0) -> np.ndarray:
    """Allow perturbations only in the darkest `dark_frac` of the image.

    Returns an (H,W) float mask in [0,1]. dark_frac=1.0 -> no masking.
    """
    if dark_frac >= 1.0:
        return np.ones(decoy_u8.shape[:2], dtype=np.float64)
    luma = (to_float(decoy_u8) @ _LUMA)
    lo, hi = luma.min(), luma.max()
    if hi - lo < 1e-6:
        return np.ones_like(luma)
    norm = (luma - lo) / (hi - lo)
    thresh = dark_frac
    if softness <= 0.0:
        return (norm <= thresh).astype(np.float64)
    # smooth ramp around the threshold
    return np.clip((thresh + softness - norm) / (2 * softness), 0.0, 1.0)


def create_text_target(
    text: str,
    width: int,
    height: int,
    invert: bool = False,
    font_size: int | None = None,
) -> np.ndarray:
    """Render `text` to a (height,width,3) uint8 image: white on black by default
    (invert=True -> black on white). Font auto-sizes to fill the box."""
    bg, fg = ((255, 255, 255), (0, 0, 0)) if invert else ((0, 0, 0), (255, 255, 255))
    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    def load_font(size: int):
        for path in (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    if font_size is None:
        # binary-search a size that fits inside the box with a small margin
        lo, hi, best = 6, max(8, height), 6
        while lo <= hi:
            mid = (lo + hi) // 2
            f = load_font(mid)
            bbox = draw.multiline_textbbox((0, 0), text, font=f, align="center")
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if tw <= width * 0.92 and th <= height * 0.92:
                best, lo = mid, mid + 1
            else:
                hi = mid - 1
        font_size = best

    font = load_font(font_size)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - tw) / 2 - bbox[0]
    y = (height - th) / 2 - bbox[1]
    draw.multiline_text((x, y), text, fill=fg, font=font, align="center")
    return np.array(img)


class AdversarialGenerator:
    """Closed-form image-scaling attack.

    Parameters
    ----------
    method      : kernel to attack ('nearest'|'bilinear'|'bicubic'|'lanczos')
    dark_frac   : restrict changes to the darkest fraction of pixels (1.0 = off)
    mask_soft   : soften the luma-mask edge (0 = hard threshold)
    iterations  : refinement steps. 1 = exact closed-form (no mask). >1 lets a
                  masked solve converge while honouring the mask.
    eps         : null-space dither magnitude (adds texture the downscaler
                  cancels out, hiding solver patterns). 0 = off.
    """

    def __init__(self, method: str = "bicubic", dark_frac: float = 1.0,
                 mask_soft: float = 0.0, iterations: int = 1, eps: float = 0.0,
                 antialias: bool = False):
        self.method = method
        self.dark_frac = float(dark_frac)
        self.mask_soft = float(mask_soft)
        self.iterations = max(1, int(iterations))
        self.eps = float(eps)
        self.antialias = bool(antialias)

    def generate(self, decoy_u8: np.ndarray, target_u8: np.ndarray) -> GenerationResult:
        h, w = decoy_u8.shape[:2]
        out_h, out_w = target_u8.shape[:2]

        # Work in linear light.
        decoy_lin = srgb_to_linear(to_float(decoy_u8))
        target_lin = srgb_to_linear(to_float(target_u8))

        A, A_pinv = _axis_pinvs(h, out_h, self.method, self.antialias)   # rows
        C, C_pinv = _axis_pinvs(w, out_w, self.method, self.antialias)   # cols
        # G such that  delta = A_pinv @ R @ G   solves A·delta·Cᵀ = R
        G = (np.linalg.inv(C @ C.T) @ C)                       # out_w x w

        mask = luma_mask(decoy_u8, self.dark_frac, self.mask_soft)  # (h,w)
        mask3 = mask[:, :, None]
        masking = self.dark_frac < 1.0

        current = decoy_lin.copy()
        for _ in range(self.iterations if masking else 1):
            # residual in output space, per channel
            down = np.stack([A @ current[:, :, c] @ C.T for c in range(3)], axis=-1)
            R = target_lin - down
            step = np.stack([A_pinv @ R[:, :, c] @ G for c in range(3)], axis=-1)
            if masking:
                step = step * mask3
            current = current + step
            current = np.clip(current, 0.0, 1.0)
            if not masking:
                break

        # Null-space dither: noise shaped to vanish under this downscaler.
        if self.eps > 0.0:
            current = self._add_nullspace_dither(current, A, A_pinv, C, G)
            current = np.clip(current, 0.0, 1.0)

        adv_u8 = to_uint8(linear_to_srgb(current))

        # Verify against our own (matrix) downscaler.
        preview_lin = matrix_downsample(current, (out_h, out_w), self.method, self.antialias)
        preview_u8 = to_uint8(linear_to_srgb(preview_lin))

        delta = np.abs(adv_u8.astype(np.float64) - decoy_u8.astype(np.float64))
        residual = float(np.mean(np.abs(
            preview_u8.astype(np.float64) - target_u8.astype(np.float64))))

        return GenerationResult(
            image=adv_u8,
            preview=preview_u8,
            max_delta=float(delta.max()),
            mean_delta=float(delta.mean()),
            residual=residual,
        )

    def _add_nullspace_dither(self, current, A, A_pinv, C, G):
        """Add random noise then project out its visible (post-downscale)
        component, leaving only a null-space residue that the scaler discards."""
        rng = np.random.default_rng(0)
        noise = rng.standard_normal(current.shape) * self.eps
        # visible part = what survives downscaling, mapped back up
        for c in range(3):
            down = A @ noise[:, :, c] @ C.T
            visible = A_pinv @ down @ G
            noise[:, :, c] -= visible
        return current + noise
