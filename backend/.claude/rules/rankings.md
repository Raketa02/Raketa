---
paths:
  - "app/modules/rankings/**"
  - "app/seeds/rankings.py"
  - "app/modules/proposals/infrastructure/rankings.py"
  - "app/bootstrap/ranking_demands.py"
  - "migrations/versions/0068_ranking_rows.py"
---

# Rankings

Decisions that are load-bearing and not obvious from the code (#768;
[ADR-0203](../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md);
`docs/specs/rankings/`). The words are root `CONTEXT.md`'s *Rankings* section.

- **A stored projection, as the stated exception to *derived, never stored*** (ADR-0203
  §10; `backend/CLAUDE.md`). `app/modules/rankings/` is a context with **no aggregate and
  no event of its own** — it registers nothing in the catalog. `ranking_rows` (migration
  0068) holds **one row per player per sport**, made on their first result there: the
  Level in **hundredths** (the ranking compares Levels at the passport's two decimals, so
  5,00 is level with any other 5,00), its σ (which prices one win on the gap line, #769),
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
- **The rebuild is a command, not a job**: `make rankings-rebuild` (`…-host` from the host)
  runs `python -m app.modules.rankings.infrastructure.rebuild_cli`, owed once to a store
  that held results before the ranking shipped, and safe to run again. The seed needs none:
  its outbox drain delivers every move.
- **No account deletion exists to hear** (`users`: *nothing deletes a User*), so ADR-0203's
  *a deleted account's rows go* has no producer yet. The read leaves out a row whose player
  nobody can name — its place kept — and the ticket that adds deletion owes this context a
  subscriber that deletes the account's rows.
- **Who is listed on General**: at least 5 results (`GENERAL_ENTRY`), the last settled
  within `LISTED_FOR` (90 days; listed while `now - last < 90 days`) — the next result puts
  a player straight back, the 5 already met. **The order is the index**
  (`ix_ranking_rows_order`: sport, hundredths desc, results desc, Level reached asc, player
  id), and every place is unique. **Places are counted over every listed row**: a row the
  read leaves out keeps its place, so the hidden and blocked rows of #772 will leave the same
  gaps.
- **`GET /rankings/{sport}?view=GENERAL`** (`ReadRanking`; `view` defaults to `GENERAL`,
  and `FRIENDS` arrives with #771; an unknown sport is `422`): **the card** — `NO_LEVEL`
  first, read live from rating's published read (`SportLevels`), then `NEEDS_RESULTS` with
  the count (fewer than 5, whatever their age), then `OFF_THE_LIST` (5 or more, none in the
  90 days), else `LISTED` with `place`, `of` and `level` — **the podium**, the first three
  rows each with its true place and none with fewer than three, and **the first page of 50
  rows**: place, id, nickname, photo (`RankedFaces`: `users`' nickname, the Player
  profile's first photograph), `form` (`WIN`/`LOSS`, oldest first), `level` and `is_you`.
  The clock is read once, so the card, the podium and the rows agree about who dropped off.
  Pages past the first, the Redis cache and the 50,000-player measurement are #770's; the
  chip and the gap line #769's.
- **Home's trophy** (`GET /home`'s `ranking`, additive): the sport of the reader's **latest
  result in any sport** (`latest_of`: the row with the latest `last_result_at`, ties to the
  sport registry's order) and their General place there, `null` when not listed; the whole
  field `null` with no result anywhere. Proposals reads it through **`RankingOnHome`**,
  signed in `proposals/infrastructure/rankings.py` (`RankingsOnHome`) over
  `ReadHomeRanking`, with a row in `proposal_demands.py`; `.importlinter`'s
  `rankings-knows-none-of-its-readers` keeps every arrow running into `rankings`. Friends'
  place on it is #771's.
- **Its neighbours are ports in its own words**, signed in `rankings/infrastructure/` and
  contracted in **`app/bootstrap/ranking_demands.py`** (the seventeenth register):
  `RatingHistories` (`RatingStreamHistories`, over the rating's own streams through the
  event store — the opening `rating.rating_initialised` and every move, decoded as rating
  recorded them), `RankedFaces` (`ProfileRankedFaces`) and `SportLevels`
  (`RatedSportLevels`, over `RatedPlayerQuery`). Friends' friend list, blocks both ways and
  *Show me in General* join it with #771 and #772. Rankings is on the record's and
  Notifications' forbidden lists: it tells nobody anything (Q10).
- **Seeded by `app/seeds/rankings.py`**: `RANKING_GAMES`, nineteen padel games the runner
  hands the played history beside the cohort's own, so each is a past booked game filled,
  played, scored and accepted through the use cases, and the rooms layer's drain folds every
  row. **Fourteen are listed** — her and thirteen of the cohort, her five three wins and two
  losses so her claim's position holds and she sits mid-list — `cohort-a-12` is the
  beginner with 3, and **nobody plays badminton**. Who may play is narrow and the module
  says why: nobody with a record fixture's count (`cohort-a-05`–`-07`, `-a-13`, `-a-14`,
  `-a-16`), no named account whose claim sits near its band's edge, nobody Advanced (the
  histogram's floor is 2), everybody within the competitive window of everybody, and
  `cohort-a-09`'s *men only* in all-men games. **The fill draws the sides off the Levels
  before any game moved them**, so a loss of hers names whoever it seats across the net.
  `assert_the_ranking` fails the run by name unless she is listed off the podium and not
  last, the beginner reads *needs results* with 2–4, and badminton lists nobody. **Her
  trophy reads tennis**: her evenings are her latest results.
