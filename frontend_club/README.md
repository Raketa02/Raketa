# Raketa for Clubs

The club website: a club signs up with its name, district, city, sports and a pin on the map,
signs in, keeps its details, and recovers its password. Administrators and official groups
arrive with [#523](https://github.com/Raketa02/Raketa/issues/523) and
[#524](https://github.com/Raketa02/Raketa/issues/524).

Next.js 16 with the App Router, talking to the backend's club surface from its own server. The
club's session is a sealed `httpOnly` cookie, and the browser never holds a token
([ADR-0187](../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)).

## Run it

```bash
pnpm install
cp .env.example .env.local     # then set SESSION_SECRET: openssl rand -hex 32
pnpm dev                       # http://localhost:3000, against the backend on :8000
```

The backend's dev stack must be running: `cd ../backend && make up`.
Its _Forgot password?_ emails land in the local mail catcher's inbox on
http://localhost:8025, and their links open this site's `/reset/<token>`.

## Check it

```bash
pnpm check     # lint, format, types, tokens, and the Playwright suite
```

The suite builds the site and runs it against a stub backend, so it needs neither the backend
nor a `.env.local`. The first run needs a browser: `pnpm exec playwright install chromium`.

How the app is put together, and why: [`docs/architecture.md`](docs/architecture.md).
