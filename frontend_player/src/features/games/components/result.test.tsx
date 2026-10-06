/**
 * **The result argument, walked the way a player walks it**: the real route tree, the real
 * shell, and only `fetch` faked — on a booked game's result screen (`/booking/[id]/result`, #556),
 * which is where *We played* on the details leads. It walked the old loop's `/games/[id]` until that
 * route was removed ([#576](https://github.com/Raketa02/Raketa/issues/576)); the screen is the same
 * one, on its score lead.
 *
 * Four of the ticket's acceptance criteria are assertions in this file and not opinions
 * anywhere else — a player can enter, correct, agree and disagree; every refusal the aggregate
 * makes has a screen state; silence confirming is visible **before** it happens; and an unscored
 * game reads as an evening rather than as an error. The fifth is a compile error and a lint
 * rule, which is where label coverage belongs.
 *
 * The suite asserts against the **copy deck** rather than against strings, because the wording
 * is the deck's to change and the rules are not.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { AppError } from '@/shared/errors';

import type { ResultArgument } from '../domain/resultArgument';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';
import { BOOKING, bookingDetails, homeGame, stubBooking, stubHomeGames } from '@/test-support/home';
import {
  GAMES_PATH,
  GATE_USER,
  launchSignedIn,
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

import {
  ACCEPT_LABEL,
  CALLED_OFF_FOR_LACK_OF_PLAYERS,
  CANCEL_LABEL,
  COUNTER_IS_THEIR_SCORE,
  COUNTER_LABEL,
  CORRECT_LABEL,
  ENTER_LABEL,
  NOT_YOURS_LINE,
  STILL_ON_THE_TABLE,
  UNSCORED_FACTS,
  YOURS,
  clockLine,
  resultBody,
  resultTitle,
  scoreProblemLine,
  standingLine,
  submitLabel,
} from './gamePresentation';
import { gameErrorMessage } from './gameErrorMessage';

const GAME_ID = '8f14e45f-ceea-467a-9dd1-4bd9c39d4a58';
const BOOKING_ID = 'cccccccc-0000-4000-8000-000000000003';
const RESULT_PATH = `${GAMES_PATH}/${GAME_ID}/result`;
const ACCEPTANCE_PATH = `${RESULT_PATH}/acceptance`;

const READ_AT = '2026-09-05T09:00:00Z';
const ME = GATE_USER.id;
const OPPONENT = 'bbbbbbbb-0000-4000-8000-000000000002';

/** What the opponent's seat is called, and the one handle these screens ever print. */
const THEIR_HANDLE = 'tomek.p';

/** A singles padel game with me on side A. Singles, so the column heads are *You* and *Them*. */
function game(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: GAME_ID,
    challenge_id: BOOKING_ID,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: '2026-09-01T09:00:00Z',
    entry_closes_at: '2026-09-09T09:00:00Z',
    seats: [
      { side: 'A', player_id: ME, name: 'me_' },
      { side: 'B', player_id: OPPONENT, name: THEIR_HANDLE },
    ],
    proposals: [],
    no_shows: [],
    ...over,
  };
}

const SCORE: Wire['ScoreSchema'] = {
  sets: [
    { a: 6, b: 4 },
    { a: 6, b: 2 },
  ],
};

/** A score on the table from one side, with the two deadlines the screens read. */
function proposal(side: 'A' | 'B'): Wire['StandingProposalSchema'] {
  return {
    side,
    proposed_by: side === 'A' ? ME : OPPONENT,
    score: SCORE,
    proposed_at: '2026-09-04T20:00:00Z',
    answer_by: '2026-09-06T08:00:00Z',
    settles_at: '2026-09-05T15:00:00Z',
  };
}

/** The other side's answer to it — one digit apart, which is what a real disagreement is. */
const COUNTER_SCORE: Wire['ScoreSchema'] = {
  sets: [
    { a: 6, b: 4 },
    { a: 4, b: 6 },
  ],
};

/** A played game with one score waiting on an answer. */
function awaitingAnswer(side: 'A' | 'B'): Wire['GameSchema'] {
  return game({
    standing: 'AWAITING_ANSWER',
    played_at: '2026-09-04T20:00:00Z',
    entry_closes_at: null,
    proposals: [proposal(side)],
  });
}

