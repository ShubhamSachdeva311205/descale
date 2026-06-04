import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api"

export const api = axios.create({ baseURL: API_URL })

// ---- types -----------------------------------------------------------------

export type Method = "nearest" | "bilinear" | "bicubic" | "lanczos"
export type Library = "opencv" | "pillow" | "pytorch" | "tensorflow"

export interface Info {
  version: string
  methods: Method[]
  libraries: Record<Library, boolean>
  ocr_available: boolean
  defaults: { method: Method; antialias: boolean; scale: number; dark_frac: number }
}

export interface Metrics {
  ssim: number | null
  psnr: number
  delta_e: number | null
  max_delta: number
  mean_delta: number
  pct_pixels_changed: number
}

export interface AttackResult {
  available: boolean
  extracted: string | null
  similarity: number | null
  success: boolean | null
}

export interface GenerateParams {
  targetText: string
  method: Method
  antialias: boolean
  scale: number
  darkFrac: number
  iterations: number
  eps: number
  invert: boolean
}

export interface GenerateResponse {
  params: Record<string, unknown> & { out_width: number; out_height: number; scale: number }
  images: { decoy: string; adversarial: string; preview: string; target: string }
  metrics: Metrics
  attack: AttackResult
  residual: number
}

export interface CompareCell {
  library: Library
  method: Method
  image?: string
  error?: string
  attack?: AttackResult
}

export interface CompareResponse {
  scale: number
  out_width: number
  out_height: number
  results: CompareCell[]
}

// ---- calls ------------------------------------------------------------------

export async function getInfo(): Promise<Info> {
  const { data } = await api.get<Info>("/info")
  return data
}

export async function generate(file: File, p: GenerateParams): Promise<GenerateResponse> {
  const fd = new FormData()
  fd.append("file", file)
  fd.append("target_text", p.targetText)
  fd.append("method", p.method)
  fd.append("antialias", String(p.antialias))
  fd.append("scale", String(p.scale))
  fd.append("dark_frac", String(p.darkFrac))
  fd.append("iterations", String(p.iterations))
  fd.append("eps", String(p.eps))
  fd.append("invert", String(p.invert))
  const { data } = await api.post<GenerateResponse>("/generate", fd)
  return data
}

export async function compare(
  file: File,
  opts: { targetText?: string; scale: number; methods?: Method[]; libraries?: Library[] },
): Promise<CompareResponse> {
  const fd = new FormData()
  fd.append("file", file)
  fd.append("target_text", opts.targetText ?? "")
  fd.append("scale", String(opts.scale))
  if (opts.methods) fd.append("methods", opts.methods.join(","))
  if (opts.libraries) fd.append("libraries", opts.libraries.join(","))
  const { data } = await api.post<CompareResponse>("/compare", fd)
  return data
}

/** data:image/png;base64,... -> File, for feeding a generated image back in. */
export async function dataUrlToFile(dataUrl: string, name = "adversarial.png"): Promise<File> {
  const blob = await (await fetch(dataUrl)).blob()
  return new File([blob], name, { type: "image/png" })
}
