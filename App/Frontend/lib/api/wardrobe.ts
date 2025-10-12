import apiClient from './client'

export interface WardrobeItem {
  id: string
  user_id: string
  original_image_url: string
  processed_image_url: string | null
  thumbnail_url: string | null
  category: string | null
  color_primary: string | null
  color_secondary: string | null
  pattern: string | null
  season: string[]
  occasion: string[]
  brand: string | null
  detection_confidence: number | null
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  uploaded_at: string
  last_worn: string | null
  wear_count: number
}

export interface UploadResponse {
  id: string
  message: string
  processing_status: string
}

export const wardrobeApi = {
  uploadItem: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post('/wardrobe/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getItems: async (params?: {
    category?: string
    season?: string
    occasion?: string
    skip?: number
    limit?: number
  }): Promise<{ items: WardrobeItem[]; total: number }> => {
    const response = await apiClient.get('/wardrobe/items', { params })
    return response.data
  },

  getItem: async (id: string): Promise<WardrobeItem> => {
    const response = await apiClient.get(`/wardrobe/items/${id}`)
    return response.data
  },

  updateItem: async (id: string, data: Partial<WardrobeItem>): Promise<WardrobeItem> => {
    const response = await apiClient.put(`/wardrobe/items/${id}`, data)
    return response.data
  },

  deleteItem: async (id: string): Promise<void> => {
    await apiClient.delete(`/wardrobe/items/${id}`)
  },
}
