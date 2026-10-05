# ADR-0189 — A yes books a court, and the club is the seller

- **Status:** Accepted
- **Date:** 2026-09-29
- **Specified by** [`docs/specs/games-and-fill-in/the-mechanics.md`](../specs/games-and-fill-in/the-mechanics.md)
  (the rules, and the decision log Q1–Q96) and [`docs/specs/games-and-fill-in/the-screens.md`](../specs/games-and-fill-in/the-screens.md)
  (the locked player designs, the club website and the inferred backend). Where this
  record and those documents disagree on a detail, the documents win; this record holds the
  shape.
- **Supersedes** [ADR-0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §8
  (*a club isn't a court*) and [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §13
  (*what a group doesn't do yet*, except its friends list and member removal).
- **Narrows to the *Classic play* loop** — the Players deck, Chats, challenges with the
  where · day · hour plan, and Find a game, now behind one feature flag —
  [ADR-0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md),
  [ADR-0144](0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md),
  [ADR-0164](0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md),
  [ADR-0150](0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md),
  [ADR-0151](0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md),
  [ADR-0100](0100-challenge-window-derived-never-chosen.md),
  [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) and
  [ADR-0175](0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §4.
- **Amends** [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §11
  (*Games* now counts real games), [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §9
  (the You tab gains an *Account* group), [ADR-0102](0102-silence-is-never-scored.md) and
  [ADR-0120](0120-a-factor-reads-the-pair-or-it-is-not-a-factor.md) (the grid they read becomes
  hours), and extends [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
  (its screen is reused as *It's a game!*).

## Context

Groups exist ([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)):
a club's WhatsApp crowd, or a player's own. Their **Games** and **Fill in** tabs are
placeholders, and §13 says why — a group *"doesn't pick games, post games, offer or book
courts, or handle money. It has no chat."* Behind that sentence sit three older refusals:
**no booking will ever contradict the hour** ([0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md)),
**a club isn't a court** ([0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §8),
and a plan is **where · day · hour agreed in a chat** ([0144](0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md),
[0164](0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)).

The product owner's market work says the refusals were the gap, not the protection. In a club's
WhatsApp group somebody assembles four people, somebody books, somebody chases the money. The
feature Raketa is for is doing all three at once: the app proposes the game **with a court**, a
swipe is the answer, and the last yes **books and pays**. A plan agreed in a chat and never
booked is exactly what players already have.

Two earlier drafts of these mechanics (the product owner's PDFs of 17 and 22 September) held
the player's money on every swipe, ran two clocks per game (a two-hour answer window and a
four-hour court reservation restarted by every acceptance up to twelve hours) and kept a
"matched game without a court" alive between them. A 96-question grilling on 28–29 September
2026 replaced them. It was argued against **Stripe's own documentation** (holds last 4 d 18 h on
a Visa merchant-initiated authorisation; BLIK cannot be held; refunds never return the card
fee; the platform pays every fee unless the club is the seller) and against **Playtomic**, the
market leader, whose players pay their seat when they join, leave free until 24 h before, and
have no queue for a freed seat.

This record also meets the repo's own rule for an unmodelled context: *before writing code in
Clubs, Courts, Bookings or Matches, resolve the terms into `CONTEXT.md` and record the aggregate
shape, including whether it is event-sourced.* Courts, bookings and money are those contexts.

## Decision

### 1. A pool of players plus the courts around it

We will build the Games deck and Fill in for **a pool** — the players who may be dealt a game
and the clubs whose courts they may use. A group is the first pool; a city (Explore) is the
next, with distance switched back on. Nothing below names a group where it means a pool: every
game, card, yes and post belongs to a pool, and the group is one kind of it.

### 2. A yes is free and silent; the last yes books and charges

- The engine — today's Match Fit, unchanged, with distance standing down inside a group — deals
  **Picked for you** cards: a court at a club at an hour, and the most even four (or two) who
  are free for that whole hour and fit each other. A member can **post** a game; it is dealt to
  their best fits as a **Challenge**. A booked game that lost a player is dealt as a **Seat
  open** rescue.
- **A swipe right moves no money, holds no court and sends no message.** It shows as an **IN**
  tag on the card for the others, and cards with more people In rise in their decks.
- A game can be dealt in **up to three versions** (different fits for the open seats). **All
  versions share their yeses**: the game fills the moment enough people who said yes all fit
  each other.
- **The last yes books the game and charges every seat together, all or nothing**, after a
  ten-second undo. Every action that moves money gets that undo.
- There is **no clock of Raketa's own**. A card lives until its court's **book-by** (the
  club's release time, or the start minus its minimum notice) and then disappears; nobody paid.
- **Fill in offers only rescues**: open seats of *booked* games. Games still filling are offered
  only in decks; Fill in lists your own yeses on them, under *You're In*.

### 3. A club has courts, hours and prices, and chooses how it works with Raketa

A club lists its **courts** (one sport each), the **hours** it offers Raketa (a weekly pattern
in one-hour slots, plus exceptions) and **prices** per court-hour, and chooses **one way of
working**: **Only Raketa** (Raketa sells those hours alone until a release lead the club sets),
**Instant** (both sell; Raketa's booking is final and the club closes what it sells elsewhere)
or **On request** (the club confirms each full game within a time it sets; nobody pays until
it does). A card promises *a court at a club at an hour*; the court number is given at booking.
Every game is **one hour**.

### 4. The club is the seller, and money moves only when a game exists

- Payments go through **Stripe Connect with direct charges on the club's account**
  (`fees_collector = stripe`, `losses_collector = stripe`): the club is the merchant of record,
  named on every receipt and statement, and pays the card fee as at its own terminal. Raketa
  takes no fee and pays none. A player's card is saved once on the platform (a SetupIntent,
  after accepting terms that name the club as the one charging) and copied to the club's
  account for each charge.
- **Leaving before the club's cut-off** refunds at once, minus the card fee. **At the cut-off**
  a game still short is called off and everyone still in is refunded in full. **After the
  cut-off** a leaver is refunded only when someone takes the seat, and a seat nobody takes stays
  empty. Nobody ever pays more for an empty seat.
- **Payments sit behind one port** with two adapters: Stripe (test mode now, live later) and an
  in-process fake for local runs, seeds and tests. Launch methods are cards and wallets; BLIK
  waits on Stripe confirming a saved BLIK can pay a club.

### 5. The new contexts and their aggregates are event-sourced

Following [ADR-0002](0002-event-sourced-user-aggregate.md) as the rest of the
backend does, and chosen per context rather than inherited:

| Context | Aggregate (one stream per…) | Holds |
| --- | --- | --- |
| **Clubs** (grows) | **Club courts** — per club | courts, weekly Raketa hours, exceptions, price bands, the way of working and its settings, the Stripe account link, pause |
| **Proposals** (new) | **Proposal** — per proposed game | pool, sport, kind, origin (the engine's pick or a member's post), the court hour at a club, the share, the versions dealt, the yeses, the book-by; ends *filled*, *expired* or *withdrawn* |
| **Bookings** (new) | **Booking** — per filled proposal | the court and its number, the seats and their sides, the club's answer (On request), the cut-off, leavers and rescues, check-ins; *waiting for the club*, *booked*, *seat open*, *called off*, *played* |
| **Games** (grows) | **Game** — today's, unchanged in kind | opened by a booking, as a completed line-up opens one today: the result, its confirmation, the stars, the record, and the no-show report |
| **Payments** (new) | **Payment method** — per player; **Seat charge** — per seat per booking | the saved method and the consent record; authorised, captured, refunded, failed — Stripe's identifiers and outcome, folded idempotently from its webhooks |
| **Notifications** (new) | **Notification preferences** — per player | the three optional alerts; deliveries go through ports (push, email via [0186](0186-email-goes-through-a-port-and-a-purged-queue.md)'s mailer, in-app) |

Stripe is the ledger of record for money; a Seat charge is Raketa's account of it. **After the
fill, everything that happens to a game today — the result, the stars, the record — happens to
it unchanged** (Q6): a Booking opens an ordinary Game, which is why the after-game path needs
no second model. A card, a deck, Fill in and the club's Bookings page are **projections**,
never aggregates. The court
hours a club can sell are **derived** from its pattern, its exceptions and the booked games,
never stored hour by hour. Availability in the Player profile becomes **hours per weekday**
(07:00–23:00), replacing the 7 × 3 grid; the engine's availability term reads it, and its
offline gates are regenerated with it.

### 6. The player app

- The bottom bar is **Home · ⚡ Play · You**. Home holds your games from the moment they fill.
- **Classic play** — the Players deck, the Chats tab, challenges with the where · day · hour
  plan, and Find a game — moves behind **one feature flag, off by default**, untouched.
- Every chat belongs to one game, opens when it is booked, and is reached from that game's details;
  **Leave the game** returns to the game details.
- The You tab gains an **Account** group: *Games & money*, *Payments*, *Notifications*.
- Push notifications are built (Expo push; iPhone push needs the Apple Developer membership),
  with an in-app fallback; every money event is also emailed.

### 7. The club website

It gains **Bookings** (Accept / Refuse for On request, Move, Cancel), **Check in** (a QR or a
short code, optional per club), **Courts & prices**, **Money** and **Raketa settings**, and an
Overview that shows the setup checklist until the club is live and, after that, only what is
waiting for its answer.

### 8. What is superseded, narrowed and amended, claim by claim

- **0182 §8**, *a club isn't a court* — superseded: a club has courts and sells their hours.
- **0183 §13** — superseded, except *no friends list* and *no removing members*, which stand: a
  group picks games, members post them, courts are booked, money is handled, and a game has a
  chat. **0183 §11**'s *Games* reads the games actually booked in each official group.
- **0145** (*no booking will ever contradict the hour*), **0144** and **0164** (the plan),
  **0150** (the fill), **0151** and **0100** (answer windows), **0169** (the deck on Players) and
  **0175 §4** (leaving is one gesture on the Chats row) — **narrowed to Classic play**. They go
  on governing that loop, word for word, while it exists behind its flag; they no longer
  describe how a game is made.
- **0179 §9** — amended: the You tab asks about the account, in its Account group.
- **0102** and **0120** — amended: the grid is hours; a blank week is still absent, and the
  overlap is still read from the pair.
- **0167** — extended: its screen, with one word, is *It's a game!*.

## Consequences

- **Raketa now touches real money, and carries what that means.** Stripe Connect onboarding for
  every club, a legally reviewed consent text, card data only ever in Stripe's own fields,
  webhooks that arrive twice and out of order, and a cut-off job whose correctness decides who
  is refunded. None of this existed; all of it is new code that must be right the first time a
  club goes live.
- **A booking can now contradict the hour, on purpose.** Everything 0145 argued stays true of
  the Classic play loop, and the two ways of making a game will coexist behind a flag until the
  loop is removed. Two game-making paths are a maintenance cost the product owner has accepted.
- **The club carries the fees**, including those on refunds it did not cause (a called-off
  game, its own cancellation). A refunded leaver bears their own. Clubs must be told this
  plainly during setup.
- **Clubs on Instant can double-sell**, because Raketa cannot see their desk. The remedy is a
  cancellation with full refunds, which players will feel. On request trades that risk for a
  wait the club sets (half an hour by default).
- **Open items outside the code:** BLIK with the club as seller (Stripe copies cards only),
  holding club payouts until after the game, the consent wording, Apple Pay for one-off
  charges, and the club's fiscal receipts. Each is listed in the mechanics §21 and blocks the
  first live club, not the build.
- **The availability change ripples.** Onboarding, the You tab's *Your week*, the engine's
  availability term, the judged pairings and the ruleset diff all move with it; the gates will
  go red until they are regenerated in the same change.
- **Seeds grow a fake payments adapter**, and a Stripe test account is needed before anyone can
  exercise the real flow; its keys are a human's to place.
- **The pool abstraction costs a little now** — a group could have been hard-wired — and saves
  the rewrite when Explore becomes a city-wide pool.

## Amendment — 2026-09-30: Proposals holds a player's Games & money

§5's table gives **Proposals** one aggregate, the Proposal. Building the group deck
([#539](https://github.com/Raketa02/Raketa/issues/539)) gave it a second: **Games & money** — a
player's *games per week* (1–7, default 2, Monday to Sunday) and *most I'll pay* (off, 35, 45 or
60 zł), which the mechanics §6.6 and §17.1 decide and this record placed nowhere. It is
**event-sourced, one stream per player** under the player's own id (`proposals.games_and_money_set`
/ v1, both values on every event), and **born by being used**: a player who never opened the
screen is at the defaults and has written nothing. A same-valued save records nothing — a
preference, as a Play intent is.

It lives in Proposals, not in the Player profile or Payments, because every rule that reads it is
about which games are dealt and which yeses stand: the deck (#539), the proposer (#540), the
fill's pause (#541) and posting's guard (#546). The deck itself stays what §5 says it is — a
projection, recomputed at every read and stored nowhere.
