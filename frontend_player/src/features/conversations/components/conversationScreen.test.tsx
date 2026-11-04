/**
 * **A booked game's room, walked the way a member walks it**: the real route tree, the real shell,
 * the booked game's details it is opened from, and only `fetch` faked.
 *
 * Most of [#364](https://github.com/Raketa02/Raketa/issues/364)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the header names the people, the sport and
 * the booking's word, the stream is two components, the author's handle is drawn only in a room
 * of more than two, there is no timestamp and there is a day separator, the stream pages backward
 * by cursor, a send is optimistic and reconciled on `client_message_id`, and every entry is one
 * element a listener can move through.
 *
 * It walked the old loop's room from the Chats tab until that loop was removed
 * ([#576](https://github.com/Raketa02/Raketa/issues/576)); the room is a booked game's now, reached
 * from its details, with no plan card, no quick chips and no *Details* door — and this file says
 * so.
 *
 * It asserts against the **copy deck** rather than against strings wherever a sentence has one,
 * because the wording is the deck's to change and the rules are not.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { KeyboardAvoidingView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { BOOKING, bookingDetails, homeGame, stubBooking, stubHomeGames } from '@/test-support/home';
import {
  conversationPath,
  GATE_USER,
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
import {
  SIDE_FORMED_LINE,
  headerSubline,
  headerTitle,
  systemLineSentence,
} from './conversationPresentation';
import { sportLabel } from '@/features/onboarding/types';

import {
  COMPOSER_LABEL,
  COMPOSER_PLACEHOLDER,
  CONVERSATION_SCREEN_TITLE,
  OPEN_THE_CHAT,
  ROOM_OVER_LINE,
  SEND,
  WAITING_FOR_OTHERS,
} from './conversationPresentation';
import { conversationHeaderLabel } from './conversationAccessibility';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'cccccccc-0000-4000-8000-000000000003';
/** Somebody who said no to this court — named by the wire's `people`, and never a member. */
const BO = 'dddddddd-0000-4000-8000-000000000004';

const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';

/** The header's second line in a booked room: the sport, and the booking's word. */
const BOOKED = 'booked';

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

function member(playerId: string, name: string): Wire['ConversationMemberSchema'] {
  return { player_id: playerId, nickname: name };
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

/** A *no* on this court, told by the one line whose actor a roster can never name (#409). */
function saidNo(seq: number): Wire['SystemLineSchema'] {
  return { ...line(seq, 'SEAT_LEFT'), actor_id: BO, values: { departure: 'DECLINED' } };
}

/** A title budget no room in these tests needs, so a line is asserted on its words alone. */
const ROOM_ENOUGH = 80;

/**
 * A room whose `people` is its members and nobody else — the ordinary room, where everybody the
 * entries name is on the court. A suite naming somebody who is not supplies `people` itself.
 */
function room(over: Partial<Wire['ConversationResponse']> = {}): Wire['ConversationResponse'] {
  const members = over.members ?? PAIR;

  return {
    read_at: READ_AT,
    conversation_id: ROOM,
    booking_id: BOOKING,
    game_id: GAME,
    sport: 'PADEL',
    members,
    people: members,
    entries: [],
    ...over,
  };
}

function listed(over: Partial<Wire['ConversationRowSchema']> = {}): Wire['ConversationRowSchema'] {
  const members = over.members ?? PAIR;

  return {
    conversation_id: ROOM,
    booking_id: BOOKING,
    game_id: GAME,
    sport: 'PADEL',
    members,
    people: members,
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
  await forgetPhonePreferences();
});

/** Where the booked game's room is — pushed over its details, or over Home from its card (Q100). */
const CHAT_ROUTE = `/booking/${BOOKING}/chat`;

/**
 * Land on the booked game's details and press *Open the chat* — the walk every assertion here
 * starts with. `listedAs` is the room the rooms list holds, which is what the details find the
 * room by; the room's own read is `answer`.
 */
async function openTheRoom(
  answer: Wire['ConversationResponse'] = room(),
  listedAs: Wire['ConversationRowSchema'] = listed({ members: answer.members }),
) {
  stubHomeGames(transport, [homeGame({ game_id: GAME })]);
  stubBooking(transport, bookingDetails({ game_id: GAME }));
  stubConversations(transport, [listedAs]);
  stubConversation(transport, answer);
  stubEntries(transport, ROOM);

  await launchSignedIn(`/booking/${BOOKING}`);
  fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));
  await waitFor(() => expect(screen).toHavePathname(CHAT_ROUTE));
}

