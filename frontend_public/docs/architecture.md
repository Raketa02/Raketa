# The public site's standard

**Server-rendered pages that hold nothing**, as
[ADR-0187](../../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
§4 and §6 decided. It is this app's own. It has the club website's shape minus the session, and
it keeps a copy of whatever it borrows from there: nothing learned in either web app, or in the
player app, transfers by import. Each part below is a rule and the reason for it. A change that
needs to break one changes this page in the same pull request.

## 1. Where code lives

```
src/
  app/                 routes and layouts only
    join/[code]/       the group page (#525)
    preview/[code]/    the group page's preview image, a route handler
    not-found.tsx      Nothing at that link: every address here is reached by a link
    error.tsx          Something went wrong: the backend failed, which is not a dead link
  instrumentation.ts   refuses to start without the configuration (§5)
  server/              the only code that reaches the backend or the configuration; `server-only`
  features/<page>/     queries.ts · mappers.ts · copy.ts · metadata.ts · preview.tsx · components/
  ui/                  tokens.css, tokens.ts and the primitives
  generated/           openapi-typescript output; never edited by hand
e2e/                   the Playwright suite and its stub backend (§6)
```

- **Routes compose; they decide nothing.** A page reads through a feature's `queries.ts` and
  hands a view model to a feature's component. ESLint refuses `@/server/*` everywhere but
  `src/server/` itself and a feature's `queries.ts`, so the backend and the configuration are
  only ever reached through a query.
- **A feature is a page, or a part every page has**: `group-page` (the group, its preview tags and
  its preview image) and `get-the-app` (the two stores and **Open in Raketa**, which every page
  about a link offers, ADR-0187 §4). A dead link and the error page offer neither: there is
  nothing there for the app to open. #526's invitation and reset pages arrive as features of their own. A feature may use
  another feature's components, copy and mappers, never its queries (ESLint refuses them); a
  route calls each feature's queries itself.
- **`mappers.ts` is the only file outside `src/server/` that imports a generated type**, besides
  the suite's stub in `e2e/`, which types its replies from the contract on purpose. It turns a
  wire type into a view model. Sports are a `Record` over the wire's enum, and so are their names
  and their dots, so a fifth sport fails to compile until it has both; the tile's eight fills are
  a `Record` over its eight keys the same way.
- **`metadata.ts` builds a page's preview tags from its view model**, purely; `preview.tsx` draws
  its preview image. Both are §4's.
- **`src/ui/` knows nothing of any feature.** Primitives take words and values as props.
  `src/ui/copy.ts` holds the words that belong to no feature: the brand, the dead link and the
  error page.

## 2. Holding nothing

The public surface takes no session (ADR-0187 §4), so this site has **no sign-in, no session, no
cookie and no secret**. `src/server/backend.ts` has one door, `fromBackend(call)`, because there
is nobody to call as.

- **No response sets a cookie**, and the suite asserts it.
- **No page loads a script from anywhere but this site**, and the suite asserts that too. A
  link here can carry a code, and #526's a token; nothing may carry it off in analytics.
- **Every response sends `Referrer-Policy: no-referrer`** (`next.config.ts`), so nothing an
  address carries leaves in a `Referer`. The same headers keep every page out of somebody else's
  frame.

## 3. Calling the backend

Each call is `openapi-fetch` over the generated `paths`, with a ten-second timeout, and settles
into an **outcome**: `{ ok: true, data }` or `{ ok: false, error: { status, code } }`.
`code` is the backend's, or one of the site's own three: `backend_unreachable` (no answer),
`backend_failed` (an answer with no envelope) and `request_invalid` (any `422`, a bug here).
Failures that are nobody's doing are logged by code and trace id, never with a payload.

- **Decisions branch on `code`, never on `message`.** `group_not_found` is a dead link; every
  other failure throws, and the page says _Something went wrong_ with a 500. A backend that could
  not be reached never says _Nothing at that link_: that would send away somebody holding a live
  link.
- **A code or token in an address is untrusted route input** (ADR-0187 §7). A group code that is
  not letters and digits leads nowhere without asking the backend, and nothing else is ever put
  into a link this site draws, the preview's and **Open in Raketa**'s included.
- **A page and its preview tags read once.** `generateMetadata` and the page both ask; the query
  is wrapped in React's `cache`, so the backend hears one request per page view.

## 4. Pages, preview tags and the preview image

**Every page is server-rendered**, so a messenger, which runs no JavaScript, reads what a person
sees (ADR-0187 §4). The suite reads the raw HTML to prove it.

- **Preview tags come from `generateMetadata`**, per group: the title is the group's name, the
  description where it plays, its sports and its size, and the image its tile. Every address in
  them is absolute and made from `PUBLIC_SITE_URL`, the address people reach the site by.
- **They are in `<head>` for every user agent.** `htmlLimitedBots: /.*/` turns off Next's
  streaming of metadata, which would put the tags in the body for any messenger missing from
  Next's list of bots once a page flushes its shell early. Today no page has a loading boundary,
  so nothing streams either way; the setting keeps it so when one does.
- **A dead link answers 404** by `notFound()`, and has no preview: no card is drawn for a link
  that leads nowhere. Any other address says the same, because every page here is reached by a
  link.
- **The preview image is the group's tile, square** (`/preview/<code>`, outside `/join/`, which
  the app claims on a phone that has it). A messenger draws it beside the name, as the app draws
  the tile. `ImageResponse` (Satori) draws it from inline styles, which cannot read a custom
  property, so its values are `src/ui/tokens.ts`'s, a copy of `tokens.css`'s that the suite holds
  to the page pixel by pixel. Its face is Archivo Bold from `@fontsource/archivo`, Latin and Latin
  Extended, each subset a family of its own, because Satori keeps one font per name and weight
  and a Kraków group's tile may start with _Ł_. **A letter Archivo lacks is fetched when the
  image is drawn**: an emoji from next/og's emoji CDN (seen), and, by next/og's design, a letter
  from another script from Google Fonts (not seen here). Each is a server-side fetch that carries
  only those letters; without a network the letter is missing from the picture.
