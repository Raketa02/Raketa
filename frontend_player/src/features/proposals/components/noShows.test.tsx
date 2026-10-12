/**
 * **Somebody didn't come — marked where the result is entered, disputed by the player marked**
 * ([#560](https://github.com/Raketa02/Raketa/issues/560); the Games & Fill in mechanics §15.3; the
 * backend's #547), walked the way a player walks it: the real route tree and shell, only `fetch`
 * faked.
 *
 * The acceptance criteria are assertions here. A booked game's result entry offers *Kuba didn't
 * come* for each other player — nobody at the club checks anybody in (ADR-0195); the mark goes
 * through a sheet that says what it does, and the screen then reads the report. The player marked
 * finds it on Home, opens the game and says they were there inside their day.
 *
 * The rules are `games`' `noShows.test.ts` and `resultArgument.test.ts`, and the words
 * `gamePresentation.test.ts`; what is asserted here is that the screens are wired to them.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import {
  BARTEK,
  BOOKED_GAME,
  BOOKING,
  INES,
  PIOTR,
  bookedGameOnTheList,
  bookedRoomRow,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import {
  GATE_USER,
  HOME_PATH,
  bookingPath,
  launchSignedIn,
  stubConversations,
  stubGames,
  stubGate,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { HOME_GAME_COPY } from './homeCopy';

const HOME = HOME_GAME_COPY;

/** An hour after the game's end — Saturday 3 October, 18:00 in Warsaw. */
const AFTER = '2026-10-03T16:00:00Z';
/** The report was made at the read; the reported player's day ends 23 hours on. */
const REPORTED_AT = '2026-10-03T15:00:00Z';
const DISPUTE_BY = '2026-10-04T15:00:00Z';

const NO_SHOWS_PATH = `/api/v1/games/${BOOKED_GAME}/no-shows`;
const DISPUTE_PATH = `/api/v1/games/${BOOKED_GAME}/no-shows/dispute`;

