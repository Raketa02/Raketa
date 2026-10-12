/**
 * **The reliability filter's switch** — *Play only with players of at least High reliability*, or
 * *at least Medium*, or off
 * ([ADR-0195](../../../../../docs/adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
 * §6, [#662](https://github.com/Raketa02/Raketa/issues/662)).
 *
 * Three positions and two facts about them, which is the whole of what this client decides:
 *
 * - **the position is read off the record** — the served `minimum`, or *Off* where none is set,
 *   never a position this phone remembered;
 * - **Off is written as `null`**, the route's own word for the state every profile starts in.
 *
 * Everything the filter *does* — which pairs it keeps apart, that it acts both ways and from then
 * on, that yeses already given stand and New passes — is the server's, applied on every deal and
 * never re-derived here.
 */

import {
  RELIABILITY_MINIMUMS,
  type ReliabilityFilter,
  type ReliabilityMinimum,
} from './playerRecord';

/** Off first, then the two bands a court-mate must be at least, looser first. */
export const FILTER_POSITIONS = ['OFF', ...RELIABILITY_MINIMUMS] as const;

export type FilterPosition = (typeof FILTER_POSITIONS)[number];

/** Where the switch stands, as the record says it is saved. */
export function filterPosition(filter: ReliabilityFilter): FilterPosition {
  return filter.minimum ?? 'OFF';
}

/** What a position writes: the band, or `null` for Off. */
export function minimumOf(position: FilterPosition): ReliabilityMinimum | null {
  return position === 'OFF' ? null : position;
}
