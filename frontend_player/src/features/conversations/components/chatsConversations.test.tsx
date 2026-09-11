/**
 * **`CONVERSATIONS`, walked the way a player walks it**: the real route tree, the real shell, and
 * only `fetch` faked.
 *
 * Most of [#363](https://github.com/Raketa02/Raketa/issues/363)'s acceptance criteria are
 * assertions in this file and opinions nowhere else — the section holds every room, the heading
 * carries no count, the row is a door, the last entry is rendered by the module the stream will
 * use, a room whose membership is still growing draws the members it has, a
 * `LINE_UP_INCOMPLETE` challenge you accepted is drawn in **both** sections, and the empty state
 * names the act instead of asserting emptiness.
 *
 * It asserts against the **copy deck** rather than against strings wherever a sentence has one,
 * because the wording is the deck's to change and the rules are not.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { CHATS_COPY } from '@/features/shell/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  CONVERSATIONS_PATH,
  GATE_USER,
  launchSignedIn,
  stubChallenges,
  stubConversations,
  stubGate,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { CONVERSATIONS_HEADING } from './conversationPresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const OLA = 'cccccccc-0000-4000-8000-000000000003';
const KUBA = 'dddddddd-0000-4000-8000-000000000004';
/** Somebody who said no to this court — named by the wire's `people`, and never a member. */
const BO = 'ffffffff-0000-4000-8000-00000000000b';

const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';

