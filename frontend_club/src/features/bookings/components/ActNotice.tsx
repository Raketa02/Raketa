import { Notice } from '@/ui/Notice';

import type { BookingActState } from '../actions';
import { actRefusal, BOOKINGS_COPY } from '../copy';

const COPY = BOOKINGS_COPY.done;

/** Before any act: nothing to say. */
export const NOTHING_DONE: BookingActState = { done: null, refusal: null };

/**
 * **What came of the last act on a game**, over the list: booked, refused, moved or cancelled,
 * said about the game; a yes whose payment did not go through, said plainly; or what was refused.
 */
export function ActNotice({ state }: { state: BookingActState }) {
  if (state.refusal !== null) return <Notice tone="error">{actRefusal(state.refusal)}</Notice>;
  const { done } = state;
  if (done === null) return null;
  switch (done.act) {
    case 'accept':
      return done.accepted.booked ? (
        <Notice tone="success">{COPY.accepted(done.name, done.accepted.court)}</Notice>
      ) : (
        <Notice tone="info">{COPY.seatOpened(done.name)}</Notice>
      );
    case 'refuse':
      return <Notice tone="success">{COPY.refused(done.name)}</Notice>;
    case 'move':
      return <Notice tone="success">{COPY.moved(done.name, done.court)}</Notice>;
    case 'cancel':
      return <Notice tone="success">{COPY.cancelled(done.name)}</Notice>;
  }
}
