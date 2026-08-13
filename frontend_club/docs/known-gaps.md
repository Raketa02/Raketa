# Known gaps — club web app

Real and outstanding. **Do not assume the guardrails below already hold.** Referenced from
[`../CLAUDE.md`](../CLAUDE.md); keep it short and delete entries as they close.

## 1. ESLint still enforces the old layer set

`eslint.config.mjs` exempts `api/` and `mappers/` for generated imports and treats
`domain/`/`use-cases/` as pure. **Those folders no longer exist**
([ADR-0014](../../docs/adr/0014-club-console-production-architecture-standard.md)).

Until it is rewritten, **the import boundaries in `CLAUDE.md` are documentation, not
enforcement.** It needs:

- `server/` and the transport adapters exempted for generated imports instead
- a `server-only` boundary rule
- a deep-import ban on `features/*/{api,model,schemas,state,ui,server}`
- a rule keeping generated `paths` out of `ui/`

*(§34)*

## 2. `tsconfig.json` is missing two strict flags

`strict`, `noUncheckedIndexedAccess`, `noImplicitOverride` and `noFallthroughCasesInSwitch`
are on. §17.1 also wants `exactOptionalPropertyTypes` and `useUnknownInCatchVariables`.

## 3. §48 tooling is absent from `package.json`

No Prettier config in lint, no TanStack Query ESLint plugin, no axe, no OpenTelemetry, no
bundle budget, no OpenAPI breaking-change tool. Next and React are floating `^` ranges —
§33.1 wants exact patched pins, and §33.2 makes that a security requirement, not a
preference.

## 4. Refresh concurrency is unsettled with the backend

See the `auth` rule in `.claude/rules/auth.md`. The mechanism must be agreed with the
backend before auth is built.

---

*Closed: the ADR for adopting the production standard, and the stale "two clients share a
shape" claim in the root `CLAUDE.md` and `CONTEXT-MAP.md` — both resolved by ADR-0014.*
