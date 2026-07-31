module.exports = {
  root: true,
  extends: '@react-native',
  // Mirror tsconfig/jest: the pre-rewrite Expo app is excluded from tooling.
  ignorePatterns: ['_legacy/', 'android/', 'ios/', 'node_modules/'],
  rules: {
    // This app deliberately styles with inline objects on top of the design
    // system components (no StyleSheet layer), so the rule flags every screen.
    'react-native/no-inline-styles': 'off',
    // `void somePromise` is the codebase's fire-and-forget idiom.
    'no-void': ['warn', { allowAsStatement: true }],
  },
};
