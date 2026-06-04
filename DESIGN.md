# Design

## Theme

Dark "forensic instrument." Near-black, pure-neutral surround so the images and
the teal readouts read like a lit measurement bench. One warm amber signal,
reserved exclusively for "payload revealed / attack succeeded."

## Color

OKLCH. Stored as `L C H` channels in CSS vars, consumed as
`oklch(var(--token) / <alpha-value>)` so Tailwind opacity modifiers work.

| Role | OKLCH | Use |
|------|-------|-----|
| bg | 0.145 0 0 | app background (pure near-black) |
| surface | 0.185 0.004 220 | panels |
| surface-2 | 0.225 0.006 220 | raised controls, inputs |
| border | 0.30 0.006 220 | hairlines |
| ink | 0.96 0 0 | primary text |
| ink-muted | 0.74 0.012 220 | secondary text (≥4.5:1) |
| ink-faint | 0.60 0.012 220 | labels, units |
| primary (teal) | 0.70 0.115 185 | interactive, "the scaler" |
| signal (amber) | 0.80 0.15 72 | success / payload revealed only |
| danger | 0.64 0.19 25 | errors |

Never signal state by color alone: amber always rides with an icon + label.

## Typography

- **IBM Plex Sans** — UI and prose. Technical, slightly humanist, not the Inter default.
- **IBM Plex Mono** — every number, parameter, metric, and code-like token.
  Numerics are first-class here; they live in mono.
- Scale via `clamp()`, ≥1.25 step ratio. Display heading max ~3.5rem (this is a
  tool, not a landing page). `text-wrap: balance` on headings.

## Layout

- A two-pane workbench: a fixed-width control rail (left) and the evidence
  canvas (right). Not a card grid.
- The evidence is two large framed images — decoy and downscaled payload —
  separated by a directional glyph, with a monospace metrics strip beneath.
- Cross-library transfer is a dense comparison table/grid below the fold.
- Hairline borders, not shadows, define structure (instrument panel feel).

## Motion

Restrained. Result frames fade/translate up on arrival (≤240ms, ease-out-quint).
A quiet scan shimmer on the payload frame while generating. Everything has a
`prefers-reduced-motion: reduce` fallback (instant, no transform).
