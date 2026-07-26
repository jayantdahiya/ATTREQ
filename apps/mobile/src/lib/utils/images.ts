import { backendBaseUrl } from '@/lib/utils/env';

// Backend image URLs may be relative (/uploads/...) or absolute. On the Android
// emulator the host is 10.0.2.2, so rewrite localhost/127.0.0.1 absolutes too.
export function resolveImageUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) {
    return url.replace(/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i, backendBaseUrl);
  }
  return `${backendBaseUrl}${url.startsWith('/') ? '' : '/'}${url}`;
}
