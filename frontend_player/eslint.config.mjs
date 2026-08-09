import expoConfig from "eslint-config-expo/flat.js";

export default [
  ...expoConfig,
  {
    ignores: ["node_modules/**", ".expo/**", "android/**", "ios/**", "src/generated/**"],
  },
  {
    rules: {
      // Architectural boundaries from CLAUDE.md, enforced by the linter.
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              // Generated wire types are raw transport. They may only be read
              // inside a feature's api/ or mappers/ layer.
              group: ["**/generated/*", "@/generated/*"],
              message:
                "Import generated wire types only inside a feature's api/ or mappers/ layer. Map them to your own DTO/domain objects first. See CLAUDE.md.",
            },
            {
              // The other apps are separate deployables; they communicate over
              // HTTP only. See docs/adr/0005.
              group: ["../../backend/**", "../../frontend_club/**"],
              message:
                "frontend_player must never import from another app. Apps talk over HTTP only. See docs/adr/0005.",
            },
          ],
          paths: [
            {
              // Tokens belong in the OS keychain, not in JS-readable storage.
              name: "@react-native-async-storage/async-storage",
              message:
                "Never store credentials in AsyncStorage — it is unencrypted. Use expo-secure-store. See docs/adr/0008.",
            },
          ],
        },
      ],
    },
  },
  {
    // The wire boundary: exactly where generated types may be read.
    files: ["src/features/*/api/**", "src/features/*/mappers/**"],
    rules: { "no-restricted-imports": "off" },
  },
  {
    // domain/ and use-cases/ are pure: no React, no React Native, no fetch.
    files: ["src/features/*/domain/**", "src/features/*/use-cases/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          paths: [
            { name: "react", message: "domain/ and use-cases/ must stay pure TypeScript." },
            { name: "react-native", message: "domain/ and use-cases/ must stay pure TypeScript." },
          ],
          patterns: [
            {
              group: ["expo*", "**/generated/*", "@/generated/*"],
              message:
                "domain/ and use-cases/ must stay pure TypeScript — no React Native, Expo, or wire types.",
            },
          ],
        },
      ],
    },
  },
];
