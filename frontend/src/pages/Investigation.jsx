import { useRef, useState } from 'react'
import AppLayout from '../components/layout/AppLayout'
import ScanlineLoader from '../components/ScanlineLoader'
import VerdictBadge from '../components/VerdictBadge'
import HashTag from '../components/HashTag'
import { analyzeImage, ApiError } from '../api/client'
import { formatConfidence, formatProcessingTime } from '../utils/format'

export default function Investigation() {
  const fileInputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [caption, setCaption] = useState('')
  const [status, setStatus] = useState('idle') // idle | analyzing | done | error
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

  function handleFileSelect(selectedFile) {
    if (!selectedFile) return
    setFile(selectedFile)
    setPreviewUrl(URL.createObjectURL(selectedFile))
    setResult(null)
    setStatus('idle')
    setErrorMessage(null)
  }

  function handleDrop(event) {
    event.preventDefault()
    const droppedFile = event.dataTransfer.files?.[0]
    handleFileSelect(droppedFile)
  }

  async function handleAnalyze() {
    if (!file) return
    setStatus('analyzing')
    setErrorMessage(null)
    try {
      const analysis = await analyzeImage(file, caption || undefined)
      setResult(analysis)
      setStatus('done')
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Something went wrong during analysis.'
      setErrorMessage(message)
      setStatus('error')
    }
  }

  return (
    <AppLayout title="Investigation">
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: upload + image */}
        <div className="space-y-4">
          <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
            className="flex aspect-square cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-hairline bg-panel p-4 text-center transition-colors hover:border-cyan/50"
          >
            {status === 'analyzing' ? (
              <ScanlineLoader />
            ) : previewUrl ? (
              <img
                src={previewUrl}
                alt="Evidence preview"
                className="max-h-full max-w-full rounded-md object-contain"
              />
            ) : (
              <div className="space-y-2">
                <div className="font-mono text-3xl text-muted">⌕</div>
                <div className="font-sans text-sm text-muted">
                  Drop an image here, or click to browse
                </div>
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files?.[0])}
            />
          </div>

          <div>
            <label htmlFor="caption" className="mb-1.5 block font-sans text-sm text-muted">
              Expected caption/label <span className="text-muted/60">(optional — improves attribution accuracy)</span>
            </label>
            <input
              id="caption"
              type="text"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="e.g. a dog playing in a park"
              className="w-full rounded-md border border-hairline bg-panel px-3 py-2 font-sans text-sm text-ink placeholder:text-muted/60"
            />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!file || status === 'analyzing'}
            className="w-full rounded-md bg-cyan py-2.5 font-sans text-sm font-semibold text-void transition-opacity hover:opacity-90 disabled:opacity-40"
          >
            {status === 'analyzing' ? 'Analyzing…' : 'Analyze Image'}
          </button>

          {status === 'error' && (
            <div className="rounded-md border border-verdict-adversarial/30 bg-verdict-adversarial/10 p-3 font-sans text-sm text-verdict-adversarial">
              {errorMessage}
            </div>
          )}
        </div>

        {/* Right: results */}
        <div className="space-y-4">
          {status === 'done' && result ? (
            <>
              <VerdictBadge verdict={result.verdict} confidence={result.confidence} />

              {result.attack_type && (
                <div className="rounded-lg border border-hairline bg-panel p-4">
                  <div className="font-mono text-xs uppercase tracking-wide text-muted">
                    Attack Type
                  </div>
                  <div className="mt-1 font-mono text-lg text-verdict-warning">
                    {result.attack_type.toUpperCase()}
                    <span className="ml-2 font-sans text-sm text-muted">
                      ({formatConfidence(result.attack_type_confidence)})
                    </span>
                  </div>
                </div>
              )}

              {result.attribution_heatmap_png_base64 && (
                <div className="rounded-lg border border-hairline bg-panel p-4">
                  <div className="mb-2 font-mono text-xs uppercase tracking-wide text-muted">
                    Attribution Heatmap ({result.attribution_method})
                  </div>
                  <img
                    src={`data:image/png;base64,${result.attribution_heatmap_png_base64}`}
                    alt="Forensic attribution heatmap"
                    className="w-full rounded-md"
                  />
                </div>
              )}

              <div className="rounded-lg border border-hairline bg-panel p-4">
                <div className="mb-2 font-mono text-xs uppercase tracking-wide text-muted">
                  Explainability Panel
                </div>
                <p className="font-sans text-sm text-ink">{result.explanation_summary}</p>
                {result.explanation_details?.length > 0 && (
                  <ul className="mt-2 space-y-1.5">
                    {result.explanation_details.map((detail, i) => (
                      <li key={i} className="flex gap-2 font-sans text-xs text-muted">
                        <span className="text-cyan">–</span>
                        {detail}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="flex items-center justify-between rounded-lg border border-hairline bg-panel p-4">
                <div>
                  <div className="font-mono text-xs uppercase tracking-wide text-muted">
                    Processing Time
                  </div>
                  <div className="font-mono text-sm text-ink">
                    {formatProcessingTime(result.processing_time_ms)}
                  </div>
                </div>
                <HashTag hash={result.sha256_hash} />
              </div>
            </>
          ) : (
            <div className="flex h-full min-h-[300px] items-center justify-center rounded-lg border border-hairline bg-panel p-6 text-center">
              <p className="font-sans text-sm text-muted">
                Upload an image and click Analyze to see the detection verdict, attribution
                heatmap, and explanation here.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
