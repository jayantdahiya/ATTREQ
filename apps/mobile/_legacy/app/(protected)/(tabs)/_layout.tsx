import { Ionicons } from '@expo/vector-icons'
import { Tabs } from 'expo-router'
import { useEffect } from 'react'
import { Pressable, View } from 'react-native'
import Animated, { Easing, useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated'

import { Text } from '@/components/ui/text'
import { useThemeColors } from '@/theme/colors'

const TABS = [
  { name: 'index', icon: 'sunny-outline' as const, label: 'Today' },
  { name: 'wardrobe', icon: 'shirt-outline' as const, label: 'Wardrobe' },
  { name: 'history', icon: 'albums-outline' as const, label: 'History' },
  { name: 'profile', icon: 'person-outline' as const, label: 'Profile' },
]

function TabItem({
  icon,
  label,
  focused,
  onPress,
}: {
  icon: keyof typeof Ionicons.glyphMap
  label: string
  focused: boolean
  onPress: () => void
}) {
  const { colors } = useThemeColors()
  const scale = useSharedValue(focused ? 1.05 : 1)

  useEffect(() => {
    scale.value = withTiming(focused ? 1.08 : 1, { duration: 220, easing: Easing.out(Easing.quad) })
  }, [focused, scale])

  const iconStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }))

  const color = focused ? colors.accentMoss : colors.textTertiary

  return (
    <Pressable
      onPress={onPress}
      style={{
        flex: 1,
        alignItems: 'center',
        gap: 3,
        paddingVertical: 4,
        paddingHorizontal: 10,
        borderRadius: 18,
        backgroundColor: focused ? colors.mossSoft : 'transparent',
      }}
    >
      <Animated.View style={iconStyle}>
        <Ionicons color={color} name={icon} size={20} />
      </Animated.View>
      <Text preset="label" style={{ color, fontSize: 7.5, letterSpacing: 1.2 }}>
        {label}
      </Text>
    </Pressable>
  )
}

function CustomTabBar(props: any) {
  const { state, navigation } = props
  const { colors, isDark } = useThemeColors()

  return (
    <View
      style={{
        bottom: 20,
        left: 12,
        right: 12,
        position: 'absolute',
        flexDirection: 'row',
        backgroundColor: colors.navBg,
        borderRadius: 26,
        borderWidth: 1,
        borderColor: colors.borderSoft,
        paddingVertical: 8,
        paddingHorizontal: 6,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 16 },
        shadowOpacity: isDark ? 0.45 : 0.12,
        shadowRadius: 48,
        elevation: 12,
      }}
    >
      {(state.routes as Array<{ key: string; name: string }>).map((route, index) => {
        const tab = TABS.find((t) => t.name === route.name) ?? TABS[index]
        return (
          <TabItem
            key={route.key}
            focused={state.index === index}
            icon={tab?.icon ?? 'sunny-outline'}
            label={tab?.label ?? ''}
            onPress={() => navigation.navigate(route.name)}
          />
        )
      })}
    </View>
  )
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{ headerShown: false }}
      tabBar={(props) => <CustomTabBar {...props} />}
    >
      <Tabs.Screen name="index" options={{ title: 'Today' }} />
      <Tabs.Screen name="wardrobe" options={{ title: 'Wardrobe' }} />
      <Tabs.Screen name="history" options={{ title: 'History' }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile' }} />
    </Tabs>
  )
}