/** Both scores on the table — side A's first, which is the order the server sends them in. */
function disagreement(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return game({
    standing: 'AWAITING_ANSWER',
    played_at: '2026-09-04T20:00:00Z',
    entry_closes_at: null,
    proposals: [proposal('A'), { ...proposal('B'), score: COUNTER_SCORE }],
    ...over,
  });
}

/** A played game with one score up and an agreement waiting out its grace. */
function agreedWith(side: 'A' | 'B'): Wire['GameSchema'] {
  return game({
    standing: 'AWAITING_ANSWER',
    played_at: '2026-09-04T20:00:00Z',
    entry_closes_at: null,
    proposals: [proposal(side)],
    acceptance: {
      agreed_by: side === 'A' ? OPPONENT : ME,
      of_side: side,
      agreed_at: '2026-09-04T21:00:00Z',
      settles_at: '2026-09-05T15:00:00Z',
    },
  });
}

/** One rating, because the entry gate sends an unrated player to onboarding rather than Now. */
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
});

/** Where the booked game's result screen is — the one route this screen is mounted at. */
const RESULT_ROUTE = `/booking/${BOOKING}/result`;

/**
 * Land on a booked game's result screen, with this Game behind the booking.
 *
 * `GameScreen` is state-keyed — the arm is the standing's wherever it is entered from — so what
 * this file is about is the screen's states, entered at the route that mounts it.
 */
async function openGame(served: Wire['GameSchema']) {
  stubHomeGames(transport, [homeGame({ game_id: GAME_ID })]);
  stubBooking(transport, bookingDetails({ game_id: GAME_ID }));
  stubGames(transport, [served], READ_AT);
  await launchSignedIn(RESULT_ROUTE);
  await waitFor(() => expect(screen).toHavePathname(RESULT_ROUTE));
  // The booking is read first and the Game after it, and the screen wears *Not your game*'s
  // title while the Game is still coming — so what is waited on is that title going.
  await screen.findByLabelText('Back');
  await waitFor(() => expect(screen.queryByText(resultTitle({ kind: 'not-yours' }))).toBeNull());
}

/**
 * **The grid is the screen on an entry arm**: a booked game's result leads with the score, so
 * there is nothing behind the grid and no cancel is drawn.
 */
describe('the grid on an entry arm', () => {
  it('is the screen itself, so nothing closes it', async () => {
    await openGame(game());

    expect(screen.getByText(ENTER_LABEL)).toBeTruthy();
    expect(screen.queryByText(WE_PLAYED)).toBeNull();
    expect(screen.queryByText(CANCEL_LABEL)).toBeNull();
  });
});

/** Press one value key on the pad, into whichever cell the caret is on. */
function type(figure: string) {
  fireEvent.press(screen.getByLabelText(figure));
}

/** Fill the grid with a score, in the reader's own order: mine first, then theirs. */
function fillIn(sets: readonly (readonly [string, string])[], sides: readonly [string, string]) {
  sets.forEach(([mine, theirs], index) => {
    fireEvent.press(screen.getByLabelText(`Set ${index + 1}, ${sides[0]}, empty`));
    type(mine);
    fireEvent.press(screen.getByLabelText(`Set ${index + 1}, ${sides[1]}, empty`));
    type(theirs);
  });
}

const bodies = (path: string) => transport.requestsTo('POST', path).map((request) => request.body);

/** The refusal the screen will have mapped, so the suite asserts on the sentence for a code. */
const refusal = (code: string) =>
  new AppError('conflict', 'business-conflict', 'test failure', { code });

