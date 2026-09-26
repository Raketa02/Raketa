# Raketa — the public site

The pages a link opens when the app isn't installed. Today that is the group page: a group link,
`/join/<code>`, shows the group's tile, name, club and district, sports and size, with the App
Store and Google Play, what to do once signed up, and **Open in Raketa**. Its preview tags let
WhatsApp draw a card for the link. The invitation and password pages and the app-link files arrive
with [#526](https://github.com/Raketa02/Raketa/issues/526).

Next.js 16 with the App Router, every page server-rendered, talking to the backend's public
surface from its own server. It holds nothing: no sign-in, no session, no cookie
([ADR-0187](../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)).

## Run it

```bash
pnpm install
cp .env.example .env.local     # every value is filled in for local development
pnpm dev                       # http://localhost:3001, against the backend on :8000
```

The backend's dev stack must be running: `cd ../backend && make up`. Its group links are printed
under `http://localhost:3001/join/`, so a link copied from the app opens here.

## Check it

```bash
pnpm check     # lint, format, types, tokens, and the Playwright suite
```

The suite builds the site and runs it against a stub backend, so it needs neither the backend
nor a `.env.local`. The first run needs a browser: `pnpm exec playwright install chromium`.

How the site is put together, and why: [`docs/architecture.md`](docs/architecture.md).
