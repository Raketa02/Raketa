---
paths:
  - "app/modules/clubs/**"
  - "app/modules/auth/**"
---

# Clubs, club accounts and club courts

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A club is a place players search, and its account signs in only on the club
  surface** ([ADR-0182](../../../docs/adr/0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md),
  [ADR-0185](../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
  §6, #503). `app/modules/clubs/` holds **two event-sourced aggregates**, and the split is
  the point: a **Club** (`club_registered`, `club_details_changed` — name, district, city,
  a non-empty subset of the four sports, and a precise point stored as the desk dropped
  it) and its **Club account** (`club_account_opened` — email and hash), because a club's
  facts are searched by every player and its credentials must not sit on that stream.
  Each repository's `save` **writes its projection in the caller's transaction** —
  `clubs` for search, with `name_folded` and `district_folded` folded by
  `clubs/domain/folding.py`, the function a query will be folded by (ł → l is the one row
  Unicode needs help with); `club_accounts` for sign-in, its email unique among club
  accounts and deliberately nowhere else, since the same address may be an unrelated
  User's. **Every refusal a sign-up or a details edit can meet names its field**
  (`details.field`) with its own code, so the request schemas carry types and no bounds —
  a bound there would refuse first, as a `422` naming no field. **Every token names an
  audience** (`aud`: `player_app` or `club`), a decode states the one it expects, and a
  token with none is a player-app token so sessions from before survive; the five access
  refusals are one function, `auth/application/access.py`, shared by both surfaces.
  `RefreshAuthTokens` and `Logout` are **built once per audience**, each context answers
  `SessionHolders` for its own accounts, and a `refresh_tokens` row records whose it is by
  filling **exactly one** of `user_id` and `club_account_id` (a check constraint). The
  candidate index counts only a **player-app** refresh as liveness. Seeded by
  `app/seeds/clubs.py` — eight Kraków clubs placed as offsets from the seed centre, each
  signed up through `SignUpClub`, each desk at `desk.<name>@raketa.example` on the seed
  password.
- **A club's courts are one stream per club, and what it can sell is derived**
  ([ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §3, §5, #535).
  `clubs` holds a third aggregate, **Club courts** (`domain/club_courts.py`), filed under the
  **club's own id** and **born by being used** — nothing is written at sign-up, and `load`
  answers an unwritten aggregate, as the Plan's does. It holds the courts (one sport each, from
  the club's own; indoor or outdoor; offered or switched off), each court's **Raketa hours** —
  the player's own `WeeklyHours`, imported rather than respelled, with no floor — the
  exceptions, the price table, the way of working, the settings and pause, and the club's
  payments account (#537); **no projection of courts is written beside it** — the one row is
  which club a payments account is. Four things are load-bearing. **Money is integer grosze** and a price
  must **split** among the sport's seats (`price_does_not_split`), so a share is exact and
  nothing is rounded (`domain/prices.py`; `docs/value-formatting.md`). **What a club can sell is
  never stored**: `domain/sellable.py` folds the pattern less the exceptions less what bookings
  hold less every hour past its **book-by** — derived once, in `raketa_terms.book_by`, and
  carried on each hour — for a **live** club only, and publishes it as `SellableCourtHours`
  (`build_sellable_court_hours`), which the proposer, posting and the fill read; a paused club
  is still live and says `taking_new_cards=False`. **Bookings do not exist yet**, so
  `CourtBookings` is a demand with one adapter answering nothing (`NoCourtBookings`, as
  `NoGroupBornGames` answers nought) — `court_has_bookings` and `court_booked_then` are already
  wired to it, and API tests stand in for it by overriding `get_court_bookings`. And **the setup
  checklist is read, never stored** (`domain/setup.py`): *locked* is the backend's rule, and
  **live is all five steps** — payments done only while the provider says the club's account
  is **ready** (#537), so a club Stripe stops is live no longer, and its courts leave the
  decks with it (`PaymentsStatusChanged` makes the proposer due). A club
  cannot untick a sport one of its courts plays (`club_sport_has_courts`), asked before the
  official groups are. Every hour is wall clock in `CLUB_ZONE` — `plans`' `PLATFORM_ZONE`
  spelled again on purpose, a unit test holding the two together — through `slot_start`.
  Seeded by `app/seeds/club_courts.py`: all three ways of working, Wisła Park half set up and
  not live, Zabłocie Sport paused, and a run that fails if a live club has nothing for sale in
  the next fortnight.
- **A club's payments account is on its Club courts stream, and the provider decides
  it** (#537, `domain/payments_account.py`, `application/payments_account.py`).
  `ConnectPayments` opens the account at the provider **once** (a key of the club and the
  hour), records and commits it, then answers a fresh single-use link to the provider's
  hosted pages — back to `<CLUB_WEBSITE_URL>/overview`, and to `/payments/continue` when a
  link is spent — and **reads the account as it stands** after every link; it refuses only an account the
  provider, asked, still calls ready (`409 payments_already_connected`) — a club recorded
  ready is asked first, so a lost notice never withholds *Continue with Stripe*. `HeedPaymentsAccount` is what the
  provider's notice runs: the account's club through the `club_payments_accounts`
  projection — the one row the Club courts repository writes, which is why it takes a
  session — the status read from the provider, recorded if it moved, and **only an account
  that was ready and is not** is emailed *Stripe needs something from you* (a club still in
  the provider's pages reads *Stripe needs more details* on its own Overview); it never
  commits, because the notice's inbox row commits with it. Both ask the provider through
  `PaymentsAccounts`, this context's own port, answered by `payments` — `clubs` imports
  nothing of `payments`. Seeded by `app/seeds/club_courts.py`: every club ready through
  `ConnectPayments` on a fake that finishes onboarding on the link, Wisła Park left
  *needs more details* through `HeedPaymentsAccount`, and a club with no account is
  connected on any run.