describe('entering a result', () => {
  it('says when saying nothing stops being possible, before the clock runs', async () => {
    await openGame(game());

    const said = standingLine(
      { kind: 'awaiting-entry', entryClosesAt: '2026-09-09T09:00:00Z', seatOpen: false },
      READ_AT,
    );

    expect(screen.getByText(said)).toBeTruthy();
    // Four days, from the read to the entry's close.
    expect(said).toContain('4 days');
  });

  it('sends the score absolutely, with no act named on it', async () => {
    transport.on('POST', RESULT_PATH, () => json(game()));
    await openGame(game());

    fillIn(
      [
        ['6', '4'],
        ['6', '2'],
      ],
      ['You', 'Them'],
    );
    fireEvent.press(screen.getByText(ENTER_LABEL));

    // `a` is side A's and side A is mine, so this is the same score the grid drew — and the
    // body carries no word for which of the three acts the record will read it as.
    await waitFor(() => expect(bodies(RESULT_PATH)).toEqual([{ score: SCORE }]));
  });

  it('refuses a level set with a sentence rather than a closed control', async () => {
    await openGame(game());

    fillIn([['6', '6']], ['You', 'Them']);
    fireEvent.press(screen.getByText(ENTER_LABEL));

    expect(screen.getByText(scoreProblemLine({ code: 'level-set', set: 1 }, 'padel'))).toBeTruthy();
    expect(bodies(RESULT_PATH)).toEqual([]);
  });

  it('refuses a score that names nobody, which is the invariant and not a sanity check', async () => {
    await openGame(game());

    fillIn(
      [
        ['6', '4'],
        ['3', '6'],
      ],
      ['You', 'Them'],
    );
    fireEvent.press(screen.getByText(ENTER_LABEL));

    expect(screen.getByText(scoreProblemLine({ code: 'no-winner' }, 'padel'))).toBeTruthy();
    expect(bodies(RESULT_PATH)).toEqual([]);
  });
});

describe('correcting your own side’s score', () => {
  it('offers a change rather than a second turn, and says silence will confirm it', async () => {
    await openGame(awaitingAnswer('A'));

    expect(screen.getByText(resultTitle({ kind: 'ours-stands', proposal: PROPOSAL }))).toBeTruthy();
    expect(screen.getByText(/If nobody answers within 23 hours/)).toBeTruthy();
    expect(screen.getByText(CORRECT_LABEL)).toBeTruthy();
    // The one thing the screen must never offer the proposing side.
    expect(screen.queryByText(ACCEPT_LABEL)).toBeNull();
  });

  /**
   * The clock is the prototype's, and it is the whole of *silence confirming has to be visible
   * before it happens*: a figure to read at arm's length, and the sentence under it.
   */
  it('draws the clock as one spoken statement rather than a figure beside prose', async () => {
    await openGame(awaitingAnswer('A'));

    const clock = clockLine({ kind: 'ours-stands', proposal: PROPOSAL }, READ_AT)!;

    expect(screen.getByLabelText(`${clock.figure} ${clock.line}`)).toBeTruthy();
  });

  it('opens the grid on the score already up, so a typo is one digit', async () => {
    transport.on('POST', RESULT_PATH, () => json(awaitingAnswer('A')));
    await openGame(awaitingAnswer('A'));

    fireEvent.press(screen.getByText(CORRECT_LABEL));

    // Pre-loaded: the second set reads 6-2 before anything is typed.
    fireEvent.press(screen.getByLabelText('Set 2, Them, 2'));
    fireEvent.press(screen.getByLabelText('Rub out'));
    type('3');
    fireEvent.press(screen.getByText(submitLabel('correct')));

    await waitFor(() =>
      expect(bodies(RESULT_PATH)).toEqual([
        {
          score: {
            sets: [
              { a: 6, b: 4 },
              { a: 6, b: 3 },
            ],
          },
        },
      ]),
    );
  });

  it('can be backed out of without sending anything', async () => {
    await openGame(awaitingAnswer('A'));

    fireEvent.press(screen.getByText(CORRECT_LABEL));
    fireEvent.press(screen.getByText(CANCEL_LABEL));

    expect(screen.getByText(CORRECT_LABEL)).toBeTruthy();
    expect(bodies(RESULT_PATH)).toEqual([]);
  });
});

