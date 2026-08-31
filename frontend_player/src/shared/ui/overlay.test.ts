/**
 * The two OS questions every surface asks, and the live region that answers back.
 *
 * `the-words.md` §20.11 puts a **second condition on one path**: reduced motion and a screen
 * reader both collapse an animation to its end state, and a player may have VoiceOver on and
 * reduced motion off — which is the common case, and the one a single `useReducedMotion()`
 * silently gets wrong.
 */

import { act, renderHook } from '@testing-library/react-native';
import { AccessibilityInfo } from 'react-native';

import {
  announce,
  useCollapsedPresentation,
  useLiveRegion,
  useReducedMotion,
  useScreenReader,
} from './overlay';

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

    const { result } = renderHook(() => useReducedMotion());
    await act(async () => undefined);

    expect(result.current).toBe(false);
  });
});

describe('the collapse', () => {
  it('is one condition satisfied by either — VoiceOver on, reduced motion off', async () => {
    fakeAccessibility({ screenReader: true, reduceMotion: false });

    const { result } = renderHook(() => useCollapsedPresentation());
    await act(async () => undefined);

    expect(result.current).toBe(true);
  });

  it('holds when the OS asks for reduced motion and nothing is listening', async () => {
    fakeAccessibility({ screenReader: false, reduceMotion: true });

    const { result } = renderHook(() => useCollapsedPresentation());
    await act(async () => undefined);

    expect(result.current).toBe(true);
  });

  it('is off when neither is', async () => {
    fakeAccessibility();

    const { result } = renderHook(() => useCollapsedPresentation());
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
