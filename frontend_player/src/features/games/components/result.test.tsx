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

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { router } from 'expo-router';

import { AppError } from '@/shared/errors';

import type { ResultConversation } from '../domain/conversation';
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

/** What the opponent's seat is called, and the one handle these screens ever print. */
const THEIR_HANDLE = 'tomek.p';

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
      { side: 'A', player_id: ME, nickname: 'me_' },
      { side: 'B', player_id: OPPONENT, nickname: THEIR_HANDLE },
    ],
    proposals: [],
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

/**
 * Land in the app with these games, and open one.
 *
 * **The push is direct, because there is no longer a door.** The games list came off the Now
 * tab with the rest of the placeholder's furniture — Now is not built, and the two sections
 * standing in for it were taken off rather than out — so nothing a player can tap reaches this
 * route today. The screen and its route are unchanged, which is what this suite is about; when
 * the real flow gives it a door, this helper presses that instead.
 */
async function openGame(served: Wire['GameSchema']) {
  stubGames(transport, [served], READ_AT);
  await launchSignedIn();

  act(() => {
    router.push({ pathname: '/games/[gameId]', params: { gameId: served.game_id } });
  });
  await waitFor(() => expect(screen).toHavePathname(`/games/${served.game_id}`));
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

/**
 * **The games list is composed on no screen, so there is no walk to it.**
 *
 * Two assertions stood here — that a row says what its game is asking, and that an empty list
 * draws no section rather than an emptiness — and both were reached by landing on the Now tab.
 * That tab carries its own line and nothing else now: it is not built, and the list was
 * standing in for it. `GamesSection` is not deleted, and neither is anything under it; what is
 * gone is the composition, so a suite that lands in the app and looks for a heading is
 * asserting a screen nobody assembles.
 *
 * **Neither property is lost, and it is worth saying where each went.** *The row's sentence is
 * the screen's* is a fact about `standingLine` having one caller rather than about a walk, and
 * it is covered where that function is — `gamePresentation.test.ts`, which is also the file
 * that would fail if a second spelling appeared. *An empty list draws nothing* is
 * `GamesSection`'s own early return, over a heading only it draws.
 *
 * When a flow composes the list again, the walk comes back here rather than being invented
 * somewhere else — which is the whole reason this note is a note and not a deletion.
 */

describe('the screen this route resolves to', () => {
  it('is reachable by its own address, with no door anywhere in the app', async () => {
    await openGame(awaitingAnswer('B'));

    // The row that used to say this is gone; the screen still says it, which is the half that
    // matters to a player who arrives here from wherever the future flow sends them.
    expect(await screen.findByText(/If you say nothing for 23 hours/)).toBeTruthy();
  });

  /**
   * Now *"deliberately never says nothing is happening"* — and it now says nothing else
   * either, because the list that was standing in for it came off the tab.
   */
  it('is not on the Now tab, which carries only its own line', async () => {
    stubGames(transport, [awaitingAnswer('B')], READ_AT);
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
const AGREED_WITH_OURS: ResultConversation = {
  kind: 'agreed',
  agreement: {
    with: 'ours',
    by: { kind: 'player', nickname: 'tomek.p' },
    settlesAt: '2026-09-05T15:00:00Z',
  },
  ours: PROPOSAL,
};

const AGREED_WITH_THEIRS: ResultConversation = {
  kind: 'agreed',
  agreement: { with: 'theirs', by: { kind: 'you' }, settlesAt: '2026-09-05T15:00:00Z' },
  theirs: PROPOSAL,
};
