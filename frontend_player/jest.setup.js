// Test setup for jest-expo.
//
// Only the *native* edges are mocked here: the OS keychain and the connectivity module.
// Everything above the socket — the http client, its timeouts, error mapping, mappers,
// use-cases, hooks and screens — runs for real, because a test that mocked those would
// pass while the app was broken.
//
// `fetch` is faked per test through src/test-support/transport.ts rather than globally,
// so each test states its own network.

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
