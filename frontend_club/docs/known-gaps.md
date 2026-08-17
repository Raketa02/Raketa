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

> Partly closed: the config boundary **is** enforced. `no-restricted-syntax` keeps
> `process.env` inside `src/platform/config/` and bans `NODE_ENV` everywhere, and
> `src/platform/config/server.ts` carries `import "server-only"` so a client import of the
> FastAPI origin is a build error. The four bullets above are still open — a `server-only`
> *lint* rule would catch the same mistake one step earlier, and would cover the modules
> that have no `server-only` import of their own yet.

## 1a. The club app ships untested in CI

It has no committed `pnpm-lock.yaml`, so [`ci.yml`](../../.github/workflows/ci.yml) skips
its whole job — see [#65](https://github.com/RobertConstantin02/rakieta/issues/65). Tests
under `src/platform/config/` exist and pass locally (`pnpm check`), but **nothing runs them
on a pull request**. They light up the moment the lockfile lands; until then, treat a green
CI on a `frontend_club/**` change as saying nothing at all.

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
