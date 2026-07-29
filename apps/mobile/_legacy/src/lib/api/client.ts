import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

import { apiBaseUrl } from '@/lib/utils/env'
import { readAccessToken, refreshSessionWithStore, signOutWithStore } from '@/lib/api/session'

type RetryableRequest = InternalAxiosRequestConfig & { _retry?: boolean }

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const accessToken = readAccessToken()

  if (accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequest | undefined

    if (!originalRequest || originalRequest._retry || error.response?.status !== 401) {
      return Promise.reject(error)
    }

    if (
      originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/register')
    ) {
      return Promise.reject(error)
    }

    originalRequest._retry = true
    const refreshed = await refreshSessionWithStore()

    if (!refreshed) {
      await signOutWithStore()
      return Promise.reject(error)
    }

    const nextAccessToken = readAccessToken()
    if (nextAccessToken && originalRequest.headers) {
      originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`
    }

    return apiClient(originalRequest)
  }
)
