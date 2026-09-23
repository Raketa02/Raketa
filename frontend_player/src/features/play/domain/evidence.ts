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
  /**
   * Whether **every id the platform matched is one this build can name** — §3's gap kept in
   * place, on the one list where dropping silently would turn into a claim.
   *
   * `matched` is narrowed at the mapper like every other tag list, and for the same reason: a
   * sentence naming a tag with no words is a chip with no words on it. Everywhere else that
   * drop is free, because a reason line that cannot be written simply is not written. It stops
   * being free on the competitive card's **tag row**, which draws the amber *No tags in common*
   * when the terms fired and matched nothing ([#311](https://github.com/Raketa02/Raketa/issues/311)):
   * a build too old to read a twentieth tag id would narrow a real match down to an empty list
   * and then **say out loud** that there is no overlap, which is the one thing a gap must never
   * become.
   *
   * So the count survives the narrowing as a bit. `false` means *they share something this
   * build cannot name*, which is neither of the ticket's two spellings of absence and is drawn
   * as the third: the tags, untinted, and **no** amber line.
   *
   * **`reasonPresentation` reads it too, and for the same reason.** A tag term's precedence is
   * *matched, then complementary, then the measured zero*, so a narrowed-away match falls
   * through to *"Different on court, not incompatible"* — which is the amber claim again, in
   * prose, on every card rather than one. The measured zero is the one branch the bit closes:
   * a term that matched something did not score zero, whatever this build can read of it.
   */
  readonly matchedInFull: boolean;
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
 *
 * `km` is **the engine's input** — whole kilometres, cell to cell, what the term was scored on
 * — and no screen prints it: the distance a surface prints is the candidate's own one-decimal
 * `distanceKm`, measured spot to spot (ADR-0174 §2).
 */
export interface DistanceEvidence {
  readonly kind: 'distance';
  readonly km: number;
  readonly areaCode: string;
  readonly outsideTheirRadius: boolean;
}

/**
 * Whether this evidence is one of the two **tag comparisons** — the narrowing every reader of
 * them starts with.
 *
 * One predicate rather than two `kind === … || kind === …` cascades, because both callers ask
 * the same question and one of them was reaching for a cast to answer it: the domain rule needs
 * `TagRelationships` out of an `Evidence`, and a type guard is what makes that a narrowing
 * instead of an assertion. `null` is a variant this build has never seen and is not a tag
 * comparison — §3, and the reason an unreadable row cannot license a claim.
 */
export function isTagEvidence(
  evidence: Evidence | null,
): evidence is PlayingStyleEvidence | SocialVibeEvidence {
  return (
    evidence !== null && (evidence.kind === 'playing_style' || evidence.kind === 'social_vibe')
  );
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
 *
 * ## The two `null`s, and why the numbers beside them are not
 *
 * Old builds live on real phones for months, so a served `Term` or a ninth evidence variant
 * may be a code this build has never seen — the state
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3 legislates for. The
 * row is **kept** either way, because ADR-0106 §6 requires *"a named gap saying the app is out
 * of date, never a silently shorter list"* and the why-fit sheet prints **totals these rows
 * belong to**: a row dropped here reappears as an adjustment nobody made, and the sheet's
 * derived `applied` becomes *"a wrong number that looks like a plausible one"*.
 *
 * So the gap lands **in place**, exactly as #233 §7 specifies: an unrenderable variant *"leaves
 * its row's weight, value and contribution standing — those are numbers, not codes"* and puts
 * the gap where the reason line goes, and an unknown `Term` takes the whole row's label.
 */
export interface ScoredTerm {
  /** `null` where the served term is a code this build has no name for. */
  readonly term: Term | null;
  readonly weight: number;
  readonly value: number;
  readonly contribution: number;
  /** `null` where the served variant is one this build has no renderer for. */
  readonly evidence: Evidence | null;
}
