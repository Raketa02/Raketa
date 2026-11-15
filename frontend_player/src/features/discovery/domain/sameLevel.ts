/**
 * **A Same competitive level player** — somebody whose level in a sport the reader also plays is
 * closest, so a competitive game between them would be even
 * ([#802](https://github.com/Raketa02/Raketa/issues/802); ADR-0204 §4; the Home rows mechanics §6;
 * the backend's #794 `SameLevelPlayerSchema`).
 *
 * The rules are the server's — who is on the row, the % even (the app's Forecast with one player a
 * side, which **nothing on this client computes**), the evenest shared sport, fresh before gaps — and
 * this feature draws its answer. What is left here is **the gap in words**, which the words key by,
 * whether a card says *N sports ›*, and where a request from the row was found.
 */

import type { FoundIn, FriendRelation } from '@/features/friends/types';
import type { Sport } from '@/shared/vocabulary/sport';

/**
 * **You and them in one sport you both hold a level in** — a card's pairing, and one block of the
 * comparison sheet.
 */
export interface LevelComparison {
  readonly sport: Sport;
  /** The reader's Level in the sport — *You 2,71*. */
  readonly yourLevel: number;
  /** Theirs — *zofia.b 2,69*. */
  readonly theirLevel: number;
  /** How even a game between the two would be — the server's, 0–96: *91% EVEN*. */
  readonly percentEven: number;
  /** Their level less the reader's, to the hundredth, signed: *0,02 below you*. */
  readonly levelGap: number;
  /** The reader's band as the rating published it — the bar's bold name (*Established*). */
  readonly yourBand: string;
}

export interface SameLevelPlayer {
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Their first photograph; absent draws their court poster. */
  readonly photoUrl?: string;
  /** **The sport the card shows** — the evenest the two share, or See all's chosen sport. */
  readonly shown: LevelComparison;
  /** **Every** sport the two share, most even first — the comparison sheet's blocks. */
  readonly sports: readonly LevelComparison[];
  /** Where the reader stands with them — the round friend button. */
  readonly relation: FriendRelation;
}

/**
 * **Where a request from this row was found** — the card's round button, the comparison sheet's
 * worded one and the record a face opens all send it, **with the card's sport**: the other person's
 * Home reads *Your level in padel · 91% even* (the mechanics §12).
 */
export function foundAtSameLevel(sport: Sport): FoundIn {
  return { from: 'SAME_LEVEL', sport };
}

/**
 * **The gap in words** (the mechanics §6.4; the words §31.5) — their level less the reader's:
 *
 * | Gap | Words |
 * | --- | --- |
 * | below 0 | *0,02 below you* |
 * | above 0 | *0,09 above you* |
 * | rounds to 0,00 | *Same level* |
 */
export type LevelGap =
  | { readonly kind: 'below'; readonly gap: number }
  | { readonly kind: 'above'; readonly gap: number }
  | { readonly kind: 'same' };

/**
 * The served gap, read to the hundredth it was sent to — a level gap travels as a float, and
 * 2,69 − 2,71 is −0,0199… in binary, which is still two hundredths.
 */
export function levelGapOf(levelGap: number): LevelGap {
  const hundredths = Math.round(levelGap * 100);
  if (hundredths === 0) return { kind: 'same' };
  return hundredths < 0
    ? { kind: 'below', gap: -hundredths / 100 }
    : { kind: 'above', gap: hundredths / 100 };
}

/**
 * ***N sports ›*** (the mechanics §6.3) — how many sports the two share, **only with more than
 * one**: with one, the card's footer is the gap alone and there is no sheet to open.
 */
export function moreSportsOf(player: SameLevelPlayer): number | undefined {
  return player.sports.length > 1 ? player.sports.length : undefined;
}
