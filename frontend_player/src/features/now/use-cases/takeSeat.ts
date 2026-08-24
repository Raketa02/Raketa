/**
 * Take the seat an offer named.
 *
 * A thin pass-through, and `ADR-0009`'s escape hatch covers exactly that: whether
 * the seat is still there is the aggregate's question and the client has no
 * weaker second opinion to hold about it. What comes back is what is true now,
 * for a tap that applied and for a tap that did not alike (`ADR-0070`).
 *
 * The sport goes out on the request and is **not** read again on the way back:
 * the answer being mapped is the answer to *this* tap, and the two regions in it
 * were composed under the chip that was sent. Which cache entry they belong to is
 * the hook's, for the same reason.
 */

import { takeSeat as postSeat } from '../api/seatApi';
import type { SeatAnswer } from '../domain/ComposedScreen';
import type { SportFilter } from '../mappers/codes';
import { toSeatAnswer } from '../mappers/nowMappers';

export interface TakeSeatOptions {
  readonly matchId: string;
  readonly sport: SportFilter;
  readonly signal?: AbortSignal;
}

export function takeSeat({ matchId, sport, signal }: TakeSeatOptions): Promise<SeatAnswer> {
  return postSeat({ matchId, sport, signal }).then(toSeatAnswer);
}
