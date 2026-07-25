import { Platform } from 'react-native';

// The ATTREQ dev backend runs on host port 8001 (8000 is a different service).
// Android emulators reach the host machine via 10.0.2.2, not 127.0.0.1.
export const apiBaseUrl =
  Platform.OS === 'android' ? 'http://10.0.2.2:8001/api/v1' : 'http://127.0.0.1:8001/api/v1';

export const backendBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '');
