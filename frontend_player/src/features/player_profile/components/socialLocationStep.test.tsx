/**
 * The location step, driven through the real route tree with the socket and the device
 * faked — and nothing else.
 *
 * Two edges are outside the app and both are described per test: the network, through
 * `installTransport`, and the device's own position, through the app's **own port**. The
 * native module is never touched — it has no JS implementation a test could drive, which is
 * the whole reason `LocationPort` exists, and it is also why *granted* and *refused* can
 * both be exercised here at all. Everything between the two runs for real: the router, the
 * domain rule that coarsens a fix, the store and the screen.
 *
 * **The refusal is half the ticket.** Location is what search and matchmaking are worked out
 * from, so the step insists — and a player who says no still finishes it, with the cost
 * named on the control that leaves. A suite that only walked the granted path would prove
 * the case that was never in doubt.
 *
 * Every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told — **with one deliberate exception**. The draft is read
 * directly once, because *the area is held in the part's draft* is a requirement of this
 * step and the commit that would make it observable is a later ticket. The figure on screen
 * is asserted separately, so the two together say the drawn area and the kept area are one
 * pair.
 */

import { focusManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  resetLocation,
  stubGate as stubGateWith,
  stubLocation,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { fakeLocation, type FakeLocation } from '@/test-support/platform';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { useProfileDraft } from '../store/profileDraft.store';

import {
  ACCESS_BODY,
  ACCESS_TITLE,
  AREA_UNSET_LINE,
  NO_FIX_TITLE,
  OPEN_SETTINGS,
  USE_MY_LOCATION,
  WHY_BODY,
  WHY_TITLE,
  WITHOUT_AN_AREA_LABEL,
  WITH_AN_AREA_LABEL,
} from './locationPresentation';

/** One rating: the first part is behind this player, and the second one is not. */
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

/**
 * A reading with metres in it, and the area it falls in.
 *
 * The two are stated separately on purpose: every assertion about what is drawn and what is
 * kept names `AREA`, and `PRECISE` appears only where the point is that it is **not** there.
 */
const PRECISE = { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 };
const AREA_DRAWN = '41,39° N · 2,17° E';
const AREA_SPOKEN = 'Your area: 41,39 degrees north, 2,17 degrees east';
const AREA_KEPT = { latitude: 41.39, longitude: 2.17 };

/** Somewhere else entirely — what a player who travelled comes back to the app holding. */
const ELSEWHERE = { latitude: 40.4168, longitude: -3.7038, accuracyMetres: 20 };
const ELSEWHERE_DRAWN = '40,42° N · 3,70° W';

let transport: Transport;
let device: FakeLocation;

/** A launch by a player the gate owes the second part to, walked as far as step four. */
async function reachTheLocationStep() {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);
  stubLocation(device);

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/photos'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/availability'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/location'));
  await screen.findByText('Where do you play?');
}

/** Press the one control that reaches the device, and let the permission and the fix land. */
async function askTheDevice() {
  fireEvent.press(screen.getByLabelText(USE_MY_LOCATION));
  // The permission and the fix are both promises, and the screen is redrawn as each lands.
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

/** What the OS does when the player leaves the app and comes back to it. */
async function leaveAndReturn() {
  await act(async () => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
    await Promise.resolve();
    await Promise.resolve();
  });
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useProfileDraft.getState().reset();
  focusManager.setFocused(true);
  // The ordinary device: never asked, would say yes, and knows where it is. Every case that
  // wants another answer says so before launching.
  device = fakeLocation({ fix: PRECISE });
});

