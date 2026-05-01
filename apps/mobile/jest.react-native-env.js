const ReactNativeEnv = require('react-native/jest/react-native-env')

module.exports = class AttreqReactNativeEnv extends ReactNativeEnv {
  constructor(config, context) {
    super(
      {
        ...config,
        projectConfig: {
          ...(config?.projectConfig ?? {}),
          testEnvironmentOptions: config?.projectConfig?.testEnvironmentOptions ?? {},
        },
      },
      context
    )
  }
}
