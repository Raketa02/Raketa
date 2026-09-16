/**
 * ***Remove the challenge* from the Chats list, walked the way an organiser walks it**: the real
 * route tree, the real shell, the real rows, a finger on one of them, and only `fetch` faked.
 *
 * [#428](https://github.com/Raketa02/Raketa/issues/428)'s acceptance criteria for the list are
 * assertions in this file and opinions nowhere else — the organiser's row with no acceptances
 * reveals *Remove the challenge*, confirming calls the withdrawal route and the row is gone without
 * a refetch, and with one acceptance the same row reveals nothing; the sheet says it is gone for
 * the invitees too; a refused removal says so on the sheet and leaves the row in place; and the
 * revealed button is reachable by the row's accessibility action as well as by the swipe. The
 * challenge screen's own door is `challengeScreen.test.tsx`'s; *Call it off* for any player is
 * `callOff.test.tsx`'s.
 *
 * The finger is `test-support/swipe.ts`'. The words are the deck's —
 * `challengeDetailPresentation.ts` — and the refusal sentence is that deck's too, over
 * `challengeErrorMessage`'s fallback.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { onlineManager } from '@tanstack/react-query';

import { AppError, offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { gameKeys } from '@/features/games/types';
import { planKeys } from '@/features/plans/types';
import {
  CHALLENGES_PATH,
  CONVERSATIONS_PATH,
  GATE_USER,
  launchSignedIn,
  stubChallenges,
  stubConversations,
  stubGames,
  stubGate,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { swipe } from '@/test-support/swipe';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { challengeErrorMessage } from './challengeErrorMessage';
import {
  REMOVE_SHEET_BODY,
  REMOVE_SHEET_CLOSE_LABEL,
  REMOVE_SHEET_TITLE,
  REMOVE_THE_CHALLENGE,
  REMOVING,
  removeRefusalMessage,
} from './challengeDetailPresentation';
import { LEAVE_THE_GAME } from './leaveGamePresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'cccccccc-0000-4000-8000-000000000003';
const EWA = 'dddddddd-0000-4000-8000-000000000004';

const MY_SEND = 'ffffffff-0000-4000-8000-000000000006';
const MY_JOINED_SEND = 'ffffffff-0000-4000-8000-000000000007';
const THEIR_SEND = 'ffffffff-0000-4000-8000-000000000008';

const WITHDRAWAL_PATH = `/api/v1/challenges/${MY_SEND}/withdrawal`;
const READ_AT = '2026-09-12T09:00:00Z';
const ANSWER_BY = '2026-09-13T08:00:00Z';
const REVEAL = theme.size.swipeRow.reveal;

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

/** My padel four, just sent: two asked, nobody has answered — the row this ticket is about. */
const MY_SEND_ROW: Wire['ChallengeSchema'] = {
  challenge_id: MY_SEND,
  sport: 'PADEL',
  organiser_id: ME,
  standing: 'AWAITING_ANSWERS',
  opened_at: '2026-09-11T08:00:00Z',
  ended_at: null,
  seats: [
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'A', player_id: TOMEK, answer: null, answer_by: ANSWER_BY, name: 'tomek.p' },
    { side: 'B', player_id: OLA, answer: null, answer_by: ANSWER_BY, name: 'ola.k' },
    { side: 'B', player_id: null, answer: null, name: null },
  ],
};

/** My squash send that Ewa has already joined this morning: a court with somebody, nobody's to remove. */
const MY_JOINED_ROW: Wire['ChallengeSchema'] = {
  challenge_id: MY_JOINED_SEND,
  sport: 'SQUASH',
  organiser_id: ME,
  standing: 'ON',
  opened_at: '2026-09-12T07:00:00Z',
  ended_at: null,
  seats: [
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'B', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
  ],
};

/** Somebody else's send that I accepted: the invitee's row, which is never mine to remove. */
const THEIR_SEND_ROW: Wire['ChallengeSchema'] = {
  challenge_id: THEIR_SEND,
  sport: 'TENNIS',
  organiser_id: OLA,
  standing: 'AWAITING_ANSWERS',
  opened_at: '2026-09-11T06:00:00Z',
  ended_at: null,
  seats: [
    { side: 'A', player_id: OLA, answer: 'ACCEPTED', name: 'ola.k' },
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'B', player_id: TOMEK, answer: null, answer_by: ANSWER_BY, name: 'tomek.p' },
    { side: 'B', player_id: null, answer: null, name: null },
  ],
};