/** One rating is what puts this player past the onboarding gate and into the app. */
const SQUASH_RATING: Wire['RatingResponse'] = {
  sport: 'SQUASH',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

function member(
  playerId: string,
  nickname: string,
  over: Partial<Wire['ConversationMemberSchema']> = {},
): Wire['ConversationMemberSchema'] {
  return { player_id: playerId, nickname, ...over };
}

/**
 * A row whose `people` is its members and nobody else — the ordinary row, where whoever the last
 * entry is about is on the court. A suite naming somebody who is not supplies `people` itself.
 */
function room(over: Partial<Wire['ConversationRowSchema']> = {}): Wire['ConversationRowSchema'] {
  const members = over.members ?? [member(ME, 'me_'), member(TOMEK, 'tomek.p')];

  return {
    conversation_id: ROOM,
    challenge_id: 'ffffffff-0000-4000-8000-000000000006',
    game_id: null,
    sport: 'SQUASH',
    members,
    people: members,
    last_entry: null,
    ...over,
  };
}

function systemLine(
  code: string,
  values: Readonly<Record<string, string>>,
  actorId: string = TOMEK,
): Wire['SystemLineSchema'] {
  return {
    type: 'system_line',
    seq: 4,
    code,
    occurred_at: '2026-09-08T11:00:00Z',
    actor_id: actorId,
    values,
  };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [SQUASH_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land in the app with these rooms, and open the Chats tab. */
async function openChats(rooms: readonly Wire['ConversationRowSchema'][] = []) {
  stubConversations(transport, rooms);
  await launchSignedIn();

  fireEvent.press(await screen.findByLabelText(/^Chats/));
  await waitFor(() => expect(screen).toHavePathname('/chats'));
}

describe('what the section holds', () => {
  it('holds every room you are a member of, under one heading', async () => {
    await openChats([
      room(),
      room({
        conversation_id: 'aaaaaaaa-0000-4000-8000-00000000000a',
        sport: 'PADEL',
        members: [member(ME, 'me_'), member(OLA, 'ola.k'), member(KUBA, 'kuba.z')],
      }),
    ]);

    expect(await screen.findByRole('header', { name: CONVERSATIONS_HEADING })).toBeTruthy();
    expect(await screen.findByLabelText(/^tomek\.p, Squash/)).toBeTruthy();
    expect(await screen.findByLabelText(/^ola\.k and kuba\.z, Padel/)).toBeTruthy();
  });

  /**
   * The badge is the only number on this screen, and it counts unanswered challenges addressed
   * to you — a count of rooms beside it would be two numbers meaning different things.
   */
  it('puts no count on the heading', async () => {
    await openChats([room()]);

    const heading = await screen.findByRole('header', { name: CONVERSATIONS_HEADING });

    expect(heading.props.children).toBe(CONVERSATIONS_HEADING);
  });

  /** Membership grows one acceptance at a time; a row that drew four would draw the court. */
  it('draws the members a growing doubles room has, never the court it will become', async () => {
    await openChats([
      room({ sport: 'PADEL', members: [member(ME, 'me_'), member(TOMEK, 'tomek.p')] }),
    ]);

    expect(await screen.findByText('tomek.p')).toBeTruthy();
    expect(screen.queryByText(/\+\d/)).toBeNull();
  });
});

describe('the row', () => {
  it('is one element and one door: the whole row is the button', async () => {
    await openChats([room()]);

    fireEvent.press(await screen.findByLabelText(/^tomek\.p, Squash/));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
  });

  it('says the sport and the last thing that happened, on one line', async () => {
    await openChats([room({ last_entry: systemLine('SEAT_ACCEPTED', {}) })]);

    const line = await screen.findByText('Squash · tomek.p is in');

    expect(line.props.numberOfLines).toBe(1);
  });

  /** A message renders as its own text, with nobody named in front of it. */
  it('draws a message as the words somebody typed', async () => {
    await openChats([
      room({
        last_entry: {
          type: 'message',
          seq: 9,
          author_id: TOMEK,
          sent_at: '2026-09-08T11:30:00Z',
          text: 'six works for me',
          client_message_id: 'aaaaaaaa-0000-4000-8000-00000000000b',
        },
      }),
    ]);

    expect(await screen.findByText('Squash · six works for me')).toBeTruthy();
  });

  /**
   * A system line is a code and its values, and `{name}` is filled from the people the row
   * already holds — never from `values`, so a corrected handle fixes the whole backlog.
   */
  it('draws a system line from its code, naming its actor out of the people it holds', async () => {
    await openChats([room({ last_entry: systemLine('DAY_RECORDED', { value: '2026-09-12' }) })]);

    expect(await screen.findByText('Squash · tomek.p set the day · Saturday')).toBeTruthy();
  });

  /** #335: when a system line does not fit, the fix is a shorter value rather than a second line. */
  it('drops the court from a place that is too long, and stays on one line', async () => {
    await openChats([
      room({ last_entry: systemLine('PLACE_RECORDED', { value: 'Zabłocie Sport, court 3' }) }),
    ]);

    const line = await screen.findByText('Squash · tomek.p set the place · Zabłocie Sport');

    expect(line.props.numberOfLines).toBe(1);
  });

  /** §20.4: the visible label truncates, the spoken one never does — in either register. */
  it('speaks the whole place, and every handle, whatever the row drew', async () => {
    await openChats([
      room({
        members: [member(ME, 'me_'), member(TOMEK, 'tomek.p'), member(OLA, 'ola.k')],
        last_entry: systemLine('PLACE_RECORDED', { value: 'Zabłocie Sport, court 3' }),
      }),
    ]);

    const row = await screen.findByLabelText(/^tomek\.p and ola\.k, Squash/);

    expect(row.props.accessibilityLabel).toContain(
      'tomek.p set the place · Zabłocie Sport, court 3',
    );
  });

  /**
   * **The one line a roster lookup cannot name** ([#409](https://github.com/Raketa02/Raketa/issues/409)):
   * a *no* is not an accepted seat, so the actor of a `SEAT_LEFT` line was never a member and the
   * row used to read `? said no`. `{name}` is filled from the row's `people`, which names them —
   * in the drawn line and in the spoken one alike.
   */
  it('names a player who said no off the people the row holds, though they are not a member', async () => {
    await openChats([
      room({
        sport: 'PADEL',
        members: [member(ME, 'me_'), member(TOMEK, 'tomek.p'), member(OLA, 'ola.k')],
        people: [
          member(ME, 'me_'),
          member(TOMEK, 'tomek.p'),
          member(OLA, 'ola.k'),
          member(BO, 'bo'),
        ],
        last_entry: systemLine('SEAT_LEFT', { departure: 'DECLINED' }, BO),
      }),
    ]);

    expect(await screen.findByText('Padel · bo said no — that seat is open again')).toBeTruthy();
    const row = screen.getByLabelText(/^tomek\.p and ola\.k, Padel/);
    expect(row.props.accessibilityLabel).toContain('bo said no — that seat is open again');
  });

  /** The opening writes no line, so a room with no history has genuinely had nothing happen. */
  it('says the sport alone in a room where nothing has happened yet', async () => {
    await openChats([room()]);

    expect(await screen.findByText('Squash')).toBeTruthy();
  });

  /**
   * ADR-0148 §6: the last line is what a pill would have said, and the only pill this client
   * could draw would be joined off the games cache.
   */
  it('draws no state pill of any kind', async () => {
    await openChats([room({ last_entry: systemLine('SEAT_ACCEPTED', {}) })]);

    await screen.findByLabelText(/^tomek\.p, Squash/);

    for (const pill of [/^Planning$/, /^Game on$/, /^Confirm the result$/, /^Settle up$/]) {
      expect(screen.queryByText(pill)).toBeNull();
    }
  });
});

describe('the row that is in both sections at once', () => {
  /**
   * §13's own sentence asserts both facts in one breath, so a screen asserting both in two
   * places is the copy's shape rather than a duplicate: the challenge row is the **obligation**
   * and the conversation row is the **room**. Drawing it only under `CHALLENGES` would make it
   * the waiting room #221 says it is not.
   */
  it('draws a line-up-incomplete challenge you accepted under both headings', async () => {
    stubChallenges(
      transport,
      [
        {
          challenge_id: 'ffffffff-0000-4000-8000-000000000006',
          sport: 'PADEL',
          organiser_id: TOMEK,
          standing: 'LINE_UP_INCOMPLETE',
          opened_at: '2026-09-05T08:00:00Z',
          seats: [
            { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', nickname: 'tomek.p' },
            { side: 'A', player_id: ME, answer: 'ACCEPTED', nickname: 'me_' },
            { side: 'B' },
            { side: 'B' },
          ],
        },
      ],
      '2026-09-05T09:00:00Z',
    );

    await openChats([
      room({
        sport: 'PADEL',
        members: [member(ME, 'me_'), member(TOMEK, 'tomek.p')],
        last_entry: systemLine('SEAT_ACCEPTED', {}),
      }),
    ]);

    // Two reads, two sections, and they land independently — so the count is awaited rather
    // than taken the moment the first of them arrives.
    await waitFor(() => expect(screen.getAllByLabelText(/^tomek\.p, Padel/)).toHaveLength(2));

    // Two jobs, and they say two different things: the obligation names the open seats, and the
    // room names the last thing that happened in it.
    const said = screen
      .getAllByLabelText(/^tomek\.p, Padel/)
      .map((row) => String(row.props.accessibilityLabel));

    expect(said).toEqual(
      expect.arrayContaining([
        expect.stringContaining('seats open'),
        expect.stringContaining('tomek.p is in'),
      ]),
    );
  });
});

describe('what the section says when it holds nothing', () => {
  it('names the act instead of asserting that nothing is happening', async () => {
    await openChats([]);

    expect(await screen.findByText(CHATS_COPY.emptyConversations)).toBeTruthy();
    expect(screen.queryByText(/nothing|empty/i)).toBeNull();
  });

  /** A section that vanished on a read failure is indistinguishable from having no rooms. */
  it('says a read failed rather than drawing the emptiness it cannot tell apart', async () => {
    transport.on('GET', CONVERSATIONS_PATH, () => errorResponse(500, 'boom'));
    await launchSignedIn();

    fireEvent.press(await screen.findByLabelText(/^Chats/));

    expect(await screen.findByRole('header', { name: CONVERSATIONS_HEADING })).toBeTruthy();
    expect(screen.queryByText(CHATS_COPY.emptyConversations)).toBeNull();
  });
});
