// Test setup for jest-expo.
//
// Only the *native* edges are mocked here: the OS keychain, the connectivity module, the
// device's position, the photo library, and one function of the font registry.
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
// src/test-support/platform.ts, and they are what every test above the ports uses. Four of
// these exist so the two ports themselves can be tested at all.
//
// **The fifth is a different kind and is called out rather than folded in.** `expo-font` is
// not the far side of a port and nothing here is testing it: it is mocked *partially* — the
// real module, with one function replaced — because a single native CONSTANT it reads is
// absent under jest-expo, and every icon in the app asks for it before it draws. That is a
// harness gap, not a boundary.
//
// Three more gaps of that kind follow, each called out where it is: a function React Native's
// own jest mock leaves out, React's scheduler reading the real clock under fake timers, and a
// rendered node printed as its whole fiber.

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

// --- the device's own storage -------------------------------------------------
// AsyncStorage is a native module with no JS fallback, and exactly one module reads it: the
// feature flags' saved datafile (ADR-0180 §6). The library ships its own in-memory mock of the
// whole surface, which is the far side of that module the way the keychain map above is the far
// side of `shared/lib/auth` — so it is used as it comes rather than restated.
//
// **Emptied after every test**, unlike the keychain, which every suite that signs in clears for
// itself. Nothing but the flag seam writes here, and a datafile a flag suite saved would
// otherwise be read back by the next suite's launch as that device's last good one — a Find a
// game switched off in a suite that never mentioned a flag.
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
);
afterEach(() => require('@react-native-async-storage/async-storage').clear());

// --- the font registry ------------------------------------------------------
// The one partial mock in this file, and the one that is not a port's far side.
//
// `@expo/vector-icons` asks `Font.isLoaded()` in every icon's constructor, and `isLoaded`
// reads `ExpoFontLoader.loadedFonts` — a NATIVE constant jest-expo does not supply, so the
// real implementation throws `loadedNativeFonts.forEach is not a function` before a single
// glyph renders. **Only that one function is replaced.** `loadAsync` stays real, because
// `bootstrap/fonts.ts` is the module this app actually has to get right and `fonts.test.ts`
// is what holds it; and the answer is `true` because a glyph font the native side registers
// at launch is loaded by the time anything draws.
jest.mock('expo-font', () => ({
  ...jest.requireActual('expo-font'),
  isLoaded: jest.fn(() => true),
}));

// --- one function React Native's own jest mock leaves out ---------------------
// The second gap of the `expo-font` kind, and called out for the same reason: this is not a
// port's far side and nothing here is testing React Native.
//
// `AccessibilityInfo.announceForAccessibilityWithOptions` is public API and is what
// design-system Part 13's *queued* announcement is — but `react-native/jest/setup.js` lists
// `announceForAccessibility` and not the variant beside it, so a component that speaks
// politely throws `is not a function` under jest and passes on a device. The real module is
// left alone; one absent function is supplied, exactly as `expo-font`'s `isLoaded` is.
require('react-native/Libraries/Components/AccessibilityInfo/AccessibilityInfo').default.announceForAccessibilityWithOptions ??=
  jest.fn();

// --- React's scheduler, on the clock the suite is on ----------------------------
// The third gap of the `expo-font` kind, and the one that made tests race the machine they ran
// on (#493): nothing here is testing React. `scheduler` read the real clock under suites whose
// every other clock is fake, so how many of a commit's effects ran before a test's next step was
// a fact about the runner — and on a starved one a press landed on a control whose `Pressable`
// had not yet heard it was enabled. It is also what bounds the deck suite's memory (#494): the
// clock `scheduler` captured was React Native's `jest.fn` `performance.now`, which kept every
// call on record. The reasoning, and what was measured, is in the module.
//
// First, because the next section renders, and a render loads the scheduler.
require('./src/test-support/schedulerClock').runSchedulerOnTheSuiteClock();

// --- a rendered node prints as the element it is --------------------------------
// The fourth gap of the same kind, and the other half of #493: nothing here is testing the
// renderer. A failing matcher walked a node's whole fiber to print it — on every poll of a
// `waitFor` that had not passed yet — which spent a test's budget formatting on a starved runner
// and half the deck suite's time. The reasoning is in the module.
require('./src/test-support/nodePrinting').printNodesAsElements();

// --- the gesture system and the UI-thread animations ----------------------------
// The radar's field moves on `react-native-gesture-handler` and `react-native-reanimated`
// (ADR-0176 §2), and both are native modules with an official jest shape rather than a
// port: the gesture library's own setup registers the handlers a `GestureDetector` mounts,
// and reanimated's runs every worklet — a gesture's callbacks, an animated style, a reaction
// — on the JavaScript thread, with `withTiming` driven by the harness's fake clock. Nothing
// above them is replaced: `radar.test.tsx` fires the field's gestures through the library's
// own `fireGestureHandler` and reads the field it drew.
require('react-native-gesture-handler/jestSetup');
require('react-native-reanimated').setUpTests();

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
