import type { CSSProperties, DragEvent } from 'react'
import { servicesByCategory, type CatalogService } from '../../catalog/services'

export const PALETTE_MIME = 'application/infrapilot-service'

interface ServicePaletteProps {
  onAddService: (service: CatalogService) => void
}

export function ServicePalette({ onAddService }: ServicePaletteProps) {
  const groups = servicesByCategory()

  function onDragStart(e: DragEvent, service: CatalogService) {
    e.dataTransfer.setData(PALETTE_MIME, service.id)
    e.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <aside className="studio-palette" aria-label="AWS service palette">
      <div className="studio-palette-head">
        <h2>Services</h2>
        <p>Drag onto canvas or click to add</p>
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
                  className="palette-chip"
                  style={{ '--chip-color': service.color } as CSSProperties}
                  draggable
                  onDragStart={(e) => onDragStart(e, service)}
                  onClick={() => onAddService(service)}
                  title={service.name}
                >
                  {service.shortLabel}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}
