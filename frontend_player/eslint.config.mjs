import path from "node:path";
import { fileURLToPath } from "node:url";

import { FlatCompat } from "@eslint/eslintrc";

// eslint-config-expo only ships a flat config from v9, which belongs to SDK 53 —
// `npx expo install --check` pins this app to ~8.0.1, and dependency agreement with the
// SDK wins over config ergonomics. FlatCompat loads that eslintrc-style config into flat
// config unchanged, so the base rule set is Expo's own either way. Delete this bridge and
// go back to `eslint-config-expo/flat.js` at the SDK 53 upgrade.
const compat = new FlatCompat({
  baseDirectory: path.dirname(fileURLToPath(import.meta.url)),
});

const expoConfig = compat.extends("eslint-config-expo");

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
  "domain",
  "use-cases",
  "api",
  "mappers",
  "schemas",
  "components",
  "hooks",
  "store",
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
    "Never deep-import another feature. Go through its types.ts public surface, or move the shared concept into src/shared/. Inside your own feature, import relatively (../domain/Match). See docs/architecture.md Part 1.",
};

const crossAppImports = {
  // The other apps are separate deployables; they communicate over HTTP only.
  group: ["../../backend/**", "../../frontend_club/**"],
  message:
    "frontend_player must never import from another app. Apps talk over HTTP only. See docs/adr/0005.",
};

const secureStoreImport = {
  group: ["expo-secure-store"],
  message:
    "Only src/shared/lib/auth may touch the keychain. One module owning it is what makes token lifetime auditable. See docs/adr/0008.",
};

const observabilityVendorImports = {
  group: ["@sentry/*", "posthog-*", "@amplitude/*", "mixpanel-*"],
  message:
    "Call observability and analytics vendors only through src/shared/lib/observability. Features depend on the interface, never the SDK — that is what keeps the vendor replaceable and consent/PII filtering central. See docs/architecture.md Part 15.",
};

const generatedImports = {
  // Generated wire types are raw transport. They may only be read inside a
  // feature's api/ or mappers/ layer.
  group: ["**/generated/*", "**/generated/**", "@/generated/*", "@/generated/**"],
  message:
    "Import generated wire types only inside a feature's api/ or mappers/ layer. Map them to your own DTO/domain objects first. See CLAUDE.md.",
};

const featureImportsFromShared = {
  group: ["@/features/**", "**/features/**"],
  message:
    "src/shared/ must never import a feature — that reverses the dependency arrow and couples every future feature to this one. See docs/architecture.md Part 1.",
};

const asyncStoragePath = {
  // Tokens belong in the OS keychain, not in JS-readable storage.
  name: "@react-native-async-storage/async-storage",
  message:
    "Never store credentials in AsyncStorage — it is unencrypted. Use expo-secure-store through src/shared/lib/auth. See docs/adr/0008.",
};

/** Applies everywhere under src/, including api/ and mappers/. */
const CORE_PATTERNS = [
  crossAppImports,
  deepFeatureImports,
  secureStoreImport,
  observabilityVendorImports,
];

const restrict = (patterns, paths = [asyncStoragePath]) => [
  "error",
  { patterns, paths },
];

