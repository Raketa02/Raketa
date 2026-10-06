---
paths:
  - "app/modules/matchmaking/**"
  - "app/engines/matchfit/**"
  - "scripts/ruleset_diff/**"
  - "scripts/judged_pairings/**"
---

# Matchmaking — the index, the ledgers, interest, the deck, the search record

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **The candidate index tails the log; the outbox delivers side effects**
  ([ADR-0110](../../../docs/adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md),
  [ADR-0111](../../../docs/adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md),
  [ADR-0112](../../../docs/adr/0112-the-snapshot-is-a-per-partition-container-bound-once.md)).
  The platform's first read model, and **the same domain event now has two consumers with
  different guarantees** — hold both in your head. `CandidateIndexTail` reads `event_store`
  by `sequence_no`, takes the one cursor row `FOR UPDATE`, and applies **only the contiguous
  prefix**, because a position is assigned at `INSERT` and not at `COMMIT`. A hole is stepped
  over only once the snapshot horizon proves it permanent — **and never on SQLite**, which has
  neither a horizon nor a concurrent appender, so that path is exercised against Postgres or
  not at all. `DatabaseCandidateSource` holds one immutable container per partition per
  process, refreshes it by copying row references, and calls `gc.freeze()` after every load and
  after every refresh that decoded a row — **not** after one that decoded none, because the
  freeze promotes everything tracked and would otherwise leak whatever was in flight, every two
  seconds, for ever.
  Three rules that outlive the code: **the index holds only facts a player changes about
  themselves** (every live-truth fact travels in the search context instead — a column for one
  would make staleness cost safety); **the partition is derived and there is no shard-key
  field**; and **`rebuild == tail`**, which is why every stamp is the moving event's own
  sequence number and never a batch boundary. Repair is `make rebuild-candidate-index` and
  **there is no admin route** — a walk over `app/api/` and every `presentation/` fails the
  build if one appears. The staleness **ladder** is domain
  (`matchmaking/domain/index_staleness.py`); only the two cadences are configuration.
- **The three lossy ledgers live in Redis, and the gate is the cache — the evidence is
  the row** ([ADR-0093](../../../docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md),
  `the-engine.md` §12). Exposure and suppression are ports in
  `matchmaking/domain/ledgers.py` with TTLs, and the **prompt ledger** — where the two
  loops leave a standing question — is declared in `matchmaking/domain/prompts.py` and
  registered in the same posture table; everything that must survive is a durable row
  elsewhere, and a test at each port says so. **All three fail soft**, which is the opposite of
  the block gate beside them and is deliberate: applying ADR-0095's *a gate that cannot be
  evaluated excludes* to a courtesy would **empty the deck rather than protect anybody**.
  The posture is a wrapper applied in the composition root, so **no unwrapped adapter is
  ever handed out** and `.importlinter` keeps `redis` — and the adapter over it — out of
  every domain and application layer. Neither TTL is configuration: `PASS_SUPPRESS` is in
  the released ruleset and `EXPOSURE_RETENTION_WEEKS` in the domain, and only `REDIS_URL`
  and the loops' cadences are settings. **No test needs Redis** — all three ports have an
  in-memory implementation that `tests/conftest.py` wires for the whole HTTP suite, and the
  Redis adapters are held to the same contract suite against an in-process stand-in.
