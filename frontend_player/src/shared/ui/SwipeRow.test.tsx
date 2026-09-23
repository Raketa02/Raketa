/**
 * The swipe row, driven by touches — the things about it no screen can observe from a press.
 *
 * The finger is `test-support/swipe.ts`', which says why the handlers are called directly and in
 * which order. What is asserted is what a player would meet — **whether the control behind the
 * row is reachable** — and one thing only a test can see: which moves the row claims and which it
 * leaves to the list, because that decision is made before anything is drawn.
 *
 * The arithmetic is `swipeRowGeometry.test.ts`'; this is the component obeying it.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';

import {
  claimsThePress,
  gestureSurfaceOf,
  moved,
  swipe,
  touchDown,
  yieldsToTheList,
} from '@/test-support/swipe';

import { PressableCard } from './Card';
import { SwipeRow, type SwipeRowProps } from './SwipeRow';
import { theme } from './theme';

const ROW = 'tomek.p, Squash';
const LEAVE = 'Leave the game';
const { reveal: REVEAL, intent: INTENT } = theme.size.swipeRow;

function draw(over: Partial<SwipeRowProps> = {}) {
  const props: SwipeRowProps = {
    reveal: { label: LEAVE, onPress: () => undefined },
    children: (
      <PressableCard accessibilityLabel={ROW} onPress={() => undefined}>
        <Text>tomek.p</Text>
      </PressableCard>
    ),
    ...over,
  };
  return render(<SwipeRow {...props} />);
}

const card = () => screen.getByLabelText(ROW);

describe('which moves the row claims', () => {
  /** The list's own gesture, and the one thing this control must never take. */
  it('leaves a move down the screen to the list', () => {
    draw();
    touchDown(card());

    expect(moved(card(), -4, 40)).toBe(false);
  });

  it('claims a move across the screen once it has travelled the intent distance', () => {
    draw();
    touchDown(card());

    expect(moved(card(), -INTENT + 1, 3)).toBe(false);
    expect(moved(card(), -INTENT, 3)).toBe(true);
  });

  /** A tap is a tap: the card under the finger is a door, and the row never takes the press. */
  it('claims nothing when the finger lands', () => {
    draw();

    expect(claimsThePress(card())).toBe(false);
  });

  /** Once claimed, the list may not take the gesture back mid-swipe — the slider's own rule. */
  it('refuses to hand a claimed swipe back to the list', () => {
    draw();

    expect(yieldsToTheList(card())).toBe(false);
  });
});

describe('what a swipe reveals', () => {
  /** Closed, the control is behind the card — and behind it for a screen reader too. */
  it('keeps the control out of reach while the row is closed', () => {
    draw();

    expect(card()).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE })).toBeNull();
  });

  it('reveals the control once the card has been dragged half its width', () => {
    draw();

    swipe(card(), -REVEAL / 2);

    expect(screen.getByRole('button', { name: LEAVE })).toBeTruthy();
  });

  it('reveals nothing on a swipe short of that', () => {
    draw();

    swipe(card(), -REVEAL / 2 + 1);

    expect(screen.queryByRole('button', { name: LEAVE })).toBeNull();
  });

  /** From fully revealed, the card has to come back past the middle to close. */
  it('closes again on a swipe back the other way', () => {
    draw();

    swipe(card(), -REVEAL);
    swipe(card(), REVEAL / 2 + 1);

    expect(screen.queryByRole('button', { name: LEAVE })).toBeNull();
  });

  it('stays revealed on a swipe back that stops short of the middle', () => {
    draw();

    swipe(card(), -REVEAL);
    swipe(card(), REVEAL / 2 - 1);

    expect(screen.getByRole('button', { name: LEAVE })).toBeTruthy();
  });

  /** The swipe only reveals; the act is the control's, and the row closes behind it. */
  it('presses through to the control, and closes the row', () => {
    const pressed: string[] = [];
    draw({ reveal: { label: LEAVE, onPress: () => pressed.push('left') } });

    swipe(card(), -REVEAL);
    fireEvent.press(screen.getByRole('button', { name: LEAVE }));

    expect(pressed).toEqual(['left']);
    expect(screen.queryByRole('button', { name: LEAVE })).toBeNull();
  });
});

describe('a row with nothing to reveal', () => {
  /** No dead controls: the row does not move, and there is nothing behind it to reach. */
  it('claims no touch at all, and holds no control', () => {
    draw({ reveal: undefined });

    expect(gestureSurfaceOf(card())).toBeUndefined();
    expect(swipe(card(), -REVEAL)).toBe(false);
    expect(screen.queryByText(LEAVE, { includeHiddenElements: true })).toBeNull();
  });

  /** A row whose control goes away while it is open closes, rather than framing an empty space. */
  it('closes when what it revealed is withdrawn', () => {
    const drawn = draw();
    swipe(card(), -REVEAL);
    expect(screen.getByRole('button', { name: LEAVE })).toBeTruthy();

    drawn.rerender(
      <SwipeRow reveal={undefined}>
        <PressableCard accessibilityLabel={ROW} onPress={() => undefined}>
          <Text>tomek.p</Text>
        </PressableCard>
      </SwipeRow>,
    );

    expect(screen.queryByText(LEAVE, { includeHiddenElements: true })).toBeNull();
  });
});
