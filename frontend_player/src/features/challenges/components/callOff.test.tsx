/**
 * ***Call it off*, walked the way a player walks it**: the real route tree, the real shell, the
 * game screen's plan lead, and only `fetch` faked.
 *
 * [#419](https://github.com/Raketa02/Raketa/issues/419) §2's acceptance criteria for the act are
 * assertions in this file and opinions nowhere else — the control is drawn on the *Needs a player*
 * arm alone, above *Leave this game*, for the organiser and, once the organiser has left, for
 * anyone still on the court, and for nobody else; the sheet says the four things `the-words.md`
 * §22.9 fixes for a court that has been a game; a call-off in flight is busy and never optimistic;
 * success re-reads every list the act touched and **stays**, so the screen re-folds into the
 * called-off arm; and each refusal code costs the screen exactly what `actRefusal.ts` says it does.
 * The ending's card is `nowRail.test.tsx`'s and its screen is `result.test.tsx`'s.
 *
 * The words are the deck's — `callOffPresentation.ts` — and the refusal sentence is
 * `challengeErrorMessage`'s, as it is for every write in this feature.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { IT_WAS_CALLED_OFF } from '@/features/games/types';
import { AppError, offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  CHALLENGES_PATH,
  CONVERSATIONS_PATH,
  GAMES_PATH,
  GATE_USER,
  PLANS_PATH,
  launchSignedIn,
  stubChallenges,
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
  CALL_IT_OFF,
  CALL_OFF_SHEET_BODY,
  CALL_OFF_SHEET_CLOSE_LABEL,
  CALL_OFF_SHEET_TITLE,
  CALLING_IT_OFF,
} from './callOffPresentation';
import { LEAVE_THIS_GAME } from './leaveGamePresentation';

const ME = GATE_USER.id;
const KASIA = 'cccccccc-0000-4000-8000-000000000003';
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const MAREK = 'dddddddd-0000-4000-8000-000000000004';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';

const WITHDRAWAL_PATH = `/api/v1/challenges/${CHALLENGE}/withdrawal`;

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

const THREE: Wire['ConversationMemberSchema'][] = [
  { player_id: ME, nickname: 'me_' },
  { player_id: KASIA, nickname: 'kasia_w' },
  { player_id: TOMEK, nickname: 'tomek.p' },
];

/** A padel four after Marek left: three in, one open — the court every case here is read on. */
const SHORT: Wire['GameSchema']['seats'] = [
  { side: 'A', player_id: ME, nickname: 'me_' },
  { side: 'A', player_id: KASIA, nickname: 'kasia_w' },
  { side: 'B', player_id: TOMEK, nickname: 'tomek.p' },
  { side: 'B', player_id: null, nickname: null },
];

const FULL: Wire['GameSchema']['seats'] = [
  ...SHORT.slice(0, 3),
  { side: 'B', player_id: MAREK, nickname: 'marekb' },
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
    seats: SHORT,
    proposals: [],
    ...over,
  };
}

/**
 * The same court on the challenge list — **where the organiser is a fact** (ADR-0149 §3's join).
 * Tomek organised it unless a case says otherwise, and Marek's seat reads `LEFT`.
 */
function row(over: Partial<Wire['ChallengeSchema']> = {}): Wire['ChallengeSchema'] {
  return {
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    organiser_id: TOMEK,
    standing: 'LINE_UP_INCOMPLETE',
    opened_at: '2026-09-07T09:00:00Z',
    ended_at: null,
    seats: [
      { side: 'A', player_id: ME, nickname: 'me_', answer: 'ACCEPTED', answer_by: null },
      { side: 'A', player_id: KASIA, nickname: 'kasia_w', answer: 'ACCEPTED', answer_by: null },
      { side: 'B', player_id: TOMEK, nickname: 'tomek.p', answer: 'ACCEPTED', answer_by: null },
      { side: 'B', player_id: MAREK, nickname: 'marekb', answer: 'LEFT', answer_by: null },
    ],
    ...over,
  };
}

