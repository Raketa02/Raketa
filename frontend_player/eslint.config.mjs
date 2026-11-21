import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { FlatCompat } from '@eslint/eslintrc';

// eslint-config-expo only ships a flat config from v9, which belongs to SDK 53 —
// `npx expo install --check` pins this app to ~8.0.1, and dependency agreement with the
// SDK wins over config ergonomics. FlatCompat loads that eslintrc-style config into flat
// config unchanged, so the base rule set is Expo's own either way. Delete this bridge and
// go back to `eslint-config-expo/flat.js` at the SDK 53 upgrade.
const compat = new FlatCompat({
  baseDirectory: path.dirname(fileURLToPath(import.meta.url)),
});

const expoConfig = compat.extends('eslint-config-expo');

// ---------------------------------------------------------------------------
// Architectural boundaries from CLAUDE.md and docs/architecture.md, enforced by
// the linter. "Architecture that exists only in documentation will eventually be
// violated" — so every rule an agent could plausibly break lives here too.
//
// Restriction entries are composed rather than repeated: ESLint's flat config
// *replaces* a rule when a later block re-declares it, so a block that only
// wanted to add one ban would silently drop all the others.
// ---------------------------------------------------------------------------

/** The private layers of a feature. Only `types.ts` is a public surface. */
const FEATURE_LAYERS = [
  'domain',
  'use-cases',
  'api',
  'mappers',
  'schemas',
  'components',
  'hooks',
  'store',
];

/** `@/features/x/domain/**` and the relative form that climbs out of a feature. */
const deepFeatureImports = {
  group: FEATURE_LAYERS.flatMap((layer) => [
    `@/features/*/${layer}`,
    `@/features/*/${layer}/**`,
    `**/features/*/${layer}/**`,
    `../../*/${layer}/**`,
  ]),
  message:
    'Never deep-import another feature. Go through its types.ts public surface, or move the shared concept into src/shared/. Inside your own feature, import relatively (../domain/Match). See docs/architecture.md Part 1.',
};

const crossAppImports = {
  // The other apps are separate deployables; they communicate over HTTP only.
  group: ['../../backend/**', '../../frontend_club/**'],
  message:
    'frontend_player must never import from another app. Apps talk over HTTP only. See docs/adr/0005.',
};

const secureStoreImport = {
  group: ['expo-secure-store'],
  message:
    'Only src/shared/lib/auth may touch the keychain. One module owning it is what makes token lifetime auditable. See docs/adr/0008.',
};

const locationImport = {
  group: ['expo-location'],
  message:
    'Only src/shared/lib/platform may import expo-location. A native module cannot be ' +
    'driven from a test, so a feature that imports one is a feature that cannot be ' +
    'tested — and one file owning the capability is what keeps it foreground-only and ' +
    'readable in one sitting. Use the LocationPort from @/shared/lib/platform.',
};

const imagePickerImport = {
  group: ['expo-image-picker'],
  message:
    'Only src/shared/lib/platform may import expo-image-picker. Use the ImagePickingPort ' +
    'from @/shared/lib/platform, and fakeImagePicking() from src/test-support/platform.ts ' +
    'in a test — a native module has no JS implementation a test could drive.',
};

const liveStreamImport = {
  group: ['react-native-sse'],
  message:
    'Only src/shared/lib/platform/liveStream.ts may import react-native-sse. A transport ' +
    'cannot be driven from a test, so a screen that opened its own stream is a screen no ' +
    'suite can put in front of a severed one — and one file owning the app’s only ' +
    'long-lived connection is what keeps close-on-background and reconnect-with-a-fresh-token ' +
    'in one place. Use the LiveStreamPort from @/shared/lib/platform, and fakeLiveStream() ' +
    'from src/test-support/platform.ts in a test. See docs/adr/0147.',
};

const clipboardImport = {
  group: ['expo-clipboard'],
  message:
    'Only src/shared/lib/platform/clipboard.ts may import expo-clipboard. A native module cannot ' +
    'be driven from a test, and Join a group has to be walked with a link on the clipboard — use ' +
    'the ClipboardPort from @/shared/lib/platform, and fakeClipboard() from ' +
    'src/test-support/platform.ts in a test. See #512.',
};

