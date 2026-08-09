import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({ baseDirectory: __dirname });

export default [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/**", "node_modules/**", "src/generated/**"],
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
              group: ["../../backend/**", "../../frontend_player/**"],
              message:
                "frontend_club must never import from another app. Apps talk over HTTP only. See docs/adr/0005.",
            },
          ],
        },
      ],
    },
  },
  {
    // The wire boundary: these two layers are exactly where generated types
    // are allowed to be read.
    files: ["src/features/*/api/**", "src/features/*/mappers/**"],
    rules: { "no-restricted-imports": "off" },
  },
  {
    // domain/ and use-cases/ are pure: no React, no Next, no fetch.
    files: ["src/features/*/domain/**", "src/features/*/use-cases/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          paths: [
            { name: "react", message: "domain/ and use-cases/ must stay pure TypeScript." },
            { name: "next", message: "domain/ and use-cases/ must stay pure TypeScript." },
          ],
          patterns: [
            {
              group: ["next/*", "react-dom", "**/generated/*", "@/generated/*"],
              message: "domain/ and use-cases/ must stay pure TypeScript — no React, Next, or wire types.",
            },
          ],
        },
      ],
    },
  },
];