/** The court once its organiser has left too: two seats open, and the exit fallen back to us. */
const ORGANISER_LEFT = row({
  seats: [
    { side: 'A', player_id: ME, nickname: 'me_', answer: 'ACCEPTED', answer_by: null },
    { side: 'A', player_id: KASIA, nickname: 'kasia_w', answer: 'ACCEPTED', answer_by: null },
    { side: 'B', player_id: TOMEK, nickname: 'tomek.p', answer: 'LEFT', answer_by: null },
    { side: 'B', player_id: MAREK, nickname: 'marekb', answer: 'LEFT', answer_by: null },
  ],
});

const TWO_SHORT: Wire['GameSchema']['seats'] = [
  ...SHORT.slice(0, 2),
  { side: 'B', player_id: null, nickname: null },
  { side: 'B', player_id: null, nickname: null },
];

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

/** The whole plan, agreed for yesterday evening — the moment has passed. */
const PASSED = plan({
  place: 'Zabłocie Sport, court 3',
  day: '2026-09-11',
  hour: '18:00',
  agreed_point: '2026-09-11T16:00:00Z',
});

/** What the route says back: the challenge as it now stands, withdrawn. */
const WITHDRAWN: Wire['ChallengeSchema'] = row({
  standing: 'WITHDRAWN',
  ended_at: '2026-09-12T09:05:00Z',
});

/** The game once the act has landed and the list has been re-read: the fourth end, dated. */
const CALLED_OFF = game({
  standing: 'CALLED_OFF',
  entry_closes_at: null,
  called_off_at: '2026-09-12T09:05:00Z',
});

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

/** Every list the screen reads, the challenge list the control joins, and the room behind it. */
function stubTheWorld({
  games = [game()],
  plans = [],
  challenges = [row()],
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly plans?: readonly Wire['PlanSchema'][];
  readonly challenges?: readonly Wire['ChallengeSchema'][];
} = {}) {
  stubGames(transport, games, READ_AT);
  stubPlans(transport, plans);
  stubChallenges(transport, challenges, READ_AT);
  stubConversations(transport, [
    {
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: GAME,
      sport: 'PADEL',
      members: THREE,
      people: THREE,
      last_entry: null,
    },
  ]);
  stubConversation(transport, {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: GAME,
    sport: 'PADEL',
    members: THREE,
    people: THREE,
    entries: [],
  });
  stubEntries(transport, ROOM);
  stubPairing(transport, GAME, { refused: 409, code: 'pairing_is_history' });
}

/**
 * In at the screen's own address under Now, **pushed from the rail** so *back* has somewhere to
 * go. By route rather than through the card's door, because on this rung the door is the fill
 * (#419 §1) and what this suite walks is the act beneath it.
 */
async function openTheGame(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn();
  await waitFor(() => expect(screen).toHavePathname('/'));
  act(() => router.push(`/games/${GAME}`));
  await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
  await screen.findByText(OPEN_THE_CHAT);
}

/** The control, then the sheet's own act — one label, and the sheet hides the first. */
async function callItOff() {
  fireEvent.press(await screen.findByRole('button', { name: CALL_IT_OFF }));
  await screen.findByText(CALL_OFF_SHEET_TITLE);
  fireEvent.press(screen.getByRole('button', { name: CALL_IT_OFF }));
}

