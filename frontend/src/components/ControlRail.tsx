import { useState } from "react"
import { ChevronDown, Crosshair, Loader2 } from "lucide-react"
import type { GenerateParams, Info, Method } from "../api/client"
import { METHOD_LABEL } from "../lib/format"
import { cn } from "../lib/utils"

interface Props {
  info: Info | null
  params: GenerateParams
  onChange: (patch: Partial<GenerateParams>) => void
  onGenerate: () => void
  busy: boolean
  ready: boolean
}

function Segmented<T extends string | number>({
  value,
  options,
  onChange,
  label,
}: {
  value: T
  options: { value: T; label: string }[]
  onChange: (v: T) => void
  label: string
}) {
  return (
    <div role="radiogroup" aria-label={label} className="grid grid-flow-col gap-1 rounded-md border border-border bg-bg p-1">
      {options.map((o) => (
        <button
          key={String(o.value)}
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            "rounded-sm px-2 py-1.5 font-mono text-xs transition-colors",
            value === o.value
              ? "bg-primary/15 text-primary"
              : "text-ink-muted hover:bg-surface-2 hover:text-ink",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

function FieldLabel({ children, hint }: { children: React.ReactNode; hint?: string }) {
  return (
    <div className="mb-1.5 flex items-baseline justify-between">
      <span className="text-xs font-medium uppercase tracking-wide text-ink-faint">{children}</span>
      {hint && <span className="font-mono text-[11px] text-ink-faint">{hint}</span>}
    </div>
  )
}

export function ControlRail({ info, params, onChange, onGenerate, busy, ready }: Props) {
  const [advanced, setAdvanced] = useState(false)
  const methods = info?.methods ?? (["nearest", "bilinear", "bicubic", "lanczos"] as Method[])

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (ready && !busy) onGenerate()
      }}
      className="flex flex-col gap-5"
    >
      <div>
        <FieldLabel hint={`${params.targetText.length}/40`}>Hidden text</FieldLabel>
        <input
          value={params.targetText}
          onChange={(e) => onChange({ targetText: e.target.value.slice(0, 40) })}
          placeholder="SEND MONEY"
          className="w-full rounded-md border border-input bg-bg px-3 py-2 font-mono text-sm text-ink placeholder:text-ink-faint/60 focus-visible:border-primary/60 focus-visible:outline-none"
        />
        <p className="mt-1.5 text-xs text-ink-faint">Surfaces only after the image is downscaled.</p>
      </div>

      <div>
        <FieldLabel>Target algorithm</FieldLabel>
        <div className="grid grid-cols-2 gap-1 rounded-md border border-border bg-bg p-1">
          {methods.map((m) => (
            <button
              key={m}
              type="button"
              aria-pressed={params.method === m}
              onClick={() => onChange({ method: m })}
              className={cn(
                "rounded-sm px-2 py-1.5 font-mono text-xs transition-colors",
                params.method === m
                  ? "bg-primary/15 text-primary"
                  : "text-ink-muted hover:bg-surface-2 hover:text-ink",
              )}
            >
              {METHOD_LABEL[m]}
            </button>
          ))}
        </div>
      </div>

      <div>
        <FieldLabel hint={`${params.scale}× downscale`}>Scale factor</FieldLabel>
        <Segmented
          label="Scale factor"
          value={params.scale}
          onChange={(v) => onChange({ scale: v })}
          options={[2, 4, 8, 16].map((n) => ({ value: n, label: `${n}×` }))}
        />
      </div>

      <label className="flex cursor-pointer items-start justify-between gap-3 rounded-md border border-border bg-bg px-3 py-2.5">
        <span>
          <span className="block text-sm text-ink">Anti-aliased scaler</span>
          <span className="mt-0.5 block text-xs text-ink-faint">
            {params.antialias ? "Robust target (Pillow-style). Hard to hide." : "Sampling target (OpenCV-style). Stealthy."}
          </span>
        </span>
        <input
          type="checkbox"
          checked={params.antialias}
          onChange={(e) => onChange({ antialias: e.target.checked })}
          className="mt-0.5 h-4 w-4 accent-[oklch(0.70_0.115_185)]"
        />
      </label>

      <div>
        <button
          type="button"
          onClick={() => setAdvanced((v) => !v)}
          className="flex w-full items-center justify-between text-xs font-medium uppercase tracking-wide text-ink-faint transition-colors hover:text-ink-muted"
        >
          Stealth controls
          <ChevronDown className={cn("h-4 w-4 transition-transform", advanced && "rotate-180")} />
        </button>
        {advanced && (
          <div className="mt-3 space-y-4 animate-fade-up">
            <div>
              <FieldLabel hint={params.darkFrac >= 1 ? "off" : params.darkFrac.toFixed(2)}>
                Dark-region mask
              </FieldLabel>
              <input
                type="range"
                min={0.1}
                max={1}
                step={0.05}
                value={params.darkFrac}
                onChange={(e) => onChange({ darkFrac: parseFloat(e.target.value) })}
                className="w-full accent-[oklch(0.70_0.115_185)]"
              />
              <p className="mt-1 text-xs text-ink-faint">Confine edits to the darkest pixels.</p>
            </div>
            {params.darkFrac < 1 && (
              <div>
                <FieldLabel hint={String(params.iterations)}>Refine iterations</FieldLabel>
                <input
                  type="range"
                  min={1}
                  max={60}
                  step={1}
                  value={params.iterations}
                  onChange={(e) => onChange({ iterations: parseInt(e.target.value) })}
                  className="w-full accent-[oklch(0.70_0.115_185)]"
                />
              </div>
            )}
            <label className="flex cursor-pointer items-center justify-between gap-3">
              <span className="text-sm text-ink">Invert payload (dark text)</span>
              <input
                type="checkbox"
                checked={params.invert}
                onChange={(e) => onChange({ invert: e.target.checked })}
                className="h-4 w-4 accent-[oklch(0.70_0.115_185)]"
              />
            </label>
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={!ready || busy}
        className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary font-medium text-primary-foreground transition-[filter,opacity] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Crosshair className="h-4 w-4" />}
        {busy ? "Crafting payload…" : "Craft payload"}
      </button>
      {!ready && <p className="-mt-2 text-center text-xs text-ink-faint">Upload a decoy image to begin.</p>}
    </form>
  )
}
