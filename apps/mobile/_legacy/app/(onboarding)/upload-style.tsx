import * as ImagePicker from 'expo-image-picker'
import { router } from 'expo-router'
import { useState } from 'react'
import { Alert, Pressable, ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { Text } from '@/components/ui/text'
import type { StylePhotoAsset } from '@/lib/api/style-dna'
import { PhotoGrid } from '@/features/style-dna/components/photo-grid'
import { useUploadStylePhotos } from '@/features/style-dna/hooks/use-style-dna'
import { useThemeColors } from '@/theme/colors'

const MIN_PHOTOS = 3
const MAX_PHOTOS = 8

export default function UploadStyleScreen() {
  const { colors } = useThemeColors()
  const [photos, setPhotos] = useState<StylePhotoAsset[]>([])
  const uploadMutation = useUploadStylePhotos()

  async function pickPhotos() {
    const remaining = MAX_PHOTOS - photos.length
    if (remaining <= 0) return

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsMultipleSelection: true,
      selectionLimit: remaining,
      quality: 0.85,
    })

    if (result.canceled) return

    const newPhotos: StylePhotoAsset[] = result.assets.map((a) => ({
      uri: a.uri,
      name: a.fileName ?? `photo_${Date.now()}.jpg`,
      mimeType: a.mimeType ?? 'image/jpeg',
    }))

    setPhotos((prev) => [...prev, ...newPhotos].slice(0, MAX_PHOTOS))
  }

  function removePhoto(index: number) {
    setPhotos((prev) => prev.filter((_, i) => i !== index))
  }

  async function handleUpload() {
    if (photos.length < MIN_PHOTOS) return

    try {
      const result = await uploadMutation.mutateAsync(photos)
      router.replace({ pathname: '/(onboarding)/results', params: { data: JSON.stringify(result) } })
    } catch (err) {
      Alert.alert(
        'Upload failed',
        err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      )
    }
  }

  const canUpload = photos.length >= MIN_PHOTOS
  const isLoading = uploadMutation.isPending

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 130 }}>
        <Text className="text-2xl font-bold mt-4 mb-2" style={{ color: colors.textPrimary }}>
          Show us your style
        </Text>
        <Text className="text-sm mb-8" style={{ color: colors.textMuted }}>
          Add {MIN_PHOTOS}–{MAX_PHOTOS} photos of outfits you love wearing — mirror shots, selfies, anything. We'll build your Style DNA and pre-fill your wardrobe.
        </Text>

        {photos.length > 0 && (
          <View className="mb-6">
            <PhotoGrid photos={photos} onRemove={removePhoto} />
          </View>
        )}

        {photos.length < MAX_PHOTOS && (
          <Pressable
            onPress={pickPhotos}
            className="rounded-2xl py-5 items-center mb-6"
            style={{ borderColor: colors.borderSubtle, borderWidth: 1, borderStyle: 'dashed' }}
          >
            <Text className="text-3xl mb-1">+</Text>
            <Text className="text-sm" style={{ color: colors.textMuted }}>
              {photos.length === 0 ? 'Select outfit photos' : `Add more (${photos.length}/${MAX_PHOTOS})`}
            </Text>
          </Pressable>
        )}

        <Text className="text-xs text-center mb-6" style={{ color: colors.textMuted }}>
          {photos.length < MIN_PHOTOS
            ? `Select at least ${MIN_PHOTOS} photos to continue`
            : `${photos.length} photo${photos.length !== 1 ? 's' : ''} selected`}
        </Text>

        <Pressable
          onPress={handleUpload}
          disabled={!canUpload || isLoading}
          className="rounded-2xl py-4 items-center"
          style={{
            backgroundColor: canUpload && !isLoading ? colors.accentGold : colors.borderSubtle,
          }}
        >
          <Text className="text-base font-semibold" style={{ color: canUpload && !isLoading ? colors.bgDeep : colors.textMuted }}>
            {isLoading ? 'Analysing your style…' : 'Build my Style DNA →'}
          </Text>
        </Pressable>

        {isLoading && (
          <Text className="text-xs text-center mt-4" style={{ color: colors.textMuted }}>
            This takes 10–30 seconds. We're reading your aesthetic.
          </Text>
        )}
      </ScrollView>
    </SafeAreaView>
  )
}