const hapticsImport = {
  group: ['expo-haptics'],
  message:
    'Only src/shared/lib/platform/haptics.ts may import expo-haptics. A native module cannot be ' +
    'driven from a test, and *exactly one buzz, and none under reduced motion* is a rule a fake ' +
    'can count — use the HapticsPort from @/shared/lib/platform, and fakeHaptics() from ' +
    'src/test-support/platform.ts in a test. See docs/adr/0167 §2.',
};

const stripeImport = {
  group: ['@stripe/*'],
  message:
    'Only src/shared/lib/platform/payments.tsx may import the Stripe SDK. Its card fields and the ' +
    "bank's check are native and cannot be driven from a test, and a saved card is a walk a suite " +
    'has to finish — use the PaymentsPort from @/shared/lib/platform (its CardFields included), ' +
    'and fakePayments() from src/test-support/platform.ts in a test. See #552.',
};

const pushImport = {
  group: ['expo-notifications'],
  message:
    'Only src/shared/lib/platform/push.ts may import expo-notifications. The permission, the push ' +
    'token, a push arriving and a push tapped are native and cannot be driven from a test — use ' +
    'the PushPort from @/shared/lib/platform, and fakePush() from src/test-support/platform.ts in ' +
    'a test. See #559.',
};

const installReferrerImport = {
  group: ['expo-application'],
  message:
    'Only src/shared/lib/platform/installReferrer.ts may import expo-application. The install ' +
    'referrer is native and read once on first launch, and *once* is a rule only a fake can ' +
    'count — use the InstallReferrerPort from @/shared/lib/platform, and fakeInstallReferrer() ' +
    'from src/test-support/platform.ts in a test. See #756.',
};

const featurevisorImport = {
  group: ['@featurevisor/*'],
  message:
    'Only src/features/feature_flags/api/featurevisor.ts may import the Featurevisor SDK. A gate ' +
    'asks useFeatureOnMount from @/features/feature_flags/types; one module holding the SDK is ' +
    'what keeps its instance, its major and what a silent datafile means in one place — and ' +
    'the flags repo pins its CLI major to this one. See docs/adr/0206 §5, §10.',
};

const observabilityVendorImports = {
  group: ['@sentry/*', 'posthog-*', '@amplitude/*', 'mixpanel-*'],
  message:
    'Call observability and analytics vendors only through src/shared/lib/observability. Features depend on the interface, never the SDK — that is what keeps the vendor replaceable and consent/PII filtering central. See docs/architecture.md Part 15.',
};

const generatedImports = {
  // Generated wire types are raw transport. They may only be read inside a
  // feature's api/ or mappers/ layer.
  group: ['**/generated/*', '**/generated/**', '@/generated/*', '@/generated/**'],
  message:
    "Import generated wire types only inside a feature's api/ or mappers/ layer. Map them to your own DTO/domain objects first. See CLAUDE.md.",
};

const featureImportsFromShared = {
  group: ['@/features/**', '**/features/**'],
  message:
    'src/shared/ must never import a feature — that reverses the dependency arrow and couples every future feature to this one. See docs/architecture.md Part 1.',
};

const asyncStoragePath = {
  // Tokens belong in the OS keychain, not in JS-readable storage. The two exemptions are files,
  // not directories: one holds a public datafile, the other the choices a player made — see
  // their blocks below.
  name: '@react-native-async-storage/async-storage',
  message:
    'AsyncStorage is unencrypted: never store credentials in it — use expo-secure-store through src/shared/lib/auth (docs/adr/0008). Its only importers are src/features/feature_flags/api/datafileCache.ts, which keeps the public feature-flag datafile (docs/adr/0206 §6), and src/shared/lib/preferences/phonePreferences.ts, which keeps the per-account choices ADR-0188 lists (docs/adr/0188); a third need joins that allow-list by decision, not by import.',
};

/**
 * React Native's own share sheet — a **named** import from `react-native`, so it is a path entry
 * rather than a pattern: the rest of the module is every component the app draws, and only this
 * one name is fenced (#513).
 */
const shareImportPath = {
  name: 'react-native',
  importNames: ['Share'],
  message:
    'Only src/shared/lib/platform/share.ts may import Share from react-native. The sheet is ' +
    'native and a suite cannot open one, so a group page has to be walked with a sheet that ' +
    'records what it was handed — use the SharePort from @/shared/lib/platform, and fakeShare() ' +
    'from src/test-support/platform.ts in a test. See #513.',
};

