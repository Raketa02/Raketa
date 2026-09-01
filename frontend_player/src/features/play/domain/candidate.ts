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
 * ## What is not here yet
 *
 * `degraded_terms` and `modifiers` arrived with `SH.whyfit`, which is the surface that draws
 * them ([#273](https://github.com/Raketa02/Raketa/issues/273)). What is still absent is
 * `at_stake` — the sheet's five zones do not draw it — and `counted_games`, which is
 * `OMITTED` on the wire and whose block Decision 3 deleted. **`would_be_forecast` is out of
 * scope entirely**: nothing in the backend writes it, and its three consumers went with it. A
 * field is added here when a surface draws it, because a DTO with fields nobody reads is a
 * contract nobody is checking.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import type { ScoredTerm } from './evidence';
import type {
  DegradedReason,
  InclusionReason,
  LivenessReason,
  ModifierCode,
  SearchMode,
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
  /** The whole handle. Nothing derives a familiar form from it — ADR-0107, and §15. */
  readonly nickname: string;
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
  /** Their coarse area, as a machine code. **Never printed** — §6.3, and `areas.py`. */
  readonly areaCode: string;
  /** Narrowed at the mapper: a tag id this build has no words for is dropped, per §3. */
  readonly socialTags: readonly SocialTagId[];
  readonly level: number;
  /** The band's **published name**. Its numeric edges are not on the card. */
  readonly band: string;
  readonly range: LikelyRange;
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
 * **`myAreaCode` is folded on in `api/`, exactly as `OriginSearch`'s sport and week are.** It
 * is the searcher's own coarse area, and it is here because the meta line's one licensed
 * sentence is a **comparison between two codes** — the shape
 * [ADR-0021](../../../../../docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md)
 * licenses a client to compute — and a card that reached for the profile itself would be
 * reading global state, which is the defect §G6 #8 records on the why-fit sheet and
 * [#233](https://github.com/Raketa02/Raketa/issues/233) fixed there.
 *
 * ## And today there is nothing to fold on, which is why it is optional
 *
 * **No route serves the searcher their own area code.** `area_code` crosses on exactly two
 * schemas — `PlayerCardSchema` and `DistanceEvidence` — and both are the *candidate's*;
 * `GET /players/me/profile` serves a week, a radius and the declarations, and the location
 * area is one of the three facts it names as *not served yet*. So the comparison this field
 * exists for cannot fire, and the honest spelling of that is an absent value rather than a
 * sentinel string that would silently mean *never in your area*.
 *
 * The first surface to draw a card is the deck, which is where the gap was found;
 * [#279](https://github.com/Raketa02/Raketa/issues/279) is where it is decided, and until then
 * the meta line drops its clause and keeps its kilometres.
 */
export interface SearchEnvelope {
  readonly searchId: string;
  /** **Null exactly on the deck**, which has no mode. See the module note. */
  readonly mode: SearchMode | null;
  /** Absent until a route serves it — see the module note, not a bug in a caller. */
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
}

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
