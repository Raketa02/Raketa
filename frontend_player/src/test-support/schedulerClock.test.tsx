/**
 * What `schedulerClock.ts` buys, pinned (#493): a turn of the host runs every effect React has
 * queued, however long each one takes.
 *
 * **The slow machine here is real.** Every effect in the chain spends `SPENT_MS` of CPU before it
 * does anything, which is what a starved runner does to a render — no clock is doctored, so the
 * case is red with the module's install taken out of `jest.setup.js` and green with it in.
 */

import { useEffect, useState } from 'react';
import { Text } from 'react-native';
import { render } from '@testing-library/react-native';

/** Four of `scheduler`'s 5 ms frames — far past one on any machine. */
const SPENT_MS = 20;

/** The host's own next turn, taken before fake timers can replace it. */
const hostTurn = setImmediate;
const nextHostTurn = () => new Promise<void>((resolve) => hostTurn(() => resolve()));

/** Real time passing, the way a slow render passes it. Fake timers leave the real clock alone. */
function spend(ms: number) {
  const until = jest.getRealSystemTime() + ms;
  while (jest.getRealSystemTime() < until);
}

/**
 * Two commits, the second made by the first one's effect — and the second one's effect is the one
 * watched. The first is made by a timer, so it lands outside `act`, where a polling `waitFor` puts
 * every commit.
 */
function Chain({ onSettled }: { readonly onSettled: () => void }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const armed = setTimeout(() => setStep(1), 10);
    return () => clearTimeout(armed);
  }, []);

  useEffect(() => {
    if (step === 0) return;
    spend(SPENT_MS);
    if (step === 1) setStep(2);
    else onSettled();
  }, [step, onSettled]);

  return <Text>{`step ${step}`}</Text>;
}

/** React's switch for whether an update outside `act` is a mistake. `waitFor` turns it off. */
const reactGlobals = globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean };

describe('the clock React schedules effects on', () => {
  let actEnvironment: boolean | undefined;

  beforeEach(() => {
    jest.useFakeTimers();
    actEnvironment = reactGlobals.IS_REACT_ACT_ENVIRONMENT;
  });

  afterEach(() => {
    reactGlobals.IS_REACT_ACT_ENVIRONMENT = actEnvironment;
    jest.useRealTimers();
  });

  it('runs every effect a commit leaves behind in the next turn, however long each one takes', async () => {
    const settled = jest.fn();
    render(<Chain onSettled={settled} />);

    // What `waitFor` does while it polls: it turns the act environment off and moves the clock.
    reactGlobals.IS_REACT_ACT_ENVIRONMENT = false;
    jest.advanceTimersByTime(10);

    // One turn of the host after the commit — the turn `scheduler` asked for, and then this one.
    // On the real clock the first effect's 20 ms ends the scheduler's turn before the second
    // effect runs, and it runs a turn later: after anything a test does next.
    await nextHostTurn();

    expect(settled).toHaveBeenCalledTimes(1);
  });
});
