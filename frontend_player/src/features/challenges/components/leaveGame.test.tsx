/**
 * ***Leave this game*, walked the way a player walks it**: the real route tree, the real shell,
 * the game screen's plan lead, and only `fetch` faked.
 *
 * [#418](https://github.com/Raketa02/Raketa/issues/418)'s acceptance criteria for the act are
 * assertions in this file and opinions nowhere else — the control is drawn last on the plan lead
 * and only while the agreed moment is ahead, the sheet says the four things `the-words.md` §22.8
 * fixes, a leave in flight is busy and never optimistic, success re-reads every list the seat
 * touched and goes back, and each refusal code costs the screen exactly what `actRefusal.ts`
 * says it does. The rung the departure leaves behind is `nowRail.test.tsx`'s; the screen it
 * leaves behind is `gameScreenPlanLead.test.tsx`'s.
 *
 * The words are the deck's — `leaveGamePresentation.ts` — and the refusal sentence is
 * `challengeErrorMessage`'s, as it is for every write in this feature.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { AppError, offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';
import {
  CONVERSATIONS_PATH,
  GAMES_PATH,
  GATE_USER,
  PLANS_PATH,
  launchSignedIn,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPairing,
  stubPlans,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { challengeErrorMessage } from './challengeErrorMessage';
import {
  LEAVE_SHEET_BODY,
  LEAVE_SHEET_CLOSE_LABEL,
  LEAVE_SHEET_TITLE,
  LEAVE_THE_GAME,
  LEAVE_THIS_GAME,
  LEAVING,
} from './leaveGamePresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';

const DEPARTURE_PATH = `/api/v1/challenges/${CHALLENGE}/departure`;

/** Saturday the 12th of September 2026, 11:00 in Warsaw — the instant every fold here is against. */
const READ_AT = '2026-09-12T09:00:00Z';

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

const PAIR: Wire['ConversationMemberSchema'][] = [
  { player_id: ME, nickname: 'me_' },
  { player_id: TOMEK, nickname: 'tomek.p' },
];

function game(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: GAME,
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: '2026-09-08T09:00:00Z',
    entry_closes_at: '2026-09-20T09:00:00Z',
    seats: [
      { side: 'A', player_id: ME, nickname: 'me_' },
      { side: 'B', player_id: TOMEK, nickname: 'tomek.p' },
    ],
    proposals: [],
    ...over,
  };
}

function plan(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return {
    challenge_id: CHALLENGE,
    anchor: '2026-09-08T09:00:00Z',
    place: null,
    day: null,
    hour: null,
    agreed_point: null,
    locked_at: null,
    ...over,
  };
}

/** The whole plan, agreed for a day that is still ahead. */
const AHEAD = plan({
  place: 'Zabłocie Sport, court 3',
  day: '2026-09-19',
  hour: '18:00',
  agreed_point: '2026-09-19T16:00:00Z',
});

/** The whole plan, agreed for yesterday evening — the moment has passed. */
const PASSED = plan({
  place: 'Zabłocie Sport, court 3',
  day: '2026-09-11',
  hour: '18:00',
  agreed_point: '2026-09-11T16:00:00Z',
});

/** The court after the opponent left: the seat open, and the rung above the clock. */
const SHORT: Wire['GameSchema']['seats'] = [
  { side: 'A', player_id: ME, nickname: 'me_' },
  { side: 'B', player_id: null, nickname: null },
];

/** What the route says back: the challenge as it now stands, the caller's seat `LEFT`. */
const LEFT: Wire['ChallengeSchema'] = {
  challenge_id: CHALLENGE,
  organiser_id: TOMEK,
  standing: 'LINE_UP_INCOMPLETE',
  sport: 'PADEL',
  opened_at: '2026-09-07T09:00:00Z',
  ended_at: null,
  seats: [
    { side: 'A', player_id: TOMEK, nickname: 'tomek.p', answer: 'ACCEPTED', answer_by: null },
    { side: 'B', player_id: ME, nickname: 'me_', answer: 'LEFT', answer_by: null },
  ],
};

const refusal = (code: string): AppError =>
  new AppError('conflict', 'business-conflict', 'test failure', { code });

let transport: Transport;

