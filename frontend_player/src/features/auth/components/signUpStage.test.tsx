/**
 * **Create an account on the stage** ([#785](https://github.com/Raketa02/Raketa/issues/785), PRD
 * #783) — sign-in's dark hero and paper sheet with sign-up's own form, restyled to mocks 4 and 6,
 * and the move between the two read as one flow.
 *
 * `signInStage.test.tsx`'s posture: only `fetch` is faked, and where a thing sits is a device look.
 * What a query can see is what is drawn, the order a screen reader meets it in — which, for a
 * column, is where it sits — and what the navigator holds. What sign-up **does** is
 * `authFlow.test.tsx`'s, unchanged.
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import { router } from 'expo-router';
import { act, renderRouter, screen as routed } from 'expo-router/testing-library';
import { StatusBar, StyleSheet, type TextStyle, type ViewStyle } from 'react-native';

import {
  clearStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { ONBOARDING_ROUTES, stubGate } from '@/test-support/onboardingRouter';
import { inOrder as inTreeOrder } from '@/test-support/readingOrder';
import {
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { ADULT_ATTESTATION_MISSING, ADULT_LABEL, PASSWORD_RULE } from '../schemas/authForms';
import { refreshTokens } from '../use-cases/refreshTokens';

import {
  AUTH_EYEBROW,
  EMAIL_LABEL,
  EMAIL_PLACEHOLDER,
  PASSWORD_LABEL,
  PASSWORD_PLACEHOLDER,
  REPEAT_PASSWORD_LABEL,
  REPEAT_PASSWORD_PLACEHOLDER,
  SIGN_IN_COPY,
  SIGN_UP_COPY,
  STAGE_WORDMARK,
} from './authPresentation';
import { RESET_COPY } from './resetPresentation';
import { SignInScreen } from './SignInScreen';
import { SignUpScreen } from './SignUpScreen';

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

function drawSignUp() {
  render(
    <QueryClientProvider client={queryClient}>
      <SignUpScreen />
    </QueryClientProvider>,
  );
}

/** `wanted`, in the order a screen reader meets them on the screen drawn now. */
const inOrder = (wanted: readonly string[]) => inTreeOrder(screen.toJSON(), wanted);

const press = (name: string) => fireEvent.press(screen.getByLabelText(name));

/** A form this side of the wire accepts — the repeat is the caller's, to make it not match. */
function fillIn(repeat = 'backhand42') {
  fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'ania.k@gmail.com');
  fireEvent.changeText(screen.getByLabelText(PASSWORD_LABEL), 'backhand42');
  fireEvent.changeText(screen.getByLabelText(REPEAT_PASSWORD_LABEL), repeat);
  press(ADULT_LABEL);
}

describe('the hero', () => {
  /** The same stage as sign-in's, with sign-up's own line under the podium (#788, `stagePodium.test.tsx`). */
  it('draws the wordmark and sign-up’s headline, hidden from a screen reader', () => {
    drawSignUp();

    expect(screen.getByText(STAGE_WORDMARK, { includeHiddenElements: true })).toBeTruthy();
    expect(screen.getByText(SIGN_UP_COPY.headline, { includeHiddenElements: true })).toBeTruthy();
    expect(SIGN_UP_COPY.headline).toBe('Play ranked. The competition starts with you.');
    expect(screen.queryByText(SIGN_UP_COPY.headline)).toBeNull();
  });

  it('caps its words as sign-in’s are capped', () => {
    drawSignUp();

    const capped = [STAGE_WORDMARK, SIGN_UP_COPY.headline].map(
      (word) => screen.getByText(word, { includeHiddenElements: true }).props.maxFontSizeMultiplier,
    );
    expect(capped).toEqual([theme.size.stage.textMaxScale, theme.size.stage.textMaxScale]);
  });
});

