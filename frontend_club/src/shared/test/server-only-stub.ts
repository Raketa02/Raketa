/**
 * What `server-only` resolves to under Vitest.
 *
 * The real package exports a module that throws on import unless the bundler applied the
 * `react-server` export condition — which is exactly how it turns "a Client Component
 * imported server code" into a build error. Vitest is neither bundler, so importing a
 * server module in a unit test would hit that throw and fail before an assertion ran.
 *
 * Turning the `react-server` condition on globally instead would also redirect `react`
 * itself to its server build and break `@testing-library/react`, so the alias is aimed at
 * this one specifier. Wired up in `vitest.config.ts`.
 *
 * This does **not** weaken the boundary: the boundary is enforced by the Next bundler at
 * build time, on the real module graph. Nothing about the test runner's module resolution
 * reaches production.
 */

export {};
