---
paths:
  - "app/modules/rankings/**"
  - "app/seeds/rankings.py"
  - "app/seeds/ranking_crowd.py"
  - "app/bootstrap/general_order_demands.py"
  - "app/modules/proposals/infrastructure/rankings.py"
  - "app/bootstrap/ranking_demands.py"
  - "migrations/versions/0068_ranking_rows.py"
  - "migrations/versions/0069_ranking_level_history.py"
  - "app/engines/racketskill/update_v1/rule.py"
---

# Rankings

Decisions that are load-bearing and not obvious from the code (#768, #769, #770, #771;
[ADR-0203](../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md);
`docs/specs/rankings/`). The words are root `CONTEXT.md`'s *Rankings* section.

- **A stored projection, as the stated exception to *derived, never stored*** (ADR-0203
  §10; `backend/CLAUDE.md`). `app/modules/rankings/` is a context with **no aggregate and
  no event of its own** — it registers nothing in the catalog. `ranking_rows` (migration
  0068) holds **one row per player per sport**, made on their first result there: the
  Level in **hundredths** (the ranking compares Levels at the passport's two decimals, so
  5,00 is level with any other 5,00), its σ (which prices one win on the gap line),
  the count of results, when the last settled, when the Level took its current value,
  when the player first entered General (the 5th result) and Friends (the 1st), and the
  last five outcomes oldest first (`W`/`L`). **A result** is a confirmed competitive result
  with a winner — exactly one `rating.moved_on_result` — so a For fun game, *Played · no
  score* and a disputed game never reach it.
- **The row is a fold of the whole rating stream, and the fold is one function**
  (`domain/ranking.py`'s `row_of`). **The move** (`application/projection.py`'s
  `MoveTheRanking`), an outbox subscriber to `rating.moved_on_result` added per delivery run
  over its session (`subscribe_the_ranking_mover`, `app/bootstrap/events.py`), reads the
  player's rating stream (`RatingHistories`) and folds it whole — so **a redelivery changes
  nothing**, an out-of-order delivery writes the row the stream stands at, and **the
  rebuild** (`RebuildTheRankings`, every rating stream in the order they were opened) writes
  what live delivery wrote, row for row. `tests/api/test_rankings.py` holds both. **A row is
  never replaced by one with fewer results** (`SqlAlchemyRankingRows.save`, one `INSERT … ON
  CONFLICT DO UPDATE … WHERE stored.results <= new.results`, so it holds under two
  deliveries at once): results only add up, so a fold that read the stream before another
  delivery's move committed cannot take that move back. **The last result is the latest to
  settle**, not the last in stream order — the catch-up and the outbox may apply two a minute
  apart — and the form is in stream order, as `Outcome`s (`W`/`L` stored). **When the Level was reached** is when it last took its current value —
  the questionnaire's moment if no result has moved it off that since; two partners moved
  by one result reach it at one instant, and the id decides between them.
- **The level history is the same fold, point by point** (#769; `ranking_level_history`,
  migration 0069; `points_of`, and `row_of` is its last point). **One point per stored
  event** (`event_store.id`, carried on `LevelMove.event_id` and `RatingHistory.opened_by`):
  the rating's **opening** (results `0`, the questionnaire's Level) and every result —
  the Level in hundredths, the results by then and when that Level was reached. The opening
  is kept so the history answers *where a player stood at any instant since the rating
  opened*. **The move hands `LevelHistory.append` every point of the stream**, and the
  adapter inserts only the event ids it doesn't hold (`ON CONFLICT DO NOTHING` on the
  event), so a redelivery changes nothing and a store that never had a player's earlier
  points gains them on that player's next result. **No night-time job**: today every server
  process would run one on its own.
