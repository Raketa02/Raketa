---
paths:
  - "app/modules/proposals/**"
---

# Proposals and the group deck

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A proposal is a game still filling, and its yeses are the game's**
  ([ADR-0189](../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §2, §5,
  #538). `app/modules/proposals/` holds the **Proposal** — event-sourced, one stream per
  proposed game, `proposals.*` v1 — with the **pools**, **proposals** and **proposal people**
  projections written by the repository's `save` in the caller's transaction. Five things are
  load-bearing. **The pool is first-class and a group is its first kind**: every proposal
  carries a `pool_id` referencing `pools`, a group's pool is filed under the group's own id
  and its row written by the first proposal made in it, and who is in it is asked of
  `GroupDirectory` through `Pools` — nothing joins through a group; a leaver has left the pool,
  and **their yeses there are withdrawn** by an outbox subscriber to `GroupLeft` and
  `GroupDeleted`, added per delivery run over its session like the room teller. **Yeses are
  the game's, never a version's**: a version (at most three, each person in one, never more
  names than open seats — the dealer's `invariant`s) is only who was shown it, a seat a no
  left is dealt again *into* its version (at most three next best fits per open seat), and a
  yes on any version counts toward the one game. **The In set stays pairwise fit**: a version must fit everybody
  In and each other, and so must a yes (`no_longer_fits`, naming nobody), judged by
  `PlayerFit` — the matcher's own line-up mask (blocks, mutual gender preference, the kind's
  `level_tolerance`, narrowed for a newcomer) over live profiles and rating's published read,
  failing closed on a missing fact and raising on an unreadable block. **The court hour is
  read, never supplied**: the share and the book-by come off `SellableCourtHours`
  (`CourtHours`), so a paused or unlive club, an unsold hour or one past its book-by is
  `court_hour_not_for_sale`. **Expired is read off the clock**: `standing_at` compares the
  book-by with the caller's instant, so every act and every live read refuses an expired
  proposal before the sweep records it. The player surface is `POST /proposals/{id}/yes`
  (answers `open_seats`), `POST …/no` and `DELETE …/yes` (withdraw) — silent, a repeated tap
  recording nothing, a no final and a withdrawn yes free to be said again, a post withdrawn by
  its poster with nobody else In ending it (`ProposalWithdrawn`) — and
  `GET /players/me/live-yeses`, across
  pools, soonest first, with `cap_per_sport`. A yes needs a saved method
  (`payment_method_required`) and a live yes to spare (`live_yeses_exhausted`, ten per sport).
  **No route makes a proposal**: `MakeProposal` and `DealVersion` are the dealer's, built by
  the composition root for the engine (#540), seeds and tests; the fill (#541) is where a
  yes that leaves `open_seats` at nought books. Seeded by `app/seeds/proposals.py`: the
  protagonist's *Padel po pracy* at Bonarka Arena, gathered from the cohort members who fit
  her and each other, with four picks at her hours — nought, one, two and three In.
  **The group deck is a read over those streams, stored nowhere** (#539):
  `GET /pools/{id}/deck?sport&kind` deals each card as **the reader's own version** — In,
  the reader, the rest of their version in dealt order (`domain/deck.py`) — with the sides
  drawn as the evenest arrangement **the engine's own `forecast`** gives over rating's
  estimates (`BalanceForecasts`, no candidate index), an overlap grid graded off the
  engine's `group_availability` (`domain/overlap.py`), and the court block. The order is
  §8.2's four keys, the fourth read as **the forecast of the reader's version**; the same
  people only at their best hour, per segment. Every filter is read live: `PlayerFit` for
  blocks, gender preference and the level window — a card with somebody In the reader does
  not fit is withheld, a name that does not fit them or anybody on the card is left off —
  the Play intent (`WantedKinds`; *no preference* is both segments, undeclared is none), a
  club no longer selling (`ClubTerms`, off the published offer, which is also where *no free
  cancellation* and *the club confirms* come from), and the reader's **Games & money** — its own event-sourced aggregate, one stream
  per player, born by being used (`GET/PUT /players/me/games-and-money`,
  `proposals.games_and_money_set` / v1). Games per week and *one game per hour* read
  **`BookedGames`, whose only adapter answers nothing until #541**; API tests override
  `get_booked_games`. A withdrawn yes is dealt again. The seed fails if her deck would be
  empty (`assert_the_group_deck`, beside the screens battery).
