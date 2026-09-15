/**
 * ***Leave the game* from the Chats list, walked the way a player walks it**: the real route
 * tree, the real shell, the real rows, a finger on one of them, and only `fetch` faked.
 *
 * [#427](https://github.com/Raketa02/Raketa/issues/427)'s acceptance criteria are assertions in
 * this file and opinions nowhere else — a swipe past the threshold reveals *Leave the game* on a
 * chat row and a swipe short of it reveals nothing, the sheet names the consequence, confirming
 * calls the departure route and both rows are gone without a refetch, cancelling reveals nothing,
 * a refused departure says so on the sheet and leaves the row in place, and the revealed button
 * is reachable by the row's accessibility action as well as by the swipe. The challenge screen's
 * own door is `challengeFill.test.tsx`'s and `challengeScreen.test.tsx`'s; the game screen's
 * *Leave this game* is `leaveGame.test.tsx`'s and is unchanged.
 *
 * The finger is `test-support/swipe.ts`'. The words are the deck's — `leaveGamePresentation.ts`
 * — and the refusal sentence is that deck's too, over `challengeErrorMessage`'s fallback.
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
import { moved, swipe, touchDown } from '@/test-support/swipe';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { challengeErrorMessage } from './challengeErrorMessage';
import {
  LEAVE_FROM_THE_LIST_BODY,
  LEAVE_SHEET_CLOSE_LABEL,
  LEAVE_SHEET_TITLE,
  LEAVE_THE_GAME,
  LEAVING,
  leaveRefusalMessage,
} from './leaveGamePresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'cccccccc-0000-4000-8000-000000000003';

const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const OTHER_CHALLENGE = 'ffffffff-0000-4000-8000-000000000007';
const OTHER_ROOM = 'eeeeeeee-0000-4000-8000-000000000008';

const DEPARTURE_PATH = `/api/v1/challenges/${CHALLENGE}/departure`;
const READ_AT = '2026-09-12T09:00:00Z';
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

function member(playerId: string, name: string): Wire['ConversationMemberSchema'] {
  return { player_id: playerId, name };
}

/** The room a half-built padel four opened: the organiser and me, two seats still deciding. */
const PADEL_ROOM: Wire['ConversationRowSchema'] = {
  conversation_id: ROOM,
  challenge_id: CHALLENGE,
  game_id: null,
  sport: 'PADEL',
  members: [member(ME, 'me_'), member(TOMEK, 'tomek.p')],
  people: [member(ME, 'me_'), member(TOMEK, 'tomek.p')],
  last_entry: null,
};

/** A second room, so the list is a list and the one that goes can be told from the one that stays. */
const SQUASH_ROOM: Wire['ConversationRowSchema'] = {
  conversation_id: OTHER_ROOM,
  challenge_id: OTHER_CHALLENGE,
  game_id: null,
  sport: 'SQUASH',
  members: [member(ME, 'me_'), member(OLA, 'ola.k')],
  people: [member(ME, 'me_'), member(OLA, 'ola.k')],
  last_entry: null,
};

