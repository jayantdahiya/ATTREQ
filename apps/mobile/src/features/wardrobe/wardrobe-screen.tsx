import { Ionicons } from '@expo/vector-icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as ImagePicker from 'expo-image-picker'
import { Image } from 'expo-image'
import { LinearGradient } from 'expo-linear-gradient'
import { useState } from 'react'
import { Alert, ScrollView, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { EditorialCard, EditorialHeader, GarmentTile, IconCircle, MonoLabel, fontFamily, type GarmentTone } from '@/components/attreq/editorial'
import { EmptyState } from '@/components/common/empty-state'
import { LoadingScreen } from '@/components/common/loading-screen'
import { Button } from '@/components/ui/button'
import { Text } from '@/components/ui/text'
import { authApi } from '@/lib/api/auth'
import { queryKeys } from '@/lib/query/query-client'
import { wardrobeApi, type UploadAssetInput } from '@/lib/api/wardrobe'
import { resolveApiImageUrl } from '@/lib/utils/images'
import { useThemeColors } from '@/theme/colors'
import type { WardrobeItem } from '@/lib/api/types'

type DraftAsset = UploadAssetInput & { previewUri: string }

const categories = ['All', 'Tops', 'Bottoms', 'Outer', 'Accents', 'Shoes']

function toneForCategory(category?: string | null): GarmentTone {
  const value = category?.toLowerCase() ?? ''
  if (value.includes('bottom') || value.includes('pant') || value.includes('trouser')) return 'bottom'
  if (value.includes('shoe') || value.includes('boot')) return 'shoes'
  if (value.includes('outer') || value.includes('coat') || value.includes('jacket')) return 'outer'
  if (value.includes('bag')) return 'bag'
  if (value.includes('access') || value.includes('scarf')) return 'accent'
  return 'top'
}

function WardrobeMasonryItem({ item, index }: { item: WardrobeItem; index: number }) {
  const uri = resolveApiImageUrl(item.thumbnail_url ?? item.processed_image_url ?? item.original_image_url)
  const height = [220, 260, 238, 184, 204, 230][index % 6]

  return (
    <View className="mb-4">
      <GarmentTile imageStyle={{ height }} tone={toneForCategory(item.category)} uri={uri} />
      <View className="px-0.5 pt-2">
        <Text preset="h3" style={{ fontFamily: fontFamily.displaySemi, fontStyle: 'italic' }}>
          {item.category ?? 'Processing item'}
        </Text>
        <MonoLabel>{item.color_primary ?? item.processing_status}</MonoLabel>
      </View>
    </View>
  )
}

async function pickAsset(source: 'library' | 'camera') {
  const permission =
    source === 'library'
      ? await ImagePicker.requestMediaLibraryPermissionsAsync()
      : await ImagePicker.requestCameraPermissionsAsync()

  if (!permission.granted) {
    throw new Error(
      source === 'library'
        ? 'Photo library permission is required to upload wardrobe items.'
        : 'Camera permission is required to capture wardrobe items.'
    )
  }

  const result =
    source === 'library'
      ? await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ['images'],
          quality: 0.9,
        })
      : await ImagePicker.launchCameraAsync({
          cameraType: ImagePicker.CameraType.back,
          mediaTypes: ['images'],
          quality: 0.9,
        })

  if (result.canceled || !result.assets[0]) {
    return null
  }

  const asset = result.assets[0]
  return {
    mimeType: asset.mimeType ?? 'image/jpeg',
    name: asset.fileName ?? `wardrobe-${Date.now()}.jpg`,
    previewUri: asset.uri,
    uri: asset.uri,
  } satisfies DraftAsset
}

