"""Downsampling kernels expressed as explicit weight matrices.

The whole attack hinges on one fact: separable image downscaling is a *linear*
operation. Resizing an (H_in x W_in) image to (H_out x W_out) can be written as

    OUT = A @ IN @ Cᵀ                     (per colour channel)

where  A is (H_out x H_in)  resamples the rows (vertical axis), and
       C is (W_out x W_in)  resamples the columns (horizontal axis).

Because we know A and C exactly, we can *invert* the relationship and solve for
the input pixels that produce any desired output (see core/generators.py).

These matrices are built with PIL/Pillow's resampling convention (a kernel
stretched by the downscale ratio for anti-aliasing, half-pixel centre
alignment), which is the same convention most production scalers approximate.

The concrete image libraries (OpenCV / Pillow / PyTorch / TensorFlow) live in
`library_downsample` and are used for the cross-library comparison feature, to
show that a payload crafted for one scaler may or may not survive another.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# 1-D interpolation kernels (defined on the kernel's native, unscaled support)
# ---------------------------------------------------------------------------

def _nearest_kernel(x: float) -> float:
    return 1.0 if -0.5 <= x < 0.5 else 0.0


def _linear_kernel(x: float) -> float:
    x = abs(x)
    return (1.0 - x) if x < 1.0 else 0.0


def _make_cubic(a: float):
    def k(x: float) -> float:
        x = abs(x)
        if x < 1.0:
            return (a + 2.0) * x**3 - (a + 3.0) * x**2 + 1.0
        if x < 2.0:
            return a * x**3 - 5.0 * a * x**2 + 8.0 * a * x - 4.0 * a
        return 0.0
    return k


def _cubic_kernel(x: float, a: float = -0.5) -> float:
    """Keys cubic convolution kernel. a=-0.5 is Catmull-Rom (Pillow/MATLAB),
    a=-0.75 is what OpenCV uses for INTER_CUBIC."""
    return _make_cubic(a)(x)


def _lanczos_kernel(x: float, lobes: int = 3) -> float:
    if x == 0.0:
        return 1.0
    if abs(x) >= lobes:
        return 0.0
    px = np.pi * x
    return lobes * np.sin(px) * np.sin(px / lobes) / (px * px)


# name -> (kernel callable, native support radius)
KERNELS: dict[str, Tuple[Callable[[float], float], float]] = {
    "nearest": (_nearest_kernel, 0.5),
    "bilinear": (_linear_kernel, 1.0),
    "bicubic": (lambda x: _cubic_kernel(x, -0.5), 2.0),
    "lanczos": (lambda x: _lanczos_kernel(x, 3), 3.0),
}


def resize_matrix(in_size: int, out_size: int, method: str,
                  antialias: bool = False) -> np.ndarray:
    """Build the (out_size x in_size) row-stochastic resampling matrix for one
    axis.

    antialias=True   -> Pillow-style: the kernel is stretched by the downscale
                        ratio so every source pixel in the region contributes.
                        These scalers are *robust* (hard to attack stealthily).
    antialias=False  -> OpenCV / default-PyTorch / default-TensorFlow style: the
                        kernel keeps its native support and merely *samples* a
                        few pixels around each target centre. Most source pixels
                        get zero weight, which is exactly what makes the classic
                        image-scaling attack stealthy.

    For bicubic we use a=-0.5 (Catmull-Rom) when anti-aliasing and a=-0.75 (the
    OpenCV constant) when sampling, so verification matches the real library.
    """
    if method not in KERNELS:
        raise ValueError(f"unknown method '{method}'")
    kernel, support = KERNELS[method]
    if method == "bicubic" and not antialias:
        kernel = _make_cubic(-0.75)

    ratio = in_size / out_size
    filter_scale = max(1.0, ratio) if antialias else 1.0
    scaled_support = support * filter_scale

    M = np.zeros((out_size, in_size), dtype=np.float64)
    for i in range(out_size):
        center = (i + 0.5) * ratio - 0.5
        left = int(np.ceil(center - scaled_support))
        right = int(np.floor(center + scaled_support))
        weights = []
        idxs = []
        for j in range(left, right + 1):
            jj = min(max(j, 0), in_size - 1)  # clamp (edge replication)
            w = kernel((j - center) / filter_scale)
            if w != 0.0:
                weights.append(w)
                idxs.append(jj)
        if not weights:  # degenerate (e.g. nearest landing between samples)
            idxs = [min(max(int(round(center)), 0), in_size - 1)]
            weights = [1.0]
        weights = np.array(weights, dtype=np.float64)
        weights /= weights.sum()
        for jj, w in zip(idxs, weights):
            M[i, jj] += w
    return M


def matrix_downsample(image: np.ndarray, out_hw: Tuple[int, int], method: str,
                      antialias: bool = False) -> np.ndarray:
    """Downsample using our explicit matrices. `image` is (H,W,C) float.
    `out_hw` is (out_h, out_w). Returns float (out_h, out_w, C)."""
    h, w = image.shape[:2]
    out_h, out_w = out_hw
    A = resize_matrix(h, out_h, method, antialias)        # (out_h x h)
    C = resize_matrix(w, out_w, method, antialias)        # (out_w x w)
    chans = []
    for c in range(image.shape[2]):
        chans.append(A @ image[:, :, c] @ C.T)
    return np.stack(chans, axis=-1)


# ---------------------------------------------------------------------------
# Real-library downsamplers (for the cross-library comparison feature)
# ---------------------------------------------------------------------------

class Downsampler(ABC):
    @abstractmethod
    def downsample(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """image: (H,W,C) uint8 RGB. target_size: (width, height). -> uint8 RGB."""


def library_downsample(image_u8: np.ndarray, out_wh: Tuple[int, int], library: str, method: str) -> np.ndarray:
    """Downsample with a concrete library so we can compare real behaviour.
    out_wh is (width, height) to match the libraries' conventions."""
    out_w, out_h = out_wh
    library = library.lower()

    if library == "opencv":
        import cv2
        interp = {
            "nearest": cv2.INTER_NEAREST,
            "bilinear": cv2.INTER_LINEAR,
            "bicubic": cv2.INTER_CUBIC,
            "lanczos": cv2.INTER_LANCZOS4,
            "area": cv2.INTER_AREA,
        }.get(method, cv2.INTER_CUBIC)
        return cv2.resize(image_u8, (out_w, out_h), interpolation=interp)

    if library == "pillow":
        from PIL import Image
        resample = {
            "nearest": Image.NEAREST,
            "bilinear": Image.BILINEAR,
            "bicubic": Image.BICUBIC,
            "lanczos": Image.LANCZOS,
        }.get(method, Image.BICUBIC)
        return np.array(Image.fromarray(image_u8).resize((out_w, out_h), resample=resample))

    if library == "pytorch":
        import torch
        import torch.nn.functional as F
        mode = {
            "nearest": "nearest",
            "bilinear": "bilinear",
            "bicubic": "bicubic",
        }.get(method, "bicubic")
        t = torch.from_numpy(image_u8).permute(2, 0, 1).unsqueeze(0).float()
        kwargs = {"size": (out_h, out_w), "mode": mode}
        if mode != "nearest":
            kwargs["align_corners"] = False
            kwargs["antialias"] = True
        out = F.interpolate(t, **kwargs)
        out = out.clamp(0, 255).squeeze(0).permute(1, 2, 0).numpy()
        return out.round().astype(np.uint8)

    if library == "tensorflow":
        import tensorflow as tf
        mode = {
            "nearest": "nearest",
            "bilinear": "bilinear",
            "bicubic": "bicubic",
            "lanczos": "lanczos3",
        }.get(method, "bicubic")
        t = tf.convert_to_tensor(image_u8, dtype=tf.float32)
        out = tf.image.resize(t, (out_h, out_w), method=mode, antialias=True)
        return tf.cast(tf.round(tf.clip_by_value(out, 0, 255)), tf.uint8).numpy()

    raise ValueError(f"unknown library '{library}'")


def available_libraries() -> dict[str, bool]:
    """Report which optional image libraries are importable in this env."""
    status = {"opencv": False, "pillow": False, "pytorch": False, "tensorflow": False}
    for name, mod in (("opencv", "cv2"), ("pillow", "PIL"),
                      ("pytorch", "torch"), ("tensorflow", "tensorflow")):
        try:
            __import__(mod)
            status[name] = True
        except Exception:
            status[name] = False
    return status
