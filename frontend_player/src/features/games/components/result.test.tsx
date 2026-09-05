/**
 * **The result conversation, walked the way a player walks it**: the real route tree, the real
 * shell, and only `fetch` faked.
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
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
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
  CANCEL_LABEL,
  COUNTER_IS_THEIR_SCORE,
  COUNTER_LABEL,
  CORRECT_LABEL,
  ENTER_LABEL,
  NOT_YOURS_LINE,
  STILL_ON_THE_TABLE,
  UNSCORED_FACTS,
  YOURS,
  acceptedLine,
  clockLine,
  resultBody,
  resultTitle,
  scoreProblemLine,
  standingLine,
  submitLabel,
} from './gamePresentation';
import { gameErrorMessage } from './gameErrorMessage';

const GAME_ID = '8f14e45f-ceea-467a-9dd1-4bd9c39d4a58';
const RESULT_PATH = `${GAMES_PATH}/${GAME_ID}/result`;
const ACCEPTANCE_PATH = `${RESULT_PATH}/acceptance`;

const READ_AT = '2026-09-05T09:00:00Z';
const ME = GATE_USER.id;
const OPPONENT = 'bbbbbbbb-0000-4000-8000-000000000002';

/** A singles padel game with me on side A. Singles, so the column heads are *You* and *Them*. */
function game(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: GAME_ID,
    challenge_id: 'cccccccc-0000-4000-8000-000000000003',
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: '2026-09-01T09:00:00Z',
    entry_closes_at: '2026-09-09T09:00:00Z',
    seats: [
      { side: 'A', player_id: ME },
      { side: 'B', player_id: OPPONENT },
    ],
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

/** A played game with one score waiting on an answer. */
function awaitingAnswer(side: 'A' | 'B'): Wire['GameSchema'] {
  return game({
    standing: 'AWAITING_ANSWER',
    played_at: '2026-09-04T20:00:00Z',
    entry_closes_at: null,
    standing_proposal: proposal(side),
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

/** Land in the app with these games, and open the first of them from the Now tab. */
async function openGame(served: Wire['GameSchema'], sport = 'Padel') {
  stubGames(transport, [served], READ_AT);
  await launchSignedIn();

  const row = await screen.findByLabelText(new RegExp(`^${sport} · arranged`));
  fireEvent.press(row);
  await waitFor(() => expect(screen).toHavePathname(`/games/${GAME_ID}`));
}

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

describe('the list on the Now tab', () => {
  it('says what each game is asking, and the screen says the same sentence', async () => {
    const served = awaitingAnswer('B');
    stubGames(transport, [served], READ_AT);
    await launchSignedIn();

    // The row's own sentence is the screen's: a player who reads a row, taps it and finds a
    // different deadline is the state `standingLine` having one caller exists to prevent.
    const line = await screen.findByText(/If you say nothing for 23 hours/);

    expect(line).toBeTruthy();
  });

  /**
   * Now *"deliberately never says nothing is happening"*, and a challenge whose line-up has not
   * completed is not a game yet — so an empty list draws no section rather than an emptiness.
   */
  it('draws nothing at all when there are no games', async () => {
    await launchSignedIn();
    await screen.findByText(/not built yet/);

    expect(screen.queryByText('Your games')).toBeNull();
  });
});

describe('entering a result', () => {
  it('says when saying nothing stops being possible, before the clock runs', async () => {
    await openGame(game());

    const said = standingLine(
      { kind: 'awaiting-entry', entryClosesAt: '2026-09-09T09:00:00Z' },
      READ_AT,
    );

    expect(screen.getByText(said)).toBeTruthy();
    // Four days: the plan's horizon is one ordinary week and entry stays open a day past it.
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

  it('agrees across the net, and says when that becomes final', async () => {
    transport.on('POST', ACCEPTANCE_PATH, () => json(awaitingAnswer('B')));
    await openGame(awaitingAnswer('B'));

    fireEvent.press(screen.getByText(ACCEPT_LABEL));

    await screen.findByText(acceptedLine('2026-09-05T15:00:00Z', READ_AT));
    expect(transport.requestsTo('POST', ACCEPTANCE_PATH)).toHaveLength(1);
    // The grace runs from the score, so a disagreement still wins inside it — and the control
    // for one is still there.
    expect(screen.getByText(COUNTER_LABEL)).toBeTruthy();
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
    await openGame(game({ sport: 'SQUASH' }), 'Squash');

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
   * Two scores stand and the wire returns neither — `standing_proposal` is *"when exactly one
   * is"*. So the screen states the ending and offers no control, rather than asking somebody to
   * agree with a score it cannot show them. See `domain/conversation.ts`.
   */
  it('states the disagreement without offering an agreement it cannot draw', async () => {
    await openGame(
      game({
        standing: 'AWAITING_ANSWER',
        played_at: '2026-09-04T20:00:00Z',
        entry_closes_at: null,
      }),
    );

    expect(screen.getByText(standingLine({ kind: 'both-stand' }, READ_AT))).toBeTruthy();
    expect(screen.queryByText(ACCEPT_LABEL)).toBeNull();
    expect(screen.queryByText(COUNTER_LABEL)).toBeNull();
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

describe('a link that goes nowhere', () => {
  it('says no game of yours has this address rather than inventing a screen', async () => {
    stubGames(transport, [], READ_AT);
    await launchSignedIn(`/games/${GAME_ID}`);

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
