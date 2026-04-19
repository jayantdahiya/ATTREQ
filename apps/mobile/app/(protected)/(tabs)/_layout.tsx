import { Ionicons } from '@expo/vector-icons'
import { Tabs } from 'expo-router'
import { useEffect } from 'react'
import { View } from 'react-native'
import Animated, { Easing, useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated'

import { Text } from '@/components/ui/text'
import { useThemeColors } from '@/theme/colors'

function TabIcon({ color, focused, name }: { color: string; focused: boolean; name: keyof typeof Ionicons.glyphMap }) {
  const scale = useSharedValue(focused ? 1.05 : 1)

  useEffect(() => {
    scale.value = withTiming(focused ? 1.08 : 1, { duration: 220, easing: Easing.out(Easing.quad) })
  }, [focused, scale])

  const iconStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }))

  return (
    <View className="items-center">
      <Animated.View style={iconStyle}>
        <Ionicons color={color} name={name} size={22} />
      </Animated.View>
      <View
        className="mt-1 h-1 w-1 rounded-full"
        style={{ backgroundColor: focused ? color : 'transparent' }}
      />
    </View>
  )
}

export default function TabsLayout() {
  const { colors } = useThemeColors()

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.accentMoss,
        tabBarInactiveTintColor: colors.textTertiary,
        tabBarStyle: {
          borderTopWidth: 0,
          backgroundColor: colors.bgDeep,
          height: 96,
          paddingTop: 12,
          paddingBottom: 14,
        },
        tabBarLabel: ({ color, children }) => (
          <Text color={color === colors.accentMoss ? 'textPrimary' : 'textTertiary'} preset="caption">
            {children}
          </Text>
        ),
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Today',
          tabBarIcon: ({ color, focused }) => <TabIcon color={color} focused={focused} name="sunny-outline" />,
        }}
      />
      <Tabs.Screen
        name="wardrobe"
        options={{
          title: 'Wardrobe',
          tabBarIcon: ({ color, focused }) => <TabIcon color={color} focused={focused} name="shirt-outline" />,
        }}
      />
      <Tabs.Screen
        name="history"
        options={{
          title: 'History',
          tabBarIcon: ({ color, focused }) => <TabIcon color={color} focused={focused} name="albums-outline" />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, focused }) => <TabIcon color={color} focused={focused} name="person-outline" />,
        }}
      />
    </Tabs>
  )
}
