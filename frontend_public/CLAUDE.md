# Raketa — the public site

Next.js 16 (App Router) + React 19 + TypeScript, pnpm. The pages a link opens when the app isn't
installed: the group page (`/join/<code>`) and its preview, the invitation page
(`/invite/<token>`) and the reset page (`/reset/<token>`), and the app-link files
([ADR-0187](../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §4).
Every page is server-rendered, and the site talks to the backend's **public surface**
(`backend/openapi.public.json`) **from its server only**. It holds nothing: no session, no
cookie, no secret.

> One app of the monorepo — see the root [`CLAUDE.md`](../CLAUDE.md). Run every command from this
> directory. It imports nothing from another app, the club website included; a hook blocks
> writes outside it.

**Read [`docs/architecture.md`](docs/architecture.md) before adding a page, a form, a preview or
a call to the backend.** It is this app's standard, with the reason for each rule. The words this app
uses for its own machinery are in [`CONTEXT.md`](CONTEXT.md); domain words are the root
glossary's.

## The standard, in one screen

- **`src/app/`** holds routes: pages, the preview image's and the app-link files' route handlers,
  _Nothing at that link_ and _Something went wrong_.
- **`src/server/`** is the only code that reaches the backend or the configuration, and every file
  in it imports `server-only`. **One door, `fromBackend`**, because there is nobody to call as.
- **`src/features/<page>/`**: `queries.ts` reads, `actions.ts` writes, `mappers.ts` holds the
  view models and turns wire into them (**the only file outside `src/server/` and `e2e/` that
  imports a generated type**), `schemas.ts` checks what arrives (a form, or a code, token or
  mark in an address), `copy.ts` holds every sentence,
  `metadata.ts` builds the preview tags, `preview.tsx` draws the preview image, and `components/`
  are server components unless a page needs interaction. A feature may use another feature's
  components, schemas, copy and mappers, never its queries or actions.
- **Decisions branch on the backend's error `code`, never its message.** `group_not_found` and
  `credential_not_found` on a read are a dead link; any other failure is _Something went wrong_,
  never a dead link.
- **A code or token in an address is untrusted route input**: it is asked about, or put into a
  link this site draws, only once it is known to be letters, digits (and, for a token, `-` and
  `_`). A page binds its token to its action on the server, and the action checks it again.
- **Setting a password signs nobody in.** It lands back on the page marked `?password=set`, which
  reads the link again and says to sign in to the app.
- **Preview tags come from `generateMetadata`**, in `<head>`, for every user agent.
- **`src/ui/`** holds the design tokens (`tokens.css`, copied from the club website and the app)
  and the primitives, which take their words as props. **No literal colour or size appears
  anywhere else**, except `tokens.ts`, the preview image's copy, which the suite holds to the
  page, and the favicon.

ESLint enforces the import rules and `pnpm test:tokens` the token rule. Both name the rule they
enforce when they fail.

## Commands

```bash
pnpm dev          # next dev on :3001, the backend's default PUBLIC_SITE_URL, reading .env.local
pnpm check        # lint + format:check + typecheck + tokens + test: the local gate
pnpm exec playwright test e2e/<file>.spec.ts   # one spec while iterating
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.public.json
```

`pnpm test` builds first, and **`next build` type-checks `e2e/` too**: a type error in a spec
fails the web server, reported as _"Process from config.webServer was not able to start"_.

## Environment

**Copy `.env.example` → `.env.local` before `pnpm dev`.** Every variable is required and has no
default. `src/instrumentation.ts` validates them when the server starts and **exits** naming each
bad one. `APP_ENV` is one of the four names and only `local` runs today.

## The test seam

Playwright drives the built pages while `API_URL` points at **the stub backend** in `e2e/stub/`,
which answers with payloads typed from the generated contract and records every request. The
fixtures reset it before each test and install **the fake group directory** and **the fake
credentials** (`e2e/stub/groups.ts`, `e2e/stub/credentials.ts`): a test seats a group behind a
code with `groups.seat`, and a link behind a token with `credentials.invite` or
`credentials.reset` (`token(n)` makes one), and overrides an operation with `stub.on` only for a
test about one reply. One worker, because the one server
talks to the one stub.

- **The preview tags are read from the raw HTML**, never from the browser's DOM, which would have
  run JavaScript that a messenger never runs.
- **A picture the browser fetched is kept for its ten minutes**: a test that draws two images
  seats each group behind its own code.
- **Next's route announcer is a `role="alert"` too**, outside `<main>`: look for a form's alert
  with `page.getByRole('main').getByRole('alert')`.
- Reading `node_modules/`, `.next/`, `test-results/` and `playwright-report/` is denied here.
  Fetch a library's source or docs from GitHub, or `nextjs.org/docs`, at the pinned version.

## Safety — never without an explicit request

- Create or edit a real `.env*` file. Edit `.env.example`, and let a human copy it.
- Give a page a cookie, a session, a third-party script or analytics. The site holds nothing
  (ADR-0187 §4).
- Name a production domain or a store listing, or turn on a deployed environment. Both are
  deploy-time items (ADR-0187 §7).
