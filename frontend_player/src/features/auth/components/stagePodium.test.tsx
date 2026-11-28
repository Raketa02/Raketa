/**
 * **Sign-up's podium** ([#788](https://github.com/Rakieta02/Rakieta/issues/788), PRD #783) — the
 * Rankings podium in the hero, with You on the first step, rising once when the screen opens.
 *
 * Drawn through `SignUpScreen` under the reduced-motion provider's `value` override, with the clock
 * driven by `act(advanceTimersByTime)` — the deck's way (`stageDeck.test.tsx`). **What a person sees
 * is read off the drawing**: how far a step has risen is its transform against its height, and
 * whether a player is there is their opacity and their transform. How it looks is a device look.
 * The router-harness case at the foot opens sign-up twice through the real route tree.
 *
 * The hero is hidden from screen readers (ADR-0198), so every query that looks at the podium opts
 * into hidden elements; the ones that do not are the proof that a listener never meets it.
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
import { ONBOARDING_ROUTES, stubGate } from '@/test-support/onboardingRouter';
import { hearAScreenReader, stopHearingAScreenReader } from '@/test-support/screenReader';
import { installTransport, type Transport } from '@/test-support/transport';

import { refreshTokens } from '../use-cases/refreshTokens';

import { SIGN_IN_COPY, SIGN_UP_COPY } from './authPresentation';
import { SignUpScreen } from './SignUpScreen';
import { PODIUM_BOX, PODIUM_PLACES, type PodiumPlace } from './stagePodiumGeometry';

const HIDDEN_TOO = { includeHiddenElements: true } as const;

const BEAT = theme.motion.stagePodium;
const PODIUM = theme.size.stage.podium;

/** The moments of the rise, from the screen's opening — see `motion.stagePodium`. */
const THIRD_STARTS = BEAT.empty;
const SECOND_STARTS = THIRD_STARTS + BEAT.stagger;
const FIRST_STARTS = SECOND_STARTS + BEAT.stagger;
/** When a step has settled and its player starts to arrive. */
const SETTLES = {
  third: THIRD_STARTS + BEAT.step,
  second: SECOND_STARTS + BEAT.step,
  first: FIRST_STARTS + BEAT.step,
} as const satisfies Readonly<Record<PodiumPlace, number>>;
const RISEN = SETTLES.first + BEAT.player;

/**
 * A margin past a moment. Every timed move starts on the frame after the one before it ended, so a
 * sequence runs a frame or so late per move; this covers the rise's.
 */
const SETTLE = 100;

// --- reading the drawing ------------------------------------------------------------------

type Tree = typeof screen | typeof routed;

/** A view's style, flattened, and one entry of its transform. */
function styleOf(view: { readonly props: { readonly style?: unknown } }) {
  const style = StyleSheet.flatten(view.props.style as ViewStyle);
  const transform = (style.transform ?? []) as readonly Record<string, unknown>[];
  return { style, read: (key: string) => transform.find((entry) => key in entry)?.[key] };
}

/** How far the step at `place` has risen: nought flat against the baseline, one at its height. */
function stepRisen(place: PodiumPlace, tree: Tree = screen): number {
  const { read } = styleOf(tree.getByTestId(`stage-podium-step-${place}`, HIDDEN_TOO));
  return 1 - Number(read('translateY')) / PODIUM.step[place];
}

/** Whether the player at `place` is there: how much of them shows, and how far below they are. */
function playerOn(place: PodiumPlace, tree: Tree = screen) {
  const { style, read } = styleOf(tree.getByTestId(`stage-podium-player-${place}`, HIDDEN_TOO));
  return { shows: Number(style.opacity), below: Number(read('translateY')) };
}

/** The whole podium, as a person sees it now. */
function podium(tree: Tree = screen) {
  const at = (place: PodiumPlace) => ({
    step: stepRisen(place, tree),
    player: playerOn(place, tree),
  });
  return { first: at('first'), second: at('second'), third: at('third') };
}

const EMPTY_STAGE = { step: 0, player: { shows: 0, below: theme.space.md } };
const STANDING = { step: 1, player: { shows: 1, below: 0 } };
const ALL_EMPTY = { first: EMPTY_STAGE, second: EMPTY_STAGE, third: EMPTY_STAGE };
const ALL_STANDING = { first: STANDING, second: STANDING, third: STANDING };

// --- the clock, from the screen's opening -------------------------------------------------

let elapsed = 0;