/** Applies everywhere under src/, including api/ and mappers/. */
const CORE_PATTERNS = [
  crossAppImports,
  deepFeatureImports,
  secureStoreImport,
  locationImport,
  imagePickerImport,
  liveStreamImport,
  hapticsImport,
  clipboardImport,
  stripeImport,
  pushImport,
  installReferrerImport,
  featurevisorImport,
  observabilityVendorImports,
];

/** The two layers that stay pure TypeScript, as constants rather than as an inline literal. */
const PURE_PATTERNS = [
  ...CORE_PATTERNS,
  generatedImports,
  {
    group: ['expo', 'expo-*', 'react-native', 'react-native-*', '@tanstack/*'],
    message:
      'domain/ and use-cases/ must stay pure TypeScript — no React Native, Expo, or data-fetching library. That purity is what makes them testable without a renderer.',
  },
];

const PURE_PATHS = [
  asyncStoragePath,
  { name: 'react', message: 'domain/ and use-cases/ must stay pure TypeScript.' },
  { name: 'react-native', message: 'domain/ and use-cases/ must stay pure TypeScript.' },
  {
    name: 'zustand',
    message:
      'State lives in store/ or hooks/, not in a domain rule. domain/ is pure functions over plain data.',
  },
];

/**
 * The two path bans every block carries unless it is the one file exempt from one of them. The
 * pure layers carry `PURE_PATHS` instead, which bans `react-native` whole and so the share sheet
 * with it.
 */
const DEFAULT_PATHS = [asyncStoragePath, shareImportPath];

const restrict = (patterns, paths = DEFAULT_PATHS) => ['error', { patterns, paths }];

const literalHexColour = {
  selector: 'Literal[value=/^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/]',
  message:
    'No literal colour in a component. Every value comes from @/shared/ui/theme.ts, and colour is chosen by meaning (coral = the one accent, mint = settled, amber = reversible, red = ended badly). If the value genuinely does not exist, add it to theme.ts AND docs/design-system.md in the same commit.',
};

const literalFunctionalColour = {
  selector: 'Literal[value=/^(?:rgba?|hsla?)\\(/]',
  message:
    'No literal colour in a component — including rgba(). Use a token from @/shared/ui/theme.ts. Translucent values live in the theme too.',
};

const fontWeightProperty = {
  selector: "Property[key.name='fontWeight'], Property[key.value='fontWeight']",
  message:
    "fontWeight is IGNORED on Android when a custom fontFamily is set — this is how an RN app silently loses its typography on one platform. Weight is a family name: theme.font.sans[700], never fontWeight: '700'. See docs/design-system.md Part 3.",
};

/** The syntax bans that apply everywhere, composed for the same reason the imports are. */
const SYNTAX_BANS = [literalHexColour, literalFunctionalColour, fontWeightProperty];

/**
 * Every `Pressable` under `features/games/` and `features/proposals/` names itself, or says it is
 * hidden.
 *
 * `the-words.md` §20.12 books **two** gates over this contract, and this is the half a type
 * cannot give. Label coverage is already a compile error — §1's copy tables are `Record`s
 * keyed by the generated unions, so a code with no words does not build — but the historical
 * failure was an **omission**: §E6 opens by recording that the prototype has *"seven
 * `aria-label`s in the whole file, two of them in this feature. No `role`, no `aria-live`, no
 * `alt`, no `aria-selected`, no `aria-pressed`."* A missing prop is not a missing branch, and
 * no `Record` can see one.
 *
 * The escape is `accessibilityElementsHidden` / `importantForAccessibility`, which is a
 * decision written down rather than a control nobody labelled — the court's holding ring and
 * an already-announced toast are both legitimately silent. A spread also satisfies it: the
 * props are then the caller's, and this rule cannot see where they came from.
 *
 * **`Pressable` and nothing else, because every other pressable in this app already fails to
 * compile without a name.** `PressableCard`, `CloseControl` and the three photo tiles take
 * `accessibilityLabel: string` as a REQUIRED prop; `Switch` and `TickBox` take a required
 * `label` that *is* the accessible name; `Button` and `Chip` take a required `label` the name
 * falls back to. So for every primitive the coverage gate is the compiler, which is the half
 * §20.12 says a type does give. What a type cannot see is the one shape where the prop is
 * optional — a raw `Pressable` from `react-native` — and that is exactly what this covers.
 * Adding `Button` or `Chip` here would restate a required prop as a lint rule; adding a
 * primitive that did NOT require a name would be papering over the missing prop rather than
 * adding it. **The right response to a new tappable primitive is a required prop on it**, and
 * this entry stays one line wide.
 */
