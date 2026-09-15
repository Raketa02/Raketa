/**
 * One row of a shortlist, and the search it came off — this app's spelling of the two shapes
 * every Play surface is drawn from.
 *
 * [#218](https://github.com/Raketa02/Raketa/issues/218) established that the three cards are
 * **three renderings of one candidate**, which is an argument for one *contract* and was read
 * once as an argument for one component. It is not
 * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md)
 * §3): the contract is here, and the three shapes over it are three files.
 *
 * ## Why the envelope travels beside the candidate rather than a `mode` string
 *
 * `SearchEnvelope.mode` is **null exactly on the deck**, and `IntentAlignmentEvidence.myMode`
 * is not — the row says what kind of evening was *priced*, and the deck asked nobody to pick
 * one. The two are **supposed** to disagree there
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §2), so a card handed
 * a single `mode` would have to be told which of the two it was being handed. Handed both
 * objects it cannot conflate them, and a card that wants the priced mode reads it off the
 * evidence where it always was.
 *
 * ## A field arrives when a surface draws it
 *
 * `degraded_terms` and `modifiers` arrived with `SH.whyfit`, which is the surface that draws
 * them ([#273](https://github.com/Raketa02/Raketa/issues/273)). `player_score` arrived with the
 * chip row, because *Most reliable* is an ordering over that number and a comparator cannot
 * order by a field the DTO does not carry ([#306](https://github.com/Raketa02/Raketa/issues/306)).
 * `counted_games`, `last_five` and `at_stake` arrive with the blocks that print them
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)) — three record boxes and a pair of
 * stake boxes on the competitive card, which is the first surface in this app to draw any of
 * the three. `review` arrives with the ON COURT mark on the photo panel
 * ([#313](https://github.com/Raketa02/Raketa/issues/313)), which is the only surface anywhere
 * in this app that reads another player's verdict.
 *
 * **`would_be_forecast` is out of scope entirely**: nothing in the backend writes it, and its
 * three consumers went with it. A field is added here when a surface draws it, because a DTO
 * with fields nobody reads is a contract nobody is checking.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { ScoredTerm } from './evidence';
import type {
  DegradedReason,
  GameResult,
  InclusionReason,
  LivenessReason,
  ModifierCode,
  OptimisedFor,
  PhotoReview,
  RelaxationAsk,
  Rung,
  SearchMode,
  SortOption,
  Term,
  Window,
} from './vocabulary';

/** μ ± σ, as `rating` published it. The **likely range** — never the band's own edges. */
export interface LikelyRange {
  readonly low: number;
  readonly high: number;
}

/**
 * Who this person is, on a card — a closed list, and every field a fact about *them alone*.
 *
 * That is ADR-0107's test, and it is why `distanceKm` sits on the candidate instead: a
 * distance is a fact about a **pair**, and it would be the one field here whose value changed
 * depending on who was looking.
 */