afterEach(() => {
  transport.restore();
  resetLocation();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// Before anybody is asked anything
// ---------------------------------------------------------------------------

describe('arriving on the step', () => {
  it('explains what the area is for before the phone asks for anything', async () => {
    await reachTheLocationStep();

    expect(screen.getByText(WHY_TITLE)).toBeTruthy();
    expect(screen.getByText(WHY_BODY)).toBeTruthy();

    // Story 54, and the assertion that makes it a fact: an untouched permission is a
    // permission nobody prompted for. iOS shows its dialog once per install, so a prompt
    // that arrives before the sentence spends the only ask this app gets.
    expect(device.state).toBe('undetermined');
    expect(device.reads).toBe(0);
  });

  it('reads nothing until the player presses, and says so', async () => {
    await reachTheLocationStep();

    expect(screen.queryByText(AREA_DRAWN)).toBeNull();
    expect(screen.getByLabelText(USE_MY_LOCATION)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The player says yes
// ---------------------------------------------------------------------------

describe('granting the permission', () => {
  it('captures one fix and shows the area it falls in', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(device.state).toBe('granted');
    // One fix. Nothing here watches, polls or subscribes — a stream of positions is a
    // movement trail, which is a different privacy class from the one that was asked about.
    expect(device.reads).toBe(1);
    expect(await screen.findByText(AREA_DRAWN)).toBeTruthy();
  });

  /**
   * The reading had metres in it and the screen has a kilometre. Story 55: what is held is
   * coarse, and the fix that produced it is not recoverable from anything on this screen.
   */
  it('never draws the reading the device gave it', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(AREA_DRAWN);

    expect(screen.queryByText(/3874|1686/)).toBeNull();
    expect(screen.queryByText(/12 m|accuracy/i)).toBeNull();
  });

  /** The coordinate pair and the words that name it are one thing, or they are two halves. */
  it('reads the area out with the symbols spelled', async () => {
    await reachTheLocationStep();
    await askTheDevice();

    expect(await screen.findByLabelText(AREA_SPOKEN)).toBeTruthy();
  });

  it('holds the coarse area in the part draft, and only the coarse one', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(AREA_DRAWN);

    // The one direct read of the draft in this suite — see the note at the top. What is
    // kept is the pair on screen, which is also the pair the commit will send.
    expect(useProfileDraft.getState().draft?.location).toEqual(AREA_KEPT);
  });

  it('continues plainly once there is an area', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(AREA_DRAWN);

    fireEvent.press(screen.getByLabelText(WITH_AN_AREA_LABEL));

    await waitFor(() => expect(screen).toHavePathname('/radius'));
  });
});

// ---------------------------------------------------------------------------
// The player says no
// ---------------------------------------------------------------------------

describe('refusing the permission', () => {
  beforeEach(() => {
    device = fakeLocation({ answer: 'denied', fix: PRECISE });
  });

  it('says what a refusal costs and how to undo it', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(await screen.findByText(ACCESS_TITLE.refused)).toBeTruthy();
    expect(screen.getByText(ACCESS_BODY.refused)).toBeTruthy();
    // No fix was read: the port answers none without a permission, and nothing here
    // pretends otherwise by drawing an area anyway.
    expect(screen.queryByText(AREA_DRAWN)).toBeNull();
  });

  /**
   * The step insists; it does not hold anybody hostage. A player stuck on step four of six
   * behind a permission they can change at any time is not a setup flow — and the label is
   * where the cost is stated, because a note beside it is a note they may not read.
   */
  it('lets the player finish the step, with the cost on the control that leaves', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.refused);

    fireEvent.press(screen.getByLabelText(WITHOUT_AN_AREA_LABEL));

    await waitFor(() => expect(screen).toHavePathname('/radius'));
    // Nothing was claimed on their behalf. An unanswered location is absent, never a zero
    // pair, and the commit will find it exactly as the player left it.
    expect(useProfileDraft.getState().draft?.location).toBeUndefined();
  });

  it('offers the prompt again on the next press', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.refused);

    // The player changed their mind, which is the whole reason a refused permission is not
    // a permanent one: the next press shows the OS dialog again.
    device.answer = 'granted';
    await askTheDevice();

    expect(await screen.findByText(AREA_DRAWN)).toBeTruthy();
    expect(screen.queryByText(ACCESS_TITLE.refused)).toBeNull();
  });

  /** A return to the app is not a press. Re-prompting on every foreground is a wall. */
  it('does not ask again when the app comes back', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.refused);

    device.answer = 'granted';
    await leaveAndReturn();

    expect(device.state).toBe('denied');
    expect(device.reads).toBe(0);
    expect(screen.queryByText(AREA_DRAWN)).toBeNull();
  });
});

