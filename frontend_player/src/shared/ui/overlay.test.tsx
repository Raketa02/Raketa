/**
 * The two OS questions every surface asks, and the live region that answers back.
 *
 * `the-words.md` §20.11 puts a **second condition on one path**: reduced motion and a screen
 * reader both collapse an animation to its end state, and a player may have VoiceOver on and
 * reduced motion off — which is the common case, and the one a single `useReducedMotion()`
 * silently gets wrong.
 */

import { act, renderHook } from '@testing-library/react-native';
import type { ReactNode } from 'react';
import { AccessibilityInfo } from 'react-native';
import { useReducedMotion as reducedMotionAtStart } from 'react-native-reanimated';

import {
  ReducedMotionProvider,
  announce,
  useCollapsedPresentation,
  useLiveRegion,
  useReducedMotion,
  useScreenReader,
} from './overlay';

/**
 * **The OS's answer as the process started** — Reanimated's, which the native side hands the
 * JavaScript runtime as it installs, so it is there before the first render. Under jest there is no
 * native side and it answers `false`; this replaces only that one read, real everything else, so a
 * test can be a phone that started with reduced motion on. The far side of a native module, as
 * `jest.setup.js` mocks the others.
 */
jest.mock('react-native-reanimated', () => ({
  ...jest.requireActual('react-native-reanimated'),
  useReducedMotion: jest.fn(() => false),
}));

const atStart = jest.mocked(reducedMotionAtStart);

/**
 * Reduced motion is read once, at the root, and handed down — so a hook that reads it is
 * rendered under the provider that owns the subscription, exactly as the app renders it.
 */
function underTheProvider({ children }: { readonly children: ReactNode }) {
  return <ReducedMotionProvider>{children}</ReducedMotionProvider>;
}

type Listener = (enabled: boolean) => void;

/** The OS, as a pair of switches a test can flip. */
function fakeAccessibility(initial: { reduceMotion?: boolean; screenReader?: boolean } = {}) {
  const listeners: Record<string, Listener[]> = {};

  jest
    .spyOn(AccessibilityInfo, 'isReduceMotionEnabled')
    .mockResolvedValue(initial.reduceMotion ?? false);
  jest
    .spyOn(AccessibilityInfo, 'isScreenReaderEnabled')
    .mockResolvedValue(initial.screenReader ?? false);
  jest.spyOn(AccessibilityInfo, 'addEventListener').mockImplementation(((
    event: string,
    handler: Listener,
  ) => {
    (listeners[event] ??= []).push(handler);
    return { remove: () => undefined };
  }) as unknown as typeof AccessibilityInfo.addEventListener);

  return {
    change: (event: string, enabled: boolean) => {
      act(() => listeners[event]?.forEach((handler) => handler(enabled)));
    },
  };
}

/**
 * The spy is made once and cleared between tests, never re-made. `jest.spyOn` on a property
 * that is already a spy hands back the **same** mock, so a per-test `spyOn` inherits the
 * previous test's calls — which is a leak that reads as a bug in the code under test.
 */
let spoken: jest.SpyInstance<
  void,
  Parameters<typeof AccessibilityInfo.announceForAccessibilityWithOptions>
>;

beforeEach(() => {
  jest.restoreAllMocks();
  atStart.mockReturnValue(false);
  spoken = jest
    .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
    .mockImplementation(() => undefined);
  spoken.mockClear();
});

describe('the two questions', () => {
  it('reads the screen reader the same way it reads reduced motion', async () => {
    fakeAccessibility({ screenReader: true });

    const { result } = renderHook(() => useScreenReader());
    await act(async () => undefined);

    expect(result.current).toBe(true);
  });

  it('follows the OS while the screen is open', async () => {
    const os = fakeAccessibility();
    const { result } = renderHook(() => useScreenReader());
    await act(async () => undefined);

    expect(result.current).toBe(false);
    os.change('screenReaderChanged', true);
    expect(result.current).toBe(true);
  });

  it('leaves reduced motion answering only for itself', async () => {
    fakeAccessibility({ screenReader: true });

    const { result } = renderHook(() => useReducedMotion(), { wrapper: underTheProvider });
    await act(async () => undefined);

    expect(result.current).toBe(false);
  });
});

