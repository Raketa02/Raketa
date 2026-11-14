# ADR-0189 — A yes books a court, and the club is the seller

- **Status:** Accepted — **amended below** (2026-09-30: Proposals holds a player's Games &
  money; 2026-10-09: the Home card's bubble also opens the chat, Q100; 2026-10-09: the bell's
  number, *It's a game!* when the four are matched, the club's answer emailed, and time to pay,
  Q101–Q112; 2026-10-10: the share is held until the club's cut-off, and leaving before it is
  free, Q113)
- **Date:** 2026-09-29
- **§5's *check-ins* (Bookings) and *no-show report* (Games), and §7's *Check in*,
  amended 2026-10-11 by [ADR-0195](0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)** §3–§4. Desk check-in is **removed** from the player app, the club
  website and the backend. A no-show is caught **at the court** instead: a player at the club taps
  *isn't here yet* in the first half of the game, and the arrival decides *on time*, *Came late*
  or *Didn't come*. Money still never moves on any of it (§4 stands). The mechanics Q62 and Q66
  are amended by Q115 and Q116.
- **§3's three ways of working, §2's book-by, §5's way of working and *waiting for the club*, §7's
  Accept / Refuse and Overview, the *Consequences*' Instant and On request, and the 2026-10-09 and
  2026-10-10 amendments where they speak of a club's yes, amended 2026-10-12 by
  [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)**
  §1–§4. **Only Raketa is the one way** until Raketa is the club's booking software: *Instant* and
  *On request* are removed, the book-by is always the release time, and a full game books the moment
  it fills, at every club. **A club's cancel first moves the game** to a free court of the same club
  when nothing about it changes, and otherwise calls it off as before, its players owed a card that
  is closest to the lost game and first in their deck. **Players see the kind of court.** The
  mechanics Q121–Q123 log it, and a dated note marks each passage below.
- **§8's *no friends list*, §2's *the last yes books the game* and §4's *nobody ever pays more for
  an empty seat*, amended 2026-11-06 by
  [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)**
  §1, §5–§6. A player has friends. A **friends game** is a second birth of the Booking, **booked the
  moment its sender sends it**, and its sender's **Cover** pays for any seat still without its own
  payment at the cut-off: the one place a player pays for another's seat, up to the maximum he
  agreed to above his button. The deck's, Post a game's and rescues' money is unchanged. The
  mechanics Q128 logs it, and a dated note marks each passage below.
- **Specified by** [`docs/specs/games-and-fill-in/the-mechanics.md`](../specs/games-and-fill-in/the-mechanics.md)
  (the rules, and the decision log Q1–Q131) and [`docs/specs/games-and-fill-in/the-screens.md`](../specs/games-and-fill-in/the-screens.md)
  (the locked player designs, the club website and the inferred backend). Where this
  record and those documents disagree on a detail, the documents win; this record holds the
  shape.