describe('the header', () => {
  /**
   * **The drawn line is stemmed and the spoken name is whole, and the two differing is the point**
   * ([#401](https://github.com/Raketa02/Raketa/issues/401)) — so both are asserted in one test,
   * against the copy deck: `headerTitle` is `handleStem` over `handleLine`, and
   * `conversationHeaderLabel` is every handle whole in the row's own dialect.
   */
  it('draws the stems and speaks the whole handles, in one element', async () => {
    await openTheRoom(room({ members: THREE }));

    const spoken = conversationHeaderLabel(['tomek.p', 'ola.k'], sportLabel('padel'), BOOKED);
    const header = await screen.findByRole('header', { name: spoken });

    expect(within(header).getByText(headerTitle(['tomek.p', 'ola.k'], ROOM_ENOUGH))).toBeTruthy();
    expect(within(header).queryByText(/tomek\.p/)).toBeNull();
  });

  /**
   * **ania.k, by her nickname, and never with an @**
   * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1). The
   * header draws her stem — cut at her first dot, a prefix she typed, drawn only in this box
   * (ADR-0157) — and speaks her whole; her bubble in a room of three draws her whole, and the line
   * about what she did says her whole.
   */
  it('names a member by her nickname — the header, her bubble and a line about her', async () => {
    await openTheRoom(
      room({
        members: [member(ME, 'me_'), member(TOMEK, 'ania.k'), member(OLA, 'ola.k')],
        entries: [line(1, 'SEAT_ACCEPTED'), message(2, TOMEK, 'six works for me')],
      }),
    );

    const spoken = conversationHeaderLabel(['ania.k', 'ola.k'], sportLabel('padel'), BOOKED);
    const header = await screen.findByRole('header', { name: spoken });
    expect(within(header).getByText(headerTitle(['ania.k', 'ola.k'], ROOM_ENOUGH))).toBeTruthy();
    expect(within(header).queryByText(/ania\.k/)).toBeNull();

    const bubble = screen.getByLabelText('ania.k: six works for me');
    expect(within(bubble).getByText('ania.k')).toBeTruthy();

    const sentence = systemLineSentence(
      {
        kind: 'system-line',
        seq: 1,
        code: 'SEAT_ACCEPTED',
        occurredAt: READ_AT,
        actorId: TOMEK,
        values: {},
      },
      [{ playerId: TOMEK, name: 'ania.k' }],
    );
    expect(sentence).toMatch(/^ania\.k /);
    expect(screen.getByText(sentence)).toBeTruthy();
    expect(screen.queryByText(/@/)).toBeNull();
  });

  /**
   * **The booking's word after the sport** (#556): the details have just read the booking, and the
   * room says where the game stands in the word its card says — drawn and spoken.
   */
  it('says where the game stands, in the booking’s own word', async () => {
    await openTheRoom();

    const header = await screen.findByRole('header', {
      name: conversationHeaderLabel(['tomek.p'], sportLabel('padel'), BOOKED),
    });

    expect(within(header).getByText(headerSubline(sportLabel('padel'), BOOKED))).toBeTruthy();
  });

  /**
   * **The organiser alone again** ([#429](https://github.com/Raketa02/Raketa/issues/429) E4):
   * B joined and left while C and D were still deciding, so the room stands with one member and
   * nobody to name. The title slot said nothing — a blank at `h1` over *Padel* — and now says
   * what the room is doing, spoken the same way. The list is stubbed as it last read the room, a
   * pair, so there is a row to open; what is asserted is the room's own read.
   */
  it('says it is waiting for others where the reader is alone in the room', async () => {
    await openTheRoom(room({ members: [member(ME, 'me_')] }), listed());

    const header = await screen.findByRole('header', {
      name: conversationHeaderLabel([], sportLabel('padel'), BOOKED),
    });

    expect(within(header).getByText(WAITING_FOR_OTHERS)).toBeTruthy();
    expect(within(header).getByText(headerSubline(sportLabel('padel'), BOOKED))).toBeTruthy();
    expect(within(header).queryByText(/me_/)).toBeNull();
  });

  /**
   * **No door back into the details** (#556): the room is reached from them, and *back* is them —
   * a second way to the same screen would stack the details on themselves.
   */
  it('draws no Details door, and back is the details it was opened from', async () => {
    await openTheRoom();

    const header = await screen.findByRole('header', {
      name: conversationHeaderLabel(['tomek.p'], sportLabel('padel'), BOOKED),
    });
    expect(within(header).queryByText('Details')).toBeNull();
    expect(screen.queryByLabelText('Open the game')).toBeNull();

    fireEvent.press(screen.getAllByLabelText('Back').at(-1)!);
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
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
      [{ playerId: TOMEK, name: 'tomek.p' }],
    );

    expect(await screen.findByText(sentence)).toBeTruthy();
    expect(screen.getByLabelText('tomek.p: six works for me')).toBeTruthy();
  });

  /**
   * The old loop's lock line, which no room writes any more (#576) and a stored room may still
   * hold: rendered from the copy deck with `{name}` filled from the people the room names, and
   * quoting no value (ADR-0155). A stored line folds; a code with no words would not compile.
   */
  it('draws a stored lock line as the sentence the deck writes, and quotes no value', async () => {
    await openTheRoom(room({ entries: [line(1, 'PLAN_LOCKED')] }));

    const sentence = systemLineSentence(
      {
        kind: 'system-line',
        seq: 1,
        code: 'PLAN_LOCKED',
        occurredAt: READ_AT,
        actorId: TOMEK,
        values: {},
      },
      [{ playerId: TOMEK, name: 'tomek.p' }],
    );

    expect(await screen.findByText(sentence)).toBeTruthy();
  });

  /**
   * **The old doubles room's first words** — a line the old loop's rooms were born with, at
   * `seq` 1 with no actor, drawn as every other system line is (ADR-0169 §8). Which rooms carry it
   * is the stream's, and the client draws what the stream holds without reading the sport.
   */
  it('draws a stored You two are a side, named by nobody', async () => {
    const born: Wire['SystemLineSchema'] = { ...line(1, 'SIDE_FORMED'), actor_id: null };
    await openTheRoom(room({ entries: [born, message(2, TOMEK, 'who do we ask?')] }));

    expect(await screen.findByText(SIDE_FORMED_LINE)).toBeTruthy();
    expect(screen.queryByText(/^\? /)).toBeNull();
  });

  it('draws no such line in a room the stream did not open with one', async () => {
    await openTheRoom(room({ sport: 'TENNIS', entries: [line(1, 'SEAT_ACCEPTED')] }));

    await screen.findByText('tomek.p is in');
    expect(screen.queryByText(SIDE_FORMED_LINE)).toBeNull();
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

  /**
   * A page names its own authors and actors and nothing about the roster, and the room's first
   * read could not have named them — so the page's `people` is **merged** into what the screen
   * holds, and a line on it names somebody nobody else on screen has heard of.
   */
  it('names a departed player off the page that carries them', async () => {
    await openTheRoom(room({ entries: [message(4, TOMEK, 'four')] }));
    await screen.findByLabelText('tomek.p: four');
    stubEntries(transport, ROOM, [saidNo(3)], [{ player_id: BO, nickname: 'bo' }]);

    fireEvent(screen.getByTestId('conversation-stream'), 'endReached');

    await waitFor(() =>
      expect(screen.getByText('bo said no — that seat is open again')).toBeTruthy(),
    );
    expect(screen.getByLabelText('tomek.p: four')).toBeTruthy();
  });
});

/**
 * **`{name}` is filled from the people the response names, and not from the roster**
 * ([#409](https://github.com/Raketa02/Raketa/issues/409)). Membership is the accepted seats, a
 * *no* is not one, so the actor of a `SEAT_LEFT` line was never a member and the room used to
 * draw `? said no — that seat is open again` — the one line a roster lookup cannot name.
 */
describe('who a line names', () => {
  it('names a player who said no, though they are not a member', async () => {
    await openTheRoom(
      room({
        members: PAIR,
        people: [...PAIR, { player_id: BO, nickname: 'bo' }],
        entries: [saidNo(1), message(2, TOMEK, 'shame')],
      }),
    );

    expect(await screen.findByText('bo said no — that seat is open again')).toBeTruthy();
    expect(screen.queryByText(/^\? said no/)).toBeNull();
  });

  /** The line says the whole name, space and all — *Diego Fabregat left*, never *Diego.Fabregat*. */
  it('names the actor of a line by their whole name', async () => {
    await openTheRoom(
      room({
        members: PAIR,
        people: [...PAIR, { player_id: BO, nickname: 'Diego Fabregat' }],
        entries: [saidNo(1)],
      }),
    );

    expect(
      await screen.findByText('Diego Fabregat said no — that seat is open again'),
    ).toBeTruthy();
  });

  /** The `?` is for one case: the platform can no longer name the account. */
  it('draws the unknown player for somebody the platform has lost the handle of', async () => {
    await openTheRoom(
      room({ people: [...PAIR, { player_id: BO, nickname: null }], entries: [saidNo(1)] }),
    );

    expect(await screen.findByText('? said no — that seat is open again')).toBeTruthy();
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

    fireEvent.changeText(await screen.findByLabelText(COMPOSER_LABEL), 'on my way');
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

    fireEvent.changeText(await screen.findByLabelText(COMPOSER_LABEL), 'on my way');
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

    const box = await screen.findByLabelText(COMPOSER_LABEL);
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
    expect(screen.getByLabelText(COMPOSER_LABEL).props.value).toBe('a very long message');
    expect(screen.queryByLabelText('You: a very long message')).toBeNull();
  });

  /**
   * §3.7 as amended by [#429](https://github.com/Raketa02/Raketa/issues/429): **a room that ends
   * while it is on screen stays on screen, closed.** A send answered `conversation_not_found` is
   * a send racing the nudge, and it does not decide the room is over — the read does, so the send
   * asks the read again and the read closes the room. One code for three cases, and there is no
   * retry that changes any of them.
   */
  it('closes the room in place when a send finds it has gone', async () => {
    await openTheRoom();
    await screen.findByLabelText(COMPOSER_LABEL);

    transport.on('POST', `${conversationPath(ROOM)}/messages`, () =>
      errorResponse(404, 'conversation_not_found'),
    );
    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));

    fireEvent.changeText(screen.getByLabelText(COMPOSER_LABEL), 'anyone there?');
    fireEvent.press(screen.getByRole('button', { name: SEND }));

    expect(await screen.findByText(ROOM_OVER_LINE)).toBeTruthy();
    expect(screen).toHavePathname(CHAT_ROUTE);
    expect(screen.queryByLabelText(COMPOSER_LABEL)).toBeNull();
  });

  it('leaves the screen when the read finds the room has gone', async () => {
    stubHomeGames(transport, [homeGame({ game_id: GAME })]);
    stubBooking(transport, bookingDetails({ game_id: GAME }));
    stubConversations(transport, [listed()]);
    transport.on('GET', conversationPath(ROOM), () => errorResponse(404, 'conversation_not_found'));
    stubEntries(transport, ROOM);

    await launchSignedIn(`/booking/${BOOKING}`);
    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    // It gets as far as the route and comes straight back, rather than sitting on a sentence
    // about a room that is not there.
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  });
});

