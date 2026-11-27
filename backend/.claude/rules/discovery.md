---
paths:
  - "app/modules/discovery/**"
  - "app/bootstrap/discovery_demands.py"
  - "app/seeds/new_in_rakieta.py"
  - "app/seeds/same_level.py"
  - "app/seeds/same_vibe.py"
  - "migrations/versions/0073_player_directory.py"
  - "migrations/versions/0074_discovery_levels.py"
  - "migrations/versions/0075_discovery_rest_counts.py"
---

# Discovery

Decisions that are load-bearing and not obvious from the code (#793, #794, #795, #796, #812;
[ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§4–§7, §9, §10; [ADR-0205](../../../docs/adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)
§6; `docs/specs/home-rows/` §4.6, §6–§9, §12, §16). The words are root
`CONTEXT.md`'s *Discovery* section and the words §31.5–§31.8, §31.10.

- **The people rows' context, with no aggregate and no event of its own** — it registers nothing
  in the catalog. It owns *Same competitive level players*, *New in Rakieta* and *Same vibe
  players*, their See all reads and the copies they read. **New in Rakieta** (#793), **Same
  competitive level** (#794, with the current levels), **Same vibe** (#795), **the rest
  count** (#796) and **each row's total** (#812) are built.
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
  did — `tests/api/test_new_in_rakieta.py` holds it, twice. A new field a row reads is a new
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
  glossary's 14-day **Newcomer** (root `CONTEXT.md` › Discovery › *New in Rakieta*, _Avoid_) —
  and on the wire a `NewInRakietaPlayerSchema` under `players`.
- **New in Rakieta** (`domain/new_in_rakieta.py`, `application/new_in_rakieta.py`):
  `GET /new-in-rakieta` and `GET /new-in-rakieta/all?sport&after` (player surface). **New is
  strictly the last 30 days** (`NEW_FOR`): `now − joined < 30 days`, so a player who joined
  exactly 30 days ago is out. **The row is the 10 newest, then ordered** — the unconnected
  first (an `ASKED_YOU` among them, call 7), then `SENT`, then `FRIEND`, newest first within
  each (`on_the_row`) — so a friend among the 10 newest waits at the back, and an 11th
  sign-up pushes the oldest off. **Newest first** is *joined* descending, then the player id.
  **See all** is everybody, newest first, friends where they fall, in pages of 20 (`A_PAGE`):
  the cursor (`after`, `next`) is the last card's key (*joined* in microseconds and the id,
  base64url), and a page is everybody strictly behind it as the list stands now, so a sign-up
  between two pages moves nothing; a cursor this server never wrote is `400
  not_a_new_in_rakieta_page`. With `sport`, only joiners holding a level in it; `sports` is every
  sport at least one joiner holds a level in, whatever the filter. **`days_since_joined` is
  Warsaw days** (call 8) — the phone words it (*Joined today* … *Joined 4 weeks ago*, the words
  §31.7). Each card: id, nickname, first photo and its link, `joined_at`, every sport with a
  level and the Level (`LevelsHeld`, over rating's published read), and the reader's
  `relation` as `FriendRelation` — **no request id**: every friends route names a request by
  the other player's id (a call made by #793, against the PRD's *pending request id*).
- **See all reads every joiner's levels** — one stream load per joiner and sport — because
  the pill and the filter need them all. Bounded by the month's sign-ups, and still live:
  `LevelsHeld` is the port the current levels (below) can swap behind, a call #794 left —
  New in Rakieta's tests file their levels straight on the log, which the projection never
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
- **Seeded by `app/seeds/new_in_rakieta.py`**, after the friends and Hottest groups layers:
  `JOINERS`, eight players **outside the cohort** written by `seed_the_cohort` on the clock
  their row names — joined today with no level, yesterday (padel, badminton; **she asked them
  from the row**, so their Home reads *Found you among new players*), 2 days ago (padel; **asked
  her**), 4 days ago (no level; **her friend**), 9, 16 and 23 days ago (tennis, nothing,
  squash) and **35 days ago, out** — in no group, so nobody deals them. Her relations go through
  the friends' use cases, each pair read first. `assert_new_in_rakieta` reads her row and every
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
  best first, ten in all — a rested player among the gaps (#796, below). **See all** is the
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
- **Seeded by `app/seeds/same_level.py`**, after New in Rakieta: **no player of its own** —
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
- **Keeping a row alive is one rule for both rows** (`domain/fresh_then_gaps.py`, #795; the
  mechanics §9.1): `FreshThenGaps` takes the cards best first and is full once ten are fresh
  or once a card that is no good match has come with ten taken; it is built with the row's own
  **good match** (`good`). Each row's `RowOfTen` is it with its line — Same competitive
  level's `is_good_match` (≥ 70%), Same vibe's (≥ 2 shared tags) — and each row's `is_fresh`
  asks the same rule with that line; everything else is §9's.
- **Same vibe players** (#795; `domain/same_vibe.py`, `application/same_vibe.py`):
  `GET /same-vibe` and `GET /same-vibe/all?sport&after` (player surface). **Anyone sharing a
  Social tag with the reader**; every tag counts the same and **skill plays no part**, so a
  reader with no level sees it too (Q14) and no level is read but See all's sport. **The vibe
  %** is 1 − ½ⁿ for n shared tags, **a half rounded up** (`vibe_percent`: 87,5 reads 88): 50,
  75, 88, 94, 97, 98, and since a player may hold eight (ADR-0207 §7, #829) 99 and 100 — 100
  true, since eight shared are both players' eight. **The order** (`VibeKey`) is more shared first, then **fewer of their
  tags the reader doesn't hold**, then the player id. A person on the row is a `VibePlayer` —
  never a *match* (the glossary's _Avoid_ for the % is *match %*). **The row**: §9's rule, a
  good match **two shared tags or more** (`GOOD_MATCH`), a rested player a gap (#796); it reads
  the order **twenty at a time** (`A_BATCH`), asking Friends once per batch, and stops once
  the row is full — a reader whose friends crowd the top reads a batch more, nobody reads the
  crowd. **See all** is the plain order in pages of 20, the cursor the last card's `VibeKey`
  (in common, not shared, the id, base64url; `400 not_a_same_vibe_page` otherwise, nought in
  common included); with `sport`, only players holding a level in it (an `EXISTS` on the
  current levels); `sports` is every sport somebody listed holds a level in, whatever the
  filter (`sports_alike`, one `DISTINCT`).
- **Shared tags are counted portably in SQL** (`PlayerDirectory.alike`): **one pass over the tag
  rows**, grouped by player — `sum(CASE tag IN the reader's)` *in common*, `count(*)` *held* —
  then ordered and keyset-paged in a derived table **joined back to its players' tags, one
  statement**, so a card's count and its chips come from one snapshot. A scan, not the tag
  index: nearly everybody shares a tag with a reader holding six, and probing the index then
  joining a second count back measured 151 ms against the pass's 62. **The chips are in the
  vocabulary's order**, put there by the adapter, which may read `SOCIAL_TAG_VOCABULARY` (a
  tag it no longer lists stands last); the domain's tags are the directory's sets. **The
  reader's own tags are the directory's too** (`tags_of`), so a tag change — theirs or the
  reader's — reads into the read after its delivery, as every field the follower writes.
  **`tags_of_each` is the same read for many, in one statement** (#830): Proposals' deck reads
  every For-fun table's tags through it (`DirectoryPlayersTags`, ADR-0207 §11), and since
  #835 Games' pairing reads a booked For-fun court's (`DirectoryTagsOnTheCourt`), so the copy
  this context keeps is the one a Social vibe is worked out from, and its lag is theirs too.
- **Measured at 50,000** (#795; Postgres 17 in Docker on the laptop, the real adapters, the
  seeded store plus 50,000 synthetic players written straight into the directory's two tables,
  2–6 tags each at random, 40% with a padel level; her six tags): **the row 53 ms** (5
  statements, one batch), See all's first page 78 ms (6, with the pill), the page after 500
  70 ms, padel alone 69 ms. **No cache** (call 11).
- **Its card on the wire** (`SameVibePlayerSchema`): `vibe_percent`, `in_common`, `shared_tags`
  (the green chips, in the vocabulary's order) and `relation`, **no request id**, as #793's
  call has it. **The vibe sheet reads the record** (all photos, the intro, the distance, every
  tag with *· you too*), which #791 opened to everyone — no route of its own.
- **A request from the row is `made_from` `SAME_VIBE`**, naming **no group and no sport**
  (`Where`'s invariant; `pressed_on` drops either sent). **Its line is counted when read**
  (call 6): the receiver's Home card carries `from_same_vibe` and `in_common` — today's,
  through Proposals' `TagsInCommon` (`ProfileTagsInCommon`, over the Player profile, the tags'
  one owner, live), `0` once nothing is shared (*Found you through your tags*) and `null` on
  every other card; its notice `reason` `FROM_SAME_VIBE` says *6 things in common* (*1 thing in
  common*) through Notifications' own `TagsInCommon` (`ProfileTagsInCommon` in
  `told_by.py`), counted for the notice's reader at push time and on every read. Both ports
  have rows in their context's register.
- **Seeded by `app/seeds/same_vibe.py`**, after Same competitive level: **no player of its
  own** — she holds six tags (`catalog.HER_TAGS`, the protagonists' three and three more where
  the cohort's own draws meet hers at every count: `cohort-a-01` all six, `cohort-a-15` and
  `cohort-d-07` five — re-picked, two of them among ADR-0207's eight, when #832 redrew the
  cohort from all twenty-seven tags), the ranking's crowd shares two, the For-fun deck's four
  five to one, and the New in Rakieta joiners none — and
  **a request each way from the row**, each pair read first: she asks `cohort-a-15`
  (`SHE_ASKS`, five in common) and `cohort-a-01` (`ASKS_HER`, six) asks her. **A store seeded
  before #795** committed her three — and one seeded before #832 her old six — and the commit
  is idempotent, so the layer gives her the six through *Edit tags*' own `ChangeSocialTags`,
  which records nothing once they are hers; the runner does the same for every cohort member
  whose stored tags aren't their row's (`_ensure_the_drawn_tags`, `seeds.md`).
  `assert_same_vibe` reads her row and every See all page among the screens and fails the run
  by name unless the row holds `min(10, See all)`, sits inside See all in the rule's order,
  **every count from one to six is in See all**, a friend shares two tags or more, and — **on
  the run that asked** — the two relations stand. **Her row is all fresh**: far more than ten
  unconnected players share two tags with her, so her friends and her request wait in See all
  and the run says so as a cost; gaps are walked in the API tests.
- **The rest count, the third stated exception** (#796; ADR-0204 §7, §10; the mechanics §9.2;
  `backend/CLAUDE.md`): `discovery_rest_counts` (migration 0075) — **one row per viewer, row
  and player seen** (`row` `SAME_LEVEL` or `SAME_VIBE`, `OnScreenRow`), holding `days`, the
  different Warsaw days the card came on screen, and `last_day`, the last of them. **The
  phone's word, so event-free and with no rebuild** (`domain-events.md`): no stream holds what
  a phone saw, and a phone that never reports rests nobody. **No foreign key** to the
  directory, as the levels have none.
- **`POST /on-screen`** (`ReportOnScreen`, `application/on_screen.py`; player surface,
  `{row, player_ids}`, 1–50 ids (`A_REPORT`), `204` whatever it counted): **one count per card, row and Warsaw day**
  (`day_on_screen`, the request's clock) — one statement, `INSERT … ON CONFLICT DO UPDATE SET
  days = days + 1 … WHERE stored.last_day < new.last_day`, the ids deduplicated and sorted, so
  the same day twice, in one report or two at once, counts once, and a report racing midnight
  can lose a day but never count one twice. **Ignored, with the same answer**: an id the
  directory holds no entry for, the reader, a block either way, *Show me to new people* off,
  an account that doesn't play (`PlayerDirectory.which_may_be_listed`, the rows' own `WHERE`)
  — and **anybody connected** (`counts_toward_rest`, `Relation.connected` — `SENT` or `FRIEND`,
  the glossary's *Connected*, which `is_fresh` reads too — asked of Friends' relations), so a
  day a friend's card or a requested one was on screen never rests them after the friendship
  or the request ends: the mechanics' *without the reader adding them* (a reading, open to the
  PO). Fails closed (`503 block_state_unavailable`), counting nothing, safe to send again. A report names a row and never checks the
  card was on it: a stale card is still a card the phone showed.
- **Five days rest a player in that row** (`RESTS_AFTER`, `has_rested`), and **each row keeps
  its own count**. **Rested is a gap, never hidden**: each row's read asks the count once per
  batch (Same vibe's twenty, Same competitive level's ten), only about the cards that could be
  fresh (`FreshThenGaps.may_be_fresh`: a good match, unconnected) — so today's Same competitive
  level, with no good match, never asks — and hands `rested` to §9's rule, which puts them with
  the friends, the requests sent and the weaker matches, best first. **The count never resets**
  (call 9): a rested player added stays a gap as `SENT` or `FRIEND`, and is still rested when
  the request is cancelled or the friendship removed. **See all rests nobody**, and New in
  Rakieta is never reported. `tests/api/test_rows_stay_alive.py` walks it over HTTP, day by
  day on the request's clock; `tests/unit/test_same_level_widening.py` holds a crowd with rests
  to the brute force.
- **A gone account's rows go on either side** (`RestCount.forget`, by the viewer's key prefix
  and `ix_discovery_rest_counts_player_id`): the directory's follower and its rebuild forget
  them with the entry, in the same transaction (`application/directory.py`). Nothing disables an
  account yet; `tests/unit/test_directory_follower.py` holds the seam, and the API test flips
  the `users` row and runs the real follower.
- **Not seeded**: nothing on the dev store rests, since five reported days can't be walked in one
  run and the seed reports none. A rested card is walked in the API tests.
- **Each row's read answers a `total`** (#812; ADR-0205 §6; `domain/totals.py`): how many the row
  could show — **everybody who qualifies, never its good matches** — under the row's own `WHERE`
  and the reader's blocks, **each person once**, `0` for an empty or hidden row; FOR YOU's line
  count and *See all N ›*. ADR-0205 calls them the rows' *pools*; the code doesn't, since **Pool**
  is the glossary's word for whom a game is dealt to. Additive on the wire
  (`NewInRakietaResponse`, `SameLevelResponse`, `SameVibeResponse`); See all carries none. **Counted
  up to 100** (`COUNTED_UP_TO`, `capped`), because the phone draws *99+* past 99: counting on buys
  nothing on screen and costs a scan of everybody who qualifies. **Each adds at most one statement
  to its row's read, and none scores anybody**:
  - *New in Rakieta*: **the row itself when it came back short of ten** (it is everybody); otherwise
    `how_many_joined`, one count with a `LIMIT 100` inside it (`count_up_to`) on
    `ix_discovery_players_joined_at`'s range.
  - *Same vibe*: **`count(*) OVER ()` on the first batch's page** (`alike(…, counting=True)`,
    `Alike.listed`), over every player the `WHERE` keeps before the `LIMIT` — read from the top,
    so its list is everybody sharing a tag. **Never a second pass**, and a later batch and See all
    don't count: the window holds the whole list before the sort.
  - *Same competitive level*: **what the windows already read** (`_Widening.read`, distinct players)
    once they read everybody (`read_everybody`) or 100; otherwise `how_many_hold`, one count over the
    directory with an `EXISTS` on a level in one of the reader's sports — each player once by
    construction — and a `LIMIT 100` (`count_up_to`). **Never another window**, and nobody's %
    worked out. A row that fills in a near window with fewer than 100 read is the one that counts.
  - **A count never answers fewer than the cards**: it is a later statement, so under READ
    COMMITTED it can see somebody leave whom the row read; each count's answer is
    `max(what the row read, the count)`.
  - **The cap is a `LIMIT 100`, not the ticket's 101**: a 101st row would tell 100 from more than
    100, which an answer capped at 100 never does.
  - **Held by `statements`** (`tests/conftest.py`, any API test's): each row's API test counts the
    statements on the row's own tables, where any total's cost lands (the neighbours' — the session,
    the blocks, Friends, the rating — are the cards', and move with their owners): New in Rakieta
    reads the directory once below ten and twice from ten, the second a count; Same vibe reads the
    tag rows twice, the reader's and the one pass, and See all's pass has no window; Same
    competitive level counts nothing after a drained or hundred-strong read and once, with one
    window read, otherwise. **Each count is walked against every exclusion** where only it could let
    somebody in. `tests/unit/test_same_level_widening.py` holds the total to the brute force, at most
    one count. **The seed** fails each layer unless its total is its See all's length, capped.
  - **Measured at 50,000** (#812; a scratch Postgres 17 in Docker on the laptop, the real adapters,
    50,000 synthetic players written straight into the three tables — 2–6 tags each, padel for all,
    tennis for 40%, squash for 30, about 1,900 new in the month): `how_many_joined` 1.1 ms (5.9 ms
    uncapped, for scale); `how_many_hold` 1.3 ms in padel and tennis and 1.3 ms in squash, where
    only 30 qualify — the planner drives a small sport from its levels, so the count never walks
    the directory; Same vibe's first batch 117 ms counting against 106 ms without, the window's
    whole cost (that store's pass is slower than #795's 62 ms: more tags held). ADR-0205 §6's timing
    of Home on the phone still comes before the branch merges.