/** Move the clock to `ms` after the screen opened. */
function clockTo(ms: number) {
  const step = ms - elapsed;
  if (step < 0) throw new Error(`the clock is already at ${elapsed}`);
  act(() => jest.advanceTimersByTime(step));
  elapsed = ms;
}

function drawSignUp({ reduced = false } = {}) {
  render(
    <ReducedMotionProvider value={reduced}>
      <QueryClientProvider client={new QueryClient()}>
        <SignUpScreen />
      </QueryClientProvider>
    </ReducedMotionProvider>,
  );
  elapsed = 0;
}

afterEach(() => {
  cleanup();
  jest.useRealTimers();
  stopHearingAScreenReader();
});

describe('the podium, per mock 5', () => {
  beforeEach(() => jest.useFakeTimers());

  const column = (place: PodiumPlace) =>
    within(screen.getByTestId(`stage-podium-${place}`, HIDDEN_TOO));

  it('stands three steps in 2 / 1 / 3 order, numbered so', () => {
    drawSignUp();

    const plate = screen.getByTestId('stage-podium-plate', HIDDEN_TOO);
    const columns = within(plate)
      .getAllByTestId(/^stage-podium-(first|second|third)$/, HIDDEN_TOO)
      .map((view) => view.props.testID as string);
    expect(columns).toEqual(['stage-podium-second', 'stage-podium-first', 'stage-podium-third']);

    expect(column('second').getByText('2', HIDDEN_TOO)).toBeTruthy();
    expect(column('first').getByText('1', HIDDEN_TOO)).toBeTruthy();
    expect(column('third').getByText('3', HIDDEN_TOO)).toBeTruthy();
  });

  it('makes the middle step the tallest and volt, and the outer two translucent white', () => {
    drawSignUp();

    const step = (place: PodiumPlace) =>
      styleOf(screen.getByTestId(`stage-podium-step-${place}`, HIDDEN_TOO)).style;
    expect(step('first').height).toBeGreaterThan(Number(step('second').height));
    expect(step('second').height).toBeGreaterThan(Number(step('third').height));

    expect(step('first').backgroundColor).toBe(theme.color.volt);
    expect(step('second').backgroundColor).toBe(theme.color.stageStep);
    expect(step('third').backgroundColor).toBe(theme.color.stageStep);
  });

  it('stands stas.w (SW) on 2, ines.d (ID) on 3, and You (TK) on 1', () => {
    drawSignUp();

    for (const [place, name, letters] of [
      ['second', 'stas.w', 'SW'],
      ['third', 'ines.d', 'ID'],
      ['first', 'You', 'TK'],
    ] as const) {
      const on = within(screen.getByTestId(`stage-podium-player-${place}`, HIDDEN_TOO));
      expect(on.getByText(name, HIDDEN_TOO)).toBeTruthy();
      expect(on.getByText(letters, HIDDEN_TOO)).toBeTruthy();
    }
  });

  it('draws You larger, ringed in volt, and the other two rimmed', () => {
    drawSignUp();

    const face = (place: PodiumPlace) =>
      styleOf(screen.getByTestId(`stage-podium-face-${place}`, HIDDEN_TOO)).style;
    expect(face('first').width).toBeGreaterThan(Number(face('second').width));
    expect(face('first').width).toBeGreaterThan(Number(face('third').width));

    expect(face('first')).toMatchObject({
      borderColor: theme.color.volt,
      borderWidth: PODIUM.ring,
    });
    for (const place of ['second', 'third'] as const) {
      expect(face(place)).toMatchObject({
        borderColor: theme.color.stageRim,
        borderWidth: PODIUM.rim,
      });
    }
  });

  it('keeps the headline under it', () => {
    drawSignUp();

    expect(screen.getByText(SIGN_UP_COPY.headline, HIDDEN_TOO)).toBeTruthy();
  });

  it('caps its words as the hero’s are capped', () => {
    drawSignUp();

    for (const words of ['stas.w', 'You', 'TK', '1']) {
      expect(screen.getByText(words, HIDDEN_TOO).props.maxFontSizeMultiplier).toBe(
        theme.size.stage.textMaxScale,
      );
    }
  });

  /** ADR-0198: the form is the screen; a listener never meets the picture above it. */
  it('is hidden from a screen reader', () => {
    drawSignUp();

    expect(screen.queryByTestId('stage-podium')).toBeNull();
    expect(screen.queryByText('stas.w')).toBeNull();
    expect(screen.queryByText('TK')).toBeNull();
  });
});