/**
 * **The field and Send are one block** ([#402](https://github.com/Raketa02/Raketa/issues/402)) —
 * asserted structurally, because *one block* is a claim about what contains what and a renderer
 * cannot see a ground or a hairline. A booked game has no plan, so the block asks no questions
 * about one: no quick chip is drawn (#576).
 */
describe('the composer block', () => {
  it('holds the field and Send together, and no chip', async () => {
    await openTheRoom();

    const block = await screen.findByTestId('conversation-composer');

    expect(within(block).getByLabelText(COMPOSER_LABEL)).toBeTruthy();
    expect(within(block).getByRole('button', { name: SEND })).toBeTruthy();
    expect(within(block).getAllByRole('button')).toHaveLength(1);
  });

  /** The hint is the deck's, and the name a listener gets is still `Message` — 6.13's own rule. */
  it('hints at what the box is for, and keeps its spoken name', async () => {
    await openTheRoom();

    const field = await screen.findByPlaceholderText(COMPOSER_PLACEHOLDER);

    expect(field.props.accessibilityLabel).toBe(COMPOSER_LABEL);
  });
});

/**
 * **The frame, asserted structurally**, the way `ShellScreen.test.tsx` asserts 10.1's — because
 * every claim here is about *what contains what*, and both fail invisibly in a renderer with no
 * status bar and no home indicator ([#400](https://github.com/Raketa02/Raketa/issues/400)).
 *
 * The edges are read rather than a padding measured, because the padding is the library's
 * arithmetic and the edges are the app's decision.
 */
