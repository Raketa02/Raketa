/**
 * The card's two animations, and the two things about them that are **not** decoration.
 *
 * `onLeft` is a fact rather than an animation's courtesy — it is what unlocks the two buttons
 * and advances the deck — so it has to fire whether the card travelled or not; a listener
 * under `useCollapsedPresentation` would otherwise hold a deck that never moves.
 *
 * And a card that comes back has to come back **straight**. An answer refused puts the card on
 * screen again, and a stopped `Animated.Value` keeps whatever fraction of the flight it
 * reached — so the transform is asserted here, on the one path the deck documents as
 * recoverable and the screen's own suite can only see in words.
 */

import { act, render, screen } from '@testing-library/react-native';
import { Text, View, type ViewStyle } from 'react-native';

import { ReducedMotionProvider } from '@/shared/ui';

import { DeckStage } from './DeckStage';

/** How long a card takes to leave. Longer than the component's own 240, so a flight completes. */
const PAST_THE_FLIGHT = 400;

function drawStage(leaving: boolean, onLeft = jest.fn(), collapsed = false) {
  const view = render(
    <ReducedMotionProvider value={collapsed}>
      <DeckStage leaving={leaving} onLeft={onLeft}>
        <Text>Marek Z.</Text>
      </DeckStage>
    </ReducedMotionProvider>,
  );
  return { onLeft, rerender: view.rerender };
}

/** The stage's own animated view is the only `View` it draws. */
function transformOf(): readonly Record<string, unknown>[] {
  const [stage] = screen.UNSAFE_getAllByType(View);
  const style = stage?.props.style as ViewStyle | undefined;
  return (style?.transform ?? []) as readonly Record<string, unknown>[];
}

/** An `Animated.Value` renders as itself; what matters is the number it currently holds. */
const valueOf = (transform: Record<string, unknown> | undefined, key: string): unknown =>
  transform?.[key];

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe('a card leaving', () => {
  it('reports that it has gone, once the flight is over', () => {
    const { onLeft } = drawStage(true);

    expect(onLeft).not.toHaveBeenCalled();
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    expect(onLeft).toHaveBeenCalledTimes(1);
  });

  /**
   * §20.11's collapse is one condition satisfied by **either** reduced motion or a running
   * screen reader. Under it there is no travel — and the card still lands, because the
   * callback is what tells the screen the deck may advance.
   */
  it('reports it immediately where presentation is collapsed', () => {
    const { onLeft } = drawStage(true, jest.fn(), true);

    expect(onLeft).toHaveBeenCalledTimes(1);
  });
});

describe('a card that comes back', () => {
  it('comes back straight, rather than stopped mid-flight', () => {
    const { rerender } = drawStage(true);
    act(() => jest.advanceTimersByTime(100));

    // Mid-flight: the card is shifted and turned.
    const flying = transformOf();
    expect(valueOf(flying[0], 'translateX')).not.toBe(0);

    rerender(
      <ReducedMotionProvider value={false}>
        <DeckStage leaving={false} onLeft={() => undefined}>
          <Text>Marek Z.</Text>
        </DeckStage>
      </ReducedMotionProvider>,
    );

    const returned = transformOf();
    expect(valueOf(returned[0], 'translateX')).toBe(0);
    expect(valueOf(returned[3], 'rotate')).toBe('0deg');
  });
});
