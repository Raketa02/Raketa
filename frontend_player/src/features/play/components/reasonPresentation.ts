/**
 * The reason lines — **one function per evidence variant**, which is the deck's second shape.
 *
 * A reason line is a sentence *over* a term's evidence: `LevelFitEvidence` carries a delta
 * and a direction, `AvailabilityOverlapEvidence` a count and the next shared cell, the two
 * tag terms three sets of pairs. A flat table keyed by `Term` cannot hold any of that, which
 * is ADR-0106's own *"a renderer per variant"*
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1, §6.2).
 *
 * ## The register, which is the whole of what these may say
 *
 * `the-play-screens.md` §1 forbids the obvious one by name: *"a client thresholding a term
 * value would be that judgement in TypeScript, differently in every client."*
 *
 * > **A reason line states its evidence's own facts and never grades them.**
 *
 * No *well*, no *strongly*, no *good*. The grading vocabulary belongs to `concerns[]`, which
 * is the engine's judgement and arrives ranked — see `concernPresentation`.
 *
 * That is also why a line cannot simply name its term. `reasonSelection` has already removed
 * every term whose value the surface draws, so a survivor saying *"Your weeks overlap"* would
 * sit on a card with no overlap row and carry no fact at all. **The filter and the register
 * are one decision, not two.**
 *
 * ## Three renderers answer *not a reason*
 *
 * A declared mismatch of intent, and a tag term whose only firing pairs clash, are **claims
 * about a shortfall** — and a clash is a graded claim, which the engine is the only thing
 * entitled to make. Those return `undefined` and the same fact reaches the player through
 * §7's concern instead. `undefined` here is never *"no words for this code"*; that is the
 * mapper's answer, and §3's.
 *
 * ## Mode reaches exactly one of these
 *
 * `INTENT_ALIGNMENT`'s, and it reads `my_mode` **off the evidence** rather than off the
 * envelope — the evidence carries the mode the engine actually used, on every candidate, deck
 * included, where the envelope's is null (§2).
 */

import { counted } from '@/shared/formatting/counted';
import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import { slotName } from '@/shared/vocabulary/availabilityPresentation';
import { socialTagName } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import type {
  AvailabilityOverlapEvidence,
  DistanceEvidence,
  Evidence,
  IntentAlignmentEvidence,
  LevelFitEvidence,
  PredictedBalanceEvidence,
  ReliabilityEvidence,
  TagPair,
  TagRelationships,
} from '../domain/evidence';
import type { SearchMode } from '../domain/vocabulary';

/**
 * How far apart the two levels are, in the direction the engine measured it.
 *
 * Filtered off all three cards — every one of them prints a level — so this appears in the
 * sheet alone. Levels take §B16's format throughout: two decimals, decimal comma.
 */
export function levelFitReason(evidence: LevelFitEvidence): string {
  const delta = formatLevel(evidence.delta);
  switch (evidence.direction) {
    case 'ABOVE':
      return `${delta} above you`;
    case 'BELOW':
      return `${delta} below you`;
    case 'LEVEL':
      return 'Level with you';
  }
}

/**
 * The forecast, with the platform's own caveat in the same breath — §F1 rule 4's
 * *fact · mechanism*.
 *
 * **This is the only place `confidence` is drawn at all.** `my_sigma` and `their_sigma` are
 * never printed: the candidate's σ reaches a screen exactly once, as the likely range on the
 * card, and never as a number of its own.
 */
export function predictedBalanceReason(evidence: PredictedBalanceEvidence): string {
  return `Forecast ${formatPercent(evidence.pct)} even · ${formatPercent(evidence.confidence)} sure`;
}

/**
 * What kind of evening each of them is after.
 *
 * The two mismatches are **not reasons** — a competitive searcher meeting a for-fun candidate
 * forgoes 16,1 points and the reverse forgoes 10,0, both clear the bar, and both are the
 * engine's judgement to state. They arrive as concerns instead, one sentence per direction,
 * because a single wording would state one player's mismatch as the other's.
 */
export function intentAlignmentReason(evidence: IntentAlignmentEvidence): string | undefined {
  if (evidence.theirIntent === 'NO_PREFERENCE') return "They'll play either kind of evening";
  // The two vocabularies spell the same evening the same way — a searcher's mode *is* one of
  // the declarations a player can make, which is why `PlayIntent` is `SearchMode` plus the
  // one answer a search cannot be.
  return evidence.theirIntent === evidence.myMode ? ALIGNED[evidence.myMode] : undefined;
}

const ALIGNED: Readonly<Record<SearchMode, string>> = {
  COMPETITIVE: "They're here to compete too",
  FOR_FUN: "They're here for a fun game too",
};

