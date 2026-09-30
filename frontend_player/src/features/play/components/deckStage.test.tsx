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

import { act, render, screen, within } from '@testing-library/react-native';
import { useEffect } from 'react';
import { Text, type ViewStyle } from 'react-native';

import { HapticsProvider } from '@/shared/lib/platform';
import { ReducedMotionProvider, theme } from '@/shared/ui';
import { fakeHaptics } from '@/test-support/platform';
import { dragTo, release, swipe } from '@/test-support/swipe';

import { DeckStage, type DeckExit, type DragVerdict, type StampWords } from './DeckStage';
import { PLAYERS_STAMPS } from './deckPresentation';
import { STACK } from './deckStageGeometry';

/** How long a card takes to leave. Longer than the component's own 240, so a flight completes. */
const PAST_THE_FLIGHT = 400;

const { commit } = theme.size.deckSwipe;

interface StageOver {
  readonly leaving?: DeckExit;
  readonly onLeft?: jest.Mock;
  readonly onAnswer?: jest.Mock<DragVerdict, [DeckExit]>;
  readonly collapsed?: boolean;
  /** The people on the stage, the top card first. */
  readonly cards?: readonly string[];
  readonly stamps?: Readonly<Record<DeckExit, StampWords>>;
}

/** Every mount of a face, in order — so a card promoted in place can be told from one redrawn. */
let mounted: string[] = [];

/** A card: the one element on the top, and hidden behind — the stage decides which. */
function Face({ name }: { readonly name: string }) {
  useEffect(() => {
    mounted.push(name);
  }, [name]);
  return (
    <Text accessibilityLabel={name} accessibilityRole="button">
      {name}
    </Text>
  );
}

