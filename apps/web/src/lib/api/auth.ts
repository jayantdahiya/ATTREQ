import apiClient from './client'

export interface RegisterData {
  email: string
  password: string
  full_name?: string
  location?: string
}

export interface LoginData {
  username: string // email
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface User {
  id: string
  email: string
  full_name: string | null
  location: string | null
  is_active: boolean
  created_at: string
}

export const authApi = {
  register: async (data: RegisterData): Promise<User> => {
    const response = await apiClient.post('/auth/register', data)
    return response.data
  },

  login: async (data: LoginData): Promise<AuthResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)

    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    console.log('Making getCurrentUser request...')
    const response = await apiClient.get('/users/me')
    console.log('getCurrentUser response:', response.data)
    return response.data
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.put('/users/me', data)
    return response.data
  },
}
