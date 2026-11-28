# ADR-0190 — Money goes through one port, and a notice is read once

- **Status:** Accepted — **§1 amended below** (2026-10-10: a hold's last moment, the real fee at
  capture, an exact refund, and a cancel that costs nothing — Q113)
- **Date:** 2026-09-30
- **The 2026-10-10 amendment's holds, amended 2026-10-12 by [ADR-0196](0196-only-rakieta-until-rakieta-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)**
  §1–§2: a share is held at the fill, at its holding time or at a rescue, and never at a club's yes,
  because *On request* is removed and no club gives one. A club's cancel that a free court of the same
  club absorbs moves the game and calls nothing on the port. The port itself is unchanged.
- **Builds** [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §4–§5 for
  [#536](https://github.com/Rakieta02/Rakieta/issues/536): the payments port, its two adapters, and
  the **Payment method** aggregate. Settles four things 0189 left to the ticket, one of which is
  an exemption the repository requires an ADR for.

## Context

0189 §4 decided that payments sit **behind one port with two adapters** — Stripe, and an
in-process fake for local runs, seeds and tests — and §5 that the **Payment method** is an
event-sourced aggregate, one stream per player, holding the saved method and the consent.
[The mechanics](../specs/games-and-fill-in/the-mechanics.md) §12.5 and its Appendix A add the
rules the first ticket has to keep: **the terms are accepted before anything is saved**; *change*
keeps the old method until the new one is saved; *remove* is refused while anything could be
charged to it; a card whose brand changed cannot be charged until its holder agrees again; and
Stripe's notices arrive signed, **twice as often as not and out of order**, and must be
deduplicated by their id.

Four questions were left open, and each has an obvious answer that is wrong here.

1. **Where the terms-before-save rule lives.** The obvious answer is the app: it shows the terms
   at step three and confirms with the bank at step four. But the SetupIntent's secret is what
   lets a phone save a card at Stripe, and a client holding it before the terms could save one
   the platform never had consent for — the backend would refuse to *record* it, and Stripe
   would still hold it.
2. **How a notice is deduplicated.** The obvious answer is an event per notice. But a Stripe
   event id is not a fact about any aggregate — it is the transport's bookkeeping — and
   `backend/CLAUDE.md` and `.claude/rules/domain-events.md` require **any** event-free table to
   argue for itself in an ADR.
3. **Where the webhook route lives.** ADR-0187 §5 mounts every route on the surface whose client
   calls it. Stripe is not a client, and its event shapes are Stripe's contract, not this
   backend's.
4. **How a removed card is forgotten at Stripe.** The obvious answer is inline, in the use case.
   The repository's rule is that a side effect follows the commit, from the outbox — and a
   release lost to a crash leaves a card saved at Stripe that the player asked to remove.

## Decision

### 1. The provider is a port in the Payments context, and the fake is held to Stripe's demands

`PaymentProvider` lives in `payments/domain/provider.py` and speaks Rakieta's words — a setup, a
card on file, an authorised payment, a refund with the fee withheld, a club account's three
states — never Stripe's objects. It covers what the later tickets need (#537 onboarding and
account status, #541 authorise / capture / cancel, #545 charge now, #548 refunds and payouts),
so no ticket after this one widens it for a known need.

**Two adapters.** `StripePayments` — Connect **direct charges** on the club's account, clubs as
**Accounts v2** with `fees_collector` and `losses_collector` both `stripe`, players as v1
Customers, a clone of the player's card per charge, an idempotency key on every write, the SDK's
network retries switched on. `FakePayments` — in memory, recording every call, controlled by
**the card the phone entered**: Stripe's own five test cards, down to the last four digits
(`domain/entered_cards.py`). A **demands register** (`app/bootstrap/payments_demands.py`, an
eleventh register, of its own kind: two adapters of one port onto the outside world) runs the
same demands against both — the fake always, Stripe only where a person placed a **test** key,
and skipped by name otherwise.

**Which adapter is configuration**, and three configurations refuse to start: a deployed
environment on the fake, a live key anywhere but production, a test key in production.

### 2. The secret is the answer to the terms

Starting a setup answers its id and the publishable key — **never its secret**. The secret is the
answer to accepting the terms for that setup, and to nothing else; and the save refuses a setup
whose terms were not recorded, whichever way the save arrives (the app's confirmation or Stripe's
`setup_intent.succeeded`). *The terms are accepted before anything is saved* is therefore a
property of the contract, not a promise the client keeps. The acceptance records **the version,
the moment and the address** on the player's stream; the words are the client's, as every consent
copy here is, and the backend names the version in force and refuses any other.

### 3. A notice is read once, through an inbox that is a table

`payment_notices` holds the id of every provider notice already read, written **in the
transaction that acted on it**; a notice whose id is there is acknowledged and does nothing.
**And a notice is a prompt, never a reading**: what it names — a setup, a card — is read from
the provider as it stands, because two notices about one card arrive in either order. It is
**event-free on purpose**, and this is the argument the repository asks for: the table holds **no
domain fact** — only *that* a notice was read, its kind and when — and is the outbox's mirror, the
transport's own bookkeeping on the way in as the outbox is on the way out. An event per notice
would put Stripe's delivery log into every player's history and give the outbox a subscriber to
nobody. What a notice *moves* is still event-sourced, and idempotent in its own right, so the
inbox is the first defence and not the only one.

Beside it, **`payment_customers`** is an ordinary projection of the Payment method streams —
which player a Stripe customer is — written by the repository's `save`, because a notice names a
customer and never a player.

### 4. The webhook is on no surface, and a release is a subscriber's

`POST /api/v1/webhooks/stripe` is mounted beside the three surfaces and **in no OpenAPI
document** (`app/api/v1/webhooks.py`): its caller is Stripe, and the shapes are Stripe's. It takes
no session; the signature, verified with a five-minute tolerance before a byte is read, is the
whole of the permission. The **Connected accounts** endpoint, where direct-charge and account
notices arrive, has a secret of its own and is #537's.

**The provider is called inline only where its answer is the response** — opening a setup, reading
what it saved — and always before anything is written. What an act leaves at the provider is a
**subscriber's on the outbox**, retried until it lands and keyed by what it acts on: a replaced
or removed card is released, and a setup a newer one replaced is cancelled — or, where the phone
already saved a card with it that nobody recorded, that card is released. The provider these
subscribers act at is a **per-run seam** of the delivery, as the room teller's live channel is,
so the API acts at the provider its requests hold and a seed run at its own fake.

**A key is the act and the hour it is asked in.** Stripe replays the first answer to a key for a
day, errors included, so a key that never changed would keep one passing outage between a player
and their card for a day; the hour bounds that, and costs at worst an orphaned customer or setup
across an hour's boundary, which nothing can charge. **An onboarding link takes no key of the
caller's**: it is single use, and a replay would hand back a spent one.

## Consequences

- **The Stripe adapter has not met Stripe.** It was written against stripe-python 15.6.1's own
  source and Stripe's documentation, and typechecks against the SDK's typed parameters — but no
  key existed while it was built (O7, #533). The demand suite is what will say whether it is right,
  the day a person places a test key; until then every green run is the fake's. The money half of
  that suite also needs a club account onboarded by hand in test mode
  (`STRIPE_TEST_CLUB_ACCOUNT`): onboarding is a person's walk through Stripe's hosted pages, and
  the suite does not script one.
- **A laptop's fake confirms every setup with Visa •••• 4242.** A real phone cannot confirm a
  fake's setup, so the process's fake answers as though it had — which means a laptop cannot show
  a decline or a bank's check. Tests and seeds use a fake that confirms nothing until told.
- **The secret moves to a later response than a reader of Stripe's guides expects.** The client
  ticket (#552) calls `…/setup` at step one and receives the secret at step three; a client that
  wanted it earlier cannot have it, by design.
- **A second table exempt from event sourcing.** The inbox grows by one row per notice for ever;
  nothing prunes it yet. A notice older than Stripe's retry window can never arrive again, so a
  sweep is safe whenever the table's size matters — and is not built.
- **A setup's secret is fetched from Stripe when it is handed out**, one extra read per
  acceptance, because the secret may not be written to the event store (ADR-0184 §4).
- **A card removed while the provider is down stays saved at Stripe** until the outbox's retry
  reaches it. Nothing on the platform can charge it — nothing reads a card the stream no longer
  names — but Stripe's dashboard will show it for as long as the outage lasts.
- **Five setups a day per player** is the card-testing guard the mechanics' Appendix A asks for,
  and a new number: a player changing cards six times in a day is refused until tomorrow.
- **The address on a consent is the connecting peer's.** On a laptop that is the phone; behind a
  load balancer it would be the balancer's, until the deployed server trusts its forwarded
  headers (`--forwarded-allow-ips` in `docker/api/startup.prod.sh`). Deployment is dormant, so
  this is a line for whoever reactivates it, not a fix made blind here.
- **A laptop switched from the fake to Stripe after seeding** holds fake customer ids on every
  seeded stream, which Stripe does not know: a seeded player's *Change* fails there until the
  local database is reset. Fresh sign-ups are unaffected.

## Amendment — 2026-10-10: a hold's last moment, the real fee, an exact refund

[ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s amendment of the same day
(the mechanics **Q113**, specified by [#634](https://github.com/Rakieta02/Rakieta/issues/634)) holds
each share from the fill until the club's cut-off and takes it then. A leave before the cut-off
takes nothing, and a late leaver whose seat is taken gets the share back less exactly the fee kept
on their payment. §1's port speaks of *an authorised payment* and *a refund with the fee
withheld*, and says *no ticket after this one widens it for a known need*. Q113 is a need nobody
knew of then, so the port widens, here and once, in four ways:

- **Authorising reports the hold's last moment.** A hold lasts days, not until the game: 4 days 18
  hours on a Visa charged without the player, 7 days on Mastercard. The caller decides whether a
  hold reaches the cut-off, so the port reports when it ends. On Stripe that is the authorised
  charge's `payment_method_details.card.capture_before`, read on the club's account where the
  direct charge lives. The Seat charge records it.
- **Capturing reports the real fee, or *not yet known*.** The fee exists only once the money is
  taken, and Stripe classifies a card's price tier at capture. The Stripe adapter reads it from
  the captured charge's balance transaction on the club's account. A club on its own negotiated
  pricing gets no fee there, or gets it later, and the port says *not yet known* rather than
  guessing. The Seat charge records the fee once it is known. **The card-fee estimate and the
  `CardFees` port behind it retire** from every read: Home, booking details, emails, notices and
  the club's money.
- **A refund takes an exact amount**, in place of the withhold-the-fee flag. The caller computes
  it: the share less the fee kept on that payment for a late leaver whose seat is taken, or the
  whole share for a club's cancel after the cut-off and the fallback. A refund whose fee is not
  yet known waits until it is.
- **Cancelling an uncaptured payment is how a hold is let go, and it costs nothing.** It was
  already in the port, for the fill's all or nothing. It now also carries a leave, a call-off at
  the cut-off, a club's cancel before it, and the card check at a far-ahead fill.

**The fake learns what Q113 tests.** Beside Stripe's five test cards, it models **card kinds** with
their real fees — personal EU (Stripe's standard EEA card) 1,5 % + 1 zł, business 1,9 % + 1 zł,
UK 2,5 % + 1 zł, outside Europe 3,25 % + 1 zł — and **hold windows**: Visa off-session 4 days 18 hours, Mastercard 7 days. A hold
lapses on the fake's clock: a capture after its last moment is refused, and the payment ends
cancelled. The games test console and the tests choose a seeded card's kind and network.

**The demands register gains four obligations**, run against the fake always and against Stripe
where a person placed a test key:
- an authorisation reports its last moment;
- a capture reports the real fee, or *not yet known*;
- cancelling an uncaptured payment takes nothing;
- a refund returns exactly the amount asked.

Its rescue and refund demands move off charge-now onto authorise-then-capture, the path
production uses.

**Still unchecked against Stripe**, as everything in the *Consequences* is (#533, O7):
- whether a manual capture's response already carries the balance transaction;
- whether the fee on a partial capture falls on the captured amount only;
- whether Stripe objects to a second hold placed days after a card check was let go. Renewing
  a hold is undocumented, so the holding is a second, separate off-session payment.

The build is [#636](https://github.com/Rakieta02/Rakieta/issues/636).

> **Amended 2026-10-12 by [ADR-0196](0196-only-rakieta-until-rakieta-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1–§2.** The holds above were placed at the fill or,
> through ADR-0189's amendment of the same day, at an On request club's yes. With *On request*
> removed, a share is held at the fill, at its holding time or at a rescue, and nowhere else. A
> club's cancel still lets every hold go before the cut-off and refunds in full after it when it
> calls the game off. A cancel absorbed by another court of the same club moves the game instead,
> and nothing is cancelled, captured or refunded on the port.
