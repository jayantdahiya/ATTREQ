import { backendBaseUrl } from '@/lib/utils/env'

export function resolveApiImageUrl(path?: string | null) {
  if (!path) {
    return undefined
  }

  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }

  return `${backendBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
}
