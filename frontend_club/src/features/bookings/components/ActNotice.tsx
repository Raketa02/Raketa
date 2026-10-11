import { Notice } from '@/ui/Notice';

import type { BookingActState } from '../actions';
import { actRefusal, BOOKINGS_COPY } from '../copy';
import type { Accepted } from '../mappers';

const COPY = BOOKINGS_COPY.done;

/** Before any act: nothing to say. */
export const NOTHING_DONE: BookingActState = { done: null, refusal: null };

/** What the club's yes came to, said about the game. */
function AcceptNotice({ name, accepted }: { name: string; accepted: Accepted }) {
  switch (accepted.outcome) {
    case 'BOOKED':
      return <Notice tone="success">{COPY.accepted(name, accepted.court)}</Notice>;
    case 'WAITING_FOR_A_PAYMENT':
      return (
        <Notice tone="success">
          {COPY.acceptedWaitingFor[accepted.timeTo](name, accepted.until)}
        </Notice>
      );
    case 'CALLED_OFF':
      return <Notice tone="info">{COPY.noTimeToPay(name)}</Notice>;
    case 'SEAT_OPENED':
      return <Notice tone="info">{COPY.seatOpened(name)}</Notice>;
  }
}

/**
 * **What came of the last act on a game**, over the list: booked, refused, moved or cancelled,
 * said about the game; a yes that waits on one player's card or payment, with until when; a yes
 * that came to nobody paying, said plainly; or what was refused.
 */
export function ActNotice({
  state,
  clubName,
}: {
  state: BookingActState;
  /** As the players read it. */
  clubName: string;
}) {
  if (state.refusal !== null) {
    return <Notice tone="error">{actRefusal(state.refusal, clubName)}</Notice>;
  }
  const { done } = state;
  if (done === null) return null;
  switch (done.act) {
    case 'accept':
      return <AcceptNotice name={done.name} accepted={done.accepted} />;
    case 'refuse':
      return <Notice tone="success">{COPY.refused(done.name)}</Notice>;
    case 'move':
      return <Notice tone="success">{COPY.moved(done.name, done.court)}</Notice>;
    case 'cancel':
      return <Notice tone="success">{COPY.cancelled(done.name, done.givesBack)}</Notice>;
  }
}
