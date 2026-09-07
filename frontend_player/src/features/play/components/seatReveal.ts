/**
 * **How many seats have landed** — the fill's stagger, as a number a court can draw.
 *
 * `useHeldWait` answers *is the wait still up*; this answers *how much of the answer is on
 * screen yet*, which is the half the builder needs to seat people **one at a time** rather
 * than all at once at the end of a floor. The two are the same beat read at two resolutions,
 * and both are over a **completed answer**: nothing here delays a request, and the whole
 * line-up is in memory before the first seat appears.
 *
 * ## Why the court fills rather than arriving filled
 *
 * `motion.hold.fill` was always `650 plus 550 a seat`, and the 550 is booked to *"the
 * animation it drives"* (`theme.motion.hold`) — an animation that had no drawing. The latch
 * covered the screen for the sum and then took itself away over a court that was already
 * complete, so the stagger was paid for and never seen. What it is for is the sensation the
 * court is actually describing: people arriving at a game, one after another, which is what
 * `POST /lineups` has just done.
 *
 * ## The collapse is `searchingWait`'s, and it is the same collapse
 *
 * `seatLandsAtMs` puts every seat on the floor itself when `collapsed`, so a listener or a
 * player who asked the OS to calm things down gets the whole court in one commit — *"none of
 * the craft and all of the latency"* is exactly what a staggered court would be for them. The
 * floor underneath survives, because a hold is not an animation.
 *
 * ## The timers are set once, from the edge
 *
 * One `setTimeout` per seat, armed on the rising edge of `landed` and cleared together. An
 * effect keyed on the count would re-arm every seat on every landing, which is how a stagger
 * turns into a court that fills at a rate nobody chose.
 */

import { useEffect, useState } from 'react';

import { seatLandsAtMs } from './searchingWait';

/**
 * @param landed whether an answer is on the way in — `false` while the request is in flight,
 *   and while there is nothing being filled at all.
 * @param seats the **court's** seat count, not the answer's: the presentation is how long a
 *   court takes to fill, and a court is four seats whether or not four people sat down.
 * @param collapsed reduced motion or a screen reader — `useCollapsedPresentation()`.
 * @returns how many seats, in seat order, have landed. `seats` once the last one has.
 */
export function useSeatsRevealed(landed: boolean, seats: number, collapsed: boolean): number {
  const [revealed, setRevealed] = useState(0);

  useEffect(() => {
    if (!landed) {
      setRevealed(0);
      return;
    }

    const timers = Array.from({ length: seats }, (_, at) =>
      setTimeout(() => setRevealed(at + 1), seatLandsAtMs(at, collapsed)),
    );

    return () => timers.forEach(clearTimeout);
  }, [landed, seats, collapsed]);

  return revealed;
}
