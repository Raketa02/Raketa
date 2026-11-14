---
paths:
  - "app/modules/discovery/**"
  - "app/bootstrap/discovery_demands.py"
  - "app/seeds/new_in_raketa.py"
  - "migrations/versions/0073_player_directory.py"
---

# Discovery

Decisions that are load-bearing and not obvious from the code (#793;
[ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§5, §9, §10; `docs/specs/home-rows/` §4.6, §7, §12, §16). The words are root `CONTEXT.md`'s
*Discovery* section and the words §31.7, §31.10.

- **The people rows' context, with no aggregate and no event of its own** — it registers nothing
  in the catalog. It owns *Same competitive level players*, *New in Raketa* and *Same vibe
  players*, their See all reads and the copies they read. **New in Raketa is built** (#793);
  Same level (#794, with the level projection), Same vibe (#795) and the rest count (#796) read
  the same directory.
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
  the pill and the filter need them all. Bounded by the month's sign-ups; **#794's level
  projection** (indexed by sport) is where that goes, and `LevelsHeld` is the port it swaps
  behind. Not measured against a large crowd yet: that is #794's, with the projection.
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
  (`QueriedBlocksEitherWay`), `LevelsHeld` (`PublishedLevelsHeld`) and `DirectoryFaces`
  (`PresignedDirectoryFaces`). **Its domain and application layers import no other context**
  (`.importlinter`'s *the-discovery-context-declares-its-own-ports*, as the record's): the
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