- **The rebuild is a command, not a job**: `make rankings-rebuild` (`…-host` from the host)
  runs `python -m app.modules.rankings.infrastructure.rebuild_cli`, owed once to a store
  that held results before the ranking shipped — **and again to one migrated to 0069**, or
  every chip there reads `SAME` until each player's next result — and safe to run again
  (it writes rows and the history's missing points, and reports how many). The seed needs
  none: its outbox drain delivers every move.
- **No account deletion exists to hear** (`users`: *nothing deletes a User*), so ADR-0203's
  *a deleted account's rows go* has no producer yet. The read leaves out a row whose player
  nobody can name — its place kept — and the ticket that adds deletion owes this context a
  subscriber that deletes the account's rows.
- **Who is listed on General**: at least 5 results (`GENERAL_ENTRY`), the last settled
  within `LISTED_FOR` (90 days; listed while `now - last < 90 days`) — the next result puts
  a player straight back, the 5 already met. **The order is the index's**
  (`ix_ranking_rows_order`: sport, hundredths desc, results desc, Level reached asc, player
  id), and every place is unique. **Places are counted over every listed row**: a row the
  read leaves out keeps its place, so the hidden and blocked rows of #772 will leave the same
  gaps.
- **A sport's General order is worked out once and kept for a minute** (#770; ADR-0203 §10;
  `domain/general_order.py`, `application/general_order.py`'s `TheGeneralOrder`). **One
  pass** — `RankingRows.listed(…, then=now − 7 days)`, one statement — reads every listed row
  in place order, **each with its player's level-history point at the chip's instant, for a
  player whose last result settled after it**; a player with no result since stood then
  where they stand now, so their history is never read. `work_out` places every row and
  works every chip out over the set (`chips_of`), and the order is **kept per sport**
  (`GeneralOrders`) with the instant it was worked out. **Fresh is the minute after that
  instant, by the read's own clock** (`ORDER_KEPT_FOR`, `kept_fresh`) — so who dropped off
  the 90 days, and every chip, is at most a minute old — and **a ranking write forgets its
  sport's order** (`MoveTheRanking` after its save; the rebuild every sport's), so a result
  settling is seen on the next read. **Every forget is counted, and a pass keeps its order
  at the count it began at** (`GeneralOrders.forgotten`, `keep(…, forgotten=)`): an order
  kept at an older count — a slow pass that read the projection before a write and kept
  after the write forgot — **is held by nobody**, so a write is never undone by a pass. What
  that leaves is the forget running inside the delivery's transaction: a pass that begins
  between the forget and the commit reads the old rows at the new count. **So a kept order
  that disagrees with the reader's own row is worked out again**: one missing a reader the
  projection lists now, one placing a reader with no row, and one whose row of the reader
  counts fewer results than they have — a reader never sees their own Level a minute late.
  The one disagreement kept is a placed reader whose 90 days ran out inside the minute. **The card is the order's**: the place, Level, count and chip
  are the order's row (`card_of(…, placed=…)`), so the card and the rows never disagree.
  **The order keeps every listed row and none of the reader's filtering**, so #772's hidden
  and blocked rows are dropped from a slice and leave their gaps.
- **Where it is kept** (`GeneralOrders`, a port onto the outside world, its eighteenth
  register `app/bootstrap/general_order_demands.py`): **Redis in an API process**
  (`RedisGeneralOrders`, built over the process's command pool and **always wrapped**,
  `FailSoftGeneralOrders`), **in memory everywhere else** (`InMemoryGeneralOrders`, one store
  per `build_general_orders_kept_here()` — a seed run, the rebuild's own reads, and **every
  test**: `tests/unit/kept_orders.py` keeps one per test database, so the application a test
  drives and the outbox it drains share it as an API process and its worker share Redis).
  **A kept order is a generation of three keys** — a pointer (`rankings:general:{SPORT}`:
  generation, instant, count), a sorted set of members all at score `0` whose bytes sort as
  General's order (the row's key written fixed-width, then `|` and what the row draws) and a
  hash of player → place — **the pointer swapped last** (`SET … GET`, one pipeline), the
  generation it replaces retired for `_RETIRED_FOR` (10 s) so a read on it finishes, every
  key expiring on its own. **Lossy end to end**: a store that can't answer holds and keeps
  nothing (each read works its order out), and **an order lost under a read**
  (`GeneralOrderLost`, a generation expired mid-read) is worked out again by the read. The
  outbox delivery is handed the store (`create_event_batch_for(…, orders=)`, required, as
  `nudges` and `push` are): the API's worker its Redis; a seed run and a command-line drain
  their own memory, so **an order the API holds after a seed lasts its minute** — the rebuild
  CLI forgets the API's in Redis itself.
