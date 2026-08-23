/**
 * Which claim each shelf makes, and the door at the end of it.
 *
 * **The wire carries a shelf code and never a title.** `ADR-0070` put shelf
 * presence and shelf order on the server precisely so both can change without an
 * app release, and left the words here: *"the words were never the part that
 * needed to move without a client release; shelf presence and shelf order
 * were."*
 *
 * **Every shelf ends in a card into Find**, pre-filtered by the shelf's own
 * claim plus the sport the client is already filtered to — a shelf running out
 * is a door and not a wall. The tail card is **not** in the contract; the client
 * appends it, and this table is what it routes on.
 */

import type { FindClaim, ShelfCopy } from '../domain/presentation';

import type { AssertTrue, IsClosedUnion, ShelfCode, SportFilter } from './codes';

/**
 * Total over the six codes.
 *
 * `recentlyViewed` has a row and **no consumer**. `ADR-0085` keeps the value
 * reserved on the wire and never composes it, so the shelf's return is a server
 * change rather than a client release — which is only true if the row is already
 * here. What the contract guarantees is that the value is reserved, not that
 * anything draws it, and no render path is built for it in v1.
 *
 * `bestFit` and `sameLevel` are two codes for one shelf: the second is what
 * shelf 1 is retitled to when nothing clears its floor, which is how it never
 * goes silent.
 */
export const SHELF_COPY: Readonly<Record<ShelfCode, ShelfCopy>> = {
  bestFit: {
    title: 'Best fit for you',
    claim: { seats: 'open', order: 'fit', kind: 'matches' },
  },
  sameLevel: {
    title: 'Same level',
    claim: { seats: 'open', order: 'level', kind: 'matches' },
  },
  fullWorthWaiting: {
    title: 'Full, but worth waiting for',
    claim: { seats: 'full', order: 'fit', kind: 'matches' },
  },
  recentlyViewed: {
    title: 'Recently viewed',
    claim: { seats: 'any', order: 'fit', kind: 'matches' },
  },
  newPlayers: {
    title: 'New on Raketa',
    claim: { seats: 'any', order: 'newest', kind: 'players' },
  },
  newClubs: {
    title: 'New clubs',
    claim: { seats: 'any', order: 'newest', kind: 'clubs' },
  },
};

/** Fails to compile if `ShelfCode` ever arrives as a bare string. */
export type ShelfCodeIsClosed = AssertTrue<IsClosedUnion<ShelfCode>>;

/** A shelf's claim, plus the sport the client holds. Find is opened with both. */
export interface FindPreFilter extends FindClaim {
  readonly sport: SportFilter;
}

/** The title, or `undefined` for a shelf code this build has never heard of. */
export function shelfTitle(code: string): string | undefined {
  return (SHELF_COPY as Readonly<Record<string, ShelfCopy | undefined>>)[code]?.title;
}

/**
 * What the tail card opens Find with.
 *
 * `undefined` for an unknown shelf code — which is the same answer as *do not
 * draw the tail card*. A door this build cannot address is worse than no door.
 */
export function findPreFilter(code: string, sport: SportFilter): FindPreFilter | undefined {
  const shelf: ShelfCopy | undefined = (
    SHELF_COPY as Readonly<Record<string, ShelfCopy | undefined>>
  )[code];
  return shelf === undefined ? undefined : { ...shelf.claim, sport };
}