describe('who may call it off', () => {
  /** The organiser's, while they are on the court — and it sits above *Leave this game*. */
  it('is drawn for the organiser, secondary, above Leave this game', async () => {
    await openTheGame({ challenges: [row({ organiser_id: ME })] });

    const control = await screen.findByRole('button', { name: CALL_IT_OFF });
    const buttons = screen.getAllByRole('button').map((one) => one.props.accessibilityLabel);

    expect(buttons.indexOf(CALL_IT_OFF)).toBeLessThan(buttons.indexOf(LEAVE_THIS_GAME));
    expect(buttons.indexOf(CALL_IT_OFF)).toBe(buttons.length - 2);
    expect(control.props.accessibilityState.busy).toBe(false);
  });

  it('is not drawn for anybody else while the organiser is on the court', async () => {
    await openTheGame();

    await screen.findByRole('button', { name: LEAVE_THIS_GAME });
    expect(screen.queryByRole('button', { name: CALL_IT_OFF })).toBeNull();
  });

  /** ADR-0163: once the organiser's own seat is open, the exit falls back to whoever is left. */
  it('is drawn for any remaining player once the organiser has left', async () => {
    await openTheGame({ games: [game({ seats: TWO_SHORT })], challenges: [ORGANISER_LEFT] });

    expect(await screen.findByRole('button', { name: CALL_IT_OFF })).toBeTruthy();
  });

  /**
   * Only while a seat is open: a full court that will not play lets its window lapse. **And the
   * join is not asked**: the list the tab bar holds is not refetched for an answer nothing draws.
   */
  it('is not drawn on a full court, even for the organiser, and asks the list nothing', async () => {
    await openTheGame({
      games: [game({ seats: FULL })],
      challenges: [row({ organiser_id: ME, standing: 'ON' })],
    });

    await screen.findByRole('button', { name: LEAVE_THIS_GAME });
    expect(screen.queryByRole('button', { name: CALL_IT_OFF })).toBeNull();
    // The one read is the tab bar's, at launch.
    expect(transport.requestsTo('GET', CHALLENGES_PATH)).toHaveLength(1);
  });

  /**
   * **The one act left on a short court past its moment.** The fill and the leave both mirror
   * `game_moment_has_passed` and stand down; the withdraw is not guarded by the moment — a court
   * whose window has closed is withdrawn all the same — so this control stays.
   */
  it('is still drawn once the agreed moment has passed, when nothing else is', async () => {
    await openTheGame({ plans: [PASSED], challenges: [row({ organiser_id: ME })] });

    expect(await screen.findByRole('button', { name: CALL_IT_OFF })).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE_THIS_GAME })).toBeNull();
  });

  /** ADR-0149 §3's join fails soft: no row on the list, no organiser fact, no control. */
  it('is not drawn where the challenge list has no row for the court', async () => {
    await openTheGame({ challenges: [] });

    await screen.findByRole('button', { name: LEAVE_THIS_GAME });
    expect(screen.queryByRole('button', { name: CALL_IT_OFF })).toBeNull();
  });
});

describe('the sheet', () => {
  /** §22.9: the withdraw's sheet on a court that has been a game — the moment, the three lines, the act, the way out. */
  it('says what calling it off does, in the words of the deck, and sends nothing until confirmed', async () => {
    await openTheGame({ challenges: [row({ organiser_id: ME })] });

    fireEvent.press(await screen.findByRole('button', { name: CALL_IT_OFF }));

    expect(await screen.findByText(CALL_OFF_SHEET_TITLE)).toBeTruthy();
    for (const line of CALL_OFF_SHEET_BODY) expect(screen.getByText(line)).toBeTruthy();
    expect(screen.getByRole('button', { name: CALL_IT_OFF })).toBeTruthy();
    expect(screen.getByRole('button', { name: CALL_OFF_SHEET_CLOSE_LABEL })).toBeTruthy();
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toEqual([]);
  });

  it('is dismissed by Keep it, and nothing is sent', async () => {
    await openTheGame({ challenges: [row({ organiser_id: ME })] });

    fireEvent.press(await screen.findByRole('button', { name: CALL_IT_OFF }));
    fireEvent.press(await screen.findByRole('button', { name: CALL_OFF_SHEET_CLOSE_LABEL }));

    await waitFor(() => expect(screen.queryByText(CALL_OFF_SHEET_TITLE)).toBeNull());
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toEqual([]);
    expect(screen.getByRole('button', { name: CALL_IT_OFF })).toBeTruthy();
  });
});

