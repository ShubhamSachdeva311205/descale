import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.core.generators import AdversarialGenerator, create_text_target

client = TestClient(app)


def _decoy_png(size=320):
    yy, xx = np.mgrid[0:size, 0:size]
    img = np.stack([
        (140 + 70 * np.sin(xx / 30)).clip(0, 255),
        (140 + 70 * np.cos(yy / 35)).clip(0, 255),
        (120 + 60 * np.sin((xx + yy) / 45)).clip(0, 255),
    ], axis=-1).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_info():
    j = client.get("/api/info").json()
    assert "bicubic" in j["methods"]
    assert j["libraries"]["opencv"] is True
    assert j["libraries"]["pillow"] is True


@pytest.mark.parametrize("method", ["nearest", "bilinear", "bicubic", "lanczos"])
def test_attack_is_exact_against_matching_scaler(method):
    """The crafted image must reproduce the target almost exactly under its own
    (sampling) scaler — this is the core correctness guarantee."""
    decoy = np.array(Image.open(_decoy_png()).convert("RGB"))
    target = create_text_target("HELLO", 40, 40)
    res = AdversarialGenerator(method=method, antialias=False).generate(decoy, target)
    assert res.residual < 5.0          # near-perfect reconstruction
    assert res.mean_delta < 30.0       # and reasonably stealthy


def test_generate_endpoint():
    r = client.post(
        "/api/generate",
        files={"file": ("d.png", _decoy_png(), "image/png")},
        data={"target_text": "SEND MONEY", "method": "bilinear", "scale": 8},
    )
    assert r.status_code == 200
    j = r.json()
    assert set(j["images"]) == {"decoy", "adversarial", "preview", "target"}
    assert j["images"]["adversarial"].startswith("data:image/png;base64,")
    assert j["metrics"]["ssim"] is not None
    assert j["residual"] < 5.0


def test_compare_endpoint():
    r = client.post(
        "/api/compare",
        files={"file": ("d.png", _decoy_png(), "image/png")},
        data={"scale": 8, "methods": "bilinear", "libraries": "opencv,pillow"},
    )
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 2
    assert all("image" in e for e in results)


def test_downsample_endpoint():
    r = client.post(
        "/api/downsample",
        files={"file": ("d.png", _decoy_png(), "image/png")},
        data={"method": "bicubic", "library": "opencv", "scale": 8},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
