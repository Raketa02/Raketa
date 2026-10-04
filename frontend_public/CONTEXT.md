# Public site — technical vocabulary

The words this app uses for its own machinery. **Domain words are the root
[`CONTEXT.md`](../CONTEXT.md)'s** (Group, Group link, Group member, Club, Sport, Invitation…) and
are never redefined here. Where a word below meets a domain word, it points back.

- **Server layer** — `src/server/`: the only code that opens a connection to the backend or reads
  the configuration, every file marked `server-only`. It holds the configuration, the typed client
  and its one door, `fromBackend`.
- **Public surface** — the backend's API for this app alone, `backend/openapi.public.json`
  (ADR-0187 §5). It takes no session and discloses the least a page needs: never who is in a
  Group.
- **Wire type** — a type generated from the public surface into `src/generated/schema.d.ts` by
  `pnpm gen:api`. Read only by the server layer and a feature's `mappers.ts`.
- **View model** — what a page draws, made from a wire type by a mapper: a `LinkedGroup`, the
  Group a link opens, with its tile's fill already picked. Pages never see a wire type.
- **Dead link** — an address that leads nowhere: a Group link whose code no Group has, could be
  nobody's, or whose Group was deleted (`group_not_found`); an invitation or reset link never sent
  (`credential_not_found`); and any other address on this site. Answered 404 with _Nothing at that
  link_. Never said of a backend that failed, nor of a link that has expired, been used or locked.
- **Link state** — whether an **Invitation**'s or a password reset's link can still set a
  password: `valid`, `expired`, `used` or `locked` (five wrong codes were typed for it; ADR-0184
  §3). The page reads it without changing it, and says each in a sentence of its own.
- **Setting by link** — choosing a password on the invitation or reset page, by the link's token:
  the same rules and results as the app's, but **nobody is signed in**, so the page then says to
  sign in to the app. It lands back on the page marked `?password=set`. _Avoid_: sign-up,
  activation.
- **Untrusted route input** — a code or token read from a page's address. Checked before it is
  asked about or put into any link the site draws (ADR-0187 §7).
- **Preview tags** — a page's title, description and image as `<meta>` in the `<head>` the server
  sends (`og:*`, `twitter:card`), built by a feature's `metadata.ts` through `generateMetadata`.
  What a messenger draws a card from. _Avoid_: SEO tags, unfurl.
- **Preview image** — the picture the preview tags name: a Group's tile, square, drawn by
  `ImageResponse` at `/preview/<code>`.
- **Tile** — a Group's **monogram** (root `CONTEXT.md`, _Group_) as drawn: its letters on the fill
  its colour key picks from eight.
- **The way in** — the `get-the-app` feature: the App Store and Google Play buttons, a line saying
  what to do once installed, and **Open in Raketa**. On every page a live link opens; a dead
  link has nothing to open.
- **Open in Raketa** — a link to `<APP_SCHEME>://<route>`, the app at the route the page is about
  (`join/<code>`), for a phone that has the app but where the link didn't open it (ADR-0187 §4).
  _Avoid_: deep link (the web-domain links that open the app are the app-link files').
- **App-link files** — Apple's association file and Android's asset links, at their well-known
  paths, made from settings: what lets a tapped `/join/`, `/invite/` or `/reset/` link open the app
  once a domain exists. _Avoid_: AASA, deep-link config.
- **Token** (design) — a CSS custom property in `src/ui/tokens.css`, or its copy in
  `src/ui/tokens.ts` for the preview image. The only places a colour or a size is written.
- **Stub backend** — `e2e/stub/backend.ts`: an HTTP server standing in for the public surface in
  the Playwright suite, typed from the wire types, recording every request.
- **Fake group directory** — `e2e/stub/groups.ts`: the stub's default answer to _the group a link
  opens_, keeping the backend's rules, so a test seats only the groups it is about.
- **Fake credentials** — `e2e/stub/credentials.ts`: the stub's default answers to the invitation
  and reset links, keeping the backend's rules (a set spends its link), so a test seats only the
  links it is about.