describe('answering the other side’s score', () => {
  it('offers agreeing and disagreeing, and never a bare rejection', async () => {
    await openGame(awaitingAnswer('B'));

    expect(screen.getByText(ACCEPT_LABEL)).toBeTruthy();
    expect(screen.getByText(COUNTER_LABEL)).toBeTruthy();
    expect(screen.queryByText(CORRECT_LABEL)).toBeNull();
  });

  /**
   * Variant C's own arrangement, and the thing it said only a route had room for: the score
   * being answered stays on screen beside the one being typed.
   */
  it('keeps their score on screen beside the one being typed', async () => {
    await openGame(awaitingAnswer('B'));

    fireEvent.press(screen.getByText(COUNTER_LABEL));

    expect(screen.getByText(STILL_ON_THE_TABLE)).toBeTruthy();
    expect(screen.getByText(YOURS)).toBeTruthy();
  });

  /**
   * **The agreement is read back rather than remembered.** It was drawn from `accept.isSuccess`,
   * so it was visible to the person who tapped, in that mount, and to nobody else — the response
   * carries it now, and this asserts the re-read rather than the tap.
   */
  it('agrees across the net, and says when that becomes final', async () => {
    transport.on('POST', ACCEPTANCE_PATH, () => {
      stubGames(transport, [agreedWith('B')], READ_AT);
      return json(agreedWith('B'));
    });
    await openGame(awaitingAnswer('B'));

    fireEvent.press(screen.getByText(ACCEPT_LABEL));

    await screen.findByText(standingLine(AGREED_WITH_THEIRS, READ_AT));
    expect(transport.requestsTo('POST', ACCEPTANCE_PATH)).toHaveLength(1);
    // The grace runs from the score, so a disagreement still wins inside it — and the control
    // for one is still there.
    expect(screen.getByText(COUNTER_LABEL)).toBeTruthy();
    // A second agreement is what the aggregate refuses with `the_result_is_already_accepted`.
    expect(screen.queryByText(ACCEPT_LABEL)).toBeNull();
  });

  it('disagrees with a score, because there is no rejection without one', async () => {
    transport.on('POST', RESULT_PATH, () => json(awaitingAnswer('B')));
    await openGame(awaitingAnswer('B'));

    fireEvent.press(screen.getByText(COUNTER_LABEL));
    fireEvent.press(screen.getByLabelText('Set 2, Them, 2'));
    fireEvent.press(screen.getByLabelText('Rub out'));
    type('4');
    fireEvent.press(screen.getByText(submitLabel('counter')));

    await waitFor(() =>
      expect(bodies(RESULT_PATH)).toEqual([
        {
          score: {
            sets: [
              { a: 6, b: 4 },
              { a: 6, b: 4 },
            ],
          },
        },
      ]),
    );
  });

  /**
   * The trap the pre-load creates: an unchanged counter is a second proposal that **agrees**
   * with the first, and two matching scores nobody accepts still leave the game unscored. It is
   * refused here rather than paid for a day later.
   */
  it('refuses a counter that is the score it is answering', async () => {
    await openGame(awaitingAnswer('B'));

    fireEvent.press(screen.getByText(COUNTER_LABEL));
    fireEvent.press(screen.getByText(submitLabel('counter')));

    expect(screen.getByText(COUNTER_IS_THEIR_SCORE)).toBeTruthy();
    expect(bodies(RESULT_PATH)).toEqual([]);
  });
});

describe('the score-entry instrument, which is the prototype’s', () => {
  /**
   * The `+` key is what makes the pad's range a statement about the common case rather than a
   * ruling: a padel third set is often a ten-point tie-break, and the pad stops at 7.
   */
  it('counts past its own ceiling rather than refusing a real evening', async () => {
    transport.on('POST', RESULT_PATH, () => json(game()));
    await openGame(game());

    fillIn(
      [
        ['6', '4'],
        ['3', '6'],
      ],
      ['You', 'Them'],
    );
    fireEvent.press(screen.getByLabelText('Set 3, You, empty'));
    // 8, then 9, then 10 — the key keeps counting where the pad's own face stops.
    for (let press = 0; press < 3; press += 1) fireEvent.press(screen.getByLabelText('Higher'));
    // And the pad's own face stops at 7, so the other side of a ten-point tie-break is a value
    // key and this one is not — which is exactly the range the `+` key exists to reach past.
    fireEvent.press(screen.getByLabelText('Set 3, Them, empty'));
    type('7');
    fireEvent.press(screen.getByText(ENTER_LABEL));

    await waitFor(() =>
      expect(bodies(RESULT_PATH)).toEqual([
        {
          score: {
            sets: [
              { a: 6, b: 4 },
              { a: 3, b: 6 },
              { a: 10, b: 7 },
            ],
          },
        },
      ]),
    );
  });

  it('moves the caret across the row and then down, so a score is four taps', async () => {
    await openGame(game());

    type('6');

    // The caret left the cell it filled and crossed to the other side of the same set.
    expect(screen.getByLabelText('Set 1, You, 6')).toBeTruthy();
    type('4');
    expect(screen.getByLabelText('Set 1, Them, 4')).toBeTruthy();
    type('6');
    expect(screen.getByLabelText('Set 2, You, 6')).toBeTruthy();
  });

  it('draws the sport’s own grid, in the sport’s own word for a row', async () => {
    await openGame(game({ sport: 'SQUASH' }));

    expect(screen.getByLabelText('Game 5, You, empty')).toBeTruthy();
    expect(screen.queryByLabelText('Set 1, You, empty')).toBeNull();
  });
});

