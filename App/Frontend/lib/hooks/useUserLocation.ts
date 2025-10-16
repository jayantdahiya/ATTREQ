/**
 * Custom React hook for managing user location.
 * Handles geolocation API, localStorage caching, and backend sync.
 */

import { useCallback, useEffect, useState, useRef } from 'react'
import { toast } from 'sonner'
import { updateUserLocation, LocationUpdateData } from '@/lib/api/client'
import {
  getCurrentPosition,
  getLocationFromStorage,
  saveLocationToStorage,
  clearLocationFromStorage,
  geocodeCity,
  LocationData,
  GeolocationError,
} from '@/lib/utils/location'

export interface UseUserLocationReturn {
  location: LocationData | null
  isLoading: boolean
  error: string | null
  requestLocation: () => Promise<void>
  setLocationManually: (city: string) => Promise<void>
  clearLocation: () => void
  showManualDialog: boolean
}

export const useUserLocation = (): UseUserLocationReturn => {
  const [location, setLocation] = useState<LocationData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showManualDialog, setShowManualDialog] = useState(false)
  const hasTriedGeolocation = useRef(false)

  // Sync location with backend
  const syncWithBackend = useCallback(async (locationData: LocationData) => {
    try {
      const updateData: LocationUpdateData = {
        lat: locationData.lat,
        lon: locationData.lon,
        city: locationData.city,
      }
      await updateUserLocation(updateData)
    } catch (error) {
      console.warn('Failed to sync location with backend:', error)
      // Don't show error to user as this is background sync
    }
  }, [])

  // Request location using browser geolocation
  const requestLocation = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const coords = await getCurrentPosition()
      const locationData: LocationData = {
        lat: coords.lat,
        lon: coords.lon,
        timestamp: Date.now(),
      }

      setLocation(locationData)
      saveLocationToStorage(locationData)
      
      // Sync with backend in background
      syncWithBackend(locationData)
      
      toast.success('Location updated!', {
        description: 'Your location has been saved for weather-based recommendations.',
      })
    } catch (err) {
      const error = err as GeolocationError
      let errorMessage = 'Failed to get your location'
      
      switch (error.code) {
        case 1: // PERMISSION_DENIED
          errorMessage = 'Location access denied. Please enable location permissions.'
          setShowManualDialog(true) // Show manual entry dialog
          break
        case 2: // POSITION_UNAVAILABLE
          errorMessage = 'Location information is unavailable.'
          setShowManualDialog(true) // Show manual entry dialog
          break
        case 3: // TIMEOUT
          errorMessage = 'Location request timed out.'
          setShowManualDialog(true) // Show manual entry dialog
          break
        default:
          errorMessage = error.message || 'Failed to get your location'
          setShowManualDialog(true) // Show manual entry dialog
      }
      
      setError(errorMessage)
      toast.error('Location Error', {
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }, [syncWithBackend])

  // Load location from localStorage on mount
  useEffect(() => {
    const savedLocation = getLocationFromStorage()
    if (savedLocation) {
      setLocation(savedLocation)
    } else if (!hasTriedGeolocation.current) {
      // No saved location, try to get current position automatically
      hasTriedGeolocation.current = true
      requestLocation()
    }
  }, [requestLocation])

  // Set location manually using city name
  const setLocationManually = useCallback(async (city: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const coords = await geocodeCity(city)
      const locationData: LocationData = {
        lat: coords.lat,
        lon: coords.lon,
        city: city,
        timestamp: Date.now(),
      }

      setLocation(locationData)
      saveLocationToStorage(locationData)
      setShowManualDialog(false) // Close the dialog
      
      // Sync with backend
      await syncWithBackend(locationData)
      
      toast.success('Location updated!', {
        description: `Location set to ${city} for weather-based recommendations.`,
      })
    } catch (err) {
      const errorMessage = `Failed to find location for "${city}". Please try a different city.`
      setError(errorMessage)
      toast.error('Location Error', {
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }, [syncWithBackend])

  // Clear saved location
  const clearLocation = useCallback(() => {
    setLocation(null)
    clearLocationFromStorage()
    setError(null)
    setShowManualDialog(false)
    toast.info('Location cleared', {
      description: 'You can set a new location anytime.',
    })
  }, [])

  return {
    location,
    isLoading,
    error,
    requestLocation,
    setLocationManually,
    clearLocation,
    showManualDialog,
  }
}
