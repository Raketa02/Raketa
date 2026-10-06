/**
 * The location moves on a cold start — silently, after a day in the background, never on a
 * plain foreground, and never for a player still in onboarding (ADR-0174 §6, #462).
 *
 * Driven through the platform port's fake and the profile API mock, as `the-radar.md` §8
 * asks: what the phone answers is the fake's, what the app sent is the transport's record,
 * and the clock is jest's. Nothing here renders a screen about it, because there is none —
 * the only written trace is You's one sentence, and that is `locationPresentation.test.ts`'s.
 */

import { focusManager } from '@tanstack/react-query';
import { act, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  HOME_TAB_LINE,
  launchSignedIn,
  resetLocation,
  stubGate,
  stubLocation,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { fakeLocation, type FakeLocation } from '@/test-support/platform';
import { installTransport, noContent, type Transport, type Wire } from '@/test-support/transport';

import type { PlayerProfileSurface } from '../domain/PlayerProfileSurface';

import { playerProfileKeys } from './playerProfileKeys';

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

const LOCATION_PATH = '/api/v1/players/me/location';

/** What the device reports, to five places — and what the app must never send. */
const PRECISE = { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 };
/** The cell the fix falls in: what the commit sends, and what the refresh sends. */
const AREA_SENT = { latitude: 41.39, longitude: 2.17 };

const HOUR = 60 * 60 * 1000;

/** A surface already in the cache, so the invalidation has something to mark. */
const HELD_SURFACE: PlayerProfileSurface = {
  week: [],
  playIntents: {},
  socialTagIds: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
  photos: [],
  genderPreference: 'any',
};

let transport: Transport;
let device: FakeLocation;

const puts = () => transport.requestsTo('PUT', LOCATION_PATH);

/** A cold start into the app, for a player with a committed profile. */
async function coldStart() {
  await launchSignedIn();
  expect(await screen.findByText(HOME_TAB_LINE)).toBeTruthy();
}

/** What the OS does when the player leaves the app and comes back to it. */
async function leaveAndReturn() {
  await act(async () => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

/** Let the permission, the fix and the write all land. */
async function settle() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  transport.on('PUT', LOCATION_PATH, () => noContent());
  focusManager.setFocused(true);
  // The ordinary phone after onboarding: the permission was granted there, and it knows
  // where it is. Every case that wants another answer says so before launching.
  device = fakeLocation({ state: 'granted', fix: PRECISE });
  stubLocation(device);
  queryClient.setQueryData(playerProfileKeys.surface(), HELD_SURFACE);
});

afterEach(async () => {
  transport.restore();
  resetLocation();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

describe('a cold start', () => {
  it('reads one fix and puts the area it falls in — never the fix itself', async () => {
    await coldStart();
    await settle();

    await waitFor(() => expect(puts()).toHaveLength(1));
    expect(device.reads).toBe(1);
    expect(puts()[0]?.body).toEqual(AREA_SENT);
  });

  /**
   * The profile read is the client's copy of what the profile holds, so it is marked stale
   * rather than left to say where the player was — which is what makes it follow the day the
   * read grows the area. Asserted on the cache flag: nothing on Now observes the read, so a
   * request count would pass with or without the invalidation.
   */
  it('invalidates the profile surface once the write has landed', async () => {
    await coldStart();
    await settle();

    await waitFor(() => expect(puts()).toHaveLength(1));
    await waitFor(() =>
      expect(queryClient.getQueryState(playerProfileKeys.surface())?.isInvalidated).toBe(true),
    );
  });

  /**
   * The refresh **never asks**: onboarding did, and a return to the app is not a press. A
   * permission revoked in Settings since then leaves the stored cell where it is, with no
   * prompt, no request and no sentence — nothing happens and nothing is said.
   */
  it('neither prompts nor writes when the permission has been revoked', async () => {
    device = fakeLocation({ state: 'denied', answer: 'granted', fix: PRECISE });
    stubLocation(device);

    await coldStart();
    await settle();

    expect(device.state).toBe('denied');
    expect(device.reads).toBe(0);
    expect(puts()).toHaveLength(0);
    expect(queryClient.getQueryState(playerProfileKeys.surface())?.isInvalidated).toBe(false);
  });

  it('writes nothing when the phone could not place itself', async () => {
    device = fakeLocation({ state: 'granted', fix: null });
    stubLocation(device);

    await coldStart();
    await settle();

    expect(device.reads).toBe(1);
    expect(puts()).toHaveLength(0);
  });

  /**
   * A player still in onboarding is never refreshed: the location step is where their area
   * is being asked for, with a prompt and a sentence, and a silent write behind it would be a
   * second reader of the same phone. `hasPlayerProfile: false` with a rating sends the gate
   * to the second part's first step.
   */
  it('never runs for a player still in onboarding', async () => {
    transport.restore();
    transport = installTransport();
    stubGate(transport, { ratings: [RATING], hasPlayerProfile: false });
    stubProfileOptions(transport);
    transport.on('PUT', LOCATION_PATH, () => noContent());

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/tags'));
    await settle();

    expect(device.reads).toBe(0);
    expect(puts()).toHaveLength(0);
  });
});

describe('a return from the background', () => {
  it('reads nothing on a plain foreground, or on one inside the day', async () => {
    await coldStart();
    await settle();
    await waitFor(() => expect(puts()).toHaveLength(1));

    await leaveAndReturn();
    jest.setSystemTime(Date.now() + 23 * HOUR);
    await leaveAndReturn();

    expect(device.reads).toBe(1);
    expect(puts()).toHaveLength(1);
  });

  it('reads once more after a day away', async () => {
    await coldStart();
    await settle();
    await waitFor(() => expect(puts()).toHaveLength(1));

    jest.setSystemTime(Date.now() + 25 * HOUR);
    await leaveAndReturn();
    await settle();

    await waitFor(() => expect(puts()).toHaveLength(2));
    expect(device.reads).toBe(2);
    expect(puts()[1]?.body).toEqual(AREA_SENT);
  });

  /** The day is measured from the last time the phone was asked, not the last time it answered. */
  it('measures the day from the last refresh, so the second return inside it reads nothing', async () => {
    await coldStart();
    await settle();
    await waitFor(() => expect(puts()).toHaveLength(1));

    jest.setSystemTime(Date.now() + 25 * HOUR);
    await leaveAndReturn();
    await settle();
    await waitFor(() => expect(puts()).toHaveLength(2));

    jest.setSystemTime(Date.now() + 1 * HOUR);
    await leaveAndReturn();
    await settle();

    expect(puts()).toHaveLength(2);
    expect(device.reads).toBe(2);
  });

  /** A revoked permission is checked again after the day, and still asks nobody. */
  it('still asks nobody after a day when the permission was revoked meanwhile', async () => {
    await coldStart();
    await settle();
    await waitFor(() => expect(puts()).toHaveLength(1));

    device.state = 'denied';
    jest.setSystemTime(Date.now() + 25 * HOUR);
    await leaveAndReturn();
    await settle();

    expect(device.state).toBe('denied');
    expect(device.reads).toBe(1);
    expect(puts()).toHaveLength(1);
  });
});
