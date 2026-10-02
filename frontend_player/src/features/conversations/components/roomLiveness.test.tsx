/**
 * **Live, not live, and held** — [#365](https://github.com/Raketa02/Raketa/issues/365) walked the way a
 * member walks it: the real route tree, the real shell, the real row the room is opened from, the
 * real Query cache, and two things faked — `fetch`, and the socket.
 *
 * The socket's stand-in is `fakeLiveStream()` from `src/test-support/platform.ts`, beside the two
 * device fakes and for the same reason. **Every state this ticket is about is a state a test has to
 * be able to put the screen in**, and three of the four have no shipped way to reach them: a
 * severed stream needs a server that goes away, and a hold needs a case nobody on this platform can
 * open — the hold query's only registered implementation is the null object, which
 * `backend/app/seeds/plans.py` says in as many words. That is a **named exception** to the map's
 * reachability constraint, recorded in `domain/liveState.ts`, and this file is the *component tests
 * drive it* half of the same sentence.
 */

import { AccessibilityInfo, Animated } from 'react-native';

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  conversationPath,
  CONVERSATIONS_PATH,
  GAMES_PATH,
  GATE_USER,
  launchIntoClassicPlay,
  PLANS_PATH,
  planSlotPath,
  resetLiveStream,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubLiveStream,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { fakeLiveStream, type FakeLiveStream } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  noContent,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { sportLabel } from '@/features/onboarding/types';
import { QUICK_CHIP, cardStateWord } from '@/features/plans/types';

import { OPEN_THE_GAME, conversationHeaderLabel } from './conversationAccessibility';
import {
  COMPOSER_LABEL,
  LIVE_NOTE,
  SEND,
  headerSubline,
  roomOverLine,
  systemLineSentence,
  typingLine,
} from './conversationPresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';

const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';

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

const MEMBERS: Wire['ConversationMemberSchema'][] = [
  { player_id: ME, name: 'me_' },
  { player_id: TOMEK, name: 'tomek.p' },
];

function message(seq: number, authorId: string, text: string): Wire['MessageSchema'] {
  return {
    type: 'message',
    seq,
    author_id: authorId,
    sent_at: READ_AT,
    text,
    client_message_id: `client-${seq}`,
  };
}

function room(
  entries: readonly Wire['MessageSchema'][] = [],
  members: readonly Wire['ConversationMemberSchema'][] = MEMBERS,
): Wire['ConversationResponse'] {
  return {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: null,
    sport: 'PADEL',
    members: [...members],
    people: [...members],
    entries: [...entries],
  };
}

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';

/** The court's row on `GET /plans` — the challenge's, there from the room's opening. */
function plan(over: Partial<Wire['PlanSchema']> = {}): Wire['PlanSchema'] {
  return {
    challenge_id: CHALLENGE,
    anchor: READ_AT,
    place: null,
    day: null,
    hour: null,
    agreed_point: null,
    locked_at: null,
    ...over,
  };
}

/** The room's game, as `GET /games` lists it — arranged, the day still ahead. */
function game(standing: Wire['GameSchema']['standing'] = 'AWAITING_ENTRY'): Wire['GameSchema'] {
  return {
    game_id: GAME,
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing,
    planned_at: '2026-09-08T09:00:00Z',
    entry_closes_at: '2026-09-20T07:00:00Z',
    seats: [
      { side: 'A', player_id: ME, name: 'me_' },
      { side: 'B', player_id: TOMEK, name: 'tomek.p' },
    ],
    proposals: [],
    no_shows: [],
  };
}

const LISTED: Wire['ConversationRowSchema'] = {
  conversation_id: ROOM,
  challenge_id: CHALLENGE,
  game_id: null,
  sport: 'PADEL',
  members: MEMBERS,
  people: MEMBERS,
  last_entry: null,
};

let transport: Transport;
let channel: FakeLiveStream;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  channel = fakeLiveStream();
  stubLiveStream(channel);
});

