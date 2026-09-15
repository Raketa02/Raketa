/**
 * A term that **stood down**, and whose gap it was.
 *
 * The sentence is `(term, reason)` and not either alone — *"`INTENT_ALIGNMENT +
 * NOTHING_FROM_THEM` and `SOCIAL_VIBE + NOTHING_FROM_THEM` are two different sentences from
 * one code"* ([#233](https://github.com/Raketa02/Raketa/issues/233) §8,
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §8).
 *
 * ## Two tiers, and the third reason is not a line at all
 *
 * `NOT_YET_ON_THIS_PLATFORM` is stated **once, in the footer**, never per card — otherwise
 * reliability's line prints identically on twenty cards and reads as twenty separate
 * shortfalls.
 *
 * **`NOTHING_FROM_YOU` never appears on a card either**, only in the sheet's not-counted
 * block: a list of twenty cards each telling you your own week is blank is one fact printed
 * twenty times, and the prompts are where that belongs. That is a placement rule and it lives
 * with the surfaces that place it; what is here is the sentence.
 *
 * **Which side is named when both are blank is the engine's answer, not this build's.**
 * `NOTHING_FROM_YOU` wins that tie server-side, so a client resolving it again would be a
 * second implementation of one rule.
 *
 * **The fourth reason is the surface's, and it blames neither of you.** The deck deals
 * everybody under one ruler and reads no declaration, so the intent term stands down on every
 * card there as `NOT_READ_ON_THIS_SURFACE`
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §2). Its sentence says the term is not read *here* — the sheet it is drawn in was opened from
 * the surface that declined — and never that either person left something unsaid, because on
 * that surface they may well have said it. Only the intent term has such a sentence today; a
 * term no surface stands down this way keeps the gap in place rather than borrowing one.
 *
 * ## The one wording that must not drift
 *
 * `RELIABILITY + NOTHING_FROM_THEM` says nothing about *when*. The code swallows three causes
 * — no record, the last observation past the horizon, no strand clearing `min_observations` —
 * so that the day reliability goes live the sheet still cannot date anybody. ADR-0106 §5's
 * recency refusal is held by the vocabulary's shape rather than by a reviewer noticing:
 * *"nothing on their record yet"*, and never *"not recently"*.
 */

import type { DegradedReason, Term } from '../domain/vocabulary';

/**
 * The footer, drawn once under a list.
 *
 * It names no term and no person: what it reports is that the platform is not finished, which
 * is true of every candidate equally.
 */
export const NOT_ON_THIS_PLATFORM_FOOTER =
  "Some of what the engine weighs isn't on this platform yet, so it isn't counted for anybody.";

/**
 * One row per term, **both sides side by side**.
 *
 * A full `Record` rather than a partial one, so a term added to the vocabulary forces a
 * decision here rather than silently having no sentence — and one table rather than two, so
 * the two readings of a term are written together and the asymmetry between them is visible
 * where it exists rather than hiding in the gap between two lists.
 *
 * `null` where a side cannot be the one with the gap. Level fit and distance never degrade at
 * all — both are computed from facts every player has by existing — and a *your* record is
 * never the gap, because the term reads theirs.
 */
interface WhoseGap {
  readonly you: string | null;
  readonly them: string | null;
  /** The surface's own — the term was not read for anybody here. `null` where none does that. */
  readonly here: string | null;
}

const NEVER_STANDS_DOWN: WhoseGap = { you: null, them: null, here: null };

/** A term whose gap is only ever a person's. */
const NEVER_BY_A_SURFACE = { here: null } as const;

const DEGRADED: Readonly<Record<Term, WhoseGap>> = {
  LEVEL_FIT: NEVER_STANDS_DOWN,
  PREDICTED_BALANCE: NEVER_STANDS_DOWN,
  INTENT_ALIGNMENT: {
    you: "You haven't said what kind of evening you're after",
    them: "They haven't said what kind of evening they're after",
    here: "What kind of evening you're each after isn't read here",
  },
  RELIABILITY: { you: null, them: 'Nothing on their record yet', ...NEVER_BY_A_SURFACE },
  AVAILABILITY_OVERLAP: {
    you: 'Your week is blank',
    them: 'Their week is blank',
    ...NEVER_BY_A_SURFACE,
  },
  PLAYING_STYLE: {
    you: "You haven't picked any on-court tags",
    them: "They haven't picked any on-court tags",
    ...NEVER_BY_A_SURFACE,
  },
  SOCIAL_VIBE: {
    you: "You haven't picked any tags about the evening",
    them: "They haven't picked any tags about the evening",
    ...NEVER_BY_A_SURFACE,
  },
  DISTANCE: NEVER_STANDS_DOWN,
};

/**
 * What a stood-down term says, or nothing when there is no sentence for that pair.
 *
 * `NOT_YET_ON_THIS_PLATFORM` returns nothing **by design**: its sentence is the footer above,
 * and a per-row copy of it is the repetition the two tiers exist to prevent.
 */
export function degradedLine(term: Term, reason: DegradedReason): string | undefined {
  switch (reason) {
    case 'NOT_YET_ON_THIS_PLATFORM':
      return undefined;
    case 'NOTHING_FROM_YOU':
      return DEGRADED[term].you ?? undefined;
    case 'NOTHING_FROM_THEM':
      return DEGRADED[term].them ?? undefined;
    case 'NOT_READ_ON_THIS_SURFACE':
      return DEGRADED[term].here ?? undefined;
  }
}
