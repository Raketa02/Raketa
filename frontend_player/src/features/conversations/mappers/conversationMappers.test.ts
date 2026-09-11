/**
 * The wire boundary's three answers to something it cannot read, which are deliberately three
 * different answers — and the three fields the room carries that the row does not.
 *
 * A **sport** takes the whole row with it, a **code** degrades in place, and an **entry shape**
 * collapses into a state the wire already has. Each is stated here because each is a decision
 * somebody could reasonably have made the other way.
 */

import type { Wire } from '@/test-support/transport';

import { toConversationRoom, toConversations, toEntryPage, toMessage } from './conversationMappers';

const ME = 'aaaaaaaa-0000-4000-8000-000000000001';
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
/** Somebody who said no to this court — named by the wire, and never a member. */
const BO = 'eeeeeeee-0000-4000-8000-000000000099';

function member(over: Partial<Wire['ConversationMemberSchema']> = {}) {
  return { player_id: TOMEK, nickname: 'tomek.p', ...over };
}

/**
 * A row whose `people` is its members and nobody else — the ordinary row, where every actor is
 * on the court. A suite naming somebody who is not supplies `people` itself.
 */
function room(over: Partial<Wire['ConversationRowSchema']> = {}): Wire['ConversationRowSchema'] {
  const members = over.members ?? [member(), member({ player_id: ME, nickname: 'me_' })];

  return {
    conversation_id: 'cccccccc-0000-4000-8000-000000000003',
    challenge_id: 'dddddddd-0000-4000-8000-000000000004',
    game_id: null,
    sport: 'PADEL',
    members,
    people: members,
    last_entry: null,
    ...over,
  };
}

function mapped(over: Partial<Wire['ConversationRowSchema']> = {}) {
  return toConversations({ read_at: '2026-09-08T12:00:00Z', conversations: [room(over)] });
}

describe('what crosses', () => {
  it('keeps the room, its sport and every member', () => {
    const [conversation] = mapped();

    expect(conversation).toMatchObject({
      conversationId: 'cccccccc-0000-4000-8000-000000000003',
      sport: 'padel',
      members: [
        { playerId: TOMEK, nickname: 'tomek.p' },
        { playerId: ME, nickname: 'me_' },
      ],
    });
  });

  /**
   * The game the line-up completed into rides on the row for one reader — the accept told `ON`,
   * waiting to push a room that knows its game — and `null` collapses to absent, as on the room.
   */
  it('carries the game once the room has been told it, and nothing before', () => {
    expect(mapped({ game_id: 'eeeeeeee-0000-4000-8000-000000000005' })[0]?.gameId).toBe(
      'eeeeeeee-0000-4000-8000-000000000005',
    );
    expect(mapped()[0]).not.toHaveProperty('gameId');
  });

  /** The order is the server's — *by the last entry, newest first* — and nothing re-sorts it. */
  it('keeps the order it was answered in', () => {
    const rooms = toConversations({
      read_at: '2026-09-08T12:00:00Z',
      conversations: [
        room({ conversation_id: 'first' }),
        room({ conversation_id: 'second' }),
        room({ conversation_id: 'third' }),
      ],
    });

    expect(rooms.map((one) => one.conversationId)).toEqual(['first', 'second', 'third']);
  });

  /** The two photo fields travel as a pair or not at all, and an absence is a poster. */
  it('carries a photograph where there is one, and nothing where there is not', () => {
    const [withPhoto] = mapped({
      members: [member({ photo_id: 'photo-1', photo_url: 'https://example/photo-1' })],
    });

    expect(withPhoto?.members[0]).toEqual({
      playerId: TOMEK,
      nickname: 'tomek.p',
      photoUrl: 'https://example/photo-1',
    });
    expect(mapped()[0]?.members[0]).not.toHaveProperty('photoUrl');
  });

  /** A member `users` can no longer name keeps their place: dropping them draws a short court. */
  it('keeps a member whose handle the platform has lost', () => {
    const [conversation] = mapped({ members: [member({ nickname: null })] });

    expect(conversation?.members).toEqual([{ playerId: TOMEK }]);
  });

  /**
   * **Everybody the row names, and not only who is on the court**
   * ([#409](https://github.com/Raketa02/Raketa/issues/409)). A *no* is not an accepted seat, so
   * the actor of a `SEAT_LEFT` line was never a member — `people` is the list that can name them,
   * and it is mapped as the same shape a member is, under a wider claim.
   */
  it('carries the people the row names, a member and a departed player alike', () => {
    const [conversation] = mapped({
      members: [member()],
      people: [
        member(),
        { player_id: BO, nickname: 'bo', photo_id: 'p-1', photo_url: 'https://x/1' },
      ],
    });

    expect(conversation?.people).toEqual([
      { playerId: TOMEK, nickname: 'tomek.p' },
      { playerId: BO, nickname: 'bo', photoUrl: 'https://x/1' },
    ]);
  });

  /** `nickname: null` is the one case the `?` is for, on a person exactly as on a member. */
  it('keeps a person whose handle the platform has lost, with no handle', () => {
    const [conversation] = mapped({ people: [member(), { player_id: BO, nickname: null }] });

    expect(conversation?.people).toEqual([
      { playerId: TOMEK, nickname: 'tomek.p' },
      { playerId: BO },
    ]);
  });
});