describe('the rise, played once', () => {
  beforeEach(() => jest.useFakeTimers());

  it('opens on an empty stage: the steps flat and nobody on them', () => {
    drawSignUp();

    expect(podium()).toEqual(ALL_EMPTY);

    clockTo(THIRD_STARTS - 1);
    expect(podium()).toEqual(ALL_EMPTY);
  });

  it('raises the third step, then the second, then the first', () => {
    drawSignUp();

    clockTo(THIRD_STARTS + BEAT.stagger / 2);
    expect(stepRisen('third')).toBeGreaterThan(0);
    expect(stepRisen('second')).toBe(0);
    expect(stepRisen('first')).toBe(0);

    clockTo(SECOND_STARTS + BEAT.stagger / 2);
    expect(stepRisen('second')).toBeGreaterThan(0);
    expect(stepRisen('second')).toBeLessThan(stepRisen('third'));
    expect(stepRisen('first')).toBe(0);

    clockTo(FIRST_STARTS + BEAT.step / 2);
    expect(stepRisen('first')).toBeGreaterThan(0);
    expect(stepRisen('first')).toBeLessThan(1);
  });

  /** `easeDecel`: a quick start and a soft landing — more than half the way up in half the time. */
  it('gives each step a quick start and a soft landing', () => {
    drawSignUp();

    clockTo(THIRD_STARTS + BEAT.step / 2);
    expect(stepRisen('third')).toBeGreaterThan(0.75);
    expect(stepRisen('third')).toBeLessThan(1);
  });

  it('lands each player as their step settles: ines.d, then stas.w, then You', () => {
    drawSignUp();

    // Nobody arrives before their step has risen.
    clockTo(SETTLES.third - SETTLE);
    expect(playerOn('third').shows).toBe(0);

    clockTo(SETTLES.third + BEAT.player / 2);
    expect(stepRisen('third')).toBe(1);
    const arriving = playerOn('third');
    expect(arriving.shows).toBeGreaterThan(0);
    expect(arriving.below).toBeGreaterThan(0);
    expect(playerOn('second').shows).toBe(0);
    expect(playerOn('first').shows).toBe(0);

    clockTo(SETTLES.second + BEAT.player / 2);
    expect(playerOn('third')).toEqual(STANDING.player);
    expect(playerOn('second').shows).toBeGreaterThan(0);
    expect(playerOn('first').shows).toBe(0);

    clockTo(SETTLES.first + BEAT.player / 2);
    expect(playerOn('second')).toEqual(STANDING.player);
    expect(playerOn('first').shows).toBeGreaterThan(0);
  });

  it('stands risen, with all three players, about a second and a half in', () => {
    drawSignUp();

    expect(RISEN).toBe(1500);
    clockTo(RISEN + SETTLE);
    expect(podium()).toEqual(ALL_STANDING);
  });

  it('then holds: nothing changes, however long the clock runs', () => {
    drawSignUp();

    clockTo(RISEN + SETTLE);
    const risen = podium();

    clockTo(RISEN + 60_000);
    expect(podium()).toEqual(risen);
    clockTo(RISEN + 600_000);
    expect(podium()).toEqual(risen);
  });
});

/**
 * The app's collapsed-presentation rule: either reduced motion or a running screen reader, and
 * under it the picture is its end state.
 */
describe('under collapsed presentation', () => {
  beforeEach(() => jest.useFakeTimers());

  it('stands risen with its players from the first frame under reduced motion', () => {
    drawSignUp({ reduced: true });

    expect(podium()).toEqual(ALL_STANDING);

    clockTo(RISEN + SETTLE);
    expect(podium()).toEqual(ALL_STANDING);
  });

  it('stands risen with its players at once with a screen reader running', async () => {
    hearAScreenReader();
    drawSignUp();

    // The OS answers a promise; let it land.
    await act(async () => {
      await Promise.resolve();
    });

    expect(podium()).toEqual(ALL_STANDING);
    clockTo(RISEN + SETTLE);
    expect(podium()).toEqual(ALL_STANDING);
  });
});

