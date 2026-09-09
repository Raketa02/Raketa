/**
 * The **interactive** court — the one you build a line-up on.
 *
 * *"`CourtBuild` owns the swap truth table, the selection ring, the clear badge and the
 * guard toasts"*
 * ([`the-play-components.md`](../../../../../../docs/specs/matchmaking/the-play-components.md)
 * §4). Every number it draws is `Court`'s and every rule it applies is `domain/lineup`'s; what
 * is here is the wiring between them, and the one piece of state neither of them can hold.
 *
 * ## It is a controlled component over the line-up, and holds only the selection
 *
 * [#228](https://github.com/Raketa02/Raketa/issues/228) §6 put the line-up in
 * `playSession.store` and the pending seat replacement in route-local state, so who is seated
 * arrives as a prop and every change leaves through a callback: this component writes nothing.
 *
 * **The seat selected for a swap is the exception, and it is not a line-up fact.** It is
 * meaningless off this court, it dies with the screen, and hoisting it would make every screen
 * drawing a court re-implement the three-way toggle — select, deselect, trade — that the truth
 * table already spells out. The swap **toggle** is a prop, because the switch beside the court
 * is the screen's row and 6.12's control announces itself.
 *
 * **Turning the toggle off clears the selection**, adjusted during render rather than in an
 * effect: a seat left ringed under a toggle that is now off is a selection a player cannot
 * cancel, and re-enabling the toggle would restore a partner they had forgotten choosing.
 *
 * ## The one guard toast is here because the refusal is
 *
 * A tap that resolves to `REFUSE` never reaches the screen — there is nothing for a screen to
 * do with it — so the sentence is raised here, through `seatGuardLine`, and the toast queue is
 * `shared/`'s single host ([9.3](../../../../../docs/design-system.md#93-layer-order)). It
 * belongs to the **replacement** rather than to the trade: your own seat is freely movable
 * across the net, which is what *change sides, never seats* means, and it is why the sentence
 * names the toggle.
 *
 * **The second toast is gone and the seat is silent instead**
 * ([ADR-0150](../../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)
 * §8): an accepted seat is not a control, so it has no refusal to make and the truth table
 * answers `NOTHING`. What draws the rule is the missing clear badge and the tap that does not
 * answer, which is #324's *no copy, no pill, no disabled control* applied to a seat.
 *
 * The clear badge draws no third refusal either: `seatIsClearable` decides whether it exists at
 * all, so the × a player cannot use is never on screen to press.
 *
 * ## There is no hold, and a seat does two things rather than three
 *
 * [#285](https://github.com/Raketa02/Raketa/issues/285) put a **shortcut** to `SH.whyfit` on a
 * long press, beside the forecast card's names row. The gesture is gone: the card's side rows
 * draw each player as their own face and handle now, so the route is a 44pt control with a
 * picture of the person on it, and a second way in that nothing advertises, nothing announces
 * and no accessibility API can perform was never carrying anybody the row was not.
 *
 * `seatIsExplainable` went with it. *Is there a breakdown behind this person* is still asked,
 * but it is asked where the control is — the row tests the candidate row it is about to hand
 * the sheet, which is the question itself rather than a proxy for it, and a second spelling
 * living on here would be a rule with no reader.
 *
 * A tap on a seat is therefore the whole of what a seat does: the pool, or a swap.
 */

import { useState } from 'react';

import { showToast } from '@/shared/store/toast.store';
import { Court, courtSeatSize, type SportKey } from '@/shared/ui';

import { seatIsClearable, seatPlaces, tapSeat } from '../../domain/lineup';
import { seatGuardLine } from '../courtPresentation';

import { CourtSeat, type CourtSeatOccupant } from './CourtSeat';

export interface CourtBuildProps {
  readonly sport: SportKey;
  readonly width: number;
  /** `courtSummaryLabel`'s sentence, placed before the seats. The words are the screen's. */
  readonly summary: string;
  readonly caption?: string;
  readonly sideLabels?: readonly [string, string];
  /**
   * In seat order — **your side first**, which is the order `Court` places them and the order
   * `seatPlaces` reads a side off. You are one of them, and not necessarily the first: a swap
   * moves you across the net, and the side follows you.
   */
  readonly seats: readonly CourtSeatOccupant[];
  /** 6.12's switch, drawn by the screen in its own row. */
  readonly swapping: boolean;
  /** Fill this seat, or replace who is in it — one act, against one seat. */
  readonly onOpenPool: (seat: number) => void;
  /** Trade two seats. A re-arrangement of a response the builder already holds. */
  readonly onSwap: (from: number, to: number) => void;
  readonly onClear: (seat: number) => void;
}

export function CourtBuild({
  sport,
  width,
  summary,
  caption,
  sideLabels,
  seats,
  swapping,
  onOpenPool,
  onSwap,
  onClear,
}: CourtBuildProps) {
  const [selected, setSelected] = useState<number>();
  // React's own answer to *adjust state when a prop changes*: read during render, not in an
  // effect, so no frame is drawn with a selection the toggle no longer permits.
  const [toggle, setToggle] = useState(swapping);
  if (toggle !== swapping) {
    setToggle(swapping);
    setSelected(undefined);
  }

  const size = courtSeatSize(width);
  const places = seatPlaces(seats);

  function press(at: number, occupant: CourtSeatOccupant) {
    const decision = tapSeat({ swapping, selected }, at, occupant);

    switch (decision.kind) {
      case 'OPEN_POOL':
        setSelected(undefined);
        return onOpenPool(decision.seat);
      case 'SELECT':
        return setSelected(decision.seat);
      case 'DESELECT':
        return setSelected(undefined);
      case 'SWAP':
        setSelected(undefined);
        return onSwap(decision.from, decision.to);
      case 'REFUSE':
        return showToast({ message: seatGuardLine(decision.guard) });
      // **An accepted seat is not a control**, so there is nothing to say and nothing to do
      // (ADR-0150 §8). Named rather than a `default`, so a seventh arm on the truth table is a
      // compile error here rather than a tap that silently stops working.
      case 'NOTHING':
        return;
    }
  }

  return (
    <Court sport={sport} width={width} summary={summary} caption={caption} sideLabels={sideLabels}>
      {seats.map((occupant, at) => (
        <CourtSeat
          key={at}
          size={size}
          // A court always seats you, so there is always a place; the fallback is the type
          // system's rather than a state, and it reads as the far half — never as yours.
          place={places[at] ?? 'THEIR_SIDE'}
          occupant={occupant}
          selected={selected === at}
          onPress={() => press(at, occupant)}
          onClear={seatIsClearable(occupant) ? () => onClear(at) : undefined}
        />
      ))}
    </Court>
  );
}