describe('the form', () => {
  it('reads top to bottom as mocks 4 and 6 draw it, with no RAKIETA over the title', () => {
    drawSignUp();

    const sheet = [
      `header:${SIGN_UP_COPY.title}`,
      `box:${EMAIL_LABEL}`,
      `box:${PASSWORD_LABEL}`,
      PASSWORD_RULE,
      `box:${REPEAT_PASSWORD_LABEL}`,
      `checkbox:${ADULT_LABEL}`,
      `button:${SIGN_UP_COPY.submit}`,
      SIGN_UP_COPY.haveAccount,
      `link:${SIGN_UP_COPY.signIn}`,
    ];
    expect(inOrder(sheet)).toEqual(sheet);
    // The hero's wordmark replaces the eyebrow, so the title stands alone.
    expect(screen.queryByText(AUTH_EYEBROW)).toBeNull();
  });

  it('opens with every box empty, each with its placeholder', () => {
    drawSignUp();

    const placeholders = [
      [EMAIL_LABEL, EMAIL_PLACEHOLDER],
      [PASSWORD_LABEL, PASSWORD_PLACEHOLDER],
      [REPEAT_PASSWORD_LABEL, REPEAT_PASSWORD_PLACEHOLDER],
    ] as const;
    for (const [name, placeholder] of placeholders) {
      const box = screen.getByLabelText(name);
      expect(box.props.value).toBe('');
      expect(box.props.placeholder).toBe(placeholder);
    }
    expect([PASSWORD_PLACEHOLDER, REPEAT_PASSWORD_PLACEHOLDER]).toEqual([
      'At least 8 characters',
      'Once more',
    ]);
  });

  /** Sign-in's boxes and button (6.13 and 6.1 as amended): the same flow, the same look. */
  it('draws its three boxes in the stage’s look and its button at their height', () => {
    drawSignUp();

    for (const name of [EMAIL_LABEL, PASSWORD_LABEL, REPEAT_PASSWORD_LABEL]) {
      const box = StyleSheet.flatten(screen.getByLabelText(name).props.style as TextStyle);
      expect(box.fontSize).toBe(theme.type.stageValue.fontSize);
      expect(box.minHeight).toBe(theme.size.stage.control);
    }
    const button = screen.getByRole('button', { name: SIGN_UP_COPY.submit });
    expect(StyleSheet.flatten(button.props.style as ViewStyle).minHeight).toBe(
      theme.size.stage.control,
    );
  });
});

describe('a refusal', () => {
  /**
   * Today's sentences from today's schema, each box's **on its label row** — read before the box —
   * and the age question's under the tick box, after it.
   */
  it('draws each box’s sentence on its label row, and the age question’s under the box', async () => {
    drawSignUp();

    press(SIGN_UP_COPY.submit);

    const email = 'Enter your email address.';
    const password = 'Use at least 8 characters.';
    const repeat = 'Repeat your password.';
    expect(await screen.findByText(email)).toBeTruthy();
    const order = [
      `alert:${email}`,
      `box:${EMAIL_LABEL}`,
      `alert:${password}`,
      `box:${PASSWORD_LABEL}`,
      `alert:${repeat}`,
      `box:${REPEAT_PASSWORD_LABEL}`,
      `checkbox:${ADULT_LABEL}`,
      `alert:${ADULT_ATTESTATION_MISSING}`,
    ];
    expect(inOrder(order)).toEqual(order);
    expect(transport.requests).toHaveLength(0);
  });

  /** The rule is not replaced by a refusal any more: the refusal has moved up to the label row. */
  it('keeps the password rule under the box before and after a refusal', async () => {
    drawSignUp();
    const rule = [`box:${PASSWORD_LABEL}`, PASSWORD_RULE, `box:${REPEAT_PASSWORD_LABEL}`];

    expect(inOrder(rule)).toEqual(rule);

    fireEvent.changeText(screen.getByLabelText(PASSWORD_LABEL), 'backhand');
    press(SIGN_UP_COPY.submit);

    expect(await screen.findByText('Use at least one digit.')).toBeTruthy();
    expect(inOrder(rule)).toEqual(rule);
  });

  it('draws a mismatch on the repeat box’s label row', async () => {
    drawSignUp();

    fillIn('backhand43');
    press(SIGN_UP_COPY.submit);

    const sentence = "Those passwords don't match.";
    expect(await screen.findByText(sentence)).toBeTruthy();
    const order = [`alert:${sentence}`, `box:${REPEAT_PASSWORD_LABEL}`];
    expect(inOrder(order)).toEqual(order);
  });

  /** The server's refusal against a field is that field's, on its label row (story 19). */
  it('draws a taken email on the email’s label row', async () => {
    transport.on('POST', '/api/v1/users', () =>
      json(
        {
          code: 'email_already_registered',
          message: 'email already registered',
          trace_id: 'trace-test',
          details: { field: 'email' },
        } satisfies Wire['ErrorResponse'],
        409,
      ),
    );
    drawSignUp();

    fillIn();
    press(SIGN_UP_COPY.submit);

    const sentence = 'That email already has an account. Sign in instead.';
    expect(await screen.findByText(sentence)).toBeTruthy();
    const order = [`alert:${sentence}`, `box:${EMAIL_LABEL}`];
    expect(inOrder(order)).toEqual(order);
  });

  /** A refusal about the whole form sits above the whole form. */
  it('keeps the server’s banner between the title and Email', async () => {
    transport.on('POST', '/api/v1/users', networkFailure());
    drawSignUp();

    fillIn();
    press(SIGN_UP_COPY.submit);

    const banner = "We couldn't reach Rakieta. Check your connection and try again.";
    expect(await screen.findByText(banner)).toBeTruthy();
    const order = [`header:${SIGN_UP_COPY.title}`, `alert:${banner}`, `box:${EMAIL_LABEL}`];
    expect(inOrder(order)).toEqual(order);
  });
});