const unnamedPressable = [
  "JSXOpeningElement[name.name='Pressable']",
  ":not(:has(> JSXAttribute[name.name='accessibilityLabel']))",
  ':not(:has(> JSXSpreadAttribute))',
].join('');

const pressableNeedsAName = {
  // TWO selectors, because a hide is two props and half a hide is not one. iOS reads
  // `accessibilityElementsHidden` and Android reads `importantForAccessibility`, so a control
  // carrying one of them is hidden on one platform and an unnamed button on the other — which
  // is the bug this rule exists to catch, arriving through the rule's own escape hatch.
  selector: [
    `${unnamedPressable}:not(:has(> JSXAttribute[name.name='accessibilityElementsHidden']))`,
    `${unnamedPressable}:not(:has(> JSXAttribute[name.name='importantForAccessibility']))`,
  ].join(', '),
  message:
    "Every Pressable in features/games/ and features/proposals/ carries an accessibilityLabel, or hides itself explicitly with accessibilityElementsHidden AND importantForAccessibility — one of the two hides it on one platform only. The sentence is never written here: compose it from the-words.md §20 through that feature's own accessibility presentation. See the-words.md §20.12.",
};

/** Every ban that applies to a file under `src/shared/`, which is the strictest set. */
const SHARED_PATTERNS = [...CORE_PATTERNS, generatedImports, featureImportsFromShared];

/**
 * That set minus the one ban a sanctioned owner is exempt from.
 *
 * **A subtraction, never a re-listing.** The exception blocks below used to enumerate
 * their patterns by hand, which meant a ban added to `CORE_PATTERNS` reached every file
 * in the app *except* the four that had opted out of a different rule — so
 * `expo-location` was importable from `src/shared/lib/auth/` while three documents said
 * it was importable nowhere but the platform module. A miss like that is silent: the new
 * ban is real, it fires almost everywhere, and nothing about the config looks wrong.
 *
 * Written this way the next ban propagates on its own, and an exemption states the one
 * rule it is exempt from rather than the five it still obeys.
 */
const sharedPatternsExcept = (...exemptions) =>
  SHARED_PATTERNS.filter((pattern) => !exemptions.includes(pattern));

/** The same subtraction over a feature's wire layer, whose baseline is `CORE_PATTERNS`. */
const corePatternsExcept = (...exemptions) =>
  CORE_PATTERNS.filter((pattern) => !exemptions.includes(pattern));

