// Learn more: https://docs.expo.dev/guides/customizing-metro/
const { getDefaultConfig } = require('expo/metro-config');

// NOTE: this app owns its own node_modules and shares no workspace packages with
// frontend_club (ADR-0005). That is why there is no `watchFolders` /
// `nodeModulesPaths` monorepo block here — Metro's defaults are correct.
// If shared packages are ever introduced, this file is where that support goes.
const config = getDefaultConfig(__dirname);

module.exports = config;
