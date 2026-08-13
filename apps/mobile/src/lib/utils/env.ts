import { releaseApiBaseUrl } from './release-env';

// Development uses adb reverse to the local Docker backend. Release builds
// use the stable Cloudflare hostname, which can move from the Mac to the Pi
// without requiring testers to reinstall the APK.
const developmentApiBaseUrl = 'http://127.0.0.1:8001/api/v1';
const isDevelopmentBuild = typeof __DEV__ !== 'undefined' && __DEV__;

export const apiBaseUrl = isDevelopmentBuild
  ? developmentApiBaseUrl
  : releaseApiBaseUrl;

export const backendBaseUrl = apiBaseUrl.replace(/\/api\/v1\/?$/, '');
