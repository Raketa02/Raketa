---
paths:
  - "tests/demands/**"
  - "app/bootstrap/*_demands.py"
---

# Demand registers (tests/demands/)

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- `tests/demands/` — the **outward demands**, parameterised over every implementation
  registered in a register beside the wiring
  ([ADR-0098](../../../docs/adr/0098-matcher-demands-as-executable-contracts.md)). Adding a row
  to a register enrols an adapter; a port with no row fails the suite. Not named
  *contract* — that word already means `openapi.player.json` drift here.
  **Eighteen registers, and they are eighteen on purpose — one per kind of claim.**
  `app/bootstrap/matcher_demands.py` and `player_record_demands.py` hold the ports a
  *consumer* declares of contexts it does not write; `games_demands.py`,
  `rating_demands.py`, `player_score_demands.py` and `sportsmanship_demands.py` each hold
  the ports one *provider* publishes outward; `game_demands.py` holds what `games` demands
  of other contexts — the court's pairing
  ([ADR-0161](../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md)) — on its
  own list because `games_demands.py` is what that context *publishes* and a demand is the
  other kind of claim; and
  `conversation_demands.py` holds what a **room** demands of the contexts it is told by and
  reads from. There is deliberately no *conversations provider* register, and there never
  will be: a conversation is told and tells nothing. **Two registers went with their
  contexts (#578)**: `challenge_demands.py`, what `challenges` demanded of the matcher, and
  `plan_demands.py`, what a plan demanded — and with them `games`' `AgreedMoment` and the
  `SeatableCourt` it published for challenges.
  **The matcher's register is three rows since #579**: `AccountHoldQuery`,
  `AccountStatusQuery` and `AtStakeQuery`. `PlayerScoreQuery`, `MatchHistoryQuery`,
  `HalfBuiltCourtQuery` and `SharedCourtQuery` were read by the searches, the line-ups and
  the deck alone and went with them, and `AtStakeQuery` lost its head-to-head read — a
  booked game's court is priced side against side.
  Each register's exhaustiveness
  assertion is about its own kind of claim and would stop meaning anything with another
  kind in it — which is also the rule for the next one: **a new provider or a new consumer
  gets a new register, not a row in somebody else's**, and the first person to add a row
  should not have to guess which list it belongs in. The sportsmanship register is that
  rule being followed rather than restated: the sportsmanship figure could have been a row
  on the record's consumer list, and a provider's publication on a consumer's register is
  exactly what makes an exhaustiveness assertion a claim about something else. One port on
  the record's list has **three** implementations, which is what the suite has to be
  parameterised over: *where has this reader been shown this person* is a question three
  contexts each answer about themselves.
  **The ninth, `payments_demands.py`, is a kind of its own**: the two adapters of one port
  onto the outside world — the fake and Stripe — so a fake that drifts from the provider goes red.
  Its rows build over the **settings**, not a session, and one may be absent: Stripe runs only
  where a person placed a test key, and is skipped by name otherwise (ADR-0190 §1).
  **The tenth, `proposal_demands.py`, is Proposals' consumer register** (#542): Home's and the
  details' three demands — a player's bookings (`bookings`), a booked game's result (`games`), a
  club's distance (the Player profile and `clubs`) — and, since #543, the players' Names on
  a club's bookings (`users`; its other demand, an On request club's requests and answers,
  went with On request, #669), and since #544
  what happens to a booked game after the fill (`BookedGameChanges`), a paid share given back
  (`SeatRefunds`, and since #641 a late leaver told the figure) and, since #641 in place of
  the estimate's `CardFees`, what a leaver after the cut-off would get back (`LateRefunds`)
  — and since #545 a pool's rescues
  (`PlayerBookings.rescues_in`), a seat taken or declined, and a seat-taken refund — and since
  #546 the pair rule and a player's level window (`PlayerFit` — since #661 with the
  reliability filter, and every kind over one reading) and each member's Level, week,
  gender and preference (`PlayersInPlay`) — and since #547 the club's bookings as its desk
  reads and runs them (`ClubBookings` — since #672 with the cancel's preview and a move by
  cancel), what each took and gave back (`BookingTakings`), the
  group each pool is (`PoolOrigins`) — `DeskCheckIns`, whether a club checked players in,
  went with desk check-in (#651) — and since #639 the shares checked at the fill and held
  at their Holding time (`CheckedShares`, registered over a fresh fake: what is due and a
  holding of nothing ask the provider nothing), a refused holding kept or let go
  (`CardsToFix`), when a checked
  share is held (`HoldingTimes`), and a refused holding's time to fix the card on the booked
  game (`BookedGameChanges`' card methods) — and since #640 a seat kept for a refused rescuer,
  taken or run out once (`BookedGameChanges`' keep methods).
  And since #750 the pair rule's block mask alone (`PlayerFit.blocked_pairs`) and
  **`CourtHours`**, every hour a club sells with its free courts named in the club's order
  (`ClubCourtHours`) — the first of the proposer's ports to get its row.
  And since #751 a friends game booked at send, its invited seats answered and called off
  by its sender (`FriendsGameBookings`) and each cover taken or let go at the cut-off
  (`CoversAtTheCutOff`); the sender's court held at send (`SendersCourts`) asks the
  provider and is contracted over HTTP with the fake.
  The rest of the deck's, the proposer's and the fill's ports (#538–#541) were contracted
  over HTTP only and are owed rows there.
  **The eleventh, `booking_demands.py`, is Bookings' consumer register** (#543): the first
  free court of a club at an hour with its cut-off — and every free court, each with its
  kind (#671) and its share, which a club's cancel asks before a court absorbs it (#672) —
  the court a club's cancel closes for its hour (`CourtClosures`, #673), and a club's desk —
  all the Club context's facts — and the Games context's: the ordinary Game a booking opens
  (`GameOpening`, #541, registered by #544), what leaving, a rescue, the cut-off and the
  club's cancel do to it (`GameChanges`, #544, #545, #547). Who Didn't come to it
  (`GameNoShows`, #547, #657) went with #659: a *Didn't come* is priced once, on *shows up*,
  so *keeps plans* no longer asks. **`game_demands.py` gained its third row with #547**: who the club's desk
  checked in (`ClubCheckIns`), the booking's fact a no-show report asked first — signed by
  `bookings`; it went with desk check-in (#651). **Its second row now is `GameClubs`**
  (#657): where a booked game's club is — its name and map point, and how far a position is
  from it in great-circle metres — signed by `bookings` (`BookedGameClubs`), so an attendance
  tap is measured against the place the game is played.
  **The twelfth, `bookings_demands.py`, is what Bookings publishes** (#544), beside its
  consumer register as `games_demands.py` stands beside `game_demands.py`: who kept the booked
  games they held a seat on (`BookingHistoryQuery`), *keeps plans*' input.
  **The thirteenth, `payment_demands.py`, is Payments' consumer register** (#548), apart from
  `payments_demands.py`'s two provider adapters: which games are over for good, so their money
  is the club's to be paid out (`GamesOver`, signed by `proposals`). Its older demands —
  `Sellers`, `Payers`, `PaymentCommitments` — were contracted over HTTP only and are owed rows.
  **The fourteenth, `push_demands.py`, is the second of `payments_demands.py`'s kind** (#549):
  the two adapters of the push port — the recording service every API test reads, and Expo,
  asked over a loopback server speaking Expo's documented push API, never Expo itself.
  **The fifteenth, `notification_demands.py`, is Notifications' consumer register**
  (#549): a game as it stands (`GameBriefs`), whose deck shows a card and, since #673, the
  kind of court it promises (`Decks`), what a refund gave back (`PaidShares`), who an
  open seat is offered to (`SeatOffers`) and what a person and a club are called (`Names`) —
  and since #663 a booked game's court, asked of the Game (`GameCourts`), and the booked hours
  just ended, off the bookings' projection (`EndedHours`) — and since #727 when each account
  first joined a group it is in now, off the groups' own directory (`GroupJoiners`), and who
  holds a rating, off rating's published read (`RatedAccounts`).
  Notifications is told and tells nothing, so like a conversation it publishes no port.
  **Friends' lent relations are rows in three registers** (#745; `friends.md`): the record's
  twelfth demand `RelationsOfTheReader`; Proposals' `ReaderRelations` (the faces' *friend* tag and
  the result's *PLAYED WITH*), `FriendRequestsOnHome` (Home's row, whose cards are driven over
  HTTP — a card needs a named account) and, since #764, `LevelAsksOnHome` (Home's asks for a
  level, its accounts registered over the suite's `client`); and Notifications' `Friendships`
  (since #764 with `level_asks_on`, the asks the bell keeps a *level asked* row by). Friends publishes no
  register of its own: every port onto it is a reader's, signed on the reader's side.
  `tests/demands/friends_world.py` arranges the friendships and blocks through their aggregates.
  **The sixteenth, `player_profile_demands.py`, is the Player profile's consumer register**
  (#726): where a club is (`ClubPoints`), for a Location area picked as a club in place of a
  reading ([ADR-0200](../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §10) —
  signed by `clubs` over its own directory (`DirectoryClubPoints`), the point as precise as
  the desk dropped it and nothing for an id that names no club. The profile's photo ports are
  the outside world's and are not demands on a context.
  **The seventeenth, `ranking_demands.py`, is Rankings' consumer register** (#768;
  `rankings.md`): the rating's record every row is folded from (`RatingHistories`, over the
  rating's own streams), the faces (`RankedFaces`), a level held, read live
  (`SportLevels`), and since #771 the reader's friends (`ReadersFriends`, over Friends'
  own read, its friendships arranged through `tests/demands/friends_world.py`). Home's
  trophy is a row in Proposals' register, `RankingOnHome` (the tenth's twenty-fourth).
  **The eighteenth, `general_order_demands.py`, is the third of `payments_demands.py`'s
  kind** (#770; `rankings.md`): the two adapters of the kept General orders — Redis's, as
  the composition root wraps it, over the suite's fake server, and the in-memory equivalent
  every test, a seed run and the rebuild read through — so an in-memory store that drifts
  from Redis's goes red.
  **A row carries a builder, and not always over a bare session.** Most build over a
  session; `payments_demands.py`'s and `push_demands.py`'s build over the settings, and
  `general_order_demands.py`'s over a Redis client.
  `game_demands.py` builds over the session alone since the game's pairing is read side
  against side from the people's Levels (#575), and **no test in this repository needs
  Redis running**.