- **A page is a slice of the order, named by a cursor** (the screens §5.3):
  `GET /rankings/{sport}/general/rows` (`ReadGeneralPage`) — `after=` a cursor (the 50 rows
  behind it), `before=` one (the 50 above it), `around_me=true` (25 above the reader, 24
  below, held to the list's ends — the first page when they aren't listed), none of them the
  first page, **the main read's own rows**; two at once, or a cursor this server never wrote,
  is `400 not_a_ranking_page`. **A cursor is a row's key** (`OrderKey`: hundredths, results,
  Level reached, player id — opaque, base64url, `schemas.cursor_of`), and *after* it is
  every row strictly behind that key in the order as it stands now, so a row that moved
  between two pages is never shown twice for the rows it passed. Each page answers `listed`,
  `rows` (the main read's row shape, chips and all), and `previous`/`next`: the keys of the
  slice's first and last rows, `null` at the top and bottom — **taken from the slice before
  any row is dropped**, so a reader's filtering never moves a cursor. The main read gained
  `next` (additive). Pages are 50 places, so a page with rows left out holds fewer.
- **Measured at 50,000 listed** (#770; local Postgres 17 and Redis 7.2 in Docker on the
  laptop, the real adapters; 60,000 padel rows — 5,000 short of five results, 5,000 past the
  90 days — and 1,310,767 level-history points, 3,616 players with a result in the 7 days):
  **warm** — the kept order — the main read **36 ms** (57 statements), a page after a cursor
  at place 30,000 **33 ms**, before it **31 ms**, around the reader at 25,000th **26 ms** (52
  statements each), Home's trophy **2.8 ms** (2 statements); **cold** — the first read after
  a write in the sport, or after the minute — the main read **1.2 s**: the pass **590 ms**
  (Postgres 222 ms, the rest decoding 50,000 rows), `work_out` **160 ms**, the keep **330
  ms** (50,000 members and fields, in chunks of 1,000). **A warm read's ranking is Redis
  alone** — the pointer and the forget count in one round trip, the reader's place an
  `HGET`, a slice one `ZRANGE`, a cursor one `ZLEXCOUNT` — and **its SQL is the reader's
  own rows** (the primary key's prefix) **and the faces**: `users` by id for the nicknames,
  then a profile load per face, #768's `ProfileRankedFaces`, which is 50 of the 52 — index
  lookups every one, with no plan worth recording; one question for the page's profiles is
  where a warm read's next 20 ms are. The plan: the listed rows
  a seq scan of `ranking_rows` (7 ms), the movers' points a seq scan of the history hashed
  against the 3,616 (142 ms), sorted per player and numbered (`WindowAgg`, run condition
  `nth <= 1`), hash-joined back and sorted into the order (15 ms). **What it took**: the
  first cut joined every point of the sport (window over 1.31 M points, 893 ms in Postgres)
  and hydrated ORM objects, 3.7 s cold; reading only the movers' history, reading columns,
  and **making `RankingRow`'s, `Chip`'s and the kernel's `instant()` invariants check
  before they format their message** (each formatted `repr` on every call — 1.5 s of it)
  brought it here. **Next lever, not built**: every reader in a process that arrives inside
  a cold work-out runs its own; one work-out per process per sport (single flight), and the
  keep off the reader's path, are where the cold second goes at a busy sport's write rate.
- **`GET /rankings/{sport}?view=GENERAL`** (`ReadRanking`; `view` defaults to `GENERAL`,
  `FRIENDS` below; an unknown sport is `422`): **the card** — `NO_LEVEL`
  first, read live from rating's published read (`SportLevels`), then `NEEDS_RESULTS` with
  the count (fewer than 5, whatever their age), then `OFF_THE_LIST` (5 or more, none in the
  90 days), else `LISTED` with `place`, `of`, `level`, `chip` and `gap_line` — **the podium**, the first three
  rows each with its true place and none with fewer than three, and **the first page of 50
  rows**: place, id, nickname, photo (`RankedFaces`: `users`' nickname, the Player
  profile's first photograph), `form` (`WIN`/`LOSS`, oldest first), `chip`, `level` and
  `is_you` — and `next`, the cursor the second page is read after. The clock is read once,
  and the card, the podium and the rows are one kept order's, so they agree about who
  dropped off.
- **`view=FRIENDS` is the reader and their friends** (#771; the mechanics §4.2; the
  screens §4.6; `application/friends_table.py`'s `TheFriendsTable`): Friends' friend list
  read live through **`ReadersFriends`** (`FriendsReadersFriends`, over Friends'
  `ReadRelations.friends_of` — the reader's side alone, no block read, as `friends_among`),
  then **one pass of the projection over that set alone** — `RankingRows.listed(…,
  at_least=FRIENDS_ENTRY, among={reader, *friends})`, General's own statement with a
  `player_id IN` — so **at least 1 result** (`FRIENDS_ENTRY`), the last within the same 90
  days. **Worked out on each read and kept nowhere** — `work_out(…, view=FRIENDS)` into the
  same `GeneralOrder` shape held in hand (`OrderInHand`), so the card, the podium, the rows
  and the gap line read it exactly as General's. **Places, chips and the gap line are
  counted within the set**: a stranger between two friends is not there to be named or
  passed. **The whole table, never a page** (`next` always `null`; one face question for
  every row). **The card** (`friends_card_of`): with a friend listed, `card_of(…,
  view=FRIENDS)` — `LISTED` with the Friends place, or the reader's own not-listed card above
  the friends' podium and table (Q7): `NO_LEVEL`, `NEEDS_RESULTS` with `results` `0` (*Not
  ranked in padel yet…*) or `OFF_THE_LIST`; **with none, the card is the page** —
  **`JUST_YOU`** when the reader is listed, **`NO_FRIEND_LISTED`** when they aren't either,
  whatever their own state (the PRD's rule, which #767's review kept) — with `rows` and
  `podium` empty and `listed` still counting (`1` or `0`). `results_to_enter` is the view's
  (`RankingView.entry`: 5 or 1). **Friends ignores *Show me in General***; #772's blocks
  will hide rows here too.
- **The chip** (`chips_of`, on every row and the `LISTED` card: `UP`/`DOWN` with `places`,
  `SAME`, `NEW`) compares a place in **today's set**, in today's order, with a place among
  **the same set** ordered by `LevelHistory.points_at(sport, now − 7 days, …)` — each
  player's latest point at or before that instant (most results breaking a tie of
  instants), or, for a player with none by then, their **first** (the opening: a rating
  opened inside the week, so the player is *New*) — **read in the order's own pass, and only
  for players with a result since then** (#770): one with none stood then where they stand
  now, which is also the right answer where two results settled out of stream order before
  then. So an arrival or a departure moves nobody and an overtake moves both — **in Friends
  too, over its own set**: a friend just added stands in today's order and in the week-old
  one, so adding one moves nobody. ***New*** is `now − general_entered_at < 7 days` — in
  Friends `friends_entered_at`, the first result (`RankingRow.entered(view)`); a
  comeback after 90 days reads a real chip, its Level a week ago known. **A listed row with
  no point at all** (a store the rebuild hasn't filled) stands where it stands now — never
  an invariant: it would take every reader's page down.
- **The gap line** (`gap_line` on the `LISTED` card): **the nearest named row above and the
  nearest below** — a row nobody can name is skipped, and #772's hidden and blocked rows
  will be skipped the same way (`ReadRanking._nearest_named`, faces asked only for a row
  off the page). Above: `nickname`, `gap` (two decimals), `wins` and `tied`; below:
  `nickname` and `gap` (`0` reads *level with you*); last place has no below. **First
  place is `top_of_the_list` and nothing else** — *Top of the list* is the whole line (the
  words §30.4), so neither above nor below is sent.
- **One win is how far the engine's own rule moves the reader's Level in an even game**
  (`racketskill/update_v1`'s `even_win`, beside `stakes`; no constant changed): each side
  the sport's own size folded by `one_side` from the reader's own Level and σ — a four as
  the reader and an equal partner against two more of them — the sport's share, and
  **the Level `rating_after` leaves at two decimals**, not the raw stake. The rule rounds
  every new Level, so a padel stake of 0,0149 (σ 0,30) moves it 0,01 and a 0,04 gap takes
  four wins, not three; **a stake under half a hundredth moves nothing** — every settled
  padel player's even win (σ ≤ about 0,15) — so `one_win` is `0` and the count is left
  out rather than promised. `wins_to_close` is the gap over the win in whole hundredths,
  rounded up; 1–5 is returned as is, above `WINS_COUNTED` (5) or with a win of `0`
  `null`, and a tie `tied` with no count. **The backend counts and the client draws**: as
  with *At stake*, nobody else may compute it.
- **Home's trophy** (`GET /home`'s `ranking`, additive): the sport of the reader's **latest
  result in any sport** (`latest_of`: the row with the latest `last_result_at`, ties to the
  sport registry's order) and their General place there, `null` when not listed, **and
  their Friends place there** (#771, `friends_place`: `FriendsRead.place`, `null` when they
  aren't listed among friends **or no friend is** — *Just you so far* is no place); the whole
  field `null` with no result anywhere. Both places are sent because the view the trophy
  shows is the phone's remembered choice (ADR-0188's fourth value), never the server's.
  Proposals reads it through **`RankingOnHome`**, signed in
  `proposals/infrastructure/rankings.py` (`RankingsOnHome`) over `ReadHomeRanking`, with a
  row in `proposal_demands.py`; `.importlinter`'s `rankings-knows-none-of-its-readers`
  keeps every arrow running into `rankings`.
- **Its neighbours are ports in its own words**, signed in `rankings/infrastructure/` and
  contracted in **`app/bootstrap/ranking_demands.py`** (the seventeenth register):
  `RatingHistories` (`RatingStreamHistories`, over the rating's own streams through the
  event store — the opening `rating.rating_initialised` and every move, decoded as rating
  recorded them), `RankedFaces` (`ProfileRankedFaces`), `SportLevels`
  (`RatedSportLevels`, over `RatedPlayerQuery`) and, since #771, `ReadersFriends`
  (`FriendsReadersFriends`, over Friends' `ReadRelations.friends_of` — so `rankings` is on
  `.importlinter`'s *friends-knows-none-of-its-readers*). Blocks both ways and *Show me in
  General* join it with #772. Rankings is on the record's and Notifications' forbidden
  lists: it tells nobody anything (Q10).
- **Seeded by `app/seeds/rankings.py`**: `RANKING_GAMES`, nineteen padel games the runner
  hands the played history beside the cohort's own, so each is a past booked game filled,
  played, scored and accepted through the use cases, and the rooms layer's drain folds every
  row — **and the crowd's** (#770, `app/seeds/ranking_crowd.py`): `RANKING_CROWD`, forty-eight
  padel players **outside the cohort** (so its band histogram and every deck never see
  them), rated by sitting the questionnaire (`seed_the_cohort`, three answer sets with no
  spread — 3,66, 3,74, 3,83), their week **cleared** after the commit
  (`clear_the_week=True`) so the proposer deals none of them, a card each, and `RANKING_CROWD_GAMES`,
  sixty padel games among themselves, five rounds of twelve one a day from 75 days ago, each
  round seating everybody once by a different stride. **Sixty-two are listed** — her,
  thirteen of the cohort and the crowd above them all; she is **56th**, below the first
  page, her five three wins and two losses so her claim's position holds — `cohort-a-12`
  is the beginner with 3, and **nobody plays badminton**. Proven on a fresh Postgres twice,
  the report diffed against the seed without the crowd: only the crowd's cards, games and
  rooms and her ranking line differ. **The played history joins every padel game's people
  to her *Padel na Ogrodach***, so its Members list gains the forty-eight, none of whom the
  proposer deals; and on the Stripe sandbox the crowd's forty-eight cards and 240 seat
  charges are Stripe's to take, which lengthens a sandbox run. Who may play is narrow and the module
  says why: nobody with a record fixture's count (`cohort-a-05`–`-07`, `-a-13`, `-a-14`,
  `-a-16`), no named account whose claim sits near its band's edge, nobody Advanced (the
  histogram's floor is 2), everybody within the competitive window of everybody, and
  `cohort-a-09`'s *men only* in all-men games. **The fill draws the sides off the Levels
  before any game moved them**, so a loss of hers names whoever it seats across the net.
  **Her Friends table** (#771, `write_her_ranked_friends`, run after both friends layers):
  `HER_FRIENDS` — `cohort-a-11` and `cohort-a-08` above her, `cohort-b-04` and the
  beginner below, **each at least 0,05 from her and from each other** (a seeded Level
  moves a hundredth or two between runs, as the fill draws the sides, and #771's first pick
  of two a hundredth apart swapped) — each ask her from *Padel na Ogrodach* and
  she accepts, through `AskToBeFriends` and `AcceptFriendRequest`, asked only while nothing
  stands between them; so *said yes* is told to them and her bell is untouched, and the
  friends layer's own claim on her two named friends still holds (it reads the named
  accounts alone). She reads **3rd of 5**, with a podium, the beginner listed among friends
  from their first result and short of General. **The beginner also played her at tennis**,
  so her tennis Friends table is the two of them and Home's trophy reads `friends_place` `1`
  there. `assert_the_ranking` fails the run by name unless more than a page is listed, she is
  listed below the first page and not last, the page around her (`ReadGeneralPage`) holds
  her, the beginner reads *needs results* with 2–4, badminton lists nobody, and her Friends
  view is `LISTED` with at least three friends and a podium. **Her
  trophy reads tennis**: her evenings are her latest results.
