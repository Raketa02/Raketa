/**
 * **Sign-in's hero loop** ([#787](https://github.com/Rakieta02/Rakieta/issues/787), PRD #783) — after
 * #786's deal, the front card is picked up with **I'M IN** on it, swiped off to the right, and the
 * hero becomes *It's a game!* until the cards are dealt again.
 *
 * Drawn through `SignInScreen` under the reduced-motion provider's `value` override, with the clock
 * driven by `act(advanceTimersByTime)` — #786's way. **What a person sees is read off the drawing**:
 * a card's transform and opacity, the stamp's opacity, the splash's and its word's. The router-harness
 * case at the foot walks the loop through the real route tree, where sign-up covers sign-in.
 *
 * The hero is hidden from screen readers (ADR-0198), so every query that looks at it opts into
 * hidden elements.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react-native';
import { renderRouter, screen as routed } from 'expo-router/testing-library';
import { StyleSheet, type ViewStyle } from 'react-native';

import {
  clearStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { ReducedMotionProvider, theme } from '@/shared/ui';
import { moveAppTo, stopWatchingAppState, watchAppState } from '@/test-support/appState';
import { ONBOARDING_ROUTES, stubGate } from '@/test-support/onboardingRouter';
import { hearAScreenReader, stopHearingAScreenReader } from '@/test-support/screenReader';
import { errorResponse, installTransport, type Transport } from '@/test-support/transport';

import { refreshTokens } from '../use-cases/refreshTokens';

import { EMAIL_LABEL, PASSWORD_LABEL, SIGN_IN_COPY, SIGN_UP_COPY } from './authPresentation';
import { SignInScreen } from './SignInScreen';
import { DEALT, STACKED, type DeckPlace } from './stageDeckGeometry';

const HIDDEN_TOO = { includeHiddenElements: true } as const;

const BEAT = theme.motion.stageDeck;
const ENTRANCE = theme.motion.yesEntrance;

/** The moments of one cycle, from the cycle's start — see `motion.stageDeck`. */
const DEALT_AT = BEAT.stacked + BEAT.deal;
const PICK_UP_AT = DEALT_AT + BEAT.still;
const PICKED_AT = PICK_UP_AT + BEAT.pickUp;
const GONE_AT = PICKED_AT + BEAT.swipe;
const WORD_LANDED_AT = GONE_AT + ENTRANCE.wordAfter + ENTRANCE.word;
const SPLASH_FADES_AT = GONE_AT + BEAT.splash;
const CYCLE = SPLASH_FADES_AT + BEAT.reset;

/**
 * A margin past a moment. Every timed move starts on the frame after the one before it ended, so a
 * cycle runs a frame or so late per move; this covers a cycle's worth.
 */
const SETTLE = 150;

// --- reading the drawing ------------------------------------------------------------------

type Tree = typeof screen | typeof routed;

/** A view's style, flattened, and one entry of its transform. */
function styleOf(view: { readonly props: { readonly style?: unknown } }) {
  const style = StyleSheet.flatten(view.props.style as ViewStyle);
  const transform = (style.transform ?? []) as readonly Record<string, unknown>[];
  return { style, read: (key: string) => transform.find((entry) => key in entry)?.[key] };
}

/** Where the card at `place` stands now, and how much of it shows. */
function cardOf(place: DeckPlace, tree: Tree = screen) {
  const { style, read } = styleOf(tree.getByTestId(`stage-card-${place}`, HIDDEN_TOO));
  return {
    x: Number(read('translateX')),
    y: Number(read('translateY')),
    turn: Number.parseFloat(String(read('rotate'))),
    opacity: Number(style.opacity ?? 1),
  };
}

/** The three cards' places, as `DEALT` and `STACKED` spell them. */
function placements(tree: Tree = screen) {
  const at = (place: DeckPlace) => {
    const { x, y, turn } = cardOf(place, tree);
    return { x, y, turn };
  };
  return { left: at('left'), front: at('front'), right: at('right') };
}

const ALL_STACKED = { left: STACKED, front: STACKED, right: STACKED };

const opacityOf = (testID: string, tree: Tree = screen) =>
  Number(styleOf(tree.getByTestId(testID, HIDDEN_TOO)).style.opacity);

const stampShows = (tree: Tree = screen) => opacityOf('stage-stamp', tree);

/** How much of the splash shows — nought when it is not drawn at all. */
function splashShows(tree: Tree = screen): number {
  return tree.queryByTestId('stage-splash', HIDDEN_TOO) === null
    ? 0
    : opacityOf('stage-splash', tree);
}

