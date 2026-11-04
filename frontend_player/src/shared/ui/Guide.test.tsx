/**
 * **The guide on its own** (design-system 9.4) — what a screen-level suite cannot reach: the
 * device's back button counting as *Skip*, which only Android has, so the stage is Android's here
 * (imported by file, as `ModalStage.test.tsx` does, because the harness runs as iOS); a guide
 * shown a second time starting from its first step; and the hole cut around what each step's
 * target measured, which the route tree cannot show because the test renderer answers no
 * measurement — here a target answers one.
 *
 * The walk itself — the count, *Next*, a tap on the dim, *Got it*, *Skip*, and nothing beneath
 * answering — is walked on *Your rating*, through the route tree, in the onboarding suite.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { useRef, useState, type MutableRefObject } from 'react';
import { Dimensions, Pressable, StyleSheet, Text, View } from 'react-native';
import { Path } from 'react-native-svg';

import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';

import { Guide } from './Guide';
import { GUIDE_BUBBLE_BORDER, spotlightPath, type GuideRect } from './guideGeometry';
import { OverlayHost } from './overlay';
import { theme } from './theme';

jest.mock('./ModalStage', () => jest.requireActual('./ModalStage.android'));

/** The dim is hidden from a listener — the bubble's controls carry the names — so a walk looks for it. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

// The stage fades in on frames, whatever the phone's settings (ADR-0198 §1): held on a fake clock
// and run inside `act`, so no frame lands after a test has looked.
beforeEach(() => {
  jest.useFakeTimers();
  watchHardwareBack();
});

afterEach(() => {
  act(() => {
    jest.runOnlyPendingTimers();
  });
  jest.useRealTimers();
  stopWatchingHardwareBack();
});

/**
 * A target that says where it is in the window, as a laid-out view on a device does — the test
 * renderer's own `measureInWindow` never answers.
 */
function answering(ref: MutableRefObject<View | null>, where: GuideRect | undefined) {
  return (node: View | null) => {
    ref.current = node;
    if (node === null || where === undefined) return;
    node.measureInWindow = (answer) => answer(where.x, where.y, where.width, where.height);
  };
}

interface AppProps {
  readonly onDone?: () => void;
  /** Where the two targets are, when they answer at all. */
  readonly at?: readonly [GuideRect, GuideRect];
  /** Where each target's mark is — what each step's arrow points at — when they answer at all. */
  readonly marks?: readonly [GuideRect, GuideRect];
  /** The first step asks to stand beside its mark. */
  readonly firstBeside?: boolean;
}

function App({ onDone = () => {}, at, marks, firstBeside = false }: AppProps) {
  const [open, setOpen] = useState(true);
  const first = useRef<View | null>(null);
  const second = useRef<View | null>(null);
  const firstMark = useRef<View | null>(null);
  const secondMark = useRef<View | null>(null);
  return (
    <OverlayHost>
      <View ref={answering(first, at?.[0])}>
        <Text>Two</Text>
        <View ref={answering(firstMark, marks?.[0])} />
      </View>
      <View ref={answering(second, at?.[1])}>
        <Text>Things</Text>
        <View ref={answering(secondMark, marks?.[1])} />
      </View>
      <Pressable accessibilityLabel="Show it again" onPress={() => setOpen(true)} />
      <Guide
        visible={open}
        steps={[
          {
            target: first,
            pointAt: firstMark,
            besideMark: firstBeside,
            title: 'The first',
            body: 'What the first thing is.',
          },
          {
            target: second,
            pointAt: secondMark,
            title: 'The second',
            body: 'What the second thing is.',
          },
        ]}
        onDone={() => {
          setOpen(false);
          onDone();
        }}
      />
    </OverlayHost>
  );
}

