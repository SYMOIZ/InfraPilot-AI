/** User-uploaded custom tools (icon + name) stored locally. */

const STORAGE_KEY = 'infrapilot.customServices.v1'

export interface CustomService {
  id: string
  name: string
  shortLabel: string
  category: 'management'
  color: string
  iconUrl: string
  custom: true
  emoji?: string
}

function slugify(name: string): string {
  const base = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 40)
  return base || 'tool'
}

export function loadCustomServices(): CustomService[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as CustomService[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveCustomServices(list: CustomService[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

export function addCustomService(input: {
  name: string
  iconUrl: string
  emoji?: string
}): CustomService {
  const list = loadCustomServices()
  const shortLabel = input.name.trim().slice(0, 24) || 'Custom'
  const id = `custom_${slugify(shortLabel)}_${crypto.randomUUID().slice(0, 6)}`
  const service: CustomService = {
    id,
    name: input.name.trim() || 'Custom tool',
    shortLabel,
    category: 'management',
    color: '#64748b',
    iconUrl: input.iconUrl,
    emoji: input.emoji,
    custom: true,
  }
  list.push(service)
  saveCustomServices(list)
  return service
}

export function removeCustomService(id: string): void {
  saveCustomServices(loadCustomServices().filter((s) => s.id !== id))
}

export function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(new Error('Could not read icon file'))
    reader.readAsDataURL(file)
  })
}

/** Render a single emoji character to a data-URL PNG for the palette/canvas. */
export function emojiToDataUrl(emoji: string, size = 128): string {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''
  ctx.clearRect(0, 0, size, size)
  ctx.font = `${Math.floor(size * 0.72)}px "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(emoji, size / 2, size / 2 + size * 0.04)
  return canvas.toDataURL('image/png')
}
