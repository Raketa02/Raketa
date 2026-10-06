/**
 * **The You tab, walked the way a player walks it** — the real route tree, the real bar, and
 * only `fetch` faked ([#296](https://github.com/Raketa02/Raketa/issues/296)).
 *
 * The section exists because a declaration whose only home was the search form kept reading as
 * a search setting. So the assertions are about it being a **fact about the player**: it is
 * listed per rated sport away from any search, an unanswered sport says so, and the write it
 * makes reports the surface it was made on.
 *
 * **What it must not do is asserted in the shell's own suite**, not here: *a declaration
 * changed on You does not move the mode Play opens in* is a fact about two tabs, and the
 * shell is the one feature that may read across that boundary. Nothing in `player_profile`
 * imports Play, in production or in a test.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { declarationOptionLabel } from '@/shared/vocabulary/playIntentPresentation';
import { doorRowLabel } from '@/shared/ui';
import {
  PROFILE_SURFACE_PATH,
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
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { NOT_DECLARED_LINE, playIntentRowLabel } from './playIntentsPresentation';
import {
  KIND_OF_GAME_LINE,
  WHAT_KIND_OF_GAME_TITLE,
  kindOfGameLine,
} from './youProfilePresentation';

function rating(sport: Wire['Sport']): Wire['RatingResponse'] {
  return {
    sport,
    mu: 2.71,
    sigma: 0.62,
    confidence: 28,
    range: { low: 2.09, high: 3.33 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

/** Rated in three, declared in two — so both halves of a row are on screen at once. */
const THREE_RATED = [rating('PADEL'), rating('TENNIS'), rating('SQUASH')];
const DECLARED_IN_TWO = profileSurface({
  weekly_hours: [{ day: 2, hour: 19 }],
  search_radius_km: 12,
  play_intents: { PADEL: 'COMPETITIVE', TENNIS: 'NO_PREFERENCE' },
});

const SQUASH_INTENT = '/api/v1/play-intents/SQUASH';
/** Asserted against the wire union, so a renamed surface is a red build rather than a red test. */
const PROFILE_SCREEN: Wire['PlayIntentSurface'] = 'PROFILE_SCREEN';

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: THREE_RATED, hasPlayerProfile: true });
  stubProfileSurface(transport, DECLARED_IN_TWO);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** What the row on the tab says about the three, as the two reads answer. */
const THE_ROW = doorRowLabel(
  WHAT_KIND_OF_GAME_TITLE,
  kindOfGameLine([
    { sport: 'padel', intent: 'COMPETITIVE' },
    { sport: 'tennis', intent: 'NO_PREFERENCE' },
    { sport: 'squash', intent: undefined },
  ]),
);

/** A signed-in player standing on the You tab. */
async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
}

/** …and through the row to the section behind it (ADR-0179 §2). */
async function openYou() {
  await onYou();
  fireEvent.press(await screen.findByLabelText(THE_ROW));
  await screen.findByText(KIND_OF_GAME_LINE);
  // The line arrives with the screen; the **values** are the profile read, so a declared row
  // is what says the section is finished.
  await screen.findByLabelText(playIntentRowLabel('Padel', 'COMPETITIVE'));
}

const row = (sportName: string, intent: Wire['PlayIntent'] | undefined) =>
  screen.getByLabelText(playIntentRowLabel(sportName, intent));

describe('the play intents on You', () => {
  it('lists one row per rated sport, declared or not', async () => {
    await openYou();

    expect(row('Padel', 'COMPETITIVE')).toBeTruthy();
    expect(row('Tennis', 'NO_PREFERENCE')).toBeTruthy();
    // The first place a player can find out a search there will be refused, before trying one.
    expect(row('Squash', undefined)).toBeTruthy();
    expect(screen.getByText(NOT_DECLARED_LINE)).toBeTruthy();
  });

  /** A rating is what makes a sport matchable, so an unrated one is not a question worth asking. */
  it('says nothing about a sport the player is not rated in', async () => {
    await openYou();

    expect(screen.queryByLabelText(playIntentRowLabel('Badminton', undefined))).toBeNull();
  });

  /**
   * The section's heading and body went (ADR-0179 §9); the one line under the title says the
   * thing they said, and the row on the tab says the three answers before the screen opens.
   */
  it('says the one line under its title, and nothing above the list', async () => {
    await openYou();

    expect(screen.getByText(KIND_OF_GAME_LINE)).toBeTruthy();
    expect(screen.queryByText('What other players see')).toBeNull();
  });

  it('opens the three answers on a row, and writes the one that is pressed', async () => {
    transport.on('PUT', SQUASH_INTENT, () =>
      json<Wire['PlayIntentDeclarationResponse']>({ sport: 'SQUASH', intent: 'FOR_FUN' }),
    );
    await openYou();

    fireEvent.press(row('Squash', undefined));
    fireEvent.press(await screen.findByLabelText(declarationOptionLabel('FOR_FUN', 'Squash')));

    await waitFor(() => expect(transport.requestsTo('PUT', SQUASH_INTENT)).toHaveLength(1));
    expect(transport.requestsTo('PUT', SQUASH_INTENT)[0]?.body).toEqual({
      intent: 'FOR_FUN',
      surface: PROFILE_SCREEN,
    });

    // The row draws the route's answer, and the answers close behind it.
    expect(await screen.findByLabelText(playIntentRowLabel('Squash', 'FOR_FUN'))).toBeTruthy();
    expect(screen.queryByLabelText(declarationOptionLabel('FOR_FUN', 'Squash'))).toBeNull();
  });

  /**
   * **A value nobody has read is not an answer.**
   *
   * The ratings and the profile are two reads and the ratings answer first, so an absent map
   * stood in for *nothing is declared* while the second was in flight — every row said *Not
   * set*, under a sentence telling the player they could not search in any of their sports.
   * *Not set* is the discovery this section exists to make, and a false one inverts it.
   */
  it('draws no answers at all until the read that carries them has landed', async () => {
    // Never resolves: the assertion is about the beat between the two reads.
    transport.on('GET', PROFILE_SURFACE_PATH, () => new Promise<Response>(() => {}));
    await onYou();
    // The row's own line waits for the same read, so it is opened by its title alone.
    fireEvent.press(await screen.findByLabelText(WHAT_KIND_OF_GAME_TITLE));

    await screen.findByText(KIND_OF_GAME_LINE);
    expect(screen.queryByLabelText(playIntentRowLabel('Squash', undefined))).toBeNull();
    expect(screen.queryByText(NOT_DECLARED_LINE)).toBeNull();
  });

  /**
   * And a read that failed says so, rather than saying every sport is unanswered forever.
   *
   * A `403` rather than a `500`, because the app retries a server error twice on a backoff and
   * this assertion is about the state the player is left in, not about how long it took to
   * get there.
   */
  it('says the read failed rather than that nothing is declared', async () => {
    transport.on('GET', PROFILE_SURFACE_PATH, () => errorResponse(403, 'forbidden'));
    await onYou();
    // The row says the read failed, in the recovery sentence, and still opens.
    fireEvent.press(await screen.findByLabelText(WHAT_KIND_OF_GAME_TITLE, { exact: false }));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryByLabelText(playIntentRowLabel('Squash', undefined))).toBeNull();
    expect(screen.queryByText(NOT_DECLARED_LINE)).toBeNull();
  });
});
