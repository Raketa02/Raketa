---
paths:
  - "app/modules/discovery/**"
  - "app/bootstrap/discovery_demands.py"
  - "app/seeds/new_in_raketa.py"
  - "app/seeds/same_level.py"
  - "migrations/versions/0073_player_directory.py"
  - "migrations/versions/0074_discovery_levels.py"
---

# Discovery

Decisions that are load-bearing and not obvious from the code (#793, #794;
[ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§4, §5, §7, §9, §10; `docs/specs/home-rows/` §4.6, §6, §7, §9, §12, §16). The words are root
`CONTEXT.md`'s *Discovery* section and the words §31.5–§31.7, §31.10.

- **The people rows' context, with no aggregate and no event of its own** — it registers nothing
  in the catalog. It owns *Same competitive level players*, *New in Raketa* and *Same vibe
  players*, their See all reads and the copies they read. **New in Raketa** (#793) and **Same
  competitive level** (#794, with the current levels) are built; Same vibe (#795) and the rest
  count (#796) read the same directory.
- **The player directory, a stated exception to *derived, never stored*** (ADR-0204 §10;
  `backend/CLAUDE.md`): `discovery_players` (migration 0073) — **one row per account**: the
  nickname (`users`), and, once it holds a Player profile, `plays` with the profile's *joined*
  (`created_at`, the commit that ends onboarding — the moment a **Newcomer**'s 14 days run
  from; earlier players keep their real date), first photo, area cell (the Location area's two
  decimals, **never served**), *Show me to new people* — and `discovery_player_tags`, **one row
  per tag**, so #795 counts shared tags in SQL by a join. **An account plays once it holds a
  Player profile**: an administrator-only account never commits one, so it has a row and is on
  no list.
- **An entry is written whole from what the owners hold now** (`application/directory.py`):
  the follower, an outbox subscriber added per delivery run over its session
  (`subscribe_the_directory_follower`, `app/bootstrap/events.py`), hears every event that moves
  an entry — `users.user_registered`, `…account_opened_by_invitation`, `…user_named`,
  `…user_disabled`; `player_profile.created`, `…social_tags_changed`, `…photos_changed`,
  `…location_changed`, `…show_me_to_new_people_set` and the decode-only
  `…ranking_visibility_set` (`FOLLOWED`) — and **asks the owners again** (`DirectorySources`:
  the `users` row, the profile's stream) rather than applying the event, so a redelivery
  writes the same rows, a delivery out of order writes what the owners hold, and **the
  rebuild** (`RebuildTheDirectory`, every User stream oldest first) writes what live delivery
  did — `tests/api/test_new_in_raketa.py` holds it, twice. A new field a row reads is a new
  event in `FOLLOWED` too. **An account the owners no longer know is forgotten** — no active
  `users` row, today only a disabled one (nothing disables an account yet:
  `tests/unit/test_directory_follower.py` holds the seam) — with its tags.
- **The rebuild is a command, not a job**: `make discovery-rebuild` (`…-host` from the host)
  runs `python -m app.modules.discovery.infrastructure.rebuild_cli`, **owed once to every store
  migrated to 0073** (the tables are created empty) and safe to run again. The seed needs
  none: its drains deliver every event.
- **Who is never on a people row** (ADR-0204 §10, the mechanics §4.6): the reader, everybody
  the reader blocked or who blocked the reader (`BlocksEitherWay`, over `BlockQuery`'s
  `exclusions_for` — one flat set, failing closed with `503 block_state_unavailable`),
  players with *Show me to new people* off, accounts that don't play, and accounts that are
  gone. The directory's `who_joined` holds the last three in its `WHERE` (named, `plays`, the
  switch on); the reader and the blocks are handed to it as one `NOT IN`. **The switch is
  followed through the outbox** here, unlike the record's admission, which reads it live: a
  player who turns it off leaves the rows on the read after the delivery (call 12).
- **One person on the row is a `Joiner`** in the code — never a *newcomer*, which is the
  glossary's 14-day **Newcomer** (root `CONTEXT.md` › Discovery › *New in Raketa*, _Avoid_) —
  and on the wire a `NewInRaketaPlayerSchema` under `players`.
- **New in Raketa** (`domain/new_in_raketa.py`, `application/new_in_raketa.py`):
  `GET /new-in-raketa` and `GET /new-in-raketa/all?sport&after` (player surface). **New is
  strictly the last 30 days** (`NEW_FOR`): `now − joined < 30 days`, so a player who joined
  exactly 30 days ago is out. **The row is the 10 newest, then ordered** — the unconnected
  first (an `ASKED_YOU` among them, call 7), then `SENT`, then `FRIEND`, newest first within
  each (`on_the_row`) — so a friend among the 10 newest waits at the back, and an 11th
  sign-up pushes the oldest off. **Newest first** is *joined* descending, then the player id.
  **See all** is everybody, newest first, friends where they fall, in pages of 20 (`A_PAGE`):
  the cursor (`after`, `next`) is the last card's key (*joined* in microseconds and the id,
  base64url), and a page is everybody strictly behind it as the list stands now, so a sign-up
  between two pages moves nothing; a cursor this server never wrote is `400
  not_a_new_in_raketa_page`. With `sport`, only joiners holding a level in it; `sports` is every
  sport at least one joiner holds a level in, whatever the filter. **`days_since_joined` is
  Warsaw days** (call 8) — the phone words it (*Joined today* … *Joined 4 weeks ago*, the words
  §31.7). Each card: id, nickname, first photo and its link, `joined_at`, every sport with a
  level and the Level (`LevelsHeld`, over rating's published read), and the reader's
  `relation` as `FriendRelation` — **no request id**: every friends route names a request by
  the other player's id (a call made by #793, against the PRD's *pending request id*).
- **See all reads every joiner's levels** — one stream load per joiner and sport — because
  the pill and the filter need them all. Bounded by the month's sign-ups, and still live:
  `LevelsHeld` is the port the current levels (below) can swap behind, a call #794 left —
  New in Raketa's tests file their levels straight on the log, which the projection never
  hears.
- **A request from the row is `made_from` `NEW_PLAYERS`** (Friends' `RequestOrigin`, the
  phone sends it from a record opened from the row too): **no group and no sport**
  (`Where`'s invariant; `pressed_on` drops either sent), since the line names neither (the
  mechanics §12). The receiver's Home card reads
  `from_new_players` (*Found you among new players*, Proposals' `HomeFriendRequest`) and its
  notice `reason` `FROM_NEW_PLAYERS` with that body (`notifications/application/words.py`).
- **Its neighbours are ports in its own words** (`domain/ports.py`), signed in
  `discovery/infrastructure/` and contracted in **`app/bootstrap/discovery_demands.py`** (the
  nineteenth register): `DirectorySources` (`AccountDirectorySources`), `ReadersRelations`
  (`FriendsReadersRelations`, over Friends' `ReadRelations` — so `discovery` is on
  `.importlinter`'s *friends-knows-none-of-its-readers*), `BlocksEitherWay`
  (`QueriedBlocksEitherWay`), `LevelsHeld` (`PublishedLevelsHeld`), `DirectoryFaces`
  (`PresignedDirectoryFaces`), and since #794 `LevelSources` (`RatingStreamLevels`, over
  the rating's own streams) and `HowEven` (`MatcherHowEven`, over the matcher's forecast).
  **Its domain and application layers import no other context** (`.importlinter`'s *the-discovery-context-declares-its-own-ports*, as the record's): the
  reader's relation is spelled `Relation` here, held equal to `FriendRelation` by
  `tests/unit/test_discovery_relation.py`, and the owners' events are read in
  `infrastructure/event_subscriptions.py`. It tells nobody anything (the mechanics §14), so it
  is on Notifications' forbidden list.
- **Seeded by `app/seeds/new_in_raketa.py`**, after the friends and Hottest groups layers:
  `JOINERS`, eight players **outside the cohort** written by `seed_the_cohort` on the clock
  their row names — joined today with no level, yesterday (padel, badminton; **she asked them
  from the row**, so their Home reads *Found you among new players*), 2 days ago (padel; **asked
  her**), 4 days ago (no level; **her friend**), 9, 16 and 23 days ago (tennis, nothing,
  squash) and **35 days ago, out** — in no group, so nobody deals them. Her relations go through
  the friends' use cases, each pair read first. `assert_new_in_raketa` reads her row and every
  See all page among the screens and fails the run by name unless the 35-day one is out, the
  row is in order, its cards are in See all and it holds 10 whenever See all holds more — and,
  **on the run that wrote them**, the four relations on her row and the tennis filter. The
  friends layer's Home claim reads the named accounts alone, since this layer's joiner asks
  her too.
- **The current levels, the second stated exception** (#794; ADR-0204 §10;
  `backend/CLAUDE.md`): `discovery_levels` (migration 0074) — **one row per player and sport
  with a level**, the questionnaire's alone included (what a newcomer has, and what the
  ranking's rows, made on a first result, can't serve): the Level (μ), its Uncertainty (σ),
  **the band the rating published with it** (name and edges, never `band_for` here — the
  comparison bar bolds the reader's) and how many results moved it.
  `ix_discovery_levels_sport_mu` serves the windows below, `ix_discovery_levels_sport_sigma`
  the least Uncertainty in a sport (`least_doubt`, one `min` per sport). **No foreign key to the
  directory**: a level may arrive before its account's entry, and every read joins the two.
  **Written as the directory is** (`application/levels.py`): the follower
  (`subscribe_the_level_follower`, per delivery run) hears `rating.rating_initialised` and
  `rating.moved_on_result` (`LEVELS_FOLLOWED`) and **asks the stream again**
  (`LevelSources`, `RatingStreamLevels`: the last of the two events, the results counted —
  no rating is ever closed, so nothing is forgotten);
  **a save keeps the fold with the most results** (`ON CONFLICT … WHERE stored.results <=
  new.results`, as the ranking's rows), so a fold read before another delivery's move
  committed never takes it back; **the rebuild** (`RebuildTheLevels`, every rating stream)
  runs in the same `make discovery-rebuild`, after the directory, **owed once to every store
  migrated to 0074**. `tests/api/test_same_level.py` holds rebuild == live, twice.
- **Same competitive level** (`domain/same_level.py`, `application/same_level.py`):
  `GET /same-level` and `GET /same-level/all?sport&after` (player surface). **Hidden — `[]`,
  and See all `{[], null, []}` — while the reader holds no level anywhere** (Q23). **The %
  even is `HowEven`** (`MatcherHowEven`): `matchmaking/domain/balance.py`'s
  `forecast_the_sides` with **one player a side**, so in padel and badminton the lone player
  is seated twice (the engine's *empty seat matches its partner*) and the figure is the
  singles one — the gap and the pair σ — within the ruleset's 35–96. Arithmetic, a sync
  port. **Every shared sport is compared** (`compared`), most even first, ties to the smaller
  gap then the sport order; **the card shows the evenest** (`same_level_player`), or on See all the
  sport asked, **and keeps every shared sport** for the comparison sheet (`sports`). **Best
  first** is the shown %, then the smaller gap (to a millionth, so 2,83 and 2,59 from 2,71
  are one gap), then the player id (`SameLevelKey`). A person on the row is a
  `SameLevelPlayer` — never a *match*, which the glossary bars for this row (_Avoid_). **The row** (`RowOfTen`): fresh good
  matches first — ≥ 70 (`GOOD_MATCH`), `NONE` or `ASKED_YOU`, not rested — then the gaps,
  best first, ten in all; **nobody rests until #796** (`rested=False`). **See all** is the
  plain order in pages of 20, the cursor the last card's `SameLevelKey` (the %, the gap's
  `repr` and the id, base64url; `400 not_a_same_level_page` otherwise), and `sports` the
  reader's sports somebody on a row holds a level in, whatever the filter
  (`shared_sports`, one `EXISTS` per sport).
- **Read outward in widening windows, never the whole crowd** (`_Widening`, `WINDOWS`:
  0,02 doubling to 2,56, then everybody): each window is one statement for the ring between
  it and the last (`PlayerLevels.near`), every level the ring's players hold in the reader's
  sports beside it, joined to the directory's `WHERE`; and **a window settles every card
  nobody beyond it could come before** (`Reach`): the ceiling is the Forecast for a player
  exactly that far away **as sure as the surest player in the sport** — the % falls with the
  gap and with doubt, and nobody unread is surer than everybody — and a card settles above
  it, or at it while nearer than the width. The row stops once `RowOfTen` is full, asking Friends
  about the settled cards ten at a time (a wide window may settle thousands); a page once it
  holds 21. `tests/unit/test_same_level_widening.py` holds both to the brute force
  over random crowds, launch-like and sure (a ceiling too low, or a least doubt overstated,
  fails it).
- **Measured at 50,000** (#794; Postgres 17 in Docker on the laptop, the real adapters, the
  seeded store plus 50,000 synthetic players written straight into the two tables, padel for
  all and tennis for 40%, Levels normal around 2,8/3,0 with sd 0,6, σ 0,65–0,98 as a launch's
  are; her padel 3,21 σ 0,69, tennis 3,39): **the row 67 ms** (6 statements, one window,
  1,881 candidates), See all's first page 67 ms, the page after 500 134 ms (two windows),
  after 2,000 224 ms (three), tennis alone 34 ms. Bounding a window by a perfect certainty
  instead (σ 0) read three windows and 6,222 candidates for the row, 232 ms — the reason for
  `least_doubt`. **No cache** (call 11): nothing measured asks for one.
- **No pair reaches a good match yet** (a call to raise, #794): with the engine's Uncertainty
  — a questionnaire's ≥ 0,84, five results ≈ 0,67 — two players at one Level with five results
  each read ≈ 69%, so on the seed (and a launch) the row is all gaps, best % first, and *fresh
  before gaps* never fires; the mechanics' 91% assumes σ ≈ 0,13 on both sides. The seed says
  so as a cost. The 70% line and the forecast are the spec's; changing either is the PO's.
- **Its card on the wire** (`SameLevelPlayerSchema`): `shown` and `sports`, each
  `SameLevelSportSchema` — both Levels, `percent_even`, `level_gap` (theirs less the
  reader's, to the hundredth, signed; never `gap`, which is the glossary's place in a row) and
  `your_band` (`LevelBandSchema`) — and `relation`, **no request
  id**, as #793's call has it.
- **Seeded by `app/seeds/same_level.py`**, after New in Raketa: **no player of its own** —
  the cohort already sits around her padel 3,21 and tennis 3,39, with results and on the
  questionnaire alone, her padel friends `cohort-a-08` and `cohort-a-11` among the most even —
  only **a request each way from the row**, in padel, each pair read first: she asks
  `cohort-c-01` (`SHE_ASKS`, six results) and `cohort-b-03` (`ASKS_HER`, padel and tennis on
  the questionnaire, *2 sports ›*) asks her, so both lines are walkable. `assert_same_level`
  reads her row and every See all page among the screens and fails the run by name unless the
  row holds `min(10, See all)`, is in the rule's order, sits inside See all, two friends share
  a sport with her, and — **on the run that asked** — the two relations stand; it counts the
  fresh matches, and none (today's) is a cost line. Proven twice on a fresh Postgres 17.
- **A request from the row is `made_from` `SAME_LEVEL` with the card's sport** (`Where`'s
  invariant: a sport, no group; `pressed_on` drops the group; `422` without a sport). **Its
  line is worked out when read** (call 6): the receiver's Home card carries
  `from_same_level` and `percent_even` — today's, through Proposals' `BalanceForecasts`
  over rating's estimates, the same forecast — `null` once either holds no level there
  (*Found you at your padel level*); its notice `reason` `FROM_SAME_LEVEL` says *Your level
  in padel · 91% even* through Notifications' own `PercentsEven` (`ForecastPercentsEven`),
  drawn for the notice's reader at push time and on every read.
