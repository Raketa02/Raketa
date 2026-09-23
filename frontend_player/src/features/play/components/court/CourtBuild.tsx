/**
 * The **interactive** court — the one you build a line-up on.
 *
 * *"`CourtBuild` owns the swap truth table, the selection ring and the clear badge"*
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
 * drawing a court re-implement the three-way move — select, deselect, trade — that the truth
 * table already spells out.
 *
 * ## The mode went, and three things went with it
 *
 * A swap was a `switch` the screen drew above the court and handed down as a prop, and this
 * component held a mirror of it so that **turning it off could clear the selection**. Tapping
 * a seat now always means the same thing, so there is no mode, no mirror, and no adjustment
 * during render. What tells a player is a sentence the screen prints above the graphic, and
 * what tells a listener is that same sentence — the toggle used to announce itself.
 *
 * **The two guard toasts went too, because there is nothing left to refuse.** They belonged to
 * the replacement — your own seat and an accepted one may always change sides and never be
 * swapped *out* — and a tap does not replace anybody any more. The clear badge is where a
 * replacement starts now, and it draws no refusal either: `seatIsClearable` decides whether it
 * exists at all, so the × a player cannot use is never on screen to press.
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

import { Court, courtSeatSize, type SportKey } from '@/shared/ui';

import { seatIsClearable, seatPlaces, tapSeat } from '../../domain/lineup';

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
  /** Fill this seat. Only an empty one asks, now that a tap on an occupied seat trades. */
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
  onOpenPool,
  onSwap,
  onClear,
}: CourtBuildProps) {
  const [selected, setSelected] = useState<number>();

  const size = courtSeatSize(width);
  const places = seatPlaces(seats);

  function press(at: number, occupant: CourtSeatOccupant) {
    const decision = tapSeat(selected, at, occupant);

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
