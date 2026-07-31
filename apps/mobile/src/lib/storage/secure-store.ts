import AsyncStorage from '@react-native-async-storage/async-storage';

// A1 uses AsyncStorage (maintained, New-Architecture, no Expo) for the refresh
// token. NOTE: AsyncStorage is not encrypted — acceptable for the dev build;
// upgrade to hardware-backed secure storage (e.g. react-native-keychain) before
// any production/distribution milestone.
const keys = {
  refreshToken: 'attreq.refresh-token',
  reminderEnabled: 'attreq.reminder-enabled',
};

export async function getRefreshToken() {
  return AsyncStorage.getItem(keys.refreshToken);
}

export async function saveRefreshToken(refreshToken: string) {
  return AsyncStorage.setItem(keys.refreshToken, refreshToken);
}

export async function clearRefreshToken() {
  return AsyncStorage.removeItem(keys.refreshToken);
}

export async function getReminderEnabled() {
  const stored = await AsyncStorage.getItem(keys.reminderEnabled);
  return stored === 'true';
}

export async function saveReminderEnabled(enabled: boolean) {
  return AsyncStorage.setItem(keys.reminderEnabled, String(enabled));
}
