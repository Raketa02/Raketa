/**
 * Where a seat is, in the only two terms a listener can use: **a side, and a role** — and the
 * one rule that reads them off a line-up.
 *
 * The vocabulary is **H-25's**, and [`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §7 puts *a rule somebody could be wrong about* beside its vocabulary and the words for it in a
 * presentation file (`seatPlacePresentation.ts`, one file over). Somebody can be very wrong about
 * which half is yours.
 *
 * ## Why this is `shared/vocabulary` and not `play/domain/`
 *
 * It began in `features/play/domain/lineup.ts`, because Play's builder was the only court a
 * listener placed seats on. The group page's Friends court says the same places in the same
 * words, and it may not import `features/play/` — the loop
 * [#569](https://github.com/Raketa02/Raketa/issues/569) removes — so the vocabulary and its rule
 * came below both ([#574](https://github.com/Raketa02/Raketa/issues/574)). **What stayed behind is
 * everything the builder does with a place**: which half it is on for the forecast, which seat may
 * be vacated, and what a tap means.
 */

/**
 * One seat of a line-up, as its **places** read it: yours, somebody's, or nobody's.
 *
 * Narrower than Play's builder seat, which also knew whether its occupant had already accepted:
 * where a seat is has never depended on that, so the rule takes the one fact it reads and a richer
 * seat passes straight in.
 */
export interface LineUpSeat {
  readonly kind: 'you' | 'player' | 'empty';
}

/**
 * The three places, in the order a court lists them.
 *
 * Three values and not four, because *their partner* is a role nobody on a court is seated
 * relative to: a listener places the far half by its side alone.
 */
export const SEAT_PLACES = ['YOUR_SIDE', 'YOUR_PARTNER', 'THEIR_SIDE'] as const;

export type SeatPlace = (typeof SEAT_PLACES)[number];

/**
 * Side and role for every seat, in seat order — **the one thing the drawing cannot say.**
 *
 * The court's coordinates are per Sport and `theme.size.court.seats` lists them *your side
 * first*, so a half is a slice of that list and nothing else. **H-25 is why it cannot be the
 * geometry**: squash has no net, both players stand on the same half of the drawing, and a
 * rule that read the far side off a `y` above the middle would seat both of you on your own
 * side in one Sport out of four, with nothing on screen to see.
 *
 * **And a side follows you.** Swap mode is *change sides, never seats*, so you can end up in
 * the far half — at which point that half is yours and the one you started in is theirs. A
 * place read off the index alone would keep calling it theirs.
 *
 * A court always seats you. One that does not reads as the court it started as — you in seat
 * 0 — rather than as a court with two far halves, which is a state no screen could describe.
 */
export function seatPlaces(seats: readonly LineUpSeat[]): readonly SeatPlace[] {
  const half = Math.max(1, seats.length / 2);
  const found = seats.findIndex((seat) => seat.kind === 'you');
  const yours = found === -1 ? 0 : found;
  const yourHalf = Math.floor(yours / half);

  return seats.map((_, at) => {
    if (at === yours) return 'YOUR_SIDE';
    return Math.floor(at / half) === yourHalf ? 'YOUR_PARTNER' : 'THEIR_SIDE';
  });
}
