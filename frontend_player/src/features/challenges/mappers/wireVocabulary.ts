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

import type { DegradedReason, PairingAbsence } from '../domain/challengeDetail';
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

/**
 * Why a court came back with no cards on it — **two codes, and a third answer that is their
 * absence.**
 *
 * It joined the file with the detail read. An outage drawing the identical absence as an unrated
 * sport is the collapse ADR-0143 §6 refused in as many words, so a third code added to the
 * contract must reach the sentence that names whose gap it was rather than folding into one of
 * the two already written.
 */
export const PAIRING_ABSENCE_AGREES: Exact<
  PairingAbsence,
  components['schemas']['PairingAbsence']
> = true;

/**
 * Whose gap a stood-down term was — `challenges`' own spelling, held equal to the contract.
 *
 * The pair *(term, reason)* is one sentence, and a reason this build cannot read leaves the line
 * as a named gap rather than dropping it: the not-counted list **is** the renormalisation basis
 * the Fit is read against, so a shorter one describes a different number.
 */
export const DEGRADED_REASON_AGREES: Exact<
  DegradedReason,
  components['schemas']['DegradedReason']
> = true;
