# Product

## Register

product

## Users

Security engineers, ML practitioners, and students studying multi-modal AI
safety. They arrive wanting to *see* an image-scaling attack actually work:
upload a normal-looking image, hide a prompt inside it, and watch the hidden
text surface when a downscaler shrinks it. Context is a lab/research setting,
not production. They care about whether the attack succeeds, how visible the
perturbation is, and which scaling algorithms are vulnerable vs. robust.

## Product Purpose

Descale crafts and explains image-scaling attacks for multi-modal prompt
injection (a reimplementation of the Trail of Bits research tool). It generates
a decoy image that looks benign at full resolution but collapses into attacker-
chosen text once downscaled, then *proves* the result: OCR success-check,
perceptual-difference metrics, and a side-by-side panel showing how the payload
transfers (or fails to transfer) across OpenCV / Pillow / PyTorch / TensorFlow.
Success looks like a user immediately understanding both the attack (sampling
scalers are exploitable) and the defense (anti-aliased scalers resist it).

## Brand Personality

Calibrated, forensic, quietly confident. It reads like a scientific instrument,
not a hacker toy or a marketing site. Voice is precise and factual: it states
measurements, not adjectives. Three words: instrument, evidence, clarity.

## Anti-references

- Generic SaaS dashboard (rounded cards in a 3-column grid, gradient hero).
- "Hacker terminal" cosplay: neon-green-on-black, scanlines, fake CLI logs.
- Anything that hides the images behind chrome. The images ARE the content.

## Design Principles

- **Show the evidence.** The decoy and its downscaled payload, side by side, are
  the center of the screen. Everything else is instrumentation around them.
- **Numbers are first-class.** SSIM, ΔE, residual, OCR similarity are displayed
  as precise monospace readouts, not buried.
- **Attack and defense in one view.** Always make it easy to see where the
  payload survives and where it dies.
- **Calm until it matters.** The interface is cool and neutral; the single warm
  signal is reserved for "payload revealed / attack succeeded."

## Accessibility & Inclusion

Target WCAG 2.1 AA: body text ≥4.5:1, large text ≥3:1, visible focus rings,
full keyboard operability, honor `prefers-reduced-motion`. Never encode success
or failure by color alone (pair the amber signal with an icon and text label).
