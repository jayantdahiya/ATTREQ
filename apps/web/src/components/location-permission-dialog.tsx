'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { MapPin, Loader2 } from 'lucide-react'

interface LocationPermissionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onLocationSet: (city: string) => Promise<void>
  isLoading?: boolean
}

export function LocationPermissionDialog({
  open,
  onOpenChange,
  onLocationSet,
  isLoading = false,
}: LocationPermissionDialogProps) {
  const [city, setCity] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!city.trim()) return

    await onLocationSet(city.trim())
    setCity('')
    onOpenChange(false)
  }

  const handleCancel = () => {
    setCity('')
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Set Your Location
          </DialogTitle>
          <DialogDescription>
            To provide accurate weather-based outfit recommendations, please enter your city name.
            This helps us give you personalized suggestions based on your local weather conditions.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="city" className="text-right">
                City
              </Label>
              <Input
                id="city"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="e.g., New York, London, Tokyo"
                className="col-span-3"
                disabled={isLoading}
                required
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !city.trim()}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Set Location
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
