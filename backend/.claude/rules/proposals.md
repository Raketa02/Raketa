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
  `GroupDeleted`, added per delivery run over its session like the room teller. **A block
  takes back the blocker's yeses** the same way
  ([ADR-0193](../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §4, #586): `application/blocking.py`, subscribed to `blocks.player_blocked`, withdraws
  each live yes of the blocker on a game the blocked player is **In** on — picks and posts
  alike, through `withdraw_a_yes`, so on a game waiting for its club the request goes too
  and the others In are told *someone left* — and each yes of theirs a booking paused there
  (`Proposal.withdraw_paused_yes`, the same `YesWithdrawn`, so it never resumes after an
  unblock); never the blocked player's yes and never a booked game. It is owed by the block being recorded, so a block lifted before delivery still took
  the yeses back; until delivery the fill's `NO_LONGER_FITS` re-check is the backstop. **Yeses are
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
  pools, soonest first. A yes needs a saved method (`payment_method_required`); **there is no
  live-yes cap** (removed 2026-10-05, the mechanics Q97 — games per week and one game per hour
  already bound what a yes can book).
  **No route makes a proposal**: `MakeProposal` and `DealVersion` are the dealer's, built by
  the composition root for the proposer (#540), seeds and tests; **the yes that leaves
  `open_seats` at nought books the game** — `FILLED`, every version gone — or reopens the seat
  of whoever could not pay or no longer fits, and pauses or withdraws the players' other yeses
  (#541, see `bookings.md`) — or, at an On request club, **puts it to the club**, full and
  still filling, its book-by no longer ending it, until the club's yes fills it or its no or
  silence **turns it down** (`TURNED_DOWN`, migration 0041; #543, see `bookings.md`). Seeded by `app/seeds/proposals.py`, which
  **runs the proposer for every pool**: the protagonist's *Padel po pracy* at Bonarka Arena,
  gathered from the cohort members who want competitive padel and fit her and each other,
  and four of her picks answered — nought, one, two and three In.
  **The group deck is a read over those streams, stored nowhere** (#539):
  `GET /pools/{id}/deck?sport&kind` deals each card as **the reader's own version** — In,
  the reader, the rest of their version in dealt order (`domain/deck.py`) — with the sides
  drawn as the evenest arrangement **the engine's own `forecast`** gives over rating's
  estimates (`BalanceForecasts`), an overlap grid graded off the
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
  empty (`assert_the_group_deck`, beside the screens battery). **Its filters are one
  method** (`ReadGroupDeck.deal_to`), and `shows` asks them of one card for one reader:
  Notifications' *You complete it* and challenges go only where the deck shows the card
  (#549), so a new filter added anywhere but `deal_to` is one an alert would not know.
- **The proposer builds the games, and its rules are one pure batch** (#540, the mechanics
  §4.3, §5, §6.2–§6.3, §7): `domain/proposer.py`'s `propose` — one pool, one sport, one
  instant; members (Level and σ off rating's estimates, weekly hours, intent, Games & money,
  booked games), the `PlayerFit` mask per kind, the clubs the pool plays at
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
  migration 0038): no court is left at its club and hour — read off `CourtHours.held`,
  **the offer before any deadline**, so a club lengthening its notice takes no card's
  court and a paused club's cards keep theirs — the card is over, and the people In are
  dealt a new card first at the nearest hour they are all free, the same hour at another
  of the pool's clubs before another hour. **On request** (#543): a game waiting for its
  club **holds its own court** through its request, so it is never lost to it and never
  counted twice at its hour; a game its club **turned down** — or **cancelled once booked**
  (#547, `ClubCancelled`, owed to the people still in: `Proposal.owed_to`) — is *owed*, read
  by `ProposalDirectory.owed_a_new_card_in` (`ended = 'TURNED_DOWN'` or
  `club_cancelled`), its people dealt a new card first exactly as a lost
  card's are, **never at the club and hour that turned them down**, by the first run that
  finds them an hour — owed until then, while the game's own hour is ahead
  (`proposals.redealt`, recorded once the pick has really been made, naming the card and
  those of the owed people on it — `card_id`, `player_ids` — whom Notifications tells
  *Your new game*, #622). **When**: `ProposeGames` runs per pool from two
  jobs — the sweep over every pool (`GroupDirectory.every`) and a short tick over the pools
  a delivered change made due (`DueForProposing`, fed per delivery run by
  `MarkDueForProposing`: a joining, a player's week, intent, first rating or Games & money,
  a swipe, anything a club changes about what it sells — which is everywhere). The due set
  is process memory and best effort; the sweep is the guarantee.
- **A game still filling has its details, for anybody dealt it** (#542; the mechanics §14.2):
  `GET /proposals/{id}` (`application/proposal_details.py`, rules in `domain/details.py`) is the
  deck's card as a screen for the readers the deck does not serve — a card's *i*, a You're In row,
  a payment to confirm, a game already answered. A reader still deciding sees **their own card**,
  exactly as the deck deals it, and is refused `proposal_not_found` where the deck withholds it
  (somebody In they do not fit); a reader **In** sees everybody In and nobody's deciding. **A full
  game still filling is *waiting for the club*** — only an On request club leaves one so — and
  says when the club must answer (`answer_by`, Q98, #614): the status is the proposal's, and
  only then is the request asked for its deadline (`ClubRequests.find`, the proposal's own
  id), folded as Home folds it (`answer_by_ahead`) and `null` if the club answered between the
  two reads. The `actions` are what the routes would take: `YES`/`NO`, `WITHDRAW`, `LEAVE`
  while the club decides, `CONFIRM_PAYMENT` (with `your_payment`) for a refused share, nothing
  once it is over or the answer is final (a no, `NO_LONGER_FITS`, a paused yes). **Home's
  badge counts the payments to confirm** beside the cards that need the reader (`owed_by`,
  shared with the TO CONFIRM read).
  **Home's read is bounded** (#613): it sends only what Home draws — live games, games that
  ended less than a day after their hour, games that need the reader — read from the earliest
  hour a game can still ask anything of its players, off the games' own clocks; see
  `bookings.md`.
- **Leaving a booked game, the cut-off and a paused week coming back are Proposals' too**
  (#544; see `bookings.md`): `POST /bookings/{id}/departure` (`leave_the_game.py`), the
  `cut-off` job (`cut_off.py`) and the outbox subscriber that resumes paused yeses
  (`resume_paused_yeses.py`, `YesResumed`) — each locks the game's proposal row first, and
  each reaches the booking through `GameBookings` and the money through `SeatRefunds`, ports
  in this context's words signed in `infrastructure/`. The details carry `leaving` (what
  *Leave the game* costs now) beside `open_seats`, `uncounted_reason` and
  `money.refunded_grosze`.
- **Rescues are Proposals' too** (#545; see `bookings.md`): *Fill in*'s Seats to fill
  (`GET /pools/{id}/fill-in`), the deck's `SEAT_OPEN` cards to a rescue's best fits, the
  booking's details for an outsider offered the seat, taking it (`POST /bookings/{id}/seats`)
  and a no to its card (`POST /bookings/{id}/no`) — over `PlayerBookings.rescues_in`,
  `BookedGameChanges.rescue`/`say_no_to_the_seat`, `SeatCharges` (`rescue=True`, `to_confirm`) and
  `SeatRefunds` (`SEAT_TAKEN`). The Games badge still counts cards with somebody **In**: a
  rescue's players have paid, and are not In.
- **A member posts a game; posting is their yes** (#546; the mechanics §9; the screens A5):
  `application/posting.py` over `domain/post.py` (*Who* and the Level range) and
  `domain/posting_grid.py` (the grid's and the sheet's rules). Six things are load-bearing.
  **One reading, the proposer's**: `ReadMembers` (`application/members.py`) is how both the
  proposer and posting read a pool's members — Level, week, **gender and preference** (now on
  `InPlay`), intent, Games & money, booked games — and a best fit is the
  proposer's own `may_play` at the hour, so the grid's number is who the post would be dealt
  to. **A cell counts at one hour**: the best hour in its range that has a free court (else
  the best of the range), an hour the poster is free for first — never people overlapping the
  poster at different hours (Q92). A free court is one `MakeProposal` would accept: a pool
  club, taking new cards, before its book-by. **Who it is for is stored on it**
  (`ProposalMade.who`, `level_low`, `level_high`, defaulted for older streams, which read as
  *for anybody*): the range starts as **the engine's own window** around the poster —
  `PlayerFit.level_window`, the matcher's `level_tolerance` through the same
  `gates.level_tolerance` the pair gate uses, narrowed while new — rounded **inward** to the
  hundredth, narrowed never widened (`level_range_too_wide` names the window). *Who* is
  everybody's on the game, the poster's too (`who_leaves_you_out`); only somebody with a
  gender set counts for Men/Women/Mixed, and a preference that excludes the game excludes
  them. **Mixed pairs keeps two of each**: a grid cell is a *full game* only with the men and
  the women beside the poster a mixed game needs; versions are dealt 2 + 2, a yes that would be a
  third of a gender is `no_longer_fits` (`Guards.refuse_a_yes_the_post_is_not_for`, on every
  yes and resumed yes on a post), the deck and the details withhold a card from a reader who
  would be one and leave such a name off (`view_of(may_stand=…)`), and **the sides — on the
  card, in the details and at the fill — stand a man and a woman each** (`standing_for`),
  genders read through `PlayersInPlay` only where a mixed post is on the table and never
  said. **Dealing**: at posting, one version per full set of best fits free then, evenest
  first, up to three, or one version with seats open (`versions_of_a_post`); after, every
  proposer batch keeps dealing it until its book-by with **no half-In condition** — a
  version naming fewer than its open seats takes whoever became a fit, a new full set is a
  new version while fewer than three, and a no's seat goes to next best fits of the gender
  it left. **Joining from the sheet** is a yes on a post the member was never dealt
  (`Proposal.join`, `SayYes`; version `NULL` in `proposal_people`, so a withdrawn joiner is
  not dealt it back) — only a post: a stranger's yes on a pick is still `proposal_not_found`.
  A join is held to what dealing would have asked of them now — the proposer's `may_play`:
  free for the hour, **no game then** (a join is never a second game at one hour), a week
  and a price within their Games & money, the kind they want
  (`Guards.refuse_a_join_dealing_would_not_make`, `post_not_open_to_you`) — so what the
  sheet lists (`open_to_join`) and what the yes accepts are one rule.
  The guards on *Post — you're In*, in the button's order: a method
  (`payment_method_required`), `LIVE_POSTS` (two,
  `live_posts_exhausted`, counted by `ProposalDirectory.live_posts_of` — filling, poster In),
  `games_per_week_booked`; then `you_play_then` and `nobody_fits_then`. **Telling the
  poster *your post didn't fill* is #549's push**, from `proposals.proposal_expired` on a
  post whose poster is still In (`not proposal.poster_withdrew`); the sweep records it.
  **Seeded by `app/seeds/posts.py`**: her post at the first Bonarka padel hour of her week
  from two days out with somebody who fits free, clear of every game and yes the layers above
  seeded — and `assert_the_posting_grid` fails the run unless her two weeks, read for anybody
  and for women, draw every look the server decides (*earlier today* once the morning is
  over). No people are added for it: Monday afternoon, the one third of a day none of her
  group's clubs sells padel, is *enough · no court* and *few · no court* off the cohort's
  committed weeks.
