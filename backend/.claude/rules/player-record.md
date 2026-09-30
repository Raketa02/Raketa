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
  what it decides for itself. Five things are load-bearing. **A record opens on a prior
  disclosure and never on a person**: you are the subject, a search of yours *returned*
  them, or you share a live challenge or a game — otherwise a route taking a player id is
  a player-enumeration endpoint, and a UUID being hard to guess is not an authorization
  model. **Nothing expires**, because a search record is kept for ever (ADR-0104) and a
  shorter window could only refuse a face the app is currently showing. **The four
  fail-closed gates run live, in the partition of the disclosure** — never in the sport
  the reader arrived from, since the gender gate reads a candidate index row and the index
  is keyed by sport, so a subject rated only in squash has no padel row and *a gate that
  cannot be evaluated excludes*; that is why `PriorDisclosure` answers in **sports** and
  why the partitions are walked in the sport registry's own order rather than a set's
  (ADR-0105). The reader's **own** hold refuses here too, because a hold points both ways
  and would otherwise end at the one route that remembers what a search already showed —
  while **your own record has no gates at all** and is a *second use case* rather than a
  branch, so the screen that tells a player how they appear cannot be taken down by the
  gate machinery. **The four refusals are one refusal, byte for byte** — never disclosed,
  blocked either way, held and no such player are one `404` with one body, asserted as a
  sameness rather than as four statuses. And **this context declares its own ports and its
  own types**: it borrows nothing from another context's domain, held by an `.importlinter`
  contract rather than a test, because an application layer importing `CardIdentity` would
  read as sensible reuse in the diff and nothing would go red. The cost is a second
  spelling of four words — `OnCourtVerdict` beside `PhotoReviewDecision`, `GameOutcome`
  beside `games`' `Outcome` — and their agreement is asserted, the way `games` asserts its
  two bounds against each other; the same rule reaches the **wire**, where
  `RecordLikelyRangeSchema` is named for its surface because a second `LikelyRangeSchema`
  would not shadow the card's, it would rename it.
  **`?sport=` says what the sheet is about and never who may be seen** — it reaches the
  assembler and never the admission, so naming a sport you were never shown somebody in
  changes what is drawn and nothing about whether it is drawn. Resolving it is the one rule
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
  argument the metered rows beside it print their fractions for, and the division is a
  client's. Absence is the same absence everything else here spells — no counted game means
  the row is **omitted**, never `0` and never `0 / 0` — and it is a *different* absence from
  `skill`'s, so the assembler asks for it whatever sport resolved. Its denominator is
  `counted_games_for`'s own predicate, written once in `games` and read by both, so the sheet
  cannot print a pair that disagrees with the card beside it.
  **The metered rows are the fourth fact, and they are `player_score`'s live strands put
  on a wire for the first time** (#381, and a third of them with #383). Nothing new is
  computed: the raw counts already existed in that domain and the caller stopped throwing
  them away. Each row crosses as **its
  pair and its figure** — and that third number is where a strand parts company with the
  variety beside it: a strand's percentage is what the platform *acts* on, `StrandRatio.value`
  is derived in one place so a card, a profile and the matcher's evidence cannot print three
  roundings of one record, and a client dividing the pair would be the fourth. Variety prices
  no promise, so its division stays the client's. **The weights stay off the wire** — the blend
  arrives already taken, and a row carrying its weight would let a reader re-derive the pill and
  draw one strand as worth more than another. A player with no publishable strand has the
  **whole zone omitted**, a third absence asking a third question: not `skill`'s and not
  `variety`'s, since a plan that dissolved and a seat that ran out are opportunities and
  neither is a game anybody played. `SubjectReliability` is the eighth demand and the **first
  here whose provider reads a set** — `PublishedScoreQuery` answers about five hundred
  candidates for the matcher, and the narrowing to one person is the adapter's, which is the
  mirror of variety's fence. And `ReliabilityStrand` is the one name this context imports
  rather than respells: the engines are the pure layer every context reads and none owns —
  the argument `player_score` already made beside its own import contract — and the codes are
  on the player contract under that spelling already.
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
  Its absence is the **fourth**, asking a fourth question — rating is a favour, ignoring a
  card costs nothing, and nothing records the omission, so a nought would publish a verdict
  nobody gave. The matcher reads none of it, held by an `.importlinter` contract, and a
  test walks the emitted contract to prove the words reach exactly one response type — and
  that the band's field is on none — which
  is where *it is not on search result cards* stopped being a promise.
