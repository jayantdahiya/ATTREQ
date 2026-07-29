module.exports = {
  preset: 'react-native',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testPathIgnorePatterns: ['/node_modules/', '/_legacy/'],
  modulePathIgnorePatterns: ['/_legacy/'],
  transformIgnorePatterns: [
    'node_modules/(?!(@react-native|react-native|react-native-svg|react-native-reanimated|react-native-worklets|@react-navigation|react-native-gesture-handler|react-native-safe-area-context|@shopify/flash-list|axios)/)',
  ],
};
