/**
 * The network-state wiring, over a faked `expo-network`.
 *
 * The native module is the only thing stubbed. What is under test is the part this app owns: what a
 * platform answer means — the online manager's rule — and **the launch's one read of it**, which is
 * the manager's own belief once it has its first answer, so that by the time the launch acts on it
 * the manager already agrees (ADR-0209 §4).
 */

import { onlineManager } from '@tanstack/react-query';

import { REACHABILITY_ANSWER_WITHIN_MS, readReachability, wireOnlineManager } from './networkState';

const native = jest.requireMock('expo-network') as {
  addNetworkStateListener: jest.Mock;
  getNetworkStateAsync: jest.Mock;
};

const REACHES = { isConnected: true, isInternetReachable: true };
const PORTAL = { isConnected: true, isInternetReachable: false };

let unwire: (() => void) | undefined;

// The default is restated rather than inherited from jest.setup.js: `clearAllMocks` keeps an
// implementation one case set, and the next case would read it.
beforeEach(() => {
  jest.clearAllMocks();
  native.getNetworkStateAsync.mockResolvedValue(REACHES);
});

afterEach(() => {
  unwire?.();
  unwire = undefined;
  onlineManager.setOnline(true);
  jest.useRealTimers();
});

function wire() {
  unwire = wireOnlineManager();
}

/** What the platform reports next, through the listener the wiring subscribed. */
function platformReports(state: object) {
  const [[onChange]] = native.addNetworkStateListener.mock.calls as [[(state: object) => void]];
  onChange(state);
}

describe("the launch's read of the phone's reachability", () => {
  it.each([
    ['no connection at all', { isConnected: false, isInternetReachable: false }],
    ['a connection that reaches nothing', PORTAL],
    [
      'no connection, reachability still undecided',
      { isConnected: false, isInternetReachable: null },
    ],
  ])('is unreachable on %s — and the manager already says offline', async (_, state) => {
    native.getNetworkStateAsync.mockResolvedValue(state);
    wire();

    await expect(readReachability()).resolves.toBe('unreachable');
    expect(onlineManager.isOnline()).toBe(false);
  });

  it('is undecided while the platform is still deciding — and the manager counts it online', async () => {
    native.getNetworkStateAsync.mockResolvedValue({ isConnected: true, isInternetReachable: null });
    onlineManager.setOnline(false);
    wire();

    await expect(readReachability()).resolves.toBe('undecided');
    expect(onlineManager.isOnline()).toBe(true);
  });

  it('is reachable on a connection the phone believes in', async () => {
    wire();

    await expect(readReachability()).resolves.toBe('reachable');
    expect(onlineManager.isOnline()).toBe(true);
  });

  it('fails when the phone cannot be asked — and the manager assumes online', async () => {
    native.getNetworkStateAsync.mockRejectedValue(new Error('no native answer'));
    onlineManager.setOnline(false);
    wire();

    await expect(readReachability()).rejects.toThrow('no native answer');
    expect(onlineManager.isOnline()).toBe(true);
  });

  it("waits on the manager's own first answer, so the phone is asked once", async () => {
    // Two reads could disagree — the manager's arriving after the launch's, saying the opposite —
    // and the entry gate's read would then not be paused by the time it is made.
    wire();

    await readReachability();
    await readReachability();

    expect(native.getNetworkStateAsync).toHaveBeenCalledTimes(1);
  });

  it('answers what the manager believes now, when the connection came back after the first answer', async () => {
    // A cold start while the wifi is still joining: *no internet*, then the platform changes its
    // mind while the keychain is read. Skipping on the first answer would leave nothing in the
    // cache for a gate whose read is no longer paused — it would ask on the ordinary budget, with
    // the splash held all the while. The launch's own check is the right one to send.
    native.getNetworkStateAsync.mockResolvedValue(PORTAL);
    wire();
    await expect(readReachability()).resolves.toBe('unreachable');

    platformReports(REACHES);

    await expect(readReachability()).resolves.toBe('reachable');
    expect(onlineManager.isOnline()).toBe(true);
  });

  it('never lets the first answer overwrite a change the platform reported while it was asked', async () => {
    let answer: (state: object) => void = () => {};
    native.getNetworkStateAsync.mockReturnValue(
      new Promise((resolve) => {
        answer = resolve;
      }),
    );
    wire();

    platformReports(REACHES);
    answer(PORTAL);

    await expect(readReachability()).resolves.toBe('reachable');
    expect(onlineManager.isOnline()).toBe(true);
  });

  it('fails at its budget when the phone never answers, rather than holding the launch', async () => {
    jest.useFakeTimers();
    native.getNetworkStateAsync.mockReturnValue(new Promise(() => {}));
    wire();

    let failure: unknown;
    const reading = readReachability().catch((error: unknown) => {
      failure = error;
    });

    await jest.advanceTimersByTimeAsync(REACHABILITY_ANSWER_WITHIN_MS - 1);
    expect(failure).toBeUndefined();
    await jest.advanceTimersByTimeAsync(1);
    await reading;

    expect(failure).toBeInstanceOf(Error);
  });

  it('fails when nothing wired the manager, which then believes nothing', async () => {
    await expect(readReachability()).rejects.toThrow('not wired');
    expect(native.getNetworkStateAsync).not.toHaveBeenCalled();
  });
});

describe('the online manager, wired', () => {
  it('follows every change the platform reports, by the same rule', () => {
    wire();

    platformReports(PORTAL);
    expect(onlineManager.isOnline()).toBe(false);

    platformReports({ isConnected: true, isInternetReachable: null });
    expect(onlineManager.isOnline()).toBe(true);
  });
});