afterEach(async () => {
  transport.restore();
  resetLiveStream();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/**
 * Let anything already on its way to the socket get there. A negative about the request log is only
 * honest after this: `httpRequest` awaits before it calls `fetch`, so a refetch issued on this tick
 * is recorded on a later one. An async `act` drains those microtasks — a timer would not, because
 * `expo-router/testing-library` runs this tree on fake ones — and it is enough: a nudge for this
 * room followed by this flush has its `/plans` re-read in the log, which is how the helper was sized.
 */
const settled = () =>
  act(async () => {
    await Promise.resolve();
  });

/** Land in the app, open Chats, tap the one row. The walk every case here starts with. */
async function openTheRoom(answer: Wire['ConversationResponse'] = room()) {
  stubConversations(transport, [LISTED]);
  stubConversation(transport, answer);
  stubEntries(transport, ROOM);

  await launchIntoClassicPlay(transport);
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
  await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  await screen.findByLabelText(COMPOSER_LABEL);
}

describe('one stream, and only for an open room', () => {
  /**
   * ADR-0147's *never build* list: **one stream per open conversation, and never a second one for
   * the Chats list.** A tab that opened one per row would be a socket per room for a nudge nothing
   * on that screen would redraw.
   */
  it('follows the room and nothing else — the list opens none', async () => {
    stubConversations(transport, [LISTED]);
    stubConversation(transport, room());
    stubEntries(transport, ROOM);

    await launchIntoClassicPlay(transport);
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    await screen.findByLabelText(/^tomek\.p/);

    expect(channel.opened).toEqual([]);

    fireEvent.press(screen.getByLabelText(/^tomek\.p/));
    await screen.findByLabelText(COMPOSER_LABEL);

    expect(channel.opened).toEqual([ROOM]);
    expect(channel.following).toEqual([ROOM]);
  });
});

describe('the nudge', () => {
  /**
   * The whole of the client half of ADR-0147: a frame says *this room moved*, the answer is to ask
   * the ordinary read path again, and **nobody refreshes anything.**
   */
  it('brings what somebody else said, with nothing pressed', async () => {
    await openTheRoom();

    expect(screen.queryByLabelText('tomek.p: six works for me')).toBeNull();

    stubConversation(transport, room([message(1, TOMEK, 'six works for me')]));
    act(() => channel.nudge(ROOM));

    expect(await screen.findByLabelText('tomek.p: six works for me')).toBeTruthy();
  });

  /**
   * **From its own high-water mark, never from the frame's number.** The nudge carries `last_seq`
   * and the port drops it, so the re-read is the newest page — no cursor at all — and a lost frame
   * repairs itself on the next one because the client's cursor was never the frame's.
   */
  it('re-reads through the ordinary path and cites no cursor of its own', async () => {
    await openTheRoom();

    const before = transport.requests.length;
    stubConversation(transport, room([message(1, TOMEK, 'six works for me')]));
    act(() => channel.nudge(ROOM));
    await screen.findByLabelText('tomek.p: six works for me');

    const after = transport.requests.slice(before);

    expect(after.map((request) => request.path)).toContain(conversationPath(ROOM));
    expect(after.filter((request) => request.path.includes('before_seq'))).toEqual([]);
  });

  /**
   * **A nudge re-reads what the room draws, and nothing it does not**
   * ([#405](https://github.com/Raketa02/Raketa/issues/405),
   * [#406](https://github.com/Raketa02/Raketa/issues/406)). The plan card is read off `GET /plans`
   * and the game it is about off `GET /games`; a slot somebody else set arrives as a line on this
   * very frame, and a card that did not follow it would say `Where` under *tomek.p set the place*.
   * The Chats list is **not** re-read: the room draws nothing from it, and it sits mounted under
   * this screen.
   */
  it('re-reads the plan and the game beside the room, and never the Chats list', async () => {
    await openTheRoom();

    const before = transport.requests.length;
    act(() => channel.nudge(ROOM));
    await waitFor(() =>
      expect(transport.requests.slice(before).map((request) => request.path)).toContain(GAMES_PATH),
    );

    const paths = transport.requests.slice(before).map((request) => request.path);
    expect(paths).toContain(conversationPath(ROOM));
    expect(paths).toContain(PLANS_PATH);
    expect(paths).not.toContain(CONVERSATIONS_PATH);
  });

  /**
   * **The line and the card's new value appear together.** The re-read room carries *tomek.p set
   * the place*, and the re-read plan carries the place — one nudge, two lists, and the chip says
   * what the line says on the phone that pressed nothing.
   */
  it('brings the slot another member set — the line and the chip together', async () => {
    stubGames(transport, [game()], READ_AT);
    stubPlans(transport, [plan()]);
    await openTheRoom({ ...room(), game_id: GAME });
    await screen.findByLabelText('Where: Not agreed yet');

    const set: Wire['SystemLineSchema'] = {
      type: 'system_line',
      seq: 1,
      code: 'PLACE_RECORDED',
      occurred_at: READ_AT,
      actor_id: TOMEK,
      values: { value: 'Zabłocie Sport' },
    };
    stubPlans(transport, [plan({ place: 'Zabłocie Sport' })]);
    stubConversation(transport, { ...room(), game_id: GAME, entries: [set] });
    act(() => channel.nudge(ROOM));

    const sentence = systemLineSentence(
      {
        kind: 'system-line',
        seq: 1,
        code: 'PLACE_RECORDED',
        occurredAt: READ_AT,
        actorId: TOMEK,
        values: { value: 'Zabłocie Sport' },
      },
      [{ playerId: TOMEK, name: 'tomek.p' }],
      'full',
    );
    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(await screen.findByLabelText('Where: Zabłocie Sport')).toBeTruthy();
  });

  /**
   * The header's second line is *the same state as the card in Now*, folded off the plan — so the
   * third slot landing on the nudge moves it from *planning* to *game on*, on the phone that set
   * nothing.
   */
  it('moves the header’s state word when the last slot lands', async () => {
    const agreed = (over: Partial<Wire['PlanSchema']>): Wire['PlanSchema'] =>
      plan({
        place: 'Zabłocie Sport',
        day: '2026-09-13',
        agreed_point: '2026-09-12T22:00:00Z',
        ...over,
      });
    stubGames(transport, [game()], READ_AT);
    stubPlans(transport, [agreed({})]);
    await openTheRoom({ ...room(), game_id: GAME });

    const sport = sportLabel('padel');
    expect(await screen.findByText(headerSubline(sport, cardStateWord('planning')))).toBeTruthy();

    stubPlans(transport, [agreed({ hour: '18:00:00' })]);
    act(() => channel.nudge(ROOM));

    expect(await screen.findByText(headerSubline(sport, cardStateWord('game-on')))).toBeTruthy();
  });

  /**
   * **A court that fills while you are in the room draws its door and its state word**
   * ([#406](https://github.com/Raketa02/Raketa/issues/406), amended by ADR-0164 — the card was
   * there from the opening). The last acceptance's line arrives on the nudge and the re-read room
   * now carries a game — but the header's rung is folded over `GET /games`, which was last read
   * on the way in. So the nudge re-reads that list too, and the *Details* door and the state word
   * are born here rather than on the next foregrounding; the card's lock button is born on the
   * same nudge, and `planCard.test.tsx` holds that half.
   */
  it('draws the door and the state word once the court completes, over the card already there', async () => {
    stubPlans(transport, [plan()]);
    await openTheRoom();
    await screen.findByLabelText(COMPOSER_LABEL);
    expect(await screen.findByLabelText('Where: Not agreed yet')).toBeTruthy();
    expect(screen.queryByLabelText(OPEN_THE_GAME)).toBeNull();

    stubGames(transport, [game()], READ_AT);
    stubConversation(transport, {
      ...room(),
      game_id: GAME,
      entries: [
        {
          type: 'system_line',
          seq: 1,
          code: 'SEAT_ACCEPTED',
          occurred_at: READ_AT,
          actor_id: TOMEK,
          values: {},
        },
      ],
    });
    act(() => channel.nudge(ROOM));

    expect(await screen.findByLabelText(OPEN_THE_GAME)).toBeTruthy();
    expect(
      screen.getByText(headerSubline(sportLabel('padel'), cardStateWord('planning'))),
    ).toBeTruthy();
    expect(screen.getByLabelText('Where: Not agreed yet')).toBeTruthy();
  });

  /**
   * The header's state word reads the game's **standing** where the plan has no rung to say, so a
   * *we played* line arriving on the nudge moves it off the games list and not the plan's.
   */
  it('moves the header’s state word when somebody says they played', async () => {
    stubGames(transport, [game()], READ_AT);
    await openTheRoom({ ...room(), game_id: GAME });
    const sport = sportLabel('padel');
    await screen.findByText(headerSubline(sport, cardStateWord('planning')));

    stubGames(transport, [game('AWAITING_ANSWER')], READ_AT);
    stubConversation(transport, {
      ...room(),
      game_id: GAME,
      entries: [
        {
          type: 'system_line',
          seq: 1,
          code: 'GAME_PLAYED',
          occurred_at: READ_AT,
          actor_id: TOMEK,
          values: {},
        },
      ],
    });
    act(() => channel.nudge(ROOM));

    expect(await screen.findByText(headerSubline(sport, cardStateWord('confirm')))).toBeTruthy();
  });

  /**
   * A frame is news about one room, and this one is not it — so no list is re-read either. A
   * request reaches the socket only after the client's own awaits, so the check gives one the time
   * it would have needed rather than reading the log on the same tick.
   */
  it('is ignored where it names another room', async () => {
    await openTheRoom();

    const before = transport.requests.length;
    act(() => channel.nudge('99999999-0000-4000-8000-000000000099'));
    await settled();

    expect(transport.requests.length).toBe(before);
  });
});

describe('a room that ends while it is on screen', () => {
  /**
   * **The room stays as it was, closed, and says who left**
   * ([#429](https://github.com/Raketa02/Raketa/issues/429)). The last other member leaves: the
   * challenge is over in the same commit and the room with it, so the nudge's re-read is answered
   * by `conversation_not_found` — the *left* line was written into a room nobody can read. The
   * screen used to leave on that answer, and a player reading a room was on the list a moment
   * later with the room gone from under them. Now what was held is drawn as it was, the composer
   * gives way to one sentence, and the sentence names who left — folded from the members the room
   * last read (`domain/roomOver.ts`).
   */
  it('stays as it was, closes, and says who left', async () => {
    await openTheRoom(room([message(1, TOMEK, 'six works for me')]));
    await screen.findByLabelText('tomek.p: six works for me');

    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));
    act(() => channel.nudge(ROOM));

    const sentence = roomOverLine({
      kind: 'they-left',
      members: [{ playerId: TOMEK, name: 'tomek.p' }],
    });
    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(sentence).toMatch(/^tomek\.p left/);
    expect(screen).toHavePathname(`/chats/conversation/${ROOM}`);
    // The stream is still there to be read; nothing here writes any more.
    expect(screen.getByLabelText('tomek.p: six works for me')).toBeTruthy();
    expect(screen.queryByLabelText(COMPOSER_LABEL)).toBeNull();
    expect(screen.queryByRole('button', { name: SEND })).toBeNull();
    expect(screen.queryByRole('button', { name: QUICK_CHIP.where })).toBeNull();
  });

  it('is gone from the list when the player goes back', async () => {
    await openTheRoom();
    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));
    act(() => channel.nudge(ROOM));
    await screen.findByText(/left — this chat has ended\.$/);

    stubConversations(transport, []);
    fireEvent.press(screen.getByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/chats'));

    await waitFor(() => expect(screen.queryByLabelText(/^tomek\.p/)).toBeNull());
  });

  /** The reader was alone — somebody had left while a seat was deciding — and the last no came. */
  it('says nobody else is coming where the reader was alone', async () => {
    await openTheRoom(room([], [{ player_id: ME, name: 'me_' }]));
    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));
    act(() => channel.nudge(ROOM));

    expect(await screen.findByText(roomOverLine({ kind: 'nobody-else-coming' }))).toBeTruthy();
    expect(screen).toHavePathname(`/chats/conversation/${ROOM}`);
  });

  /** A room with a game is over for a reason the game's card says, and this room says only that it ended. */
  it('says only that the chat has ended where the room had its game', async () => {
    stubGames(transport, [game()], READ_AT);
    await openTheRoom({ ...room(), game_id: GAME });
    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));
    act(() => channel.nudge(ROOM));

    expect(await screen.findByText(roomOverLine({ kind: 'ended' }))).toBeTruthy();
    expect(screen.queryByText(/left — this chat has ended/)).toBeNull();
  });

  /** The not-live line has nothing to add to a room that has ended, and is not drawn over it. */
  it('draws neither the plan card nor the not-live line once it has ended', async () => {
    stubPlans(transport, [plan()]);
    await openTheRoom();
    await screen.findByLabelText('Where: Not agreed yet');

    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));
    act(() => channel.nudge(ROOM));
    await screen.findByText(/left — this chat has ended\.$/);
    act(() => channel.lose(ROOM));

    expect(screen.queryByLabelText('Where: Not agreed yet')).toBeNull();
    expect(screen.queryByText(LIVE_NOTE['not-live'])).toBeNull();
  });
});

