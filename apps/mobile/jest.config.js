module.exports = {
  preset: 'react-native',
  testEnvironment: '<rootDir>/jest.react-native-env.js',
  forceExit: true,
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native|@react-navigation|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|expo-router|@expo/vector-icons|nativewind|react-native-reanimated|react-native-safe-area-context|@shopify/flash-list))',
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
}
