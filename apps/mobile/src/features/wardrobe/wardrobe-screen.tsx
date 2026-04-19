import { Ionicons } from '@expo/vector-icons'
import { FlashList } from '@shopify/flash-list'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as ImagePicker from 'expo-image-picker'
import { Image } from 'expo-image'
import { LinearGradient } from 'expo-linear-gradient'
import { useState } from 'react'
import { Alert, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { AnimatedListItem } from '@/components/common/animated-list-item'
import { EmptyState } from '@/components/common/empty-state'
import { LoadingScreen } from '@/components/common/loading-screen'
import { ScreenHeader } from '@/components/common/screen-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Text } from '@/components/ui/text'
import { authApi } from '@/lib/api/auth'
import { queryKeys } from '@/lib/query/query-client'
import { wardrobeApi, type UploadAssetInput } from '@/lib/api/wardrobe'
import { WardrobeItemCard } from '@/features/wardrobe/wardrobe-item-card'
import { useThemeColors } from '@/theme/colors'

type DraftAsset = UploadAssetInput & { previewUri: string }

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

  return (
    <SafeAreaView className="flex-1" style={{ backgroundColor: colors.bgDeep }}>
      <FlashList
        contentContainerStyle={{ padding: 24, paddingBottom: 120 }}
        data={items}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={
          <View className="mb-6 gap-6">
            <View>
              <ScreenHeader
                heading="Capture once, style daily."
                label="WARDROBE"
                subtitle={`${meQuery.data?.full_name ? `${meQuery.data.full_name},` : 'You'} currently have ${items.length} tracked items.`}
              />
              <View className="mt-4">
                <Badge label={`${items.length} ITEMS`} variant="muted" />
              </View>
            </View>

            <View className="flex-row gap-3">
              <Card className="flex-1 gap-2 p-4" onPress={() => void startDraft('library')} variant="outlined">
                <Ionicons color={colors.accentGold} name="images-outline" size={22} />
                <Text preset="h3">Photo Library</Text>
                <Text color="textSecondary" preset="caption">
                  Pick from your camera roll
                </Text>
              </Card>
              <Card className="flex-1 gap-2 p-4" onPress={() => void startDraft('camera')} variant="outlined">
                <Ionicons color={colors.accentMoss} name="camera-outline" size={22} />
                <Text preset="h3">Camera</Text>
                <Text color="textSecondary" preset="caption">
                  Capture right now
                </Text>
              </Card>
            </View>

            {draftAsset ? (
              <Card className="overflow-hidden p-0" variant="elevated">
                <Image
                  contentFit="cover"
                  source={{ uri: draftAsset.previewUri }}
                  style={{ width: '100%', height: 280, backgroundColor: colors.bgRaised }}
                />
                <LinearGradient
                  colors={['transparent', 'rgba(0,0,0,0.65)']}
                  style={{
                    bottom: 0,
                    left: 0,
                    padding: 16,
                    position: 'absolute',
                    right: 0,
                  }}
                >
                  <View className="flex-row gap-3">
                    <Button
                      className="flex-1"
                      icon={<Ionicons color={colors.textPrimary} name="cloud-upload-outline" size={17} />}
                      isLoading={uploadMutation.isPending}
                      label="Upload"
                      onPress={() => uploadMutation.mutate(draftAsset)}
                    />
                    <Button
                      className="flex-1"
                      icon={<Ionicons color={colors.accentGold} name="trash-outline" size={17} />}
                      label="Discard"
                      onPress={() => setDraftAsset(null)}
                      variant="ghost"
                    />
                  </View>
                </LinearGradient>
              </Card>
            ) : null}

            {items.length === 0 ? (
              <EmptyState
                title="No wardrobe items yet"
                message="Upload a top, bottom, or accessory to unlock outfit generation."
              />
            ) : null}
          </View>
        }
        renderItem={({ item, index }) => (
          <AnimatedListItem index={index}>
            <WardrobeItemCard item={item} />
          </AnimatedListItem>
        )}
        ItemSeparatorComponent={() => <View className="h-4" />}
      />
    </SafeAreaView>
  )
}
