---
paths:
  - "app/modules/player_record/**"
---

# The player record

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A record is read through a prior disclosure, and the refusal names nothing**
  ([ADR-0159](../../../docs/adr/0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)).
  `app/modules/player_record/` is the ninth context and the second that keeps **no record
  at all** — no aggregate, no table, no migration, and a structural test that walks the
  package for an ORM import and the migrations for a table named after it. What separates
  it from `player_score` is that it also **enforces admission**, and that is the whole of
  what it decides for itself. Four things are load-bearing. **A record opens on a prior
  disclosure and never on a person**: you are the subject, you **played together** (were on
  one court), you **share a group**, or you **run a group they are in** (#575) — otherwise a
  route taking a player id is a player-enumeration endpoint, and a UUID being hard to guess is
  not an authorization model. A search that showed them and a challenge you share stopped
  being disclosures with #575, and the challenges are gone (#578). Each
  strand is a `PriorDisclosure` answering **yes or no** (`GamesTheyPlayed`, `GroupsTheyShare`,
  `GroupsTheReaderRuns`), asked in turn and stopped at the first yes. A game discloses for as
  long as the pair are both on its court, played or not; a group is membership as it stands. **The gates run live**: the two about accounts
  — the subject's hold, an account that may not be shown — through `matchmaking`'s
  `AccountGates`, plus the reader's **own** hold, because a hold points both ways. **A block
  is no gate, in either direction**
  ([ADR-0193](../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §2, #586): the blocker opens the record to undo it, and the blocked person reads the
  blocker's record byte for byte as before. What the record says of a block is the
  **reader's own** — `blocked_by_you`, asked once admitted through the tenth demand,
  `BlocksByTheReader` (`OwnBlocksOfTheReader`, over `BlockQuery.blocks_made_by` with the
  reader as the blocker), a fact on the sheet that refuses nothing and is `false` on your own
  record; nothing on any port can answer *did they block me* (§3). It is the one demand
  here that **stands down rather than raising**: an unreadable block state omits
  `blocked_by_you` and takes no record down (ADR-0193, Consequences). **No gender preference is asked of any strand**: a preference says who a player is
  willing to be *matched* with, and every strand here already put the pair in front of each
  other (#575; it had been dropped for whoever runs the group by ADR-0159's 2026-10-02
  amendment, #566).
  **Your own record has no gates at all** and is a *second use case* rather than a branch, so
  the screen that tells a player how they appear cannot be taken down by the gate machinery.
  **The refusals are one refusal, byte for byte** — never disclosed, held and no such player
  are one `404` with one body, asserted as a sameness rather than as three statuses. And **this context declares its own ports and its
  own types**: it borrows nothing from another context's domain, held by an `.importlinter`
  contract rather than a test, because an application layer importing `CardIdentity` would
  read as sensible reuse in the diff and nothing would go red. The cost is a second
  spelling of four words — `OnCourtVerdict` beside `PhotoReviewDecision`, `GameOutcome`
  beside `games`' `Outcome` — and their agreement is asserted, the way `games` asserts its
  two bounds against each other; the same rule reaches the **wire**, where
  `RecordLikelyRangeSchema` is named for its surface because a second `LikelyRangeSchema`
  would not shadow the card's, it would rename it.
  **`?sport=` says what the sheet is about and never who may be seen** — it reaches the
  assembler and never the admission, so naming a sport changes what is drawn and nothing
  about whether it is drawn. Resolving it is the one rule
  this context owns (`domain/sport_choice.py`): the sport asked for where they hold a
  rating in it, otherwise their **most counted** — never their highest Level, which would
  make the header a boast, and never their most recent, which is activity recency wearing a
  sport's name — ties broken by the sport registry's own order, and `None` for somebody
  rated in nothing, whose sheet draws pills and no skill card. Registry order is
  **structural**: both functions walk `Sport` and look the mapping up rather than iterating
  a mapping and sorting after (ADR-0105). **`counted_games` on the skill card is not the
  card's number under the same word** — it is `SkillRating`'s own applied-games count, per
  sport, *what this certainty rests on*, so it comes off the same stream as the Level and
  moves in step with it; the player card's is *how much have they played*, over every sport,
  and counts an evening nobody agreed a score for. Two provider ports widened for it:
  `rating`'s **read** port gained `ratings_of` (one player, every sport — never the
  repository, which remembers stream versions), and `games` gained `recent_results_in` as a
  **second method rather than a parameter**, because the set read is frozen into search
  records kept for ever and because this one filters on the sport *before* it trims to five.
  **Opponent variety is the third fact to arrive, and it is a *separate port* on `games`
  rather than a sixth method on that one** (#380). The fold is deliberately **unbounded** —
  that is what makes it a career statistic, and a window here would be a second horizon that
  must not disagree with the matcher's — so an unbounded fold on the port a search already
  holds is one somebody eventually calls inside the walk over five hundred candidates. It
  answers about **one player and never a collection**, the fence is the signature, and both
  sides of the seam assert their own. What crosses is the **raw pair and no percentage**: a
  bare share would hide whether *70 %* is fourteen of twenty or seven of ten, which is the
  argument the reliability counts beside it print *12 of 13* for, and the division is a
  client's. Absence is the same absence everything else here spells — no counted game means
  the row is **omitted**, never `0` and never `0 / 0` — and it is a *different* absence from
  `skill`'s, so the assembler asks for it whatever sport resolved. Which games count is
  `games`' own predicate (`_counted_and_played`), written once and read by both halves of the
  pair, so the sheet cannot print two ideas of a counted game.
  **Player reliability is the fourth fact, and it is `player_score`'s figure put on a wire
  whole** (#381, #383, then #659). Since ADR-0195 §1 it is **points, the band, *New* and four
  counts** — `reliability.{player_score, band, is_new, turned_up, turned_up_of, late, kept,
  kept_of, left_in_dispute}` — every one copied from `PlayerScore` by
  `ScoreSubjectReliability` and none derived here: the band is the engine's floors, *New*
  reads every game ever played through, and a second derivation would be a second place for
  the number a player reads about themselves to be true. The strand rows, their raw pairs,
  their `pct` and `ReliabilityStrand` left the domain, the shape and the emitted document with
  the strands. **It is never absent now**: everyone starts at a hundred, so somebody nothing
  has happened to reads *100 · New* with every count at nought, `PlayerRecord.reliability`
  is not optional and `SubjectReliability.reliability_of` never answers `None` — the third
  absence this sheet used to spell is gone, and sportsmanship's is now the third.
  `SubjectReliability` is the eighth demand and the **first here whose provider reads a set**
  — `PublishedScoreQuery` answers about a whole group's members for the Members list, and
  the narrowing to one person is the adapter's, which is the mirror of variety's fence.
  `ReliabilityBand` and its floors are the names this context imports rather than respells:
  the engines are the pure layer every context reads and none owns, and the band is on the
  player contract under that spelling on the record and on Members alike.
  **The reader's own reliability filter rides on the figure, and only on your own record**
  (#661; ADR-0195 §6): `reliability.filter` — `minimum` (omitted while it is off), `hides` of
  `of` (everybody else in every group the reader is in, each counted once; never somebody
  New) and, while somebody's filter in their groups keeps them off a court,
  `back_with_everyone` (`band`, `points`) — the **highest** of those minimums, whose floor
  clears every one of them at once (a call made without a ruling: the ticket's *the lowest band
  floor among those filters* would make *at 50 you're dealt with everyone again* false for a
  Low player below both a Medium and a High filter). It is the eleventh demand,
  `ReliabilityFilters` (`FiltersInTheGroups`, over `GroupDirectory`, each member's Player
  profile and `PublishedScoreQuery`, asking no points while nobody filters), and **`ReadOwnRecord`
  alone holds it** — attached to the assembled panel, so `ReadPlayerRecord` has no such
  collaborator and nobody's filter can reach a stranger's sheet. It **names nobody**: two
  counts and a band. Who a filter hides is the engine's `passes_reliability_minimum`, the
  clause `proposals`' pair rule asks, so the sheet cannot count a player the deck would deal.
  **What other players said is the fifth fact, and it no longer depends on who is
  reading** (#382, then #468). It was the one zone that did — the figure and its count for
  a reader, a **coarse band and neither** for the person it is about, split on the **port**
  so the sheet about you asked a question with no figure in its answer, and `PlayerRecord`
  refusing the pair beside `is_self`. Since
  [ADR-0179](../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  §5 the figure crosses to its subject exactly as `GET /players/{id}/record` serves it to
  a reader — `sportsmanship.{average, raters}` on `GET /players/me/record`,
  `sportsmanship_band` retired from the domain, the shape and the emitted document, `band_for`
  gone from both ports, the invariant gone with the field it guarded, and `is_self` back to
  deciding a title and nothing on the sheet. The cost — a rater becomes nameable by their
  subject — is accepted by name in that record's Consequences and is not restated here.
  It takes **neither a sport nor an instant**, the only demand here that
  takes neither: nothing decays, because the window is fifty *people* and not fifty days.
  Its absence is the **third** (the fourth until #659), asking its own question — rating is a favour, ignoring a
  card costs nothing, and nothing records the omission, so a nought would publish a verdict
  nobody gave. The matcher reads none of it, held by an `.importlinter` contract, and a
  test walks the emitted contract to prove the words reach exactly one response type — and
  that the band's field is on none — which
  is where *it is not on search result cards* stopped being a promise.
