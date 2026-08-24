/**
 * The onboarding occasion, driven through the real route tree.
 *
 * Only `fetch` and the native notification module are faked — the same two edges
 * every other flow suite here fakes — so the router, the screens, the hook, the
 * use-cases, the mapper and the request all run for real.
 *
 * The assertions are shaped around the one thing `ADR-0061` actually decided:
 * **the OS prompt is spent only on a yes.** So half of this file is about what
 * did *not* happen — the phone was not asked, nothing was sent, nothing was kept
 * — and the other half follows a yes all the way to the wire.
 */

import { focusManager, onlineManager } from '@tanstack/react-query';
import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { PUSH_DEVICE_PATH, osMock, resetPhone, stubPhone } from '@/test-support/notifications';
import { matchCard, nowOffering, stubNow } from '@/test-support/now';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import { installTransport, noContent, type Transport, type Wire } from '@/test-support/transport';

import { useStandbyAskStore } from '../store/standbyAsk.store';

const MATCH = '9d2f0000-0000-4000-8000-000000000001';

const RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  resetPhone();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useStandbyAskStore.getState().reset();
  focusManager.setFocused(true);
  transport.on('PUT', PUSH_DEVICE_PATH, () => noContent());
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

/** The explainer, entered where onboarding enters it. */
async function openTheExplainer() {
  stubGate(transport, { ratings: [RATING] });
  await launchSignedIn('/notifications');
  expect(await screen.findByText('When a seat opens up')).toBeTruthy();
}

/** One offer card and nothing else — the shape a refusal must not cost her. */
function offer(): Wire['MatchCardResponse'] {
  return matchCard({
    matchId: MATCH,
    situation: 'seatOpened',
    clubName: 'Sunset Padel',
    clock: '2099-01-01T18:00:00Z',
    act: 'takeSeat',
  });
}

describe('what the explainer explains', () => {
  it('says why a seat is worth being told about, and what the line will say', async () => {
    await openTheExplainer();

    expect(screen.getByText('Matches lose players at short notice')).toBeTruthy();
    expect(screen.getByText(/the seat goes to whoever takes it first/)).toBeTruthy();
    expect(screen.getByText('One line, and never the venue')).toBeTruthy();
    expect(screen.getByText(/The sport and when it starts/)).toBeTruthy();
    expect(screen.getByText('One at a time, not a pile')).toBeTruthy();
  });

  /**
   * The claim the whole screen rests on, said out loud — and enforced further
   * down by a player who declines and then finds her offer card on Now.
   */
  it('says that refusing costs her nothing on Now', async () => {
    await openTheExplainer();

    expect(screen.getByText('Saying no costs you nothing here')).toBeTruthy();
    expect(screen.getByText(/on your Now screen either way/)).toBeTruthy();
  });

  it('offers exactly the two controls the record names', async () => {
    await openTheExplainer();

    expect(screen.getByLabelText('Turn on')).toBeTruthy();
    expect(screen.getByLabelText('Not now')).toBeTruthy();
  });

  /**
   * **The venue is never on a lock screen** (`ADR-0062`), and the travel figure
   * that `ADR-0062`'s exemplar carries is not promised either: nothing can supply
   * one in v1 (`Raketa02/Raketa#129`), so a screen that said *how far away it is*
   * would be describing a clause the sentence cannot print.
   */
  it('promises neither the venue nor a travel time', async () => {
    await openTheExplainer();

    expect(screen.queryByText(/which club/i)).toBeNull();
    expect(screen.queryByText(/minutes away|min away|how far/i)).toBeNull();
  });
});