function drawStage({
  leaving,
  onLeft = jest.fn(),
  onAnswer = jest.fn<DragVerdict, [DeckExit]>(() => 'taken'),
  collapsed = false,
  cards = ['Marek Z.'],
  stamps = PLAYERS_STAMPS,
}: StageOver = {}) {
  const haptics = fakeHaptics();
  const tree = (over: Partial<StageOver>) => (
    <ReducedMotionProvider value={over.collapsed ?? collapsed}>
      <HapticsProvider port={haptics}>
        <DeckStage
          leaving={'leaving' in over ? over.leaving : leaving}
          onLeft={onLeft}
          onAnswer={onAnswer}
          cards={(over.cards ?? cards).map((name) => ({ key: name, card: <Face name={name} /> }))}
          stamps={stamps}
        />
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

const card = (name = 'Marek Z.') => screen.getByLabelText(name);

/** The stamps and the cards behind are hidden from assistive technology on purpose; a query about the drawing says so. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;

/** The stage's own animated view is the responder's — the nearest `View` above the card. */
function topCard(name?: string): { readonly props: { readonly style: unknown } } {
  let node = card(name).parent;
  while (node !== null && node.props.onMoveShouldSetResponder === undefined) node = node.parent;
  if (node === null) throw new Error('no stage above the card');
  return node;
}

function styleOf(view: { readonly props: { readonly style: unknown } }): ViewStyle {
  const styles = [view.props.style].flat(3) as (ViewStyle | undefined)[];
  return Object.assign({}, ...styles.filter((entry) => entry !== undefined)) as ViewStyle;
}

function transformOf(): readonly Record<string, unknown>[] {
  return (styleOf(topCard()).transform ?? []) as readonly Record<string, unknown>[];
}

/**
 * Where a card stands in the stack — the nearest view above the face carrying a transform,
 * which is the stage's own wrapper whether the card is the top one or behind it.
 */
function standingOf(name: string): { readonly translateY: number; readonly scale: number } {
  let node = screen.getByLabelText(name, HIDDEN_TOO).parent;
  while (node !== null && styleOf(node).transform === undefined) node = node.parent;
  if (node === null) throw new Error(`no stage above ${name}`);
  const transform = styleOf(node).transform as readonly Record<string, unknown>[];
  const read = (key: string) => Number(transform.find((entry) => key in entry)?.[key]);
  return { translateY: read('translateY'), scale: read('scale') };
}

/** How faint a card is drawn — the opacity on the stage's wrapper above its face. */
function opacityOf(name: string): number {
  let node = screen.getByLabelText(name, HIDDEN_TOO).parent;
  while (node !== null && styleOf(node).transform === undefined) node = node.parent;
  if (node === null) throw new Error(`no stage above ${name}`);
  return Number(styleOf(node).opacity ?? 1);
}

/** An `Animated.Value` renders as itself; what matters is the number it currently holds. */
const valueOf = (transform: Record<string, unknown> | undefined, key: string): unknown =>
  transform?.[key];

const translateX = () => Number(valueOf(transformOf()[0], 'translateX'));

function stampOpacity(said: DeckExit): number {
  const styles = [screen.getByTestId(`deck-stamp-${said}`, HIDDEN_TOO).props.style].flat(3) as (
    { opacity?: unknown } | undefined
  )[];
  return Number(styles.find((entry) => entry?.opacity !== undefined)?.opacity);
}

beforeEach(() => {
  jest.useFakeTimers();
  mounted = [];
});
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

describe('a card that has gone', () => {
  /**
   * The screen hears `onLeft` and clears `leaving` on the spot, and advances the deck a tick
   * later — the held deal notifies on its own schedule. Between the two the same stage is drawn
   * with nothing leaving, and a card put back straight there is the answered card flashing at
   * the centre of the stage for a frame before the next one replaces it. Straight is for a card
   * that **came back**; a card that has gone stays where it went until it is taken away.
   */
  it('stays off the stage when the screen clears `leaving`, rather than snapping back', () => {
    const { onLeft, rerender } = drawStage({ leaving: 'no' });
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    expect(onLeft).toHaveBeenCalledTimes(1);
    const flown = translateX();
    expect(flown).toBeLessThan(0);

    rerender({ leaving: undefined });

    expect(translateX()).toBe(flown);
  });
});

describe('the card behind becoming the top card', () => {
  /**
   * The card under the one that left was on the stage the whole time, and it has to go on
   * being the same drawn thing as it comes forward: a card redrawn from nothing is a photograph
   * decoded again and faded in again, over the person who was plainly there a frame ago.
   */
  it('is the same element, promoted in place, and not one drawn again', () => {
    const { rerender } = drawStage({ cards: ['Marek Z.', 'Ana K.'], leaving: 'yes' });
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    rerender({ leaving: undefined, cards: ['Ana K.'] });

    // Deepest first is the paint order, so Ana mounted before Marek — and only the once.
    expect(mounted).toEqual(['Ana K.', 'Marek Z.']);
    expect(screen.getByLabelText('Ana K.')).toBeTruthy();
    expect(screen.queryByLabelText('Marek Z.', HIDDEN_TOO)).toBeNull();
  });

  /**
   * It was visible behind; it stays visible. Nothing fades in from nothing, because nothing went
   * away: it takes over at the opacity it stood at behind (#553) and brightens as it comes to rest.
   */
  it('brightens from the opacity it stood at behind, and is never faded in from nothing', () => {
    const { rerender } = drawStage({ cards: ['Marek Z.', 'Ana K.'], leaving: 'yes' });
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    expect(opacityOf('Ana K.')).toBeCloseTo(1 - STACK.fade);

    rerender({ leaving: undefined, cards: ['Ana K.'] });
    expect(opacityOf('Ana K.')).toBeCloseTo(1 - STACK.fade);

    act(() => jest.advanceTimersByTime(theme.motion.rise + 50));
    expect(opacityOf('Ana K.')).toBe(1);
  });

  /**
   * The same object coming forward: on the frame it becomes the top card it stands exactly
   * where it stood behind — one step down, one shrink smaller — and the rise brings it to rest.
   * A top card that started from rest would jump a step up and back down as it took over.
   */
  it('comes forward from the place it stood, and comes to rest', () => {
    const { rerender } = drawStage({ cards: ['Marek Z.', 'Ana K.'], leaving: 'yes' });
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    expect(standingOf('Ana K.')).toEqual({ translateY: STACK.step, scale: 1 - STACK.shrink });

    rerender({ leaving: undefined, cards: ['Ana K.'] });
    expect(standingOf('Ana K.')).toEqual({ translateY: STACK.step, scale: 1 - STACK.shrink });

    act(() => jest.advanceTimersByTime(theme.motion.rise + 50));
    expect(standingOf('Ana K.')).toEqual({ translateY: 0, scale: 1 });
  });

  /** The whole stack advances as one motion: the card behind the new top card comes forward too. */
  it('brings the cards behind it forward on the same beat', () => {
    const { rerender } = drawStage({ cards: ['Marek Z.', 'Ana K.', 'Ola W.'], leaving: 'yes' });
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    expect(standingOf('Ola W.').translateY).toBe(2 * STACK.step);

    rerender({ leaving: undefined, cards: ['Ana K.', 'Ola W.'] });
    expect(standingOf('Ola W.').translateY).toBe(2 * STACK.step);

    act(() => jest.advanceTimersByTime(theme.motion.rise + 50));
    expect(standingOf('Ola W.')).toEqual({ translateY: STACK.step, scale: 1 - STACK.shrink });
  });

  /** The new top card takes the drag: the finger lands on the person now under it. */
  it('takes the drag once it is the top card', () => {
    const { onAnswer, rerender } = drawStage({ cards: ['Marek Z.', 'Ana K.'], leaving: 'yes' });
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    rerender({ leaving: undefined, cards: ['Ana K.'] });
    swipe(card('Ana K.'), -commit);

    expect(onAnswer).toHaveBeenCalledWith('no');
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
    drawStage({ cards: ['Marek Z.', 'Ana K.', 'Ola W.'] });

    expect(screen.getByText('Ana K.', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Ola W.', HIDDEN_TOO)).toBeTruthy();
  });

  /** The top card is the one element; a listener does not hear the queue. */
  it('hides them from assistive technology', () => {
    drawStage({ cards: ['Marek Z.', 'Ana K.'] });

    expect(screen.queryByText('Ana K.')).toBeNull();
    let behind = screen.getByText('Ana K.', HIDDEN_TOO).parent;
    while (behind !== null && behind.props.accessibilityElementsHidden === undefined) {
      behind = behind.parent;
    }
    expect(behind?.props.accessibilityElementsHidden).toBe(true);
    expect(behind?.props.importantForAccessibility).toBe('no-hide-descendants');
  });

  /** #553, Q90: the two peeking cards fade as well as shrink — 0,7 and 0,4, the top card whole. */
  it('draws each card behind fainter than the one in front of it', () => {
    drawStage({ cards: ['Marek Z.', 'Ana K.', 'Ola W.'], collapsed: true });

    expect(opacityOf('Marek Z.')).toBe(1);
    expect(opacityOf('Ana K.')).toBeCloseTo(1 - STACK.fade);
    expect(opacityOf('Ola W.')).toBeCloseTo(1 - 2 * STACK.fade);
  });

  it('draws nothing behind when handed nothing', () => {
    drawStage();

    expect(screen.getByLabelText('Marek Z.')).toBeTruthy();
    expect(screen.queryByText('Ana K.', HIDDEN_TOO)).toBeNull();
  });
});

describe('the stamps', () => {
  it('say the answers’ words the deck hands them', () => {
    drawStage();

    expect(screen.getByText("Let's play", HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Not today', HIDDEN_TOO)).toBeTruthy();
  });

  /** #553: a Games yes that charges at once carries its price after the words (Q72). */
  it('draw a figure after the words when one is handed in', () => {
    drawStage({
      stamps: { yes: { words: 'I’m in', figure: '32 zł' }, no: { words: 'Not this time' } },
    });

    const yes = screen.getByTestId('deck-stamp-yes', HIDDEN_TOO);
    expect(within(yes).getByText('I’m in · 32 zł', HIDDEN_TOO)).toBeTruthy();
    const no = screen.getByTestId('deck-stamp-no', HIDDEN_TOO);
    expect(within(no).getByText('Not this time', HIDDEN_TOO)).toBeTruthy();
  });
});
