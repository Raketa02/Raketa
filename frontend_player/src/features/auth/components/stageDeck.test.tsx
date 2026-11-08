/**
 * **Sign-in's dealt deck** ([#786](https://github.com/Raketa02/Raketa/issues/786), PRD #783) —
 * three miniature game cards in the hero, dealt from a stack to the fan when the screen opens.
 *
 * Drawn through `SignInScreen`, the hero as sign-in draws it, under the reduced-motion provider's
 * `value` override and with the clock driven by `act(advanceTimersByTime)` — the yes screen's
 * entrance suite's way. **Where a card sits is read off its transform**, the one fact about the
 * deal a query can see; how it looks is a device look.
 *
 * The hero is hidden from screen readers (ADR-0198), so every query that looks at the deck opts
 * into hidden elements; the ones that do not are the proof that a listener never meets it.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react-native';
import { StyleSheet, type ViewStyle } from 'react-native';

import { ReducedMotionProvider, theme } from '@/shared/ui';
import { hearAScreenReader, stopHearingAScreenReader } from '@/test-support/screenReader';

import { SignInScreen } from './SignInScreen';
import { DEALT, FAN_BOX, STACKED, type DeckPlace } from './stageDeckGeometry';

const HIDDEN_TOO = { includeHiddenElements: true } as const;

/** Past the whole deal — the stack held, then the slide. */
const PAST_THE_DEAL = theme.motion.stageDeck.stacked + theme.motion.stageDeck.deal + 100;

function drawSignIn({ reduced = false } = {}) {
  render(
    <ReducedMotionProvider value={reduced}>
      <QueryClientProvider client={new QueryClient()}>
        <SignInScreen />
      </QueryClientProvider>
    </ReducedMotionProvider>,
  );
}

const cardAt = (place: DeckPlace) => screen.getByTestId(`stage-card-${place}`, HIDDEN_TOO);

/** A view's style, flattened, and how to read one entry of its transform. */
function styleOf(view: { readonly props: { readonly style?: unknown } }) {
  const style = StyleSheet.flatten(view.props.style as ViewStyle);
  const transform = (style.transform ?? []) as readonly Record<string, unknown>[];
  return { style, read: (key: string) => transform.find((entry) => key in entry)?.[key] };
}

/** What the card at `place` holds, as words — drawn, and hidden from a listener. */
const wordsOn = (place: DeckPlace) => within(cardAt(place));

/** Where the card at `place` stands now — its transform, read as a placement. */
function placementOf(place: DeckPlace) {
  const { read } = styleOf(cardAt(place));
  return {
    x: Number(read('translateX')),
    y: Number(read('translateY')),
    turn: Number.parseFloat(String(read('rotate'))),
  };
}

const placements = () => ({
  left: placementOf('left'),
  front: placementOf('front'),
  right: placementOf('right'),
});

const ALL_STACKED = { left: STACKED, front: STACKED, right: STACKED };

beforeEach(() => jest.useFakeTimers());
afterEach(() => {
  // The hero loops (#787): take the screen down on the fake clock, before the real one is back.
  cleanup();
  jest.useRealTimers();
  jest.restoreAllMocks();
  stopHearingAScreenReader();
});

describe('the three cards, per mock 2', () => {
  it('draws the front card: a padel game waiting for a fourth, with You completing it', () => {
    drawSignIn();
    const front = wordsOn('front');

    for (const words of [
      'Seat open',
      '21 h 00',
      'karol.t',
      '2,75 · paid',
      'ania.k',
      '2,68 · paid',
      'kuba.w',
      '2,80 · paid',
      'You complete it',
      '91%',
      'karol.t + You',
      'ania.k + kuba.w',
      'Sat 16:00 · Ogrody 33',
      '27 zł',
    ]) {
      expect(front.getByText(words, HIDDEN_TOO)).toBeTruthy();
    }
  });

  it('draws the left card: a tennis single, Picked for you', () => {
    drawSignIn();
    const left = wordsOn('left');

    for (const words of ['Picked for you', '3,15', '74%', 'Thu 19:00 · Ogrody 33']) {
      expect(left.getByText(words, HIDDEN_TOO)).toBeTruthy();
    }
    // On his tile, and as the other side of the forecast — a single is one against one.
    expect(left.getAllByText('marek.z', HIDDEN_TOO)).toHaveLength(2);
  });

  it('draws the right card: a squash Fill in with one empty seat', () => {
    drawSignIn();
    const right = wordsOn('right');

    for (const words of ['Fill in · seat open', '2 h', 'stas.w + ola.m', '30 zł']) {
      expect(right.getByText(words, HIDDEN_TOO)).toBeTruthy();
    }
    expect(right.getAllByTestId('stage-seat-empty', HIDDEN_TOO)).toHaveLength(1);
  });

  /** ADR-0198: the form is the screen; a listener never meets the picture above it. */
  it('is hidden from a screen reader', () => {
    drawSignIn();

    expect(screen.queryByTestId('stage-card-front')).toBeNull();
    expect(screen.queryByText('karol.t')).toBeNull();
    expect(screen.queryByText('Seat open')).toBeNull();
  });
});