describe('the guide', () => {
  it('counts its steps, and a tap on the dim is Next', () => {
    const onDone = jest.fn();
    render(<App onDone={onDone} />);

    expect(screen.getByText('The first')).toBeTruthy();
    expect(screen.getByText('1 of 2')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Next' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Skip the guide' })).toBeTruthy();

    fireEvent.press(screen.getByTestId('guide-dim', HIDDEN_TOO));

    expect(screen.getByText('The second')).toBeTruthy();
    expect(screen.getByText('2 of 2')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Next' })).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: 'Got it' }));

    expect(onDone).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('The second')).toBeNull();
  });

  it('takes the device’s back button as Skip, and swallows it', () => {
    const onDone = jest.fn();
    render(<App onDone={onDone} />);

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });

    expect(claimed).toBe(true);

    expect(onDone).toHaveBeenCalledTimes(1);
    expect(screen.queryByText('The first')).toBeNull();
  });

  it('starts from its first step when it is shown again', () => {
    render(<App />);
    fireEvent.press(screen.getByRole('button', { name: 'Next' }));
    fireEvent.press(screen.getByRole('button', { name: 'Skip the guide' }));

    fireEvent.press(screen.getByLabelText('Show it again'));

    expect(screen.getByText('The first')).toBeTruthy();
    expect(screen.getByText('1 of 2')).toBeTruthy();
  });

  it('cuts the hole around what each step’s target measured', () => {
    const level = { x: 33, y: 150, width: 120, height: 70 };
    const ring = { x: 260, y: 140, width: 90, height: 100 };
    const window = Dimensions.get('window');
    const grown = (rect: GuideRect) => ({
      x: rect.x - theme.space.xs,
      y: rect.y - theme.space.xs,
      width: rect.width + 2 * theme.space.xs,
      height: rect.height + 2 * theme.space.xs,
    });
    const hole = () => screen.UNSAFE_getByType(Path).props.d as string;
    render(<App at={[level, ring]} />);

    expect(hole()).toBe(spotlightPath(grown(level), window));

    fireEvent.press(screen.getByRole('button', { name: 'Next' }));

    expect(hole()).toBe(spotlightPath(grown(ring), window));
  });

  it('points each step’s arrow at its mark, not the middle of its hole', () => {
    // A figure as wide as its column, its mark near the left: the hole's middle is empty card.
    const level = { x: 30, y: 150, width: 285, height: 70 };
    const levelMark = { x: 115, y: 152, width: 20, height: 20 };
    const range = { x: 30, y: 230, width: 285, height: 24 };
    const rangeMark = { x: 200, y: 232, width: 20, height: 20 };
    // The arrow is placed from inside the bubble's outline, so its middle on the screen is the
    // bubble's edge, the outline, its offset and half its square.
    const pointedAt = () =>
      theme.size.gutter +
      GUIDE_BUBBLE_BORDER +
      StyleSheet.flatten(screen.getByTestId('guide-arrow', HIDDEN_TOO).props.style).left +
      theme.size.popoverArrow / 2;
    render(<App at={[level, range]} marks={[levelMark, rangeMark]} />);

    expect(pointedAt()).toBe(levelMark.x + levelMark.width / 2);

    fireEvent.press(screen.getByRole('button', { name: 'Next' }));

    expect(pointedAt()).toBe(rangeMark.x + rangeMark.width / 2);
  });

  it('stands a step that asks beside its mark, the arrow level with it, and the next under its hole', () => {
    // The level: a head and a large number, its mark at the head's right end — an arrow from under
    // the hole would land on whatever sits under the number.
    const level = { x: 30, y: 150, width: 111, height: 64 };
    const levelMark = { x: 121, y: 150, width: 20, height: 20 };
    const range = { x: 30, y: 230, width: 285, height: 24 };
    const rangeMark = { x: 200, y: 232, width: 20, height: 20 };
    const style = (testID: string) =>
      StyleSheet.flatten(screen.getByTestId(testID, HIDDEN_TOO).props.style);
    render(<App at={[level, range]} marks={[levelMark, rangeMark]} firstBeside />);

    const bubble = style('guide-bubble');
    expect(bubble.left).toBe(level.x + level.width + theme.space.xs + theme.space.md);
    expect(
      bubble.top + GUIDE_BUBBLE_BORDER + style('guide-arrow').top + theme.size.popoverArrow / 2,
    ).toBe(levelMark.y + levelMark.height / 2);
    // The count over the buttons, which no longer share its row.
    expect(screen.getByText('1 of 2')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'Next' }));

    expect(style('guide-bubble').left).toBe(theme.size.gutter);
  });
});