export interface PlayerCard {
  /** The whole name. Nothing derives a familiar form from it — ADR-0107 through ADR-0171, and §15. */
  readonly name: string;
  /**
   * The short-lived signed link that draws their photograph, **omitted** with the id when
   * they have none — and the client draws the generated poster instead.
   *
   * The id itself is not here, because nothing on a Play screen does anything with it: it is
   * what the *record* keeps, and `GET /photos/{id}` refuses another player's on purpose. The
   * URL is the only address this photograph has
   * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §9).
   */
  readonly photoUrl?: string;
  /**
   * What the on-court check concluded about that photograph — **omitted where nobody
   * looked**, which is not the same answer as `flagged` and is drawn identically to it.
   *
   * Three states and not two ([ADR-0138](../../../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)):
   * checked and passed, checked and flagged, and a photograph that arrived while the reviewer
   * could not be reached or before the check existed at all. **Only the first earns a mark**,
   * and the absence is where the other two meet — a card that marked the gap would be claiming
   * a check happened on every photograph on the platform.
   *
   * It is `player_profile`'s `PhotoReview` read the **opposite** way round, and the difference
   * is the difference between a warning and a badge: an upload that says nothing folds to
   * `allowed`, because *an unreachable reviewer means the player is not warned rather than
   * wrongly warned*; a card that says nothing folds to **no mark**, because a tick on a
   * photograph nobody looked at is a lie told to twenty strangers.
   *
   * **The evidence never crosses, on any route** — no confidence, no similarity vector, no
   * model, no prompt-set fingerprint. There is no number here and none may be invented from
   * the code (ADR-0133's clause, untouched by ADR-0138).
   */
  readonly photoReview?: PhotoReview;
  /** Their coarse area, as a machine code. **Never printed** — §6.3, and `areas.py`. */
  readonly areaCode: string;
  /** Narrowed at the mapper: a tag id this build has no words for is dropped, per §3. */
  readonly socialTags: readonly SocialTagId[];
  readonly level: number;
  /** The band's **published name**. Its numeric edges are not on the card. */
  readonly band: string;
  readonly range: LikelyRange;
  /**
   * Their **Player Score** out of a hundred — reliability, as the platform watched it.
   *
   * **Omitted where it has watched nothing**, which is most people today, and never `0`:
   * somebody nothing was ever arranged for has not failed to turn up. That absence is what
   * lets *Most reliable* sort them last instead of first — `distanceKm`'s rule one field up,
   * for `distanceKm`'s reason.
   *
   * **It has nothing to do with skill**, and the block that prints it must not imply
   * otherwise: it is turning up, answering challenges and confirming results
   * ([ADR-0140](../../../../../docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)),
   * where the Level two fields up is the only thing on this card that is about playing.
   */
  readonly playerScore?: number;
  /**
   * How many **counted** games are behind their rating — the honesty figure.
   *
   * *A 2,95 built on 29 games means much more than one built on three.* A friendly is not
   * one, and a game nobody agreed a score for **is**: an unscored game moved nobody's Level
   * and still says these people were on a court
   * ([ADR-0137](../../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md)).
   *
   * **Omitted where they have played none**, never `0` — absence has one spelling on this
   * card, and it is the one `distanceKm` and `playerScore` already take.
   */
  readonly countedGames?: number;
  /**
   * Their last five counted results, **oldest to newest** — the run of form, drawn left to
   * right.
   *
   * **Fewer than five is a real answer and is never padded.** Three entries means three
   * counted-and-agreed results and the card draws the gap, because the gap is the honest
   * statement: padding it to five would claim two games nobody played.
   *
   * **Outcomes in order and no dates**, at any granularity — see `GameResult`. A moment
   * beside one of these is activity recency, which no card carries in any shape.
   *
   * **Omitted where nothing of theirs has been counted and agreed**, which is not the same
   * absence as `countedGames`': a player whose games were all unscored has a count and no
   * run, and that pair is consistent rather than broken.
   */
  readonly lastFive?: readonly GameResult[];
}

/**
 * What a **counted** game against this person would do to your Level, either way.
 *
 * It sits on the candidate rather than on the card for `distanceKm`'s reason and by ADR-0107's
 * test: it is a fact about a **pair**, and it is the one figure here whose value changes
 * depending on who is looking.
 *
 * **Read forward off the rating engine's own update rule**
 * ([ADR-0139](../../../../../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
 * so the pair printed is the pair the game will deliver if it is played — and nothing on this
 * side derives, rounds or negates either half. `winDelta > 0 > lossDelta` is the server's
 * invariant and neither figure is ever zero.
 */
export interface AtStake {
  /** Signed, and in Level points. Positive, always. */
  readonly winDelta: number;
  /** Signed, and in Level points. Negative, always — the minus is the figure's, not the copy's. */
  readonly lossDelta: number;
}

/**
 * One candidate, with the pairing that put them where they are.
 *
 * `concerns` is the wire's ranked list flattened to its one field: `ConcernSchema` carries a
 * `term` and nothing else, and the card joins it back to the row it already holds — which is
 * what lets one sentence be written over the *evidence* rather than over the term's name
 * (`concernPresentation`).
 */