export function WardrobeScreen() {
  const { colors } = useThemeColors()
  const queryClient = useQueryClient()
  const [draftAsset, setDraftAsset] = useState<DraftAsset | null>(null)

  const meQuery = useQuery({
    queryKey: queryKeys.me,
    queryFn: authApi.getCurrentUser,
  })

  const wardrobeQuery = useQuery({
    queryKey: queryKeys.wardrobe,
    queryFn: () => wardrobeApi.listItems(),
  })

  const uploadMutation = useMutation({
    mutationFn: wardrobeApi.uploadItem,
    onSuccess: async () => {
      setDraftAsset(null)
      await queryClient.invalidateQueries({ queryKey: queryKeys.wardrobe })
      Alert.alert('Upload queued', 'Your image is stored and the AI processing flow has started.')
    },
    onError: (error: Error) => {
      Alert.alert('Upload failed', error.message)
    },
  })

  const startDraft = async (source: 'library' | 'camera') => {
    try {
      const asset = await pickAsset(source)
      if (asset) {
        setDraftAsset(asset)
      }
    } catch (error) {
      Alert.alert('Permission required', error instanceof Error ? error.message : 'Unable to access media source.')
    }
  }

  if (meQuery.isLoading || wardrobeQuery.isLoading) {
    return <LoadingScreen label="Loading your wardrobe" />
  }

  const items = wardrobeQuery.data?.items ?? []
  const columns = [items.filter((_, index) => index % 2 === 0), items.filter((_, index) => index % 2 === 1)]

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 130 }}>
        <EditorialHeader
          label="Closet"
          right={
            <IconCircle>
              <Ionicons color={colors.textSecondary} name="search-outline" size={16} />
            </IconCircle>
          }
          subtitle={
            <>
              <Text color="accentGold" preset="bodySmall">
                {items.length} pieces
              </Text>
              {' - last added recently'}
            </>
          }
          title="Wardrobe"
        />

        <ScrollView className="-mx-6 mt-5" contentContainerStyle={{ gap: 6, paddingHorizontal: 24 }} horizontal showsHorizontalScrollIndicator={false}>
          {categories.map((category, index) => (
            <View
              key={category}
              className="rounded-full border px-4 py-2"
              style={{
                backgroundColor: index === 0 ? colors.textPrimary : 'transparent',
                borderColor: index === 0 ? colors.textPrimary : colors.borderSubtle,
              }}
            >
              <Text preset="label" style={{ color: index === 0 ? colors.bgDeep : colors.textSecondary }}>
                {category}
              </Text>
            </View>
          ))}
        </ScrollView>

        <View className="mt-5 flex-row gap-3">
          <EditorialCard className="flex-1 border-dashed p-4" onPress={() => void startDraft('camera')} style={{ backgroundColor: colors.glowMoss }}>
            <View className="mb-3 h-8 w-8 items-center justify-center rounded-full" style={{ backgroundColor: colors.accentMoss }}>
              <Ionicons color="#F0EDE6" name="camera-outline" size={16} />
            </View>
            <Text preset="h3" style={{ fontFamily: fontFamily.displaySemi }}>
              Camera
            </Text>
            <Text className="mt-1" color="textSecondary" preset="caption">
              Capture a piece
            </Text>
          </EditorialCard>
          <EditorialCard className="flex-1 border-dashed p-4" onPress={() => void startDraft('library')}>
            <View className="mb-3 h-8 w-8 items-center justify-center rounded-full" style={{ backgroundColor: colors.bgRaised }}>
              <Ionicons color={colors.accentGold} name="images-outline" size={16} />
            </View>
            <Text preset="h3" style={{ fontFamily: fontFamily.displaySemi }}>
              Library
            </Text>
            <Text className="mt-1" color="textSecondary" preset="caption">
              From photos
            </Text>
          </EditorialCard>
        </View>

        {draftAsset ? (
          <View className="mt-6 overflow-hidden rounded-3xl border" style={{ borderColor: colors.goldSoft }}>
            <Image
              contentFit="cover"
              source={{ uri: draftAsset.previewUri }}
              style={{ width: '100%', height: 280, backgroundColor: colors.bgRaised }}
            />
            <LinearGradient
              colors={['transparent', 'rgba(13,18,16,0.88)']}
              style={{
                bottom: 0,
                left: 0,
                padding: 16,
                position: 'absolute',
                right: 0,
              }}
            >
              <MonoLabel color="accentGold">Preview - uploading</MonoLabel>
              <View className="mt-4 flex-row gap-3">
                <Button
                  className="flex-1"
                  icon={<Ionicons color="#F0EDE6" name="cloud-upload-outline" size={17} />}
                  isLoading={uploadMutation.isPending}
                  label="Upload"
                  onPress={() => uploadMutation.mutate(draftAsset)}
                />
                <Button
                  className="w-28"
                  icon={<Ionicons color={colors.accentGold} name="trash-outline" size={17} />}
                  label="Discard"
                  onPress={() => setDraftAsset(null)}
                  variant="ghost"
                />
              </View>
            </LinearGradient>
          </View>
        ) : null}

        {items.length === 0 ? (
          <View className="mt-6">
            <EmptyState
              title="No wardrobe items yet"
              message="Upload a top, bottom, or accessory to unlock outfit generation."
            />
          </View>
        ) : (
          <View className="mt-6 flex-row gap-3">
            {columns.map((column, columnIndex) => (
              <View key={columnIndex} className="flex-1">
                {column.map((item, index) => (
                  <WardrobeMasonryItem key={item.id} item={item} index={index + columnIndex} />
                ))}
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  )
}