describe('a permission that was turned off in Settings', () => {
  beforeEach(() => {
    device = fakeLocation({ state: 'blocked', fix: PRECISE });
  });

  /**
   * The OS resolves a blocked permission itself, instantly and negatively, without showing
   * the player anything — so *press again* is the one sentence this screen must not say.
   */
  it('sends the player to Settings rather than to a prompt that will not appear', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(await screen.findByText(ACCESS_TITLE.blocked)).toBeTruthy();
    expect(screen.getByText(ACCESS_BODY.blocked)).toBeTruthy();
    expect(screen.getByLabelText(OPEN_SETTINGS)).toBeTruthy();
    expect(device.reads).toBe(0);
  });

  it('still lets the step be finished', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.blocked);

    fireEvent.press(screen.getByLabelText(WITHOUT_AN_AREA_LABEL));

    await waitFor(() => expect(screen).toHavePathname('/radius'));
  });
});

describe('a phone that cannot place itself', () => {
  beforeEach(() => {
    // Allowed, asked, and no fix — indoors, underground, or a device with no signal.
    device = fakeLocation({ fix: null });
  });

  it('says so rather than leaving the press looking ignored', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(await screen.findByText(NO_FIX_TITLE)).toBeTruthy();
    expect(screen.getByLabelText(WITHOUT_AN_AREA_LABEL)).toBeTruthy();
  });

  /**
   * The line under the control is a claim about what has happened, and on a phone that was
   * already allowed it has happened — silently, on arrival. Copy that says otherwise is the
   * kind that survives a redesign, because nobody re-reads a sentence they believe.
   */
  it('does not tell an already-allowed player that nothing has been read', async () => {
    device = fakeLocation({ state: 'granted', fix: null });

    await reachTheLocationStep();

    await waitFor(() => expect(device.reads).toBe(1));
    expect(screen.queryByText(AREA_UNSET_LINE)).toBeNull();
    // And it does not scold either: nobody asked for that read, so nothing reports it.
    expect(screen.queryByText(NO_FIX_TITLE)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Coming back to the app
// ---------------------------------------------------------------------------

describe('foregrounding the app with the permission granted', () => {
  it('re-reads the fix, so what is on screen is near where the player is', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(AREA_DRAWN);

    // The player went somewhere and came back. Story 58: the moment an area can silently
    // stop being true is the one where they were elsewhere in between.
    device.fix = ELSEWHERE;
    await leaveAndReturn();

    expect(await screen.findByText(ELSEWHERE_DRAWN)).toBeTruthy();
    expect(device.reads).toBe(2);
    expect(screen.queryByText(AREA_DRAWN)).toBeNull();
  });

  it('re-reads on arrival too, when the permission is already granted', async () => {
    device = fakeLocation({ state: 'granted', fix: PRECISE });

    await reachTheLocationStep();

    // Nobody was prompted — the permission was already there — and the area is on screen
    // without the player having had to press anything.
    expect(await screen.findByText(AREA_DRAWN)).toBeTruthy();
    expect(device.reads).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// The area inside the part
// ---------------------------------------------------------------------------

describe('walking away from the step and back', () => {
  it('finds the same area, without asking the device again', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(AREA_DRAWN);

    fireEvent.press(screen.getByLabelText(WITH_AN_AREA_LABEL));
    await waitFor(() => expect(screen).toHavePathname('/radius'));

    fireEvent.press(screen.getByLabelText('Back to Where do you play?'));
    await waitFor(() => expect(screen).toHavePathname('/location'));

    expect(await screen.findByText(AREA_DRAWN)).toBeTruthy();
    // The permission is granted by now, so arriving re-reads — and the pair is the same
    // one, which is why nothing about the screen changed.
    expect(device.state).toBe('granted');
  });
});
