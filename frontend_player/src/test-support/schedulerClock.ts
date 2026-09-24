/**
 * React's scheduler, on the clock the suite is on — for the test process only
 * ([#493](https://github.com/Raketa02/Raketa/issues/493)).
 *
 * ## What this fixes
 *
 * A commit's passive effects — every `useEffect`, and React Native's `usePressability`, which is
 * where a `Pressable` learns it is no longer disabled — run as a task on `scheduler`, a macrotask
 * after the commit, whenever the commit was made outside `act`. That is every commit a `waitFor`
 * polls into: it turns the act environment off and moves the fake clock, and whatever the clock
 * sets off commits on the spot.
 *
 * `scheduler` yields to the host once a turn has run 5 ms of its clock, and it reads that clock
 * off the `performance` it captured when it loaded — before `renderRouter` installs fake timers.
 * So under the router harness, where every other clock is fake, React's alone was real. A fast
 * machine ran every pending effect in one turn; a starved CI runner ran one, and the test's next
 * step landed between two of them:
 *
 * - **A press was dropped without a word.** Find a game's search control is enabled by the commit
 *   that draws the week. Pressed the moment the week is on screen, before that commit's effects,
 *   it read enabled (`accessibilityState.disabled: false`) while its responder still answered no
 *   — and `fireEvent.press` treats no as disabled. No search, no latch.
 * - **A room was told something before it listened.** A room follows its channel in an effect,
 *   and a status the channel sent before that effect ran reached nobody.
 *
 * ## Why this, and not a slower test
 *
 * The clock is pointed at whichever clock the suite is on. A fake one does not move while a turn
 * runs, so a turn holds every task React has queued, however slow the machine; on real timers
 * nothing changes. That makes the order of effects and test steps a fact about the code rather
 * than about the runner, which a longer wait never would.
 *
 * ## Why the renderer's own copy
 *
 * `react-test-renderer` carries `scheduler` 0.23 and React Native a 0.24 canary, and the bare
 * name resolves to React Native's. The renderer's is resolved from the renderer, and it reads its
 * clock through `exports.unstable_now` everywhere, so replacing that export is the whole change.
 * `schedulerClock.test.tsx` holds it to its effect.
 *
 * Not app code — nothing under `src/` imports this.
 */

import { dirname } from 'path';

/** The export the renderer's `scheduler` reads every moment of its clock through. */
interface SchedulerClock {
  unstable_now: () => number;
}

/** Point the renderer's `scheduler` at the suite's clock. Called once, from `jest.setup.js`. */
export function runSchedulerOnTheSuiteClock(): void {
  const schedulerPath = require.resolve('scheduler', {
    paths: [dirname(require.resolve('react-test-renderer/package.json'))],
  });

  jest.doMock(schedulerPath, () => {
    const scheduler = jest.requireActual<SchedulerClock>(schedulerPath);
    scheduler.unstable_now = () => globalThis.performance.now();
    return scheduler;
  });
}