/** The same court as the inbox lists it — the obligation beside the room. */
const PADEL_CHALLENGE: Wire['ChallengeSchema'] = {
  challenge_id: CHALLENGE,
  sport: 'PADEL',
  organiser_id: TOMEK,
  standing: 'AWAITING_ANSWERS',
  opened_at: '2026-09-11T08:00:00Z',
  ended_at: null,
  seats: [
    { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', name: 'tomek.p' },
    { side: 'A', player_id: ME, answer: 'ACCEPTED', name: 'me_' },
    { side: 'B', player_id: null, answer: null, name: null },
    {
      side: 'B',
      player_id: OLA,
      answer: null,
      answer_by: '2026-09-13T08:00:00Z',
      name: 'ola.k',
    },
  ],
};

/** What the route says back: my seat open, the court still arranging without me. */
const LEFT: Wire['ChallengeSchema'] = {
  ...PADEL_CHALLENGE,
  seats: [
    { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', name: 'tomek.p' },
    { side: 'A', player_id: ME, answer: 'LEFT', name: 'me_' },
    { side: 'B', player_id: null, answer: null, name: null },
    {
      side: 'B',
      player_id: OLA,
      answer: null,
      answer_by: '2026-09-13T08:00:00Z',
      name: 'ola.k',
    },
  ],
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
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app with both rooms and the padel court's row, and open the Chats tab. */
async function openChats() {
  stubConversations(transport, [PADEL_ROOM, SQUASH_ROOM]);
  stubChallenges(transport, [PADEL_CHALLENGE], READ_AT);
  await launchSignedIn();

  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));
  await screen.findByLabelText(/^tomek\.p, Padel$/);
  // Both sections have landed: the obligation says *You're in*, the room says the sport alone.
  await screen.findByLabelText(/^tomek\.p and ola\.k, Padel, You/);
}

/** The padel **room's** row — told from the challenge row beside it by saying the sport alone. */
const padelRoom = () => screen.getByLabelText(/^tomek\.p, Padel$/);
const squashRoom = () => screen.getByLabelText(/^ola\.k, Squash$/);
const padelChallenge = () => screen.queryByLabelText(/^tomek\.p and ola\.k, Padel, You/);

/**
 * The padel room's row **while the sheet is up** — hidden from a listener behind the sheet, as
 * every surface under an overlay is, and still on the screen. A test that asserts the row stayed
 * asks for it the way the tree holds it.
 */
const padelRoomUnderTheSheet = () =>
  screen.getByLabelText(/^tomek\.p, Padel$/, { includeHiddenElements: true });

/**
 * The departure answers, and **the server's lists tell the truth from then on**: the room is gone
 * by membership and the court lists my seat `LEFT`. A stub that went on serving the old rows
 * would hand them back on the re-read, which is a server that never learned of the act.
 */
function departureAnswers(reply: () => Response | Promise<Response> = () => json(LEFT)) {
  transport.on('POST', DEPARTURE_PATH, async () => {
    const answer = await reply();
    if (answer.ok) {
      stubConversations(transport, [SQUASH_ROOM]);
      stubChallenges(transport, [LEFT], READ_AT);
    }
    return answer;
  });
}

/** Swipe the padel room open, and press what it reveals. */
async function revealAndPress() {
  swipe(padelRoom(), -REVEAL);
  fireEvent.press(await screen.findByRole('button', { name: LEAVE_THE_GAME }));
}

/** The sheet is up. Confirm on it. */
function confirm() {
  fireEvent.press(screen.getByRole('button', { name: LEAVE_THE_GAME }));
}

describe('the swipe', () => {
  it('reveals Leave the game on a chat row, once past the threshold', async () => {
    await openChats();

    swipe(padelRoom(), -REVEAL / 2);

    expect(await screen.findByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();
    expect(screen.queryByText(LEAVE_SHEET_TITLE)).toBeNull();
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toEqual([]);
  });

  it('reveals nothing short of the threshold, and leaves a scroll to the list', async () => {
    await openChats();

    swipe(padelRoom(), -REVEAL / 2 + 1);
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();

    // The list's own gesture: down the screen. The row does not claim it.
    touchDown(padelRoom());
    expect(moved(padelRoom(), -4, 40)).toBe(false);
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });

  /**
   * The obligation beside it is an **invitee's** challenge row, and an invitee's row reveals
   * nothing — the organiser's, while nobody has joined, is `removeFromTheList.test.tsx`'s (#428).
   */
  it('reveals nothing on the invitee’s challenge row beside it', async () => {
    await openChats();

    const row = padelChallenge();
    expect(row).not.toBeNull();
    if (row === null) return;

    expect(swipe(row, -REVEAL)).toBe(false);
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });
});

describe('the sheet', () => {
  it('names the consequence, and sends nothing until confirmed', async () => {
    await openChats();

    await revealAndPress();

    expect(await screen.findByText(LEAVE_SHEET_TITLE)).toBeTruthy();
    expect(screen.getByText(LEAVE_FROM_THE_LIST_BODY)).toBeTruthy();
    expect(screen.getByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();
    expect(screen.getByRole('button', { name: LEAVE_SHEET_CLOSE_LABEL })).toBeTruthy();
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toEqual([]);
  });

  /** Cancelling reveals nothing: the row closed behind the press, and nothing is sent. */
  it('is dismissed by Stay in, with the row closed and nothing sent', async () => {
    await openChats();

    await revealAndPress();
    fireEvent.press(await screen.findByRole('button', { name: LEAVE_SHEET_CLOSE_LABEL }));

    await waitFor(() => expect(screen.queryByText(LEAVE_SHEET_TITLE)).toBeNull());
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
    expect(padelRoom()).toBeTruthy();
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toEqual([]);
  });

  /**
   * A swipe is a gesture a screen reader consumes before the row sees it, so it is never the
   * only path: the row offers the act as an accessibility action, and taking it opens the sheet.
   */
  it('opens from the row’s accessibility action as well as from the swipe', async () => {
    await openChats();

    const row = padelRoom();
    expect(row.props.accessibilityActions).toEqual([
      expect.objectContaining({ label: LEAVE_THE_GAME }),
    ]);
    const [action] = row.props.accessibilityActions as readonly { name: string }[];

    fireEvent(row, 'accessibilityAction', { nativeEvent: { actionName: action?.name } });

    expect(await screen.findByText(LEAVE_SHEET_TITLE)).toBeTruthy();
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toEqual([]);
  });

  /** A row with nothing to reveal offers no action either — the squash room is somebody else's court too, so it does. */
  it('offers the action on every chat row, because every chat row is a court the reader is on', async () => {
    await openChats();

    expect(squashRoom().props.accessibilityActions).toEqual([
      expect.objectContaining({ label: LEAVE_THE_GAME }),
    ]);
  });
});

describe('the leave', () => {
  /**
   * **Gone without a refetch.** The reply says the reader's seat is `LEFT`, and membership is the
   * accepted seats — so the reply is what takes both rows away, and the re-reads that follow are
   * held here to prove they had nothing to do with it.
   */
  it('takes the chat row and the challenge row away at once, before any list is re-read', async () => {
    await openChats();
    transport.on('POST', DEPARTURE_PATH, () => json(LEFT));

    // Both lists this tab reads are held open after the act, so whatever disappears did so on
    // the reply and not on a server that was asked again.
    const held = new Promise<Response>(() => undefined);
    transport.on('GET', CONVERSATIONS_PATH, () => held);
    transport.on('GET', CHALLENGES_PATH, () => held);

    await revealAndPress();
    confirm();

    await waitFor(() => {
      expect(screen.queryByLabelText(/^tomek\.p, Padel$/)).toBeNull();
      expect(padelChallenge()).toBeNull();
    });
    expect(squashRoom()).toBeTruthy();
    expect(screen.queryByText(LEAVE_SHEET_TITLE)).toBeNull();
    expect(transport.requestsTo('POST', DEPARTURE_PATH)).toHaveLength(1);
  });

  /**
   * And then every list the seat touched is re-read, as the game screen's departure re-reads
   * them. The two lists this tab holds are refetched and counted; the games and the plans are not
   * mounted here, so they are seeded and asserted **stale** — an inactive query is marked and not
   * refetched, and the mark is the whole of the promise on a tab that does not read them.
   */
  it('re-reads the conversations and the challenges, and marks the games and the plans stale', async () => {
    await openChats();
    departureAnswers();
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
  });

  /** Pending, never optimistic: the sheet stays up and its act goes busy until the reply lands. */
  it('is busy on the sheet while it is in flight, and the rows are still there', async () => {
    let answer: () => void = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    departureAnswers(async () => {
      await held;
      return json(LEFT);
    });
    await openChats();

    await revealAndPress();
    confirm();

    const busy = await screen.findByRole('button', { name: LEAVING });
    expect(busy.props.accessibilityState.busy).toBe(true);
    expect(padelRoomUnderTheSheet()).toBeTruthy();

    answer();
    await waitFor(() =>
      expect(
        screen.queryByLabelText(/^tomek\.p, Padel$/, { includeHiddenElements: true }),
      ).toBeNull(),
    );
  });
});

describe('a refused leave', () => {
  /**
   * **The sheet says so, in words, and the row stays.** There is no fold on a list row for a
   * re-read to land on, so what the game screen answers by re-folding is answered here by the
   * sentence — and **nothing is re-read while it is being read**: the sheet is drawn inside the
   * row it is about, and a re-read landing *over* would take the row, and the sentence, away.
   */
  it.each([['game_moment_has_passed'], ['challenge_is_over'], ['game_is_history']])(
    'says why on the sheet and leaves the row in place on %s',
    async (code) => {
      transport.on('POST', DEPARTURE_PATH, () => errorResponse(409, code));
      await openChats();
      const before = {
        rooms: transport.requestsTo('GET', CONVERSATIONS_PATH).length,
        challenges: transport.requestsTo('GET', CHALLENGES_PATH).length,
      };

      await revealAndPress();
      confirm();

      expect(await screen.findByRole('alert')).toBeTruthy();
      expect(screen.getByText(leaveRefusalMessage(refusal(code)))).toBeTruthy();
      expect(screen.getByText(LEAVE_SHEET_TITLE)).toBeTruthy();
      expect(padelRoomUnderTheSheet()).toBeTruthy();
      expect(transport.requestsTo('GET', CONVERSATIONS_PATH)).toHaveLength(before.rooms);
      expect(transport.requestsTo('GET', CHALLENGES_PATH)).toHaveLength(before.challenges);

      // Stay in, and the row is where it was — reachable again, its neighbour beside it.
      fireEvent.press(screen.getByRole('button', { name: LEAVE_SHEET_CLOSE_LABEL }));
      await waitFor(() => expect(screen.queryByText(LEAVE_SHEET_TITLE)).toBeNull());
      expect(padelRoom()).toBeTruthy();
      expect(padelChallenge()).not.toBeNull();
    },
  );

  /**
   * **The re-read is owed, and paid on *Stay in*.** A court that has genuinely ended has no room
   * on the server's next read — a room without a game lives as long as its challenge — so once the
   * sentence has been read and the sheet dismissed, the lists are re-read and the row goes when the
   * server says it has, not a moment before.
   */
  it('re-reads the lists once the sheet is dismissed, and a court that is over goes then', async () => {
    transport.on('POST', DEPARTURE_PATH, () => {
      // The server's truth from here on: the court ended, and its room went with it.
      stubConversations(transport, [SQUASH_ROOM]);
      stubChallenges(transport, [{ ...LEFT, standing: 'DECLINED', ended_at: READ_AT }], READ_AT);
      return errorResponse(409, 'challenge_is_over');
    });
    await openChats();

    await revealAndPress();
    confirm();
    await screen.findByRole('alert');
    expect(padelRoomUnderTheSheet()).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: LEAVE_SHEET_CLOSE_LABEL }));

    await waitFor(() => expect(screen.queryByLabelText(/^tomek\.p, Padel$/)).toBeNull());
    expect(squashRoom()).toBeTruthy();
  });

  /** A refusal that is the account's, or the connection's, owes no re-read: nothing about the court moved. */
  it('re-reads nothing on account_held, on the sheet or after it', async () => {
    transport.on('POST', DEPARTURE_PATH, () => errorResponse(403, 'account_held'));
    await openChats();
    const rooms = transport.requestsTo('GET', CONVERSATIONS_PATH).length;

    await revealAndPress();
    confirm();
    await screen.findByRole('alert');
    fireEvent.press(screen.getByRole('button', { name: LEAVE_SHEET_CLOSE_LABEL }));
    await waitFor(() => expect(screen.queryByText(LEAVE_SHEET_TITLE)).toBeNull());

    expect(transport.requestsTo('GET', CONVERSATIONS_PATH)).toHaveLength(rooms);
  });

  /** Each refusal has its own sentence, and none of them is the fallback. */
  it('has words of its own for the moment having passed and for a court that is over', () => {
    for (const code of ['game_moment_has_passed', 'challenge_is_over', 'game_is_history']) {
      expect(leaveRefusalMessage(refusal(code))).not.toBe(challengeErrorMessage(refusal(code)));
    }
    expect(leaveRefusalMessage(refusal('account_held'))).toBe(
      challengeErrorMessage(refusal('account_held')),
    );
  });

  /** A hold is a fact about the account, said where the act was refused — the feature's sentence. */
  it('says the held note on account_held', async () => {
    transport.on('POST', DEPARTURE_PATH, () => errorResponse(403, 'account_held'));
    await openChats();

    await revealAndPress();
    confirm();

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText(challengeErrorMessage(refusal('account_held')))).toBeTruthy();
    expect(padelRoomUnderTheSheet()).toBeTruthy();
  });

  /** A second try after a refusal starts clean: the sentence goes with the press that caused it. */
  it('drops the refusal on the next confirm', async () => {
    let calls = 0;
    departureAnswers(() => {
      calls += 1;
      return calls === 1 ? errorResponse(409, 'game_moment_has_passed') : json(LEFT);
    });
    await openChats();

    await revealAndPress();
    confirm();
    await screen.findByRole('alert');
    confirm();

    await waitFor(() =>
      expect(
        screen.queryByLabelText(/^tomek\.p, Padel$/, { includeHiddenElements: true }),
      ).toBeNull(),
    );
    expect(screen.queryByRole('alert')).toBeNull();
  });

  /** The connection's absence greys the act under an amber note, as every act in this feature. */
  it('greys the act when there is no connection', async () => {
    await openChats();
    await revealAndPress();
    await screen.findByText(LEAVE_SHEET_TITLE);

    act(() => onlineManager.setOnline(false));

    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: LEAVE_THE_GAME }).props.accessibilityState.disabled,
      ).toBe(true),
    );
    expect(screen.getByText(offlineMessage('does-not-resume'))).toBeTruthy();
  });
});