export default [
  ...expoConfig,
  {
    ignores: ['node_modules/**', '.expo/**', 'android/**', 'ios/**', 'src/generated/**'],
  },

  // --- the baseline: everything, plus the wire-type ban -----------------------
  {
    rules: {
      'no-restricted-imports': restrict([...CORE_PATTERNS, generatedImports]),
      // fetch is configured in exactly one place, so that the timeout policy,
      // correlation IDs, error normalization and the single-flight 401 refresh
      // cannot be bypassed by a component doing its own request.
      'no-restricted-globals': [
        'error',
        {
          name: 'fetch',
          message:
            'Call the API through src/shared/lib/http — it owns the auth header, timeouts, cancellation, error normalization and the single-flight refresh. See docs/architecture.md Part 4.',
        },
      ],
      // The design system is locked (ADR-0012). A component never contains a
      // literal value. These three catch the ways that rule is actually broken —
      // deliberately narrow, so there are no false positives to teach an agent
      // that lint warnings are noise.
      'no-restricted-syntax': ['error', ...SYNTAX_BANS],
    },
  },

  // --- the wire boundary: exactly where generated types may be read -----------
  {
    files: ['src/features/*/api/**', 'src/features/*/mappers/**'],
    rules: { 'no-restricted-imports': restrict(CORE_PATTERNS) },
  },

  // --- domain/ and use-cases/ are pure: no React, no RN, no Expo, no wire -----
  {
    files: ['src/features/*/domain/**', 'src/features/*/use-cases/**'],
    rules: { 'no-restricted-imports': restrict(PURE_PATTERNS, PURE_PATHS) },
  },

  // --- shared/ is beneath every feature and may not reach back up -------------
  {
    files: ['src/shared/**'],
    rules: { 'no-restricted-imports': restrict(SHARED_PATTERNS) },
  },

  // --- the sanctioned exceptions ----------------------------------------------
  {
    // The single chokepoint for credentials (ADR-0008).
    files: ['src/shared/lib/auth/**'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(secureStoreImport)) },
  },
  {
    // The port that owns the device's position — and owns nothing else. The exemption is
    // one FILE, not the platform directory: a directory-wide one would let `appState.ts`
    // open the photo library, which is how a module of ports becomes the device bucket
    // this app bans. Everything above them depends on the interface, which is the only
    // reason a screen that reads a position can be exercised by a test at all.
    files: ['src/shared/lib/platform/location.ts'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(locationImport)) },
  },
  {
    // Likewise: the photo library, and not the position.
    files: ['src/shared/lib/platform/imagePicking.ts'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(imagePickerImport)) },
  },
  {
    // The live channel — and it is exempt from **two** bans, which no other file is.
    //
    // `react-native-sse` for the reason above: one file owns the transport. And
    // `src/generated/` because ADR-0147 §7 requires the client to read the live envelope as the
    // GENERATED type rather than as a hand-written mirror of it, and a stream body is not a
    // response model — so the operation's own `200` generates as `unknown` and the frame is
    // parsed against `LiveNudgeSchema` by name. The wire boundary's rule is that transport types
    // stay out of components, hooks and domain; the module that reads the socket is the api/
    // layer of this one route, and it has nowhere else to be, because a feature's api/ may not
    // import the transport.
    files: ['src/shared/lib/platform/liveStream.ts'],
    rules: {
      'no-restricted-imports': restrict(sharedPatternsExcept(liveStreamImport, generatedImports)),
    },
  },
  {
    // The motor — one verb, one file, the same one-file-wide exemption as the two native ports
    // above it.
    files: ['src/shared/lib/platform/haptics.ts'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(hapticsImport)) },
  },
  {
    // The clipboard — read and write, the same one-file-wide exemption as the motor (#512, #513).
    files: ['src/shared/lib/platform/clipboard.ts'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(clipboardImport)) },
  },
  {
    // The payment provider's phone half — Stripe's fields and the bank's check, one file wide like
    // the other native ports (#552).
    files: ['src/shared/lib/platform/payments.tsx'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(stripeImport)) },
  },
  {
    // The phone's push notifications — the permission, the token, a push arriving and one tapped,
    // one file wide like the other native ports (#559).
    files: ['src/shared/lib/platform/push.ts'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(pushImport)) },
  },
  {
    // The install referrer — one verb, one file, the same one-file-wide exemption as the other
    // native ports (#756).
    files: ['src/shared/lib/platform/installReferrer.ts'],
    rules: { 'no-restricted-imports': restrict(sharedPatternsExcept(installReferrerImport)) },
  },
  {
    // The share sheet — one verb, one file, the clipboard's exemption with the path ban
    // subtracted rather than a pattern: `Share` is one name out of `react-native` (#513).
    files: ['src/shared/lib/platform/share.ts'],
    rules: { 'no-restricted-imports': restrict(SHARED_PATTERNS, [asyncStoragePath]) },
  },
  {
    // The feature flags' saved datafile — one of the two modules that may import AsyncStorage
    // (ADR-0206 §6). The path ban is subtracted and nothing else: this file is a feature's api/
    // layer, so its baseline is `CORE_PATTERNS`, and every one of those still applies.
    files: ['src/features/feature_flags/api/datafileCache.ts'],
    rules: { 'no-restricted-imports': restrict(CORE_PATTERNS, [shareImportPath]) },
  },
  {
    // The phone-preferences store — the other module that may import AsyncStorage (ADR-0188
    // §1), one file wide for the datafile cache's reason. It sits under `shared/`, so its
    // baseline is `SHARED_PATTERNS`, and only the path ban is subtracted.
    files: ['src/shared/lib/preferences/phonePreferences.ts'],
    rules: { 'no-restricted-imports': restrict(SHARED_PATTERNS, [shareImportPath]) },
  },
  {
    // The one module that wraps the Featurevisor SDK (ADR-0206 §5) — one file wide, like the
    // native ports: the cache beside it may not evaluate a feature flag, and this may not read
    // storage.
    files: ['src/features/feature_flags/api/featurevisor.ts'],
    rules: { 'no-restricted-imports': restrict(corePatternsExcept(featurevisorImport)) },
  },
  {
    // The single place fetch is configured.
    files: ['src/shared/lib/http/**'],
    rules: { 'no-restricted-globals': 'off' },
  },
  {
    // The adapter that hides the observability vendor from everything else.
    files: ['src/shared/lib/observability/**'],
    rules: {
      'no-restricted-imports': restrict(sharedPatternsExcept(observabilityVendorImports)),
    },
  },

  {
    // The one file that is *supposed* to contain raw values: it is where the
    // design system's colours, weights and metrics are defined.
    files: ['src/shared/ui/theme.ts'],
    rules: { 'no-restricted-syntax': 'off' },
  },
  {
    // The native configuration document. Its `adaptiveIcon.backgroundColor` is an
    // Android manifest value baked into a launcher icon by `expo prebuild` — it is not
    // a design-system value and there is no token for it. It also *cannot* come from
    // the theme: this file is evaluated by Node before Metro exists, and importing
    // `theme.ts` would pull React Native into that process. The colour rule exists to
    // keep literals out of components, and this is not one; the block is kept separate
    // from theme.ts's above so the two exemptions are not read as one.
    //
    // This was `app.json` until the config became a function of the environment, and
    // ESLint does not lint JSON — so the rule is not being relaxed, it is meeting the
    // value for the first time.
    files: ['app.config.ts'],
    rules: { 'no-restricted-syntax': 'off' },
  },

  // --- tests may describe the wire, because that is what makes drift fail ------
  {
    // A test's fake responses are typed from the generated schema on purpose: a
    // backend shape change then fails `pnpm typecheck` instead of failing a test
    // run with a confusing assertion. This SERVES the wire-boundary rule rather
    // than defeating it — the rule exists to keep transport types out of
    // components, hooks and domain, and a fake response is doing exactly what an
    // api/ module does. The transport stub replaces `fetch` for the same reason:
    // it IS the socket under test, and it ships to no build.
    files: ['src/test-support/**', '**/*.test.ts', '**/*.test.tsx'],
    rules: {
      'no-restricted-imports': restrict(CORE_PATTERNS),
      'no-restricted-globals': 'off',
    },
  },

  {
    // Jest's setup file runs *inside* the test environment, where the runner injects
    // `jest` as a global. Nothing in the file's location tells ESLint that, and the
    // test-file block above is keyed on `*.test.*` — which a setup file deliberately is
    // not, because `testMatch` would then try to run it as a suite. The second file is
    // the configuration's too: what `jest.config.js` maps reanimated's mock to.
    //
    // `afterEach` for the one hook the setup file registers for every suite: emptying the
    // device storage a suite's walk left a player's choices, or a datafile, in (ADR-0188,
    // ADR-0206 §6).
    files: ['jest.setup.js', 'src/test-support/reanimatedActual.js'],
    languageOptions: { globals: { jest: 'readonly', afterEach: 'readonly' } },
  },

  // --- games and proposals: nothing tappable ships without a name -------------
  {
    // Scoped to the features that hold the contract, exactly as §20.12 scopes it, rather than
    // to `src/**` — which would make it a design-system rule, which is Part 13's job and a
    // different amendment. `features/games/` is built words-first: every sentence it says comes
    // off a copy deck, its labels are composed the same way, and its score grid is a surface made
    // of raw `Pressable`s — the one shape the compiler cannot see a missing name on.
    // `features/proposals/` holds the deck's three answers (#574), raw `Pressable`s named by the
    // deck's caller. The rule was written for the old loop's Play, which was its first feature
    // and left with that loop (#576).
    //
    // **Widening this list is not the answer to a new tappable primitive**; a required
    // `accessibilityLabel` prop on that primitive is. What belongs here is a feature that draws
    // raw `Pressable`s and owns a copy deck to name them from.
    //
    // `no-restricted-syntax` is re-declared rather than added to — flat config REPLACES a
    // rule when a later block names it — so the three baseline bans are spread back in. A
    // block that listed only the new one would switch off the colour and fontWeight rules
    // for these features, silently.
    files: ['src/features/games/**', 'src/features/proposals/**'],
    rules: { 'no-restricted-syntax': ['error', ...SYNTAX_BANS, pressableNeedsAName] },
  },

  // --- route files are adapters: feature public surfaces only -----------------
  {
    files: ['src/app/**'],
    rules: {
      'no-restricted-imports': restrict([...CORE_PATTERNS, generatedImports]),
    },
  },
];
