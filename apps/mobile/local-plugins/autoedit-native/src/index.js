'use strict';

// AutoEdit AI native shell plugin. All behaviour lives in
// ios/Sources/AutoeditNativePlugin/AutoEditNativePlugin.swift via Capacitor's
// `shouldOverrideLoad` hook. This module exists only so npm + the Capacitor CLI
// treat the package as a plugin and link the iOS pod. The app loads a remote
// URL, so nothing here executes at runtime.

try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { registerPlugin } = require('@capacitor/core');
  module.exports = { AutoEditNative: registerPlugin('AutoEditNative') };
} catch (err) {
  module.exports = { AutoEditNative: undefined };
}
