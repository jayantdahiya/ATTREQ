import { Pressable, View } from 'react-native'
import { Image } from 'expo-image'
import { Ionicons } from '@expo/vector-icons'

import { useThemeColors } from '@/theme/colors'
import type { StylePhotoAsset } from '@/lib/api/style-dna'

interface PhotoGridProps {
  photos: StylePhotoAsset[]
  onRemove: (index: number) => void
}

export function PhotoGrid({ photos, onRemove }: PhotoGridProps) {
  const { colors } = useThemeColors()

  return (
    <View className="flex-row flex-wrap gap-2">
      {photos.map((photo, idx) => (
        <View key={photo.uri} className="relative">
          <Image
            source={{ uri: photo.uri }}
            style={{ width: 90, height: 90, borderRadius: 8 }}
            contentFit="cover"
          />
          <Pressable
            onPress={() => onRemove(idx)}
            className="absolute top-1 right-1 rounded-full p-0.5"
            style={{ backgroundColor: colors.bgDeep }}
          >
            <Ionicons name="close-circle" size={18} color={colors.textMuted} />
          </Pressable>
        </View>
      ))}
    </View>
  )
}