export interface Candidate {
  readonly playerId: string;
  /** Out of a hundred, and drawn as served. Nothing on this side rounds or rescales it. */
  readonly fit: number;
  /**
   * Whole kilometres, **omitted** rather than zero when the distance term stood down.
   *
   * The two spellings of absence (ADR-0106 §4), and it is what lets *Closest* sort a
   * stood-down row last instead of first.
   */
  readonly distanceKm?: number;
  readonly card: PlayerCard;
  /** Every term that fired, **ranked by contribution**. Nothing on this side sorts. */
  readonly terms: readonly ScoredTerm[];
  /** The terms the engine is concerned about, ranked by points forgone. */
  readonly concerns: readonly Term[];
  /** Why this person moved, ranked by how far. Codes only — there is no number here. */
  readonly livenessReasons: readonly LivenessReason[];
  /** Why they are on the list **at all**, where the reason is one the searcher is owed. */
  readonly inclusionReason?: InclusionReason;
  /**
   * The terms that **stood down**, each with whose gap it was — the renormalisation basis.
   *
   * Drawn by `SH.whyfit` and by nothing else: *"a 78 built on four terms and a 78 built on
   * seven are different readings of the same number"*, and the sheet is the only surface whose
   * job is that number. It is **not** a shorter `terms[]` — a stood-down term has no weight,
   * no value, no contribution and no evidence, which is four of a row's five cells
   * ([#233](https://github.com/Raketa02/Raketa/issues/233) §1).
   */
  readonly degradedTerms: readonly DegradedTerm[];
  /** What the engine adjusted after the eight terms were summed. **Never summed** — see below. */
  readonly modifiers: readonly Modifier[];
  /**
   * What a counted game against them would move — **omitted in for fun**, where a counted
   * result is *meaningless* rather than unavailable, and omitted in competitive where either
   * of the two holds no rating in this sport.
   *
   * Present here is not the same as drawn: a card on a **doubles** seat hides it, because a
   * win against one named person is not a thing that exists until the other three seats are
   * known. That rule is `domain/atStake`'s and never a component's.
   */
  readonly atStake?: AtStake;
}

/**
 * A term the engine **did not count**, and whose gap that was.
 *
 * The pair is the sentence — *"`INTENT_ALIGNMENT + NOTHING_FROM_THEM` and `SOCIAL_VIBE +
 * NOTHING_FROM_THEM` are two different sentences from one code"* — so neither half travels
 * alone.
 */
export interface DegradedTerm {
  /** `null` where the served term is a code this build has no name for — §3's gap in place. */
  readonly term: Term | null;
  /**
   * `null` where the served reason is a code this build has never seen.
   *
   * A gap rather than a drop, because the not-counted block **is** the renormalisation basis
   * a reader is owed: a line that vanished would make the sheet's own list of what did not
   * count silently shorter (`the-words.md` §3).
   */
  readonly reason: DegradedReason | null;
}

/**
 * One adjustment the engine made after the terms were summed, and what it was worth.
 *
 * **Nothing sums this list.** `record_rows.py` forbids it in writing — the budget was applied
 * by the type that produced it — and the only total anybody may read is `applied`, which is
 * `fit − Σcontributions` and is exact by subtraction from two published numbers.
 */
export interface Modifier {
  readonly code: ModifierCode;
  /** Signed, and in Fit points. The row prints it; no row prints a running total. */
  readonly points: number;
}

/**
 * Every fact about *the search*, as opposed to about a candidate.
 *
 * **`myAreaCode` travels on the envelope rather than being looked up per card.** It is the
 * searcher's own coarse area, and it is here because the meta line's one licensed
 * sentence is a **comparison between two codes** — the shape
 * [ADR-0021](../../../../../docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md)
 * licenses a client to compute — and a card that reached for the profile itself would be
 * reading global state, which is the defect §G6 #8 records on the why-fit sheet and
 * [#233](https://github.com/Raketa02/Raketa/issues/233) fixed there.
 *
 * ## Optional, because a search may predate the fact
 *
 * `SearchEnvelope.my_area_code` is the searcher's area **as the search ran on it**, recorded
 * on the search beside the week it ran on rather than read off the profile — the profile's
 * area is what it is *now*, and a search read back a month later would otherwise say *in your
 * area* about an area the player has left
 * ([#279](https://github.com/Raketa02/Raketa/issues/279)).
 *
 * A search recorded before the backend kept one carries no code, and searches are kept for
 * ever, so the absence is a standing state rather than a migration's leftover. It stays an
 * **absent value** rather than a sentinel: an empty string compares unequal to every real code
 * and would quietly mean *never in your area*, which is a claim where this is a gap.
 */
