import { useMemo, useState, type CSSProperties, type DragEvent, type FormEvent } from 'react'
import {
  addCustomService,
  emojiToDataUrl,
  fileToDataUrl,
  loadCustomServices,
  removeCustomService,
} from '../../catalog/customServices'
import { servicesByCategory, type CatalogService } from '../../catalog/services'

export const PALETTE_MIME = 'application/infrapilot-service'

interface ServicePaletteProps {
  onAddService: (service: CatalogService) => void
}

export function ServicePalette({ onAddService }: ServicePaletteProps) {
  const [tick, setTick] = useState(0)
  const groups = useMemo(() => {
    void tick
    return servicesByCategory()
  }, [tick])

  const [name, setName] = useState('')
  const [emoji, setEmoji] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function onDragStart(e: DragEvent, service: CatalogService) {
    e.dataTransfer.setData(PALETTE_MIME, service.id)
    e.dataTransfer.effectAllowed = 'copy'
  }

  async function onSubmitCustom(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const trimmed = name.trim()
    if (!trimmed) {
      setError('Enter a tool name')
      return
    }
    if (!file && !emoji.trim()) {
      setError('Upload an icon (PNG/SVG/GIF/WebP) or enter an emoji')
      return
    }
    setBusy(true)
    try {
      let iconUrl = ''
      if (file) {
        iconUrl = await fileToDataUrl(file)
      } else {
        iconUrl = emojiToDataUrl(emoji.trim().slice(0, 8))
      }
      if (!iconUrl) throw new Error('Could not create icon')
      const service = addCustomService({
        name: trimmed,
        iconUrl,
        emoji: emoji.trim() || undefined,
      })
      setName('')
      setEmoji('')
      setFile(null)
      setTick((t) => t + 1)
      onAddService(service)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <aside className="studio-palette" aria-label="AWS service palette">
      <div className="studio-palette-head">
        <h2>Services</h2>
        <p>Official AWS icons — drag or click</p>
      </div>
      <div className="studio-palette-scroll">
        {groups.map((group) => (
          <div key={group.category} className="palette-group">
            <h3>{group.label}</h3>
            <div className="palette-chips">
              {group.services.map((service) => (
                <button
                  key={service.id}
                  type="button"
                  className="palette-chip palette-chip-icon"
                  style={{ '--chip-color': service.color } as CSSProperties}
                  draggable
                  onDragStart={(e) => onDragStart(e, service)}
                  onClick={() => onAddService(service)}
                  title={service.name}
                >
                  {service.iconUrl ? (
                    <img src={service.iconUrl} alt="" className="palette-chip-img" draggable={false} />
                  ) : null}
                  <span>{service.shortLabel}</span>
                  {service.custom ? (
                    <span
                      className="palette-chip-remove"
                      role="button"
                      tabIndex={0}
                      title="Remove custom tool"
                      onClick={(ev) => {
                        ev.stopPropagation()
                        removeCustomService(service.id)
                        setTick((t) => t + 1)
                      }}
                      onKeyDown={(ev) => {
                        if (ev.key === 'Enter' || ev.key === ' ') {
                          ev.preventDefault()
                          ev.stopPropagation()
                          removeCustomService(service.id)
                          setTick((t) => t + 1)
                        }
                      }}
                    >
                      ×
                    </span>
                  ) : null}
                </button>
              ))}
            </div>
          </div>
        ))}

        <div className="palette-group palette-custom-form">
          <h3>Add missing tool</h3>
          <p className="palette-custom-hint">
            Upload an official-style icon or emoji, give it a name, then use it on the canvas.
          </p>
          <form onSubmit={(e) => void onSubmitCustom(e)} className="custom-tool-form">
            <label>
              Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Amazon MQ"
                maxLength={48}
              />
            </label>
            <label>
              Emoji (optional)
              <input
                value={emoji}
                onChange={(e) => setEmoji(e.target.value)}
                placeholder="🚀"
                maxLength={8}
              />
            </label>
            <label>
              Icon file
              <input
                type="file"
                accept="image/png,image/svg+xml,image/gif,image/webp,image/jpeg"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            {error ? <p className="studio-agent-error">{error}</p> : null}
            <button type="submit" className="btn btn-sm" disabled={busy}>
              {busy ? 'Adding…' : 'Add to palette'}
            </button>
          </form>
          {loadCustomServices().length === 0 ? null : (
            <p className="palette-custom-hint">Custom tools stay in this browser.</p>
          )}
        </div>
      </div>
    </aside>
  )
}