- **The image is cached for ten minutes, never for good.** A rename redraws the tile; next/og's
  default is `immutable` for a year.

## 5. Configuration

Six variables, all required, none with a default, none `NEXT_PUBLIC_*`: `APP_ENV`, `API_URL`,
`PUBLIC_SITE_URL`, `APP_STORE_URL`, `GOOGLE_PLAY_URL` and `APP_SCHEME` (`.env.example` says what
each is for). **Every address is a setting, never a literal** (ADR-0187 §7). `src/server/config.ts`
parses them purely and names every bad one and why, never its value, and a variable set to nothing
counts as missing.

**`src/instrumentation.ts` calls it before the server takes a request, and exits.** Next alone
would log a failed `register()` and go on serving 500s. `APP_ENV` selects defaults only: the
site's own address and both store links must be `https://` in every deployed environment.
`API_URL` is server-to-server and carries no scheme rule (`docs/environments.md`). `APP_SCHEME`
is the app's own scheme, without `://`, and a web or script scheme is refused, so **Open in
Raketa** can only ever open the app.

## 6. The test seam

**A real browser in front, a stand-in backend behind**, and nothing in between replaced
(ADR-0187 §6). `pnpm test` builds the site and starts it on port 3200 with a configuration made
for the suite, told it is reached at `https://raketa.test`. Each Playwright worker starts the
**stub backend** on port 4020, where `API_URL` points. The ports are not the club website's, so
the two suites can run side by side.

- The stub answers each operation with a handler whose reply the compiler checks against that
  operation's declared responses in the generated contract, plus the envelope-bearing statuses
  the backend sends without declaring per route (`422`, `5xx`), and `drop`, which closes the
  connection unanswered. It records every request. An operation is named by its path as the
  contract writes it, `/api/v1/public/groups/{code}`.
- **The fake group directory** installs the default handler: a test seats a group behind a code
  (`groups.seat(code, linkedGroup({…}))`), codes are read in any case, and a code nobody has, or a
  deleted group's, is `group_not_found`. A test about one reply overrides the operation with
  `stub.on`.
- **Tests assert what a person, a messenger or the backend would see**: text on the page, the
  status, the tags in the raw HTML's `<head>`, the pixels of the preview image, the headers, and
  the requests that arrived at the stub.
- **One worker**, because the one server talks to the one stub, which each test resets.
- **Start-up refusal is tested at the process**: `e2e/config.spec.ts` spawns `next start` with a
  bad configuration and reads its exit code and output.
- **Every page is checked at 360 px** for sideways scrolling.

No automated test crosses apps. The journey through the backend, the app and this site is a QA
plan walked by hand ([#528](https://github.com/Raketa02/Raketa/issues/528)).

## 7. Tokens and primitives

`src/ui/tokens.css` is the only file that writes a colour or a size, besides `src/ui/tokens.ts`
(§4) and the favicon, `src/app/icon.svg`, which the browser draws on its own and which can read
no custom property. There are no mocks for this site: it **borrows the club website's look** (paper, the coral
square wordmark, a white card) **by copying its values**, and draws a group as the app does, with
the sport dots sampled from play 38 and the tile's eight fills copied from the app's
`MONOGRAM_HUES`. A change to either original does not reach this copy; divergence is caught by
eye (ADR-0187, _Consequences_). The type is Archivo, self-hosted from `@fontsource/archivo`, so
a build fetches no font from the network. `pnpm test:tokens` fails on a literal anywhere else,
and ESLint refuses an inline `style` everywhere but the preview image. A media query's width is
the one literal CSS allows no variable for.

**Laid out for phones first**: one white card, the full width less a gutter, that stops growing
at a narrow column on anything wider. Every button leaves the site (for a store, or for the app),
so it is a plain `<a>`. The stores' buttons are filled with ink, as their own badges are, and
**Open in Raketa** is outlined: the coral square is the page's one coral mark.
