/// <reference types="vite/client" />

declare module '*.svg' {
  const src: string
  export default src
}

declare module 'gif.js' {
  interface GIFOptions {
    workers?: number
    quality?: number
    width?: number
    height?: number
    workerScript?: string
  }
  export default class GIF {
    constructor(options?: GIFOptions)
    addFrame(
      element: CanvasImageSource | CanvasRenderingContext2D,
      options?: { delay?: number; copy?: boolean },
    ): void
    on(event: 'finished', cb: (blob: Blob) => void): void
    on(event: 'abort', cb: () => void): void
    render(): void
  }
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_DEMO_MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