// --- the clock, from the loop's start -----------------------------------------------------

let elapsed = 0;

/** The loop starts again now — from the deal — and the clock is read from here. */
function loopStartsNow() {
  elapsed = 0;
}

/** Move the clock to `ms` after the loop's start. */
function clockTo(ms: number) {
  const step = ms - elapsed;
  if (step < 0) throw new Error(`the clock is already at ${elapsed}`);
  act(() => jest.advanceTimersByTime(step));
  elapsed = ms;
}

function drawSignIn({ reduced = false, client = new QueryClient() } = {}) {
  render(
    <ReducedMotionProvider value={reduced}>
      <QueryClientProvider client={client}>
        <SignInScreen />
      </QueryClientProvider>
    </ReducedMotionProvider>,
  );
  loopStartsNow();
}

beforeEach(() => watchAppState());
afterEach(() => {
  // The loop never ends: take the screen down on the fake clock, before the real one is back.
  cleanup();
  jest.useRealTimers();
  stopWatchingAppState();
  stopHearingAScreenReader();
});

describe('one cycle, drawn on its own', () => {
  beforeEach(() => jest.useFakeTimers());

  it('holds the dealt fan still for a moment, so the cards can be read', () => {
    drawSignIn();

    clockTo(PICK_UP_AT - SETTLE);

    expect(placements()).toEqual(DEALT);
    expect(stampShows()).toBe(0);
    expect(splashShows()).toBe(0);
  });

  it('picks the front card up — a little right, a few degrees — with I’M IN on it', () => {
    drawSignIn();

    // The swipe follows the pick-up at once, slow at first, so the card is read at the moment it is
    // up — within a point and a degree of where the pick-up puts it, and the stamp within the last
    // frame of its coming up: frames are a screen's 16 ms apart (`test-support/animationFrames`).
    clockTo(PICKED_AT);

    const front = cardOf('front');
    expect(Math.abs(front.x - theme.size.stage.swipe.across)).toBeLessThan(1);
    expect(Math.abs(front.turn - theme.size.stage.swipe.turn)).toBeLessThan(1);
    expect(front.opacity).toBe(1);
    expect(stampShows()).toBeCloseTo(1, 3);
    // The stamp is the deck's words, uppercased by its style, and carries no price.
    const stamp = within(screen.getByTestId('stage-stamp', HIDDEN_TOO));
    expect(stamp.getByText('I’m in', HIDDEN_TOO)).toBeTruthy();
    expect(stamp.queryByText(/zł/, HIDDEN_TOO)).toBeNull();
    // The back cards stay where they were dealt.
    expect(placements().left).toEqual(DEALT.left);
    expect(placements().right).toEqual(DEALT.right);
  });

  it('swipes it off past the right edge, turning further and fading, while the rest stays', () => {
    drawSignIn();

    clockTo(GONE_AT - BEAT.swipe / 2);
    const midway = cardOf('front');
    expect(midway.x).toBeGreaterThan(theme.size.stage.swipe.across);
    expect(midway.opacity).toBe(1);

    clockTo(GONE_AT + SETTLE / 2);
    const gone = cardOf('front');
    expect(gone.turn).toBe(theme.size.stage.swipe.outTurn);
    expect(gone.opacity).toBe(0);
    expect(placements().left).toEqual(DEALT.left);
    expect(placements().right).toEqual(DEALT.right);
    expect(screen.getByText(SIGN_IN_COPY.headline, HIDDEN_TOO)).toBeTruthy();
  });

  it('becomes It’s a game! the moment the card is gone, the word rising last, and goes at the reset', () => {
    drawSignIn();

    clockTo(GONE_AT - SETTLE);
    expect(splashShows()).toBe(0);

    // The night first, the word still on its way…
    clockTo(GONE_AT + ENTRANCE.wordAfter);
    expect(opacityOf('stage-splash-word')).toBe(0);

    // …and landed.
    clockTo(WORD_LANDED_AT + SETTLE);
    expect(splashShows()).toBe(1);
    expect(opacityOf('stage-splash-word')).toBe(1);

    clockTo(SPLASH_FADES_AT - SETTLE);
    expect(splashShows()).toBe(1);

    clockTo(CYCLE + SETTLE);
    expect(splashShows()).toBe(0);
  });

  it('restacks the cards under the night and deals them afresh, then plays the next cycle', () => {
    drawSignIn();

    clockTo(CYCLE + SETTLE);
    // Silently: the splash has gone, and the three are stacked again, the front card back.
    expect(placements()).toEqual(ALL_STACKED);
    expect(cardOf('front').opacity).toBe(1);
    expect(stampShows()).toBe(0);

    clockTo(CYCLE + DEALT_AT + SETTLE);
    expect(placements()).toEqual(DEALT);

    clockTo(CYCLE + WORD_LANDED_AT + 2 * SETTLE);
    expect(splashShows()).toBe(1);
    expect(opacityOf('stage-splash-word')).toBe(1);

    clockTo(2 * CYCLE + 2 * SETTLE);
    expect(splashShows()).toBe(0);
  });
});

