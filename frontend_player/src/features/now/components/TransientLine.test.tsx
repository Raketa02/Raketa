/**
 * The line itself: what it does with time, and what it does when the OS has asked
 * for less movement.
 *
 * Rendered directly rather than through the screen, because the two rules worth
 * pinning are invisible from there. **The hold is not the animation** — design
 * system 12.1 established that distinction for the calculating screen and 11.4
 * inherits it — so reduced motion drops the fade and keeps the three seconds. A
 * flow test cannot tell the two apart: the line is gone either way by the time it
 * looks.
 */

import { AccessibilityInfo } from 'react-native';
import { act, render, screen } from '@testing-library/react-native';

import { theme } from '@/shared/ui';

import { TRANSIENT_LINE_ID, TransientLine } from './TransientLine';

const HOLD = theme.motion.hold.line;
const LINE = 'That seat has gone.';

let announced: jest.SpyInstance;
let reduced: jest.SpyInstance;

beforeEach(() => {
  jest.useFakeTimers();
  announced = jest
    .spyOn(AccessibilityInfo, 'announceForAccessibility')
    .mockImplementation(() => {});
  reduced = jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
});

afterEach(() => {
  announced.mockRestore();
  reduced.mockRestore();
  jest.useRealTimers();
});

/** Let the reduced-motion answer land before the fade is armed. */
async function drawn(onFaded = jest.fn()) {
  render(<TransientLine line={LINE} onFaded={onFaded} />);
  await act(async () => {});
  return onFaded;
}

function advance(ms: number) {
  act(() => {
    jest.advanceTimersByTime(ms);
  });
}

describe('the transient line', () => {
  it('says its sentence out loud when it appears', async () => {
    // Part 13's rule for the toast, and truer of something quieter than one: a
    // message a screen-reader user cannot hear is a message that did not happen.
    // There is no live region to fall back on — the line is unmounted a moment
    // later, and a region that has gone announces nothing.
    await drawn();

    expect(announced).toHaveBeenCalledWith(LINE);
  });

  it('holds the sentence long enough to read, and then reports that it has gone', async () => {
    const onFaded = await drawn();

    advance(HOLD - 100);
    expect(screen.getByTestId(TRANSIENT_LINE_ID)).toBeTruthy();
    expect(onFaded).not.toHaveBeenCalled();

    advance(100 + theme.motion.fade);
    expect(onFaded).toHaveBeenCalledTimes(1);
  });

  it('keeps the hold and skips the fade when the OS asks for less movement', async () => {
    // The fade is the animation; the three seconds are not. A player who asked for
    // reduced motion is the last one who should get a sentence she cannot finish.
    reduced.mockResolvedValue(true);
    const onFaded = await drawn();

    advance(HOLD - 1);
    expect(onFaded).not.toHaveBeenCalled();

    // One frame past the hold, with no fade to wait out.
    advance(1);
    expect(onFaded).toHaveBeenCalledTimes(1);
  });

  it('reports nothing when it is taken off screen mid-hold', async () => {
    // A second seat tapped, or the screen left. Reporting *faded* here would clear
    // whichever line is on screen now.
    const onFaded = jest.fn();
    const view = render(<TransientLine line={LINE} onFaded={onFaded} />);
    await act(async () => {});

    advance(HOLD / 2);
    view.unmount();
    advance(HOLD * 2);

    expect(onFaded).not.toHaveBeenCalled();
  });
});
