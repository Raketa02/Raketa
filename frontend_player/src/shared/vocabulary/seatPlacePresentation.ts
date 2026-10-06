/**
 * **What a court's seats are called to a listener** — the place a seat's spoken name opens with,
 * the seat's name itself, and the court's summary that precedes them
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §20.4).
 *
 * Four seats announced against nothing are four seats a listener cannot place, and a seat named
 * by its index is a seat placed by the drawing — which H-25 forbids (`seatPlace.ts`). So a court
 * says its sport and how full it is first, and each seat says its side and role.
 *
 * ## Why this is `shared/vocabulary` and not Play's accessibility presentation
 *
 * They began in `features/play/components/accessibilityPresentation.ts`, beside every other name
 * a Play control is spoken by. The group page's Friends court and its Games card say the same
 * sentences — *a group's court and a line-up's say the same thing* — and may not import
 * `features/play/`, the loop [#569](https://github.com/Raketa02/Raketa/issues/569) removes. So the
 * sentences a second feature would have written identically came below both
 * ([#574](https://github.com/Raketa02/Raketa/issues/574)). **What stayed behind is what only a
 * line-up being built says**: a seat the record no longer describes, the engine's reason a seat
 * is empty, and the clear badge.
 */

import { counted } from '@/shared/formatting/counted';
import { formatLevel } from '@/shared/formatting/ratingFormat';

import type { SeatPlace } from './seatPlace';

/**
 * The place as a seat label **opens** with it — capitalised, because it starts a sentence.
 *
 * Exported for the sentences that open the same way about a seat a caller knows more about.
 */
export const PLACE_CLAUSE: Readonly<Record<SeatPlace, string>> = {
  YOUR_SIDE: 'Your side',
  YOUR_PARTNER: 'Your side, your partner',
  THEIR_SIDE: 'Their side',
};

/** Who is in a seat, as the seat's spoken name needs them. */
export type SeatOccupant =
  | { readonly kind: 'you' }
  | { readonly kind: 'player'; readonly name: string; readonly level: number }
  | { readonly kind: 'empty' };

/**
 * `Your side, you` · `Your side, your partner, Marek, level 2,92` · `Their side, Ana, level
 * 3,10` · `Their side, empty`.
 *
 * A seat is a `button` in every case. Selected for a swap it takes
 * `accessibilityState={{ selected: true }}`, which §20.2 substitutes for the `pressed` React
 * Native does not ship — the state is never written into the name.
 *
 * **The 9,5pt seat label does not earn `allowFontScaling={false}`.** Part 13 permits that
 * escape only *"inside the level bar's drawn geometry"*, and §15 already ruled the court's
 * case the other way: *"a seat label may truncate visually; a sentence may not, and a spoken
 * name never does."* The visible label scales and truncates; this one is whole.
 */
export function seatLabel(place: SeatPlace, occupant: SeatOccupant): string {
  const where = PLACE_CLAUSE[place];
  switch (occupant.kind) {
    case 'you':
      return `${where}, you`;
    case 'player':
      return `${where}, ${occupant.name}, level ${formatLevel(occupant.level)}`;
    case 'empty':
      return `${where}, empty`;
  }
}

/**
 * A court as a sentence needs it: which Sport, and how full it is.
 *
 * One type because the three never travel apart — a count with no Sport places nothing, and a
 * Sport with no count says nothing.
 */
export interface CourtSummary {
  readonly sportName: string;
  readonly filled: number;
  readonly seats: number;
}

/**
 * The court's summary element, which **precedes** the seats: `Padel, 3 of 4 seats filled.`
 *
 * Four seats announced against nothing are four seats a listener cannot place. The sport is
 * the served name; the count routes through `counted()` for §19's reason, which is that no
 * string in this app hardcodes an `s`.
 */
export function courtSummaryLabel(court: CourtSummary): string {
  return `${court.sportName}, ${court.filled} of ${counted(court.seats, 'seat filled', 'seats filled')}.`;
}
