# `src/shared/` — cross-feature infrastructure

Generic, feature-agnostic building blocks. If something here starts to know about
courts, bookings or clubs, it belongs in a feature instead.

| Folder | Holds |
| --- | --- |
| `ui/` | Design-system primitives (button, card, input…). Owned code, no feature logic. |
| `lib/http/` | The typed fetch layer: a server-side FastAPI client and the browser-side BFF client. |
| `lib/auth/` | Session-cookie helpers used by the BFF and Server Components. |
| `lib/query-client/` | The TanStack Query client + defaults. |
| `config/` | `env.ts` — Zod-validated environment access. Nothing reads `process.env` directly. |
| `errors/` | `AppError` and the error normalization used across features. |
| `store/` | Zustand stores for **cross-cutting UI state only** (e.g. the active club). |

## Rules

- **Server data is never mirrored into a Zustand store.** TanStack Query owns server
  state; Zustand owns UI state. Mixing them is the bug that makes caches lie.
- `lib/http` is the only place `fetch` is configured. Features call it, never
  `fetch` directly.
- `config/env.ts` parses `process.env` through Zod once, at startup, and exports typed
  values. A missing variable should fail loudly at boot, not mysteriously at runtime.