/** The same court once Tomek has said yes — under the finger, or on the next read. */
const TOMEK_JOINED: Wire['ChallengeSchema'] = {
  ...MY_SEND_ROW,
  seats: [
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', name: 'tomek.p' },
    { side: 'B', player_id: OLA, answer: null, answer_by: ANSWER_BY, name: 'ola.k' },
    { side: 'B', player_id: null, answer: null, name: null },
  ],
};

/** What the route says back: withdrawn, every seat exactly as it was. */
const REMOVED: Wire['ChallengeSchema'] = {
  ...MY_SEND_ROW,
  standing: 'WITHDRAWN',
  ended_at: '2026-09-12T09:05:00Z',
};

const refusal = (code: string): AppError =>
  new AppError('conflict', 'business-conflict', 'test failure', { code });

let transport: Transport;

beforeEach(() => {
  onlineManager.setOnline(true);
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubGames(transport, [], READ_AT);
  stubPlans(transport, []);
  stubConversations(transport, []);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app with the three rows, and open the Chats tab. */
async function openChats(
  rows: readonly Wire['ChallengeSchema'][] = [MY_SEND_ROW, MY_JOINED_ROW, THEIR_SEND_ROW],
) {
  stubChallenges(transport, rows, READ_AT);
  await launchSignedIn();

  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));
  await screen.findByLabelText(/^tomek\.p and ola\.k, Padel, Waiting/);
}

const mySend = () => screen.getByLabelText(/^tomek\.p and ola\.k, Padel, Waiting/);
const mySendIfListed = () => screen.queryByLabelText(/^tomek\.p and ola\.k, Padel, Waiting/);
const myJoinedSend = () => screen.getByLabelText(/^ewa\.m, Squash/);
const theirSend = () => screen.getByLabelText(/^ola\.k and tomek\.p, Tennis/);

/** My row **while the sheet is up** — hidden from a listener behind the sheet, and still on the screen. */
const mySendUnderTheSheet = () =>
  screen.getByLabelText(/^tomek\.p and ola\.k, Padel, Waiting/, { includeHiddenElements: true });

/**
 * The removal answers, and **the server's list tells the truth from then on**: the court reads
 * `WITHDRAWN`. A stub that went on serving the live row would hand it back on the re-read, which
 * is a server that never learned of the act.
 */
function removalAnswers(reply: () => Response | Promise<Response> = () => json(REMOVED)) {
  transport.on('POST', WITHDRAWAL_PATH, async () => {
    const answer = await reply();
    if (answer.ok) stubChallenges(transport, [REMOVED, MY_JOINED_ROW, THEIR_SEND_ROW], READ_AT);
    return answer;
  });
}

/** Swipe my row open, and press what it reveals. */
async function revealAndPress() {
  swipe(mySend(), -REVEAL);
  fireEvent.press(await screen.findByRole('button', { name: REMOVE_THE_CHALLENGE }));
}

/** The sheet is up. Confirm on it. */
function confirm() {
  fireEvent.press(screen.getByRole('button', { name: REMOVE_THE_CHALLENGE }));
}

