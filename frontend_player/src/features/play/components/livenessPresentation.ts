/**
 * Why this person moved, and why they are on the list at all.
 *
 * Ten liveness codes and one inclusion code
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §10). Both are
 * **codes only**: there is no field on the wire a Liveness number could be written to, and
 * the two silent signals have no code at all — *"a silent move carries points and no code, so
 * there is no name on the value to print"*. A client inventing a sentence for one would be
 * publishing what the enum was shaped to withhold.
 *
 * **`RECENT_ACTIVITY` is the one to watch.** It is a *reason code*, which is the sanctioned
 * crossing; *"active today"* on a meta line is the refused one (ADR-0106 §5). The wording is
 * deliberately un-datable — *around this week*, never a timestamp, a day or a green dot.
 *
 * **`INTEREST_RECEIVED` and `INTEREST_LIFT` fire for the same person** and are two facts with
 * **one tag** ([#231](https://github.com/Raketa02/Raketa/issues/231), Open #14): the tag is
 * bound to the admitting code, and its sentence replaces the other's.
 */

import type { InclusionReason, LivenessReason } from '../domain/vocabulary';

const LIVENESS: Readonly<Record<LivenessReason, string>> = {
  INTEREST_RECEIVED: 'Wants to play you',
  PREVIOUS_ACCEPT: 'Said yes to you before',
  ANSWER_RATE_AND_SPEED: 'Answers quickly',
  RECENT_ACTIVITY: 'Around this week',
  OVERLAP_PROXIMITY: 'Free around when you are',
  RECIPROCAL_ASYMMETRY: "You're well inside their range",
  NEWCOMER_LIFT: 'New here',
  CHALLENGE_LOAD_SOME: 'A few challenges waiting on them',
  CHALLENGE_LOAD_BUSY: 'Plenty of challenges waiting on them',
  CHALLENGE_LOAD_FULL: 'A full inbox — they may be slow to answer',
};

export function livenessLine(reason: LivenessReason): string {
  return LIVENESS[reason];
}

/**
 * Why they are in the list **at all** — a union of one, and it *admits*.
 *
 * A table rather than a constant, because the shape is what makes a second admitting code a
 * compile error here instead of a tag with no words on it.
 */
const INCLUSION: Readonly<Record<InclusionReason, string>> = {
  INTEREST_LIFT: 'They already said yes to you',
};

export function inclusionLine(reason: InclusionReason): string {
  return INCLUSION[reason];
}

/** The sheet's zone heading over the liveness codes (#233 §7, zone 4). */
export const WHAT_ELSE_MOVED_YOU_HERE = 'What else moved you here';
