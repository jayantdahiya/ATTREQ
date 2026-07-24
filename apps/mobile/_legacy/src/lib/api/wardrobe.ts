import { apiClient } from '@/lib/api/client'
import type {
  DetectedWardrobeItem,
  WardrobeItem,
  WardrobeListResponse,
  WardrobeUploadResponse,
} from '@/lib/api/types'

export interface UploadAssetInput {
  uri: string
  name: string
  mimeType: string
}

export const wardrobeApi = {
  async listItems(page = 1) {
    const response = await apiClient.get<WardrobeListResponse>('/wardrobe/items', {
      params: { page, page_size: 50 },
    })
    return response.data
  },
  async uploadItem(asset: UploadAssetInput) {
    const formData = new FormData()
    formData.append(
      'file',
      {
        uri: asset.uri,
        name: asset.name,
        type: asset.mimeType,
      } as never
    )

    const response = await apiClient.post<WardrobeUploadResponse>('/wardrobe/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
  async getItem(itemId: string) {
    const response = await apiClient.get<WardrobeItem>(`/wardrobe/items/${itemId}`)
    return response.data
  },
  async updateItem(itemId: string, data: Partial<WardrobeItem>) {
    const response = await apiClient.put<WardrobeItem>(`/wardrobe/items/${itemId}`, data)
    return response.data
  },
  async deleteItem(itemId: string) {
    await apiClient.delete(`/wardrobe/items/${itemId}`)
  },
  async bulkAddItems(items: DetectedWardrobeItem[]): Promise<WardrobeItem[]> {
    const response = await apiClient.post<WardrobeItem[]>('/wardrobe/items/bulk', items)
    return response.data
  },
}