- **Interest is durable, in the module, and it is the only lift that admits**
  ([ADR-0127](../../../docs/adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md),
  [ADR-0109](../../../docs/adr/0109-a-read-back-names-what-it-withholds.md)). `POST/GET
  /api/v1/interest` and the `interest` table are the first durable ledger in this module
  — a row rather than a Redis key, because a person reached out to a person and that is
  the one thing here a human would miss. Four rules shape it, and each is structural
  rather than remembered. **There is no method on `InterestLedger` that answers *who has
  said yes to me***: the lift's read takes the candidate population it may answer about,
  so an inbox is not a query the port can express. **The origin key is two columns on the
  row** — an interest citing a search that is unknown, foreign or that never showed that
  person is refused, never linked as null, and the position is read off the record rather
  than sent. **Nothing decays**: `INTEREST_TTL` is flat then absent, `expires_at` is dated
  at birth, and at `OUTSTANDING_INTEREST_CAP` the write is **refused** rather than
  shortening a yes already sent. And it is the **one** thing that may admit a candidate
  below `QUALITY_FLOOR` — `admits(..., interest_received=True)` in `engines/matchfit/v1/
  floor.py`, with the reason printed; the newcomer and zero-exposure lifts reorder and
  never admit. All three numbers are ruleset rows and only the sweep's cadence is a
  setting.
  **And the tap says whether a game came of it**
  ([ADR-0154](../../../docs/adr/0154-a-mutual-names-the-game-it-has-and-names-nothing-when-it-has-none.md),
  #370). `MutualChallengeMinting` kept `UUID | None` and **moved its meaning** — from *what
  this call minted* to *the game these two have*, so a repeat tap held by 0152's idempotence
  guard is answered with the game that guard is holding it on rather than with silence. The
  ids were already in the guard's hand; `express_interest` was discarding them, which is the
  whole of what #370 was. It rides out on `ExpressedInterestResponse.challenge_id`, additive
  and nullable, and `mutual` does not move: reporting it `false` because a gate refused would
  say something about the other person no refusal may. **`None` covers two unrelated causes
  and may not be narrowed to one** — a game still being *arranged* (a send, or this mutual's
  own half-built doubles court), and a gate that refused or could not be read — which is
  ADR-0130's *a withholding is stated, the gate is not named* applied one route over. Giving
  the first case an id, which is one port read away, would make absence mean *a gate refused
  about one of you* and the field would have to go; §3 of the record is where that is
  written down. `mutual_born_challenges_that_became_games` answered **newest first** for it, so
  the row named to a player was not set iteration order (ADR-0105). **Since #578 nothing is
  minted**: the challenges went, `build_mutual_challenge_minting` signs the port with
  `NoMutualOpensAGame`, and `ExpressedInterestResponse.challenge_id` is always `null` — the
  port's own word for *no game to name* — until #579 removes the interest route. A fill's
  `completing_challenge_id` likewise names a court that does not exist
  (`NoHalfBuiltCourtsExist`), and `MatchHistoryQuery` is `games` alone (`GamesPlayed`), with no
  challenge open and a measured zero in every inbox.
- **The deck reads no declaration, and a pass is a statement about my deck**
  ([ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md),
  [ADR-0128](../../../docs/adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md),
  `the-two-contracts.md` §6). `POST /api/v1/deck` takes **the sport and the week this one
  deal runs on** and creates a search: there is no mode on the wire in either direction,
  because **every deal scores under the fun ruler for every viewer**, declared or not —
  `INHERITED_ON_THE_DECK` in `matchmaking/domain/deck.py`, a fact about the surface and
  never a function of anything the viewer said, so `play_intent_not_declared` is never
  raised here and `search.intent_read` records **the declaration as it stood** for history
  alone, `NULL` for a viewer who never made one (migration `0022`). **The intent term
  stands down for every pairing on the deck** — `STOOD_DOWN_ON_THE_DECK` on the
  `SearchContext`, threaded to the engine as `stood_down` so the term is never read and
  says `NOT_READ_ON_THIS_SURFACE`, the fourth `DegradedReason`, which is neither side's gap
  — so a declaration moves nobody, up or down, and one pair has two Fits: Find a game is
  untouched. Its order is its whole variety (**two bands** — the lifted, the person who said
  yes among them by rank key and unmarked beyond `inclusion_reason`, then the rest — then
  `PASS_SUPPRESS`); the **relaxation ladder does not reach it** — the week is the only ask
  beside the sport, and it is an ask like the shortlist's: it writes nothing, and the deal
  comes back carrying `KEEP_THESE_TIMES`, which is the offer to save it; and a spent deal
  deals again — a new `search_id`, the same exclusions plus everybody dealt within
  `DEALT_MEMORY`, so only a *fresh* deal that came back empty is the honest empty state.
  **The fourth exclusion is the cool-off** (ADR-0169 §6): somebody the viewer has a live
  challenge or game with, and for `deck_cool_off_days` — a ruleset row of its own,
  released as `2026.09.15-a` at the pass window's thirty, nought in the two datasets that
  never knew it — after the court is behind them. It is read through `SharedCourtQuery`,
  the **seventh** matcher demand, answered over `games`' own directory by
  `infrastructure/games_shared_courts.py` and failing **soft** like the suppression cache;
  **deck only** — Find a game keeps ADR-0142 §1's release. **And the envelope says two
  numbers no other surface can**: `pool.remaining`, the eligible beyond the hand, and
  `pool.want_to_play_you`, the live yeses that would be dealt with the dealt memory
  deliberately not applied — a fold over the lift's own read and never a second one, so
  the chip and the hand cannot disagree. Both are omitted on every other surface and on a
  read-back, and the latter is the **one count** ADR-0109 §2's sentence is narrowed to
  admit: `tests/unit/test_no_response_carries_an_inbox.py` refuses every other spelling of
  incoming interest on every response type, and a list anywhere.
  `POST /api/v1/passes` is **write-only and answers `204`**: no route returns a pass, to
  anyone, in any shape, and `PASS_SUPPRESS` crosses the wire in **no shape at all**. It
  has three boundaries, all the opposite of a block's — deck only, one-directional, never
  escalating — and the split that makes them enforceable is **the gate is the cache; the
  evidence is the row**: the durable `player_pass` row is written and committed first, and
  the 30-day Redis suppression derived from it is written after and **fails soft**, so an
  outage repeats a card and never empties a deal. Two telemetry columns exist for the one
  falsifier `PASS_SUPPRESS` has — `search.n_excluded_by_suppression` and
  `search_candidate.suppression_lapsed`, both **deck deals only**, both check-constrained.
  **And a pass can be cleared, by one route that touches none of the three stores it
  clears** (ADR-0169 §5 and its amendment, #440). `POST /api/v1/deck/reset` is *Show them
  again*: it writes **one moment** to the `deck_reset` table — per player, per sport,
  append-only, the module's fifth durable ledger — and the next deal reads that moment
  three ways (`domain/deck.py`: `cleared_by_reset` over the pass record, `dealt_memory_from`
  over the search record, `cooling_off` over the courts). The Redis keys are left to
  lapse and the deal subtracts what the record says was cleared, because a reset that had
  to reach the cache could fail soft and answer a `204` that was a lie. *Already asked*
  is not cleared, a court still ahead is held out whatever was pressed, and the
  `suppression_lapsed` flag is **not** widened to a reset re-show — the reset row beside
  the pass record is what names those. **The cap steps aside for a yes that closes a
  mutual** (ADR-0169 §3): `express_interest` reads the other side's yes *before* the cap,
  and a yes that is answered the instant it is written was never outstanding. And
  `ttl_days` crosses beside `cap` on every `outstanding` row, read off the ruleset at
  response time, so the deck's ending can print *21* without the client holding it.
  **`application/search_workbench.py` is the seam the two surfaces share** — read the
  searcher, bind the snapshot and every live gate fact, attach the card and the at-stake
  block, record, commit, note exposure — so a shortlist and a deal cannot come to two
  answers about which reads fail closed. What stays in each use case is what that surface
  decides: the mode, the exclusions, the order, the ladder, the prompts.
- **A returned search is a recorded search**
  ([ADR-0104](../../../docs/adr/0104-the-search-record-is-the-answer-and-never-expires.md)).
  `POST /api/v1/searches` is the platform's first matchmaking route, and the rule that
  shapes it is that the `search` row is written **in the request's own transaction and
  committed before the response returns** — if that fails, the search fails, because the
  `search_id` *is* the answer's identity. Every fact on it is search-time and **there is
  no backfill**, which is why the two tables are wide on day one and why
  `their_slot_count`, `days_away` and the raw `liveness_signals` are recorded and read by
  nothing: *a strike that is not recorded becomes irreversible by accident.* Nothing
  deletes a row; erasure will be the only path that ever does.
  Three seams are worth holding in your head, because a change lands in exactly one of
  them. **`domain/shortlist.py` is pure** — a bound `SearchContext` in, an ordered answer
  out, no I/O — which is what lets the three walkthroughs be golden files
  (`make gen-walkthroughs`; **a diff there is a design change and must be argued for in
  the pull request**). **`domain/fence.py` is the crossing**: everything the scorer will
  ever see is built there, so a field that must not reach it has one place to be refused.
  And **`application/run_shortlist_search.py` owns the order** — read the searcher live,
  bind one snapshot and every live gate fact, run the pipeline, record and commit, then
  write exposure *after* the commit. **Never a fallback list:** when the engine raises the
  feature is down, and there is deliberately nothing to catch it with.
  **`GET /api/v1/searches/{id}` reads one back, and it is not a cache**
  ([ADR-0109](../../../docs/adr/0109-a-read-back-names-what-it-withholds.md),
  [ADR-0130](../../../docs/adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)). The
  record is immutable and the four fail-closed gates — block, hold, account state, mutual
  gender — are re-evaluated live, so a row they no longer admit **keeps its place and states
  that it is withheld** while naming no gate and carrying no person. That is why both routes
  render `SearchRecord` through one function and why the row records the card, the concerns,
  the one-decimal distance and the at-stake block: what a read-back cannot reproduce off
  the row, it would have to re-read from sources that have moved on.
