// The ATTREQ dev backend runs on host port 8001 (8000 is a different service).
// Device-agnostic: use 127.0.0.1 + `adb reverse tcp:8001 tcp:8001` so the same
// URL works on both a real device (wireless/USB) and an emulator (the emulator's
// 10.0.2.2 alias isn't valid on real hardware).
export const apiBaseUrl = 'http://127.0.0.1:8001/api/v1';

export const backendBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '');
