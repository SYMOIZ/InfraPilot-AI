import { describe, expect, it } from 'vitest'
import { ApiError } from '../api/client'

describe('ApiError', () => {
  it('stores status and detail', () => {
    const err = new ApiError('Not found', 404, { detail: 'missing' })
    expect(err.message).toBe('Not found')
    expect(err.status).toBe(404)
    expect(err.name).toBe('ApiError')
    expect(err.detail).toEqual({ detail: 'missing' })
  })
})

describe('type contracts', () => {
  it('accepts architecture edge aliases used by the API', () => {
    const edge = { from: 'a', to: 'b', label: 'calls' }
    expect(edge.from).toBe('a')
    expect(edge.to).toBe('b')
  })
})