describe('the OS prompt is spent only on a yes', () => {
  it('does not ask the phone anything when she taps Not now', async () => {
    await openTheExplainer();

    fireEvent.press(screen.getByLabelText('Not now'));

    await waitFor(() => expect(screen).toHavePathname('/data'));
    expect(osMock().requestPermissionsAsync).not.toHaveBeenCalled();
  });

  it('records nothing about a refusal, on the device or on the wire', async () => {
    await openTheExplainer();
    const before = transport.requests.length;

    fireEvent.press(screen.getByLabelText('Not now'));
    await waitFor(() => expect(screen).toHavePathname('/data'));

    expect(transport.requests.length).toBe(before);
  });

  it('fires the system dialog exactly once when she taps Turn on', async () => {
    stubPhone({ answersPrompt: 'granted' });
    await openTheExplainer();

    fireEvent.press(screen.getByLabelText('Turn on'));

    await waitFor(() => expect(screen).toHavePathname('/data'));
    expect(osMock().requestPermissionsAsync).toHaveBeenCalledTimes(1);
  });

  /**
   * Both controls lead to the same place, which is the rule expressed as
   * navigation: there is no consequence screen for a refusal, because there is
   * no consequence.
   */
  it('carries on to the data screen either way', async () => {
    stubPhone({ answersPrompt: 'denied' });
    await openTheExplainer();

    fireEvent.press(screen.getByLabelText('Turn on'));

    await waitFor(() => expect(screen).toHavePathname('/data'));
  });
});

describe('what a yes sends', () => {
  it('registers the phone with its token, its platform and its setting', async () => {
    stubPhone({ answersPrompt: 'granted', token: 'ExponentPushToken[flow]' });
    await openTheExplainer();

    fireEvent.press(screen.getByLabelText('Turn on'));

    await waitFor(() => expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)).toHaveLength(1));
    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)[0]?.body).toEqual({
      token: 'ExponentPushToken[flow]',
      platform: 'ios',
      time_sensitive_setting: 'notSupported',
    });
  });

  it('sends nothing when the dialog was refused', async () => {
    stubPhone({ answersPrompt: 'denied' });
    await openTheExplainer();

    fireEvent.press(screen.getByLabelText('Turn on'));

    await waitFor(() => expect(screen).toHavePathname('/data'));
    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)).toEqual([]);
  });

  /**
   * The state of every build until an Expo project id exists
   * (`Raketa02/Raketa#26`). She granted permission, there is nowhere to send it,
   * and the screen behaves exactly as it does on a success — no sentence, no
   * failure, no retry.
   */
  it('carries on silently when the phone has no token to give', async () => {
    stubPhone({ answersPrompt: 'granted', token: undefined });
    await openTheExplainer();

    fireEvent.press(screen.getByLabelText('Turn on'));

    await waitFor(() => expect(screen).toHavePathname('/data'));
    expect(transport.requestsTo('PUT', PUSH_DEVICE_PATH)).toEqual([]);
  });

  /**
   * A registration that fails is not hers either. `ADR-0061` says a refusal
   * costs her the message and never a card; a *failure* must cost her no more
   * than a refusal does.
   */
  it('carries on silently when the registration fails', async () => {
    stubPhone({ answersPrompt: 'granted' });
    transport.on('PUT', PUSH_DEVICE_PATH, () => {
      throw new TypeError('Network request failed');
    });
    await openTheExplainer();

    fireEvent.press(screen.getByLabelText('Turn on'));

    await waitFor(() => expect(screen).toHavePathname('/data'));
  });
});

describe('a player who declined still gets the cards', () => {
  /**
   * `ADR-0061`'s promise, walked rather than asserted about: she refuses the ask
   * at the last step of onboarding, enters the app, and the seat that opened is
   * on her screen with the button that takes it.
   *
   * The mechanism behind it is that Now never asks — `nowDiscipline.test.ts`
   * walks that feature's whole source for a mention of the OS — and this is the
   * half of that rule a rendered test can carry.
   */
  it('sees the offer card, and its act, after tapping Not now', async () => {
    stubGate(transport, { ratings: [RATING] });
    stubNow(transport, nowOffering(offer()));
    await launchSignedIn('/notifications');

    fireEvent.press(await screen.findByLabelText('Not now'));
    await waitFor(() => expect(screen).toHavePathname('/data'));

    fireEvent.press(screen.getByLabelText('Start playing'));

    expect(await screen.findByLabelText(/Take the seat/)).toBeTruthy();
    expect(osMock().requestPermissionsAsync).not.toHaveBeenCalled();
  });
});
