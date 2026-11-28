/**
 * **Sign-in on the stage** ([#784](https://github.com/Rakieta02/Rakieta/issues/784), PRD #783) — the
 * dark hero, the paper sheet and the restyled form, held to what a person can read or hear.
 *
 * Only `fetch` is faked, as in `authFlow.test.tsx`: the screen, its schema, the mutation and the
 * error model all run for real. **Where a thing sits on the screen is not something a query can
 * see** — the sheet over the hero, the label row, the look — and goes to a device look. What can be
 * asked is what is drawn, in what order a screen reader meets it, and what it hides from one: so
 * the order here is the reading order, walked off the rendered tree.
 *
 * The hero is hidden from screen readers (ADR-0198), so the queries that look for its words opt
 * into hidden elements; the ones that do not are the proof that a listener never meets it.
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';
import { renderRouter, screen as routed } from 'expo-router/testing-library';
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
import { errorResponse, installTransport, type Transport } from '@/test-support/transport';

import { refreshTokens } from '../use-cases/refreshTokens';

import {
  EMAIL_LABEL,
  EMAIL_PLACEHOLDER,
  PASSWORD_LABEL,
  SIGN_IN_COPY,
  STAGE_WORDMARK,
} from './authPresentation';
import { INVITATION_COPY } from './invitationPresentation';
import { RESET_COPY } from './resetPresentation';
import { SignInScreen } from './SignInScreen';

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

function drawSignIn() {
  render(
    <QueryClientProvider client={queryClient}>
      <SignInScreen />
    </QueryClientProvider>,
  );
}

/** `wanted`, in the order a screen reader meets them on the screen drawn now. */
const inOrder = (wanted: readonly string[]) => inTreeOrder(screen.toJSON(), wanted);

describe('the hero', () => {
  it('draws the wordmark and the headline', () => {
    drawSignIn();

    expect(screen.getByText(STAGE_WORDMARK, { includeHiddenElements: true })).toBeTruthy();
    expect(screen.getByText(SIGN_IN_COPY.headline, { includeHiddenElements: true })).toBeTruthy();
  });

  /** ADR-0198: the form is the screen; a listener never meets the picture above it. */
  it('is hidden from a screen reader', () => {
    drawSignIn();

    expect(screen.queryByText(STAGE_WORDMARK)).toBeNull();
    expect(screen.queryByText(SIGN_IN_COPY.headline)).toBeNull();
  });

  /**
   * Its words grow with the OS text size only so far — the tab bar's mechanism — so a large text
   * setting cannot push the headline out of the hero. The cap's number is derived in
   * `stageTextCap.test.ts`; here, that both words are held to it.
   */
  it('caps how far its words grow with large text, and the form’s are not capped', () => {
    drawSignIn();

    const capped = [STAGE_WORDMARK, SIGN_IN_COPY.headline].map(
      (word) => screen.getByText(word, { includeHiddenElements: true }).props.maxFontSizeMultiplier,
    );
    expect(new Set(capped).size).toBe(1);
    expect(capped[0]).toBeGreaterThan(1);
    expect(screen.getByRole('header').props.maxFontSizeMultiplier).toBeUndefined();
  });
});

describe('the form', () => {
  it('reads top to bottom as the mock draws it, with no RAKIETA over the title', () => {
    drawSignIn();

    const sheet = [
      `header:${SIGN_IN_COPY.title}`,
      `box:${EMAIL_LABEL}`,
      `box:${PASSWORD_LABEL}`,
      `link:${RESET_COPY.signInLink}`,
      `button:${SIGN_IN_COPY.submit}`,
      SIGN_IN_COPY.or,
      `link:${INVITATION_COPY.signInLink}`,
      SIGN_IN_COPY.newHere,
      `link:${SIGN_IN_COPY.createAccount}`,
    ];
    expect(inOrder(sheet)).toEqual(sheet);
    // The hero's wordmark replaces the eyebrow, so the title stands alone.
    expect(screen.queryByText('Rakieta')).toBeNull();
  });

  /** Empty, so the keychain's autofill still offers the saved address (story 11). */
  it('opens with the email box empty, and you@example.com as its placeholder', () => {
    drawSignIn();

    const email = screen.getByLabelText(EMAIL_LABEL);
    expect(email.props.value).toBe('');
    expect(email.props.placeholder).toBe(EMAIL_PLACEHOLDER);
    expect(EMAIL_PLACEHOLDER).toBe('you@example.com');
  });

  /**
   * The mock's boxes and buttons, not the app's (6.13 and 6.1 as amended): both boxes in the
   * stage's look and both buttons at its height. What the look is, is `TextField`'s and `Button`'s
   * to hold; here, that sign-in asks for it.
   */
  it('draws its boxes in the stage’s look and its buttons at their height', () => {
    drawSignIn();

    for (const name of [EMAIL_LABEL, PASSWORD_LABEL]) {
      const box = StyleSheet.flatten(screen.getByLabelText(name).props.style as TextStyle);
      expect(box.fontSize).toBe(theme.type.stageValue.fontSize);
      expect(box.minHeight).toBe(theme.size.stage.control);
    }
    for (const button of [
      screen.getByRole('button', { name: SIGN_IN_COPY.submit }),
      screen.getByRole('link', { name: INVITATION_COPY.signInLink }),
    ]) {
      expect(StyleSheet.flatten(button.props.style as ViewStyle).minHeight).toBe(
        theme.size.stage.control,
      );
    }
  });

  it('calls the invitation’s way in I have an invitation code', () => {
    drawSignIn();

    expect(screen.getByRole('link', { name: 'I have an invitation code' })).toBeTruthy();
  });
});

