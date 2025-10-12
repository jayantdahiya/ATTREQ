'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import { recommendationsApi, OutfitSuggestion, WeatherData } from '@/lib/api/recommendations'
import { useAuthStore } from '@/store/auth'
import { getFullImageUrl } from '@/lib/utils'
import { Heart, RefreshCw, MapPin, Thermometer, Wind, Droplets } from 'lucide-react'


export default function DashboardPage() {
  const { user } = useAuthStore()
  const [suggestions, setSuggestions] = useState<OutfitSuggestion[]>([])
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    fetchSuggestions()
  }, [])

  const fetchSuggestions = async () => {
    setIsLoading(true)
    try {
      // For demo purposes, using default coordinates (New York)
      // In production, this would use the user's location
      const response = await recommendationsApi.getDailySuggestions({
        lat: 40.7128,
        lon: -74.0060,
        occasion: 'casual',
      })
      
      console.log('API Response:', response)
      console.log('Suggestions:', response.suggestions)
      if (response.suggestions.length > 0) {
        console.log('First suggestion:', response.suggestions[0])
        console.log('Top item:', response.suggestions[0].top_item)
        console.log('Bottom item:', response.suggestions[0].bottom_item)
        console.log('Accessory item:', response.suggestions[0].accessory_item)
      }
      setSuggestions(response.suggestions)
      setWeather(response.weather)
    } catch (error: any) {
      toast.error('Failed to load suggestions', {
        description: error.response?.data?.detail || 'Unable to fetch outfit recommendations',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleWearThis = async (suggestion: OutfitSuggestion) => {
    try {
      // TODO: Implement wear tracking API call
      toast.success('Outfit recorded!', {
        description: 'Thanks for wearing this outfit today.',
      })
    } catch (error) {
      toast.error('Failed to record outfit')
    }
  }

  const handleFeedback = (suggestion: OutfitSuggestion, liked: boolean) => {
    try {
      // TODO: Implement feedback API call
      toast.success(liked ? 'Thanks for the feedback!' : 'Noted, we\'ll improve!')
    } catch (error) {
      toast.error('Failed to submit feedback')
    }
  }

  const nextSuggestion = () => {
    setCurrentIndex((prev) => (prev + 1) % suggestions.length)
  }

  const prevSuggestion = () => {
    setCurrentIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length)
  }

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Skeleton className="h-8 w-64 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Skeleton className="h-96 w-full rounded-lg" />
          </div>
          <div className="space-y-4">
            <Skeleton className="h-32 w-full rounded-lg" />
            <Skeleton className="h-32 w-full rounded-lg" />
          </div>
        </div>
      </div>
    )
  }

  const currentSuggestion = suggestions[currentIndex]

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Good morning, {user?.full_name || user?.email?.split('@')[0]}!
        </h1>
        <p className="text-gray-600">
          Here are your personalized outfit recommendations for today.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Outfit Display */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Today's Outfit</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    {currentIndex + 1} of {suggestions.length}
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchSuggestions}
                    disabled={isLoading}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {currentSuggestion ? (
                <div className="space-y-6">
                  {/* Outfit Items */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Top */}
                    <div className="text-center">
                      <div className="aspect-square bg-gray-100 rounded-lg mb-2 flex items-center justify-center overflow-hidden">
                        {currentSuggestion.top_item && currentSuggestion.top_item.image_url ? (
                          (() => {
                            const fullUrl = getFullImageUrl(currentSuggestion.top_item.image_url)
                            console.log('Top item - Original:', currentSuggestion.top_item.image_url, 'Full:', fullUrl)
                            return (
                              <Image
                                src={fullUrl!}
                                alt={currentSuggestion.top_item.category || 'Top'}
                                width={200}
                                height={200}
                                className="object-cover w-full h-full"
                                onError={(e) => {
                                  console.error('Failed to load top item image:', fullUrl)
                                  console.error('Original URL:', currentSuggestion.top_item.image_url)
                                  e.currentTarget.style.display = 'none'
                                }}
                              />
                            )
                          })()
                        ) : (
                          <div className="text-gray-400 text-sm">No Image</div>
                        )}
                      </div>
                      <p className="text-sm font-medium">{currentSuggestion.top_item.category}</p>
                      <p className="text-xs text-gray-500">{currentSuggestion.top_item.color_primary}</p>
                    </div>
                    
                    {/* Bottom */}
                    <div className="text-center">
                      <div className="aspect-square bg-gray-100 rounded-lg mb-2 flex items-center justify-center overflow-hidden">
                        {currentSuggestion.bottom_item && currentSuggestion.bottom_item.image_url ? (
                          (() => {
                            const fullUrl = getFullImageUrl(currentSuggestion.bottom_item.image_url)
                            console.log('Bottom item - Original:', currentSuggestion.bottom_item.image_url, 'Full:', fullUrl)
                            return (
                              <Image
                                src={fullUrl!}
                                alt={currentSuggestion.bottom_item.category || 'Bottom'}
                                width={200}
                                height={200}
                                className="object-cover w-full h-full"
                                onError={(e) => {
                                  console.error('Failed to load bottom item image:', fullUrl)
                                  console.error('Original URL:', currentSuggestion.bottom_item.image_url)
                                  e.currentTarget.style.display = 'none'
                                }}
                              />
                            )
                          })()
                        ) : (
                          <div className="text-gray-400 text-sm">No Image</div>
                        )}
                      </div>
                      <p className="text-sm font-medium">{currentSuggestion.bottom_item.category}</p>
                      <p className="text-xs text-gray-500">{currentSuggestion.bottom_item.color_primary}</p>
                    </div>
                    
                    {/* Accessory */}
                    <div className="text-center">
                      <div className="aspect-square bg-gray-100 rounded-lg mb-2 flex items-center justify-center overflow-hidden">
                        {currentSuggestion.accessory_item && currentSuggestion.accessory_item.image_url ? (
                          (() => {
                            const fullUrl = getFullImageUrl(currentSuggestion.accessory_item.image_url)
                            console.log('Accessory item - Original:', currentSuggestion.accessory_item.image_url, 'Full:', fullUrl)
                            return (
                              <Image
                                src={fullUrl!}
                                alt={currentSuggestion.accessory_item.category || 'Accessory'}
                                width={200}
                                height={200}
                                className="object-cover w-full h-full"
                                onError={(e) => {
                                  console.error('Failed to load accessory item image:', fullUrl)
                                  console.error('Original URL:', currentSuggestion.accessory_item?.image_url)
                                  e.currentTarget.style.display = 'none'
                                }}
                              />
                            )
                          })()
                        ) : (
                          <div className="text-gray-400 text-sm">No Accessory</div>
                        )}
                      </div>
                      <p className="text-sm font-medium">
                        {currentSuggestion.accessory_item?.category || 'None'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {currentSuggestion.accessory_item?.color_primary || ''}
                      </p>
                    </div>
                  </div>

                  {/* Scores */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Color Harmony</p>
                      <p className="text-lg font-semibold">{currentSuggestion.scores.color_harmony.toFixed(1)}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Formality</p>
                      <p className="text-lg font-semibold">{currentSuggestion.scores.formality.toFixed(1)}</p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleWearThis(currentSuggestion)}
                      className="flex-1"
                    >
                      Wear This
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleFeedback(currentSuggestion, true)}
                    >
                      <Heart className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleFeedback(currentSuggestion, false)}
                    >
                      👎
                    </Button>
                  </div>

                  {/* Navigation */}
                  {suggestions.length > 1 && (
                    <div className="flex justify-between">
                      <Button variant="outline" onClick={prevSuggestion}>
                        Previous
                      </Button>
                      <Button variant="outline" onClick={nextSuggestion}>
                        Next
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-500">No outfit suggestions available</p>
                  <Button onClick={fetchSuggestions} className="mt-4">
                    Try Again
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Weather & Context */}
        <div className="space-y-4">
          {/* Weather Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Weather
              </CardTitle>
            </CardHeader>
            <CardContent>
              {weather ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold">{weather.temp}°F</span>
                    <span className="text-sm text-gray-600">{weather.condition}</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Thermometer className="h-4 w-4" />
                      <span>Feels like {weather.feels_like}°F</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Wind className="h-4 w-4" />
                      <span>{weather.wind_speed} mph</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Droplets className="h-4 w-4" />
                      <span>{weather.humidity}% humidity</span>
                    </div>
                  </div>
                </div>
              ) : (
                <Skeleton className="h-24 w-full" />
              )}
            </CardContent>
          </Card>

          {/* Occasion Card */}
          <Card>
            <CardHeader>
              <CardTitle>Occasion</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="secondary" className="text-sm">
                {currentSuggestion?.occasion_context || 'Casual'}
              </Badge>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