beforeEach(() => {
  onlineManager.setOnline(true);
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Every list the screen reads, and the room behind it. */
function stubTheWorld({
  games = [game()],
  plans = [],
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly plans?: readonly Wire['PlanSchema'][];
} = {}) {
  stubGames(transport, games, READ_AT);
  stubPlans(transport, plans);
  stubConversations(transport, [
    {
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: GAME,
      sport: 'PADEL',
      members: PAIR,
      people: PAIR,
      last_entry: null,
    },
  ]);
  stubConversation(transport, {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: GAME,
    sport: 'PADEL',
    members: PAIR,
    people: PAIR,
    entries: [],
  });
  stubEntries(transport, ROOM);
  stubPairing(transport, GAME, { refused: 409, code: 'pairing_is_history' });
}

/**
 * In at the screen's own address under Now, **from the rail** — so *back* has somewhere to go.
 *
 * Through the card's wide door on a full court, and by route on a court somebody left: since
 * [#419](https://github.com/Raketa02/Raketa/issues/419) that rung's door is the fill, which lands
 * in the builder rather than on this screen, and past the moment the card has no wide door at all.
 */
async function openFromNow(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/'));
  await screen.findByLabelText(/Padel/);
  const door = screen.queryByRole('button', { name: /Finish the plan|^Open$/ });
  if (door === null) act(() => router.push(`/games/${GAME}`));
  else fireEvent.press(door);
  await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
  await screen.findByText(OPEN_THE_CHAT);
}

/** The control, then the sheet's own act. */
async function leave() {
  fireEvent.press(await screen.findByRole('button', { name: LEAVE_THIS_GAME }));
  fireEvent.press(await screen.findByRole('button', { name: LEAVE_THE_GAME }));
}

describe('where the control is', () => {
  /** Quiet, destructive, and **last**: under the chat door and under *We played*. */
  it('is a secondary control at the bottom of the plan lead, after We played', async () => {
    await openFromNow();

    const control = await screen.findByRole('button', { name: LEAVE_THIS_GAME });
    const buttons = screen.getAllByRole('button').map((one) => one.props.accessibilityLabel);

    expect(buttons.indexOf(LEAVE_THIS_GAME)).toBeGreaterThan(buttons.indexOf(WE_PLAYED));
    expect(buttons.indexOf(LEAVE_THIS_GAME)).toBe(buttons.length - 1);
    expect(control.props.accessibilityState.busy).toBe(false);
  });

  it('is drawn with nothing agreed, and while the agreed moment is ahead', async () => {
    await openFromNow({ plans: [AHEAD] });

    expect(await screen.findByRole('button', { name: LEAVE_THIS_GAME })).toBeTruthy();
  });

  /**
   * **Once the moment has passed, leaving means nothing** (#411 rule 1) — the server refuses it,
   * and the client mirrors the rule rather than offering a control the act would refuse. A short
   * court past its moment is still on the plan lead, so this is the one case the rung alone
   * cannot hide.
   */
  it('is not drawn once the agreed moment has passed, even on a court somebody left', async () => {
    await openFromNow({ games: [game({ seats: SHORT })], plans: [PASSED] });

    await screen.findByText(OPEN_THE_CHAT);
    expect(screen.queryByRole('button', { name: LEAVE_THIS_GAME })).toBeNull();
  });

  it('is drawn on a court somebody else already left, while the moment is ahead', async () => {
    await openFromNow({ games: [game({ seats: SHORT })], plans: [AHEAD] });

    expect(await screen.findByRole('button', { name: LEAVE_THIS_GAME })).toBeTruthy();
  });
});

describe('the sheet', () => {
  /** §22.8: the title names the moment, the act is named once, the dismissal by what it does. */
  it('says what leaving does, in the words of the deck, and sends nothing until confirmed', async () => {
    await openFromNow();

    fireEvent.press(await screen.findByRole('button', { name: LEAVE_THIS_GAME }));

    expect(await screen.findByText(LEAVE_SHEET_TITLE)).toBeTruthy();
    for (const line of LEAVE_SHEET_BODY) expect(screen.getByText(line)).toBeTruthy();
    expect(screen.getByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();
    expect(screen.getByRole('button', { name: LEAVE_SHEET_CLOSE_LABEL })).toBeTruthy();
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toEqual([]);
  });

  it('is dismissed by Stay in, and nothing is sent', async () => {
    await openFromNow();

    fireEvent.press(await screen.findByRole('button', { name: LEAVE_THIS_GAME }));
    fireEvent.press(await screen.findByRole('button', { name: LEAVE_SHEET_CLOSE_LABEL }));

    await waitFor(() => expect(screen.queryByText(LEAVE_SHEET_TITLE)).toBeNull());
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toEqual([]);
    expect(screen.getByRole('button', { name: LEAVE_THIS_GAME })).toBeTruthy();
  });
});

describe('the leave', () => {
  /** Pending, never optimistic: the control goes busy, and the screen is not touched. */
  it('is busy while it is in flight, and the game is still on the screen', async () => {
    let answer: () => void = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('POST', DEPARTURE_PATH, async () => {
      await held;
      return json(LEFT);
    });

    await openFromNow();
    await leave();

    const busy = await screen.findByRole('button', { name: LEAVING });
    expect(busy.props.accessibilityState.busy).toBe(true);
    expect(screen).toHavePathname(`/games/${GAME}`);
    expect(screen.getByText(OPEN_THE_CHAT)).toBeTruthy();

    answer();
    await waitFor(() => expect(screen).toHavePathname('/'));
  });

  /**
   * **The card leaves the rail because the server no longer lists it**, not because the client
   * removed it: the games, the plans and the conversations are all re-read, and the screen goes
   * back to wherever it was opened from.
   */
  it('re-reads every list the seat touched and goes back', async () => {
    transport.on('POST', DEPARTURE_PATH, () => json(LEFT));

    await openFromNow();
    const games = transport.requestsTo('GET', GAMES_PATH).length;
    const plans = transport.requestsTo('GET', PLANS_PATH).length;
    const rooms = transport.requestsTo('GET', CONVERSATIONS_PATH).length;

    await leave();

    await waitFor(() => expect(screen).toHavePathname('/'));
    await waitFor(() => {
      expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(games);
      expect(transport.requestsTo('GET', PLANS_PATH).length).toBeGreaterThan(plans);
      expect(transport.requestsTo('GET', CONVERSATIONS_PATH).length).toBeGreaterThan(rooms);
    });
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toHaveLength(1);
  });
});

describe('a refused leave', () => {
  it('leaves the screen when no challenge of yours has that id', async () => {
    transport.on('POST', DEPARTURE_PATH, () => errorResponse(404, 'challenge_not_found'));

    await openFromNow();
    await leave();

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(screen.queryByRole('alert')).toBeNull();
  });

  /**
   * **A stale tap is a re-read, not a toast** (`actRefusal.ts`): the game moved under the finger,
   * and the fold the re-read lands on is the sentence. Four codes, one answer.
   */
  it.each([
    ['not_a_game_yet'],
    ['challenge_is_over'],
    ['game_is_history'],
    ['game_moment_has_passed'],
  ])('re-reads the game and says nothing on %s', async (code) => {
    transport.on('POST', DEPARTURE_PATH, () => errorResponse(409, code));

    await openFromNow();
    const games = transport.requestsTo('GET', GAMES_PATH).length;

    await leave();

    await waitFor(() =>
      expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(games),
    );
    expect(screen).toHavePathname(`/games/${GAME}`);
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.queryByText(challengeErrorMessage(refusal(code)))).toBeNull();
  });

  /** The re-read lands past the moment, and the control is gone with it. */
  it('re-folds the screen off the re-read, so the control disappears', async () => {
    transport.on('POST', DEPARTURE_PATH, () => errorResponse(409, 'game_moment_has_passed'));

    await openFromNow({ games: [game({ seats: SHORT })], plans: [AHEAD] });
    // The clock has moved on by the time the refusal is answered.
    stubGames(transport, [game({ seats: SHORT })], '2026-09-19T17:00:00Z');

    await leave();

    await waitFor(() => expect(screen.queryByRole('button', { name: LEAVE_THIS_GAME })).toBeNull());
    expect(screen.getByText(OPEN_THE_CHAT)).toBeTruthy();
  });

  /** A hold is a fact about the account, said where the act was refused. */
  it('says the held note on account_held, and stays', async () => {
    transport.on('POST', DEPARTURE_PATH, () => errorResponse(403, 'account_held'));

    await openFromNow();
    await leave();

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(challengeErrorMessage(refusal('account_held')))).toBeTruthy();
    expect(screen).toHavePathname(`/games/${GAME}`);
    expect(screen.getByRole('button', { name: LEAVE_THIS_GAME })).toBeTruthy();
  });

  /** The connection's absence is said once, in amber, and the control is greyed under it. */
  it('greys the control under an amber note when there is no connection', async () => {
    await openFromNow();
    await screen.findByRole('button', { name: LEAVE_THIS_GAME });

    onlineManager.setOnline(false);

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: LEAVE_THIS_GAME }).props.accessibilityState.disabled,
      ).toBe(true),
    );
    expect(screen.getByText(offlineMessage('does-not-resume'))).toBeTruthy();
  });
});
