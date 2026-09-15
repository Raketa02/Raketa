/**
 * The stage's drag and its two animations, and the things about them that are **not**
 * decoration.
 *
 * `onLeft` is a fact rather than an animation's courtesy — it is what unlocks the buttons and
 * advances the deck — so it has to fire whether the card travelled or not; a listener under
 * `useCollapsedPresentation` would otherwise hold a deck that never moves.
 *
 * A card that comes back has to come back **straight**. An answer refused puts the card on
 * screen again, and a stopped `Animated.Value` keeps whatever fraction of the flight it
 * reached — so the transform is asserted here, on the one path the deck documents as
 * recoverable and the screen's own suite can only see in words.
 *
 * The **direction**: a yes leaves right and a pass leaves left, which is the one thing on this
 * surface a player is told without a sentence, and a sign nobody can see is a sign that flips
 * silently.
 *
 * And the **drag**, at the seam the screen sees: the stamps follow the finger, a release past
 * the threshold asks the screen and flies on `taken`, settles on `withheld` and short of the
 * threshold, the motor ticks once at the threshold and never under reduced motion, and the
 * cards behind are drawn and hidden from a listener.
 */

import { act, render, screen } from '@testing-library/react-native';
import { Text, type ViewStyle } from 'react-native';

import { HapticsProvider } from '@/shared/lib/platform';
import { ReducedMotionProvider, theme } from '@/shared/ui';
import { fakeHaptics } from '@/test-support/platform';
import { dragTo, release, swipe } from '@/test-support/swipe';

import { DeckStage, type DeckExit, type DragVerdict } from './DeckStage';

/** How long a card takes to leave. Longer than the component's own 240, so a flight completes. */
const PAST_THE_FLIGHT = 400;

const { commit } = theme.size.deckSwipe;

interface StageOver {
  readonly leaving?: DeckExit;
  readonly onLeft?: jest.Mock;
  readonly onAnswer?: jest.Mock<DragVerdict, [DeckExit]>;
  readonly collapsed?: boolean;
  readonly behind?: readonly string[];
}

function drawStage({
  leaving,
  onLeft = jest.fn(),
  onAnswer = jest.fn<DragVerdict, [DeckExit]>(() => 'taken'),
  collapsed = false,
  behind = [],
}: StageOver = {}) {
  const haptics = fakeHaptics();
  const tree = (over: Partial<StageOver>) => (
    <ReducedMotionProvider value={over.collapsed ?? collapsed}>
      <HapticsProvider port={haptics}>
        <DeckStage
          leaving={'leaving' in over ? over.leaving : leaving}
          onLeft={onLeft}
          onAnswer={onAnswer}
          behind={(over.behind ?? behind).map((name) => (
            <Text key={name}>{name}</Text>
          ))}
        >
          <Text accessibilityLabel="Marek Z." accessibilityRole="button">
            Marek Z.
          </Text>
        </DeckStage>
      </HapticsProvider>
    </ReducedMotionProvider>
  );
  const view = render(tree({}));
  return {
    onLeft,
    onAnswer,
    haptics,
    rerender: (over: Partial<StageOver>) => view.rerender(tree(over)),
  };
}

const card = () => screen.getByLabelText('Marek Z.');

/** The stage's own animated view is the responder's — the nearest `View` above the card. */
function topCard(): { readonly props: { readonly style: unknown } } {
  let node = card().parent;
  while (node !== null && node.props.onMoveShouldSetResponder === undefined) node = node.parent;
  if (node === null) throw new Error('no stage above the card');
  return node;
}

function transformOf(): readonly Record<string, unknown>[] {
  const styles = [topCard().props.style].flat(3) as (ViewStyle | undefined)[];
  const style = styles.find((entry) => entry?.transform !== undefined);
  return (style?.transform ?? []) as readonly Record<string, unknown>[];
}

/** An `Animated.Value` renders as itself; what matters is the number it currently holds. */
const valueOf = (transform: Record<string, unknown> | undefined, key: string): unknown =>
  transform?.[key];

const translateX = () => Number(valueOf(transformOf()[0], 'translateX'));

/** The stamps and the cards behind are hidden from assistive technology on purpose; a query about the drawing says so. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

function stampOpacity(said: DeckExit): number {
  const styles = [screen.getByTestId(`deck-stamp-${said}`, HIDDEN_TOO).props.style].flat(3) as (
    { opacity?: unknown } | undefined
  )[];
  return Number(styles.find((entry) => entry?.opacity !== undefined)?.opacity);
}

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe('a card leaving on a button', () => {
  it('reports that it has gone, once the flight is over', () => {
    const { onLeft } = drawStage({ leaving: 'no' });

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
    const { onLeft } = drawStage({ leaving: 'no', collapsed: true });

    expect(onLeft).toHaveBeenCalledTimes(1);
  });

  /**
   * *Let's play* right, *Not today* left — the two buttons' own order. Asserted as **signs**
   * rather than as distances, because the distance is a number somebody may tune and the
   * directions are the decision.
   */
  it('goes right on a yes and left on a pass', () => {
    drawStage({ leaving: 'yes' });
    act(() => jest.advanceTimersByTime(100));
    const yes = translateX();

    screen.unmount();

    drawStage({ leaving: 'no' });
    act(() => jest.advanceTimersByTime(100));
    const no = translateX();

    expect(yes).toBeGreaterThan(0);
    expect(no).toBeLessThan(0);
    expect(no).toBe(-yes);
  });
});

