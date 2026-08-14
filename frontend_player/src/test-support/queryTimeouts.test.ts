/**
 * The two facts that make `queryTimeouts.ts` necessary, pinned (#29).
 *
 * Neither is observable from an ordinary test run: the symptom is a jest *worker* that will
 * not exit, and a single-suite run has no worker to fail. So the handle and the upstream
 * behaviour are asserted directly instead.
 *
 * Both assertions go through the provider `jest.setup.js` installed — nothing here swaps it,
 * because switching providers mid-run is itself something Query warns about, and a warning
 * printed on every run is the thing this issue was about.
 */

import { MutationObserver, timeoutManager } from '@tanstack/query-core';

import { queryClient } from '@/shared/lib/query-client';

/** Node's timer handle. React Native returns a number, and jest's fake timers a third thing. */
type NodeTimer = { hasRef: () => boolean };

/** Distinctive, so the scheduled gc timer is told apart from every other timer by its delay. */
const GC_TIME = 987_654;

describe("Query's garbage-collection timers", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('do not hold the process open, which is what the force-exit warning was about', () => {
    const handle = timeoutManager.setTimeout(() => {}, GC_TIME);
    try {
      expect((handle as unknown as NodeTimer).hasRef()).toBe(false);
    } finally {
      timeoutManager.clearTimeout(handle);
    }
  });

  it('survive queryClient.clear() when a mutation loses its last observer', async () => {
    const scheduled = jest.spyOn(global, 'setTimeout');
    const cancelled = jest.spyOn(global, 'clearTimeout');

    const observer = new MutationObserver(queryClient, {
      mutationFn: async () => 'done',
      gcTime: GC_TIME,
    });
    const unsubscribe = observer.subscribe(() => {});
    await observer.mutate();

    unsubscribe(); // what unmounting a screen does
    queryClient.clear(); // what every suite's afterEach does

    const gcTimers = scheduled.mock.results
      .filter((_result, index) => scheduled.mock.calls[index]?.[1] === GC_TIME)
      .map((result) => result.value as ReturnType<typeof setTimeout>);
    const cleared = new Set(cancelled.mock.calls.map(([handle]) => handle));
    const surviving = gcTimers.filter((handle) => !cleared.has(handle));

    // The point of the file: teardown ran, and the gc timer is still scheduled. At the
    // app's real `gcTime` that is five minutes of a jest worker refusing to exit.
    //
    // If this ever goes red because Query started cancelling them, the provider has done
    // its job and can be reconsidered — that is not a regression.
    expect(gcTimers.length).toBeGreaterThan(0);
    expect(surviving.length).toBeGreaterThan(0);

    surviving.forEach((handle) => clearTimeout(handle));
  });
});
