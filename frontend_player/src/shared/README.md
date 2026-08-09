# `src/shared/` — cross-feature infrastructure

Generic, feature-agnostic building blocks. If something here starts to know about
courts, bookings or matches, it belongs in a feature instead.

| Folder | Holds |
| --- | --- |
| `ui/` | Design-system primitives (button, card, text…). Owned code, no feature logic. |
| `lib/http/` | The typed fetch layer: base URL, `Authorization` header, 401 → refresh → retry. |
| `lib/auth/` | **The only module that touches `expo-secure-store`.** Token read/write/clear. |
| `lib/query-client/` | The TanStack Query client + defaults. |
| `config/` | `env.ts` — Zod-validated config read from `expo-constants`. |
| `errors/` | `AppError` and the error normalization used across features. |
| `store/` | Zustand stores for **cross-cutting UI state only**. |

## Rules

- **`lib/auth/` is the single chokepoint for credentials.** No feature, screen or hook
  imports `expo-secure-store`. One module owning the keychain is what makes the token
  lifetime auditable.
- **Never `AsyncStorage` for tokens** — it is unencrypted plaintext on device. ESLint
  blocks the import.
- **Anything in the shipped bundle is public.** `app.json` `extra` and any `EXPO_PUBLIC_*`
  variable can be read out of the binary. Config, never secrets.
- **Server data is never mirrored into a Zustand store.** TanStack Query owns server
  state; Zustand owns UI state.
- `lib/http` is the only place `fetch` is configured, and the only place the refresh
  rotation is implemented — so a 401 storm can't fan out into N concurrent refreshes.
