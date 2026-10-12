import { Notice } from '@/ui/Notice';

import type { BookingActState } from '../actions';
import { actRefusal, BOOKINGS_COPY } from '../copy';

const COPY = BOOKINGS_COPY.done;

/** Before any act: nothing to say. */
export const NOTHING_DONE: BookingActState = { done: null, refusal: null };

/**
 * **What came of the last act on a game**, over the list: moved or cancelled, said about the
 * game, or what was refused.
 */
export function ActNotice({ state }: { state: BookingActState }) {
  if (state.refusal !== null) {
    return <Notice tone="error">{actRefusal(state.refusal)}</Notice>;
  }
  const { done } = state;
  if (done === null) return null;
  switch (done.act) {
    case 'move':
      return <Notice tone="success">{COPY.moved(done.name, done.court)}</Notice>;
    case 'cancel':
      return <Notice tone="success">{COPY.cancelled(done.name, done.givesBack)}</Notice>;
  }
}
