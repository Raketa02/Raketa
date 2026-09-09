/**
 * **The room, walked the way a member walks it**: the real route tree, the real shell, the real
 * row it is opened from, and only `fetch` faked.
 *
 * Most of [#364](https://github.com/Raketa02/Raketa/issues/364)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the header names the people and the sport
 * and nothing else, *Details* is drawn only where there is a game, the stream is two components,
 * the author's handle is drawn only in a room of more than two, there is no timestamp and there
 * is a day separator, the stream pages backward by cursor, a send is optimistic and reconciled on
 * `client_message_id`, and every entry is one element a listener can move through.
 *
 * It asserts against the **copy deck** rather than against strings wherever a sentence has one,
 * because the wording is the deck's to change and the rules are not.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  conversationPath,
  launchSignedIn,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { mapErrorResponse } from '@/shared/errors';

import { conversationErrorMessage } from './conversationErrorMessage';
import { systemLineSentence } from './conversationPresentation';
import { QUICK_CHIP } from '@/features/plans/types';

import { DETAILS, SEND } from './conversationPresentation';
import { OPEN_THE_GAME } from './conversationAccessibility';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'cccccccc-0000-4000-8000-000000000003';

const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';

/** 09:00 UTC on Saturday the 12th, which is Saturday in Warsaw whatever the phone thinks. */
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

function member(playerId: string, nickname: string): Wire['ConversationMemberSchema'] {
  return { player_id: playerId, nickname };
}

const PAIR = [member(ME, 'me_'), member(TOMEK, 'tomek.p')];
const THREE = [...PAIR, member(OLA, 'ola.k')];

function message(
  seq: number,
  authorId: string,
  text: string,
  sentAt = READ_AT,
): Wire['MessageSchema'] {
  return {
    type: 'message',
    seq,
    author_id: authorId,
    sent_at: sentAt,
    text,
    client_message_id: `client-${seq}`,
  };
}

function line(seq: number, code: string, occurredAt = READ_AT): Wire['SystemLineSchema'] {
  return { type: 'system_line', seq, code, occurred_at: occurredAt, actor_id: TOMEK, values: {} };
}

function room(over: Partial<Wire['ConversationResponse']> = {}): Wire['ConversationResponse'] {
  return {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: null,
    sport: 'PADEL',
    members: PAIR,
    entries: [],
    ...over,
  };
}

function listed(over: Partial<Wire['ConversationRowSchema']> = {}): Wire['ConversationRowSchema'] {
  return {
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: null,
    sport: 'PADEL',
    members: PAIR,
    last_entry: null,
    ...over,
  };
}

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

/** Land in the app, open Chats, tap the one row — the walk every assertion here starts with. */
async function openTheRoom(answer: Wire['ConversationResponse'] = room()) {
  stubConversations(transport, [listed({ members: answer.members, game_id: answer.game_id })]);
  stubConversation(transport, answer);
  stubEntries(transport, ROOM);

  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));

  fireEvent.press(await screen.findByLabelText(/^tomek\.p/));
  await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
}

