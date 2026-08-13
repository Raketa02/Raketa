---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "e2e/**"
  - "src/features/*/test/**"
  - "src/shared/test/**"
---

# Testing *(§29)*

Confidence at the cheapest reliable layer — not the maximum number of tests.

| Layer | Covers |
| --- | --- |
| Static | TypeScript, lint/import boundaries, generated-contract drift |
| **Vitest unit** | Zod schemas, money/date rules, search-param parsing, **query-key factories**, error normalization, state transitions, DTO→UI mapping, idempotency helpers |
| Component | user-observable behavior: validation, loading/error/success, keyboard, permission-dependent UI, dialogs, filters |
| **BFF integration** | unauthenticated rejected · wrong tenant rejected · invalid input rejected before the backend call · Authorization built server-side · browser cookies not forwarded · refresh success **and** failure · cookie flags · timeout mapping · conflict mapping · request-ID propagation · bad-Origin rejection · **no backend internals leaked** |
| Contract | OpenAPI validity, generated-type drift, breaking-change detection |
| **Playwright** | login/logout · session expiry and refresh · club switching and tenant isolation · role boundaries · booking create/edit/cancel · concurrent-change conflict · deep-link filters · double-submit · security-sensitive actions |

**Security assertions are tests, not prose:** cookies are HttpOnly/Secure/SameSite · tenant A
cannot read tenant B · mutations reject disallowed origins · redirect targets cannot leave
the allowlist · token strings never appear in rendered HTML or client storage · generic BFF
URL forwarding is impossible. *(§30)*

Playwright: isolated tests, each owning its data · `getByRole`/label/text before CSS/XPath ·
**no arbitrary sleeps** · web-first assertions · traces on CI failure. **Flaky tests are
defects**, quarantined only with an owner and a deadline. Coverage is a signal, not a goal.

Colocate unit/component tests as `*.test.ts(x)` beside the file, or in the feature's
`test/`. E2E specs live in `e2e/`.
