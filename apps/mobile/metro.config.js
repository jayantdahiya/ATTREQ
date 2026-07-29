const path = require('path');
const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

// Monorepo/workspace-aware: deps are hoisted to the repo-root node_modules, so Metro
// must watch it and resolve modules from both the app and the workspace root.
const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '../..');

/** @type {import('@react-native/metro-config').MetroConfig} */
const config = {
  watchFolders: [workspaceRoot],
  resolver: {
    nodeModulesPaths: [
      path.resolve(projectRoot, 'node_modules'),
      path.resolve(workspaceRoot, 'node_modules'),
    ],
  },
};

module.exports = mergeConfig(getDefaultConfig(projectRoot), config);