describe('the header', () => {
  it('names the people whole and the sport, and nothing about a standing', async () => {
    await openTheRoom();

    expect(await screen.findByRole('header', { name: 'tomek.p' })).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
  });

  /**
   * The game id is nullable, so a room whose line-up is still filling has no game and no plan —
   * nothing for this door to open, and a drawn dead control is the disabled control #324 refused.
   */
  it('draws no Details where there is no game', async () => {
    await openTheRoom();

    expect(screen.queryByLabelText(OPEN_THE_GAME)).toBeNull();
  });

  it('draws Details where there is one, named for what is behind it', async () => {
    await openTheRoom(room({ game_id: GAME }));

    const details = await screen.findByLabelText(OPEN_THE_GAME);

    expect(details).toBeTruthy();
    expect(screen.getByText(DETAILS)).toBeTruthy();
  });

  it('opens the game under the room’s own address, so the Chats column stays lit', async () => {
    await openTheRoom(room({ game_id: GAME }));

    fireEvent.press(await screen.findByLabelText(OPEN_THE_GAME));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}/details`));
  });
});

describe('the stream', () => {
  /**
   * Two shapes, two components. A bubble is named for its author and a system line is named by
   * the sentence its code renders — which is how a listener tells them apart at all.
   */
  it('draws a bubble and a system line as different things', async () => {
    const said = line(1, 'SEAT_ACCEPTED');
    await openTheRoom(room({ entries: [said, message(2, TOMEK, 'six works for me')] }));

    const sentence = systemLineSentence(
      {
        kind: 'system-line',
        seq: 1,
        code: 'SEAT_ACCEPTED',
        occurredAt: READ_AT,
        actorId: TOMEK,
        values: {},
      },
      [{ playerId: TOMEK, nickname: 'tomek.p' }],
      'full',
    );

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(screen.getByLabelText('tomek.p: six works for me')).toBeTruthy();
  });

  /** §24.4: the author is always spoken, even where the bubble does not draw one. */
  it('names the author of every bubble, and the reader’s own as You', async () => {
    await openTheRoom(room({ entries: [message(1, ME, '18:00 works')] }));

    expect(await screen.findByLabelText('You: 18:00 works')).toBeTruthy();
  });

  /** In a pair there is nothing to disambiguate, and ADR-0107 forbids a familiar form anywhere. */
  it('draws no handle on a bubble in a room of two', async () => {
    await openTheRoom(room({ entries: [message(1, TOMEK, 'six works for me')] }));

    const bubble = await screen.findByLabelText('tomek.p: six works for me');

    expect(within(bubble).queryByText('tomek.p')).toBeNull();
  });

  it('draws the whole handle on a bubble in a room of more than two', async () => {
    await openTheRoom(room({ members: THREE, entries: [message(1, TOMEK, 'six works for me')] }));

    const bubble = await screen.findByLabelText('tomek.p: six works for me');

    expect(within(bubble).getByText('tomek.p')).toBeTruthy();
  });

  /**
   * A room lives days rather than months, so the one time-shaped fact worth drawing is which day
   * — and the day is the platform's, so one room reads the same on every phone in it.
   */
  it('separates the days and prints no clock beside a message', async () => {
    await openTheRoom(
      room({
        entries: [
          message(1, TOMEK, 'friday evening', '2026-09-11T18:00:00Z'),
          message(2, ME, 'saturday morning', '2026-09-12T07:00:00Z'),
        ],
      }),
    );

    expect(await screen.findByRole('header', { name: 'Friday' })).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Saturday' })).toBeTruthy();
    expect(screen.queryByText(/\d\d:\d\d/)).toBeNull();
  });
});

describe('paging backward', () => {
  /**
   * *What is before the oldest thing I hold* is the whole of the question — no offset, and no
   * `has_more`, because a gapless sequence makes `seq` 1 the beginning.
   */
  it('opens on the newest page and asks for nothing else until it is asked to', async () => {
    await openTheRoom(room({ entries: [message(4, TOMEK, 'four')] }));

    await screen.findByLabelText('tomek.p: four');
    expect(transport.requests.filter((one) => one.path.includes('/entries'))).toHaveLength(0);
  });

  it('asks for what is before the oldest entry it holds', async () => {
    await openTheRoom(room({ entries: [message(4, TOMEK, 'four'), message(5, ME, 'five')] }));
    await screen.findByLabelText('tomek.p: four');
    stubEntries(transport, ROOM, [message(3, TOMEK, 'three')]);

    // Reaching the end of an inverted list is reaching the top of the room, which is the one
    // gesture that asks for an older page. Driven through the list's own callback: a synthetic
    // scroll needs a layout the test renderer never performs.
    fireEvent(screen.getByTestId('conversation-stream'), 'endReached');

    await waitFor(() => expect(screen.getByLabelText('tomek.p: three')).toBeTruthy());

    const asked = transport.requests.filter((one) => one.path.includes('/entries'));
    expect(asked[0]?.path).toContain('before_seq=4');
    expect(asked[0]?.path).not.toContain('offset');
  });
});

describe('the composer', () => {
  /** The send is optimistic: the bubble is there before the round trip, not after it. */
  it('draws the message before the server has answered', async () => {
    await openTheRoom();

    let answer: (() => void) | undefined;
    transport.on('POST', `${conversationPath(ROOM)}/messages`, (request) => {
      const body = request.body as Wire['SendMessageRequest'];
      return new Promise<Response>((resolve) => {
        answer = () =>
          resolve(
            json<Wire['MessageSchema']>({
              type: 'message',
              seq: 1,
              author_id: ME,
              sent_at: READ_AT,
              text: body.text,
              client_message_id: body.client_message_id,
            }),
          );
      });
    });

    fireEvent.changeText(await screen.findByLabelText('Message'), 'on my way');
    fireEvent.press(screen.getByRole('button', { name: SEND }));

    expect(await screen.findByLabelText('You: on my way')).toBeTruthy();

    answer?.();

    // Reconciled on `client_message_id`: the real message replaces the optimistic one rather
    // than joining it, so a resumed send can never become two bubbles.
    await waitFor(() => expect(screen.getAllByLabelText('You: on my way')).toHaveLength(1));
  });

  it('sends the id it drew the bubble under, in the body', async () => {
    await openTheRoom();

    transport.on('POST', `${conversationPath(ROOM)}/messages`, (request) => {
      const body = request.body as Wire['SendMessageRequest'];
      return json<Wire['MessageSchema']>({
        type: 'message',
        seq: 1,
        author_id: ME,
        sent_at: READ_AT,
        text: body.text,
        client_message_id: body.client_message_id,
      });
    });

    fireEvent.changeText(await screen.findByLabelText('Message'), 'on my way');
    fireEvent.press(screen.getByRole('button', { name: SEND }));

    await waitFor(() =>
      expect(transport.requestsTo('POST', `${conversationPath(ROOM)}/messages`)).toHaveLength(1),
    );

    const sent = transport.requestsTo('POST', `${conversationPath(ROOM)}/messages`)[0]
      ?.body as Wire['SendMessageRequest'];

    expect(sent.text).toBe('on my way');
    expect(sent.client_message_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
  });
});

describe('a refused send', () => {
  /**
   * The words go back in the box, because the retry is the control that failed — and the sentence
   * is this feature's, since the length cap is deliberately not on the wire and so cannot be
   * pre-empted by a `maxLength`.
   */
  it('puts the words back and says what was wrong with them', async () => {
    await openTheRoom();

    transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
      errorResponse(400, 'message_is_too_long'),
    );

    const box = await screen.findByLabelText('Message');
    fireEvent.changeText(box, 'a very long message');
    fireEvent.press(screen.getByRole('button', { name: SEND }));

    // Built the way the app builds one — through the error mapper — so the sentence under test
    // is the one a real 400 on this route produces.
    const refused = mapErrorResponse(400, {
      code: 'message_is_too_long',
      message: 'too long',
      trace_id: 't',
      details: null,
    });

    expect(await screen.findByText(conversationErrorMessage(refused))).toBeTruthy();
    expect(screen.getByLabelText('Message').props.value).toBe('a very long message');
    expect(screen.queryByLabelText('You: a very long message')).toBeNull();
  });

  /**
   * §3.7: **a client holding a cursor into a destroyed conversation leaves the screen.** One code
   * for three cases, and there is no retry that changes any of them.
   */
  it('leaves the screen when the room has gone', async () => {
    await openTheRoom();
    await screen.findByLabelText('Message');

    transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
      errorResponse(404, 'conversation_not_found'),
    );

    fireEvent.changeText(screen.getByLabelText('Message'), 'anyone there?');
    fireEvent.press(screen.getByRole('button', { name: SEND }));

    await waitFor(() => expect(screen).toHavePathname('/chats'));
  });

  it('leaves the screen when the read finds the room has gone', async () => {
    stubConversations(transport, [listed()]);
    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));
    stubEntries(transport, ROOM);

    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));

    fireEvent.press(await screen.findByLabelText(/^tomek\.p/));

    // It gets as far as the route and comes straight back, rather than sitting on a sentence
    // about a room that is not there.
    await waitFor(() => expect(screen).toHavePathname('/chats'));
  });
});

describe('the quick chips', () => {
  /**
   * One per unfilled slot in slot order, and no *On my way*: this build reads no plan, and a room
   * with nothing agreed is the state `GET /plans` spells by having no row at all.
   */
  it('asks the three questions and names nothing', async () => {
    await openTheRoom();

    expect(await screen.findByRole('button', { name: QUICK_CHIP.where })).toBeTruthy();
    expect(screen.getByRole('button', { name: QUICK_CHIP.day })).toBeTruthy();
    expect(screen.getByRole('button', { name: QUICK_CHIP.hour })).toBeTruthy();
    expect(screen.queryByRole('button', { name: QUICK_CHIP['on-my-way'] })).toBeNull();
  });

  /** A chip posts words and changes nothing — ADR-0144, and the whole of what a chip does. */
  it('posts its own words as a message', async () => {
    await openTheRoom();

    transport.on('POST', `${conversationPath(ROOM)}/messages`, (request) => {
      const body = request.body as Wire['SendMessageRequest'];
      return json<Wire['MessageSchema']>({
        type: 'message',
        seq: 1,
        author_id: ME,
        sent_at: READ_AT,
        text: body.text,
        client_message_id: body.client_message_id,
      });
    });

    fireEvent.press(await screen.findByRole('button', { name: QUICK_CHIP.hour }));

    expect(await screen.findByLabelText(`You: ${QUICK_CHIP.hour}`)).toBeTruthy();
  });
});
