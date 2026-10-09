import { useCallback, useState } from 'react'
import { ApiError } from '../api/client'

export function useAsync<TArgs extends unknown[], TResult>(
  fn: (...args: TArgs) => Promise<TResult>,
) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<TResult | null>(null)

  const run = useCallback(
    async (...args: TArgs): Promise<TResult | null> => {
      setLoading(true)
      setError(null)
      try {
        const result = await fn(...args)
        setData(result)
        return result
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Something went wrong'
        setError(message)
        return null
      } finally {
        setLoading(false)
      }
    },
    [fn],
  )

  const clearError = useCallback(() => setError(null), [])

  return { loading, error, data, run, setData, clearError, setError }
}