export interface SearchEnvelope {
  readonly searchId: string;
  /** **Null exactly on the deck**, which has no mode. See the module note. */
  readonly mode: SearchMode | null;
  /** Absent on a search recorded before it was kept — see the module note, not a caller's bug. */
  readonly myAreaCode?: string;
  /** What the searcher is told about the pool this answer came from. */
  readonly pool: PoolDescription;
  /**
   * What the numbers were, and how the maths worked — the why-fit sheet's **footer**.
   *
   * Not decoration. `GET /searches/{id}` *never recomputes*
   * ([ADR-0104](../../../../../docs/adr/0104-the-search-record-is-the-answer-and-never-expires.md)),
   * so a month-old read-back is today's build drawing an older ruleset's arithmetic, and this
   * pair is the only thing on screen that says so.
   */
  readonly rulesetVersion: string;
  readonly engineVersion: string;
  /**
   * Whether a widening offer hit the **profile slider's own ceiling** — and therefore whether
   * any *widen* sentence may be said at all.
   *
   * `false` on an answer that widened nothing, which is every deal: the relaxation ladder
   * belongs to the shortlist and a deck carries no rung offers. The gate is drawn anyway,
   * because it is addressed to a player who may already be at 50 km and *asking somebody for
   * something they cannot give* is the one thing the advice must not do
   * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §17).
   */
  readonly radiusClamp: boolean;
  /**
   * Whom this answer was optimised for — and the one field on the envelope the **builder**
   * reads rather than a card.
   *
   * `GROUP` arrives the moment the searcher hand-seats somebody: the engine then fills the
   * seats around them, and the four it finds may be a worse individual match than an empty
   * court would have given. That is a thing the screen has to **say**, so it is rendered in
   * the same voice a provisional figure is
   * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §11.2).
   *
   * `null` is a code this build has never seen. It draws the same as `SEARCHER` — nothing —
   * and that is §3's **drop** rather than a gap: the sentence is an extra caveat over an
   * answer, not a row in a total, so an absent one leaves nothing unaccounted for. The
   * alternative would be claiming *optimised for you* about an answer this build cannot read.
   */
  readonly optimisedFor: OptimisedFor | null;
  /**
   * Which re-sorts the client may draw over rows it already holds — **rendered verbatim, and
   * the row vanishes when it is empty.**
   *
   * The vocabulary is the server's and *"never a lie"*: a sort that would reorder nothing is
   * not in this list, so a hardcoded row of four would be three-quarters a lie today
   * ([#231](https://github.com/Raketa02/Raketa/issues/231) §6). `[]` is a real, tested state.
   */
  readonly sortsAvailable: readonly SortOption[];
  /**
   * What relaxing your **own** asks would be worth, each priced by a genuine re-run — or
   * `null` where nobody needed them.
   *
   * The two absences are different answers and the falsifier is `null` versus not-null:
   * **`null` is *the list cleared five*** and the offers were never computed, while `[]` is
   * *they were computed and there is nothing left to offer*, which is the honest empty state
   * with the pool beside it as the whole answer. Collapsing them would make a thin list and a
   * long one say the same thing.
   */
  readonly rungOffers: readonly RungOffer[] | null;
}

/**
 * One rung of the relaxation ladder, priced. **Offered, never applied.**
 *
 * The engine computes what relaxing one of the *searcher's own* asks would be worth and hands
 * over the number; it never takes the offer, because only the player can say truthfully that
 * they are free on a Saturday
 * ([ADR-0099](../../../../../docs/adr/0099-relaxation-offers-the-searchers-own-asks.md)).
 *
 * **The one client obligation here is a rule and not a rendering: never subtract.**
 * `candidatesAboveFloor` is *the total who would clear the floor at this rung*, and rendering
 * a delta against the rows on screen is the arithmetic error `run_shortlist_search.py` names
 * by hand — *"the trigger asks is this list short, in rows shown; a rung asks would widening
 * add anybody, in people above the floor — those are two populations"*
 * ([#223](https://github.com/Raketa02/Raketa/issues/223) §1). It is also the only reason the
 * one rung whose set is **not** a superset can be priced honestly at all.
 */
