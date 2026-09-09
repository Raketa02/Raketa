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

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  conversationPath,
  launchSignedIn,
  resetLiveStream,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
  stubLiveStream,
} from '@/test-support/onboardingRouter';
import { fakeLiveStream, type FakeLiveStream } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { LIVE_NOTE, QUICK_CHIP, SEND } from './conversationPresentation';

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
  { player_id: ME, nickname: 'me_' },
  { player_id: TOMEK, nickname: 'tomek.p' },
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

function room(entries: readonly Wire['MessageSchema'][] = []): Wire['ConversationResponse'] {
  return {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: null,
    sport: 'PADEL',
    members: MEMBERS,
    entries: [...entries],
  };
}

const LISTED: Wire['ConversationRowSchema'] = {
  conversation_id: ROOM,
  challenge_id: CHALLENGE,
  game_id: null,
  sport: 'PADEL',
  members: MEMBERS,
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

/** Land in the app, open Chats, tap the one row. The walk every case here starts with. */
async function openTheRoom(answer: Wire['ConversationResponse'] = room()) {
  stubConversations(transport, [LISTED]);
  stubConversation(transport, answer);
  stubEntries(transport, ROOM);

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
  await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  await screen.findByLabelText('Message');
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

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    await screen.findByLabelText(/^tomek\.p/);

    expect(channel.opened).toEqual([]);

    fireEvent.press(screen.getByLabelText(/^tomek\.p/));
    await screen.findByLabelText('Message');

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

  /** A frame is news about one room, and this one is not it. */
  it('is ignored where it names another room', async () => {
    await openTheRoom();

    const before = transport.requests.length;
    act(() => channel.nudge('99999999-0000-4000-8000-000000000099'));

    expect(transport.requests.length).toBe(before);
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

    const box = screen.getByLabelText('Message');
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

    fireEvent.changeText(screen.getByLabelText('Message'), 'anyone there?');
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

    expect(screen.getByLabelText('Message').props.editable).toBe(false);
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

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
    await screen.findByLabelText('Message');

    transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
      errorResponse(403, 'account_held'),
    );
    fireEvent.changeText(screen.getByLabelText('Message'), 'anyone there?');
    fireEvent.press(screen.getByRole('button', { name: SEND }));
    await screen.findByText(LIVE_NOTE.held);

    expect(screen.getByRole('header', { name: 'tomek.p' })).toBeTruthy();
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
    expect(note).toBeLessThan(at(screen.getByLabelText('Message')));
    expect(note).toBeLessThan(at(screen.getByRole('button', { name: SEND })));
  });
});