describe('the swipe', () => {
  /** ADR-0165 §6's second row: the organiser's challenge, while nobody has joined. */
  it('reveals Remove the challenge on the organiser’s row while nobody has joined', async () => {
    await openChats();

    expect(swipe(mySend(), -REVEAL)).toBe(true);

    expect(await screen.findByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeTruthy();
    expect(screen.queryByText(REMOVE_SHEET_TITLE)).toBeNull();
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toEqual([]);
  });

  /** With one acceptance the same row reveals nothing — no dead controls (#324). */
  it('reveals nothing on the organiser’s row once somebody has joined', async () => {
    await openChats([TOMEK_JOINED, MY_JOINED_ROW, THEIR_SEND_ROW]);

    expect(swipe(mySend(), -REVEAL)).toBe(false);
    expect(swipe(myJoinedSend(), -REVEAL)).toBe(false);
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
    expect(mySend().props.accessibilityActions).toBeUndefined();
  });

  it('reveals nothing on an invitee’s row', async () => {
    await openChats();

    expect(swipe(theirSend(), -REVEAL)).toBe(false);
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
    expect(theirSend().props.accessibilityActions).toBeUndefined();
  });
});

describe('the sheet', () => {
  /** It says it is gone for the invitees too — the one line ADR-0165 §6 asks for. */
  it('says it is gone for the people asked too, and sends nothing until confirmed', async () => {
    await openChats();

    await revealAndPress();

    expect(await screen.findByText(REMOVE_SHEET_TITLE)).toBeTruthy();
    for (const line of REMOVE_SHEET_BODY) expect(screen.getByText(line)).toBeTruthy();
    expect(screen.getByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeTruthy();
    expect(screen.getByRole('button', { name: REMOVE_SHEET_CLOSE_LABEL })).toBeTruthy();
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toEqual([]);
  });

  it('is dismissed by Keep it open, with the row closed and nothing sent', async () => {
    await openChats();

    await revealAndPress();
    fireEvent.press(await screen.findByRole('button', { name: REMOVE_SHEET_CLOSE_LABEL }));

    await waitFor(() => expect(screen.queryByText(REMOVE_SHEET_TITLE)).toBeNull());
    expect(screen.queryByRole('button', { name: REMOVE_THE_CHALLENGE })).toBeNull();
    expect(mySend()).toBeTruthy();
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toEqual([]);
  });

  /** A swipe is never the only path: the row offers the act in the rotor, under the act's own word. */
  it('opens from the row’s accessibility action as well as from the swipe', async () => {
    await openChats();

    const row = mySend();
    expect(row.props.accessibilityActions).toEqual([
      expect.objectContaining({ label: REMOVE_THE_CHALLENGE }),
    ]);
    const [action] = row.props.accessibilityActions as readonly { name: string }[];

    fireEvent(row, 'accessibilityAction', { nativeEvent: { actionName: action?.name } });

    expect(await screen.findByText(REMOVE_SHEET_TITLE)).toBeTruthy();
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toEqual([]);
  });
});

describe('the removal', () => {
  /**
   * **Gone without a refetch.** The reply says the challenge is withdrawn with nobody else on it,
   * and an own removal leaves the inbox at once — so the reply is what takes the row away, and the
   * re-read that follows is held here to prove it had nothing to do with it.
   */
  it('takes the row away on the reply, before the list is re-read, and leaves the others', async () => {
    await openChats();
    transport.on('POST', WITHDRAWAL_PATH, () => json(REMOVED));

    const held = new Promise<Response>(() => undefined);
    transport.on('GET', CHALLENGES_PATH, () => held);

    await revealAndPress();
    confirm();

    await waitFor(() => expect(mySendIfListed()).toBeNull());
    expect(myJoinedSend()).toBeTruthy();
    expect(theirSend()).toBeTruthy();
    expect(screen.queryByText(REMOVE_SHEET_TITLE)).toBeNull();
    expect(transport.requestsTo('POST', WITHDRAWAL_PATH)).toHaveLength(1);
  });

  /**
   * And then every list the act touches is re-read — the withdraw's own cache effect: the
   * challenges, the rooms (invalidated rather than patched, because the reply says nothing about
   * one), and the games and the plans marked stale.
   */
  it('re-reads the challenges and the rooms, and marks the games and the plans stale', async () => {
    await openChats();
    removalAnswers();
    queryClient.setQueryData(gameKeys.list(), []);
    queryClient.setQueryData(planKeys.list(), []);
    const before = {
      rooms: transport.requestsTo('GET', CONVERSATIONS_PATH).length,
      challenges: transport.requestsTo('GET', CHALLENGES_PATH).length,
    };

    await revealAndPress();
    confirm();

    await waitFor(() => {
      expect(transport.requestsTo('GET', CONVERSATIONS_PATH).length).toBeGreaterThan(before.rooms);
      expect(transport.requestsTo('GET', CHALLENGES_PATH).length).toBeGreaterThan(
        before.challenges,
      );
    });
    expect(queryClient.getQueryState(gameKeys.list())?.isInvalidated).toBe(true);
    expect(queryClient.getQueryState(planKeys.list())?.isInvalidated).toBe(true);
    // And the server's own read agrees: the row is not back.
    expect(mySendIfListed()).toBeNull();
  });

  /** Pending, never optimistic: the sheet stays up and its act goes busy until the reply lands. */
  it('is busy on the sheet while it is in flight, and the row is still there', async () => {
    let answer: () => void = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    removalAnswers(async () => {
      await held;
      return json(REMOVED);
    });
    await openChats();

    await revealAndPress();
    confirm();

    const busy = await screen.findByRole('button', { name: REMOVING });
    expect(busy.props.accessibilityState.busy).toBe(true);
    expect(mySendUnderTheSheet()).toBeTruthy();

    answer();
    await waitFor(() =>
      expect(
        screen.queryByLabelText(/^tomek\.p and ola\.k, Padel, Waiting/, {
          includeHiddenElements: true,
        }),
      ).toBeNull(),
    );
  });
});

describe('a refused removal', () => {
  /**
   * **Somebody said yes under the finger.** The sheet says so, in words, and the row stays; the
   * list is re-read once the sheet is dismissed, and the row that comes back is a court with
   * somebody — which reveals nothing.
   */
  it('says why on the sheet when somebody has joined, and the row stops moving once re-read', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => {
      // The server's truth from here on: Tomek is in.
      stubChallenges(transport, [TOMEK_JOINED, MY_JOINED_ROW, THEIR_SEND_ROW], READ_AT);
      return errorResponse(409, 'somebody_has_joined');
    });
    await openChats();
    const challenges = transport.requestsTo('GET', CHALLENGES_PATH).length;

    await revealAndPress();
    confirm();

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(removeRefusalMessage(refusal('somebody_has_joined')))).toBeTruthy();
    expect(screen.getByText(REMOVE_SHEET_TITLE)).toBeTruthy();
    expect(mySendUnderTheSheet()).toBeTruthy();
    expect(transport.requestsTo('GET', CHALLENGES_PATH)).toHaveLength(challenges);

    fireEvent.press(screen.getByRole('button', { name: REMOVE_SHEET_CLOSE_LABEL }));

    await waitFor(() =>
      expect(transport.requestsTo('GET', CHALLENGES_PATH).length).toBeGreaterThan(challenges),
    );
    await waitFor(() => expect(mySend().props.accessibilityActions).toBeUndefined());
    expect(swipe(mySend(), -REVEAL)).toBe(false);
  });

  /** A court that ended under the finger goes when the server says so — on Keep it open. */
  it('re-reads the list once the sheet is dismissed, and a court that is over goes then', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => {
      stubChallenges(
        transport,
        [
          {
            ...MY_SEND_ROW,
            standing: 'DECLINED',
            ended_at: READ_AT,
            ended_by: TOMEK,
            seats: [
              { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
              { side: 'A', player_id: TOMEK, answer: 'DECLINED', name: 'tomek.p' },
              { side: 'B', player_id: OLA, answer: 'DECLINED', name: 'ola.k' },
              { side: 'B', player_id: null, answer: null, name: null },
            ],
          },
          MY_JOINED_ROW,
          THEIR_SEND_ROW,
        ],
        READ_AT,
      );
      return errorResponse(409, 'challenge_is_over');
    });
    await openChats();

    await revealAndPress();
    confirm();
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(removeRefusalMessage(refusal('challenge_is_over')))).toBeTruthy();
    expect(mySendUnderTheSheet()).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: REMOVE_SHEET_CLOSE_LABEL }));

    await waitFor(() => expect(mySendIfListed()).toBeNull());
    // The ended row is still news to the organiser — a no of somebody else's — and reveals
    // nothing; it names the one person the sentence is about (ADR-0172 §7).
    const ended = await screen.findByLabelText(/^tomek\.p, Padel, tomek\.p said no/);
    expect(swipe(ended, -REVEAL)).toBe(false);
  });

  /** Each refusal has its own sentence, and neither is the fallback. */
  it('has words of its own for somebody having joined and for a court that is over', () => {
    for (const code of ['somebody_has_joined', 'challenge_is_over']) {
      expect(removeRefusalMessage(refusal(code))).not.toBe(challengeErrorMessage(refusal(code)));
    }
    expect(removeRefusalMessage(refusal('account_held'))).toBe(
      challengeErrorMessage(refusal('account_held')),
    );
  });

  /** A hold is a fact about the account, said where the act was refused, and owes no re-read. */
  it('says the held note on account_held, and re-reads nothing after it', async () => {
    transport.on('POST', WITHDRAWAL_PATH, () => errorResponse(403, 'account_held'));
    await openChats();
    const challenges = transport.requestsTo('GET', CHALLENGES_PATH).length;

    await revealAndPress();
    confirm();

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(challengeErrorMessage(refusal('account_held')))).toBeTruthy();
    expect(mySendUnderTheSheet()).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: REMOVE_SHEET_CLOSE_LABEL }));
    await waitFor(() => expect(screen.queryByText(REMOVE_SHEET_TITLE)).toBeNull());

    expect(transport.requestsTo('GET', CHALLENGES_PATH)).toHaveLength(challenges);
    expect(mySend()).toBeTruthy();
  });

  /** The connection's absence greys the act under an amber note, as every act in this feature. */
  it('greys the act when there is no connection', async () => {
    await openChats();
    await revealAndPress();
    await screen.findByText(REMOVE_SHEET_TITLE);

    act(() => onlineManager.setOnline(false));

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: REMOVE_THE_CHALLENGE }).props.accessibilityState
          .disabled,
      ).toBe(true),
    );
    expect(screen.getByText(offlineMessage('does-not-resume'))).toBeTruthy();
  });
});