describe('the frame', () => {
  /**
   * The safe area around one thing — the stack keeps the details mounted under the room, so there
   * is more than one frame in the tree and the assertion has to say which.
   */
  function safeAreaAround(inside: (scope: ReturnType<typeof within>) => unknown) {
    const frames = screen.UNSAFE_getAllByType(SafeAreaView);
    const own = frames.find((candidate) => inside(within(candidate)) !== null);
    if (own === undefined) throw new Error('nothing of the kind is inside a safe area');
    return own;
  }

  /** The room's own frame: the one with the composer inside it. */
  const frame = () => safeAreaAround((scope) => scope.queryByLabelText(COMPOSER_LABEL));

  it('clears the status bar, and takes the bottom inset because no bar is under it', async () => {
    await openTheRoom();
    await screen.findByLabelText(COMPOSER_LABEL);

    // Both edges, and that is the exception 10.1 records: everywhere else the bottom inset is
    // the tab bar's, and this is the one screen the bar stands down on — so the inset has no
    // owner unless the room takes it, and untaken it is the field under the home indicator.
    expect(frame().props.edges).toEqual(['top', 'bottom']);
  });

  it('keeps the keyboard avoidance inside the safe area, not around it', async () => {
    await openTheRoom();
    await screen.findByLabelText(COMPOSER_LABEL);

    // Outside, the keyboard offset would be computed against a frame that includes the inset
    // and the composer would ride 34pt above the keyboard. Inside, the frame's bottom is where
    // the keyboard's top will be.
    expect(within(frame()).UNSAFE_getByType(KeyboardAvoidingView)).toBeTruthy();
  });

  it('draws the placeholder header inside a safe area too, while the room is still coming', async () => {
    // The read in flight draws 10.3's header over a title the room has before it can be named,
    // and a header that collided with the clock for the length of a read is the same bug for
    // the length of a read.
    stubHomeGames(transport, [homeGame({ game_id: GAME })]);
    stubBooking(transport, bookingDetails({ game_id: GAME }));
    stubConversations(transport, [listed()]);
    transport.on('GET', conversationPath(ROOM), () => new Promise(() => {}));
    stubEntries(transport, ROOM);

    await launchSignedIn(`/booking/${BOOKING}`);
    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));
    await waitFor(() => expect(screen).toHavePathname(CHAT_ROUTE));

    await screen.findByRole('header', { name: CONVERSATION_SCREEN_TITLE });
    const around = safeAreaAround((scope) =>
      scope.queryByRole('header', { name: CONVERSATION_SCREEN_TITLE }),
    );

    expect(around.props.edges).toEqual(['top']);
  });
});
