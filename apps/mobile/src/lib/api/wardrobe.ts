import { apiClient } from '@/lib/api/client';
import type {
  WardrobeItem,
  WardrobeItemStatus,
  WardrobeItemUpdatePayload,
  WardrobeListResponse,
  WardrobeUploadResponse,
} from '@/lib/api/types';

export interface UploadAsset {
  uri: string;
  name: string;
  type: string;
}

export const wardrobeApi = {
  async list(status: WardrobeItemStatus = 'active', page = 1) {
    const response = await apiClient.get<WardrobeListResponse>('/wardrobe/items', {
      params: { page, page_size: 50, status },
    });
    return response.data;
  },
  async upload(asset: UploadAsset) {
    const formData = new FormData();
    formData.append('file', { uri: asset.uri, name: asset.name, type: asset.type } as never);
    const response = await apiClient.post<WardrobeUploadResponse>('/wardrobe/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  // POST /wardrobe/batch-upload — multipart, repeated field `files`, up to
  // `wardrobe_batch_upload_max_files` (20, RI-7). One bad image never fails the
  // rest of the batch. Returns one WardrobeUploadResponse per uploaded item.
  async batchUpload(assets: UploadAsset[]) {
    const formData = new FormData();
    assets.forEach((asset, i) => {
      formData.append('files', {
        uri: asset.uri,
        name: asset.name || `garment-${i}.jpg`,
        type: asset.type || 'image/jpeg',
      } as never);
    });
    const response = await apiClient.post<WardrobeUploadResponse[]>('/wardrobe/batch-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  async getItem(itemId: string) {
    const response = await apiClient.get<WardrobeItem>(`/wardrobe/items/${itemId}`);
    return response.data;
  },
  async updateItem(itemId: string, payload: WardrobeItemUpdatePayload) {
    const response = await apiClient.put<WardrobeItem>(`/wardrobe/items/${itemId}`, payload);
    return response.data;
  },
  async setStatus(itemId: string, status: WardrobeItemStatus) {
    const response = await apiClient.patch<WardrobeItem>(`/wardrobe/items/${itemId}/status`, { status });
    return response.data;
  },
  async deleteItem(itemId: string) {
    await apiClient.delete(`/wardrobe/items/${itemId}`);
  },
};
