/**
 * The result conversation, driven through the real route tree and the network
 * boundary.
 *
 * The same shape as the Now and departure suites, and deliberately so: only `fetch`
 * is faked. The router, the http client, error mapping, the mappers, the use-cases,
 * the hooks and both screens run for real — so a pass here means the act works end
 * to end minus the socket, including the part nobody can see from one screen, which
 * is that **Now corrects itself off the player's own tap**.
 *
 * **Assertions are about what a player can see, or what left the device.** The body
 * of the write is the second kind: what she typed is invisible in the render tree
 * once it has gone, and it is the whole of what the pad is for.
 */

import { focusManager, onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { SCORE_BOARD_ROW_ID } from '@/shared/ui';
import { emptyNow, matchCard, nowPathFor, stubNow } from '@/test-support/now';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import {
  acceptancePath,
  emptyResultBlock,
  resultPath,
  resultScreen,
  resultWrite,
  scoreLine,
  stubResult,
} from '@/test-support/result';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { ENDING_ID, GRACE_ID, HERO_CLOCK_ID, RESULT_BODY_ID } from './ResultScreen';
import { PAD_ID, padCellId, padKeyId } from './ScorePadView';
import {
  ACCEPT_LABEL,
  ASKED_LINE,
  CLOSE_LABEL,
  CORRECT_LABEL,
  COUNTER_LABEL,
  LOAD_FAILED,
  PAD_UNFINISHED,
  RESULT_TITLE,
  SEND_LABEL,
  WAITING_LINE,
  WRITE_FAILED,
} from './resultCopy';

const MATCH = '5b0c0000-0000-4000-8000-000000000001';
const HOUR = 60 * 60 * 1000;

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
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  focusManager.setFocused(true);
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

/** A moment the suite's own clock can count to, so a countdown is a real figure. */
function inHours(hours: number): string {
  return new Date(Date.now() + hours * HOUR).toISOString();
}

/** A line only Now draws, so the suite knows which screen it is standing on. */
const ON_NOW = /Sunset Padel · indoor/;

/** The score two sides put up: hers first, in both halves. */
function aScore(): Wire['ScoreLineResponse'] {
  return scoreLine(
    [
      ['Ada', 'Kuba'],
      ['Marta', 'Ola'],
    ],
    [
      [6, 4],
      [3, 6],
    ],
  );
}

/** A live proposal from one side or the other. */
function proposal(by: number, proposals = 1): Wire['ResultBlockResponse'] {
  return { agreed: false, proposals, score: aScore(), proposed_by: by };
}

/** A settled result: agreed, and still printed. */
function settled(): Wire['ResultBlockResponse'] {
  return { agreed: true, proposals: 1, score: aScore(), proposed_by: 0 };
}

function nowHolding(card: Wire['MatchCardResponse']): Wire['NowResponse'] {
  return { ...emptyNow(), your_matches: { stamp: 1, cards: [card] } };
}

async function launchOnNow(body: Wire['NowResponse']) {
  stubGate(transport, { ratings: [RATING] });
  stubNow(transport, body);

  await launchSignedIn();
  await screen.findByText(ON_NOW);
}

/** Straight to the screen, for the cases that are about the screen itself. */
async function launchOnResult(wire: Wire['ResultScreenResponse']) {
  stubGate(transport, { ratings: [RATING] });
  stubResult(transport, wire);

  await launchSignedIn(`/matches/${MATCH}/result`);
  await screen.findByText(RESULT_TITLE);
  // The header draws while the answer is still in flight, so waiting on the title
  // alone would let an assertion run against a screen that has nothing on it. The
  // body exists exactly when an answer does, on every one of the renderings.
  await screen.findByTestId(RESULT_BODY_ID);
}

/** Wait until the result route has actually been popped. */
async function backOnNow() {
  await waitFor(() => expect(screen).toHavePathname('/'));
}

/** What the writes were asked to do, as they left the device. */
function scoresSent(): readonly Record<string, unknown>[] {
  return transport
    .requestsTo('POST', resultPath(MATCH))
    .map((request) => request.body as Record<string, unknown>);
}

function composes(): number {
  return transport.requestsTo('GET', nowPathFor('all')).length;
}

/** Type a run of numbers on the pad. */
function typeScore(values: readonly number[]) {
  for (const value of values) fireEvent.press(screen.getByTestId(padKeyId(value)));
}

// ---------------------------------------------------------------------------
// Getting there
// ---------------------------------------------------------------------------

describe('the act on a played match’s card', () => {
  it('opens this screen in one tap', async () => {
    await launchOnNow(
      nowHolding(matchCard({ matchId: MATCH, situation: 'needsResult', act: 'enterResult' })),
    );
    stubResult(
      transport,
      resultScreen({ matchId: MATCH, mayEnter: true, settlementDeadline: inHours(20) }),
    );

    fireEvent.press(screen.getByLabelText('Enter the score, Sunset Padel'));

    expect(await screen.findByTestId(PAD_ID)).toBeTruthy();
    // It asked about the match and about nothing else: the card's own already
    // composed facts are not carried across, because what the conversation is doing
    // is asked for at the instant the screen opens.
    expect(transport.requestsTo('GET', resultPath(MATCH))).toHaveLength(1);
  });

  it('is the same route for the other of the two post-play acts', async () => {
    // `ADR-0060`: *"one route resolving the same situation the card resolved"*. Two
    // labels, two moments of one conversation, one screen.
    await launchOnNow(
      nowHolding(matchCard({ matchId: MATCH, situation: 'confirmResult', act: 'answerResult' })),
    );
    stubResult(
      transport,
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        mayAccept: true,
        mayCounter: true,
        settlementDeadline: inHours(20),
      }),
    );

    fireEvent.press(screen.getByLabelText('Answer the score, Sunset Padel'));

    expect(await screen.findByText(ASKED_LINE)).toBeTruthy();
  });

  it('asks again every time it is opened', async () => {
    // Everything on this screen turns on clocks the phone does not hold: a proposal
    // can land, settle or be countered between two visits, and offering *accept*
    // against a score somebody has replaced asks her to agree with a number that is
    // no longer on the table.
    await launchOnResult(
      resultScreen({ matchId: MATCH, situation: 'completed', result: settled() }),
    );
    expect(transport.requestsTo('GET', resultPath(MATCH))).toHaveLength(1);

    await act(async () => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
      await Promise.resolve();
    });

    await waitFor(() => expect(transport.requestsTo('GET', resultPath(MATCH))).toHaveLength(2));
  });

  it('is opened by the result acts and by no other, because the rest have nowhere to go', async () => {
    // `ADR-0083` closes the act set on the rule that a card names an act when a **v1
    // surface can receive it**, and five of the seven still have none — the seat
    // claim and its payment, Find, the Getting-in sheet, leaving standby. An act
    // whose destination this build cannot open is received and dropped, and a screen
    // that pushed the result route for all of them would answer *take the seat* with
    // a screen about a score.
    await launchOnNow(
      nowHolding(
        matchCard({ matchId: MATCH, situation: 'seatOffered', act: 'takeSeat', amount: 3800 }),
      ),
    );

    fireEvent.press(screen.getByLabelText('Take the seat · 38,00 zł, Sunset Padel'));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('GET', resultPath(MATCH))).toHaveLength(0);
  });

  it('asks again every time it is opened, and never serves what it was shown before', async () => {
    // A cached conversation is the one thing this screen must not show: between two
    // visits a proposal can land, settle or be countered, and the app's 30-second
    // default would serve her a screen offering *accept* against a score somebody
    // has already replaced.
    await launchOnNow(
      nowHolding(matchCard({ matchId: MATCH, situation: 'confirmResult', act: 'answerResult' })),
    );
    stubResult(
      transport,
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        mayAccept: true,
        settlementDeadline: inHours(20),
      }),
    );

    fireEvent.press(screen.getByLabelText('Answer the score, Sunset Padel'));
    await screen.findByText(ASKED_LINE);
    expect(transport.requestsTo('GET', resultPath(MATCH))).toHaveLength(1);

    fireEvent.press(screen.getByLabelText(CLOSE_LABEL));
    await backOnNow();

    fireEvent.press(screen.getByLabelText('Answer the score, Sunset Padel'));
    await screen.findByText(ASKED_LINE);

    expect(transport.requestsTo('GET', resultPath(MATCH))).toHaveLength(2);
  });

  it('asks as the signed-in player, because a stranger gets a 404 either way', async () => {
    // The route is authorisation as well as an address: the server answers somebody
    // who did not play with a 404, and it can only do that if the read carries her
    // token. An unauthenticated read is a 401 on a screen that would then say only
    // that it could not be opened.
    await launchOnResult(
      resultScreen({ matchId: MATCH, situation: 'completed', result: settled() }),
    );

    const read = transport.requestsTo('GET', resultPath(MATCH))[0];

    expect(read?.headers['Authorization']).toMatch(/^Bearer /);
  });

  it('goes home rather than asking about a link it cannot trust', async () => {
    stubGate(transport, { ratings: [RATING] });

    await launchSignedIn('/matches/not-a-match/result');

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('GET', '/api/v1/matches/not-a-match/result')).toHaveLength(0);
  });

  it('says so when it cannot be opened at all, and can be asked again', async () => {
    stubGate(transport, { ratings: [RATING] });
    transport.on('GET', resultPath(MATCH), () => errorResponse(404, 'match_not_found'));

    await launchSignedIn(`/matches/${MATCH}/result`);

    expect(await screen.findByText(LOAD_FAILED)).toBeTruthy();

    transport.on('GET', resultPath(MATCH), () =>
      json(resultScreen({ matchId: MATCH, situation: 'completed', result: settled() })),
    );
    fireEvent.press(screen.getByLabelText('Try again'));

    expect(await screen.findAllByTestId(SCORE_BOARD_ROW_ID)).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// The two clocks
// ---------------------------------------------------------------------------

describe('the clocks', () => {
  it('draws the settlement deadline as the hero, with the sentence that says nobody has to act', async () => {
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        mayAccept: true,
        mayCounter: true,
        settlementDeadline: inHours(20),
      }),
    );

    const hero = screen.getByTestId(HERO_CLOCK_ID);

    // The figure, not the moment: a row's value is composed separately from its
    // label, so asserting the label alone leaves a raw ISO string green.
    expect(hero.props.children).toMatch(/^\d+ h( \d+ min)?$/);
    expect(screen.getByLabelText(/^\d+ h.* left$/)).toBeTruthy();
    expect(screen.queryByText(/^2026-/)).toBeNull();
    expect(screen.getByText(/If this is not answered, it stands/)).toBeTruthy();
  });

  it('says what silence does differently once both sides have spoken', async () => {
    // One proposal stands; two count for nothing. The screen that asks for a tap has
    // to say what happens without one, and those are opposite outcomes.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1, 2),
        mayAccept: true,
        settlementDeadline: inHours(20),
      }),
    );

    expect(screen.getByText(/counts for nothing/)).toBeTruthy();
    expect(screen.queryByText(/it stands/)).toBeNull();
  });

  it('draws the acceptance grace while it runs, and not once it has passed', async () => {
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        mayAccept: true,
        settlementDeadline: inHours(20),
        acceptanceGrace: inHours(0.4),
      }),
    );

    expect(screen.getByTestId(GRACE_ID)).toBeTruthy();
    expect(screen.getByText(/still beats an acceptance/)).toBeTruthy();
  });

  it('draws no grace when the server sends none', async () => {
    // It is present **only while it runs**, and the server is what decides that. A
    // screen that hid it would say *settled* half an hour early; a screen that drew
    // it always would count down to a moment that has passed.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        mayAccept: true,
        settlementDeadline: inHours(20),
      }),
    );

    expect(screen.queryByTestId(GRACE_ID)).toBeNull();
  });

  it('says how many of them turned up, on a match that has been played', async () => {
    // Sent rather than derived: *one less than the seats* stops being minus one the
    // moment a doubles match loses two people.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'playedNoScore',
        counts: { seats: 4, paid: 4, held: 0, turned_up: 3 },
      }),
    );

    expect(screen.getByLabelText('Turned up, 3 of 4')).toBeTruthy();
  });

  it('says nothing about who turned up before the match has been played', async () => {
    // The count is absent until then, and a row reading `0 of 4` would say that
    // nobody came to a match nobody has played yet.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'forming',
        counts: { seats: 4, paid: 2, held: 0, turned_up: null },
      }),
    );

    expect(screen.queryByText('Turned up')).toBeNull();
  });

  it('repaints the hero clock, and asks for nothing while it does', async () => {
    // A countdown **repainting** is drawing; a countdown **reaching zero** is one of
    // Now's four asks (`ADR-0088`). Twice, because a clock that ticked once and
    // stopped is the shape a timer that forgets to re-arm produces, and one tick
    // cannot tell them apart.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        mayAccept: true,
        // Inside the seconds band, where the label draws a clock face and the screen
        // repaints every second.
        settlementDeadline: inHours(0.08),
      }),
    );

    const reading = () => String(screen.getByTestId(HERO_CLOCK_ID).props.children);
    const first = reading();

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    const second = reading();

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });
    const third = reading();

    expect(new Set([first, second, third]).size).toBe(3);
    expect(transport.requestsTo('GET', resultPath(MATCH))).toHaveLength(1);
  });

  it('counts to nothing on a conversation that is over', async () => {
    // A settled result and an unscored evening count to nothing rather than to zero.
    await launchOnResult(
      resultScreen({ matchId: MATCH, situation: 'completed', result: settled() }),
    );

    expect(screen.queryByTestId(HERO_CLOCK_ID)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The five renderings
// ---------------------------------------------------------------------------

describe('the five renderings', () => {
  it('entry: the pad is open, and the match’s own sentence is above it', async () => {
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        result: emptyResultBlock(),
        mayEnter: true,
        settlementDeadline: inHours(20),
      }),
    );

    expect(screen.getByTestId(PAD_ID)).toBeTruthy();
    // Now's table, not a second one: the sentence on this screen is the sentence on
    // the card she tapped.
    expect(screen.getByText('Settled — the score has not been entered yet.')).toBeTruthy();
    expect(screen.getByText(/If nobody does, the evening still counts/)).toBeTruthy();
  });

  it('asked: the other side’s score, with accept and a modification', async () => {
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        mayAccept: true,
        mayCounter: true,
        settlementDeadline: inHours(20),
      }),
    );

    expect(screen.getByText(ASKED_LINE)).toBeTruthy();
    expect(screen.getByLabelText(ACCEPT_LABEL)).toBeTruthy();
    expect(screen.getByLabelText(COUNTER_LABEL)).toBeTruthy();
    expect(screen.queryByTestId(PAD_ID)).toBeNull();
  });

  it('waiting: her own side’s score, with only a correction', async () => {
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(0),
        mayEnter: true,
        settlementDeadline: inHours(20),
      }),
    );

    expect(screen.getByText(WAITING_LINE)).toBeTruthy();
    expect(screen.getByLabelText(CORRECT_LABEL)).toBeTruthy();
    // A teammate agreeing with a teammate proves nothing, so the server says no and
    // the control is simply not drawn.
    expect(screen.queryByLabelText(ACCEPT_LABEL)).toBeNull();
  });

  it('settled: the score, the ending, and no controls at all', async () => {
    await launchOnResult(
      resultScreen({ matchId: MATCH, situation: 'completed', result: settled() }),
    );

    expect(screen.getAllByTestId(SCORE_BOARD_ROW_ID)).toHaveLength(2);
    expect(screen.getByTestId(ENDING_ID)).toBeTruthy();
    expect(screen.getByText('Settled — the result is agreed.')).toBeTruthy();
    expect(screen.queryByLabelText(ACCEPT_LABEL)).toBeNull();
    expect(screen.queryByLabelText(COUNTER_LABEL)).toBeNull();
    expect(screen.queryByTestId(PAD_ID)).toBeNull();
    // Neither the question nor the wait: the conversation is over, and the ending
    // says what it is instead.
    expect(screen.queryByText(ASKED_LINE)).toBeNull();
    expect(screen.queryByText(WAITING_LINE)).toBeNull();
  });

  it('settled: says nothing about anybody’s level', async () => {
    // No engine produces a level movement, so the app must not invent a number
    // nothing computed — in either direction.
    await launchOnResult(
      resultScreen({ matchId: MATCH, situation: 'completed', result: settled() }),
    );

    expect(screen.queryByText(/level/i)).toBeNull();
  });

  it('unscored: what the evening counted for, and what it did not', async () => {
    await launchOnResult(
      resultScreen({ matchId: MATCH, situation: 'playedNoScore', result: emptyResultBlock() }),
    );

    expect(screen.getByText(/counts as an evening/)).toBeTruthy();
    expect(screen.getByText(/Nobody’s level moved, nobody was penalised/)).toBeTruthy();
    expect(screen.getByText('Settled — nobody entered a score.')).toBeTruthy();
    expect(screen.queryByTestId(PAD_ID)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Whose 6 was that
// ---------------------------------------------------------------------------

describe('the score', () => {
  it('names both sides by their players, with the viewer’s first', async () => {
    // `ADR-0060`: *"with four people and two sides an unlabelled string is
    // unusable"*, so every surface that shows a score names both sides.
    await launchOnResult(
      resultScreen({ matchId: MATCH, situation: 'completed', result: settled() }),
    );

    const rows = screen.getAllByTestId(SCORE_BOARD_ROW_ID);

    expect(rows[0]?.props.accessibilityLabel).toBe('Ada and Kuba, 6, 3');
    expect(rows[1]?.props.accessibilityLabel).toBe('Marta and Ola, 4, 6');
  });

  it('names a side by where it sat when the wire named nobody on it', async () => {
    // A leaver's own seat is vacated, so her side can come back with a name missing
    // or with none at all — and she is exactly the player who most needs the score
    // to read the right way round.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'completed',
        result: {
          agreed: true,
          proposals: 1,
          score: scoreLine([[], ['Marta', 'Ola']], [[6, 4]]),
          proposed_by: 1,
        },
      }),
    );

    expect(screen.getAllByTestId(SCORE_BOARD_ROW_ID)[0]?.props.accessibilityLabel).toBe(
      'Your side, 6',
    );
  });
});

