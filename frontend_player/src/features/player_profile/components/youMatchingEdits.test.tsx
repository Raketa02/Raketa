/**
 * **Who you play with, walked the way a player walks it** — the real route tree, the real bar,
 * and only `fetch` faked
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §4; [#472](https://github.com/Raketa02/Raketa/issues/472)).
 *
 * The screen is the onboarding step's two groups under the tab's chrome, and the step's own
 * suite already proves the controls — the three answers and the reach sentence. What is
 * proved here is what the tab added: each group **pre-selects from the read** and **saves
 * alone** through its own route; the reach sentence is said at the press and never for
 * *Anyone*; and the row says the preference and **never the gender**. And, since 2026-09-18,
 * that each group's *Save* is green and saying *Saved* while its draft is the profile's own —
 * so the group just saved turns green and the other stays as it was.
 *
 * *Game suggestions* beside it is gone, with the proposals question it answered again
 * ([#582](https://github.com/Raketa02/Raketa/issues/582)).
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, theme } from '@/shared/ui';
import { fillOf } from '@/test-support/drawn';
import {
  PROFILE_SURFACE_SERVED,
  launchSignedIn,
  profileSurface,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { reachOf } from '../domain/gender';

import {
  GENDER_HEADING,
  GENDER_SCOPE,
  PREFERENCE_HEADING,
  PREFERENCE_IS_DURABLE,
  PREFER_NOT_TO_SAY_COST,
  reachNote,
} from './genderPresentation';
import {
  SAVE,
  SAVED,
  WHO_YOU_PLAY_WITH_TITLE,
  YOUR_WEEK_TITLE,
  groupSaveLabel,
  weekLine,
  whoYouPlayWithLine,
} from './youProfilePresentation';

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

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const TWO_SLOTS = weekLine([
  { day: 2, hour: 19 },
  { day: 6, hour: 9 },
]);

/** A signed-in player standing on the You tab, with the profile read in. */
async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  await screen.findByLabelText(doorRowLabel(YOUR_WEEK_TITLE, TWO_SLOTS));
}

const row = (title: string, line: string) => screen.getByLabelText(doorRowLabel(title, line));

const control = (label: string) => screen.getByLabelText(label);
const isSelected = (label: string) => control(label).props.accessibilityState?.selected;
const isDisabled = (label: string) => control(label).props.accessibilityState?.disabled;
const isGreen = (label: string) => fillOf(control(label)) === theme.color.mintInk;

const GENDER_PATH = '/api/v1/players/me/gender';
const PREFERENCE_PATH = '/api/v1/players/me/gender-preference';

const puts = (path: string) => transport.requestsTo('PUT', path);

// ---------------------------------------------------------------------------
// The row
// ---------------------------------------------------------------------------

