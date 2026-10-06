/**
 * **The yes screen's one motion, on a fake clock** — `deckStage.test.tsx`'s way.
 *
 * Three things about it are not decoration, and each is a claim a diff cannot show: the
 * entrance completes in one pass and nothing loops; under reduced motion everything is simply
 * there and nothing buzzes; and otherwise the motor is asked **exactly once**, as the word lands.
 */

import { act, render, screen } from '@testing-library/react-native';
import { AccessibilityInfo, StyleSheet, Text, type ViewStyle } from 'react-native';

import { HapticsProvider } from '@/shared/lib/platform';
import { ReducedMotionProvider, theme } from '@/shared/ui';
import { fakeHaptics } from '@/test-support/platform';

import { YesEntrance } from './YesEntrance';

/** Past the whole beat — the sides, the word after them, the buttons after that. */
const PAST_THE_ENTRANCE =
  theme.motion.yesEntrance.buttonsAfter + theme.motion.yesEntrance.buttons + 100;

function draw({ ready = true, reduced = false } = {}) {
  const haptics = fakeHaptics();
  const view = render(
    <ReducedMotionProvider value={reduced}>
      <HapticsProvider port={haptics}>
        <YesEntrance
          ready={ready}
          label="Challenge! You against them"
          left={<Text>you</Text>}
          between={<Text>vs</Text>}
          right={<Text>them</Text>}
          word={<Text>Challenge!</Text>}
          buttons={<Text>doors</Text>}
        />
      </HapticsProvider>
    </ReducedMotionProvider>,
  );
  return { haptics, rerender: view.rerender };
}

function styleOf(testID: string): ViewStyle {
  return StyleSheet.flatten(screen.getByTestId(testID).props.style) as ViewStyle;
}

function translateXOf(testID: string): number {
  const transform = (styleOf(testID).transform ?? []) as readonly Record<string, unknown>[];
  return Number(transform.find((one) => 'translateX' in one)?.translateX);
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => {
  jest.useRealTimers();
  jest.restoreAllMocks();
});

describe('the entrance', () => {
  it('starts with the sides off the edges and the word and the doors invisible', () => {
    draw();

    expect(translateXOf('yes-left')).toBeLessThan(0);
    expect(translateXOf('yes-right')).toBeGreaterThan(0);
    expect(styleOf('yes-word').opacity).toBe(0);
    expect(styleOf('yes-buttons').opacity).toBe(0);
  });

  it('completes in one pass — the sides meet, the word lands, the doors fade in, and nothing loops', () => {
    draw();

    act(() => jest.advanceTimersByTime(PAST_THE_ENTRANCE));

    expect(translateXOf('yes-left')).toBe(0);
    expect(translateXOf('yes-right')).toBe(0);
    expect(styleOf('yes-word').opacity).toBe(1);
    expect(styleOf('yes-buttons').opacity).toBe(1);

    // Still there, a long time later: nothing loops.
    act(() => jest.advanceTimersByTime(PAST_THE_ENTRANCE * 10));
    expect(styleOf('yes-buttons').opacity).toBe(1);
  });

  it('fades the doors in last, after the word has landed', () => {
    draw();

    act(() => jest.advanceTimersByTime(theme.motion.yesEntrance.buttonsAfter - 1));

    expect(styleOf('yes-buttons').opacity).toBe(0);
  });

  it('asks the motor once, as the word lands, and never again', () => {
    const { haptics } = draw();

    act(() => jest.advanceTimersByTime(theme.motion.yesEntrance.wordAfter));
    expect(haptics.felt).toHaveLength(0);

    act(() => jest.advanceTimersByTime(PAST_THE_ENTRANCE));
    expect(haptics.felt).toEqual(['success']);

    act(() => jest.advanceTimersByTime(PAST_THE_ENTRANCE * 10));
    expect(haptics.felt).toHaveLength(1);
  });

  it('waits for its faces: nothing moves until the screen says it is ready', () => {
    const { haptics, rerender } = draw({ ready: false });

    act(() => jest.advanceTimersByTime(PAST_THE_ENTRANCE));
    expect(styleOf('yes-word').opacity).toBe(0);
    expect(haptics.felt).toHaveLength(0);

    rerender(
      <ReducedMotionProvider value={false}>
        <HapticsProvider port={haptics}>
          <YesEntrance
            ready
            label="Challenge! You against them"
            left={<Text>you</Text>}
            between={<Text>vs</Text>}
            right={<Text>them</Text>}
            word={<Text>Challenge!</Text>}
            buttons={<Text>doors</Text>}
          />
        </HapticsProvider>
      </ReducedMotionProvider>,
    );
    act(() => jest.advanceTimersByTime(PAST_THE_ENTRANCE));

    expect(styleOf('yes-word').opacity).toBe(1);
    expect(haptics.felt).toEqual(['success']);
  });
});

describe('under reduced motion', () => {
  it('is simply there, and nothing buzzes', () => {
    const { haptics } = draw({ reduced: true });

    expect(translateXOf('yes-left')).toBe(0);
    expect(translateXOf('yes-right')).toBe(0);
    expect(styleOf('yes-word').opacity).toBe(1);
    expect(styleOf('yes-buttons').opacity).toBe(1);

    act(() => jest.advanceTimersByTime(PAST_THE_ENTRANCE));
    expect(haptics.felt).toHaveLength(0);
  });
});

/**
 * §20.11's collapse is one condition satisfied by **either** reduced motion or a running screen
 * reader — but a buzz is not a picture, so a listener who has not asked for calm still gets the
 * one haptic, at once.
 */
describe('under a screen reader', () => {
  it('is simply there, and buzzes once', async () => {
    jest.spyOn(AccessibilityInfo, 'isScreenReaderEnabled').mockResolvedValue(true);
    const { haptics } = draw();

    // The OS answers a promise; let it land.
    await act(async () => {
      await Promise.resolve();
    });

    expect(styleOf('yes-word').opacity).toBe(1);
    expect(haptics.felt).toEqual(['success']);
  });
});
