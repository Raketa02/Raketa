import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import { Text } from 'react-native';
import * as SplashScreen from 'expo-splash-screen';

import { BootstrapGate } from './BootstrapGate';

jest.mock('expo-splash-screen', () => ({
  preventAutoHideAsync: jest.fn(async () => {}),
  hideAsync: jest.fn(async () => {}),
}));

const hideAsync = jest.mocked(SplashScreen.hideAsync);

function deferred() {
  let resolve!: () => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<void>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

/** The splash only leaves once the tree behind it has laid out. */
function layOutTheApp() {
  fireEvent(screen.getByTestId('app-root'), 'layout', {
    nativeEvent: { layout: { x: 0, y: 0, width: 390, height: 844 } },
  });
}

/**
 * This suite renders without the `expo-router/testing-library` harness, so it runs on
 * **real timers** where the router-harness suites run on jest's fake ones. That is what
 * makes it the only suite here sensitive to wall-clock contention: its `waitFor` calls
 * wait for actual elapsed time, not for a clock the test advances itself.
 *
 * The work is small — the first test takes ~400 ms — but it needed only a >12× slowdown
 * to blow the 5 s default, and it reached that under two test suites running at once on
 * one container. CI runners with noisy neighbours are not exotic, and a timeout failure
 * reads as a broken gate rather than a busy machine.
 *
 * So the margin is stated rather than left implicit. This is headroom for a loaded
 * machine, never permission for the sequence to be slow: if a test here genuinely
 * approaches this number, something has started doing real work and the fix is not a
 * larger timeout.
 */
jest.setTimeout(30_000);

beforeEach(() => {
  jest.clearAllMocks();
});

describe('BootstrapGate', () => {
  it('shows nothing and keeps the splash up while the sequence runs', async () => {
    const startup = deferred();

    render(
      <BootstrapGate run={() => startup.promise}>
        <Text>the app</Text>
      </BootstrapGate>,
    );

    expect(screen.queryByText('the app')).toBeNull();
    expect(hideAsync).not.toHaveBeenCalled();

    startup.resolve();
    await waitFor(() => expect(screen.getByText('the app')).toBeTruthy());
  });

  it('hides the splash only after the app has laid out', async () => {
    render(
      <BootstrapGate run={async () => {}}>
        <Text>the app</Text>
      </BootstrapGate>,
    );

    await waitFor(() => expect(screen.getByText('the app')).toBeTruthy());
    expect(hideAsync).not.toHaveBeenCalled();

    layOutTheApp();
    expect(hideAsync).toHaveBeenCalledTimes(1);

    layOutTheApp();
    expect(hideAsync).toHaveBeenCalledTimes(1);
  });

  it('shows why the launch failed instead of hanging on the splash', async () => {
    render(
      <BootstrapGate
        run={() =>
          Promise.reject(new Error('Invalid app configuration — EXPO_PUBLIC_API_URL: Required'))
        }
      >
        <Text>the app</Text>
      </BootstrapGate>,
    );

    await waitFor(() => expect(screen.getByText(/EXPO_PUBLIC_API_URL/)).toBeTruthy());
    expect(screen.queryByText('the app')).toBeNull();

    layOutTheApp();
    expect(hideAsync).toHaveBeenCalledTimes(1);
  });
});
