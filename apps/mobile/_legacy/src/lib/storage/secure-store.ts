import * as SecureStore from 'expo-secure-store'
import { Platform } from 'react-native'

const keys = {
  refreshToken: 'attreq.refresh-token',
  reminderEnabled: 'attreq.reminder-enabled',
}

export async function getRefreshToken() {
  if (Platform.OS === 'web') {
    return typeof window !== 'undefined' ? localStorage.getItem(keys.refreshToken) : null
  }
  return SecureStore.getItemAsync(keys.refreshToken)
}

export async function saveRefreshToken(refreshToken: string) {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined') localStorage.setItem(keys.refreshToken, refreshToken)
    return
  }
  return SecureStore.setItemAsync(keys.refreshToken, refreshToken)
}

export async function clearRefreshToken() {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined') localStorage.removeItem(keys.refreshToken)
    return
  }
  return SecureStore.deleteItemAsync(keys.refreshToken)
}

export async function getReminderEnabled() {
  if (Platform.OS === 'web') {
    const stored = typeof window !== 'undefined' ? localStorage.getItem(keys.reminderEnabled) : null
    return stored === 'true'
  }
  const stored = await SecureStore.getItemAsync(keys.reminderEnabled)
  return stored === 'true'
}

export async function saveReminderEnabled(enabled: boolean) {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined') localStorage.setItem(keys.reminderEnabled, String(enabled))
    return
  }
  return SecureStore.setItemAsync(keys.reminderEnabled, String(enabled))
}