describe('the fit', () => {
  beforeEach(() => jest.useFakeTimers());

  const room = () => screen.getByTestId('stage-podium', HIDDEN_TOO);
  const plate = () => screen.getByTestId('stage-podium-plate', HIDDEN_TOO);

  /** The room, laid out — after the OS's answers about motion and screen readers have landed. */
  async function measure(width: number, height: number) {
    await act(async () => {
      await Promise.resolve();
    });
    fireEvent(room(), 'layout', { nativeEvent: { layout: { x: 0, y: 0, width, height } } });
  }

  /** Where the plate's box lands in the room once scaled about its centre. */
  function drawn() {
    const { style, read } = styleOf(plate());
    const scale = Number(read('scale'));
    const left = Number(style.left);
    const top = Number(style.top);
    const grownX = (PODIUM_BOX.width * (1 - scale)) / 2;
    const grownY = (PODIUM_BOX.height * (1 - scale)) / 2;
    return {
      // A measured plate sets none of its own.
      opacity: Number(style.opacity ?? 1),
      scale,
      left: left + grownX,
      right: left + PODIUM_BOX.width - grownX,
      top: top + grownY,
      bottom: top + PODIUM_BOX.height - grownY,
    };
  }

  it('draws nothing until it knows its room', async () => {
    drawSignUp();

    expect(drawn().opacity).toBe(0);

    await measure(342, 178);
    expect(drawn().opacity).toBe(1);
  });

  /**
   * A 390pt phone's room, then a 375 × 667 phone's with the headline at two lines, then a 320pt
   * phone's with the headline at the text cap's three: the podium scales down whole into each,
   * centred, its feet on the room's foot just over the headline — never over the headline or the
   * wordmark, and never larger than drawn.
   */
  it.each([
    { width: 342, height: 260 },
    { width: 342, height: 178 },
    { width: 327, height: 120 },
    { width: 272, height: 72 },
  ])('fits a $width × $height room, standing on its foot', async ({ width, height }) => {
    drawSignUp();

    await measure(width, height);

    const box = drawn();
    expect(box.scale).toBeGreaterThan(0);
    expect(box.scale).toBeLessThanOrEqual(1);
    expect(box.left).toBeGreaterThanOrEqual(-1e-6);
    expect(box.right).toBeLessThanOrEqual(width + 1e-6);
    expect(box.top).toBeGreaterThanOrEqual(-1e-6);
    expect(box.bottom).toBeCloseTo(height, 6);
    expect(box.left).toBeCloseTo(width - box.right, 6);
  });

  it('is drawn for the text cap, so the largest names still fit the box', () => {
    const tallest = Math.max(
      ...PODIUM_PLACES.map(
        (place) =>
          PODIUM.face[place] +
          theme.type.cardTitle.lineHeight * theme.size.stage.textMaxScale +
          PODIUM.step[place],
      ),
    );
    expect(PODIUM_BOX.height).toBeGreaterThan(tallest);
  });
});

/**
 * **Through the real route tree**: sign-up opened from sign-in rises; *Sign in* goes back, which
 * takes sign-up down; opened again it rises again.
 *
 * **The harness runs every pending timer on each navigation** (`renderRouter` subscribes
 * `runOnlyPendingTimers` to the root state), which can set a rise armed in a mount effect going
 * before the test looks, by a few hundred milliseconds that depend on what else the suite has run.
 * So what is held at each opening is a podium **not yet risen** — You not on it, the first step not
 * up — and then risen once the clock has run. The empty stage itself is held on the screen drawn on
 * its own, above.
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

  /** The push lands at once; a `waitFor` would only move the fake clock under the rise. */
  function openSignUp() {
    fireEvent.press(routed.getByLabelText(SIGN_IN_COPY.createAccount));
    expect(routed).toHavePathname('/sign-up');
  }

  /** A podium the rise has not yet finished: You not on the first step, which is not up. */
  function expectNotYetRisen() {
    const now = podium(routed);
    expect(now.first.step).toBeLessThan(1);
    expect(now.first.player.shows).toBe(0);
  }

  it('plays the rise again each time sign-up is opened again', async () => {
    stubGate(transport, { hasPlayerProfile: true });
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/sign-in' });
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));

    openSignUp();
    expectNotYetRisen();
    act(() => jest.advanceTimersByTime(RISEN + SETTLE));
    expect(podium(routed)).toEqual(ALL_STANDING);

    fireEvent.press(routed.getByRole('link', { name: SIGN_UP_COPY.signIn }));
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));
    // Gone with the screen: the risen podium is not kept anywhere to come back to.
    expect(routed.queryByTestId('stage-podium', HIDDEN_TOO)).toBeNull();

    openSignUp();
    expectNotYetRisen();
    act(() => jest.advanceTimersByTime(RISEN + SETTLE));
    expect(podium(routed)).toEqual(ALL_STANDING);
  });
});
