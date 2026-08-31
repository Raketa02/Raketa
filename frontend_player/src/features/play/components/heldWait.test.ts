/**
 * The minimum-display floor — the mechanism that makes an answer legible.
 *
 * Every case here is a **boundary in time**, and none of them is observable from a screen: a
 * wait that ended one frame after the response and a wait that held its answer look identical
 * in a snapshot and are the difference between a number nobody reads and a number. So the
 * clock is driven rather than waited on, exactly as `Toast.test.tsx` drives its hold.
 *
 * The case that matters most is the **slow** answer, because that is the one the first draft
 * got wrong: a floor measured from the press has nothing left of itself by the time a real
 * search comes back, and the count it exists to show is drawn for zero milliseconds.
 */

import { act, renderHook } from '@testing-library/react-native';

import { useHeldWait } from './heldWait';

const FLOOR = 1000;

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

const tick = (ms: number) => act(() => jest.advanceTimersByTime(ms));

function drive(floorMs = FLOOR) {
  const { result, rerender } = renderHook(
    ({ running }: { running: boolean }) => useHeldWait(running, floorMs),
    { initialProps: { running: false } },
  );

  return {
    held: () => result.current,
    set: (running: boolean) => act(() => rerender({ running })),
  };
}

describe('the wait', () => {
  it('is down until something is running', () => {
    const wait = drive();

    expect(wait.held()).toBe(false);
    tick(FLOOR * 2);
    expect(wait.held()).toBe(false);
  });

  it('goes up on the act, not on a timer', () => {
    const wait = drive();

    wait.set(true);

    // No clock has moved. The floor is what comes *after* the act; the act itself raises the
    // wait, or a player would watch their own screen for a frame before it responded.
    expect(wait.held()).toBe(true);
  });

  it('outlasts a request that never ends', () => {
    const wait = drive();

    wait.set(true);
    tick(FLOOR * 10);

    expect(wait.held()).toBe(true);
  });
});

describe('the floor over the answer', () => {
  it('holds a fast answer for the whole floor', () => {
    const wait = drive();

    wait.set(true);
    tick(50);
    wait.set(false);

    tick(FLOOR - 1);
    expect(wait.held()).toBe(true);

    tick(1);
    expect(wait.held()).toBe(false);
  });

  /**
   * The one the first draft failed. A floor anchored to the press is spent long before a real
   * search answers, so the answer — and the count on it — would be drawn for nothing.
   */
  it('holds a slow answer for exactly as long as a fast one', () => {
    const wait = drive();

    wait.set(true);
    tick(FLOOR * 3);
    wait.set(false);

    expect(wait.held()).toBe(true);
    tick(FLOOR - 1);
    expect(wait.held()).toBe(true);

    tick(1);
    expect(wait.held()).toBe(false);
  });

  /**
   * There is no commit in which the request has finished and the hold has not yet begun — a
   * latch that blinked out and back in at the moment the answer landed would be the flash the
   * floor exists to prevent, arriving from inside it.
   */
  it('never drops between the answer and its own floor', () => {
    const wait = drive();

    wait.set(true);
    wait.set(false);

    expect(wait.held()).toBe(true);
  });

  it('gives a second act its own floor rather than the first one’s remainder', () => {
    const wait = drive();

    wait.set(true);
    wait.set(false);
    tick(FLOOR - 100);

    // The second search starts inside the first answer's floor and takes it over.
    wait.set(true);
    expect(wait.held()).toBe(true);
    tick(FLOOR * 2);
    expect(wait.held()).toBe(true);

    wait.set(false);
    tick(FLOOR - 1);
    expect(wait.held()).toBe(true);

    tick(1);
    expect(wait.held()).toBe(false);
  });

  /** A floor of nothing is a wait bound to its act alone. */
  it('takes a floor of zero without holding a frame it was not asked for', () => {
    const wait = drive(0);

    wait.set(true);
    wait.set(false);
    tick(0);

    expect(wait.held()).toBe(false);
  });
});
