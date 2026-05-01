import '@testing-library/jest-native/extend-expect'

jest.doMock('react-native-reanimated', () => {
  const React = require('react')
  const { View } = require('react-native')
  const chain = {
    delay: () => chain,
    duration: () => chain,
    easing: () => chain,
  }

  return {
    __esModule: true,
    default: {
      View,
      createAnimatedComponent: (component: unknown) => component,
    },
    Easing: {
      bezier: () => (value: number) => value,
      inOut: () => (value: number) => value,
      out: () => (value: number) => value,
      quad: (value: number) => value,
    },
    FadeIn: chain,
    FadeInDown: chain,
    ZoomIn: chain,
    createAnimatedComponent: (component: unknown) => component,
    useAnimatedStyle: (factory: () => unknown) => factory(),
    useSharedValue: (value: unknown) => ({ value }),
    withRepeat: (value: unknown) => value,
    withTiming: (value: unknown) => value,
  }
})
jest.doMock('expo-linear-gradient', () => {
  const React = require('react')
  const { View } = require('react-native')
  return {
    LinearGradient: ({ children, ...props }: { children?: React.ReactNode }) =>
      React.createElement(View, props, children),
  }
})
jest.doMock('expo-image', () => {
  const { Image } = require('react-native')
  return { Image }
})
jest.doMock('@expo/vector-icons', () => {
  const React = require('react')
  const { Text } = require('react-native')
  const Icon = ({ name }: { name?: string }) => React.createElement(Text, null, name ?? 'icon')
  return {
    Ionicons: Icon,
  }
})
jest.doMock('expo-haptics', () => ({
  ImpactFeedbackStyle: { Light: 'light' },
  impactAsync: jest.fn(),
}))
jest.doMock('@expo-google-fonts/cormorant-garamond', () => ({
  CormorantGaramond_600SemiBold: 1,
  CormorantGaramond_700Bold: 1,
}))
jest.doMock('@expo-google-fonts/dm-sans', () => ({
  DMSans_400Regular: 1,
  DMSans_500Medium: 1,
  DMSans_600SemiBold: 1,
}))
jest.doMock('@expo-google-fonts/ibm-plex-mono', () => ({
  IBMPlexMono_400Regular: 1,
  IBMPlexMono_500Medium: 1,
}))
jest.doMock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}))
jest.doMock('expo-location', () => ({
  requestForegroundPermissionsAsync: jest.fn(),
  getCurrentPositionAsync: jest.fn(),
  reverseGeocodeAsync: jest.fn(),
}))
jest.doMock('expo-image-picker', () => ({
  ImagePicker: {},
  MediaTypeOptions: {},
  requestMediaLibraryPermissionsAsync: jest.fn(),
  requestCameraPermissionsAsync: jest.fn(),
  launchImageLibraryAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  CameraType: { back: 'back' },
}))
