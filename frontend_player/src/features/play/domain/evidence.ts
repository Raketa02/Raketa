/**
 * The eight typed evidence variants a term carries, in this app's own spelling.
 *
 * A reason line is a **sentence over its evidence**, not a name for its term: a flat table
 * keyed by `Term` cannot hold *"3 slots you both ticked · next Tue evening"*, because the
 * facts are in the payload. That is ADR-0106's own *"a renderer per variant"*, and it is why
 * these are eight types rather than one with an optional bag on it
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1).
 *
 * **Discriminated on `kind`, and the discriminator keeps the wire's spelling** — it is a
 * closed code like every other, and renaming it here would buy a second table that has to be
 * kept in step. The field *names* are this app's, which is the ordinary mapper boundary.
 *
 * **What is not here is as decided as what is.** `my_sigma` and `their_sigma` are carried and
 * never drawn; `area_code` is carried and is not a word (§6.3); a `Term`'s weight and value
 * live on the row, not in the evidence, because a reason line never prints a weight.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { LevelDirection, PlayIntent, SearchMode, Term } from './vocabulary';

/** How far apart the two levels are, and which way. `delta` is unsigned; `direction` carries the sign. */
export interface LevelFitEvidence {
  readonly kind: 'level_fit';
  readonly myMu: number;
  readonly theirMu: number;
  readonly delta: number;
  readonly direction: LevelDirection;
}

/** How even the game is forecast to be, and how sure of that the platform is. */
export interface PredictedBalanceEvidence {
  readonly kind: 'predicted_balance';
  readonly pct: number;
  readonly mySigma: number;
  readonly theirSigma: number;
  readonly confidence: number;
}

/**
 * What kind of evening each of them is after.
 *
 * `myMode` is the mode **the engine actually used**, carried on every candidate including
 * the deck's — where `SearchEnvelope.mode` is null. The two sources must not be merged: the
 * row says what kind of evening was priced, and the sheet's header names no mode (§2).
 */
export interface IntentAlignmentEvidence {
  readonly kind: 'intent_alignment';
  readonly myMode: SearchMode;
  readonly theirIntent: PlayIntent;
  readonly aligned: boolean;
}

/**
 * What their record says about turning up.
 *
 * `score` is the **published Player Score**, the number on their own profile — never the
 * matcher's private blend of the same strands. Unreachable day one, and written anyway: a
 * code with no words is how a term arrives blank the day its provider lands.
 */
export interface ReliabilityEvidence {
  readonly kind: 'reliability';
  readonly score: number;
  readonly floorBreached: boolean;
}

/** How much of the searcher's week they are free in, and the soonest cell both ticked. */
export interface AvailabilityOverlapEvidence {
  readonly kind: 'availability_overlap';
  readonly sharedCount: number;
  readonly nextSlot: WeekCell | null;
}

/** Two Social tag ids the product claims fit together, or do not. */
export interface TagPair {
  readonly a: SocialTagId;
  readonly b: SocialTagId;
}

/**
 * What fired between two players' tags, in one column of the matrix.
 *
 * The three sets travel together everywhere and are read in one precedence — matched, then
 * complementary, then the clash — so they are one type rather than three fields repeated on
 * two variants. **It is not a nesting on the wire and is not one here**: both variants spread
 * it flat, because the payload is what the two terms share and the `kind` is what keeps them
 * apart.
 */
export interface TagRelationships {
  readonly matched: readonly SocialTagId[];
  readonly complementary: readonly TagPair[];
  readonly clashing: readonly TagPair[];
}

/** What the two of them are like during the hour on court. */
export interface PlayingStyleEvidence extends TagRelationships {
  readonly kind: 'playing_style';
}

/**
 * What the two of them are like around the game.
 *
 * The same shape as playing style and deliberately a **separate variant**: the two terms
 * carry different weights, invert between the modes, and are rendered under different
 * headings. One variant with a column field would make *which term is this* a value the
 * client branches on rather than a type it dispatches over.
 */
export interface SocialVibeEvidence extends TagRelationships {
  readonly kind: 'social_vibe';
}

/**
 * How far away they are, and whether the searcher sits outside *their* ring.
 *
 * A candidate's own radius is a dock and never a gate, so the second fact is one the searcher
 * is owed rather than a penalty applied behind their back.
 */
export interface DistanceEvidence {
  readonly kind: 'distance';
  readonly km: number;
  readonly areaCode: string;
  readonly outsideTheirRadius: boolean;
}

export type Evidence =
  | LevelFitEvidence
  | PredictedBalanceEvidence
  | IntentAlignmentEvidence
  | ReliabilityEvidence
  | AvailabilityOverlapEvidence
  | PlayingStyleEvidence
  | SocialVibeEvidence
  | DistanceEvidence;

/**
 * One term that fired, with the arithmetic that put it where it is.
 *
 * The list arrives **ranked by contribution**; nothing on this side sorts. The cap on how
 * many are drawn is the client's, and it is `reasonSelection`'s.
 */
export interface ScoredTerm {
  readonly term: Term;
  readonly weight: number;
  readonly value: number;
  readonly contribution: number;
  readonly evidence: Evidence;
}
