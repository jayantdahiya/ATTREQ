import { apiClient } from '@/lib/api/client';
import type { UploadAsset } from '@/lib/api/wardrobe';
import type {
  StyleDnaCorrection,
  StyleDnaProfileResponse,
  StyleDnaUploadResponse,
} from '@/lib/api/types';

// Style DNA API — router mounted at /users, so paths are `/users/style-dna/*`.
// Backend contract: apps/api/src/attreq_api/api/v1/endpoints/style_dna.py.
// Mirrors iOS StyleDnaRepository.swift.

function appendFiles(formData: FormData, assets: UploadAsset[], fallback: string) {
  assets.forEach((a, i) => {
    // Repeated multipart field name `files` (FastAPI `list[UploadFile] = File(...)`).
    formData.append('files', {
      uri: a.uri,
      name: a.name || `${fallback}-${i}.jpg`,
      type: a.type || 'image/jpeg',
    } as never);
  });
}

export const styleDnaApi = {
  /** POST /users/style-dna/upload — multipart `files`, 3–8 outfit photos. 201. */
  async uploadStylePhotos(assets: UploadAsset[]) {
    const formData = new FormData();
    appendFiles(formData, assets, 'photo');
    const response = await apiClient.post<StyleDnaUploadResponse>('/users/style-dna/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /** GET /users/style-dna — profile (null until first upload) + seed photos. */
  async getStyleDna() {
    const response = await apiClient.get<StyleDnaProfileResponse>('/users/style-dna');
    return response.data;
  },

  /** PATCH /users/style-dna — { corrections } deep-merged server-side (snake_case keys). */
  async updateStyleDna(correction: StyleDnaCorrection) {
    const response = await apiClient.patch<StyleDnaProfileResponse>('/users/style-dna', correction);
    return response.data;
  },

  /** DELETE /users/style-dna/photos — removes ALL seed photos (no per-photo delete). 204. */
  async deleteStylePhotos() {
    await apiClient.delete('/users/style-dna/photos');
  },

  /** POST /users/style-dna/regenerate — re-synthesize from stored photos (no new uploads). */
  async regenerate() {
    const response = await apiClient.post<StyleDnaUploadResponse>('/users/style-dna/regenerate');
    return response.data;
  },

  /**
   * POST /users/style-dna/selfie — optional, opt-in personal-color estimation
   * (RI-3). Multipart field `file` (single face photo) + form field `consent`.
   * Feature-flagged OFF server-side (404) and 400s without consent; callers
   * MUST treat both — and any failure — as a soft skip, never a hard block.
   */
  async estimatePersonalColorSelfie(asset: UploadAsset, consent: boolean) {
    const formData = new FormData();
    formData.append('file', {
      uri: asset.uri,
      name: asset.name || 'selfie.jpg',
      type: asset.type || 'image/jpeg',
    } as never);
    formData.append('consent', consent ? 'true' : 'false');
    const response = await apiClient.post<StyleDnaProfileResponse>('/users/style-dna/selfie', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
