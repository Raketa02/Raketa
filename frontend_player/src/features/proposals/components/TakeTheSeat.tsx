/**
 * ***I'm in · 27 zł* on a rescue** — a booked game's open seat taken and paid for at once
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3.1, A4.3; the mechanics
 * §10.1), from a rescue's details and from a *Seats to fill* row.
 *
 * **The fill is the deck's** (`useFillYes`): with nothing saved the payment setup opens first and the
 * join lands once a method is; every rescue join counts ten seconds behind *Undo* (Q74) — the button
 * busy *Booking…* meanwhile — and then pays, raising *It's a game!*; a second booking while one
 * counts says *one at a time*. A lost race is the fill's to say: *Someone just took it*.
 *
 * Volt, as the row and the details draw it: the one door on the surface that books.
 */

import { showToast } from '@/shared/store/toast.store';
import { Button, type ButtonSize } from '@/shared/ui';

import type { DealtIn, YesOn } from '../domain/fill';
import { useFillYes } from '../hooks/useFillYes';
import { useLatest } from '../hooks/useLatest';

import { seatButtonLabel, seatButtonSpoken } from './deckPresentation';
import { FILL_COPY } from './fillCopy';

export interface TakeTheSeatProps {
  /** The rescue — its booking's id, and its sides when the surface holds them. */
  readonly seat: YesOn;
  /** The group, sport and kind the seat is offered in — what a join re-reads. */
  readonly dealtIn: DealtIn;
  /** *27 zł* — what the join charges. */
  readonly share: string;
  readonly size: ButtonSize;
  /** The screen to leave once the seat is taken — the details; nothing on a row. */
  readonly leave?: () => void;
}

export function TakeTheSeat({ seat, dealtIn, share, size, leave }: TakeTheSeatProps) {
  const fill = useFillYes(dealtIn, leave);
  const counting = fill.counting === seat.proposalId;

  const take = () => {
    if (counting) return;
    if (fill.held(seat)) {
      showToast({ message: FILL_COPY.undo.oneAtATime });
      return;
    }
    if (fill.setUpFirst(() => takeLater.current())) return;
    fill.book(seat);
  };
  /** `take` as of the last render — what the setup's `then` calls. */
  const takeLater = useLatest(take);

  return (
    <Button
      label={seatButtonLabel(share)}
      accessibilityLabel={seatButtonSpoken(share)}
      variant="volt"
      size={size}
      busy={counting}
      busyLabel={FILL_COPY.undo.booking}
      onPress={take}
    />
  );
}