describe('a card that comes back', () => {
  it('comes back straight, rather than stopped mid-flight', () => {
    const { rerender } = drawStage({ leaving: 'no' });
    act(() => jest.advanceTimersByTime(100));

    // Mid-flight: the card is shifted and turned.
    expect(translateX()).not.toBe(0);

    rerender({ leaving: undefined });

    expect(translateX()).toBe(0);
    expect(valueOf(transformOf()[3], 'rotate')).toBe('0deg');
  });
});

describe('the drag', () => {
  it('is claimed on a move across, and never on the press', () => {
    drawStage();

    expect(dragTo(card(), 40)).toBe(true);
  });

  /** The stamps are invisible at rest, follow the drag, and are full at the threshold. */
  it('fades the stamp in with the finger, and is full at the threshold', () => {
    drawStage();
    expect(stampOpacity('yes')).toBe(0);
    expect(stampOpacity('no')).toBe(0);

    dragTo(card(), commit / 2);
    expect(stampOpacity('yes')).toBeCloseTo(0.5, 5);
    expect(stampOpacity('no')).toBe(0);
    release(card());

    dragTo(card(), -commit);
    expect(stampOpacity('no')).toBe(1);
    expect(stampOpacity('yes')).toBe(0);
  });

  it('follows the finger across, and turns with it', () => {
    drawStage();

    dragTo(card(), 60);

    expect(translateX()).toBe(60);
    expect(valueOf(transformOf()[3], 'rotate')).not.toBe('0deg');
  });

  /** Released short of the threshold, the card goes back to rest — no answer, nobody asked. */
  it('settles back when released short of the threshold', () => {
    const { onAnswer } = drawStage();

    swipe(card(), commit - 1);
    act(() => jest.advanceTimersByTime(theme.motion.settle + 50));

    expect(onAnswer).not.toHaveBeenCalled();
    expect(translateX()).toBe(0);
  });

  it('asks the screen at the threshold, and flies in the drag’s direction once taken', () => {
    const { onAnswer, onLeft, rerender } = drawStage();

    swipe(card(), commit);
    expect(onAnswer).toHaveBeenCalledWith('yes');

    // The screen took the answer: it sets `leaving`, and the flight runs from where the
    // finger left the card.
    rerender({ leaving: 'yes' });
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    expect(translateX()).toBeGreaterThan(commit);
    expect(onLeft).toHaveBeenCalledTimes(1);
  });

  it('asks for a pass on a drag left', () => {
    const { onAnswer } = drawStage();

    swipe(card(), -commit);

    expect(onAnswer).toHaveBeenCalledWith('no');
  });

  /** The ceiling: the screen withholds, and the card settles with nothing sent. */
  it('settles back when the screen withholds the answer', () => {
    const { onAnswer, onLeft } = drawStage({
      onAnswer: jest.fn<DragVerdict, [DeckExit]>(() => 'withheld'),
    });

    swipe(card(), commit + 20);
    act(() => jest.advanceTimersByTime(theme.motion.settle + 50));

    expect(onAnswer).toHaveBeenCalledWith('yes');
    expect(onLeft).not.toHaveBeenCalled();
    expect(translateX()).toBe(0);
  });

  /** A card already on its way cannot be dragged: the answer has been given. */
  it('is not claimed while the card is leaving', () => {
    drawStage({ leaving: 'yes' });

    expect(dragTo(card(), 40)).toBe(false);
  });
});

describe('the haptic', () => {
  it('ticks once as the finger first crosses the threshold, and not before', () => {
    const { haptics } = drawStage();

    dragTo(card(), commit - 1);
    expect(haptics.felt).toEqual([]);
    release(card());

    dragTo(card(), commit + 30);
    expect(haptics.felt).toEqual(['light']);
  });

  it('ticks once per gesture, however far past the threshold the finger goes', () => {
    const { haptics } = drawStage();

    swipe(card(), commit * 3);

    expect(haptics.felt).toEqual(['light']);
  });

  /** No motion, no buzz — and the answer still lands, which the collapsed flight test holds. */
  it('is silent under reduced motion', () => {
    const { haptics, onAnswer } = drawStage({ collapsed: true });

    swipe(card(), commit + 30);

    expect(haptics.felt).toEqual([]);
    expect(onAnswer).toHaveBeenCalledWith('yes');
  });
});

describe('the cards behind', () => {
  it('draws the real cards it is handed, behind the top one', () => {
    drawStage({ behind: ['Ana K.', 'Ola W.'] });

    expect(screen.getByText('Ana K.', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Ola W.', HIDDEN_TOO)).toBeTruthy();
  });

  /** The top card is the one element; a listener does not hear the queue. */
  it('hides them from assistive technology', () => {
    drawStage({ behind: ['Ana K.'] });

    expect(screen.queryByText('Ana K.')).toBeNull();
    let behind = screen.getByText('Ana K.', HIDDEN_TOO).parent;
    while (behind !== null && behind.props.accessibilityElementsHidden === undefined) {
      behind = behind.parent;
    }
    expect(behind?.props.accessibilityElementsHidden).toBe(true);
    expect(behind?.props.importantForAccessibility).toBe('no-hide-descendants');
  });

  it('draws nothing behind when handed nothing', () => {
    drawStage();

    expect(screen.getByLabelText('Marek Z.')).toBeTruthy();
    expect(screen.queryByText('Ana K.', HIDDEN_TOO)).toBeNull();
  });
});
