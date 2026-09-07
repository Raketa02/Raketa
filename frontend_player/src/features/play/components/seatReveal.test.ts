/**
 * **The seats landing** — the half of the fill's wait that had never been drawn.
 *
 * `motion.hold.fill` has been `650 plus 550 a seat` since before there was a court to seat
 * anybody on, and `theme.ts` books the 550 to *"the animation it drives"*. Nothing drove it:
 * the latch covered the screen for the sum and lifted onto a court that was already complete.
 * These cases are that arithmetic read the way a player sees it — one seat, then another —
 * and every one of them is a **boundary in time** that no snapshot of a screen could tell
 * apart from the state one millisecond either side of it.
 *
 * The contract that ties the two halves together is asserted here rather than described:
 * **the last seat lands exactly as the floor ends.** `searchingFloorMs` sums how long the
 * court takes to fill and `seatLandsAtMs` says when each seat arrives, and a court that lifted
 * halfway through filling itself is what the sum exists to prevent.
 */

import { act, renderHook } from '@testing-library/react-native';

import { SEAT_STAGGER_MS, searchingFloorMs, seatLandsAtMs } from './searchingWait';
import { useSeatsRevealed } from './seatReveal';

const SEATS = 4;

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

const tick = (ms: number) => act(() => jest.advanceTimersByTime(ms));

function drive(collapsed = false) {
  const { result, rerender } = renderHook(
    ({ landed }: { landed: boolean }) => useSeatsRevealed(landed, SEATS, collapsed),
    { initialProps: { landed: false } },
  );

  return {
    revealed: () => result.current,
    land: (landed: boolean) => act(() => rerender({ landed })),
  };
}

describe('the court filling', () => {
  it('shows nobody while the request is still in flight', () => {
    const fill = drive();

    tick(searchingFloorMs({ kind: 'fill', seats: SEATS, collapsed: false }));

    expect(fill.revealed()).toBe(0);
  });

  /** One seat, then another — which is the sensation the court is describing. */
  it('lands one seat per stagger, and the first on the floor', () => {
    const fill = drive();
    fill.land(true);

    tick(seatLandsAtMs(0, false) - 1);
    expect(fill.revealed()).toBe(0);

    tick(1);
    expect(fill.revealed()).toBe(1);

    tick(SEAT_STAGGER_MS);
    expect(fill.revealed()).toBe(2);

    tick(SEAT_STAGGER_MS);
    expect(fill.revealed()).toBe(3);
  });

  /**
   * The contract between the two halves, and the reason the floor is a sum: a wait that lifted
   * at the bare 650 would take the court away with three seats still to arrive.
   */
  it('lands the last seat exactly as the wait ends', () => {
    const fill = drive();
    fill.land(true);

    tick(searchingFloorMs({ kind: 'fill', seats: SEATS, collapsed: false }));

    expect(fill.revealed()).toBe(SEATS);
    expect(seatLandsAtMs(SEATS - 1, false)).toBe(
      searchingFloorMs({ kind: 'fill', seats: SEATS, collapsed: false }),
    );
  });

  /**
   * **A hold is not an animation.** The stagger is motion and goes; the floor is a hold and
   * stays — so a listener, or a player who asked the OS to calm things down, gets the whole
   * court in one commit and gets it at the same moment everybody else gets the last seat of a
   * two-seat court. None of the craft and none of the latency either.
   */
  it('lands the whole court at once when the presentation is collapsed', () => {
    const fill = drive(true);
    fill.land(true);

    tick(seatLandsAtMs(0, true) - 1);
    expect(fill.revealed()).toBe(0);

    tick(1);
    expect(fill.revealed()).toBe(SEATS);
  });

  /** A court that is no longer being filled is not a court with four people frozen on it. */
  it('forgets the landing when there is nothing landing', () => {
    const fill = drive();
    fill.land(true);
    tick(searchingFloorMs({ kind: 'fill', seats: SEATS, collapsed: false }));

    fill.land(false);

    expect(fill.revealed()).toBe(0);
  });
});
