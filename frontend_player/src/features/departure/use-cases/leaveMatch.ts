/**
 * Leave, at the outcome she was looking at.
 *
 * **The quote goes back unread.** It is the label the screen was showing when she
 * decided, and the server refuses if the live outcome has since become strictly
 * worse — so anything this layer did to it would be changing the basis of a
 * comparison it does not make. `ADR-0033`: a label, never an amount.
 *
 * **The key comes from the caller** rather than being minted here, because *one
 * key per visit to the screen* is a fact about the screen and not about the call:
 * minting one here would make every press a fresh command, and the second press of
 * a departure whose first answer was lost would come back as *she has already
 * left* — true, and the wrong thing to tell somebody asking whether her first tap
 * worked. See `domain/requestKey.ts`.
 *
 * The refusal path is not here either, and that is `ADR-0070`: a departure that no
 * longer applies is a 200 carrying what a success carries. This resolves; the
 * screen reads `applied` and says which of the two happened.
 */

import { leaveMatch as postDeparture } from '../api/departureApi';
import type { DepartureAnswer } from '../domain/Departure';
import { toDepartureAnswer } from '../mappers/departureMappers';

export interface LeaveMatchOptions {
  readonly matchId: string;
  readonly quote: string;
  readonly idempotencyKey: string;
  readonly signal?: AbortSignal;
}

export function leaveMatch({
  matchId,
  quote,
  idempotencyKey,
  signal,
}: LeaveMatchOptions): Promise<DepartureAnswer> {
  return postDeparture({ matchId, quote, idempotencyKey, signal }).then(toDepartureAnswer);
}
