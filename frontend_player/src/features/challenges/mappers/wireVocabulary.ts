/**
 * The agreement between `domain/standing.ts` and the contract — asserted by the compiler.
 *
 * The same mechanism `features/play/mappers/wireVocabulary.ts` uses, over the one `Exact` in
 * `@/shared/vocabulary/wireAgreement`: the copy deck must be keyed by the generated union, and
 * generated types may be read only in `api/` or `mappers/`. A standing added, removed or renamed on the contract fails here, at
 * `pnpm typecheck`, in the file whose whole job is saying so.
 */

import type { components } from '@/generated/schema';
import type { Exact } from '@/shared/vocabulary/wireAgreement';

import type { SeatAnswer, Standing } from '../domain/standing';

export const STANDING_AGREES: Exact<Standing, components['schemas']['Standing']> = true;

/**
 * The three answers a seat can carry — and *awaiting* is the absence of one on both sides.
 *
 * It joined the file with the pair rule: `playersStillIn` drops the seat that declined or
 * lapsed, so a fourth answer added to the contract would silently keep somebody in a game they
 * had left.
 */
export const SEAT_ANSWER_AGREES: Exact<SeatAnswer, components['schemas']['SeatAnswer']> = true;
