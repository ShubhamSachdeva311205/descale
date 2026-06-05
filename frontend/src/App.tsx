import { useEffect, useMemo, useState } from "react"
import { Github, ImageOff, Layers, ScanLine } from "lucide-react"
import { Dropzone } from "./components/Dropzone"
import { ControlRail } from "./components/ControlRail"
import { Evidence } from "./components/Evidence"
import { TransferGrid } from "./components/TransferGrid"
import {
  type CompareResponse,
  type GenerateParams,
  type GenerateResponse,
  type Info,
  type Library,
  compare,
  dataUrlToFile,
  generate,
  getInfo,
} from "./api/client"

const DEFAULTS: GenerateParams = {
  targetText: "SEND MONEY",
  method: "bicubic",
  antialias: false,
  scale: 8,
  darkFrac: 1,
  iterations: 12,
  eps: 0,
  invert: false,
}

type Status = "connecting" | "online" | "offline"

function StatusBadge({ status, version }: { status: Status; version?: string }) {
  const dot =
    status === "online" ? "bg-primary" : status === "offline" ? "bg-destructive" : "bg-ink-faint"
  const label =
    status === "online" ? `backend ${version ?? ""}`.trim() : status === "offline" ? "backend offline" : "connecting…"
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 font-mono text-[11px] text-ink-muted">
      <span className={`h-1.5 w-1.5 rounded-full ${dot} ${status === "connecting" ? "animate-pulse-soft" : ""}`} />
      {label}
    </span>
  )
}

export default function App() {
  const [info, setInfo] = useState<Info | null>(null)
  const [status, setStatus] = useState<Status>("connecting")

  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [params, setParams] = useState<GenerateParams>(DEFAULTS)

  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [transfer, setTransfer] = useState<CompareResponse | null>(null)
  const [transferBusy, setTransferBusy] = useState(false)

  useEffect(() => {
    getInfo()
      .then((i) => {
        setInfo(i)
        setStatus("online")
        setParams((p) => ({ ...p, method: i.defaults.method, scale: i.defaults.scale }))
      })
      .catch(() => setStatus("offline"))
  }, [])

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const onChange = (patch: Partial<GenerateParams>) => setParams((p) => ({ ...p, ...patch }))

  const onSelect = (f: File) => {
    setFile(f)
    setResult(null)
    setTransfer(null)
    setError(null)
  }

  const onClear = () => {
    setFile(null)
    setResult(null)
    setTransfer(null)
    setError(null)
  }

  const onGenerate = async () => {
    if (!file) return
    setBusy(true)
    setError(null)
    setTransfer(null)
    try {
      setResult(await generate(file, params))
    } catch {
      setError(
        status === "offline"
          ? "Backend offline. Start the API on :8000."
          : "Generation failed. Check the API logs.",
      )
    } finally {
      setBusy(false)
    }
  }

  const onDownload = () => {
    if (!result) return
    const a = document.createElement("a")
    a.href = result.images.adversarial
    a.download = `descale_${params.method}_${params.scale}x.png`
    a.click()
  }

  const onProbe = async () => {
    if (!result) return
    setTransferBusy(true)
    try {
      const advFile = await dataUrlToFile(result.images.adversarial)
      const libs = info
        ? (Object.keys(info.libraries) as Library[]).filter((l) => info.libraries[l])
        : undefined
      setTransfer(
        await compare(advFile, {
          targetText: params.targetText,
          scale: params.scale,
          methods: ["nearest", "bilinear", "bicubic", "lanczos"],
          libraries: libs,
        }),
      )
    } catch {
      /* surfaced via empty grid */
    } finally {
      setTransferBusy(false)
    }
  }

  const ready = !!file
  const libsOn = useMemo(
    () => (info ? Object.values(info.libraries).filter(Boolean).length : 0),
    [info],
  )

  return (
    <div className="min-h-screen overflow-x-hidden">
      <header className="sticky top-0 z-20 border-b border-border bg-bg/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3">
          <div className="flex items-center gap-2.5">
            <div className="grid h-8 w-8 place-items-center rounded-md border border-primary/30 bg-primary/10 text-primary">
              <Layers className="h-4 w-4" strokeWidth={1.75} />
            </div>
            <div className="leading-tight">
              <h1 className="text-sm font-semibold tracking-tight text-ink">Descale</h1>
              <p className="font-mono text-[11px] text-ink-faint">image-scaling attack lab</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={status} version={info?.version} />
            <a
              href="https://github.com/trailofbits/anamorpher"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs text-ink-muted transition-colors hover:bg-surface hover:text-ink"
            >
              <Github className="h-3.5 w-3.5" /> Research
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl grid-cols-1 gap-6 px-5 py-7 lg:grid-cols-[340px_1fr]">
        <aside className="flex min-w-0 flex-col gap-5 lg:sticky lg:top-[68px] lg:h-fit">
          <Dropzone file={file} previewUrl={previewUrl} onSelect={onSelect} onClear={onClear} />
          <ControlRail
            info={info}
            params={params}
            onChange={onChange}
            onGenerate={onGenerate}
            busy={busy}
            ready={ready}
          />
        </aside>

        <section className="min-w-0 space-y-6">
          {error && (
            <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-ink">
              <ImageOff className="h-4 w-4 text-destructive" /> {error}
            </div>
          )}

          {result ? (
            <Evidence result={result} busy={busy} onDownload={onDownload} onProbe={onProbe} />
          ) : (
            <div className="flex min-h-[420px] flex-col items-center justify-center rounded-md border border-dashed border-border bg-surface/40 p-10 text-center">
              <ScanLine className="h-9 w-9 text-ink-faint" strokeWidth={1.25} />
              <h2 className="mt-4 text-base font-medium text-ink">No payload yet</h2>
              <p className="mt-1 max-w-sm text-sm text-ink-faint">
                Upload a decoy image and craft a payload. You'll see the full-resolution decoy beside
                exactly what a downscaler extracts from it, with measured stealth and an OCR verdict.
              </p>
              <p className="mt-4 font-mono text-[11px] text-ink-faint">
                {libsOn} image {libsOn === 1 ? "library" : "libraries"} available
                {info && !info.ocr_available ? " · OCR off" : ""}
              </p>
            </div>
          )}

          {(transfer || transferBusy) && <TransferGrid data={transfer} busy={transferBusy} />}
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-5 pb-10 pt-2">
        <p className="flex flex-wrap items-center gap-x-2 border-t border-border pt-4 text-xs text-ink-faint">
          <a href="explainer.html" className="text-primary hover:underline">Read the deep dive →</a>
          <span aria-hidden>·</span>
          <span>
            For security research and education. Reimplements the technique from Trail of Bits'
            Anamorpher and the image-scaling attack literature (Xiao et al., Quiring et al.). Use
            only on systems you are authorized to test.
          </span>
        </p>
      </footer>
    </div>
  )
}
