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
 * `degraded_terms`, `modifiers` and `at_stake` are the why-fit sheet's and arrive with it;
 * `counted_games` is `OMITTED` on the wire and Decision 3 deleted the block that would have
 * drawn it. **`would_be_forecast` is out of scope entirely** — nothing in the backend writes
 * it, and its three consumers went with it. A field is added here when a surface draws it,
 * because a DTO with fields nobody reads is a contract nobody is checking.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import type { ScoredTerm } from './evidence';
import type { InclusionReason, LivenessReason, SearchMode, Term } from './vocabulary';

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
 */
export interface SearchEnvelope {
  readonly searchId: string;
  /** **Null exactly on the deck**, which has no mode. See the module note. */
  readonly mode: SearchMode | null;
  readonly myAreaCode: string;
}
