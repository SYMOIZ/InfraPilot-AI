import { toPng } from 'html-to-image'
import GIF from 'gif.js'

/**
 * Capture the React Flow viewport as an animated GIF (data-travel frames).
 * Returns a Blob suitable for download.
 */
export async function exportCanvasGif(
  viewportEl: HTMLElement,
  opts?: { frames?: number; delayMs?: number; width?: number },
): Promise<Blob> {
  const frames = opts?.frames ?? 12
  const delayMs = opts?.delayMs ?? 120

  const rect = viewportEl.getBoundingClientRect()
  const width = Math.min(Math.round(opts?.width ?? rect.width), 1280)
  const height = Math.round((rect.height / rect.width) * width)

  const gif = new GIF({
    workers: 2,
    quality: 10,
    width,
    height,
    workerScript: `${import.meta.env.BASE_URL}gif.worker.js`,
  })

  for (let i = 0; i < frames; i++) {
    // Allow CSS/SVG animations to advance between captures
    await new Promise((r) => setTimeout(r, delayMs))
    const dataUrl = await toPng(viewportEl, {
      cacheBust: true,
      pixelRatio: 1,
      width: rect.width,
      height: rect.height,
      style: {
        width: `${rect.width}px`,
        height: `${rect.height}px`,
      },
    })
    const img = await loadImage(dataUrl)
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Canvas unavailable')
    ctx.fillStyle = '#f3f6f8'
    ctx.fillRect(0, 0, width, height)
    ctx.drawImage(img, 0, 0, width, height)
    gif.addFrame(canvas, { delay: delayMs, copy: true })
  }

  return new Promise((resolve, reject) => {
    gif.on('finished', (blob: Blob) => resolve(blob))
    gif.on('abort', () => reject(new Error('GIF export aborted')))
    gif.render()
  })
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Failed to load frame'))
    img.src = src
  })
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
