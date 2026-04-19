import { Platform } from 'react-native'

// Android emulators cannot reach the host machine via 127.0.0.1.
const fallbackApiUrl =
  Platform.OS === 'android' ? 'http://10.0.2.2:8000/api/v1' : 'http://127.0.0.1:8000/api/v1'

export const apiBaseUrl = process.env.EXPO_PUBLIC_API_URL ?? fallbackApiUrl
export const backendBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '')
