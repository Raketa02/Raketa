/**
 * The queue, the live region and the dismiss — 9.2's three unbuilt parts.
 *
 * Two of the three are unobservable from a screen and both were shipped bugs elsewhere: an
 * announcement has no rendered node, and a toast that is still on screen after its hold is
 * indistinguishable from one that is not until you wait 2,6 seconds.
 *
 * `announceForAccessibility` **interrupts** on both platforms, and nineteen toasts fire from
 * the Play tab alone: one landing mid-card cuts a listener off in the middle of the reason
 * lines they were listening to. That is what the queued variant is for, and it is why the one
 * message that still interrupts has to be a decision rather than a call site.
 */

import { act, fireEvent, render as renderTree, screen } from '@testing-library/react-native';
import { AccessibilityInfo, StyleSheet, View, type ViewStyle } from 'react-native';
import { SafeAreaProvider, type Metrics } from 'react-native-safe-area-context';

import { showToast, useToastQueue } from '@/shared/store/toast.store';

import { SplashCoverProvider } from './overlay';
import { TAB_BAR_HEIGHT } from './TabBar';
import { theme } from './theme';
import { ToastHost } from './Toast';

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

/** A notched phone — the inset the toast has to clear along with the bar above it. */
const METRICS: Metrics = {
  frame: { x: 0, y: 0, width: 320, height: 693 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

/** The host is mounted once at the root, so every case here renders exactly one of it. */
function render(): void {
  renderTree(
    <SafeAreaProvider initialMetrics={METRICS}>
      <ToastHost />
    </SafeAreaProvider>,
  );
}

let announced: jest.SpyInstance;

beforeEach(() => {
  jest.useFakeTimers();
  useToastQueue.getState().clear();
  announced = jest
    .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
    .mockImplementation(() => undefined);
});

afterEach(() => {
  announced.mockRestore();
  jest.useRealTimers();
});

const hold = () => act(() => jest.advanceTimersByTime(theme.motion.hold.toast));

/** The host itself — the one View carrying the toast layer. */
const hostNode = () =>
  screen
    .UNSAFE_queryAllByType(View)
    .find((node) => flatten(node.props.style)?.zIndex !== undefined);

const hostStyle = () => flatten(hostNode()?.props.style);

/**
 * What is on screen. Every query here asks for hidden elements, because the toast is hidden
 * from assistive technology on purpose — the host has already spoken it.
 */
const drawn = (message: string) => screen.queryByText(message, { includeHiddenElements: true });

describe('the queue', () => {
  it('shows one message at a time, and the next one takes its place', () => {
    render();

    act(() => {
      showToast({ message: 'Asked Marek along' });
      showToast({ message: 'Saved to your profile', tone: 'ok' });
    });

    expect(drawn('Asked Marek along')).toBeTruthy();
    // A queue and not a stack: a screen showing three sentences while a listener is being
    // read one is the two channels disagreeing about what just happened.
    expect(drawn('Saved to your profile')).toBeNull();

    hold();
    expect(drawn('Saved to your profile')).toBeTruthy();
  });

  it('empties, and the host draws nothing at all when it is empty', () => {
    render();
    act(() => showToast({ message: 'Unmarked' }));

    hold();

    expect(drawn('Unmarked')).toBeNull();
    expect(useToastQueue.getState().queue).toHaveLength(0);
  });

  it('holds each message for its own time rather than what is left of the one before', () => {
    render();
    act(() => {
      showToast({ message: 'First' });
      showToast({ message: 'Second' });
    });

    hold();
    act(() => jest.advanceTimersByTime(theme.motion.hold.toast - 1));

    expect(drawn('Second')).toBeTruthy();
  });
});

/**
 * **A message raised under the launch's drawn splash** (ADR-0209 §2): the host is in the tree the
 * splash covers for the first seconds of a cold open, so a hold started there would run out unseen
 * — a two-second toast raised at 0.4 s gone before the fade at 2.6 s. It waits, unsaid, until the
 * splash is gone, and then has its whole time.
 */
describe('under the launch’s splash', () => {
  function renderCovered(covered: boolean) {
    return (
      <SafeAreaProvider initialMetrics={METRICS}>
        <SplashCoverProvider covered={covered}>
          <ToastHost />
        </SplashCoverProvider>
      </SafeAreaProvider>
    );
  }

  it('says nothing and starts no hold until the splash has gone, then has its whole time', () => {
    const view = renderTree(renderCovered(true));
    act(() => showToast({ message: 'That link has already been used' }));

    hold();
    hold();
    expect(drawn('That link has already been used')).toBeTruthy();
    expect(announced).not.toHaveBeenCalled();

    view.rerender(renderCovered(false));
    expect(announced).toHaveBeenCalledTimes(1);

    act(() => jest.advanceTimersByTime(theme.motion.hold.toast - 1));
    expect(drawn('That link has already been used')).toBeTruthy();

    act(() => jest.advanceTimersByTime(1));
    expect(drawn('That link has already been used')).toBeNull();
  });
});

describe('the announcement', () => {
  it('is queued, which is what keeps a toast from cutting a listener off mid-card', () => {
    render();
    act(() => showToast({ message: 'Not today, Marek' }));

    expect(announced).toHaveBeenCalledWith('Not today, Marek', { queue: true });
  });

  it('interrupts for the one message that is the whole of an irreversible act succeeding', () => {
    render();
    act(() => showToast({ message: 'Challenge sent', tone: 'ok', politeness: 'interrupting' }));

    expect(announced).toHaveBeenCalledWith('Challenge sent', { queue: false });
  });

  /**
   * §20.10's exception is that it *"does not queue behind anything"*, and a politeness flag
   * alone would not have given it that: behind two held messages the send confirmation waits
   * 5,2 seconds to be spoken at all — on a destination that is a placeholder with nothing else
   * on it to say the challenge went.
   */
  it('puts the interrupting message in front of everything not yet shown', () => {
    render();
    act(() => {
      showToast({ message: 'First' });
      showToast({ message: 'Second' });
      showToast({ message: 'Challenge sent', tone: 'ok', politeness: 'interrupting' });
    });

    // The one already on screen keeps its place — pulling a sentence out from under a reader
    // is the interruption the whole amendment exists to stop.
    expect(drawn('First')).toBeTruthy();

    hold();
    expect(drawn('Challenge sent')).toBeTruthy();
    expect(announced).toHaveBeenLastCalledWith('Challenge sent', { queue: false });

    hold();
    expect(drawn('Second')).toBeTruthy();
  });

  it('fires as a message becomes the head, never as it is queued behind three others', () => {
    render();
    act(() => {
      showToast({ message: 'First' });
      showToast({ message: 'Second' });
    });

    expect(announced).toHaveBeenCalledTimes(1);

    hold();
    expect(announced).toHaveBeenCalledTimes(2);
  });

  it('leaves the drawn toast out of the accessibility tree, so it is not read twice', () => {
    render();
    act(() => showToast({ message: 'Saved' }));

    expect(screen.queryByText('Saved')).toBeNull();
    expect(drawn('Saved')).toBeTruthy();
  });
});

describe('the host', () => {
  it('never blocks a tap, which is also why the dismiss is a hold and not a control', () => {
    render();
    act(() => showToast({ message: 'Saved' }));

    expect(hostNode()?.props.pointerEvents).toBe('none');
    expect(hostStyle()?.zIndex).toBe(theme.layer.toast);
  });

  it('sits above the tab bar and the bottom inset, rather than over the app’s own chrome', () => {
    render();
    act(() => showToast({ message: 'Saved' }));

    // The bar's height is derived where the bar is drawn; a copy of it here would be the
    // two numbers `TAB_BAR_HEIGHT` exists to keep as one.
    expect(hostStyle()?.bottom).toBe(TAB_BAR_HEIGHT + METRICS.insets.bottom + theme.space.sm);
  });

  /** Rule C: white on `mint` is 4,07:1, so the settled toast is `mintInk`. */
  it.each([
    ['base', theme.color.night],
    ['ok', theme.color.mintInk],
    ['bad', theme.color.red],
  ] as const)('paints a %s toast in a value white reads on', (tone, expected) => {
    render();
    act(() => showToast({ message: 'Saved', tone }));

    const fills = screen.UNSAFE_queryAllByType(View).map((node) => flatten(node.props.style));
    expect(fills).toEqual(
      expect.arrayContaining([expect.objectContaining({ backgroundColor: expected })]),
    );
  });
});

describe('a failure the player must read', () => {
  it('stays for the notice hold, not the toast’s, and the player can close it before then', () => {
    render();

    act(() => {
      showToast({ message: 'Payments can’t be reached right now.', tone: 'bad' });
    });
    act(() => jest.advanceTimersByTime(theme.motion.hold.toast));

    expect(drawn('Payments can’t be reached right now.')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Dismiss this message' }));

    expect(drawn('Payments can’t be reached right now.')).toBeNull();
  });

  it('leaves on its own once the notice hold has passed', () => {
    render();

    act(() => {
      showToast({ message: 'Payments can’t be reached right now.', tone: 'bad' });
    });
    act(() => jest.advanceTimersByTime(theme.motion.hold.notice));

    expect(drawn('Payments can’t be reached right now.')).toBeNull();
  });

  it('a success keeps the short hold and no close control, as before', () => {
    render();

    act(() => {
      showToast({ message: 'Saved to your profile', tone: 'ok' });
    });

    expect(screen.queryByRole('button', { name: 'Dismiss this message' })).toBeNull();
    hold();
    expect(drawn('Saved to your profile')).toBeNull();
  });
});

describe('a neutral refusal the player must read', () => {
  const ONE_AT_A_TIME = 'One game at a time — wait for this one to book.';

  it('keeps its neutral colour, stays for the notice hold, and can be closed', () => {
    render();

    act(() => {
      showToast({ message: ONE_AT_A_TIME, hold: 'read' });
    });
    expect(useToastQueue.getState().queue[0]?.tone).toBe('base');

    act(() => jest.advanceTimersByTime(theme.motion.hold.toast));
    expect(drawn(ONE_AT_A_TIME)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Dismiss this message' }));
    expect(drawn(ONE_AT_A_TIME)).toBeNull();
  });

  it('leaves on its own once the notice hold has passed', () => {
    render();

    act(() => {
      showToast({ message: ONE_AT_A_TIME, hold: 'read' });
    });
    act(() => jest.advanceTimersByTime(theme.motion.hold.notice));

    expect(drawn(ONE_AT_A_TIME)).toBeNull();
  });

  it('a neutral sentence that asks nothing keeps the short hold and no close control', () => {
    render();

    act(() => {
      showToast({ message: 'Posted — you’re In.' });
    });

    expect(screen.queryByRole('button', { name: 'Dismiss this message' })).toBeNull();
    hold();
    expect(drawn('Posted — you’re In.')).toBeNull();
  });
});