describe('the ends', () => {
  it('reads an unscored game as an evening and offers nothing', async () => {
    await openGame(
      game({ standing: 'UNSCORED', played_at: '2026-09-04T20:00:00Z', entry_closes_at: null }),
    );

    expect(screen.getByText(resultBody({ kind: 'unscored' })!)).toBeTruthy();
    // Variant C's fact list: an account of what the evening still is, not an apology.
    for (const fact of UNSCORED_FACTS) expect(screen.getByText(fact)).toBeTruthy();
    expect(screen.queryByText(ENTER_LABEL)).toBeNull();
    expect(screen.queryByText(ACCEPT_LABEL)).toBeNull();
  });

  /**
   * **The fourth end, drawn as the ghost is** (#419 §3, ADR-0163): the title and the standing
   * line the ticket fixes, the ghost's own body — nothing anybody is measured on moves — and
   * nothing to press: no doors, no act on the court, and no pairing asked for, because
   * the read is `enabled` on `AWAITING_ENTRY` alone and answers `pairing_is_history` anyway.
   * With `called_off_by` null it is the hour's (ADR-0175 §3), and the body says so.
   */
  it('reads a called-off game as its fourth end and offers nothing', async () => {
    await openGame(
      game({
        standing: 'CALLED_OFF',
        entry_closes_at: null,
        called_off_at: '2026-09-04T20:00:00Z',
      }),
    );

    const ending = { how: 'the-hour', format: 'singles' } as const;
    expect(screen.getByText(resultTitle({ kind: 'called-off', ending }))).toBeTruthy();
    expect(screen.getByText(standingLine({ kind: 'called-off', ending }, READ_AT))).toBeTruthy();
    expect(screen.getByText(resultBody({ kind: 'called-off', ending })!)).toBeTruthy();
    expect(screen.queryByText(WE_PLAYED)).toBeNull();
    expect(screen.queryByText(ENTER_LABEL)).toBeNull();
    expect(screen.queryByText(/Open the chat/)).toBeNull();
    expect(screen.queryByText(/Leave this game|Call it off|Fill the seat/)).toBeNull();
    expect(screen.queryByText(/The plan/)).toBeNull();
    expect(transport.requestsTo('GET', `${GAMES_PATH}/${GAME_ID}/pairing`)).toEqual([]);
  });

  /**
   * **The ending block, keyed by how it ended** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
   * §8): a departure is told from a press by whether `called_off_by` still holds a seat, and the
   * heading and body follow — the shortage and who left on a singles and on a doubles, the
   * presser's name on the button's, and *You* where the reader pressed it.
   */
  describe('the called-off ending block', () => {
    const PARTNER = 'cccccccc-0000-4000-8000-000000000004';
    const tomek = { kind: 'player', name: THEIR_HANDLE } as const;
    const calledOff = (
      seats: Wire['GameSchema']['seats'],
      by: Wire['CalledOffBySchema'],
    ): Wire['GameSchema'] =>
      game({
        standing: 'CALLED_OFF',
        entry_closes_at: null,
        called_off_at: '2026-09-04T20:00:00Z',
        called_off_by: by,
        seats,
      });

    it('says a singles game was called off for lack of players, and that the opponent left', async () => {
      await openGame(
        calledOff(
          [
            { side: 'A', player_id: ME, name: 'me_' },
            { side: 'B', player_id: null, name: null },
          ],
          { player_id: OPPONENT, name: THEIR_HANDLE },
        ),
      );

      const ending = { by: tomek, how: 'departure', format: 'singles' } as const;
      expect(screen.getByText(resultTitle({ kind: 'called-off', ending }))).toBeTruthy();
      expect(screen.getByText(resultBody({ kind: 'called-off', ending })!)).toBeTruthy();
      expect(screen.getByText(standingLine({ kind: 'called-off', ending }, READ_AT))).toBeTruthy();
    });

    it('says a doubles game was called off for lack of players, and who was the last to leave', async () => {
      await openGame(
        calledOff(
          [
            { side: 'A', player_id: ME, name: 'me_' },
            { side: 'A', player_id: null, name: null },
            { side: 'B', player_id: null, name: null },
            { side: 'B', player_id: null, name: null },
          ],
          { player_id: OPPONENT, name: THEIR_HANDLE },
        ),
      );

      const ending = { by: tomek, how: 'departure', format: 'doubles' } as const;
      expect(screen.getByText(resultTitle({ kind: 'called-off', ending }))).toBeTruthy();
      expect(screen.getByText(resultBody({ kind: 'called-off', ending })!)).toBeTruthy();
    });

    /**
     * **Whoever `called_off_by` names, the heading is the shortage's** (ADR-0175 §1): nobody
     * presses a call-off any more, and a record naming somebody still seated — written while
     * somebody could — folds as a departure by the person it names.
     */
    it('never heads the ending with a presser', async () => {
      const court: Wire['GameSchema']['seats'] = [
        { side: 'A', player_id: ME, name: 'me_' },
        { side: 'A', player_id: PARTNER, name: 'kasia_w' },
        { side: 'B', player_id: OPPONENT, name: THEIR_HANDLE },
        { side: 'B', player_id: null, name: null },
      ];
      await openGame(calledOff(court, { player_id: OPPONENT, name: THEIR_HANDLE }));

      expect(screen.getByText(CALLED_OFF_FOR_LACK_OF_PLAYERS)).toBeTruthy();
      expect(screen.queryByText(/called the game off/)).toBeNull();
    });
  });

  it('draws a confirmed result with both sides named, and nothing to press', async () => {
    await openGame(
      game({
        standing: 'CONFIRMED',
        played_at: '2026-09-04T20:00:00Z',
        entry_closes_at: null,
        score: SCORE,
        outcome: 'WIN',
      }),
    );

    expect(screen.getByLabelText(/^The agreed score\. Set 1, You 6, Them 4/)).toBeTruthy();
    expect(screen.getByText('You won.')).toBeTruthy();
    expect(screen.queryByText(ENTER_LABEL)).toBeNull();
  });
});

