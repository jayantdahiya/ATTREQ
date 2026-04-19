import type { ReactNode } from 'react'
import Animated, { FadeInDown } from 'react-native-reanimated'

export function AnimatedListItem({ children, index }: { children: ReactNode; index: number }) {
  return <Animated.View entering={FadeInDown.delay(index * 80).duration(400)}>{children}</Animated.View>
}
