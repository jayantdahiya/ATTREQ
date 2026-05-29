import { apiClient } from '@/lib/api/client'
import type {
  DetectedWardrobeItem,
  StyleDnaCorrection,
  StyleDnaProfileResponse,
  StyleDnaUploadResponse,
} from '@/lib/api/types'

export interface StylePhotoAsset {
  uri: string
  name: string
  mimeType: string
}

export const styleDnaApi = {
  async uploadStylePhotos(photos: StylePhotoAsset[]): Promise<StyleDnaUploadResponse> {
    const formData = new FormData()
    for (const photo of photos) {
      formData.append('files', {
        uri: photo.uri,
        name: photo.name,
        type: photo.mimeType,
      } as never)
    }
    const response = await apiClient.post<StyleDnaUploadResponse>(
      '/users/style-dna/upload',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return response.data
  },

  async getStyleDna(): Promise<StyleDnaProfileResponse> {
    const response = await apiClient.get<StyleDnaProfileResponse>('/users/style-dna')
    return response.data
  },

  async updateStyleDna(correction: StyleDnaCorrection): Promise<StyleDnaProfileResponse> {
    const response = await apiClient.patch<StyleDnaProfileResponse>('/users/style-dna', correction)
    return response.data
  },

  async deleteStylePhotos(): Promise<void> {
    await apiClient.delete('/users/style-dna/photos')
  },

  async regenerateStyleDna(): Promise<StyleDnaUploadResponse> {
    const response = await apiClient.post<StyleDnaUploadResponse>('/users/style-dna/regenerate')
    return response.data
  },
}