describe('a refusal', () => {
  /**
   * Today's sentences and sources, drawn **on the box's label row** — read before the box rather
   * than after it — so the form under it does not shift (story 18).
   */
  it('draws an empty box’s sentence on that box’s label row', async () => {
    drawSignIn();

    fireEvent.press(screen.getByLabelText(SIGN_IN_COPY.submit));

    expect(await screen.findByText('Enter your email address.')).toBeTruthy();
    expect(screen.getByText('Enter your password.')).toBeTruthy();
    expect(
      inOrder([
        `alert:Enter your email address.`,
        `box:${EMAIL_LABEL}`,
        `alert:Enter your password.`,
        `box:${PASSWORD_LABEL}`,
      ]),
    ).toEqual([
      `alert:Enter your email address.`,
      `box:${EMAIL_LABEL}`,
      `alert:Enter your password.`,
      `box:${PASSWORD_LABEL}`,
    ]);
    expect(transport.requests).toHaveLength(0);
  });

  it('draws a malformed email’s sentence on the email’s label row', async () => {
    drawSignIn();

    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'tomek.k');
    fireEvent.changeText(screen.getByLabelText(PASSWORD_LABEL), 'backhand42');
    fireEvent.press(screen.getByLabelText(SIGN_IN_COPY.submit));

    const sentence = "That doesn't look like an email address.";
    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(inOrder([`alert:${sentence}`, `box:${EMAIL_LABEL}`])).toEqual([
      `alert:${sentence}`,
      `box:${EMAIL_LABEL}`,
    ]);
  });

  /** A refusal about the whole form sits above the whole form (story 20). */
  it('keeps the server’s banner between the title and Email', async () => {
    transport.on('POST', '/api/v1/auth/login', () => errorResponse(401, 'invalid_credentials'));
    drawSignIn();

    fireEvent.changeText(screen.getByLabelText(EMAIL_LABEL), 'tomek.k@gmail.com');
    fireEvent.changeText(screen.getByLabelText(PASSWORD_LABEL), 'wrong');
    fireEvent.press(screen.getByLabelText(SIGN_IN_COPY.submit));

    const banner = "That email and password don't match. Try again.";
    expect(await screen.findByText(banner)).toBeTruthy();
    expect(
      inOrder([`header:${SIGN_IN_COPY.title}`, `alert:${banner}`, `box:${EMAIL_LABEL}`]),
    ).toEqual([`header:${SIGN_IN_COPY.title}`, `alert:${banner}`, `box:${EMAIL_LABEL}`]);
  });
});

/**
 * **The status bar is light over the hero, and only while sign-in is the screen in view.** A stack
 * keeps sign-in mounted under the screen pushed over it, so a light bar drawn for as long as it is
 * mounted would leave white icons over *Forgot password?*'s paper. Through the real route tree.
 */
describe('the status bar', () => {
  /** The light bars mounted now — React Native's own `StatusBar`, which `expo-status-bar` draws. */
  const lightBars = () =>
    routed.UNSAFE_queryAllByType(StatusBar).filter((bar) => bar.props.barStyle === 'light-content');

  it('is light on sign-in, goes with it when a screen covers it, and comes back on return', async () => {
    stubGate(transport, { hasPlayerProfile: true });
    renderRouter(ONBOARDING_ROUTES, { initialUrl: '/sign-in' });
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));

    expect(lightBars()).toHaveLength(1);

    fireEvent.press(routed.getByLabelText(RESET_COPY.signInLink));
    await waitFor(() => expect(routed).toHavePathname('/forgot-password'));
    expect(lightBars()).toHaveLength(0);

    fireEvent.press(routed.getByLabelText(RESET_COPY.backToSignIn));
    await waitFor(() => expect(routed).toHavePathname('/sign-in'));
    expect(lightBars()).toHaveLength(1);
  });
});
