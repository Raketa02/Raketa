// `EXPO_PUBLIC_*` variables are set HERE, not in jest.setup.js, and the difference is
// load-bearing. babel-preset-expo substitutes these at **transform time** — the app reads
// `process.env.EXPO_PUBLIC_API_URL` as a statically written member access precisely so
// that it survives bundling — so a value assigned once the test file is already running
// is a value Babel has long since inlined as `undefined`.
//
// This file is evaluated in the main process before any worker forks, and workers inherit
// `process.env`, so the substitution sees them.
//
// These are config, never secrets: the app deliberately refuses to boot without them, and
// CI has no .env file (nor may an agent create one).
process.env.EXPO_PUBLIC_API_URL = 'https://api.test.raketa.invalid';
process.env.EXPO_PUBLIC_ENV = 'development';

module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testMatch: ['<rootDir>/src/**/*.test.{ts,tsx}'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@sentry/react-native|native-base|react-native-svg)',
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
