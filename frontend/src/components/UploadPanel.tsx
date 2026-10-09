import { useRef, useState, type ChangeEvent, type FormEvent } from 'react'

interface UploadPanelProps {
  uploading?: boolean
  onUpload: (file: File) => void
}

export function UploadPanel({ uploading = false, onUpload }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [localError, setLocalError] = useState<string | null>(null)

  function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    setLocalError(null)
    const next = e.target.files?.[0] ?? null
    setFile(next)
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!file) {
      setLocalError('Choose a .drawio, .xml, or image file first.')
      return
    }
    onUpload(file)
  }

  return (
    <form className="panel anim-rise" onSubmit={handleSubmit}>
      <p>
        Upload an existing draw.io / XML diagram to extract services, or attach a
        PNG/JPG for reference. Image-only uploads do not invent architecture.
      </p>
      <div className="field">
        <label htmlFor="arch-upload">Architecture file</label>
        <input
          ref={inputRef}
          id="arch-upload"
          type="file"
          accept=".drawio,.xml,.png,.jpg,.jpeg"
          onChange={onFileChange}
        />
        {file ? (
          <p className="hint">
            Selected: {file.name} ({Math.round(file.size / 1024)} KB)
          </p>
        ) : null}
        {localError ? (
          <p className="hint" role="alert" style={{ color: 'var(--fail)' }}>
            {localError}
          </p>
        ) : null}
      </div>
      <div className="actions-row">
        <button type="submit" className="btn" disabled={uploading || !file}>
          {uploading ? 'Uploading…' : 'Upload'}
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => {
            setFile(null)
            setLocalError(null)
            if (inputRef.current) inputRef.current.value = ''
          }}
        >
          Clear
        </button>
      </div>
    </form>
  )
}
