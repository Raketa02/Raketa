/**
 * The real `react-native-reanimated`, under the name of its mock.
 *
 * `expo-router/testing-library` `jest.mock`s reanimated with the library's inert mock the
 * moment it is imported — no reaction ever fires, `withTiming` lands at once — and registers
 * it after anything a test file could hoist, so no test can undo it. The radar's field is
 * real reanimated under test (ADR-0176 §2: gestures fired through the library's own
 * utilities, flights driven by the fake clock), so `jest.config.js` points the mock's module
 * name here, and the router's factory hands out the module `jest.setup.js` already set up.
 *
 * `requireActual` and not `require`, because inside that factory a plain `require` of the
 * module being mocked is the factory calling itself.
 *
 * Not app code — nothing under `src/` outside the jest configuration reaches this.
 */

module.exports = jest.requireActual('react-native-reanimated');