// ---------------------------------------------------------------------------
// A player who left before the match
// ---------------------------------------------------------------------------

describe('a leaver', () => {
  it('opens the screen and is offered nothing', async () => {
    // She is never told her match did not exist — she played half an evening and
    // paid for it — and `ADR-0048` lets her do none of it.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(1),
        settlementDeadline: inHours(20),
      }),
    );

    expect(screen.getAllByTestId(SCORE_BOARD_ROW_ID)).toHaveLength(2);
    expect(screen.queryByLabelText(ACCEPT_LABEL)).toBeNull();
    expect(screen.queryByLabelText(COUNTER_LABEL)).toBeNull();
    expect(screen.queryByLabelText(CORRECT_LABEL)).toBeNull();
    expect(screen.queryByTestId(PAD_ID)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Entering, correcting, countering
// ---------------------------------------------------------------------------

describe('entering a score', () => {
  const entry = () =>
    resultScreen({
      matchId: MATCH,
      result: emptyResultBlock(),
      mayEnter: true,
      settlementDeadline: inHours(20),
    });

  it('sends what she typed, her side first, as pairs of integers', async () => {
    await launchOnResult(entry());
    transport.on('POST', resultPath(MATCH), () =>
      json(
        resultWrite(
          resultScreen({
            matchId: MATCH,
            situation: 'confirmResult',
            result: proposal(0),
            mayEnter: true,
            settlementDeadline: inHours(24),
          }),
          matchCard({ matchId: MATCH, situation: 'confirmResult' }),
        ),
      ),
    );

    typeScore([6, 4, 3, 6]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));

    await waitFor(() => expect(scoresSent()).toHaveLength(1));
    expect(scoresSent()[0]).toEqual({
      sets: [
        [6, 4],
        [3, 6],
      ],
    });
  });

  it('offers no send until a set is finished, and says what is missing', async () => {
    await launchOnResult(entry());

    expect(screen.queryByLabelText(SEND_LABEL)).toBeNull();

    typeScore([6]);

    expect(screen.getByText(PAD_UNFINISHED)).toBeTruthy();
    expect(screen.queryByLabelText(SEND_LABEL)).toBeNull();

    typeScore([4]);

    expect(screen.queryByText(PAD_UNFINISHED)).toBeNull();
    expect(screen.getByLabelText(SEND_LABEL)).toBeTruthy();
  });

  it('offers no send while one set is finished and another is half-typed', async () => {
    // The case a single unfinished row cannot make: there **is** something to send,
    // and sending it would mean choosing a number she did not type.
    await launchOnResult(entry());

    typeScore([6, 4, 3]);

    expect(screen.getByText(PAD_UNFINISHED)).toBeTruthy();
    expect(screen.queryByLabelText(SEND_LABEL)).toBeNull();

    typeScore([6]);

    expect(screen.getByLabelText(SEND_LABEL)).toBeTruthy();
  });

  it('reaches every number badminton can score, not only a single digit', async () => {
    // The pad is the widest of `ADR-0060`'s four because the sport is not on the
    // wire, and a pad that stopped at nine would make a badminton score unsendable
    // on the one instrument the app has.
    await launchOnResult(entry());
    transport.on('POST', resultPath(MATCH), () =>
      json(
        resultWrite(
          resultScreen({
            matchId: MATCH,
            situation: 'confirmResult',
            result: proposal(0),
            settlementDeadline: inHours(24),
          }),
          matchCard({ matchId: MATCH, situation: 'confirmResult' }),
        ),
      ),
    );

    typeScore([21, 19]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));

    await waitFor(() => expect(scoresSent()).toHaveLength(1));
    expect(scoresSent()[0]).toEqual({ sets: [[21, 19]] });
  });

  it('retypes the cell she taps, which is how a typo is fixed', async () => {
    // The cursor walks forward on its own; tapping a cell is the only way back to
    // one she has already filled, and fixing a mistyped set is the ordinary case.
    await launchOnResult(entry());

    typeScore([6, 4]);
    fireEvent.press(screen.getByTestId(padCellId(0, 1)));
    typeScore([2]);

    expect(screen.getByTestId(padCellId(0, 0)).props.accessibilityLabel).toMatch(/, 6$/);
    expect(screen.getByTestId(padCellId(0, 1)).props.accessibilityLabel).toMatch(/, 2$/);
  });

  it('closes the pad once the score is on the table', async () => {
    await launchOnResult(entry());
    transport.on('POST', resultPath(MATCH), () =>
      json(
        resultWrite(
          resultScreen({
            matchId: MATCH,
            situation: 'confirmResult',
            result: proposal(0),
            mayEnter: true,
            settlementDeadline: inHours(24),
          }),
          matchCard({ matchId: MATCH, situation: 'confirmResult' }),
        ),
      ),
    );

    typeScore([6, 4]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));

    // What she typed is now above her, and the pad would otherwise offer her the
    // same act again with her own numbers still in it.
    expect(await screen.findByText(WAITING_LINE)).toBeTruthy();
    expect(screen.queryByTestId(PAD_ID)).toBeNull();
  });

  it('is never retried on the app’s own initiative', async () => {
    await launchOnResult(entry());
    transport.on('POST', resultPath(MATCH), networkFailure());

    typeScore([6, 4]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));
    await screen.findByText(WRITE_FAILED);

    await act(async () => {
      await Promise.resolve();
    });

    expect(scoresSent()).toHaveLength(1);
  });

  it('says only the general thing for a failure code this build has never heard of', async () => {
    // Old app versions live on real phones for months and the backend will add codes
    // this build has never seen, so an unknown one falls back rather than being lost — the
    // prototype-key half of that rule is unreachable from here and is asserted on
    // `writeFailureLine` directly, in `resultCopy.test.ts`.
    await launchOnResult(entry());
    transport.on('POST', resultPath(MATCH), () => errorResponse(409, 'match_side_has_proposed'));

    typeScore([6, 4]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));

    expect(await screen.findByText(WRITE_FAILED)).toBeTruthy();
  });

  it('says what she typed could not have been played, and keeps it on the pad', async () => {
    // The one refusal that is **not** a recomposed screen: it is about what she
    // typed rather than about what the match is doing, and re-presenting the same
    // table would show her no reason at all.
    await launchOnResult(entry());
    transport.on('POST', resultPath(MATCH), () => errorResponse(400, 'match_impossible_score'));

    typeScore([0, 0]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));

    expect(await screen.findByText(/could not have been played/)).toBeTruthy();
    expect(screen.getByTestId(PAD_ID)).toBeTruthy();
  });
});