describe('reduced motion, read once for the whole tree', () => {
  it('subscribes to the OS once however many surfaces are asking', () => {
    // The reason it stopped being a hook: a listener per consumer, on surfaces mounted for as
    // long as the tab is. One provider, one subscription.
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
    // Cleared rather than freshly made, for the reason recorded above `spoken`: `spyOn` on a
    // property that is already a spy hands back the same mock, calls and all.
    const listened = jest.spyOn(AccessibilityInfo, 'addEventListener');
    listened.mockClear();

    renderHook(
      () => {
        useReducedMotion();
        useReducedMotion();
        useReducedMotion();
      },
      { wrapper: underTheProvider },
    );

    expect(listened).toHaveBeenCalledTimes(1);
    expect(listened).toHaveBeenCalledWith('reduceMotionChanged', expect.any(Function));
  });

  it('takes the value a test hands it over the device it is running on', async () => {
    // Part 13's shape for a port's context: the device, unless a test says otherwise.
    fakeAccessibility({ reduceMotion: false });

    const { result } = renderHook(() => useReducedMotion(), {
      wrapper: ({ children }) => <ReducedMotionProvider value>{children}</ReducedMotionProvider>,
    });
    await act(async () => undefined);

    expect(result.current).toBe(true);
  });

  /**
   * **Never a provisional `false`** (ADR-0209 §2). The asynchronous read lands after the first
   * frame, and the launch's splash decides its variant once, before it — so the provider's first
   * answer has to be the OS's already, from the one source that knows before anything renders.
   */
  it('answers what the OS said as the process started on its very first render', () => {
    atStart.mockReturnValue(true);
    // The asynchronous read never lands in this test: the answer cannot have come from it.
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockReturnValue(new Promise(() => {}));

    const answers: boolean[] = [];
    renderHook(() => answers.push(useReducedMotion()), { wrapper: underTheProvider });

    expect(answers[0]).toBe(true);
  });

  it('follows the OS from there, when the player changes it while the app is open', async () => {
    atStart.mockReturnValue(true);
    const os = fakeAccessibility({ reduceMotion: true });

    const { result } = renderHook(() => useReducedMotion(), { wrapper: underTheProvider });
    await act(async () => undefined);
    expect(result.current).toBe(true);

    os.change('reduceMotionChanged', false);
    expect(result.current).toBe(false);
  });

  it('is off outside a provider, which is what the app looked like before anybody asked', async () => {
    fakeAccessibility({ reduceMotion: true });

    const { result } = renderHook(() => useReducedMotion());
    await act(async () => undefined);

    expect(result.current).toBe(false);
  });
});

describe('the collapse', () => {
  it('is one condition satisfied by either — VoiceOver on, reduced motion off', async () => {
    fakeAccessibility({ screenReader: true, reduceMotion: false });

    const { result } = renderHook(() => useCollapsedPresentation(), {
      wrapper: underTheProvider,
    });
    await act(async () => undefined);

    expect(result.current).toBe(true);
  });

  it('holds when the OS asks for reduced motion and nothing is listening', async () => {
    fakeAccessibility({ screenReader: false, reduceMotion: true });

    const { result } = renderHook(() => useCollapsedPresentation(), {
      wrapper: underTheProvider,
    });
    await act(async () => undefined);

    expect(result.current).toBe(true);
  });

  it('is off when neither is', async () => {
    fakeAccessibility();

    const { result } = renderHook(() => useCollapsedPresentation(), {
      wrapper: underTheProvider,
    });
    await act(async () => undefined);

    expect(result.current).toBe(false);
  });
});

describe('a live region', () => {
  it('speaks a figure when it arrives, politely', () => {
    renderHook(() => useLiveRegion('Fairly even, 74%'));

    expect(spoken).toHaveBeenCalledWith('Fairly even, 74%', { queue: true });
  });

  it('speaks again only when the figure changes', () => {
    const { rerender } = renderHook(({ message }) => useLiveRegion(message), {
      initialProps: { message: 'Fairly even, 74%' },
    });
    rerender({ message: 'Fairly even, 74%' });
    rerender({ message: 'Very even, 91%' });

    expect(spoken.mock.calls.map(([message]) => message)).toEqual([
      'Fairly even, 74%',
      'Very even, 91%',
    ]);
  });

  it('says nothing when the region has nothing in it', () => {
    renderHook(() => useLiveRegion(null));

    expect(spoken).not.toHaveBeenCalled();
  });
});

describe('an announcement', () => {
  it('queues by default, and takes the floor only when asked', () => {
    announce('Challenge sent', 'interrupting');
    announce('Ranking everybody you could play…');

    expect(spoken).toHaveBeenNthCalledWith(1, 'Challenge sent', { queue: false });
    expect(spoken).toHaveBeenNthCalledWith(2, 'Ranking everybody you could play…', { queue: true });
  });
});