describe('not live', () => {
  /** **Never on a cold open.** Drawn after a failure, or every arrival on every room flashes it. */
  it('says nothing while the channel is still connecting', async () => {
    await openTheRoom();

    expect(screen.queryByText(LIVE_NOTE['not-live'])).toBeNull();
  });

  it('says nothing on an open channel', async () => {
    await openTheRoom();
    act(() => channel.connect(ROOM));

    expect(screen.queryByText(LIVE_NOTE['not-live'])).toBeNull();
  });

  it('says one line once a connect attempt has failed', async () => {
    await openTheRoom();
    act(() => channel.connect(ROOM));
    act(() => channel.lose(ROOM));

    expect(await screen.findByText(LIVE_NOTE['not-live'])).toBeTruthy();
  });

  /**
   * **A room opened with no signal says so, without ever having been live** — the one place *never
   * on a cold open* is deliberately not honoured, because *a phone with no signal produces the same
   * thing as a severed stream* is the other half of the same ticket and would otherwise be false.
   * The port reports `lost` without attempting: `onlineManager` has already settled it, and that is
   * not the handshake flash the cold-open rule is about (`domain/liveState.ts` carries the argument).
   */
  it('says it on a room opened with nothing to connect over', async () => {
    await openTheRoom();
    act(() => channel.lose(ROOM));

    expect(await screen.findByText(LIVE_NOTE['not-live'])).toBeTruthy();
  });

  /**
   * **Not a disabled composer.** Sends are ordinary authenticated `POST`s and the channel is
   * unidirectional by construction, so writing is unaffected — and closing the control would state
   * something false about the half that still works.
   */
  it('leaves the composer working, and the send goes', async () => {
    await openTheRoom();
    act(() => channel.lose(ROOM));
    await screen.findByText(LIVE_NOTE['not-live']);

    transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
      json<Wire['MessageSchema']>(message(1, ME, 'on my way')),
    );

    const box = screen.getByLabelText(COMPOSER_LABEL);
    expect(box.props.editable).not.toBe(false);

    fireEvent.changeText(box, 'on my way');
    fireEvent.press(screen.getByRole('button', { name: SEND }));

    await waitFor(() =>
      expect(transport.requestsTo('POST', `${conversationPath(ROOM)}/messages`)).toHaveLength(1),
    );
  });

  /**
   * A stream closed on the way to the background was closed **deliberately** — ADR-0147 §9 — so it
   * is not news about the room, and the line is *only in the foreground*.
   */
  it('says nothing about a channel closed for the background', async () => {
    await openTheRoom();
    act(() => channel.lose(ROOM));
    await screen.findByText(LIVE_NOTE['not-live']);

    act(() => channel.background(ROOM));

    await waitFor(() => expect(screen.queryByText(LIVE_NOTE['not-live'])).toBeNull());
  });

  /** It goes away by itself, which is the whole of *routinely and briefly*. */
  it('goes when the channel comes back', async () => {
    await openTheRoom();
    act(() => channel.lose(ROOM));
    await screen.findByText(LIVE_NOTE['not-live']);

    act(() => channel.connect(ROOM));

    await waitFor(() => expect(screen.queryByText(LIVE_NOTE['not-live'])).toBeNull());
  });
});

