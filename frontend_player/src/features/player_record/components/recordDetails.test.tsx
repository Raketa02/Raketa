/**
 * **The *Full record* fold, at its own seam** — shut by default, opened and shut again by its row,
 * moving both ways on the UI thread, and hidden from assistive technology while shut.
 *
 * Reanimated is real here, as it is in the router harness (ADR-0176 §2): every worklet runs on the
 * JavaScript thread and `withTiming` on the fake clock. Nothing lays anything out under jest, so the
 * content's height is handed to the fold as a layout event — the fast filter's suite's method.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import { ReducedMotionProvider, theme } from '@/shared/ui';

import { RecordDetails } from './RecordDetails';
import { FULL_RECORD } from './recordPresentation';

/** What the record card and the tags would measure at, laid out at their whole height. */
const CONTENT = 240;

/** One frame: an animated style is applied on the next frame, on the fake clock. */
const FRAME = 16;

function drawFold({ reduced = false }: { readonly reduced?: boolean } = {}) {
  render(
    <ReducedMotionProvider value={reduced}>
      <RecordDetails>
        <Text>Shows up</Text>
      </RecordDetails>
    </ReducedMotionProvider>,
  );
  fireEvent(screen.getByTestId('full-record-content', { includeHiddenElements: true }), 'layout', {
    nativeEvent: { layout: { width: 345, height: CONTENT, x: 0, y: 0 } },
  });
}

const row = () => screen.getByRole('button', { name: FULL_RECORD });

function foldHeight(): number | undefined {
  const fold = screen.getByTestId('full-record-fold', { includeHiddenElements: true });
  return (getAnimatedStyle(fold) as { readonly height?: number }).height;
}

function press() {
  fireEvent.press(row());
}

function run(ms: number) {
  act(() => jest.advanceTimersByTime(ms));
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe('the Full record fold', () => {
  it('starts shut: nothing under it is read, and the row says it is collapsed', () => {
    drawFold();
    run(FRAME);

    expect(row().props.accessibilityState).toEqual({ expanded: false });
    expect(screen.queryByText('Shows up')).toBeNull();
    expect(foldHeight()).toBe(0);
  });

  it('draws a chevron alone, with no words, and is named Full record for a screen reader', () => {
    drawFold();

    expect(row().props.accessibilityLabel).toBe(FULL_RECORD);
    expect(screen.queryByText(FULL_RECORD, { includeHiddenElements: true })).toBeNull();
  });

  it('opens on a press, growing to the content’s height over the disclose', () => {
    drawFold();
    press();

    expect(row().props.accessibilityState).toEqual({ expanded: true });
    expect(screen.getByText('Shows up')).toBeTruthy();

    run(theme.motion.disclose / 2);
    const halfway = foldHeight() ?? 0;
    expect(halfway).toBeGreaterThan(0);
    expect(halfway).toBeLessThan(CONTENT);

    run(theme.motion.disclose);
    expect(foldHeight()).toBe(CONTENT);
  });

  it('shuts on a second press, and moves on the way back too', () => {
    drawFold();
    press();
    run(theme.motion.disclose + FRAME);

    press();
    expect(row().props.accessibilityState).toEqual({ expanded: false });
    expect(screen.queryByText('Shows up')).toBeNull();

    run(theme.motion.disclose / 2);
    const halfway = foldHeight() ?? 0;
    expect(halfway).toBeGreaterThan(0);
    expect(halfway).toBeLessThan(CONTENT);

    run(theme.motion.disclose);
    expect(foldHeight()).toBe(0);
  });

  it('is simply open or shut under reduced motion', () => {
    drawFold({ reduced: true });
    press();
    run(FRAME);
    expect(foldHeight()).toBe(CONTENT);

    press();
    run(FRAME);
    expect(foldHeight()).toBe(0);
  });
});
