/**
 * **Player reliability, as a record serves it** — the fixture every suite that answers
 * `GET /players/…/record` builds on ([#660](https://github.com/Raketa02/Raketa/issues/660),
 * ADR-0195 §1).
 *
 * The block is **always present** since #659: everyone starts at 100, so a player nothing has
 * happened to reads `100`, `VERY_HIGH`, *New* and every count `0`. That is the default here, and a
 * suite moves only what it is about off it.
 */

import type { Wire } from './transport';

/** Nerea: 100 · New — nothing has happened to her yet, and every count is nought. */
export const NEW_RELIABILITY: Wire['ReliabilitySchema'] = {
  player_score: 100,
  band: 'VERY_HIGH',
  is_new: true,
  turned_up: 0,
  turned_up_of: 0,
  late: 0,
  kept: 0,
  kept_of: 0,
  left_in_dispute: 0,
};

/** Sergio: 75 · High — turned up 12 of 13, kept 13 of 14, late once, nothing left in dispute. */
export const SERGIO_RELIABILITY: Wire['ReliabilitySchema'] = {
  player_score: 75,
  band: 'HIGH',
  is_new: false,
  turned_up: 12,
  turned_up_of: 13,
  late: 1,
  kept: 13,
  kept_of: 14,
  left_in_dispute: 0,
};

export function servedReliability(
  over: Partial<Wire['ReliabilitySchema']> = {},
): Wire['ReliabilitySchema'] {
  return { ...NEW_RELIABILITY, ...over };
}

/**
 * A Members row's reliability for somebody nothing has happened to — `100`, `VERY_HIGH`. Every row
 * carries both since #659; Members has no *New*.
 */
export const NEW_MEMBER_RELIABILITY = {
  player_score: 100,
  reliability_band: 'VERY_HIGH',
} as const satisfies Pick<Wire['GroupMemberSchema'], 'player_score' | 'reliability_band'>;