/**
 * **Sign-in and sign-up are two pages of one flow** — through the real route tree. The move each
 * way is a cross-fade rather than the platform's slide, so the stage seems to stay while its
 * contents change, and *Sign in* goes back to the sign-in underneath rather than stacking a second.
 *
 * **What the navigator holds is read off the native stack's screens**: the animation each asked for
 * (`stackAnimation`) and how many of each screen are mounted. Nothing a person sees in a suite says
 * how a screen arrived, and a native stack mounts every screen on it.
 */
describe('moving between sign-in and sign-up', () => {
  /** A drawn element, as far as this suite reads one. */
  type Drawn = { readonly type: unknown; readonly props: Readonly<Record<string, unknown>> };

  async function open(path: '/sign-in' | '/sign-up') {
    stubGate(transport, { hasPlayerProfile: true });
    renderRouter(ONBOARDING_ROUTES, { initialUrl: path });
    await waitFor(() => expect(routed).toHavePathname(path));
  }

  async function openSignUp() {
    await open('/sign-in');

    fireEvent.press(routed.getByLabelText(SIGN_IN_COPY.createAccount));
    await waitFor(() => expect(routed).toHavePathname('/sign-up'));
  }

  /**
   * The animation each screen on the stack asked the native stack for, bottom to top — the one it
   * is pushed and popped with. `undefined` is the platform's own slide.
   */
  const animations = () =>
    routed.UNSAFE_root.findAll((node: Drawn) => node.type === 'RNSScreen').map(
      (node: Drawn) => node.props.stackAnimation as string | undefined,
    );

  const signIns = () => routed.UNSAFE_queryAllByType(SignInScreen);
  const signUps = () => routed.UNSAFE_queryAllByType(SignUpScreen);

  /**
   * Sign-up's fade is the one it is pushed with and popped with, so it carries both directions.
   * Sign-in keeps the slide: it is what an email link's recovery screen puts in its own place.
   */
  it('opens Create an account over sign-in with a cross-fade', async () => {
    await openSignUp();

    expect(animations()).toEqual([undefined, 'fade']);
    expect(signUps()).toHaveLength(1);
  });

  /** Only sign-up fades: a recovery screen over sign-in still slides in. */
  it('keeps the platform’s slide for the screens off the stage', async () => {
    await open('/sign-in');

    fireEvent.press(routed.getByLabelText(RESET_COPY.signInLink));
    await waitFor(() => expect(routed).toHavePathname('/forgot-password'));

    expect(animations()).toEqual([undefined, undefined]);
  });

  it('goes back to the one sign-in on Sign in, never stacking a second', async () => {
    await openSignUp();

    fireEvent.press(routed.getByRole('link', { name: SIGN_UP_COPY.signIn }));
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));

    expect(signIns()).toHaveLength(1);
    expect(signUps()).toHaveLength(0);
    expect(router.canGoBack()).toBe(false);
  });

  /** A sign-up opened with nothing under it has no sign-in to go back to, so one takes its place. */
  it('puts sign-in in its place when nothing is under it', async () => {
    await open('/sign-up');
    expect(router.canGoBack()).toBe(false);

    fireEvent.press(routed.getByRole('link', { name: SIGN_UP_COPY.signIn }));
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));

    expect(signIns()).toHaveLength(1);
    expect(signUps()).toHaveLength(0);
    expect(router.canGoBack()).toBe(false);
  });

  /** Android's back button is the navigator's own back. */
  it('returns to sign-in on the device’s back', async () => {
    await openSignUp();

    act(() => router.back());
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));

    expect(signIns()).toHaveLength(1);
  });

  /** Sign-in's bar goes as sign-up covers it, and sign-up draws its own over the same night. */
  it('keeps the status bar light, drawn by the screen in view', async () => {
    await openSignUp();

    const lightBars = routed
      .UNSAFE_queryAllByType(StatusBar)
      .filter((bar) => bar.props.barStyle === 'light-content');
    expect(lightBars).toHaveLength(1);
  });
});
