/**
 * **The You tab, walked the way a player walks it** — the real route tree, the real bar, and
 * only `fetch` faked ([#296](https://github.com/Rakieta02/Rakieta/issues/296)).
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

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

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
  play_intents: { PADEL: 'COMPETITIVE', TENNIS: 'NO_PREFERENCE' },
});

const SQUASH_INTENT = '/api/v1/play-intents/SQUASH';
const PADEL_INTENT = '/api/v1/play-intents/PADEL';
const DECK_COUNTS = '/api/v1/players/me/deck-counts';
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

    // Only an answer on a group's Games tab deals its group now (#741, ADR-0201 §4); the jobs deal
    // the groups of an answer given here.
    expect(
      transport.requests.filter(
        (request) => request.method === 'POST' && /\/pools\/[^/]+\/deal$/.test(request.path),
      ),
    ).toEqual([]);
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

/**
 * **What a change costs, said before the tap** (ADR-0201 §6,
 * [#742](https://github.com/Rakieta02/Rakieta/issues/742)): opening a declared sport reads its cards
 * across the groups, and each answer that would change something says what it does to them.
 */
describe('what an answer costs, on You', () => {
  /** Ania's padel: seven competitive cards across her groups, Tennis three, Squash one for fun. */
  const COUNTS: Readonly<Record<string, Wire['DeckCountsResponse']>> = {
    PADEL: { sport: 'PADEL', competitive: 7, for_fun: 0 },
    TENNIS: { sport: 'TENNIS', competitive: 3, for_fun: 0 },
    SQUASH: { sport: 'SQUASH', competitive: 0, for_fun: 1 },
  };

  beforeEach(() => {
    transport.on('GET', DECK_COUNTS, (request) => {
      const sport = new URLSearchParams(request.path.split('?')[1]).get('sport') ?? '';
      const counts = COUNTS[sport];
      return counts === undefined ? errorResponse(404, 'not_found') : json(counts);
    });
  });

  /** One answer's button and whatever is said under it. */
  const answer = (intent: Wire['PlayIntent']) => within(screen.getByTestId(`answer-${intent}`));

  /** The two kinds of line, so an answer with none can be asserted to say neither. */
  const ANY_COST = /in your groups|ones too|stops dealing/;

  it('reads the open sport’s cards across the groups, once, on opening it', async () => {
    await openYou();
    expect(transport.requestsTo('GET', DECK_COUNTS)).toEqual([]);

    fireEvent.press(row('Padel', 'COMPETITIVE'));

    await waitFor(() => expect(transport.requestsTo('GET', DECK_COUNTS)).toHaveLength(1));
    expect(transport.requestsTo('GET', DECK_COUNTS)[0]?.path).toBe(`${DECK_COUNTS}?sport=PADEL`);
  });

  it('says what each change costs a Competitive player, and nothing on Competitive', async () => {
    await openYou();
    fireEvent.press(row('Padel', 'COMPETITIVE'));

    const goes = 'Your 7 competitive cards in your groups go. Games you’re In on stay.';
    expect(await answer('FOR_FUN').findByText(goes)).toBeTruthy();
    expect(
      answer('NO_PREFERENCE').getByText('Keep your competitive cards and get for-fun ones too.'),
    ).toBeTruthy();
    expect(answer('COMPETITIVE').queryByText(ANY_COST)).toBeNull();
  });

  it('says what each change costs a For fun player, one card in the singular', async () => {
    stubProfileSurface(
      transport,
      profileSurface({
        weekly_hours: [{ day: 2, hour: 19 }],
        play_intents: { PADEL: 'COMPETITIVE', TENNIS: 'NO_PREFERENCE', SQUASH: 'FOR_FUN' },
      }),
    );
    await onYou();
    fireEvent.press(await screen.findByLabelText(WHAT_KIND_OF_GAME_TITLE, { exact: false }));
    fireEvent.press(await screen.findByLabelText(playIntentRowLabel('Squash', 'FOR_FUN')));

    const goes = 'Your 1 for-fun card in your groups goes. Games you’re In on stay.';
    expect(await answer('COMPETITIVE').findByText(goes)).toBeTruthy();
    expect(
      answer('NO_PREFERENCE').getByText('Keep your for-fun cards and get competitive ones too.'),
    ).toBeTruthy();
    expect(answer('FOR_FUN').queryByText(ANY_COST)).toBeNull();
  });

  /** From *Either suits me* the count is the kind that goes; a kind with no cards loses its number. */
  it('says what each narrowing costs an Either suits me player, zero without a number', async () => {
    await openYou();
    fireEvent.press(row('Tennis', 'NO_PREFERENCE'));

    const goes = 'Your 3 competitive cards in your groups go. Games you’re In on stay.';
    expect(await answer('FOR_FUN').findByText(goes)).toBeTruthy();
    expect(
      answer('COMPETITIVE').getByText(
        'Rakieta stops dealing you for-fun games. Games you’re In on stay.',
      ),
    ).toBeTruthy();
    expect(answer('NO_PREFERENCE').queryByText(ANY_COST)).toBeNull();
  });

  it('says nothing under the answers of a sport with no answer yet, and keeps its footnote', async () => {
    await openYou();
    fireEvent.press(row('Squash', undefined));

    await screen.findByLabelText(declarationOptionLabel('FOR_FUN', 'Squash'));
    expect(screen.queryByText(ANY_COST)).toBeNull();
    expect(screen.getByText(NOT_DECLARED_LINE)).toBeTruthy();
    expect(transport.requestsTo('GET', DECK_COUNTS)).toEqual([]);
  });

  /**
   * A count not in hand is not zero, so the lines keep their shape and lose only the number — and
   * the answers still answer.
   */
  it('draws the lines without a number while the count is on its way, and a press still works', async () => {
    transport.on('GET', DECK_COUNTS, () => new Promise<Response>(() => {}));
    transport.on('PUT', PADEL_INTENT, () =>
      json<Wire['PlayIntentDeclarationResponse']>({ sport: 'PADEL', intent: 'FOR_FUN' }),
    );
    await openYou();
    fireEvent.press(row('Padel', 'COMPETITIVE'));

    expect(
      await answer('FOR_FUN').findByText(
        'Your competitive cards in your groups go. Games you’re In on stay.',
      ),
    ).toBeTruthy();
    expect(
      answer('NO_PREFERENCE').getByText('Keep your competitive cards and get for-fun ones too.'),
    ).toBeTruthy();

    fireEvent.press(screen.getByLabelText(declarationOptionLabel('FOR_FUN', 'Padel')));

    await waitFor(() => expect(transport.requestsTo('PUT', PADEL_INTENT)).toHaveLength(1));
    expect(transport.requestsTo('PUT', PADEL_INTENT)[0]?.body).toEqual({
      intent: 'FOR_FUN',
      surface: PROFILE_SCREEN,
    });
    expect(await screen.findByLabelText(playIntentRowLabel('Padel', 'FOR_FUN'))).toBeTruthy();
  });

  /** A `403`, so the app's retries on a server error don't stand between the read and the line. */
  it('draws the lines without a number when the count could not be read', async () => {
    transport.on('GET', DECK_COUNTS, () => errorResponse(403, 'forbidden'));
    await openYou();
    fireEvent.press(row('Padel', 'COMPETITIVE'));

    await waitFor(() => expect(transport.requestsTo('GET', DECK_COUNTS)).toHaveLength(1));
    expect(
      await answer('FOR_FUN').findByText(
        'Your competitive cards in your groups go. Games you’re In on stay.',
      ),
    ).toBeTruthy();
    // The count's failure is not the player's to act on: the lines are the whole of what it costs.
    expect(screen.queryByRole('alert')).toBeNull();
  });

  /**
   * **A count is as old as the opening that read it.** Between two openings the jobs deal, the deck
   * is answered and the group page's door changes the intent, none of it seen here — so a second
   * opening says no number until its own read lands, and never the first opening's.
   */
  it('draws no number from an earlier opening while the row reads again', async () => {
    await openYou();
    fireEvent.press(row('Padel', 'COMPETITIVE'));
    await answer('FOR_FUN').findByText(
      'Your 7 competitive cards in your groups go. Games you’re In on stay.',
    );
    fireEvent.press(row('Padel', 'COMPETITIVE'));
    expect(screen.queryByTestId('answer-FOR_FUN')).toBeNull();
    // The router harness runs fake timers, so the tick a finger takes to come back is stepped.
    act(() => jest.advanceTimersByTime(0));

    transport.on('GET', DECK_COUNTS, () => new Promise<Response>(() => {}));
    fireEvent.press(row('Padel', 'COMPETITIVE'));

    expect(
      await answer('FOR_FUN').findByText(
        'Your competitive cards in your groups go. Games you’re In on stay.',
      ),
    ).toBeTruthy();
    expect(transport.requestsTo('GET', DECK_COUNTS)).toHaveLength(2);
  });

  /**
   * **A count from before a change is never drawn after it** — the change took the player off the
   * dropped kind's cards, so the next opening reads again and says no number until it lands.
   */
  it('reads the count again after a change, drawing none from before it', async () => {
    transport.on('PUT', PADEL_INTENT, () =>
      json<Wire['PlayIntentDeclarationResponse']>({ sport: 'PADEL', intent: 'NO_PREFERENCE' }),
    );
    await openYou();
    fireEvent.press(row('Padel', 'COMPETITIVE'));
    await answer('FOR_FUN').findByText(
      'Your 7 competitive cards in your groups go. Games you’re In on stay.',
    );

    fireEvent.press(screen.getByLabelText(declarationOptionLabel('NO_PREFERENCE', 'Padel')));
    const nowEither = await screen.findByLabelText(playIntentRowLabel('Padel', 'NO_PREFERENCE'));
    // The change reads nothing by itself, and the count closes with the row it was read for.
    expect(transport.requestsTo('GET', DECK_COUNTS)).toHaveLength(1);

    transport.on('GET', DECK_COUNTS, () => new Promise<Response>(() => {}));
    fireEvent.press(nowEither);

    expect(
      await answer('FOR_FUN').findByText(
        'Your competitive cards in your groups go. Games you’re In on stay.',
      ),
    ).toBeTruthy();
    expect(transport.requestsTo('GET', DECK_COUNTS)).toHaveLength(2);
  });
});
