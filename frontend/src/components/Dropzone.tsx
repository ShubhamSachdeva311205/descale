import { useCallback, useRef, useState } from "react"
import { ImageDown, X } from "lucide-react"
import { cn } from "../lib/utils"

interface Props {
  file: File | null
  previewUrl: string | null
  onSelect: (file: File) => void
  onClear: () => void
}

export function Dropzone({ file, previewUrl, onSelect, onClear }: Props) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const take = useCallback(
    (f: File | undefined) => {
      if (f && f.type.startsWith("image/")) onSelect(f)
    },
    [onSelect],
  )

  if (file && previewUrl) {
    return (
      <figure className="group relative overflow-hidden rounded-md border border-border bg-bg">
        <img
          src={previewUrl}
          alt={`Decoy source: ${file.name}`}
          className="aspect-[4/3] w-full object-contain"
        />
        <figcaption className="flex items-center justify-between gap-2 border-t border-border bg-surface px-3 py-2">
          <span className="truncate font-mono text-xs text-ink-faint">{file.name}</span>
          <button
            type="button"
            onClick={onClear}
            className="inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 text-xs text-ink-muted transition-colors hover:bg-surface-2 hover:text-ink"
          >
            <X className="h-3.5 w-3.5" /> Replace
          </button>
        </figcaption>
      </figure>
    )
  }

  return (
    <button
      type="button"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        take(e.dataTransfer.files?.[0])
      }}
      className={cn(
        "flex aspect-[4/3] w-full flex-col items-center justify-center gap-3 rounded-md border border-dashed px-6 text-center transition-colors",
        dragging
          ? "border-primary bg-primary/5"
          : "border-border-strong/60 hover:border-primary/60 hover:bg-surface/60",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="sr-only"
        onChange={(e) => take(e.target.files?.[0])}
      />
      <ImageDown className="h-7 w-7 text-primary" strokeWidth={1.5} />
      <div>
        <p className="text-sm font-medium text-ink">Drop a decoy image</p>
        <p className="mt-0.5 text-xs text-ink-faint">
          or click to browse · PNG / JPG · higher resolution hides more
        </p>
      </div>
    </button>
  )
}
