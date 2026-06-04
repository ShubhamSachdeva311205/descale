export const fmt = (v: number | null | undefined, digits = 2, dash = "—") =>
  v === null || v === undefined || Number.isNaN(v) ? dash : v.toFixed(digits)

export const pct = (v: number | null | undefined, digits = 1) =>
  v === null || v === undefined ? "—" : `${v.toFixed(digits)}%`

export const LIBRARY_LABEL: Record<string, string> = {
  opencv: "OpenCV",
  pillow: "Pillow",
  pytorch: "PyTorch",
  tensorflow: "TensorFlow",
}

export const METHOD_LABEL: Record<string, string> = {
  nearest: "Nearest",
  bilinear: "Bilinear",
  bicubic: "Bicubic",
  lanczos: "Lanczos",
}
