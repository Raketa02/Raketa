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
  alike, through `withdraw_a_yes`, so on a full game waiting for one payment the
  blocker's hold goes too and the others In are told *someone left* — and each yes of theirs a booking paused there
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
  failing closed on a missing fact and raising on an unreadable block — and since #661 **the
  reliability filter** ([ADR-0195](../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §6): a pair is unfit when either's minimum (a Player profile preference,
  `PUT /players/me/reliability-filter`) is above the other's band, *New* passing every minimum
  (the engine's `passes_reliability_minimum`), the points read off `player_score`'s published
  query **only where somebody among them has a filter on** — and **each person's folded at
  most once per deal**: the adapter remembers whose it read at one instant (it is built per
  request and per job run), so a deck read asking for its cards, the reader's rescues and the
  whole pool folds nobody twice, and the proposer, the deck and rescues ask every kind at once
  (`unfit_pairs_by_kind`). **Yeses already given stand**: the fill's `NO_LONGER_FITS` re-check,
  a paused yes coming back (`Guards.refuse_a_yes_that_does_not_fit(…, already_given=True)`)
  and a seat kept for a refused rescuer confirmed within its time (#640;
  `RescueOffers.is_offered(…, already_kept=True)`) ask it with `reliability_filter=False` —
  unlike a block, the filter takes back no yes, not even at the fill (a call, the grilling's
  *from then on*); a new yes, a join, a version dealt, the deck, the details, posting and
  rescues all ask it, and a booked game is never touched. A seat reopened when a time to pay
  ran out is a yes again, so its late confirmation meets the filter (a call). **A changed Play
  intent leaves the cards not yet answered** (Q127;
  [ADR-0201](../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
  §3, #738), the filter's *from then on* again: a name **not In, with no yes paused there**,
  whose intent no longer wants a card's kind **holds no seat on it** — `domain/deck.py`'s
  `left_the_kind`, read live and recorded nowhere, and **not a no**. Others' decks and the
  details leave it off (`view_of(…, wants=…)`, every name's intent read through `WantedKinds`
  by `wants_of`); the proposer counts it gone (`_gone`, and `_widens`), so its seat goes to
  up to three next best fits at the next run (one in singles); and a new yes is
  `no_longer_fits` (`Guards.refuse_a_yes_of_a_kind_not_wanted`, after the method, before the
  fit — a join keeps `post_not_open_to_you` through *may play*). Wanting the kind again names
  them again, beside any fits dealt meanwhile — the first yes takes the seat, and nothing is
  dealt for the return. **Never asked of a yes already given**: somebody In or paused, the
  fill's re-check, a paused yes coming back, a seat kept for a refused rescuer confirmed
  (`RescueOffers.offered(…, already_kept=True)` skips the kind as it skips the filter). **An
  empty intent is undeclared and never asked** — every declared intent wants a kind and
  nothing deals to none, so only a changed intent leaves one — **nor is a post's poster**,
  whose post is a one-off of the kind they chose (ADR-0201 §2), their yes said again after a
  withdrawal included. Calls made without a ruling: a
  reopened seat's late confirmation is a new yes and meets it, as it meets the filter; the
  card stays open to the player who left its kind, whose details still offer *I'm in*; and
  the name still counts as on a card at that hour, and among that card's people, for the
  proposer, so a switch frees no hour for a card of the other kind. **The court hour is
  read, never supplied**: the share and the book-by come off `SellableCourtHours`
  (`CourtHours`), so a paused or unlive club, an unsold hour or one past its book-by is
  `court_hour_not_for_sale`. **Expired is read off the clock**: `standing_at` compares the
  book-by with the caller's instant, so every act and every live read refuses an expired
  proposal before the sweep records it. The player surface is `POST /proposals/{id}/yes`
  (answers `open_seats`), `POST …/no` and `DELETE …/yes` (withdraw) — silent, a repeated tap
  recording nothing, a no final and a withdrawn yes free to be said again, a post withdrawn by
  its poster with nobody else In ending it (`ProposalWithdrawn`) — and
  `GET /players/me/live-yeses`, across
  pools, soonest first, each with `indoor` (#706): the deck card's kind of court, read off the
  same `CourtKinds` free-court read at the yes's club, sport and hour — `true` / `false` when
  every free court is of one kind, `null` when they are mixed, so the You're In row can say
  *Indoor* or *Outdoor* before a yes. A yes needs a saved method (`payment_method_required`);
  **there is no live-yes cap** (removed 2026-10-05, the mechanics Q97 — games per week and one game per hour
  already bound what a yes can book).
  **A refused share at the fill holds its seat for its player** (#625, #626): the
  player stays In with `Proposal.paying` until their time to pay ends — the game full to
  everybody else, `waiting_for_a_payment` — and `TimeToPayRanOut` reopens it; before the
  club's cut-off the same time is **to fix the card** (`TimeTo`, #638); see `bookings.md`.
  **No route makes a card itself** (amended by Q127;
  [ADR-0201](../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
  §5, #739): `MakeProposal` and `DealVersion` are the dealer's, built by the composition root
  for the proposer (#540), seeds and tests — and **one route runs the proposer**,
  `POST /pools/{id}/deal` (`DealThePoolNow`, beside `ProposeGames`): right after an intent
  answer on Games the phone asks for its group to be dealt now and waits, so *Finding for-fun
  games for you…* lasts as long as the dealing. It is `ProposeGames.execute` for that one pool,
  every sport it plays, over the request's session and clock — the batch the jobs run, safe
  beside them and beside itself by the same construction (a repeat deals nothing new), its
  records on the outbox in the transaction of each act and told as the jobs' are (*Your new
  game* included) — behind the deck's refusal: `pool_not_found` for no such pool and for one
  the caller is not in, one code. `204`, no body. No rate limit (ADR-0201 *Consequences*; the
  cost is in #739's handover). **The yes that leaves
  `open_seats` at nought books the game** — `FILLED`, every version gone — or reopens the seat
  of whoever could not pay or no longer fits, and pauses or withdraws the players' other yeses
  (#541, see `bookings.md`) — **at every club: no club confirms a game** (#669; ADR-0196
  §1), so a full game is never put to a club and nothing is turned down; migration 0058
  dropped `waiting_for_the_club` and `TURNED_DOWN`. Seeded by `app/seeds/proposals.py`, which
  **runs the proposer for every pool**: the protagonist's *Padel po pracy* at Bonarka Arena,
  gathered from the cohort members who want competitive padel and fit her and each other,
  and four of her picks answered — nought, one, two and three In.
  **The group deck is a read over those streams, stored nowhere** (#539):
  `GET /pools/{id}/deck?sport&kind` deals each card as **the reader's own version** — In,
  the reader, the rest of their version in dealt order (`domain/deck.py`) — with the sides
  drawn as the evenest arrangement **the engine's own `forecast`** gives over rating's
  estimates (`BalanceForecasts`), an overlap grid graded off the
  engine's `group_availability` (`domain/overlap.py`), and the court block — **with the kind
  of court it promises only when that is certain** (#671; the mechanics §5.2, Q122):
  `DeckCard.indoor` is *Indoor* or *Outdoor* when every free court of the card's sport at
  its club and hour is of that kind, read live off `CourtKinds` (`SellableCourtKinds`, the
  offer before any deadline, as `held` reads it — registered in `proposal_demands.py`), and
  `None` when they are mixed, since the first free court in the club's order is the one
  booked; a `SEAT_OPEN` card carries its booked court's kind. The details read it the same
  way (`ProposalDetails.indoor`). A player sees it and never chooses by it. The order is
  §8.2's four keys, the fourth read as **the forecast of the reader's version**; the same
  people only at their best hour, per segment — **after the cards owed to the reader**
  (#673; Q123): a card whose `owed_card_for` names the reader is `DeckCard.owed_to_you`
  and dealt first, soonest first among owed cards, ahead of the usual order and kept over
  the same people at another hour (`dealt_in_order`). Never on the wire — it carries no
  mark — and nobody else's deck is touched: a best fit dealt beside the owed people reads it
  in the usual order. A card answered leaves the deck, so the usual order applies again;
  the phone still lifts a notice-opened card on top. Every filter is read live: `PlayerFit` for
  blocks, gender preference and the level window — a card with somebody In the reader does
  not fit is withheld, a name that does not fit them or anybody on the card is left off —
  the Play intent (`WantedKinds`; *no preference* is both segments, undeclared is none), a
  club no longer selling (`ClubTerms`, off the published offer, which is also where *no free
  cancellation* comes from), and the reader's **Games & money** — its own event-sourced aggregate, one stream
  per player, born by being used (`GET/PUT /players/me/games-and-money`,
  `proposals.games_and_money_set` / v1). Games per week and *one game per hour* read
  **`BookedGames`**, answered off the bookings (#541); API tests may override
  `get_booked_games`. A withdrawn yes is dealt again. The seed fails if her deck would be
  empty (`assert_the_group_deck`, beside the screens battery). **Its filters are one
  method** (`ReadGroupDeck.deal_to`), and `shows` asks them of one card for one reader:
  Notifications' *You complete it* and challenges go only where the deck shows the card
  (#549), so a new filter added anywhere but `deal_to` is one an alert would not know.
  **And the route's read loads each stream once** (#704, ADR-0197 §2c):
  `build_read_group_deck_once` — the routes' builder and nobody else's: `get_read_group_deck`'s,
  and `build_read_deck_counts`'s below — hands
  every adapter one `ReadOnceEventStore` over the request's store, so the profile,
  rating, proposal, booking, intent, Games & money and club-courts streams the pair rule,
  the forecasts, the card's people and the rescues share are replayed once per read, and two
  loads in flight together are one. It lives as long as the request and **nothing beside a
  writer takes it**: a use case that appends and reloads must see its own events, and so
  must the notifications handler, whose `build_decks` asks the deck `shows` for every row of
  an outbox batch over one session while other handlers in the batch append to the proposal
  and booking streams — it and the seed's screen assertion take the plain
  `build_read_group_deck`, and `test_the_reuse_is_the_requests_alone` holds that line. The
  wrapper's `append` forgets its stream all the same, and
  `tests/api/test_group_deck_read_once.py` reads with the reuse and without it. Each builder
  takes the store as an optional `event_store` through `_own_or` and builds its own when
  handed none. Post a game's
  grid loads the same way and is deliberately not wired (211 statements measured; a
  follow-up once the seam has proved out). Measured on the busy seed deck (47 dealt, 33
  shown, 13 people): 257 → 138 statements, 160 → 56 ms CPU with #702 and #703.
  **The reader's switches, added up** (#739; ADR-0201 §6): `GET /players/me/deck-counts?sport=`
  (`ReadDeckCounts`) answers `{sport, competitive, for_fun}` for You › *What kind of game*'s
  *Your 7 competitive cards in your groups go* — each kind summed over every pool the reader is
  in (`Pools.of_player`), **each pool's number read by this deck's own `execute`**, its
  `segments`, so it is the switch's count with every filter and the Seat open cards, and never
  a second account of it (ADR-0201 *Two counts must agree*). A kind the intent does not show
  has no segment, so `0`; an undeclared sport has none, so `0` and `0`; a pool left between the
  two reads is skipped. Built over `build_read_group_deck_once`, so the pools share one
  read-once store; it is read-only, which is what the reuse asks.
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
  `distance_km` over the Club directory's `inside` box); an official group its club, and —
  while `other_clubs_courts` is on, **on by default** — the clubs within the club's distance
  **only at a sport and hour its club has no free court** (#746; ADR-0202 §7): **the court
  source answers per hour**, `PoolClubs.offered`, read by the proposer's `_selling` and
  Post a game's grid, and by the friends card (#750, below) — so a group never has two
  court rules. The
  old *no shared hour at home in 14 days* refusal is gone. **No free court is read off what
  Raketa may sell now** — booked out, closed, outside the Raketa hours, past its book-by,
  or the club paused — as the old refusal read *an hour at home* (a call, #746's handover):
  so inside the home club's release lead, a neighbour with a shorter one is offered at
  every hour it sells, and the soonest-first dealing reaches it first.
  **Dealing**: every seat a no left goes to up to three next best fits dealt into its
  version (`DealtVersion.first_named` is how many a version was dealt for, so a declining
  fit is replaced and a fit who said yes took the seat) — one in singles, where each fit is
  a version; a pick at half In with somebody named unswiped widens into new versions, three
  in all. A name whose intent left the card's kind is gone exactly as a no is, for both
  (Q127, above). **A lost court hour** is `proposals.court_hour_lost` (ending `COURT_HOUR_LOST`,
  migration 0038): no court is left at its club and hour — read off `CourtHours.held`,
  **the offer before any deadline**, so a club lengthening its release lead takes no card's
  court and a paused club's cards keep theirs — the card is over, and the people In are
  dealt a new card first at the nearest hour they are all free, the same hour at another
  of the pool's clubs before another hour. **A booked game its club cancelled** (#547,
  `ClubCancelled`, owed to the people still in: `Proposal.owed_to`) is *owed* — the one
  source of an owed game since On request went (#669) — read by
  `ProposalDirectory.owed_a_new_card_in` (`club_cancelled`), its people dealt **the owed
  card** (#673; ADR-0196 §3, Q123) **closest to the cancelled game first**, one sort for a
  lost card's people and an owed game's: by distance in time, then **the lost card's own
  club at its own hour**, then the home club and the others nearest first, then the earlier
  of two hours as close — so the same club, day and hour come first (sold again on a court of the other
  kind, or at a new price), then another club at that hour — for an official group only
  where its club has no free court then — then the closest hour, home club first. **The *never at this club and hour* exclusion is gone
  entirely**; the court the club cancelled is closed for the hour instead (`bookings.md`),
  so the same club and hour is never the broken court. An official group reaches another
  club at that hour too, **whenever its club has no free court then** (the court source,
  as for any card — ADR-0196 §3's second step since #746), every owed player must still be free to play it (free
  for the hour, a week under the cap, within *most I'll pay* at the new price), and a game with no hour stays
  owed until its old hour passes. **The card records whom it is owed to**:
  `Pick.owed_card_for` → `MakeProposalCommand.owed_card_for` → `ProposalMade.owed_card_for`
  (defaulted, so an older card is owed to nobody) → `Proposal.owed_card_for` — the owed
  people on it, never the best fit completing it, and nothing on a lost card's new one,
  which no notice promised. **A redealt pick's id names the game it is dealt after**
  (`pick_id(…, after=)`): the owed card may be the same four at the same club and hour,
  which is the cancelled pick's own id, whose stream is taken. Dealt by the first run that
  finds them an hour — owed until then, while the game's own hour is ahead
  (`proposals.redealt`, recorded once the pick has really been made, naming the card and
  those of the owed people on it — `card_id`, `player_ids` — whom Notifications tells
  *Your new game*, #622). **When**: `ProposeGames` runs per pool from two
  jobs — the sweep over every pool (`GroupDirectory.every`) and a short tick over the pools
  a delivered change made due (`DueForProposing`, fed per delivery run by
  `MarkDueForProposing`: a joining, a player's week, intent, first rating, Games & money or
  reliability filter, a swipe, anything a club changes about what it sells — which is everywhere). The due set
  is process memory and best effort; the sweep is the guarantee. **And at a member's
  request**, for one pool, from `POST /pools/{id}/deal` (#739, above) — the short tick still
  runs the pool the intent change made due, and deals nothing the route already dealt.
- **Every face carries the reader's *friend* tag, and Home the friend requests** (#745;
  ADR-0202 §1–§2; `friends.md`): `DeckPerson.friend`, marked for the reader by
  `application/friends.py`'s `with_the_readers_friends` over `ReaderRelations` — one question for
  the set — in the deck, the details, Home, a booked game's details, Fill in and Post a game's
  slot sheet (`DeckTileSchema.friend`, `BookedTileSchema.friend`, `SlotFitSchema.friend`);
  `DeckPeople` itself knows no reader, so a read that forgets to mark them sends `false`. `GET /bookings/{id}` adds `played_with`, the reader's whole
  relation to everybody else on the game — the result's *PLAYED WITH* card — and `GET /home` adds
  `friend_requests` (`FriendRequestsOnHome`), not counted in `needing_you`. Both ports are signed
  in `proposals/infrastructure/friends.py`, so the arrow runs `proposals → friends`.
- **A friends game is sent, answered and called off here** (#751; ADR-0202 §5–§6;
  `application/friends_games.py`; see `bookings.md` and `payments.md`): `POST /pools/{id}/
  friends-games` (`SendAFriendsGame`, `FriendsGameSentResponse`: booked, or `your_payments`
  to confirm and send again with `booking_id`), `POST /bookings/{id}/invitation/acceptance`
  and `…/invitation/decline` (`AnswerAFriendsGame`), `POST /bookings/{id}/call-off`
  (`CallOffAFriendsGame`), and the `invitations` job (`RunOutTheInvitations`). Its demands
  are `FriendsGameBookings` (bookings), `SendersCourts` and `CoversAtTheCutOff` (payments) —
  the first and last with rows in `proposal_demands.py`. **Home** gains `friends_games`
  (*FRIENDS GAME · n*, the invitations still waiting on the reader, soonest to end first, not
  in `needing_you`), and every card and `GET /bookings/{id}` a `friends_game` block (the
  sender, the pay mode, each seat's state — `IN`, `WAITING` with its end, `CANT_MAKE_IT`,
  `DIDNT_ANSWER` off the clock, `EMPTY` and `SEAT_OPEN` since #752 — `your_invitation_until`, `can_call_off`);
  a friend invited and not In reads the details too (`_as_invited`), every seat the card drew
  among `sides` (`BookedGame.planned_sides`). **A friends game is no proposal**, so
  `the_game`, `load_for_update` and the payments-to-confirm rows find none for it.
  **Its empty seats** (#752; see `bookings.md`): `POST /bookings/{id}/seats/{seat_of}/
  invitations` (`InviteIntoASeat`, `SeatInvitationCommand`, `{friend_id}`: anybody In, one
  of their own friends;
  refused naming nobody — `not_a_friend`, `no_level`, `cannot_play_together` against
  everybody In and every friend invited into another seat, `friend_plays_then`,
  `friends_week_is_full`, `already_on_the_game`, `seat_just_taken`) and `…/opening`
  (`OpenASeat`, `SeatOpeningCommand`: the sender, In, before the cut-off —
  `cut_off_has_passed` after); both
  run out a card invitation whose time is up first, as the job would. The accept into a
  seat open to the group pays its payer back (`the_seat_paid_back`) and, the last open
  seat taken, lets go of every rescue payment still pending. `POST /bookings/{id}/departure`
  leaves a friends game too, and the `cover-warning` job is `WarnTheCovers`. The
  details' `friends_game.seats` are **one row per seat** (`BookedGame.seat_states`): every
  player In, the sender first, each card seat still waiting, then each empty seat and each
  seat open to the group — `seat_of`, `invitations` (each with its nickname, from
  `people_on`, which reads every invitee), `can_invite`, `can_open` — the face of a seat
  nobody holds whose it was, or the reader's own on a seat they are invited into
  (`planned_sides_for`, `seen_by(…, now=)`); `leaving` is the ordinary `LeaveTerms`; and
  `can_call_off` needs the sender In.
- **A game still filling has its details, for anybody dealt it** (#542; the mechanics §14.2):
  `GET /proposals/{id}` (`application/proposal_details.py`, rules in `domain/details.py`) is the
  deck's card as a screen for the readers the deck does not serve — a card's *i*, a You're In row,
  a payment to confirm, a game already answered. A reader still deciding sees **their own card**,
  exactly as the deck deals it, and is refused `proposal_not_found` where the deck withholds it
  (somebody In they do not fit); a reader **In** sees everybody In and nobody's deciding. **A full
  game still filling is *waiting for a payment*** (#625) — no club confirms a game — and says
  until when (`payment_due_by`). The `actions` are what the routes would take: `YES`/`NO`,
  `WITHDRAW`, `LEAVE` while a payment is awaited, `CONFIRM_PAYMENT` (with `your_payment`) for a refused share, nothing
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
  `money.refunded_grosze`. **A full game that falls back stays on Home** (#624, Q106): its
  booking is read `FILLING_AGAIN` and folded against this proposal on every read
  (`application/home.py`'s `as_it_stands`) — see `bookings.md`.
- **Rescues are Proposals' too** (#545; see `bookings.md`): *Fill in*'s Seats to fill
  (`GET /pools/{id}/fill-in`), the deck's `SEAT_OPEN` cards to a rescue's best fits, the
  booking's details for an outsider offered the seat, taking it (`POST /bookings/{id}/seats`)
  and a no to its card (`POST /bookings/{id}/no`) — over `PlayerBookings.rescues_in`,
  `BookedGameChanges.rescue`/`say_no_to_the_seat`, `SeatCharges` (`rescue=True`, `to_confirm`) and
  `SeatRefunds` (`SEAT_TAKEN`). **A refused rescuer keeps a seat** for thirty minutes (#640),
  over `BookedGameChanges.keep_the_seat`/`kept_seat_ran_out`/`keeps_past`/`kept_for` — see
  `bookings.md`. The Games badge still counts cards with somebody **In**: a
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
  club, taking new cards, before its book-by — **and the court source's own, hour by hour**
  (`PoolClubs.offered`, #746): an official group's grid and sheet list another club only
  where its club is full then, each such row `FreeCourtSchema.home_club_full`, and a post
  there at any other hour is `court_hour_not_for_sale`. **Who it is for is stored on it**
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
- **The friends card and *Find a court* are reads of a fixed line-up** (#750;
  [ADR-0202](../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
  §5; the friends mechanics §7.4–§7.6): `GET /pools/{id}/friends-card?sport&kind&friend_ids…`
  and `GET /pools/{id}/friends-card/courts?sport&friend_ids…`, `application/friends_card.py`
  over `domain/friends_card.py`. **Nothing is recorded**, so *no route makes a card itself*
  stands. Five things are load-bearing. **One reading for both, and for the send**:
  `ReadFriendsLineUp.read` is what #751's send must read the line-up through, so the card
  and the send cannot disagree. Its checks run in the order that says least, each naming
  nobody: the reader in the pool (`pool_not_found`; the friends need not be — a
  non-member is a **guest**), the sport's line-up (`wrong_line_up_size`, `details.friends`:
  three in doubles, one in singles, each once, never the reader), each friend the
  reader's now (`not_a_friend`, through `ReaderRelations.friends_among`, before anything
  is read about them), a level in the sport for all four, the reader too (`no_level`), and
  **the pair rule's block mask alone** (`cannot_play_together`, `PlayerFit.blocked_pairs`)
  — the level window, the kind's tolerance, gender preferences, the reliability filter,
  a Play intent and *most I'll pay* don't apply (call 10). **The sides are the deck's**:
  `arrangements` of the line-up in the order sent and `evenest` over `BalanceForecasts`,
  the first among equals — or the sides sent, named by **`partner_id`** (the friend
  beside the reader; doubles only, else `sides_not_of_the_line_up`), a call: the reader
  always stands on their own side (Q70), so a partner names every way to stand. **The
  courts are the court source's**, `PoolClubs.offered` over `CourtHours.on_sale` from now
  to now + the deck's 14 days, **one row per free court** — `CourtHourOnSale.free`, the
  courts named in the club's order (`CourtOnSale`, the first being the one a booking
  then is given), so *Court 3* is printed — soonest first, the home club first within an
  hour, each with who of the four is free for the whole hour and who is **busy** (outside
  their weekly hours, nothing else). **Left out**: an hour where one of them has a game
  (call 5) — **and nothing for a full week**: call 5 refuses that one's Accept with a
  sentence instead (§8.4), and the send refuses the sender's own (#751). **The court
  proposed** is the first row where all are free, failing that the first where the most
  are (`max` over the free count keeps the soonest) — a call: it may be an hour only one
  of them is free — and `null` only with no row at all, so the screen's *Pick a
  different court* is gone exactly when the list is empty;
  `court_id` + `starts_at` picks a row (`court_hour_incomplete` for one without the other,
  `court_hour_not_for_sale` for one the list does not hold now, both the use case's). The
  window is now to now + 14 days, the deck's horizon. The card adds the overlap
  of the four weeks at the court's hour (`null` with no court, whose card the screen
  replaces with its sentence) and **`cut_off`**, the club's cut-off for that hour off
  `ClubTerms` (`deck.cut_off_of`) — a call, for the send sheet's *until Fri 10:00*.
  **Measured** on the seed's busiest pool, *Padel po pracy* (20 members, a player group
  reaching 4 clubs), in the API container: the card 54 statements, ~45 ms CPU warm;
  *Find a court* 48 statements, ~44 ms, and **829 rows, 300 KiB** of JSON over 13 days —
  every court, as §7.6 asks.