/**
 * Their record, as the number on their own profile.
 *
 * **Unreachable day one** (`NoPlayerScoresExist`), and written anyway: the vocabulary is
 * closed, and a code with no words is how a term arrives blank the day its provider lands.
 *
 * `floorBreached` is deliberately not drawn here — it is `RELIABILITY_FLOOR_BREACH`'s, in
 * `modifierPresentation`, and printing it twice would make one dock look like two.
 */
export function reliabilityReason(evidence: ReliabilityEvidence): string {
  return `Player Score ${evidence.score}`;
}

/**
 * How much of the searcher's week they are free in.
 *
 * The zero case is a **fact about arranging a game**, not a refusal: overlap is evidence a
 * game can be arranged, and the times rung of the ladder exists for exactly this pairing.
 */
export function availabilityOverlapReason(evidence: AvailabilityOverlapEvidence): string {
  if (evidence.sharedCount === 0) return 'No shared slots — one of you would have to bend';

  // Through the one pluralisation helper, so that no sentence here assumes English's plural.
  const both = `${counted(evidence.sharedCount, 'slot', 'slots')} you both ticked`;

  return evidence.nextSlot === null ? both : `${both} · next ${slotName(evidence.nextSlot)}`;
}

/** The hour on court. */
export function playingStyleReason(evidence: TagRelationships): string | undefined {
  return tagTermReason(evidence, 'Different on court, not incompatible');
}

/**
 * The evening around it.
 *
 * One renderer each rather than one shared with a heading argument: the two terms carry
 * different weights, invert between the modes, and are rendered under different headings —
 * and the difference between them is a whole sentence, not a noun slot.
 */
export function socialVibeReason(evidence: TagRelationships): string | undefined {
  return tagTermReason(evidence, 'Different around the game, not incompatible');
}

/**
 * The shared shape of the two tag terms: **matched, then complementary, then the zero.**
 *
 * `clashing`-only is not a reason and returns nothing — it is §7's concern. The last case is
 * the term's **measured zero**, and the words are the code's own: *"a pair with nothing
 * firing is different, not incompatible — the term's zero is a real clash, never an absence
 * of relationship."* It is **not** the same state as the term standing down, which is §8's.
 */
function tagTermReason(evidence: TagRelationships, measuredZero: string): string | undefined {
  const [firstMatched] = evidence.matched;
  if (firstMatched !== undefined) return `Both of you: ${tagList(evidence.matched)}`;

  const [firstComplementary] = evidence.complementary;
  if (firstComplementary !== undefined) return complementaryPair(firstComplementary);

  return evidence.clashing.length > 0 ? undefined : measuredZero;
}

/** `{a} meets {b}` — the pair the product claims fit together, in the order it claims it. */
function complementaryPair(pair: TagPair): string {
  return `${socialTagName(pair.a)} meets ${socialTagName(pair.b)}`;
}

/**
 * Tag ids resolved through the **promoted** table, never re-worded here.
 *
 * The words alone and no glyphs: this is a sentence, and the emoji belongs to the chip.
 */
function tagList(tagIds: readonly SocialTagId[]): string {
  return tagIds.map(socialTagName).join(', ');
}

/**
 * How far away they are.
 *
 * The second sentence is a fact the searcher is owed rather than a penalty applied behind
 * their back: *"somebody who set a small radius is not refusing to be found, and the searcher
 * is shown the fact rather than having the person removed."*
 */
export function distanceReason(evidence: DistanceEvidence): string {
  const away = `${evidence.km} km away`;
  return evidence.outsideTheirRadius ? `${away} — outside the ring they set` : away;
}

/**
 * The one entry point a surface calls, dispatched on `kind`.
 *
 * `undefined` means **this evidence is not a reason** — the three cases above — and the
 * caller drops the line. A term whose evidence this build cannot read never reaches here at
 * all: an unknown `kind` is stopped at the mapper, and §3 rules a card's reason line one of
 * the placements where an unreadable code is *dropped* rather than named.
 */
export function reasonLine(evidence: Evidence): string | undefined {
  switch (evidence.kind) {
    case 'level_fit':
      return levelFitReason(evidence);
    case 'predicted_balance':
      return predictedBalanceReason(evidence);
    case 'intent_alignment':
      return intentAlignmentReason(evidence);
    case 'reliability':
      return reliabilityReason(evidence);
    case 'availability_overlap':
      return availabilityOverlapReason(evidence);
    case 'playing_style':
      return playingStyleReason(evidence);
    case 'social_vibe':
      return socialVibeReason(evidence);
    case 'distance':
      return distanceReason(evidence);
  }
}
