import { Loader2, ShieldAlert, ShieldCheck } from "lucide-react"
import type { CompareResponse } from "../api/client"
import { LIBRARY_LABEL, METHOD_LABEL, fmt } from "../lib/format"

export function TransferGrid({ data, busy }: { data: CompareResponse | null; busy: boolean }) {
  if (busy) {
    return (
      <div className="flex items-center justify-center gap-2 rounded-md border border-border bg-surface py-10 text-sm text-ink-muted">
        <Loader2 className="h-4 w-4 animate-spin" /> Downscaling across libraries…
      </div>
    )
  }
  if (!data) return null

  const cells = data.results.filter((c) => c.image)

  return (
    <section className="space-y-3">
      <header className="flex items-baseline justify-between">
        <h2 className="text-sm font-medium text-ink">Cross-library transfer</h2>
        <span className="font-mono text-[11px] text-ink-faint">
          downscaled to {data.out_width}×{data.out_height}
        </span>
      </header>
      <p className="max-w-prose text-xs text-ink-faint">
        The same payload, downscaled by each installed library. A payload tuned for one sampling
        algorithm often dies under a different (especially anti-aliased) one — that gap is the defense.
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {cells.map((c) => {
          const ok = c.attack?.success
          return (
            <figure key={`${c.library}-${c.method}`} className="overflow-hidden rounded-md border border-border bg-surface">
              <img
                src={c.image}
                alt={`${c.library} ${c.method}`}
                style={{ imageRendering: "pixelated" }}
                className="aspect-[4/3] w-full bg-bg object-contain"
              />
              <figcaption className="space-y-1 border-t border-border px-2.5 py-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-ink">{LIBRARY_LABEL[c.library] ?? c.library}</span>
                  <span className="font-mono text-[11px] text-ink-faint">{METHOD_LABEL[c.method]}</span>
                </div>
                {c.attack && (
                  <div
                    className={
                      "inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-[11px] " +
                      (ok ? "bg-signal/15 text-signal" : "bg-surface-2 text-ink-muted")
                    }
                  >
                    {ok ? <ShieldAlert className="h-3 w-3" /> : <ShieldCheck className="h-3 w-3" />}
                    {ok ? "revealed" : "resisted"} · {fmt(c.attack.similarity, 2)}
                  </div>
                )}
              </figcaption>
            </figure>
          )
        })}
      </div>
    </section>
  )
}
