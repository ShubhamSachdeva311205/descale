"""HTTP API for Descale.

Endpoints
  GET  /api/info       capabilities (methods, which image libs are installed)
  POST /api/generate   craft an adversarial decoy from an uploaded image
  POST /api/compare    downscale an image across libraries/methods + OCR check
  POST /api/downsample single downscale utility (returns PNG)
"""

from __future__ import annotations

import base64
import io
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image

from ..core import analysis
from ..core.downsamplers import (
    KERNELS,
    available_libraries,
    library_downsample,
)
from ..core.generators import AdversarialGenerator, create_text_target

router = APIRouter()

METHODS = list(KERNELS.keys())


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def read_image(file_bytes: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return np.array(img)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid image: {exc}")


def png_b64(image: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(image).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def crop_to_scale(image: np.ndarray, scale: int) -> np.ndarray:
    """Crop the image so each dimension is an exact multiple of `scale`.

    Integer downscale ratios are what make the attack reliable: each output pixel
    maps cleanly onto a fixed block of source pixels, so the solver hits the
    target without clipping overshoot. (Non-integer ratios force per-pixel
    overshoot that clamping then breaks.)
    """
    h, w = image.shape[:2]
    return image[: h - h % scale, : w - w % scale]


def out_dims(image: np.ndarray, scale: int) -> tuple[int, int]:
    """(out_h, out_w) for an already scale-cropped image."""
    h, w = image.shape[:2]
    return h // scale, w // scale


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #
@router.get("/info")
async def info():
    libs = available_libraries()
    return {
        "version": "3.0.0",
        "methods": METHODS,
        "libraries": libs,
        "ocr_available": _tesseract_present(),
        "defaults": {
            "method": "bicubic",
            "antialias": False,
            "scale": 8,
            "dark_frac": 1.0,
        },
    }


def _tesseract_present() -> bool:
    try:
        import pytesseract  # noqa: F401
        from shutil import which
        return which("tesseract") is not None
    except Exception:
        return False


@router.post("/generate")
async def generate(
    file: UploadFile = File(...),
    target_text: str = Form(...),
    method: str = Form("bicubic"),
    antialias: bool = Form(False),
    scale: int = Form(8),
    dark_frac: float = Form(1.0),
    mask_soft: float = Form(0.0),
    iterations: int = Form(1),
    eps: float = Form(0.0),
    invert: bool = Form(False),
):
    if method not in METHODS:
        raise HTTPException(400, f"method must be one of {METHODS}")
    scale = max(2, min(scale, 16))

    decoy = crop_to_scale(read_image(await file.read()), scale)
    out_h, out_w = out_dims(decoy, scale)
    target = create_text_target(target_text, out_w, out_h, invert=invert)

    gen = AdversarialGenerator(
        method=method,
        dark_frac=dark_frac,
        mask_soft=mask_soft,
        iterations=iterations,
        eps=eps,
        antialias=antialias,
    )
    result = gen.generate(decoy, target)

    metrics = analysis.perceptual_metrics(decoy, result.image)
    attack = analysis.attack_success(result.preview, target_text)

    return {
        "params": {
            "method": method, "antialias": antialias, "scale": scale,
            "out_width": out_w, "out_height": out_h, "dark_frac": dark_frac,
            "iterations": iterations, "eps": eps, "target_text": target_text,
        },
        "images": {
            "decoy": png_b64(decoy),
            "adversarial": png_b64(result.image),
            "preview": png_b64(result.preview),   # what the scaler "sees"
            "target": png_b64(target),
        },
        "metrics": metrics,
        "attack": attack,
        "residual": result.residual,
    }


@router.post("/compare")
async def compare(
    file: UploadFile = File(...),
    target_text: str = Form(""),
    scale: int = Form(8),
    methods: Optional[str] = Form(None),     # comma-separated
    libraries: Optional[str] = Form(None),   # comma-separated
):
    """Downscale the uploaded (adversarial) image with every requested
    library+method and report what surfaces. Demonstrates that a payload tuned
    for one scaler may not transfer to another."""
    scale = max(2, min(scale, 16))
    image = crop_to_scale(read_image(await file.read()), scale)
    out_h, out_w = out_dims(image, scale)

    avail = available_libraries()
    chosen_methods = [m for m in (methods.split(",") if methods else METHODS) if m in METHODS]
    chosen_libs = [
        l for l in (libraries.split(",") if libraries else avail.keys())
        if avail.get(l, False)
    ]

    results = []
    for lib in chosen_libs:
        for method in chosen_methods:
            try:
                down = library_downsample(image, (out_w, out_h), lib, method)
            except Exception as exc:  # noqa: BLE001
                results.append({"library": lib, "method": method, "error": str(exc)})
                continue
            entry = {
                "library": lib,
                "method": method,
                "image": png_b64(down),
            }
            if target_text:
                entry["attack"] = analysis.attack_success(down, target_text)
            results.append(entry)

    return {"scale": scale, "out_width": out_w, "out_height": out_h, "results": results}


@router.post("/downsample")
async def downsample(
    file: UploadFile = File(...),
    library: str = Form("opencv"),
    method: str = Form("bicubic"),
    scale: int = Form(8),
):
    scale = max(2, min(scale, 16))
    image = crop_to_scale(read_image(await file.read()), scale)
    out_h, out_w = out_dims(image, scale)
    try:
        down = library_downsample(image, (out_w, out_h), library, method)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, str(exc))
    buf = io.BytesIO()
    Image.fromarray(down).save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