describe('the two shapes on the stream', () => {
  it('reads a message as somebody’s own words', () => {
    const [conversation] = mapped({
      last_entry: {
        type: 'message',
        seq: 7,
        author_id: TOMEK,
        sent_at: '2026-09-08T11:00:00Z',
        text: 'on my way',
        client_message_id: 'eeeeeeee-0000-4000-8000-000000000005',
      },
    });

    expect(conversation?.lastEntry).toEqual({
      kind: 'message',
      seq: 7,
      authorId: TOMEK,
      sentAt: '2026-09-08T11:00:00Z',
      text: 'on my way',
      clientMessageId: 'eeeeeeee-0000-4000-8000-000000000005',
    });
  });

  it('reads a system line as a code, an actor and its values', () => {
    const [conversation] = mapped({
      last_entry: {
        type: 'system_line',
        seq: 3,
        code: 'DAY_RECORDED',
        occurred_at: '2026-09-08T11:00:00Z',
        actor_id: TOMEK,
        values: { value: '2026-09-12' },
      },
    });

    expect(conversation?.lastEntry).toEqual({
      kind: 'system-line',
      seq: 3,
      code: 'DAY_RECORDED',
      occurredAt: '2026-09-08T11:00:00Z',
      actorId: TOMEK,
      values: { value: '2026-09-12' },
    });
  });

  /**
   * A room whose first acceptance is its whole history has no entry at all — the opening writes
   * no line. It is a real state rather than an edge case, and `null` collapses to absent.
   */
  it('reads no last entry at all as an absence rather than as a blank', () => {
    expect(mapped()[0]).not.toHaveProperty('lastEntry');
  });
});

describe('what this build cannot read', () => {
  /** Vocabulary degrades in place: the line stays and the row draws §3's named gap. */
  it('keeps a system line whose code it has no words for', () => {
    const [conversation] = mapped({
      last_entry: {
        type: 'system_line',
        seq: 3,
        code: 'BOOKING_CONFIRMED',
        occurred_at: '2026-09-08T11:00:00Z',
        actor_id: TOMEK,
        values: {},
      },
    });

    expect(conversation?.lastEntry).toMatchObject({ kind: 'system-line', seq: 3 });
    expect(conversation?.lastEntry).not.toHaveProperty('code');
  });

  /** Structure is refused whole: the sport is what the row calls the room. */
  it('drops a room whose sport it cannot name', () => {
    expect(mapped({ sport: 'PICKLEBALL' as Wire['Sport'] })).toEqual([]);
  });
});