describe('the splash, per mocks 7–8', () => {
  beforeEach(() => jest.useFakeTimers());

  it('faces karol.t and You against ania.k and kuba.w, You with no letters', () => {
    drawSignIn();
    clockTo(WORD_LANDED_AT + SETTLE);
    const splash = within(screen.getByTestId('stage-splash', HIDDEN_TOO));

    for (const letters of ['KT', 'AK', 'KW']) {
      expect(splash.getByText(letters, HIDDEN_TOO)).toBeTruthy();
    }
    // You is the court illustration and nothing over it: no TK, no letters of any kind.
    expect(splash.queryByText('TK', HIDDEN_TOO)).toBeNull();
    const you = within(splash.getByTestId('stage-splash-you', HIDDEN_TOO));
    expect(you.queryAllByText(/./, HIDDEN_TOO)).toHaveLength(0);
    expect(splash.getByText('vs', HIDDEN_TOO)).toBeTruthy();
  });

  it('says It’s a game! over the booked court, with no buttons', () => {
    drawSignIn();
    clockTo(WORD_LANDED_AT + SETTLE);
    const word = within(screen.getByTestId('stage-splash-word', HIDDEN_TOO));

    expect(word.getByText('It’s a game!', HIDDEN_TOO)).toBeTruthy();
    expect(
      word.getByText('Saturday 16:00 · Ogrody 33 · Court 6 · 27 zł each', HIDDEN_TOO),
    ).toBeTruthy();
    expect(
      within(screen.getByTestId('stage-splash', HIDDEN_TOO)).queryAllByRole('button', HIDDEN_TOO),
    ).toHaveLength(0);
  });

  it('covers the hero only: the wordmark stays, and nothing of it reaches a listener', () => {
    drawSignIn();
    clockTo(WORD_LANDED_AT + SETTLE);

    expect(screen.getByText('Rakieta', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByRole('header', { name: SIGN_IN_COPY.title })).toBeTruthy();
    expect(screen.queryByText('It’s a game!')).toBeNull();
  });
});

/** The app's collapsed-presentation rule: either reduced motion or a running screen reader. */
describe('under collapsed presentation', () => {
  beforeEach(() => jest.useFakeTimers());

  it('never runs under reduced motion: dealt and still, past several cycles, and no splash', () => {
    drawSignIn({ reduced: true });

    for (let cycle = 1; cycle <= 3; cycle += 1) {
      clockTo(cycle * CYCLE - CYCLE / 2);
      expect(placements()).toEqual(DEALT);
      expect(cardOf('front').opacity).toBe(1);
      expect(splashShows()).toBe(0);
    }
  });

  it('never runs with a screen reader: dealt and still, past several cycles, and no splash', async () => {
    hearAScreenReader();
    drawSignIn();
    await act(async () => {
      await Promise.resolve();
    });

    for (const at of [WORD_LANDED_AT + SETTLE, CYCLE + WORD_LANDED_AT, 3 * CYCLE]) {
      clockTo(at);
      expect(placements()).toEqual(DEALT);
      expect(splashShows()).toBe(0);
      expect(stampShows()).toBe(0);
    }
  });
});

describe('the app leaving', () => {
  beforeEach(() => jest.useFakeTimers());

  it('stops while the app is in the background, and starts again from the deal on its return', () => {
    drawSignIn();
    clockTo(PICK_UP_AT + BEAT.pickUp / 2);
    act(() => moveAppTo('background'));
    const away = { ...placements(), front: cardOf('front'), splash: splashShows() };

    clockTo(PICK_UP_AT + BEAT.pickUp / 2 + 2 * CYCLE);
    expect({ ...placements(), front: cardOf('front'), splash: splashShows() }).toEqual(away);

    act(() => moveAppTo('active'));
    loopStartsNow();
    expect(placements()).toEqual(ALL_STACKED);
    expect(splashShows()).toBe(0);

    clockTo(DEALT_AT + SETTLE);
    expect(placements()).toEqual(DEALT);
  });

  /** iOS's `inactive` is Face ID behind the keychain's autofill, among others: still in view. */
  it('keeps running through iOS’s inactive, so autofilling the form never resets it', () => {
    drawSignIn();
    clockTo(PICK_UP_AT);
    act(() => moveAppTo('inactive'));
    clockTo(PICK_UP_AT + BEAT.pickUp / 2);
    act(() => moveAppTo('active'));

    clockTo(WORD_LANDED_AT + SETTLE);
    expect(splashShows()).toBe(1);
  });
});

describe('the form beside it', () => {
  let transport: Transport;

  beforeEach(async () => {
    jest.useFakeTimers();
    transport = installTransport();
    resetSessionStatus();
    wireHttpCredentials(refreshTokens);
    await clearStoredTokens();
    queryClient.clear();
    setSessionStatus('unauthenticated');
  });

  afterEach(async () => {
    transport.restore();
    queryClient.clear();
    resetSessionStatus();
    await clearStoredTokens();
  });

  it('keeps time while somebody types: the splash comes at its moment', () => {
    drawSignIn({ client: queryClient });

    clockTo(DEALT_AT + SETTLE);
    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'tomek.k@gmail.com');
    clockTo(PICK_UP_AT);
    fireEvent.changeText(screen.getByLabelText(PASSWORD_LABEL), 'backhand42');

    clockTo(GONE_AT - SETTLE);
    expect(splashShows()).toBe(0);
    clockTo(WORD_LANDED_AT + SETTLE);
    expect(splashShows()).toBe(1);
  });

  it('keeps running beside a refused sign-in', async () => {
    transport.on('POST', '/api/v1/auth/login', () => errorResponse(401, 'invalid_credentials'));
    drawSignIn({ client: queryClient });

    clockTo(DEALT_AT + SETTLE);
    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'tomek.k@gmail.com');
    fireEvent.changeText(screen.getByLabelText(PASSWORD_LABEL), 'wrong');
    fireEvent.press(screen.getByLabelText(SIGN_IN_COPY.submit));
    expect(await screen.findByText("That email and password don't match. Try again.")).toBeTruthy();

    // Wherever in the cycle the refusal landed, a whole cycle on shows the splash.
    let shown = false;
    for (let step = 0; step < CYCLE + SETTLE; step += 100) {
      act(() => jest.advanceTimersByTime(100));
      if (splashShows() === 1) shown = true;
    }
    expect(shown).toBe(true);
  });
});

