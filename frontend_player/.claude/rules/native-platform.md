---
paths:
  - 'app.json'
  - 'app.config.*'
  - 'src/shared/lib/platform/**'
  - 'eas.json'
  - 'package.json'
---

# Native, Expo and release mechanics

- **New Architecture stays on.** A dependency that blocks it is technical debt with a
  migration plan, not an exemption. Check any new native dependency for SDK 52 + New
  Architecture compatibility, and run `pnpm doctor`.
- **`android/` and `ios/` are `expo prebuild` output** and are not committed. Native config
  goes through `app.json` and config plugins; a hand edit is lost on the next prebuild.
- **Concentrate platform differences behind adapters** (`share.ios.ts` / `share.android.ts`
  in `shared/lib/platform`), not `if (Platform.OS === 'ios')` scattered through features.
- **OTA respects native compatibility.** A JS-only change → EAS Update; a native dependency
  or config change → a new build. Never ship JS expecting native code the installed binary
  lacks.
- **Nothing in the bundle is secret.** `app.json` `extra` and every `EXPO_PUBLIC_*` variable
  are readable from a shipped app — they are config. A secret a mobile client "needs" is a
  design error; it belongs behind the backend.
- **Expo pins its own packages tightly.** After changing dependencies run
  `npx expo install --check` and trust Expo's resolution over the pins in `package.json`.
- **Keep the JS thread free.** No big synchronous parses, heavy array work in render, or
  synchronous secure-storage calls. Profile before optimizing — `memo` everywhere is
  complexity without evidence. Virtualize long lists; don't fetch full-resolution images for
  a card.

Builds and submissions (`eas build`, `eas submit`, `eas update`, `expo publish`) require an
explicit human request and are blocked by a hook.