describe('held', () => {
  /**
   * The one way a hold reaches this client: `account_held`, a `403` on the write. No read serves
   * it, which is why the pre-emptive half of §3.6 is bought with one tap in this build — recorded
   * in `domain/liveState.ts` rather than pretended away.
   */
  async function refuseTheSend() {
    await openTheRoom();

    transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
      errorResponse(403, 'account_held'),
    );

    fireEvent.changeText(screen.getByLabelText(COMPOSER_LABEL), 'anyone there?');
    fireEvent.press(screen.getByRole('button', { name: SEND }));

    await screen.findByText(LIVE_NOTE.held);
  }

  it('names the fact once, and never twice in two registers', async () => {
    await refuseTheSend();

    expect(screen.getAllByText(LIVE_NOTE.held)).toHaveLength(1);
    // One element, and it is the amber note — the coral refusal is the other register, and a
    // hold is not a thing about this message.
    const alerts = screen.getAllByRole('alert');
    expect(alerts).toHaveLength(1);
    expect(within(alerts[0]!).getByText(LIVE_NOTE.held)).toBeTruthy();
  });

  /**
   * **A listener who pressed Send has to hear why nothing happened.** The pre-emptive half of
   * §3.6 is bought with one tap in this build, so the note that lands on that tap is announced —
   * and it is the one that is, because *not live* comes and goes on its own every quarter of an
   * hour and would interrupt four times an hour to say nothing anybody must act on.
   */
  it('announces the hold, and never announces not live', async () => {
    await openTheRoom();
    act(() => channel.lose(ROOM));
    await screen.findByText(LIVE_NOTE['not-live']);

    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('greys the composer and closes the send', async () => {
    await refuseTheSend();

    expect(screen.getByLabelText(COMPOSER_LABEL).props.editable).toBe(false);
    expect(screen.getByRole('button', { name: SEND }).props.accessibilityState.disabled).toBe(true);
  });

  /** One note for every refused control, not one per chip — and the chips stay, greyed. */
  it('greys every quick chip and keeps them all', async () => {
    await refuseTheSend();

    for (const chip of ['where', 'day', 'hour'] as const) {
      const control = screen.getByRole('button', { name: QUICK_CHIP[chip] });
      expect(control.props.accessibilityState.disabled).toBe(true);
    }

    expect(screen.getAllByText(LIVE_NOTE.held)).toHaveLength(1);
  });

  /** **Reading is never blocked, and a hold never removes the room** (ADR-0148 §9). */
  it('leaves the room and its stream exactly where they were', async () => {
    stubConversations(transport, [LISTED]);
    stubConversation(transport, room([message(1, TOMEK, 'six works for me')]));
    stubEntries(transport, ROOM);

    await launchIntoClassicPlay(transport);
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
    await screen.findByLabelText(COMPOSER_LABEL);

    transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
      errorResponse(403, 'account_held'),
    );
    fireEvent.changeText(screen.getByLabelText(COMPOSER_LABEL), 'anyone there?');
    fireEvent.press(screen.getByRole('button', { name: SEND }));
    await screen.findByText(LIVE_NOTE.held);

    expect(
      screen.getByRole('header', {
        name: conversationHeaderLabel(['tomek.p'], sportLabel('padel'), undefined),
      }),
    ).toBeTruthy();
    expect(screen.getByLabelText('tomek.p: six works for me')).toBeTruthy();
  });

  /**
   * A hold and a dead channel are both true here, and §3.6 asks for **one** note. The fold picks
   * the one that closes a control, and held's own sentence already promises that reading works.
   */
  it('is the one thing said, even on a channel that has also failed', async () => {
    await refuseTheSend();
    act(() => channel.lose(ROOM));

    await waitFor(() => expect(screen.queryByText(LIVE_NOTE['not-live'])).toBeNull());
    expect(screen.getByText(LIVE_NOTE.held)).toBeTruthy();
  });

  /**
   * **A greyed text field is acceptable only because the note is above it and arrives first.**
   * Rendered under the strip it would be the dead end #324 refused — and for a listener, who meets
   * the screen in one order and no other, *above* is the only thing that means *first*.
   */
  it('sits above every control it explains, in render order', async () => {
    await refuseTheSend();

    const inOrder = screen.root.findAll(() => true);
    const at = (node: (typeof inOrder)[number]) => inOrder.indexOf(node);

    const note = at(screen.getByText(LIVE_NOTE.held));

    expect(note).toBeLessThan(at(screen.getByRole('button', { name: QUICK_CHIP.where })));
    expect(note).toBeLessThan(at(screen.getByLabelText(COMPOSER_LABEL)));
    expect(note).toBeLessThan(at(screen.getByRole('button', { name: SEND })));
  });

  /**
   * **Every write on the screen is a producer, not only the send.** A hold met on a plan write is
   * the same fact about the account, and it reaches this fold off `features/plans`' mutation cache
   * — so the one note is drawn, in the same words, with the composer and every chip greyed under
   * it, and no coral sentence anywhere.
   */
  it('is told by a plan write, not only by the send', async () => {
    const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
    stubGames(
      transport,
      [
        {
          game_id: GAME,
          challenge_id: CHALLENGE,
          sport: 'PADEL',
          kind: 'COUNTED',
          standing: 'AWAITING_ENTRY',
          planned_at: READ_AT,
          entry_closes_at: '2026-09-20T09:00:00Z',
          seats: [
            { side: 'A', player_id: ME, name: 'me_' },
            { side: 'B', player_id: TOMEK, name: 'tomek.p' },
          ],
          proposals: [],
          no_shows: [],
        },
      ],
      READ_AT,
    );
    stubPlans(transport, [plan()]);
    stubConversations(transport, [{ ...LISTED, game_id: GAME }]);
    stubConversation(transport, { ...room(), game_id: GAME });
    stubEntries(transport, ROOM);
    transport.on('PUT', planSlotPath(CHALLENGE, 'day'), () => errorResponse(403, 'account_held'));

    await launchIntoClassicPlay(transport);
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
    await screen.findByLabelText(COMPOSER_LABEL);

    // The day chip and its row are the plan's own controls, named by that feature's deck; what is
    // asserted here is the room's half — the note, and what it greys.
    fireEvent.press(await screen.findByRole('button', { name: /^Day:/ }));
    fireEvent.press(await screen.findByRole('button', { name: 'Sunday' }));

    await screen.findByText(LIVE_NOTE.held);
    expect(screen.getAllByText(LIVE_NOTE.held)).toHaveLength(1);
    expect(screen.getAllByRole('alert')).toHaveLength(1);
    expect(screen.getByLabelText(COMPOSER_LABEL).props.editable).toBe(false);
    expect(screen.getByRole('button', { name: SEND }).props.accessibilityState.disabled).toBe(true);
  });
});