- **Supersedes** [ADR-0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §8
  (*a club isn't a court*) and [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §13
  (*what a group doesn't do yet*, except its friends list and member removal).
- **Narrows to the *Classic play* loop** — the Players deck, Chats, challenges with the
  where · day · hour plan, and Find a game, now behind one feature flag —
  ADR-0145,
  ADR-0144,
  ADR-0164,
  ADR-0150,
  [ADR-0151](0151-a-window-whose-default-costs-you-the-game-must-outlast-the-gap-between-app-opens.md),
  ADR-0100,
  [ADR-0169](0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md) and
  [ADR-0175](0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md) §4.
- **Amends** [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §11
  (*Games* now counts real games), [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md) §9
  (the You tab gains an *Account* group), [ADR-0102](0102-silence-is-never-scored.md) and
  ADR-0120 (the grid they read becomes
  hours), and extends [ADR-0167](0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
  (its screen is reused as *It's a game!*).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** Classic play is removed, not flagged: the Players deck, Chats, challenges with their plan, Find a game and the flag are gone. Of the records the header narrows to that loop, 0100, 0144, 0145, 0150 and 0164 were deleted; 0151, 0169 and 0175 stayed with notes, because a live rule rests on each (see the [ADR index](README.md#the-2026-10-06-classic-play-removal--the-second-gap)). So §6's second bullet, §8's third bullet and the *Consequences*' two game-making paths are history, and this record is the one way a game is made. The "who fits whom" ranking went too (#580): what deals is the pair rule (`PlayerFit`: no block, mutual gender preference, the level window) and the balance forecast, so §2's *today's Match Fit, unchanged*, §5's availability term and the judged pairings and ruleset diff in the *Consequences* no longer apply. ADR-0120, which the header amends, was deleted with the ranking; the hours a card's people share are read only to grade its overlap, over everybody on it. A Game is opened only by a booking.

## Context

Groups exist ([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)):
a club's WhatsApp crowd, or a player's own. Their **Games** and **Fill in** tabs are
placeholders, and §13 says why — a group *"doesn't pick games, post games, offer or book
courts, or handle money. It has no chat."* Behind that sentence sit three older refusals:
**no booking will ever contradict the hour** (0145),
**a club isn't a court** ([0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md) §8),
and a plan is **where · day · hour agreed in a chat** (0144,
0164).

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
  *(Amended 2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §5: a friends game is
  booked at its send, before anybody else says yes. The deck's games still book on their last
  yes.)*
- There is **no clock of Raketa's own**. A card lives until its court's **book-by** (the
  club's release time, or the start minus its minimum notice) and then disappears; nobody paid.
- **Fill in offers only rescues**: open seats of *booked* games. Games still filling are offered
  only in decks; Fill in lists your own yeses on them, under *You're In*.

> **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1.** The book-by is
> always the club's release time: *the start minus its minimum notice* went with *Instant*, *On
> request* and the minimum notice. So no card can fill later than a day before its game, and by
> default three. *No clock of Raketa's own* stands.

### 3. A club has courts, hours and prices, and chooses how it works with Raketa

A club lists its **courts** (one sport each), the **hours** it offers Raketa (a weekly pattern
in one-hour slots, plus exceptions) and **prices** per court-hour, and chooses **one way of
working**: **Only Raketa** (Raketa sells those hours alone until a release lead the club sets),
**Instant** (both sell; Raketa's booking is final and the club closes what it sells elsewhere)
or **On request** (the club confirms each full game within a time it sets; nobody pays until
it does). A card promises *a court at a club at an hour*; the court number is given at booking.
Every game is **one hour**.

> **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1.**
> A club no longer chooses. **Only Raketa is the one way** until Raketa is the club's booking
> software: *Instant* and *On request* are removed, with the minimum notice and the time to confirm,
> and §2's book-by is always the release time. A full game books the moment its last yes lands, at
> every club, so §5's Booking is born *booked* and §7's Bookings has no Accept or Refuse. The courts,
> their hours and prices, the release lead, and *a court at a club at an hour* stand. Since the same
> amendment (§4) players see each court's **kind**, indoor or outdoor.

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
  *(Amended 2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §6: the sender of a
  friends game pays a **Cover** for each seat still without its own payment at the cut-off, up to
  the maximum stated above his button, and a covered game is never called off for an empty seat.
  Nobody else pays more for one.)*
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

> **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1–§2.** Club courts no
> longer holds *the way of working*, or the minimum notice and time to confirm among its settings.
> The Booking no longer holds *the club's answer (On request)* or the state *waiting for the club*:
> it is born *booked*. Its court move now also records the new court's kind and, when a club's
> cancel moved it, the cancel's reason.

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

> **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1–§2.**
> Bookings has no Accept or Refuse: nothing waits for the club's answer. *Cancel* shows where the
> game would move and offers *Cancel the game anyway*, and *Move* keeps the court's kind and tells
> the players. The Overview, once the club is live, says so and links to today's Bookings.

### 8. What is superseded, narrowed and amended, claim by claim

- **0182 §8**, *a club isn't a court* — superseded: a club has courts and sells their hours.
- **0183 §13** — superseded, except *no friends list* and *no removing members*, which stand: a
  group picks games, members post them, courts are booked, money is handled, and a game has a
  chat. **0183 §11**'s *Games* reads the games actually booked in each official group.
  *(Amended 2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md): *no friends list* no
  longer stands. *No removing members* still does.)*
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

  > **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1–§2.**
  > Neither way exists any more, so neither its double sale nor its wait does. A club that sells a
  > handed-over hour at its own desk by mistake still cancels with *double booking*, and a free
  > court of the same club now absorbs that cancel when nothing about the game changes. Otherwise
  > the remedy is still a cancellation.
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

## Amendment — 2026-10-09: the Home card's bubble also opens the chat

§6 says every chat *is reached from that game's details*. That now also means the **speech
bubble on the game's Home card**: tapping it opens the chat straight over Home, and the back
chevron returns to **whichever screen opened the chat** — Home from the bubble, the details from
their *Chat*. The room stays only the conversation, with no way into the details, and opening it
from the bubble clears the card's *new*, as opening the details does.

The product owner ruled it on 2026-10-09 from story S-01A
([#605](https://github.com/Raketa02/Raketa/issues/605), F-HOME-15.1). Marta tapped the bubble at
18:20 to say she would be late, and nothing happened — yet a chat icon is a button in every app a
player uses, and Playtomic opens a match's chat from the match itself. It is **Q100** in the
mechanics' decision log, which amends §14.3 there and the screens' A4.4 and A8. Nothing else in
§6 moves: a chat still belongs to one game and opens when it is booked.

## Amendment — 2026-10-09: the bell's number, *It's a game!* when the four are matched, the club's answer emailed, and time to pay

The product owner ruled twelve questions on 2026-10-09 from story S-01B
([#606](https://github.com/Raketa02/Raketa/issues/606)), **Q101–Q112** in the mechanics' decision
log. Four of them move this record's shape; the rest are words and screens, and live in the
mechanics §11–§17 and the screens A2.4, A4.2, A7–A9, B4, B9 and C3.

- **The bell's number is kept by the server, per player** (Q101). §5 gives Notifications one
  aggregate, the Notification preferences, and §6 an in-app fallback beside push. The recent
  notices behind the bell now carry a number: the notices given since the player last opened the
  list, the same on every phone, cleared by opening it. Nothing is marked read row by row. A
  player's own act — the yes that filled a game, a payment they confirmed that completed one — is
  never counted or bannered back to them (Q102), and nothing comes down at launch.
- ***It's a game!* means the four are matched**, not that they are booked (Q103, Q110). §2's *the
  last yes books the game* still says when money moves. But at an On request club the filler sees
  *It's a game!* with when the club answers, and all four are told it before anybody pays; the
  club's yes is then one notice, never a second *It's a game!*. The same holds while one payment
  is missing: the game is matched, and *booked · you paid* follows when the payment is in.
- **The club's no and its silence are emailed beside money** (Q105). §6's *every money event is
  also emailed* gains two that move none: *Kazimierz Padel said no* and *… didn't answer in time*,
  told apart in the notice, the email and on Home. While push is off, email is the only way to
  reach a player outside the app.
- **Time to pay** (Q109, Q112). §2's *all or nothing* stands: if one share is refused, nobody
  pays. What changes is that the refusal no longer lets everything go at once. The refused
  player's seat is theirs alone for **30 minutes**, never past the book-by. The other shares'
  holds stay on their cards, and at an On request club the club's yes and its court stay too. Paid
  in time, the game books on the kept holds, and neither anybody's bank nor the desk is asked again.
  Lapsed, the holds are let go and the seat is offered as before. This is the one clock a game
  gets after it fills besides the club's time to confirm. It is one player's, and never outlasts
  the book-by, so §2's *no clock of Raketa's own* still holds for a card.

Where the bell's number and the kept holds live among §5's aggregates is left to their builds,
[#621](https://github.com/Raketa02/Raketa/issues/621),
[#625](https://github.com/Raketa02/Raketa/issues/625) and
[#626](https://github.com/Raketa02/Raketa/issues/626). Each records its shape here when it lands,
as the 2026-09-30 amendment recorded Games & money once it was built.

**The bell's number, as built by #621.** Notifications gains a further aggregate, the **Bell**:
when a player last opened their recent notices. It is **event-sourced, one stream per player**
under the player's own id (`notifications.recent_notices_opened` / v1), born by being used, and
records a visit only when it is later than the last, so the moment never moves back. The number
itself is stored nowhere: it is the notices that reached the list after that visit, never the
player's own, read on the notices' own route and never on Home's. *After* is the event store's
order — past the newest notice the list held at the visit — not the instant a notice tells of,
because the outbox delivers after the act; a notice a later one was bundled into moved up, and
counts again. A notice is **the player's own** when
their act booked the seat: the fill records whose yes, join or confirmed payment left no seat
open (`ProposalFilled.filled_by`, nobody for the club's yes or a paused yes coming back), and a
rescuer took theirs themselves. An own notice is listed, never counted and never pushed.

The same rulings keep a full game that falls back to filling on its players' Home as *Seat open*
(Q106) and tell everyone still in it every ending and fall-back (Q104). They also tell a leaver
only what touches them (Q108), and announce the new card owed after a no (Q107). A card that never
filled still ends silently, and the record (§4's leaving rules, the mechanics §15.4) is unchanged.

> **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1 and §3,
> where this amendment speaks of a club's yes.** With On request removed there is no club's yes:
> *It's a game!* never waits on a club or says when it answers (Q103's club half), the club's no and
> silence are never told or emailed (Q105), and time to pay keeps no club's yes or court, because
> none is given (Q109, Q112). A full game is booked at its fill or, while one card is refused,
> waits on that payment alone, so a fall-back is never *asked again* (Q104, Q106). The bell's number,
> *It's a game!* when the four are matched, every ending told, a leaver told only what touches them,
> and time to pay at the fill all stand. **The new card (Q107) now has one source, a club's cancel**:
> it is chosen closest to the cancelled game, may be at the same club and hour, and is first in its
> players' deck.

## Amendment — 2026-10-10: the share is held until the club's cut-off, and leaving before it is free

The product owner ruled on 2026-10-10 from story S-01A
([#605](https://github.com/Raketa02/Raketa/issues/605), F-LEAVE-6.1), **Q113** in the mechanics'
decision log, specified by [#634](https://github.com/Raketa02/Raketa/issues/634). It moves **when
money moves and what a leave costs**. It changes §2's *the last yes books the game and charges
every seat together*, §4's second bullet, and two lines of the *Consequences*: *the club carries
the fees, including those on refunds it did not cause (a called-off game, its own cancellation)*,
now true only of a cancellation after the cut-off; and *a refunded leaver bears their own*. The
rules are in the mechanics §10.1, §12–§13, §14.1, §15.4, §16.8–§16.11, §17.2 and §18, and the
screens are in A2–A9, B4, B7, B9, C1, C3 and Part D.

**The product owner's three rules** decide it, in order: the law first; **the club never pays for
a player's leave**; and **the club's cut-off is the one deadline, the same for everyone** —
leaving before it is free, and after it it isn't.

- **The last yes holds; the cut-off takes.** §2's *all or nothing* and its ten-second undo stand,
  and the court is booked as before. But at the fill, or at an On request club's yes, every share
  is **held** on its player's card and nothing is taken. At the club's cut-off a full game's
  shares are **taken**. A game still short at the cut-off is called off and every hold is **let
  go**, so nobody pays anything. After the cut-off, money is taken at once, as before: a game that
  fills after it, a club's yes after it, a rescue taken after it.
- **A hold lasts only days, so a far-ahead fill is checked.** A hold placed without the player
  lasts 4 days 18 hours on Visa and 7 days on Mastercard. A seat's hold **reaches** the cut-off
  when its last moment is at least 6 hours after it, and is then kept. One that doesn't is let go
  at once — a **Card check**, which proves the money is there that day — and is held again at its
  **Holding time**, four days before the cut-off, by a new periodic job. If that holding still
  falls short, it is taken at its last safe moment, and a later leave before the cut-off is
  refunded in full. That fallback is the one place the club could pay for a leave, and the
  documented windows never trigger it.
- **What a leave costs.** Before the cut-off, nothing: the hold is let go, nothing is refunded,
  and no fee arises for the leaver or the club. §4's *refunds at once, minus the card fee* is gone.
  After the cut-off, a leaver whose seat is taken gets the share back less **exactly the fee Stripe
  kept on their own payment**, known once the share is taken, so the club neither earns nor loses.
  That is the *Consequences*' *a refunded leaver bears their own*, now only after the cut-off and
  never an estimate. **No estimated card fee is printed anywhere**, to players or clubs.
- **A card refused before the cut-off gets time to fix it.** Before the cut-off nothing is being
  taken, so the refused player isn't asked to pay. The 2026-10-09 amendment's time to pay serves a
  second window, **Time to fix the card**: 30 minutes with the seat kept and the others' holds
  kept, nothing paid, never past the cut-off. After the cut-off the window keeps its name. A card
  not fixed at its holding opens its seat as a rescue, and its player owes nothing. A refused
  rescuer now keeps the seat for 30 minutes too, never past the start.
- **Why holding, and not keeping the fee.** Stripe never returns its fee on a refund, so under §4
  somebody always paid for a timely leave: the leaver, or the club on a called-off game. And the
  1,60 zł the card printed was an estimate, while the fee kept depended on the card. Keeping
  "the card fee" from a leaver also tied the sum to how they paid. Polish payment law bars a
  payee's charge for using a personal card issued in the EU (art. 37a ust. 3 of the payment
  services act), and the European Commission reads the consumer-law payment-fee rule as covering
  any fee linked to how someone paid. Stripe's terms forbid surcharges the law doesn't permit.
  Letting a hold go costs nothing at Stripe, so a leave before the cut-off now costs nobody
  anything. The deduction after the cut-off is in the terms' new version, and its wording waits for
  the lawyer (open item O3). If the lawyer refuses it on personal EU cards, the fallback is
  everything back on those cards.
- **The shape.** §5's **Seat charge** tells apart a *checked* charge, a *held* one (with the hold's
  last moment), a *taken* one (with the real fee once known), a *released* one and a *refunded*
  one (with the exact amount given back). A held charge is not paid. The club's *Collected* counts
  taken charges only, and a released one is settled for payouts. The payments port moves with it:
  [ADR-0190](0190-money-goes-through-one-port-and-a-notice-is-read-once.md)'s §1 is amended the
  same day. **BLIK can't be held**, so §4's *BLIK waits* gains a reason: its rule is decided when it
  launches, and it is cards only until then.

Six calls [#634](https://github.com/Raketa02/Raketa/issues/634) made without a ruling are rules
until the product owner overrules them, each marked where it stands in the mechanics:
- a seat lost to a card not fixed at its holding counts as a leave before the cut-off on the
  record;
- the take at the cut-off is a quiet row and a receipt, not a push;
- a refused rescuer keeps the seat;
- the 6-hour reach margin and the 4-day holding lead are domain constants;
- the fallback;
- the club's figures drop the estimate too.

§4's *a game still short at the cut-off is called off* and *a seat nobody takes after it stays
empty* stand, as do the record's rules and the club's payout after the game. The builds are
[#636](https://github.com/Raketa02/Raketa/issues/636)–[#641](https://github.com/Raketa02/Raketa/issues/641)
(backend), [#642](https://github.com/Raketa02/Raketa/issues/642)–[#645](https://github.com/Raketa02/Raketa/issues/645)
(player app) and [#646](https://github.com/Raketa02/Raketa/issues/646) (club website). Where the
Seat charge's states and the holding job live is theirs to record here when they land, as the
2026-09-30 amendment recorded Games & money.

> **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1–§2,
> where this amendment speaks of a club's yes.** No club gives one any more, so a share is held at
> the fill, at its holding time or at a rescue, and *a club's yes after* the cut-off no longer takes
> money at once. A refused card at the fill keeps its time to fix the card, or time to pay, as
> above. A club's cancel before the cut-off still lets every hold go and after it still refunds in
> full, but only when it calls the game off: a cancel that a free court of the same club absorbs
> moves the game, and touches no money.
