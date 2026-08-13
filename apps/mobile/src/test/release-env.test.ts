import { releaseApiBaseUrl } from '@/lib/utils/release-env';

describe('Android release environment', () => {
  it('uses the stable HTTPS beta backend path', () => {
    expect(releaseApiBaseUrl).toBe('https://dev-server-1.online/api/v1');
    expect(releaseApiBaseUrl).not.toMatch(/localhost|127\.0\.0\.1|10\.0\.2\.2/);
  });
});
