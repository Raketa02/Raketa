/**
 * Metro injects a `process` shim into the bundle, and Expo's Babel plugin substitutes
 * `EXPO_PUBLIC_*` reads inside it at build time. `env.ts` is the only module that touches
 * either, so the declaration lives beside it.
 *
 * Declared narrowly on purpose. Installing `@types/node` would satisfy the same error by
 * telling the type checker that `fs`, `Buffer`, `path` and the rest of Node exist — in a
 * runtime that has none of them, where the mistake surfaces as a red screen on a device
 * rather than as a compile error.
 */
declare const process: {
  readonly env: Readonly<Record<string, string | undefined>>;
};
