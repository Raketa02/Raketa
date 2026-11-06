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
    f/[code]/          the friend link's page (#755)
    face/[code]/       its owner's face, the page's picture and its preview image, a route handler
    invite/[token]/    the invitation page (#526)
    reset/[token]/     the reset page, for players and administrators (#526)
    .well-known/       the app-link files, route handlers (#526)
    not-found.tsx      Nothing at that link: every address here is reached by a link
    error.tsx          Something went wrong: the backend failed, which is not a dead link
  instrumentation.ts   refuses to start without the configuration (§6)
  server/              the only code that reaches the backend, the photographs it signs links to,
                       or the configuration; `server-only`
  features/<page>/     queries.ts · actions.ts · mappers.ts · schemas.ts · copy.ts · metadata.ts ·
                       preview.tsx · components/
  ui/                  tokens.css, tokens.ts and the primitives
  generated/           openapi-typescript output; never edited by hand
e2e/                   the Playwright suite and its stub backend (§7)
```

- **Routes compose; they decide nothing.** A page reads through a feature's `queries.ts`, binds
  a feature's action to what it read, and hands both to a feature's component. ESLint refuses
  `@/server/*` everywhere but `src/server/` itself and a feature's `queries.ts` and `actions.ts`,
  so the backend and the configuration are only ever reached through a query or an action.
- **A feature is a page, or a part several pages have**:
  - `group-page`: the group, its preview tags and its preview image, and what a code could be
    (`schemas.ts`), which a friend link's code is shaped like;
  - `friend-link`: whose a friend link is, its preview tags, and their face;
  - `invitation` and `password-reset`: reading a link, and what each page says in each state;
  - `set-password`: what both of those pages share: a link's state, the form, its checks and its
    actions;
  - `get-the-app`: the two stores and **Open in Raketa**, which every page about a link offers
    (ADR-0187 §4). A dead link and the error page offer neither: there is nothing there for the
    app to open. It also holds `APP_ROUTES`, the routes the app and this site both answer
    (`join`, `f`, `invite`, `reset`), written once for every link, redirect and claim;
  - `app-link-files`: Apple's association file and Android's asset links.

  A feature may use another feature's components, schemas, copy and mappers, never its queries
  or actions (ESLint refuses them); a route calls those itself.

- **`mappers.ts` holds a feature's view models, and is the only file outside `src/server/` that
  imports a generated type**, besides the suite's stub in `e2e/`, which types its replies from the
  contract on purpose. It turns a wire type into a view model. Sports and a link's states are a
  `Record` over the wire's enum, so a fifth fails to compile until it is mapped; a sport's name
  and dot are a `Record` over the site's sports too, so a new one fails until it has both, and the
  tile's eight fills are a `Record` over its keys.
- **`schemas.ts` checks what arrives from outside** before anything is done with it: a form's
  boxes, and a code, a token or a mark in an address.
- **`metadata.ts` builds a page's preview tags from its view model**, purely; `preview.tsx` draws
  its preview image. Both are §4's.
- **`src/ui/` knows nothing of any feature.** Primitives take words and values as props.
  `src/ui/copy.ts` holds the words that belong to no feature: the brand, the dead link, the error
  page and the refusals every form can meet.

## 2. Holding nothing

The public surface takes no session (ADR-0187 §4), so this site has **no sign-in, no session, no
cookie and no secret**. `src/server/backend.ts` has one door, `fromBackend(call)`, because there
is nobody to call as. Setting a password signs nobody in, here or anywhere.

- **No response sets a cookie**, setting a password included, and the suite asserts it.
- **The browser asks nothing of any other site**: no script, no font, no picture. A link here can
  carry a code or a token, and nothing may carry it off in analytics. The suite watches every
  request an invitation page makes, through setting the password, and a friend link's page.
- **A friend link owner's face is fetched by this server, never by the browser.** The backend
  answers it as a link into its photo storage, signed for minutes (#748); `src/server/photos.ts`
  fetches it, `no-store`, so Next's data cache writes nothing to disk, and the site serves the
  picture as its own (`/face/<code>`). The page never carries the signed link.
- **Every response sends `Referrer-Policy: no-referrer`** (`next.config.ts`), so nothing an
  address carries leaves in a `Referer`. The same headers keep every page out of somebody else's
  frame.
- **A credential's page asks never to be listed**: the invitation and reset pages send `robots`
  `noindex, nofollow`.

## 3. Calling the backend

Each call is `openapi-fetch` over the generated `paths`, with a ten-second timeout, and settles
into an **outcome**: `{ ok: true, data }` or `{ ok: false, error: { status, code, field? } }`.
`code` is the backend's, or one of the site's own three: `backend_unreachable` (no answer),
`backend_failed` (an answer with no envelope) and `request_invalid` (any `422`, a bug here).
Failures that are nobody's doing are logged by code and trace id, never with a payload.

- **Decisions branch on `code`, never on `message`.** `group_not_found`, `friend_link_not_found` and
  `credential_not_found` on a read are a dead link; every other failed read throws, and the page
  says _Something went wrong_ with a 500. A backend that could not be reached never says _Nothing at
  that link_: that would send away somebody holding a live link.
- **A code or token in an address is untrusted route input** (ADR-0187 §7). A group's or a friend
  link's code that is not letters and digits, or a token that is not the URL-safe letters the
  backend mints, leads nowhere without asking the backend, and nothing else is ever put into a link
  this site draws, the preview's and **Open in Raketa**'s included.
- **A token travels in a body**, as the contract has it, so it is in no backend access log. It is
  in this site's own, since it is in the page's address.
- **A page and its preview tags read once.** `generateMetadata` and the page both ask; the query
  is wrapped in React's `cache`, so the backend hears one request per page view.

## 4. Pages, preview tags and the preview image

**Every page is server-rendered**, so a messenger, which runs no JavaScript, reads what a person
sees (ADR-0187 §4). The suite reads the raw HTML to prove it.

- **Preview tags come from `generateMetadata`**, per group: the title is the group's name, the
  description where it plays, its sports and its size, and the image its tile. Every address in
  them is absolute and made from `PUBLIC_SITE_URL`, the address people reach the site by. The
  invitation and reset pages have a title and no preview: a credential's page describes nobody.
- **A friend link's preview** is _Tomek invited you to play on Raketa_, whole, without the site's
  name after it, over _Tomek wants to be your friend_, beside his face. Somebody with no photograph
  has no picture, on the page or in the preview: the app's stand-in, a poster, is drawn from an id
  the public read withholds, and a face carries no initials (ADR-0167 §3). The page asks never to
  be listed (`noindex, nofollow`): it names somebody and shows their face by a link they can turn
  off.
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
- **A friend link owner's face is their photograph, square, 300 px** (`/face/<code>`, outside
  `/f/`), cut to fill it from the middle, since the backend keeps a photograph's own shape. It is
  smaller than the tile because a photograph does not shrink as a PNG the way two letters on one
  fill do. **It is read afresh for every picture**: its own request reads the link again and fetches
  the photograph by the link that read signed, because a signed link expires within minutes. Cached
  ten minutes, as the tile, but `private`: no cache in between keeps a person's face, so a New link
  ends it for everybody but whoever already fetched it.

## 5. Setting a password by a link

The invitation page and the reset page each read their link (`by-token`, which changes nothing)
and draw what it is: **valid**, **expired**, **used** or **locked**, each with its own sentence,
worded as the app words it. While it is valid the page offers the form.

- **A server action checks what it can, then asks the backend, then answers with codes.** The
  password rule (8 to 128 characters, a letter and a digit) and the repeat are checked here, with
  the backend's code where it has one (`password_too_weak`), so a form the site refuses never
  reaches the backend, and one sentence serves a refusal from either side.
- **The token is the one the page was opened with**, bound to the action on the server and checked
  again inside it, because a bound argument comes back from the browser.
- **A refusal goes under the box it names, or over the form**: `sign_in_to_accept` (the email has
  an account now, which accepts in the app), an unreachable backend. The boxes are controlled, so
  a refusal keeps what was typed, and a box's refusal goes as soon as that box changes.
- **A link spent while the page was open redraws the page**, which then says what the link is now.
- **A set lands back on the page, marked `?password=set`.** The page reads the link again, finds
  it used, and says what to do next: sign in to the app. The mark only chooses between two
  sentences for a used link; on a link that still works it changes nothing.
- **The form needs JavaScript.** Under `Referrer-Policy: no-referrer` a browser posts a plain form
  with `Origin: null`, which Next refuses as a cross-site action. A browser without it is told so
  in a `<noscript>`, and everything else on these pages reads without it.
- **Raketa is named only where ADR-0187 names it**: _after you install, open Raketa and enter this
  code_ (§4) and _Open Raketa and sign in with your email and password_ (§8). Everywhere else
  these pages say _the app_, as the copy rule has it.
- **Open in Raketa** opens the app at `invite/<token>` or `reset/<token>` while the link works
  (#520), and at the app's start once it can't, where the person signs in.

## 6. Configuration

Ten variables, all required, none with a default, none `NEXT_PUBLIC_*` (`.env.example` says what
each is for):

- `APP_ENV`, one of the four names;
- `API_URL`, `PUBLIC_SITE_URL`, `APP_STORE_URL` and `GOOGLE_PLAY_URL`;
- `APP_SCHEME`, the app's own scheme;
- `APPLE_TEAM_ID`, `IOS_BUNDLE_ID`, `ANDROID_PACKAGE` and `ANDROID_CERT_FINGERPRINTS`, which the
  app-link files name.

**Every address and identifier is a setting, never a literal** (ADR-0187 §7).
`src/server/config.ts` parses them purely and names every bad one and why, never its value, and a
variable set to nothing counts as missing.

**`src/instrumentation.ts` calls it before the server takes a request, and exits.** Next alone
would log a failed `register()` and go on serving 500s. `APP_ENV` selects defaults only: the
site's own address and both store links must be `https://` in every deployed environment.
`API_URL` is server-to-server and carries no scheme rule (`docs/environments.md`). `APP_SCHEME`
is the app's own scheme, without `://`, and a web or script scheme is refused, so **Open in
Raketa** can only ever open the app.

**The app-link files** (`/.well-known/apple-app-site-association` and
`/.well-known/assetlinks.json`) are made per request from those settings, as JSON with no redirect.
Apple's claims `/join/*`, `/f/*`, `/invite/*` and `/reset/*` for the app; Android's names the app
and every key it is signed with, and the paths it takes are the app's own intent filters' (#520).
Both go live only once a domain exists; locally nothing reads them.

**The Google Play button carries the page's own link as the install referrer** on the group page
and the friend link's page (the friends mechanics §4.3): `referrer=<PUBLIC_SITE_URL>/join/<code>`
or `/f/<code>`, set on `GOOGLE_PLAY_URL` by parsing it, so a setting that does not parse is
refused at start. Play hands it to the app on its first launch, which opens it as if it had been
tapped (#756). An iPhone has no such thing, so the App Store button is the listing as it is, and
the friend link's page says to come back and tap **Open in Raketa**. The invitation and reset
pages carry nothing: Play keeps a referrer for 90 days, and a token is a credential.

## 7. The test seam

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
- **The fake group directory, the fake credentials and the fake friend links** install the
  default handlers, keeping the backend's rules: a test seats a group behind a code
  (`groups.seat`), an invitation or a reset behind a token (`credentials.invite`,
  `credentials.reset`), and a friend link behind a code (`friendLinks.seat`, `replace`); anything
  nobody seated leads nowhere, and a set spends its link. A test about one reply overrides the
  operation with `stub.on`.
- **The stub is the photo storage too**, at `/storage/`: a seated owner's photograph (a JPEG a
  test draws in the browser, `e2e/photographs.ts`) is answered as a fresh signed link on every
  read, which works until the test calls `stub.expireSignedLinks()`, so a site that kept one would
  be refused. `stub.storageOpened()` is every link it was opened by.
- **Tests assert what a person, a messenger or the backend would see**: text on the page, the
  status, the tags in the raw HTML's `<head>`, the pixels of the preview image, the headers, and
  the requests that arrived at the stub.
- **One worker**, because the one server talks to the one stub, which each test resets.
- **Start-up refusal is tested at the process**: `e2e/config.spec.ts` spawns `next start` with a
  bad configuration and reads its exit code and output, and starts it with a deploy's settings to
  show the app-link files carry them.
- **Every page is checked at 360 px** for sideways scrolling.

No automated test crosses apps. The journey through the backend, the app and this site is a QA
plan walked by hand ([#528](https://github.com/Raketa02/Raketa/issues/528)).

## 8. Tokens and primitives

`src/ui/tokens.css` is the only file that writes a colour or a size, besides `src/ui/tokens.ts`
(§4) and the favicon, `src/app/icon.svg`, which the browser draws on its own and which can read
no custom property. There are no mocks for this site: it **borrows the club website's look**
(paper, the coral square wordmark, a white card, its boxes and its primary button) **by copying
its values**, and draws a group as the app does, with the sport dots sampled from play 38 and the
tile's eight fills copied from the app's `MONOGRAM_HUES`. A change to either original does not
reach this copy; divergence is caught by eye (ADR-0187, _Consequences_). The type is Archivo, and
IBM Plex Mono for an invitation's code, self-hosted from `@fontsource`, so a build fetches no
font from the network. `pnpm test:tokens` fails on a literal anywhere else, and ESLint refuses an
inline `style` everywhere but the preview image. A media query's width is the one literal CSS
allows no variable for.

**Laid out for phones first**: one white card, the full width less a gutter, that stops growing at a
narrow column on anything wider. A link owner's face stands where a group's tile does, a box rounded
at a third of its side, as the app rounds a face. A button that leaves the site (for a store, or for
the app) is a plain `<a>`: the stores' are filled with ink, as their own badges are, and **Open in
Raketa** is outlined. A form's one button is coral, as the club website's is.
