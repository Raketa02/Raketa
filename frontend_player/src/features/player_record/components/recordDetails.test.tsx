/**
 * **The *Full record* fold, at its own seam** — shut by default, opened and shut again by its row,
 * moving both ways, and hidden from assistive technology while shut.
 *
 * Reanimated is real here, as it is in the router harness (ADR-0176 §2): every worklet runs on the
 * JavaScript thread and `withTiming` on the fake clock. Nothing lays anything out under jest, so the
 * content's height is handed to the fold as a layout event — the fast filter's suite's method.
 *
 * **What this seam cannot show, and what it holds instead.** The fold once animated its `height`
 * frame by frame, and on the phone it froze mid-way and jumped: under the New Architecture
 * Reanimated commits a layout prop to the shadow tree and skips that commit while React commits
 * anywhere in the app. Jest has no shadow tree and no commit to skip, so the freeze cannot be
 * reproduced here — it was measured on the device. What it holds is the shape that keeps it fixed:
 * the fold's height is React's, one change per press, and the only values animated frame by frame
 * are opacity and transform.
 */

import { act, fireEvent, render, renderHook, screen } from '@testing-library/react-native';
import type { ReactNode } from 'react';
import { StyleSheet, Text } from 'react-native';
import { getAnimatedStyle } from 'react-native-reanimated';

import { ReducedMotionProvider, theme } from '@/shared/ui';

import { RecordDetails, useFoldTransition } from './RecordDetails';
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
  fireEvent(content(), 'layout', {
    nativeEvent: { layout: { width: 345, height: CONTENT, x: 0, y: 0 } },
  });
}

const row = () => screen.getByRole('button', { name: FULL_RECORD });
const fold = () => screen.getByTestId('full-record-fold', { includeHiddenElements: true });
const content = () => screen.getByTestId('full-record-content', { includeHiddenElements: true });

/** The fold's height as React lays it out — the one change a press makes. */
function foldHeight(): number | undefined {
  return (StyleSheet.flatten(fold().props.style) as { readonly height?: number }).height;
}

function contentOpacity(): number {
  return (getAnimatedStyle(content()) as { readonly opacity?: number }).opacity ?? 0;
}

/** The fold's and the content's styles as drawn on this frame, React's and Reanimated's merged. */
function drawn(): Record<string, string>[] {
  return [fold(), content()].map((view) =>
    Object.fromEntries(
      Object.entries(getAnimatedStyle(view) ?? {}).map(([key, value]) => [
        key,
        JSON.stringify(value),
      ]),
    ),
  );
}

/** Which style keys changed value between two frames — with no press between them, only what is
 *  animated frame by frame. */
function movedBetween(before: Record<string, string>[], after: Record<string, string>[]): string[] {
  const keys = new Set<string>();
  before.forEach((was, i) => {
    const now = after[i] ?? {};
    for (const key of new Set([...Object.keys(was), ...Object.keys(now)])) {
      if (was[key] !== now[key]) keys.add(key);
    }
  });
  return [...keys].sort();
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

  it('opens on a press to the content’s height in one change, and fades the content in over the disclose', () => {
    drawFold();
    press();

    expect(row().props.accessibilityState).toEqual({ expanded: true });
    expect(screen.getByText('Shows up')).toBeTruthy();
    // React's height, at once: the layout transition is what moves the native frame there.
    expect(foldHeight()).toBe(CONTENT);

    run(theme.motion.disclose / 2);
    expect(contentOpacity()).toBeGreaterThan(0);
    expect(contentOpacity()).toBeLessThan(1);

    run(theme.motion.disclose);
    expect(contentOpacity()).toBe(1);
  });

  it('shuts on a second press in one change, and fades the content out on the way back', () => {
    drawFold();
    press();
    run(theme.motion.disclose + FRAME);

    press();
    expect(row().props.accessibilityState).toEqual({ expanded: false });
    expect(screen.queryByText('Shows up')).toBeNull();
    expect(foldHeight()).toBe(0);

    run(theme.motion.disclose / 2);
    expect(contentOpacity()).toBeGreaterThan(0);
    expect(contentOpacity()).toBeLessThan(1);

    run(theme.motion.disclose);
    expect(contentOpacity()).toBe(0);
  });

  it('animates no layout prop frame by frame, either way — opacity and transform only', () => {
    drawFold();
    const pressAndWatch = () => {
      press();
      run(FRAME);
      const early = drawn();
      run(theme.motion.disclose / 2);
      const halfway = drawn();
      run(theme.motion.disclose);
      return movedBetween(early, halfway);
    };

    // On the phone a moving `height` froze whenever React committed (the module note above).
    expect(pressAndWatch()).toEqual(['opacity', 'transform']);
    expect(pressAndWatch()).toEqual(['opacity', 'transform']);
  });

  it('takes its new height again when the content is measured anew while open', () => {
    drawFold();
    press();
    run(theme.motion.disclose + FRAME);

    fireEvent(content(), 'layout', {
      nativeEvent: { layout: { width: 345, height: CONTENT + 60, x: 0, y: 0 } },
    });
    expect(foldHeight()).toBe(CONTENT + 60);
  });

  it('is simply open or shut under reduced motion', () => {
    drawFold({ reduced: true });
    press();
    run(FRAME);
    expect(foldHeight()).toBe(CONTENT);
    expect(contentOpacity()).toBe(1);

    press();
    run(FRAME);
    expect(foldHeight()).toBe(0);
    expect(contentOpacity()).toBe(0);
  });
});

describe('useFoldTransition — what moves the fold, the sheet and the foot', () => {
  function under(reduced: boolean) {
    return function Motion({ children }: { readonly children: ReactNode }) {
      return <ReducedMotionProvider value={reduced}>{children}</ReducedMotionProvider>;
    };
  }

  it('is a layout transition, the same one on every call', () => {
    const first = renderHook(() => useFoldTransition(), { wrapper: under(false) }).result.current;
    const second = renderHook(() => useFoldTransition(), { wrapper: under(false) }).result.current;

    expect(first).toBeDefined();
    expect(second).toBe(first);
  });

  it('is absent under reduced motion, so every frame takes its new place at once', () => {
    expect(
      renderHook(() => useFoldTransition(), { wrapper: under(true) }).result.current,
    ).toBeUndefined();
  });
});
