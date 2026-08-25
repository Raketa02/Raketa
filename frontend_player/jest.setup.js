// Test setup for jest-expo.
//
// Only the *native* edges are mocked here: the OS keychain, the connectivity module, the
// device's position and the photo library.
// Everything above the socket — the http client, its timeouts, error mapping, mappers,
// use-cases, hooks and screens — runs for real, because a test that mocked those would
// pass while the app was broken.
//
// `fetch` is faked per test through src/test-support/transport.ts rather than globally,
// so each test states its own network.
//
// These are `jest.mock` calls on real modules, which .claude/rules/testing.md tells you
// not to reach for — and the rule is about *ports*: mock those with hand-written stubs.
// It is not being bent. A native module is the far side of a port, not a port; it has no
// JS implementation to run, so there is nothing to stub by hand and nothing above it
// would execute. The hand-written stubs the rule asks for are in
// src/test-support/platform.ts, and they are what every test above the ports uses. These
// four exist so the two ports themselves can be tested at all.

// --- the OS keychain --------------------------------------------------------
// expo-secure-store talks to the iOS Keychain / Android Keystore and has no JS
// implementation to fall back on. An in-memory map with the same async shape is enough
// to exercise every path src/shared/lib/auth actually takes, including a failing read.
jest.mock('expo-secure-store', () => {
  const store = new Map();
  return {
    __store: store,
    getItemAsync: jest.fn(async (key) => (store.has(key) ? store.get(key) : null)),
    setItemAsync: jest.fn(async (key, value) => {
      store.set(key, value);
    }),
    deleteItemAsync: jest.fn(async (key) => {
      store.delete(key);
    }),
  };
});

// --- native connectivity ----------------------------------------------------
// Reports a working connection and never changes it. Tests that care about offline
// behaviour drive onlineManager directly rather than through this.
jest.mock('expo-network', () => ({
  addNetworkStateListener: jest.fn(() => ({ remove: jest.fn() })),
  getNetworkStateAsync: jest.fn(async () => ({
    isConnected: true,
    isInternetReachable: true,
  })),
}));

// --- the device's own position ----------------------------------------------
// expo-location is a native module with no JS fallback. The default is a device that has
// not been asked yet and, once asked, says yes — the ordinary path — and every test that
// wants another answer overrides these per case.
//
// The two *background* functions are mocked although nothing calls them, and that is the
// point: `location.test.ts` asserts they were never called, which is how "foreground
// only, no movement trail" is a fact about the code rather than a sentence in a comment.
jest.mock('expo-location', () => ({
  Accuracy: { Lowest: 1, Low: 2, Balanced: 3, High: 4, Highest: 5, BestForNavigation: 6 },
  getForegroundPermissionsAsync: jest.fn(async () => ({
    granted: false,
    canAskAgain: true,
    status: 'undetermined',
  })),
  requestForegroundPermissionsAsync: jest.fn(async () => ({
    granted: true,
    canAskAgain: false,
    status: 'granted',
  })),
  getCurrentPositionAsync: jest.fn(async () => ({
    coords: { latitude: 41.3874, longitude: 2.1686, accuracy: 12 },
    timestamp: 0,
  })),
  getBackgroundPermissionsAsync: jest.fn(),
  requestBackgroundPermissionsAsync: jest.fn(),
  startLocationUpdatesAsync: jest.fn(),
  watchPositionAsync: jest.fn(),
}));

// --- the photo library -------------------------------------------------------
// Same shape, same reason. `launchImageLibraryAsync` defaults to a player who opened the
// picker and backed out, because that is the case a port most easily gets wrong.
jest.mock('expo-image-picker', () => ({
  getMediaLibraryPermissionsAsync: jest.fn(async () => ({
    granted: false,
    canAskAgain: true,
    status: 'undetermined',
  })),
  requestMediaLibraryPermissionsAsync: jest.fn(async () => ({
    granted: true,
    canAskAgain: false,
    status: 'granted',
  })),
  launchImageLibraryAsync: jest.fn(async () => ({ canceled: true, assets: null })),
}));

// --- public runtime config --------------------------------------------------
// The variables themselves are set in jest.config.js — see the note there; Babel inlines
// them at transform time, so setting them from here would be too late.
//
// What happens here is the step the bootstrap sequence performs: config is read and
// validated once, through `loadEnv`. A test that skipped it would have every request fail
// on unvalidated config rather than on whatever the test is actually about.
// `src/shared/config/env.test.ts` still covers the failure paths, on `parseEnv`.
require('./src/shared/config/env').loadEnv();

// --- Query's garbage-collection timers ---------------------------------------
// `gcTime` is five minutes, so an unmounted query or mutation leaves a real five-minute
// timer behind and the jest worker's event loop never empties — which is the whole of the
// "failed to exit gracefully" warning (#29). `queryClient.clear()` cannot cancel all of
// them; the reasoning, and what was measured, is in the module.
//
// Installed here rather than per suite so no suite has to remember, and installed before
// any test file loads so nothing is scheduled through the old provider.
require('./src/test-support/queryTimeouts').installUnrefTimeouts();
