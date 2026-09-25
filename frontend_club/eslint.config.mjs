import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';

// ---------------------------------------------------------------------------
// The club website's standard (docs/architecture.md, ADR-0187 §6), enforced by the linter
// where a rule can be. Restriction entries are composed rather than repeated: flat config
// *replaces* a rule a later block re-declares, so a block that meant to add one ban would
// silently drop the others.
// ---------------------------------------------------------------------------

/** The generated wire types: `src/server/` and a feature's `mappers.ts` only. */
const generatedTypes = {
  group: ['@/generated/*', '**/generated/schema'],
  message:
    "Only src/server/ and a feature's mappers.ts import a generated wire type. Map it to a view model in mappers.ts. See docs/architecture.md.",
};

/** The other apps are separate deployables; they talk over HTTP only (ADR-0005). */
const otherApps = {
  group: ['**/frontend_player/**', '**/frontend_public/**', '**/backend/**'],
  message:
    'frontend_club never imports from another app. Apps talk over HTTP only. See docs/adr/0005.',
};

/** Pages and layouts compose features and primitives; the server layer is a feature's to call. */
const serverLayer = {
  group: ['@/server/*'],
  message:
    "Reach the backend through a feature's queries.ts or actions.ts, never from a route, a component or a primitive. See docs/architecture.md.",
};

/** A primitive knows nothing of the club, the session or any feature. */
const features = {
  group: ['@/features/*', '@/features/**'],
  message: 'src/ui/ holds presentational primitives only; it never imports a feature.',
};

const restrict = (...patterns) => ['error', { patterns }];

export default defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([
    '.next/**',
    'node_modules/**',
    'src/generated/**',
    'playwright-report/**',
    'test-results/**',
    'next-env.d.ts',
  ]),
  {
    files: ['**/*.{ts,tsx,mjs}'],
    rules: {
      'no-restricted-imports': restrict(generatedTypes, otherApps),
      // Every size and colour is a token; an inline style is where a literal would hide.
      'react/forbid-dom-props': ['error', { forbid: ['style'] }],
    },
  },
  {
    files: ['src/server/**', 'src/features/*/mappers.ts', 'e2e/**'],
    rules: { 'no-restricted-imports': restrict(otherApps) },
  },
  {
    // Playwright's fixtures hand over with a function called `use`, which is not React's.
    files: ['e2e/**'],
    rules: { 'react-hooks/rules-of-hooks': 'off' },
  },
  {
    files: ['src/app/**', 'src/features/*/components/**'],
    rules: { 'no-restricted-imports': restrict(generatedTypes, otherApps, serverLayer) },
  },
  {
    // The session's own routes are the server layer's endpoints, as the proxy is.
    files: ['src/app/session/**/route.ts'],
    rules: { 'no-restricted-imports': restrict(generatedTypes, otherApps) },
  },
  {
    files: ['src/ui/**'],
    rules: { 'no-restricted-imports': restrict(generatedTypes, otherApps, serverLayer, features) },
  },
]);