describe('the row under Finding players', () => {
  it('draws the preference from the read', async () => {
    await onYou();

    expect(row(WHO_YOU_PLAY_WITH_TITLE, whoYouPlayWithLine('any'))).toBeTruthy();
  });

  it('never carries the gender — the row says who the player is matched with, and nothing about them', async () => {
    stubProfileSurface(
      transport,
      profileSurface({ gender: 'WOMAN', gender_preference: 'MEN_ONLY' }),
    );
    await onYou();

    expect(row(WHO_YOU_PLAY_WITH_TITLE, 'Matched with men only')).toBeTruthy();
    // Nowhere on the tab — not the row, not the header card, not a line under any row.
    expect(screen.queryByText('Woman')).toBeNull();
    expect(screen.queryByLabelText(/\bwoman\b/i)).toBeNull();
    expect(screen.queryByText(/\bwoman\b/i)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Who you play with
// ---------------------------------------------------------------------------

describe('Who you play with', () => {
  /** The two *Save*s, as a listener hears them: the visible word and the group it belongs to. */
  const SAVE_ABOUT_YOU = groupSaveLabel(SAVE, GENDER_HEADING);
  const SAVED_ABOUT_YOU = groupSaveLabel(SAVED, GENDER_HEADING);
  const SAVE_PREFERENCE = groupSaveLabel(SAVE, PREFERENCE_HEADING);
  const SAVED_PREFERENCE = groupSaveLabel(SAVED, PREFERENCE_HEADING);

  async function openWhoYouPlayWith(line = whoYouPlayWithLine('any')) {
    await onYou();
    fireEvent.press(row(WHO_YOU_PLAY_WITH_TITLE, line));
    await screen.findByRole('header', { name: WHO_YOU_PLAY_WITH_TITLE });
    await screen.findByLabelText('Anyone');
  }

  it('opens on both answers the profile holds, each group with Saved shut, and none of the step’s scope sentences', async () => {
    await openWhoYouPlayWith();

    expect(screen.getByText(GENDER_HEADING)).toBeTruthy();
    expect(screen.getByText(PREFERENCE_HEADING)).toBeTruthy();
    expect(isSelected('Man')).toBe(true);
    expect(isSelected('Woman')).toBe(false);
    expect(isSelected('Prefer not to say')).toBe(false);
    expect(isSelected('Anyone')).toBe(true);
    expect(isSelected('Women only')).toBe(false);

    expect(SAVED_ABOUT_YOU).toBe('Saved — About you');
    expect(isDisabled(SAVED_ABOUT_YOU)).toBe(true);
    expect(isDisabled(SAVED_PREFERENCE)).toBe(true);
    expect(isGreen(SAVED_ABOUT_YOU)).toBe(true);
    expect(isGreen(SAVED_PREFERENCE)).toBe(true);
    expect(screen.queryByLabelText(SAVE_ABOUT_YOU)).toBeNull();
    expect(screen.queryByLabelText(SAVE_PREFERENCE)).toBeNull();
    expect(screen.queryByLabelText('Continue')).toBeNull();

    // What the step said once, on the way in, is not said again on the way back (ADR-0179 §2).
    expect(screen.queryByText(GENDER_SCOPE)).toBeNull();
    expect(screen.queryByText(PREFERENCE_IS_DURABLE)).toBeNull();
  });

  it('says what narrowing costs at the press, saves that group alone, and the row follows', async () => {
    transport.on('PUT', PREFERENCE_PATH, () => noContent());
    await openWhoYouPlayWith();
    const womenOnly = reachNote(reachOf('women-only')) ?? '';

    expect(screen.queryByText(womenOnly)).toBeNull();
    fireEvent.press(control('Women only'));

    // **The sentence ADR-0096 requires**, on the second surface that takes the value — before
    // the save, not after it.
    expect(screen.getByText(womenOnly)).toBeTruthy();
    expect(isSelected('Women only')).toBe(true);
    expect(isSelected('Anyone')).toBe(false);
    // One Save opened and one still shut: the group about the player has not changed.
    expect(isDisabled(SAVE_PREFERENCE)).toBe(false);
    expect(fillOf(control(SAVE_PREFERENCE))).toBe(theme.color.coralInk);
    expect(isDisabled(SAVED_ABOUT_YOU)).toBe(true);
    expect(isGreen(SAVED_ABOUT_YOU)).toBe(true);
    expect(puts(PREFERENCE_PATH)).toHaveLength(0);

    fireEvent.press(control(SAVE_PREFERENCE));

    await waitFor(() => expect(puts(PREFERENCE_PATH)).toHaveLength(1));
    expect(puts(PREFERENCE_PATH)[0]?.body).toEqual({ gender_preference: 'WOMEN_ONLY' });
    expect(puts(GENDER_PATH)).toHaveLength(0);
    expect(await screen.findByLabelText(SAVED_PREFERENCE)).toBeTruthy();
    expect(isGreen(SAVED_PREFERENCE)).toBe(true);
    expect(screen.getByText(womenOnly)).toBeTruthy();

    fireEvent.press(control('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(WHO_YOU_PLAY_WITH_TITLE, 'Matched with women only'),
      ),
    ).toBeTruthy();
  });

  it('takes the reach sentence away again on Anyone, and never says it for Anyone', async () => {
    stubProfileSurface(transport, profileSurface({ gender_preference: 'MEN_ONLY' }));
    await openWhoYouPlayWith(whoYouPlayWithLine('men-only'));
    const menOnly = reachNote(reachOf('men-only')) ?? '';

    // Opened on a narrowed preference, the cost is said before anything is pressed.
    expect(screen.getByText(menOnly)).toBeTruthy();

    fireEvent.press(control('Anyone'));

    expect(screen.queryByText(menOnly)).toBeNull();
    expect(screen.queryByText(reachNote(reachOf('women-only')) ?? '')).toBeNull();
    expect(isDisabled(SAVE_PREFERENCE)).toBe(false);
  });

  it('saves the answer about the player alone, with the cost line where that answer is not free', async () => {
    transport.on('PUT', GENDER_PATH, () => noContent());
    await openWhoYouPlayWith();

    expect(screen.queryByText(PREFER_NOT_TO_SAY_COST)).toBeNull();
    fireEvent.press(control('Prefer not to say'));
    expect(screen.getByText(PREFER_NOT_TO_SAY_COST)).toBeTruthy();

    fireEvent.press(control(SAVE_ABOUT_YOU));

    await waitFor(() => expect(puts(GENDER_PATH)).toHaveLength(1));
    expect(puts(GENDER_PATH)[0]?.body).toEqual({ gender: 'PREFER_NOT_TO_SAY' });
    expect(puts(PREFERENCE_PATH)).toHaveLength(0);
    expect(await screen.findByLabelText(SAVED_ABOUT_YOU)).toBeTruthy();
    expect(isGreen(SAVED_ABOUT_YOU)).toBe(true);
    expect(isDisabled(SAVED_PREFERENCE)).toBe(true);
    expect(isSelected('Prefer not to say')).toBe(true);

    // The row still says who the player is matched with, and nothing about them.
    fireEvent.press(control('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(WHO_YOU_PLAY_WITH_TITLE, whoYouPlayWithLine('any')),
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/prefer not to say/i)).toBeNull();
  });

  it('pre-selects nothing about a player the question was never put to', async () => {
    // A profile committed before the question existed holds no gender, and the absence is
    // never read as *Prefer not to say* — that is an answer somebody gives.
    const { gender: _neverAsked, ...neverAsked } = PROFILE_SURFACE_SERVED;
    stubProfileSurface(transport, neverAsked);
    await openWhoYouPlayWith();

    for (const label of ['Woman', 'Man', 'Prefer not to say']) {
      expect(isSelected(label)).toBe(false);
    }
    expect(isSelected('Anyone')).toBe(true);
    expect(isDisabled(SAVED_ABOUT_YOU)).toBe(true);
    expect(isDisabled(SAVED_PREFERENCE)).toBe(true);

    fireEvent.press(control('Woman'));
    expect(isDisabled(SAVE_ABOUT_YOU)).toBe(false);
  });

  it('keeps the draft and says why under the group when a save is refused', async () => {
    transport.on('PUT', PREFERENCE_PATH, () => errorResponse(403, 'forbidden'));
    await openWhoYouPlayWith();

    fireEvent.press(control('Men only'));
    fireEvent.press(control(SAVE_PREFERENCE));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(isSelected('Men only')).toBe(true);
    expect(isDisabled(SAVE_PREFERENCE)).toBe(false);
  });
});
