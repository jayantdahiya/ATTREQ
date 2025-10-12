'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { toast } from 'sonner'
import { wardrobeApi, WardrobeItem } from '@/lib/api/wardrobe'
import { useWardrobeStore } from '@/store/wardrobe'
import { getFullImageUrl } from '@/lib/utils'
import { Upload, MoreVertical, Trash2, Edit, Eye } from 'lucide-react'

export default function WardrobePage() {
  const { items, setItems, removeItem, selectedCategory, selectedSeason, selectedOccasion, setFilter } = useWardrobeStore()
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedItem, setSelectedItem] = useState<WardrobeItem | null>(null)

  useEffect(() => {
    fetchItems()
  }, [])

  const fetchItems = async () => {
    setIsLoading(true)
    try {
      const response = await wardrobeApi.getItems({
        category: selectedCategory || undefined,
        season: selectedSeason || undefined,
        occasion: selectedOccasion || undefined,
      })
      setItems(response.items)
    } catch (error: any) {
      toast.error('Failed to load wardrobe', {
        description: error.response?.data?.detail || 'Unable to fetch wardrobe items',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    try {
      const response = await wardrobeApi.uploadItem(file)
      toast.success('Item uploaded successfully!', {
        description: 'Your clothing item is being processed.',
      })
      
      // Refresh the list
      await fetchItems()
    } catch (error: any) {
      toast.error('Upload failed', {
        description: error.response?.data?.detail || 'Failed to upload item',
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handleDeleteItem = async (item: WardrobeItem) => {
    try {
      await wardrobeApi.deleteItem(item.id)
      removeItem(item.id)
      toast.success('Item deleted successfully')
    } catch (error: any) {
      toast.error('Failed to delete item', {
        description: error.response?.data?.detail || 'Unable to delete item',
      })
    }
  }

  const categories = ['Tops', 'Bottoms', 'Dresses', 'Outerwear', 'Shoes', 'Accessories']
  const seasons = ['Spring', 'Summer', 'Fall', 'Winter']
  const occasions = ['Casual', 'Work', 'Formal', 'Party', 'Athletic']

  const filteredItems = items.filter(item => {
    if (selectedCategory && item.category !== selectedCategory) return false
    if (selectedSeason && (!item.season || !item.season.includes(selectedSeason))) return false
    if (selectedOccasion && (!item.occasion || !item.occasion.includes(selectedOccasion))) return false
    return true
  })

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">My Wardrobe</h1>
        <p className="text-gray-600">
          Manage your clothing items and organize your wardrobe.
        </p>
      </div>

      {/* Upload Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Add New Item</CardTitle>
          <CardDescription>Upload a photo of your clothing item</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <input
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button asChild disabled={isUploading}>
                <span>
                  <Upload className="h-4 w-4 mr-2" />
                  {isUploading ? 'Uploading...' : 'Choose File'}
                </span>
              </Button>
            </label>
            <span className="text-sm text-gray-500">
              {isUploading ? 'Processing your item...' : 'JPG, PNG up to 10MB'}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Category: {selectedCategory || 'All'}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setFilter({ category: undefined })}>
              All Categories
            </DropdownMenuItem>
            {categories.map(category => (
              <DropdownMenuItem
                key={category}
                onClick={() => setFilter({ category })}
              >
                {category}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Season: {selectedSeason || 'All'}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setFilter({ season: undefined })}>
              All Seasons
            </DropdownMenuItem>
            {seasons.map(season => (
              <DropdownMenuItem
                key={season}
                onClick={() => setFilter({ season })}
              >
                {season}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              Occasion: {selectedOccasion || 'All'}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setFilter({ occasion: undefined })}>
              All Occasions
            </DropdownMenuItem>
            {occasions.map(occasion => (
              <DropdownMenuItem
                key={occasion}
                onClick={() => setFilter({ occasion })}
              >
                {occasion}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="outline"
          onClick={() => {
            setFilter({ category: undefined, season: undefined, occasion: undefined })
            fetchItems()
          }}
        >
          Clear Filters
        </Button>
      </div>

      {/* Wardrobe Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="aspect-square rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredItems.map((item) => (
            <Card key={item.id} className="overflow-hidden">
              <div className="aspect-square bg-gray-100 flex items-center justify-center">
                {item.thumbnail_url ? (
                  <Image
                    src={getFullImageUrl(item.thumbnail_url)!}
                    alt={item.category || 'Wardrobe item'}
                    width={200}
                    height={200}
                    className="object-cover w-full h-full"
                  />
                ) : (
                  <span className="text-gray-500">No Image</span>
                )}
              </div>
              <CardContent className="p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {item.category || 'Unknown'}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {item.color_primary || 'No color'}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {item.season && item.season.slice(0, 2).map(season => (
                        <Badge key={season} variant="secondary" className="text-xs">
                          {season}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => setSelectedItem(item)}>
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleDeleteItem(item)}
                        className="text-red-600"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {filteredItems.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No items found</p>
          <Button onClick={fetchItems}>Refresh</Button>
        </div>
      )}

      {/* Item Detail Dialog */}
      <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Item Details</DialogTitle>
            <DialogDescription>
              Detailed information about this wardrobe item
            </DialogDescription>
          </DialogHeader>
          {selectedItem && (
            <div className="space-y-4">
              <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center">
                {selectedItem.processed_image_url ? (
                  <Image
                    src={getFullImageUrl(selectedItem.processed_image_url)!}
                    alt={selectedItem.category || 'Wardrobe item'}
                    width={400}
                    height={400}
                    className="object-cover w-full h-full rounded-lg"
                  />
                ) : (
                  <span className="text-gray-500">No Image</span>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Category</p>
                  <p className="text-sm text-gray-600">{selectedItem.category || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Primary Color</p>
                  <p className="text-sm text-gray-600">{selectedItem.color_primary || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Secondary Color</p>
                  <p className="text-sm text-gray-600">{selectedItem.color_secondary || 'None'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Pattern</p>
                  <p className="text-sm text-gray-600">{selectedItem.pattern || 'None'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Seasons</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedItem.season && selectedItem.season.map(season => (
                      <Badge key={season} variant="secondary" className="text-xs">
                        {season}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium">Occasions</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedItem.occasion && selectedItem.occasion.map(occasion => (
                      <Badge key={occasion} variant="outline" className="text-xs">
                        {occasion}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium">Brand</p>
                  <p className="text-sm text-gray-600">{selectedItem.brand || 'Unknown'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Wear Count</p>
                  <p className="text-sm text-gray-600">{selectedItem.wear_count}</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