describe('the deal', () => {
  it('opens with the three cards stacked exactly on top of each other', () => {
    drawSignIn();

    expect(placements()).toEqual(ALL_STACKED);

    act(() => jest.advanceTimersByTime(theme.motion.stageDeck.stacked - 1));
    expect(placements()).toEqual(ALL_STACKED);
  });

  it('slides the two back cards out to their turned places, and the front card stays put', () => {
    drawSignIn();

    act(() => jest.advanceTimersByTime(theme.motion.stageDeck.stacked + 1));
    act(() => jest.advanceTimersByTime(theme.motion.stageDeck.deal / 2));
    const midway = placements();
    expect(midway.front).toEqual(STACKED);
    expect(midway.left.x).toBeLessThan(0);
    expect(midway.left.x).toBeGreaterThan(DEALT.left.x);

    act(() => jest.advanceTimersByTime(PAST_THE_DEAL));
    expect(placements()).toEqual(DEALT);
  });

  /** What follows the still moment is the loop's (#787, `stageLoop.test.tsx`). */
  it('holds the dealt fan still until the front card is picked up', () => {
    drawSignIn();

    act(() => jest.advanceTimersByTime(PAST_THE_DEAL));
    act(() => jest.advanceTimersByTime(theme.motion.stageDeck.still - 200));

    expect(placements()).toEqual(DEALT);
  });
});

/**
 * The app's collapsed-presentation rule: either reduced motion or a running screen reader, and
 * under it the picture is its end state.
 */
describe('under collapsed presentation', () => {
  it('deals the cards from the first frame under reduced motion, and nothing moves', () => {
    drawSignIn({ reduced: true });

    expect(placements()).toEqual(DEALT);

    act(() => jest.advanceTimersByTime(theme.motion.stageDeck.stacked));
    expect(placements()).toEqual(DEALT);
    act(() => jest.advanceTimersByTime(PAST_THE_DEAL));
    expect(placements()).toEqual(DEALT);
  });

  it('deals the cards at once with a screen reader running, and nothing moves', async () => {
    hearAScreenReader();
    drawSignIn();

    // The OS answers a promise; let it land.
    await act(async () => {
      await Promise.resolve();
    });

    expect(placements()).toEqual(DEALT);
    act(() => jest.advanceTimersByTime(PAST_THE_DEAL));
    expect(placements()).toEqual(DEALT);
  });
});

describe('the fit', () => {
  const deck = () => screen.getByTestId('stage-deck', HIDDEN_TOO);
  const plate = () => screen.getByTestId('stage-deck-plate', HIDDEN_TOO);

  /** The room, laid out — after the OS's answers about motion and screen readers have landed. */
  async function measure(width: number, height: number) {
    await act(async () => {
      await Promise.resolve();
    });
    fireEvent(deck(), 'layout', { nativeEvent: { layout: { x: 0, y: 0, width, height } } });
  }

  function plateStyle() {
    const { style, read } = styleOf(plate());
    return { opacity: style.opacity, scale: Number(read('scale')) };
  }

  it('draws nothing until it knows its room', async () => {
    drawSignIn();

    expect(plateStyle().opacity).toBe(0);

    await measure(342, 184);
    expect(plateStyle().opacity).toBe(1);
  });

  /**
   * A 320pt phone with the headline at the text cap's three lines leaves the deck a strip; the fan
   * scales down into it rather than running over the wordmark or the headline.
   */
  it.each([
    { width: 342, height: 184 },
    { width: 272, height: 60 },
  ])('scales the whole fan into a $width × $height room', async ({ width, height }) => {
    drawSignIn();

    await measure(width, height);

    const box = FAN_BOX;
    const { scale } = plateStyle();
    expect(scale).toBeGreaterThan(0);
    expect(box.width * scale).toBeLessThanOrEqual(width + 1e-6);
    expect(box.height * scale).toBeLessThanOrEqual(height + 1e-6);
  });
});