describe('one room, opened', () => {
  function opened(over: Partial<Wire['ConversationResponse']> = {}): Wire['ConversationResponse'] {
    const members = over.members ?? [member()];

    return {
      read_at: '2026-09-08T12:00:00Z',
      conversation_id: 'cccccccc-0000-4000-8000-000000000003',
      challenge_id: 'dddddddd-0000-4000-8000-000000000004',
      game_id: null,
      sport: 'PADEL',
      members,
      people: members,
      entries: [],
      ...over,
    };
  }

  /** Three fields the row deliberately leaves off, each mapped by the screen that draws it. */
  it('carries the instant it was folded and both ids', () => {
    const room = toConversationRoom(
      opened({ game_id: 'eeeeeeee-0000-4000-8000-000000000005' }),
    )?.room;

    expect(room?.readAt).toBe('2026-09-08T12:00:00Z');
    expect(room?.challengeId).toBe('dddddddd-0000-4000-8000-000000000004');
    expect(room?.gameId).toBe('eeeeeeee-0000-4000-8000-000000000005');
  });

  /** A room with no game is a room with no *Details*, and `null` collapses to absent. */
  it('has no game where the wire says none', () => {
    expect(toConversationRoom(opened())?.room.gameId).toBeUndefined();
  });

  /**
   * The identifying fact is missing, so the record is refused whole — `challengeMappers`' and
   * `gameMappers`' answer for the same field, and the screen says the one thing true of every
   * cause it shares an answer with.
   */
  it('refuses the whole room where its sport is one this build cannot name', () => {
    expect(toConversationRoom(opened({ sport: 'PICKLEBALL' as Wire['Sport'] }))).toBeUndefined();
  });

  it('maps the newest page beside the header, oldest first as it arrived', () => {
    const said: Wire['MessageSchema'] = {
      type: 'message',
      seq: 4,
      author_id: TOMEK,
      sent_at: '2026-09-08T11:00:00Z',
      text: 'six works',
      client_message_id: 'client-4',
    };

    expect(toConversationRoom(opened({ entries: [said] }))?.entries).toEqual([
      {
        kind: 'message',
        seq: 4,
        authorId: TOMEK,
        sentAt: '2026-09-08T11:00:00Z',
        text: 'six works',
        clientMessageId: 'client-4',
      },
    ]);
  });

  /**
   * The people ride **beside** the header rather than on it: the header comes off the first read
   * alone, where the people grow with every page — so they are kept with the entries, which grow
   * the same way.
   */
  it('carries the people the newest page names, beside the room and not on it', () => {
    const room = toConversationRoom(
      opened({ members: [member()], people: [member(), { player_id: BO, nickname: 'bo' }] }),
    );

    expect(room?.people).toEqual([
      { playerId: TOMEK, nickname: 'tomek.p' },
      { playerId: BO, nickname: 'bo' },
    ]);
    expect(room?.room.members).toEqual([{ playerId: TOMEK, nickname: 'tomek.p' }]);
    expect(room?.room).not.toHaveProperty('people');
  });
});

describe('a page backward', () => {
  const line: Wire['SystemLineSchema'] = {
    type: 'system_line',
    seq: 2,
    code: 'SEAT_ACCEPTED',
    occurred_at: '2026-09-08T10:00:00Z',
    actor_id: TOMEK,
    values: {},
  };

  it('is the same narrowing with no header over it', () => {
    expect(toEntryPage({ entries: [line], people: [member()] }).entries).toEqual([
      {
        kind: 'system-line',
        seq: 2,
        code: 'SEAT_ACCEPTED',
        occurredAt: '2026-09-08T10:00:00Z',
        actorId: TOMEK,
        values: {},
      },
    ]);
  });

  /** The page's own authors and actors — not the roster, and nothing about who is in the room. */
  it('carries the people the page names, which is not the roster', () => {
    expect(toEntryPage({ entries: [line], people: [{ player_id: BO, nickname: null }] })).toEqual({
      entries: [expect.objectContaining({ seq: 2 })],
      people: [{ playerId: BO }],
    });
  });
});

describe('the message a send answers with', () => {
  /** The `seq` the server minted, and the id the optimistic bubble is reconciled on. */
  it('carries the seq and the client id', () => {
    expect(
      toMessage({
        type: 'message',
        seq: 9,
        author_id: ME,
        sent_at: '2026-09-08T12:00:00Z',
        text: 'on my way',
        client_message_id: 'client-9',
      }),
    ).toEqual({
      kind: 'message',
      seq: 9,
      authorId: ME,
      sentAt: '2026-09-08T12:00:00Z',
      text: 'on my way',
      clientMessageId: 'client-9',
    });
  });
});
