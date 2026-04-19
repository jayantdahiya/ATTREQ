const fallbackApiUrl = 'http://127.0.0.1:8000/api/v1'

export const apiBaseUrl = process.env.EXPO_PUBLIC_API_URL ?? fallbackApiUrl
export const backendBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '')
