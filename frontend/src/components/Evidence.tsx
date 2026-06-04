import { ArrowRight, CheckCircle2, Download, ScanSearch, ShieldAlert, ShieldQuestion } from "lucide-react"
import type { GenerateResponse } from "../api/client"
import { fmt, pct } from "../lib/format"

function Frame({
  src,
  title,
  caption,
  tone = "neutral",
  pixelated = false,
}: {
  src: string
  title: string
  caption: string
  tone?: "neutral" | "signal"
  pixelated?: boolean
}) {
  return (
    <figure className="flex min-w-0 flex-1 flex-col">
      <figcaption className="mb-2 flex items-baseline justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-wide text-ink-faint">{title}</span>
        <span className="font-mono text-[11px] text-ink-faint">{caption}</span>
      </figcaption>
      <div
        className={
          "relative overflow-hidden rounded-md border bg-bg " +
          (tone === "signal" ? "border-signal/40" : "border-border")
        }
      >
        <img
          src={src}
          alt={title}
          style={pixelated ? { imageRendering: "pixelated" } : undefined}
          className="aspect-[4/3] w-full bg-[oklch(0.1_0_0)] object-contain"
        />
      </div>
    </figure>
  )
}

function Metric({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="flex flex-col gap-0.5 px-3 py-2">
      <span className="text-[10px] uppercase tracking-wide text-ink-faint">{label}</span>
      <span className="font-mono text-sm text-ink">
        {value}
        {unit && <span className="ml-0.5 text-xs text-ink-faint">{unit}</span>}
      </span>
    </div>
  )
}

export function Evidence({
  result,
  busy,
  onDownload,
  onProbe,
}: {
  result: GenerateResponse
  busy: boolean
  onDownload: () => void
  onProbe: () => void
}) {
  const { images, metrics, attack, params, residual } = result
  const verdict = attack.success

  return (
    <div className="animate-fade-up space-y-5">
      <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
        <Frame
          src={images.adversarial}
          title="Decoy (full resolution)"
          caption={`${params.out_width * params.scale}×${params.out_height * params.scale}`}
        />
        <ArrowRight className="mx-auto hidden h-5 w-5 shrink-0 text-ink-faint sm:block" />
        <div className="mx-auto h-px w-12 bg-border sm:hidden" />
        <div className="relative min-w-0 flex-1">
          <Frame
            src={images.preview}
            title="What the scaler sees"
            caption={`${params.out_width}×${params.out_height}`}
            tone="signal"
            pixelated
          />
          {busy && (
            <div className="pointer-events-none absolute inset-x-0 top-7 bottom-0 overflow-hidden rounded-md">
              <div className="absolute inset-x-0 h-12 animate-scan bg-gradient-to-b from-transparent via-primary/15 to-transparent" />
            </div>
          )}
        </div>
      </div>

      {/* verdict */}
      <div
        className={
          "flex items-start gap-3 rounded-md border px-4 py-3 " +
          (verdict === true
            ? "border-signal/40 bg-signal/10"
            : verdict === false
              ? "border-border bg-surface"
              : "border-border bg-surface")
        }
      >
        {verdict === true ? (
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-signal" />
        ) : verdict === false ? (
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-ink-muted" />
        ) : (
          <ShieldQuestion className="mt-0.5 h-5 w-5 shrink-0 text-ink-muted" />
        )}
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink">
            {verdict === true
              ? "Payload revealed — attack succeeded"
              : verdict === false
                ? "Payload not legible after downscale"
                : attack.available
                  ? "Inconclusive"
                  : "OCR unavailable (install Tesseract to auto-verify)"}
          </p>
          {attack.available && (
            <p className="mt-0.5 truncate font-mono text-xs text-ink-muted">
              OCR read: “{attack.extracted || "—"}” · similarity {fmt(attack.similarity, 2)}
            </p>
          )}
        </div>
      </div>

      {/* metrics + actions */}
      <div className="overflow-hidden rounded-md border border-border bg-surface">
        <div className="grid grid-cols-2 divide-x divide-border border-b border-border sm:grid-cols-4">
          <Metric label="SSIM" value={fmt(metrics.ssim, 3)} />
          <Metric label="ΔE (CIEDE2000)" value={fmt(metrics.delta_e, 2)} />
          <Metric label="PSNR" value={fmt(metrics.psnr, 1)} unit="dB" />
          <Metric label="Pixels changed" value={pct(metrics.pct_pixels_changed)} />
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 px-3 py-2.5">
          <span className="font-mono text-xs text-ink-faint">
            mean Δ {fmt(metrics.mean_delta, 1)} · max Δ {fmt(metrics.max_delta, 0)} · residual {fmt(residual, 2)}
          </span>
          <div className="flex gap-2">
            <button
              onClick={onProbe}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
            >
              <ScanSearch className="h-3.5 w-3.5" /> Test transfer
            </button>
            <button
              onClick={onDownload}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary/15 px-3 py-1.5 text-xs text-primary transition-colors hover:bg-primary/25"
            >
              <Download className="h-3.5 w-3.5" /> Download payload
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