describe('somebody is typing', () => {
  const OLA = 'cccccccc-0000-4000-8000-000000000003';
  const THREE: Wire['ConversationMemberSchema'][] = [...MEMBERS, { player_id: OLA, name: 'ola.k' }];
  const named = (ids: readonly string[], members = MEMBERS) =>
    typingLine(
      ids,
      members.map((one) => ({
        playerId: one.player_id,
        ...(one.name === null ? {} : { name: one.name }),
      })),
    ) ?? '';
  const typingPath = `${conversationPath(ROOM)}/typing`;

  // The OS switch is set in one case below, and **set back rather than restored**: React Native's
  // `AccessibilityInfo` is already a Jest mock, so a spy over it cannot be restored to anything —
  // `overlay.test.tsx` sets it both ways for the same reason.
  afterEach(() => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
    jest.restoreAllMocks();
  });

  /** What was said to a screen reader, and how. Cleared per case, since RN's stub is one mock. */
  let spoken: jest.SpyInstance<
    void,
    Parameters<typeof AccessibilityInfo.announceForAccessibilityWithOptions>
  >;

  beforeEach(() => {
    spoken = jest
      .spyOn(AccessibilityInfo, 'announceForAccessibilityWithOptions')
      .mockImplementation(() => undefined);
    spoken.mockClear();
  });

  /** The room, live, so the roster it is handed is one it may draw. */
  async function openLive(answer: Wire['ConversationResponse'] = room()) {
    await openTheRoom(answer);
    // The root's one read of the OS motion switch resolves off the render that mounted it.
    await act(async () => {});
    act(() => channel.connect(ROOM));
  }

  /**
   * The bubble is one element, named by §22.5's sentence and polite: it is a courtesy about
   * somebody else's fingers, and interrupting a listener mid-message to deliver it would be the
   * loudest possible way to say the least important thing on the screen. **Polite is two
   * mechanisms**: on this platform (iOS under jest-expo) the queued announcement, on Android the
   * attribute — both are asserted, because each is the whole of it on one platform.
   */
  it('appears on a typing frame, as one polite element named for who is typing', async () => {
    await openLive();

    act(() => channel.typing(ROOM, [TOMEK]));

    const bubble = await screen.findByLabelText(named([TOMEK]));
    expect(named([TOMEK])).toBe('tomek.p is typing…');
    expect(bubble.props.accessibilityLiveRegion).toBe('polite');
    expect(spoken).toHaveBeenCalledTimes(1);
    expect(spoken).toHaveBeenCalledWith(named([TOMEK]), { queue: true });
  });

  /** Said on change and never on a heartbeat, and nothing is said when it goes (§24.6). */
  it('is announced once per change, and its going is not announced', async () => {
    await openLive();

    act(() => channel.typing(ROOM, [TOMEK]));
    await screen.findByLabelText(named([TOMEK]));
    act(() => channel.typing(ROOM, []));
    await waitFor(() => expect(screen.queryByLabelText(named([TOMEK]))).toBeNull());

    expect(spoken).toHaveBeenCalledTimes(1);
  });

  /** An empty list is the clear, and it is the only clear the server sends. */
  it('clears on the empty frame', async () => {
    await openLive();

    act(() => channel.typing(ROOM, [TOMEK]));
    await screen.findByLabelText(named([TOMEK]));

    act(() => channel.typing(ROOM, []));

    await waitFor(() => expect(screen.queryByLabelText(named([TOMEK]))).toBeNull());
  });

  /**
   * **Clears on its own when no further frame can arrive.** The server sends a frame only when the
   * answer changes, so a clock would clear the indicator on somebody still typing; what the client
   * keys its own net on is the channel — a roster is only as live as the stream that carried it,
   * and a severed stream, a backgrounded app and a phone with no signal all drop it at once.
   */
  it('clears on its own when the channel is lost, with no further frame', async () => {
    await openLive();

    act(() => channel.typing(ROOM, [TOMEK]));
    await screen.findByLabelText(named([TOMEK]));

    act(() => channel.lose(ROOM));

    await waitFor(() => expect(screen.queryByLabelText(named([TOMEK]))).toBeNull());

    // And it does not come back on reconnect by itself: the server re-announces anybody still
    // typing on its first check, so a roster this client remembered would be a guess.
    act(() => channel.connect(ROOM));
    expect(screen.queryByLabelText(named([TOMEK]))).toBeNull();
  });

  it('clears when the app goes to the background', async () => {
    await openLive();

    act(() => channel.typing(ROOM, [TOMEK]));
    await screen.findByLabelText(named([TOMEK]));

    act(() => channel.background(ROOM));

    await waitFor(() => expect(screen.queryByLabelText(named([TOMEK]))).toBeNull());
  });

  /** The server filters the reader out; the client filters again, because the bug is visible. */
  it('draws nothing for the reader’s own id', async () => {
    await openLive();

    act(() => channel.typing(ROOM, [ME]));
    act(() => channel.typing(ROOM, [ME, TOMEK]));

    await screen.findByLabelText(named([TOMEK]));
    expect(screen.queryByLabelText(/me_ .*typing/)).toBeNull();
  });

  /** One indicator whichever number are typing, and the sentence counts from three. */
  it('draws one indicator for a group, naming two and counting three', async () => {
    const ZOFIA = 'dddddddd-0000-4000-8000-000000000004';
    const FOUR: Wire['ConversationMemberSchema'][] = [
      ...THREE,
      { player_id: ZOFIA, name: 'zofia.b' },
    ];
    await openLive(room([], FOUR));

    act(() => channel.typing(ROOM, [TOMEK, OLA]));
    await screen.findByLabelText(named([TOMEK, OLA], FOUR));
    expect(named([TOMEK, OLA], FOUR)).toBe('tomek.p and ola.k are typing…');

    act(() => channel.typing(ROOM, [TOMEK, OLA, ZOFIA]));
    await screen.findByLabelText(named([TOMEK, OLA, ZOFIA], FOUR));
    expect(named([TOMEK, OLA, ZOFIA], FOUR)).toBe('3 people are typing…');
    expect(screen.getAllByLabelText(/typing…$/)).toHaveLength(1);
  });

  /**
   * **Typing is not query cache state.** A typing frame invalidates nothing and advances no cursor:
   * the room is not re-read and no page is asked for, however many frames arrive.
   */
  it('never re-reads the room and never pages on a typing frame', async () => {
    await openLive();
    const reads = () => transport.requestsTo('GET', conversationPath(ROOM)).length;
    const pages = () => transport.requestsTo('GET', `${conversationPath(ROOM)}/entries`).length;
    const before = { reads: reads(), pages: pages() };

    act(() => channel.typing(ROOM, [TOMEK]));
    await screen.findByLabelText(named([TOMEK]));
    act(() => channel.typing(ROOM, []));
    act(() => channel.typing(ROOM, [TOMEK]));

    await screen.findByLabelText(named([TOMEK]));
    expect(reads()).toBe(before.reads);
    expect(pages()).toBe(before.pages);

    // A nudge still does what a nudge does, so the two are told apart and not merely both dropped.
    act(() => channel.nudge(ROOM));
    await waitFor(() => expect(reads()).toBe(before.reads + 1));
  });

  /**
   * **Reduce motion draws the dots still and keeps the sentence.** The one loop this screen runs
   * is not started, and the element is named exactly as it is with motion on.
   */
  it('draws static dots under reduced motion, and keeps the accessible name', async () => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
    const loop = jest.spyOn(Animated, 'loop');

    await openLive();
    act(() => channel.typing(ROOM, [TOMEK]));

    expect(await screen.findByLabelText(named([TOMEK]))).toBeTruthy();
    expect(loop).not.toHaveBeenCalled();
  });

  /**
   * The loop is the one thing here a walk cannot observe, so it is asked directly: started with
   * the bubble, and **stopped when the indicator clears** — a loop left running would run for the
   * life of the screen.
   */
  it('animates the dots when motion is not reduced, and stops when the indicator clears', async () => {
    const loop = jest.spyOn(Animated, 'loop');

    await openLive();
    act(() => channel.typing(ROOM, [TOMEK]));
    await screen.findByLabelText(named([TOMEK]));

    expect(loop).toHaveBeenCalledTimes(1);
    const running = loop.mock.results[0]?.value as { stop: () => void } | undefined;
    const stop = jest.spyOn(running ?? { stop: () => undefined }, 'stop');

    act(() => channel.typing(ROOM, []));
    await waitFor(() => expect(screen.queryByLabelText(named([TOMEK]))).toBeNull());

    expect(stop).toHaveBeenCalled();
  });

  describe('the heartbeat', () => {
    beforeEach(() => {
      transport.on('POST', typingPath, () => noContent());
    });

    /**
     * Posted on a keystroke and **never per keystroke**: a burst of them is one beat. The cadence
     * itself — the second beat three seconds on — is `beatIsDue`'s and is pinned in
     * `domain/typing.test.ts` against an explicit clock, which is the seam that number lives at.
     */
    it('is posted on typing, once for a burst of keystrokes, with no body', async () => {
      await openLive();

      const box = screen.getByLabelText(COMPOSER_LABEL);
      fireEvent.changeText(box, 's');
      fireEvent.changeText(box, 'si');
      fireEvent.changeText(box, 'six');

      await waitFor(() => expect(transport.requestsTo('POST', typingPath)).toHaveLength(1));
      expect(transport.requestsTo('POST', typingPath)[0]?.body).toBeUndefined();

      fireEvent.changeText(box, 'six?');
      await act(async () => {});
      expect(transport.requestsTo('POST', typingPath)).toHaveLength(1);
    });

    /** A hold stops you writing anywhere another player sees it, and this is seen by others. */
    it('is silent when the account is held', async () => {
      await openLive();
      transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
        errorResponse(403, 'account_held'),
      );
      fireEvent.changeText(screen.getByLabelText(COMPOSER_LABEL), 'anyone there?');
      fireEvent.press(screen.getByRole('button', { name: SEND }));
      await screen.findByText(LIVE_NOTE.held);

      // The box is greyed, so a keystroke cannot reach it on a device; what a test can still
      // drive through it is exactly what must not beat.
      const beforeHold = transport.requestsTo('POST', typingPath).length;
      fireEvent.changeText(screen.getByLabelText(COMPOSER_LABEL), 'still here?');

      await act(async () => {});
      expect(transport.requestsTo('POST', typingPath)).toHaveLength(beforeHold);
    });

    /** Nobody needs to be told their typing indicator did not reach anybody. */
    it('says nothing when it fails', async () => {
      transport.on('POST', typingPath, () => errorResponse(500, 'boom'));
      await openLive();

      fireEvent.changeText(screen.getByLabelText(COMPOSER_LABEL), 'hi');

      await waitFor(() => expect(transport.requestsTo('POST', typingPath)).toHaveLength(1));
      await act(async () => {});
      expect(screen.queryByRole('alert')).toBeNull();
      expect(screen.queryByText(/went wrong|try again/i)).toBeNull();
    });
  });
});
