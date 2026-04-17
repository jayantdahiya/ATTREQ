/**
 * Location utility functions for geolocation and localStorage management.
 */

export interface LocationData {
  lat: number
  lon: number
  city?: string
  timestamp: number
}

export interface GeolocationError {
  code: number
  message: string
}

/**
 * Get current position using browser's Geolocation API.
 * Returns a promise that resolves with coordinates or rejects with an error.
 */
export const getCurrentPosition = (): Promise<{ lat: number; lon: number }> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject({
        code: 0,
        message: 'Geolocation is not supported by this browser.',
      })
      return
    }

    // Add timeout to prevent hanging
    const timeoutId = setTimeout(() => {
      reject({
        code: 3, // TIMEOUT
        message: 'Location request timed out.',
      })
    }, 15000) // 15 second timeout

    navigator.geolocation.getCurrentPosition(
      (position) => {
        clearTimeout(timeoutId)
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        })
      },
      (error) => {
        clearTimeout(timeoutId)
        reject({
          code: error.code,
          message: error.message,
        })
      },
      {
        enableHighAccuracy: false, // Reduce accuracy requirements to avoid CoreLocation issues
        timeout: 10000,
        maximumAge: 300000, // 5 minutes
      }
    )
  })
}

/**
 * Save location data to localStorage.
 */
export const saveLocationToStorage = (location: LocationData): void => {
  try {
    localStorage.setItem('attreq_user_location', JSON.stringify(location))
  } catch (error) {
    console.error('Failed to save location to localStorage:', error)
  }
}

/**
 * Retrieve location data from localStorage.
 */
export const getLocationFromStorage = (): LocationData | null => {
  try {
    const stored = localStorage.getItem('attreq_user_location')
    if (!stored) return null

    const location = JSON.parse(stored) as LocationData
    
    // Check if location is not too old (24 hours)
    const maxAge = 24 * 60 * 60 * 1000 // 24 hours in milliseconds
    if (Date.now() - location.timestamp > maxAge) {
      clearLocationFromStorage()
      return null
    }

    return location
  } catch (error) {
    console.error('Failed to retrieve location from localStorage:', error)
    return null
  }
}

/**
 * Clear location data from localStorage.
 */
export const clearLocationFromStorage = (): void => {
  try {
    localStorage.removeItem('attreq_user_location')
  } catch (error) {
    console.error('Failed to clear location from localStorage:', error)
  }
}

/**
 * Convert city name to coordinates using a geocoding service.
 * This is a placeholder implementation - in production, you'd use a real geocoding API.
 */
export const geocodeCity = async (city: string): Promise<{ lat: number; lon: number }> => {
  // For now, return a default location (New York)
  // In production, integrate with Google Geocoding API, OpenCage, or similar
  console.warn(`Geocoding not implemented. Using default location for city: ${city}`)
  
  return {
    lat: 40.7128,
    lon: -74.0060,
  }
}

/**
 * Get location display name for UI.
 */
export const getLocationDisplayName = (location: LocationData): string => {
  if (location.city) {
    return location.city
  }
  
  // Format coordinates as a readable location
  return `${location.lat.toFixed(2)}, ${location.lon.toFixed(2)}`
}

/**
 * Check if geolocation permission is granted.
 */
export const checkGeolocationPermission = async (): Promise<PermissionState> => {
  if (!navigator.permissions) {
    return 'prompt'
  }

  try {
    const result = await navigator.permissions.query({ name: 'geolocation' as PermissionName })
    return result.state
  } catch (error) {
    console.warn('Failed to check geolocation permission:', error)
    return 'prompt'
  }
}

/**
 * Save the "user has been prompted" flag to localStorage.
 */
export const saveUserPromptedFlag = (): void => {
  try {
    localStorage.setItem('attreq_user_prompted_location', 'true')
  } catch (error) {
    console.error('Failed to save user prompted flag to localStorage:', error)
  }
}

/**
 * Check if user has been prompted for location before.
 */
export const hasUserBeenPrompted = (): boolean => {
  try {
    const prompted = localStorage.getItem('attreq_user_prompted_location')
    return prompted === 'true'
  } catch (error) {
    console.error('Failed to check user prompted flag:', error)
    return false
  }
}

/**
 * Clear the "user has been prompted" flag from localStorage.
 */
export const clearUserPromptedFlag = (): void => {
  try {
    localStorage.removeItem('attreq_user_prompted_location')
  } catch (error) {
    console.error('Failed to clear user prompted flag from localStorage:', error)
  }
}
