---
paths:
  - '**/*.test.ts'
  - '**/*.test.tsx'
  - 'src/**/__tests__/**'
---

# Testing — test first

Write the failing test, make it pass, refactor. Pyramid: many pure unit tests → component
tests → integration → a few E2E journeys.

- **Jest (`jest-expo`) + Testing Library React Native.** `domain/`, `use-cases/`, `mappers/`,
  schemas, formatters, key factories and the refresh coordinator are pure — test those first
  and hardest, with no renderer.
- Colocate as `*.test.ts(x)` next to the file under test — **except router tests, which live
  outside `src/app/`.** Cover redirects, the authenticated boundary, deep-link routes and
  params.
- Component tests assert what the user can observe, never internal state.
- Mock ports with hand-written stubs, not deep module mocks.
- **Auth concurrency is mandatory, not optional.** Ordinary login tests miss all four:
  many simultaneous 401s → exactly one refresh; refresh rejected → one logout with tokens and
  cache cleared; refresh times out → session survives; retried request 401s again → no
  infinite loop.
- Query integration: correct key, correct `enabled`, cache update and invalidation after a
  mutation, cache cleanup on logout.
- Snapshots are a narrow tool — large ones get updated without being read.
