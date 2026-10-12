import { Notice } from '@/ui/Notice';

import type { BookingActState, Done } from '../actions';
import { actRefusal, BOOKINGS_COPY, courtWithKind } from '../copy';

const COPY = BOOKINGS_COPY.done;

/** Before any act: nothing to say. */
export const NOTHING_DONE: BookingActState = { done: null, refusal: null };

/**
 * **What a cancel came to**, said against what the dialog said it would do: the cancel decides
 * afresh, so the court it named may have been taken, or a court come free, in between (Q122).
 */
function cancelled(done: Extract<Done, { act: 'cancel' }>): string {
  const { name, landed, foretold, givesBack } = done;
  if (landed.outcome === 'MOVED') {
    const to = courtWithKind(landed.court);
    if (foretold?.outcome === 'CALLED_OFF') return COPY.movedAfterAll(name, to);
    if (foretold?.outcome === 'MOVED' && foretold.court.id !== landed.court.id) {
      return COPY.movedInstead(foretold.court.name, name, to);
    }
    return COPY.movedByCancel(name, to);
  }
  if (foretold?.outcome === 'MOVED') {
    return COPY.calledOffInstead(foretold.court.name, name, givesBack);
  }
  return COPY.calledOff(name, givesBack);
}

/**
 * **What came of the last act on a game**, over the list: moved, moved by a cancel or called off,
 * said about the game, or what was refused.
 */
export function ActNotice({ state }: { state: BookingActState }) {
  if (state.refusal !== null) {
    return <Notice tone="error">{actRefusal(state.refusal)}</Notice>;
  }
  const { done } = state;
  if (done === null) return null;
  switch (done.act) {
    case 'move':
      return <Notice tone="success">{COPY.moved(done.name, courtWithKind(done.court))}</Notice>;
    case 'cancel':
      return <Notice tone="success">{cancelled(done)}</Notice>;
  }
}