export type RungOffer = RungOfferFacts & RelaxedAsk;

interface RungOfferFacts {
  /**
   * Which rung. **Never printed** — the letters are letters precisely so nobody lines them up
   * against a struck rung, and printing either spelling publishes an engine-internal ordering.
   * It is carried because it is what `RunSearchRequest.rung` cites when the offer is taken.
   */
  readonly rung: Rung;
  /** The **total** above the floor at this rung, from a real re-run. See the note: never a delta. */
  readonly candidatesAboveFloor: number;
  /**
   * This rung's **own** window — a challenge sliding from `WEEKEND` to `THIS_WEEK` is part of
   * what widening costs, and it is shown before it is paid. `null` where the served code is
   * one this build has never seen, which drops the clause and keeps the count (§3).
   */
  readonly window: Window | null;
  /**
   * The one cell a **times** rung would add to the searcher's grid, for that one search.
   *
   * It is here rather than on `RelaxedAsk` beside the radius, though the wire makes the two
   * look alike, because the union below is *the pair the label is written from* and this cell
   * is in no label: the control says *look outside your week* rather than naming a Saturday
   * morning, and nothing in this feature prints a slot the player never ticked. What it is for
   * is the **tick** on the grid two screens back
   * ([#283](https://github.com/Raketa02/Raketa/issues/283)), which is drawing rather than
   * words.
   *
   * `null` on every radius rung — a rung never relaxes two asks at once — and `null` on a
   * times rung whose cell the wire omitted or spelled in a way this build cannot read. The
   * offer **survives** that, which is `window`'s answer above and not `radiusKm`'s: the label
   * and the count are both true without it, where a radius rung with no radius has no sentence
   * left at all.
   */
  readonly slot: WeekCell | null;
}

/**
 * Which of the searcher's own asks a rung relaxes — **a union rather than a code beside an
 * optional number.**
 *
 * The wire carries `ask` and an optional `radius_km`, and the two are only meaningful together:
 * a `RADIUS` rung's whole label *is* that number. Spelling it as one union is what makes the
 * mapper's decision permanent — a `RADIUS` offer arriving without a radius is **dropped**,
 * because there is no sentence left to draw and an offer is not a row in any total a gap would
 * have to hold open — and it is what stops every reader downstream carrying a fallback for a
 * state the mapper has already refused to produce.
 *
 * A rung never touches a measurement, a term, a weight or the quality floor. These are the two
 * things the searcher asked for, and nothing else is relaxable.
 *
 * **The times rung's cell is not here**, though the wire carries it beside the radius. This
 * union is the pair a *sentence* is built from, and the cell is in no sentence: it is a mark on
 * a grid ([#283](https://github.com/Raketa02/Raketa/issues/283)), so it sits on the facts above
 * with the count and the window. Putting it here would hand it to every reader of a taken rung,
 * each of which refuses to print it.
 */
export type RelaxedAsk =
  | { readonly ask: Extract<RelaxationAsk, 'TIMES'> }
  | { readonly ask: Extract<RelaxationAsk, 'RADIUS'>; readonly radiusKm: number };

/**
 * The pool an answer came out of — sent on **every** search and not only on empty ones,
 * *"because a thin pool and a broken floor are indistinguishable without it"*.
 *
 * ADR-0099's shape minus its two constants. `post_gate` is always `true` and travels only so
 * the count cannot be misread, and the **sport is not here**: the screen that draws a pool
 * already knows which sport it asked about and holds this app's word for it, which is the
 * same division `poolRankingStatus` takes. A sport narrowed twice is a sport that can be
 * narrowed differently in two places.
 *
 * **The count is post-gate, always.** No pre-gate count crosses, because the delta would be
 * the number of people a mutual preference hid from this searcher
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
 */
export interface PoolDescription {
  /** The searcher's own radius, in whole kilometres, as the search actually ran on it. */
  readonly radiusKmUsed: number;
  readonly playersInRange: number;
  /** `null` where the served window is a code this build has never seen — §3's drop. */
  readonly window: Window | null;
}