describe('a disagreement, which used to cross with neither score on it', () => {
  /**
   * Both scores travel now, so a reader can see what is being argued about — and *"the client
   * could offer the act only by asking somebody to agree with a score it cannot show them"*
   * stops being true ([#317](https://github.com/Raketa02/Raketa/issues/317)).
   */
  it('draws both scores, the reader’s own side first in each', async () => {
    await openGame(disagreement());

    expect(
      screen.getByLabelText('Your score. Set 1, You 6, Them 4. Set 2, You 6, Them 2'),
    ).toBeTruthy();
    expect(
      screen.getByLabelText('Their score. Set 1, You 6, Them 4. Set 2, You 4, Them 6'),
    ).toBeTruthy();
  });

  /**
   * ADR-0137 §4's only end short of the game going unscored, offered at last — and **named for
   * the score it agrees with**, because *That's right* is true of every game ever played.
   */
  it('offers agreeing with the other side’s score, and never a second one of our own', async () => {
    transport.on('POST', ACCEPTANCE_PATH, () => json(disagreement()));
    await openGame(disagreement());

    expect(
      screen.getByLabelText(`${ACCEPT_LABEL}. Set 1, You 6, Them 4. Set 2, You 4, Them 6`),
    ).toBeTruthy();
    // This side has had its one turn, which is what bounds the argument to two rounds.
    expect(screen.queryByText(COUNTER_LABEL)).toBeNull();
    expect(screen.queryByText(CORRECT_LABEL)).toBeNull();

    fireEvent.press(screen.getByText(ACCEPT_LABEL));

    await waitFor(() => expect(transport.requestsTo('POST', ACCEPTANCE_PATH)).toHaveLength(1));
  });

  it('names the way out rather than stating an ending as though it were the only one', async () => {
    await openGame(disagreement());

    // Against the deck rather than against a string: what this suite is for is that the
    // disagreement's own paragraph is the one on screen. `gamePresentation.test.ts` is where
    // what that paragraph has to say is held.
    expect(
      screen.getByText(resultBody({ kind: 'both-stand', ours: PROPOSAL, theirs: COUNTER })!),
    ).toBeTruthy();
  });
});

