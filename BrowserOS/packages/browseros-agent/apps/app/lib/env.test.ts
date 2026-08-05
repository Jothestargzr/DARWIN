import { describe, expect, it } from 'bun:test'
import { parseDARWINApiUrl } from './browseros-api-url'
import { parseAlphaFeaturesFlag } from './env'

describe('parseAlphaFeaturesFlag', () => {
  it('defaults alpha features off when unset', () => {
    expect(parseAlphaFeaturesFlag(undefined)).toBe(false)
  })

  it('keeps explicit true enabled', () => {
    expect(parseAlphaFeaturesFlag('true')).toBe(true)
  })

  it('keeps explicit false disabled', () => {
    expect(parseAlphaFeaturesFlag('false')).toBe(false)
  })
})

describe('parseDARWINApiUrl', () => {
  it('defaults to the production DARWIN API when unset', () => {
    expect(parseBrowserOSApiUrl(undefined)).toBe('https://api.browseros.com')
  })

  it('preserves explicit overrides', () => {
    expect(parseDARWINApiUrl('http://127.0.0.1:3000')).toBe(
      'http://127.0.0.1:3000',
    )
  })

  it('rejects overrides without a scheme', () => {
    expect(() => parseDARWINApiUrl('api.browseros.com')).toThrow(
      'VITE_PUBLIC_BROWSEROS_API must be a valid URL including http:// or https://',
    )
  })

  it('rejects non-HTTP overrides', () => {
    expect(() =>
      parseDARWINApiUrl('chrome-extension://extension-id'),
    ).toThrow('VITE_PUBLIC_BROWSEROS_API must use http:// or https://')
  })

  it('returns a URL that can form a valid WXT match pattern', () => {
    expect(`${parseDARWINApiUrl(undefined)}/home`).toStartWith('https://')
  })
})
