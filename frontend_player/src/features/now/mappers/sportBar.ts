/**
 * The sport bar's five chips: what each says, and the order they stand in.
 *
 * **Five fixed chips for every player**, identical whatever she is rated at
 * (`ADR-0084`). A chip for a sport she has never been rated at is kept at a named
 * cost — *hiding it hides the business, and the moment a padel player decides to
 * try squash is the moment we are most valuable to her* — and the dishonest empty
 * message a fixed chip creates is answered by the door (`Raketa02/Raketa#78`,
 * `#94`) rather than by a hidden chip, which is a dead end with no fix at all.
 *
 * Keyed on the generated union like every other table in this layer, so a fifth
 * sport is a compile error here rather than a chip nobody drew. The order is a
 * separate list because a `Record` has no order to assert, and the order is the
 * UI authorities' and is load-bearing: `All` is first because it is the default.
 */

import type { SportChipCopy } from '../domain/presentation';

import type { AssertTrue, IsClosedUnion, SportFilter } from './codes';

/**
 * Total over the five values the request can carry.
 *
 * The four sports keep the registry's own upper-case spelling — one name for one
 * sport — and `all` is lower-case because it is not a sport.
 */
export const SPORT_CHIP_COPY: Readonly<Record<SportFilter, SportChipCopy>> = {
  all: { label: 'All', swatch: undefined },
  PADEL: { label: 'Padel', swatch: 'padel' },
  TENNIS: { label: 'Tennis', swatch: 'tennis' },
  SQUASH: { label: 'Squash', swatch: 'squash' },
  BADMINTON: { label: 'Badminton', swatch: 'badminton' },
};

/** Fails to compile if `SportFilter` ever arrives as a bare string. */
export type SportFilterIsClosed = AssertTrue<IsClosedUnion<SportFilter>>;

/**
 * The bar, left to right: **All · Padel · Tennis · Squash · Badminton**.
 *
 * Both UI authorities fix this order and `ADR-0084` keeps it. A `Record` cannot
 * carry it, so it is written out and `sportBar.test.ts` asserts the two agree in
 * both directions — a sixth chip added to one and not the other is the failure
 * that would otherwise ship a sport nobody can filter to.
 */
export const SPORT_BAR: readonly SportFilter[] = ['all', 'PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'];

/**
 * What the bar starts at on every visit.
 *
 * `all` resolves, server-side, to *the sports this player holds a rating at* —
 * never to every sport on the platform. That is the only reading under which the
 * empty line *"Nothing open in your sports right now"* is true, and the only one
 * under which *Best fit for you* is a claim about the player rather than about
 * our inventory.
 */
export const DEFAULT_SPORT_FILTER: SportFilter = 'all';