describe('answering a score', () => {
  const asked = () =>
    resultScreen({
      matchId: MATCH,
      situation: 'confirmResult',
      result: proposal(1),
      mayAccept: true,
      mayCounter: true,
      settlementDeadline: inHours(20),
    });

  it('accepts with a body-less write to its own address', async () => {
    await launchOnResult(asked());
    transport.on('POST', acceptancePath(MATCH), () =>
      json(
        resultWrite(
          resultScreen({ matchId: MATCH, situation: 'completed', result: settled() }),
          matchCard({ matchId: MATCH, situation: 'completed' }),
        ),
      ),
    );

    fireEvent.press(screen.getByLabelText(ACCEPT_LABEL));

    expect(await screen.findByTestId(ENDING_ID)).toBeTruthy();
    expect(transport.requestsTo('POST', acceptancePath(MATCH))).toHaveLength(1);
    expect(transport.requestsTo('POST', acceptancePath(MATCH))[0]?.body).toBeUndefined();
    // Accepting is not a score, and it never goes to the score's address.
    expect(scoresSent()).toHaveLength(0);
  });

  it('opens an empty pad to disagree, and there is no way to say no without one', async () => {
    // `ADR-0048`: *"a counter must carry a score. There is no bare rejection."* The
    // way that is made true is by there being nowhere to send one — not by a
    // validator turning one away.
    await launchOnResult(asked());

    fireEvent.press(screen.getByLabelText(COUNTER_LABEL));

    expect(screen.getByTestId(PAD_ID)).toBeTruthy();
    // Empty, not pre-filled with the score it is countering: one tap from a
    // "different" score identical to the one on the table would consume her side's
    // one proposal on a statement she did not mean to make.
    expect(screen.getByTestId(padCellId(0, 0)).props.accessibilityLabel).toMatch(/empty$/);
    expect(screen.queryByLabelText(SEND_LABEL)).toBeNull();
  });

  it('sends the counter to the score’s address, like any other score', async () => {
    await launchOnResult(asked());
    transport.on('POST', resultPath(MATCH), () =>
      json(
        resultWrite(
          resultScreen({
            matchId: MATCH,
            situation: 'confirmResult',
            result: proposal(0, 2),
            settlementDeadline: inHours(24),
          }),
          matchCard({ matchId: MATCH, situation: 'confirmResult' }),
        ),
      ),
    );

    fireEvent.press(screen.getByLabelText(COUNTER_LABEL));
    typeScore([6, 4, 6, 3]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));

    await waitFor(() => expect(scoresSent()).toHaveLength(1));
    expect(scoresSent()[0]).toEqual({
      sets: [
        [6, 4],
        [6, 3],
      ],
    });
  });

  it('opens a correction on what is already there', async () => {
    // Correcting is editing her own side's sentence, so the numbers she is fixing
    // are the ones in front of her.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(0),
        mayEnter: true,
        settlementDeadline: inHours(20),
      }),
    );

    fireEvent.press(screen.getByLabelText(CORRECT_LABEL));

    expect(screen.getByTestId(padCellId(0, 0)).props.accessibilityLabel).toMatch(/, 6$/);
    expect(screen.getByTestId(padCellId(1, 1)).props.accessibilityLabel).toMatch(/, 6$/);
    expect(screen.getByLabelText(SEND_LABEL)).toBeTruthy();
  });

  it('names the pad’s two columns by the players, once there is a score to read them from', async () => {
    // `ADR-0060` again, applied to the instrument: a grid of digits with no names is
    // the unlabelled `6-4, 3-6, 6-2` the whole rule exists to refuse. The names are
    // on the wire exactly when a score is, so entry has the positional pair and
    // every other rendering has the people.
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        situation: 'confirmResult',
        result: proposal(0),
        mayEnter: true,
        settlementDeadline: inHours(20),
      }),
    );

    fireEvent.press(screen.getByLabelText(CORRECT_LABEL));

    expect(screen.getByTestId(padCellId(0, 0)).props.accessibilityLabel).toMatch(
      /^Set 1, Ada and Kuba,/,
    );
    expect(screen.getByTestId(padCellId(0, 1)).props.accessibilityLabel).toMatch(
      /^Set 1, Marta and Ola,/,
    );
  });

  it('names them by where they sat while there is no score to read them from', async () => {
    await launchOnResult(
      resultScreen({
        matchId: MATCH,
        result: emptyResultBlock(),
        mayEnter: true,
        settlementDeadline: inHours(20),
      }),
    );

    expect(screen.getByTestId(padCellId(0, 0)).props.accessibilityLabel).toBe(
      'Set 1, Your side, empty',
    );
  });

  it('renders a refusal as the conversation as it is now, with no dialog', async () => {
    // A stale accept is `ADR-0074`'s own named case and comes back as the counter's
    // situation with `mayAccept` false. She *sees* the correction rather than being
    // told it.
    await launchOnResult(asked());
    transport.on('POST', acceptancePath(MATCH), () =>
      json(
        resultWrite(
          resultScreen({
            matchId: MATCH,
            situation: 'confirmResult',
            result: proposal(0, 2),
            settlementDeadline: inHours(24),
          }),
          matchCard({ matchId: MATCH, situation: 'confirmResult' }),
        ),
      ),
    );

    fireEvent.press(screen.getByLabelText(ACCEPT_LABEL));

    expect(await screen.findByText(WAITING_LINE)).toBeTruthy();
    expect(screen.queryByLabelText(ACCEPT_LABEL)).toBeNull();
    expect(screen.queryByText(WRITE_FAILED)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// What it does to Now
// ---------------------------------------------------------------------------

describe('the card behind the screen', () => {
  it('corrects itself off her own tap, without asking Now for anything', async () => {
    await launchOnNow(
      nowHolding(matchCard({ matchId: MATCH, situation: 'needsResult', act: 'enterResult' })),
    );
    stubResult(
      transport,
      resultScreen({
        matchId: MATCH,
        result: emptyResultBlock(),
        mayEnter: true,
        settlementDeadline: inHours(20),
      }),
    );

    fireEvent.press(screen.getByLabelText('Enter the score, Sunset Padel'));
    await screen.findByTestId(PAD_ID);
    const before = composes();

    transport.on('POST', resultPath(MATCH), () =>
      json(
        resultWrite(
          resultScreen({
            matchId: MATCH,
            situation: 'confirmResult',
            result: proposal(0),
            mayEnter: true,
            settlementDeadline: inHours(24),
          }),
          matchCard({
            matchId: MATCH,
            situation: 'completed',
            act: null,
            facts: { score: aScore() },
          }),
        ),
      ),
    );

    typeScore([6, 4, 3, 6]);
    fireEvent.press(screen.getByLabelText(SEND_LABEL));
    await screen.findByText(WAITING_LINE);

    fireEvent.press(screen.getByLabelText(CLOSE_LABEL));
    await backOnNow();

    // The card is the one that came back in the write's own answer.
    expect(await screen.findByText('Settled — the result is agreed.')).toBeTruthy();
    // Popping back off a route is none of `ADR-0054`'s four asks, so a second
    // compose here would be a cost bought for tidiness — and she would watch the
    // screen she just came back to rebuild itself.
    expect(composes()).toBe(before);
  });

  it('prints a settled score on the card, with both sides named and no level movement', async () => {
    await launchOnNow(
      nowHolding(matchCard({ matchId: MATCH, situation: 'completed', facts: { score: aScore() } })),
    );

    const rows = screen.getAllByTestId(SCORE_BOARD_ROW_ID);

    expect(rows).toHaveLength(2);
    expect(rows[0]?.props.accessibilityLabel).toBe('Ada and Kuba, 6, 3');
    expect(rows[1]?.props.accessibilityLabel).toBe('Marta and Ola, 4, 6');
    expect(screen.queryByText(/level/i)).toBeNull();
  });

  it('leaves an ordinary card saying nothing about a score', async () => {
    // The negative half: the score is present exactly when the server sends one,
    // which is on the two situations that have one to print.
    await launchOnNow(nowHolding(matchCard({ matchId: MATCH, situation: 'forming' })));

    expect(screen.queryAllByTestId(SCORE_BOARD_ROW_ID)).toHaveLength(0);
  });
});
