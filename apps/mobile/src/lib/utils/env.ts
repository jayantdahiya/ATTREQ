// The ATTREQ dev backend runs on host port 8001 (8000 is a different service).
// Two ways to reach it from the app:
// - Public tunnel (works anywhere, no adb needed): a permanent named Cloudflare
//   tunnel (`attreq-backend`, see ~/.cloudflared/config.yml) forwards
//   dev-server-1.online -> localhost:8001, running as a launchd service so it
//   survives restarts. The URL below is stable — no need to update it.
// - Local dev: 'http://127.0.0.1:8001/api/v1' + `adb reverse tcp:8001 tcp:8001`
//   (works on both emulator and USB/wireless devices).
export const apiBaseUrl = 'https://dev-server-1.online/api/v1';

export const backendBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '');