/**
 * **Through the real route tree**: sign-up pushed over sign-in covers it, and the loop holds; back
 * on sign-in it starts again from the deal. The harness runs the pending timers on every navigation
 * (`renderRouter`), so what is compared is the drawing once each move has settled.
 */
describe('in the route tree', () => {
  let transport: Transport;

  beforeEach(async () => {
    transport = installTransport();
    resetSessionStatus();
    wireHttpCredentials(refreshTokens);
    await clearStoredTokens();
    queryClient.clear();
    setSessionStatus('unauthenticated');
  });

  afterEach(async () => {
    transport.restore();
    queryClient.clear();
    resetSessionStatus();
    await clearStoredTokens();
  });

  const snapshot = () => ({
    ...placements(routed),
    front: cardOf('front', routed),
    splash: splashShows(routed),
  });

  it('holds while sign-up covers sign-in, and starts from the deal on the way back', async () => {
    stubGate(transport, { hasPlayerProfile: true });
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/sign-in' });
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));

    act(() => jest.advanceTimersByTime(PICK_UP_AT + BEAT.pickUp / 2));

    fireEvent.press(routed.getByLabelText(SIGN_IN_COPY.createAccount));
    await waitFor(() => expect(routed).toHavePathname('/sign-up'));
    const covered = snapshot();

    act(() => jest.advanceTimersByTime(2 * CYCLE));
    expect(snapshot()).toEqual(covered);

    fireEvent.press(routed.getByRole('link', { name: SIGN_UP_COPY.signIn }));
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));
    expect(placements(routed)).toEqual(ALL_STACKED);
    expect(splashShows(routed)).toBe(0);

    act(() => jest.advanceTimersByTime(DEALT_AT + SETTLE));
    expect(placements(routed)).toEqual(DEALT);
  });
});