describe('an agreement, which the side it protects could not see', () => {
  /**
   * The proposing side went on being told silence would confirm their score for the whole grace
   * after somebody had already agreed with it, and went on being offered a correction
   * `state_result` refuses with `the_other_side_has_answered`.
   */
  it('tells the proposing side their score was agreed, and stops offering the correction', async () => {
    await openGame(agreedWith('A'));

    expect(screen.getByText(standingLine(AGREED_WITH_OURS, READ_AT))).toBeTruthy();
    expect(screen.queryByText(/If nobody answers within/)).toBeNull();
    expect(screen.queryByText(CORRECT_LABEL)).toBeNull();
  });

  /**
   * The grace and the answer window run from the same moment and are different spans, so a clock
   * still counting the answer window would be counting a question nobody is being asked.
   */
  it('counts down to the moment it settles, not to a question already answered', async () => {
    await openGame(agreedWith('A'));

    const clock = clockLine(AGREED_WITH_OURS, READ_AT)!;

    expect(clock.figure).toBe('6 hours');
    expect(screen.getByLabelText(`${clock.figure} ${clock.line}`)).toBeTruthy();
  });
});

describe('what the aggregate refuses, on screen', () => {
  it.each([
    ['the_other_side_has_answered', 409],
    ['your_side_has_already_answered', 409],
    ['the_entry_window_has_closed', 409],
    ['a_score_must_name_a_winner', 400],
  ])('says what happened when it refuses with %s', async (code, status) => {
    transport.on('POST', RESULT_PATH, () => errorResponse(status, code));
    await openGame(game());

    fillIn([['6', '4']], ['You', 'Them']);
    fireEvent.press(screen.getByText(ENTER_LABEL));

    await screen.findByText(gameErrorMessage(refusal(code)));
  });

  it('says only the other side may agree, when the server says so', async () => {
    transport.on('POST', ACCEPTANCE_PATH, () =>
      errorResponse(409, 'accepting_your_own_sides_result'),
    );
    await openGame(awaitingAnswer('B'));

    fireEvent.press(screen.getByText(ACCEPT_LABEL));

    await screen.findByText(gameErrorMessage(refusal('accepting_your_own_sides_result')));
  });
});

describe('a Game the list does not hold', () => {
  it('says no game of yours has this address rather than inventing a screen', async () => {
    stubBooking(transport, bookingDetails({ game_id: GAME_ID }));
    stubGames(transport, [], READ_AT);
    await launchSignedIn(RESULT_ROUTE);

    await screen.findByText(NOT_YOURS_LINE);
  });
});

const PROPOSAL = {
  side: 'A',
  proposedBy: ME,
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 6, b: 2 },
    ],
  },
  answerBy: '2026-09-06T08:00:00Z',
  settlesAt: '2026-09-05T15:00:00Z',
} as const;

/** The other side's score, as the domain reads it. Only its figures reach any assertion here. */
const COUNTER = {
  side: 'B',
  proposedBy: OPPONENT,
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 4, b: 6 },
    ],
  },
  answerBy: '2026-09-06T08:00:00Z',
  settlesAt: '2026-09-05T15:00:00Z',
} as const;

/** One agreement, as the two sides read it. Six hours from `READ_AT`, measured from the score. */
const AGREED_WITH_OURS: ResultArgument = {
  kind: 'agreed',
  agreement: {
    with: 'ours',
    by: { kind: 'player', name: 'tomek.p' },
    settlesAt: '2026-09-05T15:00:00Z',
  },
  ours: PROPOSAL,
};

const AGREED_WITH_THEIRS: ResultArgument = {
  kind: 'agreed',
  agreement: { with: 'theirs', by: { kind: 'you' }, settlesAt: '2026-09-05T15:00:00Z' },
  theirs: PROPOSAL,
};
