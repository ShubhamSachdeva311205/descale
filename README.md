# Descale

**Craft and analyze image-scaling attacks for multi-modal prompt injection.**

Many AI pipelines downscale large images before sending them to a model.
Descale exploits that step: it generates a *decoy* image that looks benign at
full resolution but collapses into attacker-chosen text once a downscaler shrinks
it. The model then "reads" a prompt the human uploader never saw.

This is a from-scratch reimplementation of the technique behind
[Trail of Bits' Anamorpher](https://github.com/trailofbits/anamorpher) and the
image-scaling attack literature (Xiao et al., USENIX 2019; Quiring et al.),
rebuilt with a correct closed-form solver, an attack-success checker, and a
forensic-instrument UI. **For security research and education only.**

![empty state](docs/screenshot-empty.png)

---

## What makes it actually work

The original prototype used a naive "upscale the error and add it back" loop,
which does not reliably reveal the hidden text. This version models downscaling
for what it is, a **linear operator**, and inverts it:

- Resizing an image is `OUT = A · IN · Cᵀ` per colour channel, where `A` and `C`
  are the row/column resampling weight matrices for the chosen kernel
  (`backend/core/downsamplers.py`).
- Given a decoy `D` and a target `T`, the smallest perturbation `δ` with
  `A · δ · Cᵀ = T − A·D·Cᵀ` has a closed form:
  `δ = A⁺ · R · G` (`backend/core/generators.py`).
- All of it happens in **linear-RGB** light, because that is the only space where
  pixel averaging is physically correct.
- A **luma mask** + iterative refinement can confine the perturbation to dark
  regions for extra stealth.

### Attack *and* defense

The solver targets two scaler families, which tells the whole security story:

| Scaler family | Example | Result |
|---|---|---|
| **Sampling** (no anti-aliasing) | OpenCV default, PyTorch/TF default | Stealthy attack: ~1–10% of pixels change, payload survives |
| **Anti-aliased** | Pillow, PyTorch `antialias=True` | Robust: hiding the payload requires rewriting the whole image, so it is obvious |

So **anti-aliased downscaling is a practical defense**. The cross-library panel
lets you watch a payload tuned for OpenCV get *resisted* by Pillow.

---

## Features

- **Closed-form payload generation** for nearest / bilinear / bicubic / lanczos.
- **OCR attack-success check** (Tesseract): reads the downscaled image back and
  scores it against the intended text.
- **Perceptual metrics**: SSIM, PSNR, CIEDE2000 ΔE, % pixels changed.
- **Cross-library transfer panel**: downscale the payload with OpenCV / Pillow /
  PyTorch / TensorFlow (whichever are installed) and see where it survives.
- **Stealth controls**: dark-region luma masking, refinement iterations.
- **Forensic-instrument UI**: React 19 + Vite + Tailwind, dark theme, the decoy
  and its downscaled payload side by side with live readouts.

---

## Architecture

```
descale/
├── backend/                 FastAPI service
│   ├── core/
│   │   ├── colorspace.py     sRGB <-> linear
│   │   ├── downsamplers.py   weight matrices + real-library scalers
│   │   ├── generators.py     closed-form attack solver
│   │   └── analysis.py       OCR success-check + perceptual metrics
│   ├── api/endpoints.py      /info /generate /compare /downsample
│   └── tests/                pytest
└── frontend/                React + Vite + Tailwind (IBM Plex, OKLCH tokens)
```

## Running it

### Backend (Python 3.10+)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# from the project root, so the package imports resolve:
cd .. && uvicorn backend.main:app --reload --port 8000
```

OCR uses Tesseract. On macOS: `brew install tesseract`. Optional: install
`torch` / `tensorflow` to add them to the cross-library panel.

### Frontend (Node 18+)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Set `VITE_API_URL` if the API is not on `http://localhost:8000/api`.

### Tests

```bash
source backend/.venv/bin/activate
python -m pytest backend/tests -q
```

---

## API

| Method | Path | Purpose |
|---|---|---|
| `GET`  | `/api/info` | versions, available libraries, OCR status |
| `POST` | `/api/generate` | craft a payload (returns base64 images + metrics + OCR verdict) |
| `POST` | `/api/compare` | downscale an image across libraries/methods + OCR each |
| `POST` | `/api/downsample` | single downscale (PNG) |

`generate` takes a multipart `file` plus `target_text`, `method`, `antialias`,
`scale` (integer downscale factor), and the stealth params.

---

## Ethics

This tool exists to help people understand and defend against image-scaling
attacks. Only use it on systems you own or are authorized to test. The default
payloads are harmless ("SEND MONEY") and meant to demonstrate the mechanism.