describe('the call-off', () => {
  /** Pending, never optimistic: the control goes busy, and the screen is not touched. */
  it('is busy while it is in flight, and the game is still on the screen', async () => {
    let answer: () => void = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('POST', WITHDRAWAL_PATH, async () => {
      await held;
      return json(WITHDRAWN);
    });

    await openTheGame({ challenges: [row({ organiser_id: ME })] });
    await callItOff();

    const busy = await screen.findByRole('button', { name: CALLING_IT_OFF });
    expect(busy.props.accessibilityState.busy).toBe(true);
    expect(screen.getByText(OPEN_THE_CHAT)).toBeTruthy();

    stubGames(transport, [CALLED_OFF], READ_AT);
    answer();
    await screen.findByText(IT_WAS_CALLED_OFF);
  });

  /**
   * **The act is the withdraw**, on the challenge's own route with an empty body — and it stays:
   * the games, the plans, the rooms and the challenges are all re-read, and the screen re-folds
   * into the called-off arm off the games list, with the plan and the doors gone.
   */
  it('re-reads every list the act touched and stays, re-folded into the called-off arm', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => json(WITHDRAWN));

    await openTheGame({ challenges: [row({ organiser_id: ME })] });
    const games = transport.requestsTo('GET', GAMES_PATH).length;
    const plans = transport.requestsTo('GET', PLANS_PATH).length;
    const rooms = transport.requestsTo('GET', CONVERSATIONS_PATH).length;
    const challenges = transport.requestsTo('GET', CHALLENGES_PATH).length;
    stubGames(transport, [CALLED_OFF], READ_AT);

    await callItOff();

    expect(await screen.findByText(IT_WAS_CALLED_OFF)).toBeTruthy();
    expect(screen).toHavePathname(`/games/${GAME}`);
    await waitFor(() => {
      expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(games);
      expect(transport.requestsTo('GET', PLANS_PATH).length).toBeGreaterThan(plans);
      expect(transport.requestsTo('GET', CONVERSATIONS_PATH).length).toBeGreaterThan(rooms);
      expect(transport.requestsTo('GET', CHALLENGES_PATH).length).toBeGreaterThan(challenges);
    });
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toHaveLength(1);
    expect(screen.queryByText(OPEN_THE_CHAT)).toBeNull();
    expect(screen.queryByRole('button', { name: CALL_IT_OFF })).toBeNull();
    expect(screen.queryByRole('button', { name: LEAVE_THIS_GAME })).toBeNull();
  });
});

describe('a refused call-off', () => {
  it('leaves the screen when no challenge of yours has that id', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => errorResponse(404, 'challenge_not_found'));

    await openTheGame({ challenges: [row({ organiser_id: ME })] });
    await callItOff();

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(screen.queryByRole('alert')).toBeNull();
  });

  /**
   * **A stale tap is a re-read, not a toast** (`actRefusal.ts`): the court moved under the
   * finger, and the fold the re-read lands on is the sentence. Three codes, one answer.
   */
  it.each([['withdraw_is_the_organisers'], ['not_a_half_built_line_up'], ['challenge_is_over']])(
    're-reads the game and says nothing on %s',
    async (code) => {
      transport.on('POST', WITHDRAWAL_PATH, () => errorResponse(409, code));

      await openTheGame({ challenges: [row({ organiser_id: ME })] });
      const games = transport.requestsTo('GET', GAMES_PATH).length;

      await callItOff();

      await waitFor(() =>
        expect(transport.requestsTo('GET', GAMES_PATH).length).toBeGreaterThan(games),
      );
      expect(screen).toHavePathname(`/games/${GAME}`);
      expect(screen.queryByRole('alert')).toBeNull();
      expect(screen.queryByText(challengeErrorMessage(refusal(code)))).toBeNull();
    },
  );

  /** A hold is a fact about the account, said where the act was refused. */
  it('says the held note on account_held, and stays', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => errorResponse(403, 'account_held'));

    await openTheGame({ challenges: [row({ organiser_id: ME })] });
    await callItOff();

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(challengeErrorMessage(refusal('account_held')))).toBeTruthy();
    expect(screen).toHavePathname(`/games/${GAME}`);
    expect(screen.getByRole('button', { name: CALL_IT_OFF })).toBeTruthy();
  });

  /** The connection's absence is said once, in amber, and the control is greyed under it. */
  it('greys the control under an amber note when there is no connection', async () => {
    await openTheGame({ challenges: [row({ organiser_id: ME })] });
    await screen.findByRole('button', { name: CALL_IT_OFF });

    onlineManager.setOnline(false);

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: CALL_IT_OFF }).props.accessibilityState.disabled,
      ).toBe(true),
    );
    expect(screen.getAllByText(offlineMessage('does-not-resume')).length).toBeGreaterThan(0);
  });
});
