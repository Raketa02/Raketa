import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';

// ---------------------------------------------------------------------------
// The public site's standard (docs/architecture.md, ADR-0187 §6), enforced by the linter where a
// rule can be. Restriction entries are composed rather than repeated: flat config *replaces* a
// rule a later block re-declares, so a block that meant to add one ban would silently drop the
// others.
// ---------------------------------------------------------------------------

/** The generated wire types: `src/server/` and a feature's `mappers.ts` only. */
const generatedTypes = {
  group: ['@/generated/*', '**/generated/schema'],
  message:
    "Only src/server/ and a feature's mappers.ts import a generated wire type. Map it to a view model in mappers.ts. See docs/architecture.md.",
};

/** The other apps are separate deployables; they talk over HTTP only (ADR-0005). */
const otherApps = {
  group: ['**/frontend_player/**', '**/frontend_club/**', '**/backend/**'],
  message:
    'frontend_public never imports from another app, the club website included: it copies what it borrows. Apps talk over HTTP only. See docs/adr/0005 and 0187 §6.',
};

/** Pages, routes and components compose features; the server layer is a feature's to call. */
const serverLayer = {
  group: ['@/server/*'],
  message:
    "Reach the backend and the configuration through a feature's queries.ts, never from a route, a component or a primitive. See docs/architecture.md.",
};

/** A primitive knows nothing of any feature. */
const features = {
  group: ['@/features/*', '@/features/**'],
  message: 'src/ui/ holds presentational primitives only; it never imports a feature.',
};

/** A feature reads and writes through its own; another feature's are its route's to call. */
const otherFeatureCalls = {
  group: [
    '@/features/*/queries',
    '**/features/*/queries',
    '@/features/*/actions',
    '**/features/*/actions',
  ],
  message:
    "A feature never calls another feature's queries or actions. The route calls them and hands down view models and bound actions. See docs/architecture.md.",
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
    files: ['src/server/**', 'e2e/**'],
    rules: { 'no-restricted-imports': restrict(otherApps) },
  },
  {
    // Playwright's fixtures hand over with a function called `use`, which is not React's.
    files: ['e2e/**'],
    rules: { 'react-hooks/rules-of-hooks': 'off' },
  },
  {
    files: ['src/app/**'],
    rules: { 'no-restricted-imports': restrict(generatedTypes, otherApps, serverLayer) },
  },
  {
    // Everything in a feature but its queries, actions and mappers.
    files: ['src/features/**'],
    ignores: [
      'src/features/*/queries.ts',
      'src/features/*/actions.ts',
      'src/features/*/mappers.ts',
    ],
    rules: {
      'no-restricted-imports': restrict(generatedTypes, otherApps, serverLayer, otherFeatureCalls),
    },
  },
  {
    files: ['src/features/*/queries.ts', 'src/features/*/actions.ts'],
    rules: { 'no-restricted-imports': restrict(generatedTypes, otherApps, otherFeatureCalls) },
  },
  {
    files: ['src/features/*/mappers.ts'],
    rules: { 'no-restricted-imports': restrict(otherApps, serverLayer, otherFeatureCalls) },
  },
  {
    files: ['src/ui/**'],
    rules: { 'no-restricted-imports': restrict(generatedTypes, otherApps, serverLayer, features) },
  },
  {
    // The preview image is drawn by Satori, which reads inline styles and nothing else. Its
    // values are src/ui/tokens.ts's, never literals.
    files: ['src/features/*/preview.tsx'],
    rules: { 'react/forbid-dom-props': 'off' },
  },
]);
