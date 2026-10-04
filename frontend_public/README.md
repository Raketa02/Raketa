# Raketa — the public site

The pages a link opens when the app isn't installed:

- **A group link**, `/join/<code>`, shows the group's tile, name, club and district, sports and
  size, with the App Store and Google Play, what to do once signed up, and **Open in Raketa**. Its
  preview tags let WhatsApp draw a card for the link.
- **An invitation link**, `/invite/<token>`, greets the new administrator for the club, shows the
  code to type into the app, and lets them set their password right there.
- **A reset link**, `/reset/<token>`, sets a new password for a player or an administrator.
- **The app-link files**, at `/.well-known/`, let those links open the app once a domain exists.

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
under `http://localhost:3001/join/`, so a link copied from the app opens here, and its invitation
and reset emails, in the local mail catcher's inbox on http://localhost:8025, link here too.

## Check it

```bash
pnpm check     # lint, format, types, tokens, and the Playwright suite
```

The suite builds the site and runs it against a stub backend, so it needs neither the backend
nor a `.env.local`. The first run needs a browser: `pnpm exec playwright install chromium`.

How the site is put together, and why: [`docs/architecture.md`](docs/architecture.md).
