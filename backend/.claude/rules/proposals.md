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
  the composition root for the proposer (#540), seeds and tests; **the yes that leaves
  `open_seats` at nought books the game** — `FILLED`, every version gone — or reopens the seat
  of whoever could not pay or no longer fits, and pauses or withdraws the players' other yeses
  (#541, see `bookings.md`). Seeded by `app/seeds/proposals.py`, which
  **runs the proposer for every pool**: the protagonist's *Padel po pracy* at Bonarka Arena,
  gathered from the cohort members who want competitive padel and fit her and each other,
  and four of her picks answered — nought, one, two and three In.
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
  **`BookedGames`**, answered off the bookings (#541); API tests may override
  `get_booked_games`. A withdrawn yes is dealt again. The seed fails if her deck would be
  empty (`assert_the_group_deck`, beside the screens battery).
- **The proposer builds the games, and its rules are one pure batch** (#540, the mechanics
  §4.3, §5, §6.2–§6.3, §7): `domain/proposer.py`'s `propose` — one pool, one sport, one
  instant; members (Level and σ off rating's estimates, weekly hours, intent, Games & money,
  booked games, live yeses), the `PlayerFit` mask per kind, the clubs the pool plays at
  (`PoolClubs` — not *Reach*, which is the Radar's word), the court hours on sale and the
  hours still **held** in → the cards that **lost** their court hour, the **picks** and the
  **deals**. Tested at that seam (`tests/unit/test_the_proposer.py`) and over HTTP
  (`tests/api/test_the_proposer.py`). Seven things are load-bearing. **Assembly, never a
  second scoring**: *most even* is the engine's own `forecast` over every way a set could
  stand; it is a rounded percent that saturates at `pct_max`, so a tie goes to the closest
  Levels, then to join order. **Bounded**: past `CONSIDERED_AT_AN_HOUR` (12) members free
  at once, the ones holding the fewest cards are considered — exact below it, and a big
  official group's cards spread; the walk is a bitmask clique walk ranked once per
  distinct pool, and runs off the event loop (`asyncio.to_thread`). **One card per court
  per hour, of either kind**, for different people — Competitive before For fun within an
  hour; the same four once per batch, soonest hour first; a four already on a card, an
  hour already holding its picks and a person already on a card then are not dealt again —
  which, with **a pick's id being its game** (`domain/ids.py`, `uuid5`), is what makes N
  processes safe with no lock. **Where**: `GroupClubs` — a player group's home club, then
  clubs within `PLAYER_GROUP_CLUBS_WITHIN_KM` of it nearest first (the matcher's
  `distance_km` over the Club directory's `inside` box); an official group only its club,
  unless `other_clubs_courts` is on, and then only for players who share no hour at home.
  **Dealing**: every seat a no left goes to up to three next best fits dealt into its
  version (`DealtVersion.first_named` is how many a version was dealt for, so a declining
  fit is replaced and a fit who said yes took the seat) — one in singles, where each fit is
  a version; a pick at half In with somebody named unswiped widens into new versions, three
  in all. **A lost court hour** is `proposals.court_hour_lost` (ending `COURT_HOUR_LOST`,
  migration 0037): no court is left at its club and hour — read off `CourtHours.held`,
  **the offer before any deadline**, so a club lengthening its notice takes no card's
  court and a paused club's cards keep theirs — the card is over, and the people In are
  dealt a new card first at the nearest hour they are all free, the same hour at another
  of the pool's clubs before another hour. **When**: `ProposeGames` runs per pool from two
  jobs — the sweep over every pool (`GroupDirectory.every`) and a short tick over the pools
  a delivered change made due (`DueForProposing`, fed per delivery run by
  `MarkDueForProposing`: a joining, a player's week, intent, first rating or Games & money,
  a swipe, anything a club changes about what it sells — which is everywhere). The due set
  is process memory and best effort; the sweep is the guarantee.