export default [
  ...expoConfig,
  {
    ignores: ["node_modules/**", ".expo/**", "android/**", "ios/**", "src/generated/**"],
  },

  // --- the baseline: everything, plus the wire-type ban -----------------------
  {
    rules: {
      "no-restricted-imports": restrict([...CORE_PATTERNS, generatedImports]),
      // fetch is configured in exactly one place, so that the timeout policy,
      // correlation IDs, error normalization and the single-flight 401 refresh
      // cannot be bypassed by a component doing its own request.
      "no-restricted-globals": [
        "error",
        {
          name: "fetch",
          message:
            "Call the API through src/shared/lib/http — it owns the auth header, timeouts, cancellation, error normalization and the single-flight refresh. See docs/architecture.md Part 4.",
        },
      ],
      // The design system is locked (ADR-0012). A component never contains a
      // literal value. These three catch the ways that rule is actually broken —
      // deliberately narrow, so there are no false positives to teach an agent
      // that lint warnings are noise.
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "Literal[value=/^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/]",
          message:
            "No literal colour in a component. Every value comes from @/shared/ui/theme.ts, and colour is chosen by meaning (coral = the one accent, mint = settled, amber = reversible, red = ended badly). If the value genuinely does not exist, add it to theme.ts AND docs/design-system.md in the same commit.",
        },
        {
          selector: "Literal[value=/^(?:rgba?|hsla?)\\(/]",
          message:
            "No literal colour in a component — including rgba(). Use a token from @/shared/ui/theme.ts. Translucent values live in the theme too.",
        },
        {
          selector: "Property[key.name='fontWeight'], Property[key.value='fontWeight']",
          message:
            "fontWeight is IGNORED on Android when a custom fontFamily is set — this is how an RN app silently loses its typography on one platform. Weight is a family name: theme.font.sans[700], never fontWeight: '700'. See docs/design-system.md Part 3.",
        },
      ],
    },
  },

  // --- the wire boundary: exactly where generated types may be read -----------
  {
    files: ["src/features/*/api/**", "src/features/*/mappers/**"],
    rules: { "no-restricted-imports": restrict(CORE_PATTERNS) },
  },

  // --- domain/ and use-cases/ are pure: no React, no RN, no Expo, no wire -----
  {
    files: ["src/features/*/domain/**", "src/features/*/use-cases/**"],
    rules: {
      "no-restricted-imports": restrict(
        [
          ...CORE_PATTERNS,
          generatedImports,
          {
            group: ["expo", "expo-*", "react-native", "react-native-*", "@tanstack/*"],
            message:
              "domain/ and use-cases/ must stay pure TypeScript — no React Native, Expo, or data-fetching library. That purity is what makes them testable without a renderer.",
          },
        ],
        [
          asyncStoragePath,
          { name: "react", message: "domain/ and use-cases/ must stay pure TypeScript." },
          {
            name: "react-native",
            message: "domain/ and use-cases/ must stay pure TypeScript.",
          },
          {
            name: "zustand",
            message:
              "State lives in store/ or hooks/, not in a domain rule. domain/ is pure functions over plain data.",
          },
        ],
      ),
    },
  },

  // --- shared/ is beneath every feature and may not reach back up -------------
  {
    files: ["src/shared/**"],
    rules: {
      "no-restricted-imports": restrict([
        ...CORE_PATTERNS,
        generatedImports,
        featureImportsFromShared,
      ]),
    },
  },

  // --- the three sanctioned exceptions ----------------------------------------
  {
    // The single chokepoint for credentials (ADR-0008).
    files: ["src/shared/lib/auth/**"],
    rules: {
      "no-restricted-imports": restrict([
        crossAppImports,
        deepFeatureImports,
        observabilityVendorImports,
        generatedImports,
        featureImportsFromShared,
      ]),
    },
  },
  {
    // The single place fetch is configured.
    files: ["src/shared/lib/http/**"],
    rules: { "no-restricted-globals": "off" },
  },
  {
    // The adapter that hides the observability vendor from everything else.
    files: ["src/shared/lib/observability/**"],
    rules: {
      "no-restricted-imports": restrict([
        crossAppImports,
        deepFeatureImports,
        secureStoreImport,
        generatedImports,
        featureImportsFromShared,
      ]),
    },
  },

  {
    // The one file that is *supposed* to contain raw values: it is where the
    // design system's colours, weights and metrics are defined.
    files: ["src/shared/ui/theme.ts"],
    rules: { "no-restricted-syntax": "off" },
  },

  // --- route files are adapters: feature public surfaces only -----------------
  {
    files: ["src/app/**"],
    rules: {
      "no-restricted-imports": restrict([...CORE_PATTERNS, generatedImports]),
    },
  },
];