const PADEL_RATING: Wire['RatingResponse'] = {
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
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

/** A report of one player, as `GET /games` carries it. */
function noShow(
  playerId: string,
  name: string,
  extra: Partial<Wire['NoShowSchema']> = {},
): Wire['NoShowSchema'] {
  return {
    player_id: playerId,
    name,
    reported_at: REPORTED_AT,
    dispute_by: DISPUTE_BY,
    disputed_at: null,
    ...extra,
  };
}

/** The booked Game, its hour over, as the list reads it — nothing entered unless said. */
function theGame(extra: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return bookedGameOnTheList({ entry_closes_at: '2026-10-06T15:00:00Z', ...extra });
}

/** Land on Home with the game, open its details, and take the result act they offer. */
async function openResult(details: Wire['BookingDetailsResponse'], act: string) {
  stubHomeGames(transport, [
    homeGame({
      status: details.status,
      uncounted_reason: details.uncounted_reason,
      needs_you: details.needs_you,
    }),
  ]);
  stubBooking(transport, details);
  stubConversations(transport, [bookedRoomRow()]);
  await launchSignedIn();

  fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
  fireEvent.press(await screen.findByRole('button', { name: act }));
  await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/result`));
}

// ---------------------------------------------------------------------------
// Marking
// ---------------------------------------------------------------------------

describe('marking somebody who didn’t come, where the result is entered', () => {
  const needsResult = () =>
    bookingDetails({
      status: 'NEEDS_RESULT',
      needs_you: true,
      read_at: AFTER,
      leaving: null,
      shows_forecast: false,
    });

  it('offers it for each other player, and draws nobody as checked in', async () => {
    stubGames(transport, [theGame()], AFTER);
    await openResult(needsResult(), HOME.details.resultAct['we-played']);

    expect(await screen.findByRole('button', { name: 'Piotr Sowa didn’t come' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Inés Díaz didn’t come' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Bartek Lis didn’t come' })).toBeTruthy();
    expect(screen.queryByText(/checked in/)).toBeNull();
    // Never the reader: you are the one person your report proves came.
    expect(screen.queryByRole('button', { name: 'You didn’t come' })).toBeNull();
    // The score is still the screen's: the grid's send stays where it was.
    expect(screen.getByRole('button', { name: /Send this score/ })).toBeTruthy();
  });

  it('asks first, then marks them, and the screen reads the report', async () => {
    stubGames(transport, [theGame()], AFTER);
    transport.on('POST', NO_SHOWS_PATH, () => {
      const reported = theGame({
        standing: 'NO_SHOW_REPORTED',
        entry_closes_at: null,
        no_shows: [noShow(BARTEK, 'Bartek Lis')],
      });
      stubGames(transport, [reported], AFTER);
      return json(reported);
    });
    await openResult(needsResult(), HOME.details.resultAct['we-played']);

    fireEvent.press(await screen.findByRole('button', { name: 'Bartek Lis didn’t come' }));

    const sheet = await screen.findByTestId('bottom-sheet');
    expect(within(sheet).getByRole('header', { name: 'Before you say so' })).toBeTruthy();
    expect(
      within(sheet).getByText(
        'Bartek Lis gets 24 hours to say they were there. If they don’t, it stands — the strongest mark on a record.',
      ),
    ).toBeTruthy();
    expect(transport.requestsTo('POST', NO_SHOWS_PATH)).toHaveLength(0);

    const bookingReads = transport.requestsTo('GET', bookingPath(BOOKING)).length;
    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    fireEvent.press(within(sheet).getByRole('button', { name: 'Bartek Lis didn’t come' }));

    await waitFor(() => expect(transport.requestsTo('POST', NO_SHOWS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', NO_SHOWS_PATH)[0]?.body).toEqual({ player_id: BARTEK });

    expect(await screen.findByText('Bartek Lis was marked as not coming.')).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Somebody didn’t come' })).toBeTruthy();
    expect(screen.getByText('Bartek Lis — 23 hours left to say they were there')).toBeTruthy();
    // A report is the game's entry: the score goes, and the second absentee can still be marked.
    expect(screen.queryByRole('button', { name: /Send this score/ })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Bartek Lis didn’t come' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Piotr Sowa didn’t come' })).toBeTruthy();
    // Home's status and badge, and the details under this screen, are read again.
    await waitFor(() =>
      expect(transport.requestsTo('GET', bookingPath(BOOKING)).length).toBeGreaterThan(
        bookingReads,
      ),
    );
    expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads);
  });

  it('marks nobody when the sheet is put away', async () => {
    stubGames(transport, [theGame()], AFTER);
    await openResult(needsResult(), HOME.details.resultAct['we-played']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa didn’t come' }));
    const sheet = await screen.findByTestId('bottom-sheet');
    fireEvent.press(within(sheet).getByRole('button', { name: 'Don’t mark anybody' }));

    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());
    expect(transport.requestsTo('POST', NO_SHOWS_PATH)).toHaveLength(0);
  });

  it('says why a mark was refused — a score went in meanwhile', async () => {
    stubGames(transport, [theGame()], AFTER);
    transport.on('POST', NO_SHOWS_PATH, () => errorResponse(409, 'a_result_is_entered'));
    await openResult(needsResult(), HOME.details.resultAct['we-played']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa didn’t come' }));
    const sheet = await screen.findByTestId('bottom-sheet');
    fireEvent.press(within(sheet).getByRole('button', { name: 'Piotr Sowa didn’t come' }));

    expect(
      await screen.findByText(
        'A score went in while this screen was open, so the game happened — answer the score instead.',
      ),
    ).toBeTruthy();
  });

  it('clears a refused mark’s sentence once a score goes through instead', async () => {
    stubGames(transport, [theGame()], AFTER);
    transport.on('POST', NO_SHOWS_PATH, () => errorResponse(400, 'not_on_this_court'));
    const RESULT_PATH = `/api/v1/games/${BOOKED_GAME}/result`;
    transport.on('POST', RESULT_PATH, () => json(theGame()));
    await openResult(needsResult(), HOME.details.resultAct['we-played']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa didn’t come' }));
    const sheet = await screen.findByTestId('bottom-sheet');
    fireEvent.press(within(sheet).getByRole('button', { name: 'Piotr Sowa didn’t come' }));
    expect(await screen.findByText('That player isn’t on this game.')).toBeTruthy();

    // They all came after all: 6–4, 6–2, the caret crossing the row and then down.
    for (const figure of ['6', '4', '6', '2']) fireEvent.press(screen.getByLabelText(figure));
    fireEvent.press(screen.getByRole('button', { name: /Send this score/ }));

    await waitFor(() => expect(transport.requestsTo('POST', RESULT_PATH)).toHaveLength(1));
    await waitFor(() => expect(screen.queryByText('That player isn’t on this game.')).toBeNull());
  });
});

/**
 * **Straight onto the result screen**, as the reporter is right after a mark: the details offer no
 * door back to it on an uncounted game, so the screen is reached by its own address.
 */
async function landOnResult(game: Wire['GameSchema']) {
  stubGames(transport, [game], AFTER);
  stubHomeGames(transport, [homeGame({ status: 'UNCOUNTED', uncounted_reason: 'NO_SHOW' })]);
  stubBooking(
    transport,
    bookingDetails({
      status: 'UNCOUNTED',
      uncounted_reason: 'NO_SHOW',
      read_at: AFTER,
      leaving: null,
      shows_forecast: false,
    }),
  );
  stubConversations(transport, [bookedRoomRow()]);
  await launchSignedIn(`/booking/${BOOKING}/result`);
}

describe('while a mark’s day runs, and once it has', () => {
  const bartekMarked = () =>
    theGame({
      standing: 'NO_SHOW_REPORTED',
      entry_closes_at: null,
      no_shows: [noShow(BARTEK, 'Bartek Lis')],
    });

  it('marks the second player who didn’t come to a doubles game, after the first', async () => {
    transport.on('POST', NO_SHOWS_PATH, () => json(bartekMarked()));
    await landOnResult(bartekMarked());

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa didn’t come' }));
    const sheet = await screen.findByTestId('bottom-sheet');
    fireEvent.press(within(sheet).getByRole('button', { name: 'Piotr Sowa didn’t come' }));

    await waitFor(() => expect(transport.requestsTo('POST', NO_SHOWS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', NO_SHOWS_PATH)[0]?.body).toEqual({ player_id: PIOTR });
  });

  it('says a mark came too late, never that the game went unrecorded', async () => {
    transport.on('POST', NO_SHOWS_PATH, () => errorResponse(409, 'the_entry_window_has_closed'));
    await landOnResult(bartekMarked());

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa didn’t come' }));
    const sheet = await screen.findByTestId('bottom-sheet');
    fireEvent.press(within(sheet).getByRole('button', { name: 'Piotr Sowa didn’t come' }));

    expect(
      await screen.findByText('It’s too late to mark anybody else on this game.'),
    ).toBeTruthy();
  });

  it('ends naming who didn’t come once the day has passed, with nobody left to mark', async () => {
    await landOnResult(
      theGame({
        standing: 'NO_SHOW',
        entry_closes_at: null,
        no_shows: [
          noShow(BARTEK, 'Bartek Lis', {
            reported_at: '2026-10-02T15:00:00Z',
            dispute_by: '2026-10-03T15:00:00Z',
          }),
        ],
      }),
    );

    expect(await screen.findByRole('header', { name: 'No result' })).toBeTruthy();
    expect(screen.getByText('Bartek Lis didn’t come.')).toBeTruthy();
    expect(
      screen.getByText(
        'The game didn’t count and no Level moved. Nobody who came is marked for it.',
      ),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: /didn’t come/ })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Disputing
// ---------------------------------------------------------------------------

describe('the player marked says they were there, inside their day', () => {
  const marked = () =>
    bookingDetails({
      status: 'UNCOUNTED',
      uncounted_reason: 'NO_SHOW',
      needs_you: true,
      read_at: AFTER,
      leaving: null,
      shows_forecast: false,
    });
  const reportedMe = () =>
    theGame({
      standing: 'NO_SHOW_REPORTED',
      entry_closes_at: null,
      no_shows: [noShow(GATE_USER.id, GATE_USER.name ?? 'Ada')],
    });

  it('finds it on Home, and on the details the door to answering it', async () => {
    stubGames(transport, [reportedMe()], AFTER);
    await openResult(marked(), HOME.details.resultAct.dispute);

    expect(await screen.findByRole('header', { name: 'Were you there?' })).toBeTruthy();
    expect(screen.getByLabelText(/^23 hours left to say you were there/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'I was there' })).toBeTruthy();
    // Theirs is the dispute: nobody to mark, and no score to enter.
    expect(screen.queryByRole('button', { name: /didn’t come/ })).toBeNull();
    expect(screen.queryByRole('button', { name: /Send this score/ })).toBeNull();
  });

  it('says on Home’s card that they were marked', async () => {
    stubGames(transport, [reportedMe()], AFTER);
    stubHomeGames(transport, [
      homeGame({ status: 'UNCOUNTED', uncounted_reason: 'NO_SHOW', needs_you: true }),
    ]);
    await launchSignedIn();

    const card = await screen.findByTestId(`home-game-${BOOKING}`);
    expect(
      within(card).getByText('You were marked as not coming · say so if you were there'),
    ).toBeTruthy();
  });

  it('disputes it, and the mark is gone', async () => {
    stubGames(transport, [reportedMe()], AFTER);
    transport.on('POST', DISPUTE_PATH, () => {
      const disputed = theGame({
        standing: 'UNSCORED',
        entry_closes_at: null,
        no_shows: [
          noShow(GATE_USER.id, GATE_USER.name ?? 'Ada', { disputed_at: '2026-10-03T16:05:00Z' }),
        ],
      });
      stubGames(transport, [disputed], AFTER);
      return json(disputed);
    });
    await openResult(marked(), HOME.details.resultAct.dispute);

    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    fireEvent.press(await screen.findByRole('button', { name: 'I was there' }));

    await waitFor(() => expect(transport.requestsTo('POST', DISPUTE_PATH)).toHaveLength(1));
    expect(await screen.findByRole('header', { name: 'No result' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'I was there' })).toBeNull();
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads),
    );
  });

  it('says so when their day has passed meanwhile', async () => {
    stubGames(transport, [reportedMe()], AFTER);
    transport.on('POST', DISPUTE_PATH, () => errorResponse(409, 'the_dispute_window_has_closed'));
    await openResult(marked(), HOME.details.resultAct.dispute);

    fireEvent.press(await screen.findByRole('button', { name: 'I was there' }));

    expect(
      await screen.findByText('Your day to say you were there has passed, so the mark stands.'),
    ).toBeTruthy();
  });

  it('offers nobody else the door — the read says it is not theirs', async () => {
    stubGames(transport, [theGame({ standing: 'NO_SHOW_REPORTED', entry_closes_at: null })], AFTER);
    stubHomeGames(transport, [homeGame({ status: 'UNCOUNTED', uncounted_reason: 'NO_SHOW' })]);
    stubBooking(transport, { ...marked(), needs_you: false });
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
    await screen.findByText('Padel · uncounted');
    expect(screen.queryByRole('button', { name: HOME.details.resultAct.dispute })).toBeNull();
    expect(
      screen.getByLabelText('Paid, 28 zł, Somebody didn’t come · no Level moved'),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Every act on a booked game's result re-reads its booking
// ---------------------------------------------------------------------------

/**
 * **Home and the details follow every act on the result screen** — a score agreed as much as a
 * mark (#560): the booking's reads are the composer's, handed to the Game's writes.
 */
describe('an act on a booked game’s result', () => {
  it('re-reads Home and the details once a score is agreed with', async () => {
    const theirs: Wire['StandingProposalSchema'] = {
      side: 'B',
      proposed_by: INES,
      score: {
        sets: [
          { a: 6, b: 4 },
          { a: 6, b: 3 },
        ],
      },
      proposed_at: '2026-10-03T15:30:00Z',
      answer_by: '2026-10-04T15:30:00Z',
    };
    stubGames(
      transport,
      [
        theGame({
          standing: 'AWAITING_ANSWER',
          played_at: '2026-10-03T15:30:00Z',
          entry_closes_at: null,
          proposals: [theirs],
        }),
      ],
      AFTER,
    );
    const ACCEPTANCE_PATH = `/api/v1/games/${BOOKED_GAME}/result/acceptance`;
    transport.on('POST', ACCEPTANCE_PATH, () => json(theGame()));
    await openResult(
      bookingDetails({
        status: 'CONFIRM_THE_RESULT',
        needs_you: true,
        read_at: AFTER,
        leaving: null,
        shows_forecast: false,
      }),
      HOME.details.resultAct.confirm,
    );

    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    const bookingReads = transport.requestsTo('GET', bookingPath(BOOKING)).length;
    fireEvent.press(await screen.findByText('That’s right'));

    await waitFor(() => expect(transport.requestsTo('POST', ACCEPTANCE_PATH)).toHaveLength(1));
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads),
    );
    expect(transport.requestsTo('GET', bookingPath(BOOKING)).length).toBeGreaterThan(bookingReads);
  });
});
