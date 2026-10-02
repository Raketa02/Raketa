# Club website — technical vocabulary

The words this app uses for its own machinery. **Domain words are the root
[`CONTEXT.md`](../CONTEXT.md)'s** (Club, Club account, Administrator, Official group, Signing
out everywhere, Audience…) and are never redefined here. Where a word below meets a domain word,
it points back.

- **Server layer** — `src/server/`: the only code that opens a connection to the backend, every
  file marked `server-only`. It holds the cookie session, the refresh and the typed client.
- **Club surface** — the backend's API for this app alone, `backend/openapi.club.json`
  (ADR-0187 §5). Its tokens carry the club **Audience**; a player's are refused on it.
- **Wire type** — a type generated from the club surface into `src/generated/schema.d.ts` by
  `pnpm gen:api`. Read only by the server layer and a feature's `mappers.ts`.
- **View model** — what a page draws, made from a wire type by a mapper: a `Club`, with its
  sports in the registry's order. Pages never see a wire type.
- **Cookie session** — the club's token pair and the moment its access token lapses, sealed with
  `SESSION_SECRET` into one `httpOnly` cookie, `raketa_club_session`. Only the server can read it.
  _Avoid_: login, auth state.
- **Mark** — a plain cookie that remembers what this browser was told once:
  `raketa_club_told_live`, set when Overview says the club is live and cleared when it is not
  any more. Holds no token. Not a session.
- **Recovery cookie** — _Forgot password?_'s own sealed cookie, `raketa_club_recovery`: the email
  a recovery was asked with, and once a right code is claimed, its **ticket**. Not a session.
- **Ticket** — what a right code is exchanged for; the new password is set with it. A credential,
  so it lives in the recovery cookie and never reaches the browser.
- **Renewal** — exchanging the refresh token for a new pair. The proxy does it ahead of time; a
  server action does it on a 401, and a render through the renewal hop. _Avoid_: re-login.
- **Single flight** — one renewal per refresh token, shared by every request holding it, with the
  result kept for a grace window so a request that left before the new cookie landed gets the
  same pair. The backend spends a refresh token on use, so a second renewal would be refused.
- **Proxy** — `src/proxy.ts`, Next 16's name for middleware. It renews a lapsing pair before a
  render or an action reads it, and does nothing else.
- **The three doors** — `anonymously`, `readAsClub` and `writeAsClub` in `src/server/club.ts`:
  how a feature calls the backend with no session, while rendering, and from a server action.
- **The renewal hop** — a render refused with a 401 hands itself to `/session/renew?to=<its
path>`, a route handler that can set the cookie the render cannot, and is sent back. Its path
  comes from `x-club-path`, which the proxy stamps on every request.
- **Server action** — a function in a feature's `actions.ts` (`'use server'`) that a form posts
  to. It answers the form with a **form state** of refusal codes, or leaves by `redirect`.
- **Refusal** — a code the backend or a local check refused with, placed under the field it
  names or over the form. Turned into a sentence only by the feature's `copy.ts`. The website's
  own codes (`backend_unreachable`, `club_point_missing`, `code_wrong_length`…) share the
  backend's vocabulary.
- **Token** (design) — a CSS custom property in `src/ui/tokens.css`. The only place a colour or a
  size is written. Not to be confused with an access or refresh token, which this app always
  calls by those names.
- **Pin** — the club's point on the map, as the desk drops it (the domain's precise location of
  a **Club**, never a player's Location area).
- **Stub backend** — `e2e/stub/backend.ts`: an HTTP server standing in for the club surface in
  the Playwright suite, typed from the wire types, recording every request.
- **Fake club** — `e2e/stub/club.ts`: the stub's default handlers, one club whose tokens rotate,
  whose reset signs everyone out and whose administrators, official groups, Raketa offer
  (`club.raketa`, `e2e/stub/courts.ts`) and bookings (`club.bookings`, `e2e/stub/bookings.ts`)
  keep the backend's rules, so a test programs only the reply it is about.
- **Scan** — what the Check in page's camera read off a player's QR code: the whole payload
  (`RAKETA-CHECK-IN:1:…`), sent to the backend as it was read, once each time the code is held
  up (taken away for a second, it is new again). The **short code** is the six
  characters under the QR code, typed when the camera won't read. Both are the domain's
  **Check-in** code; what a code _is_ (whose seat, which day) is only the backend's to say.
- **Fake camera** — `e2e/camera.ts`: the camera the suite gives the Check in page, a canvas's
  stream showing a real QR code a test holds up, which counts the frames the page looks at.
- **Countdown** — what is left of a request's time to answer, counted from the backend's own
  `read_at`, so a browser whose clock is wrong draws the same figure. Not a timer of the
  backend's: when it runs out the page is read again, and the backend says the request is off.
