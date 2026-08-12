import { apiClient } from '@/lib/api/client';
import { styleDnaApi } from '@/lib/api/style-dna';

const STYLE_DNA_BUILD_TIMEOUT_MS = 180_000;

describe('Style DNA API build timeout', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('gives photo uploads enough time for extraction and synthesis', async () => {
    const post = jest.spyOn(apiClient, 'post').mockResolvedValue({ data: { ok: true } } as never);

    await styleDnaApi.uploadStylePhotos([
      { uri: 'file:///photo.jpg', name: 'photo.jpg', type: 'image/jpeg' },
    ]);

    expect(post).toHaveBeenCalledWith(
      '/users/style-dna/upload',
      expect.any(FormData),
      expect.objectContaining({ timeout: STYLE_DNA_BUILD_TIMEOUT_MS }),
    );
  });

  it('gives regeneration enough time for synthesis', async () => {
    const post = jest.spyOn(apiClient, 'post').mockResolvedValue({ data: { ok: true } } as never);

    await styleDnaApi.regenerate();

    expect(post).toHaveBeenCalledWith('/users/style-dna/regenerate', undefined, {
      timeout: STYLE_DNA_BUILD_TIMEOUT_MS,
    });
  });
});
