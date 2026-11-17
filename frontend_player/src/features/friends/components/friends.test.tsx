/**
 * **Friends, walked through the real route tree** ([#753](https://github.com/Raketa02/Raketa/issues/753),
 * PRD #743; [ADR-0202](../../../../../docs/adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md);
 * the friends screens §1, §2, §6.2).
 *
 * - **Members**: every row but yours ends in where the reader stands with them — **+ Add**,
 *   *request sent*, *friend* or **Accept** — and the pill acts while the rest of the row opens the
 *   record.
 * - **The record**: its foot is *Add friend* beside *Block*, *Request sent ▾* and *Friend ✓ ▾* behind
 *   a sheet that asks first, or *Accept*; your own has neither. (A blocked pair's record never opens
 *   since #773, so *Unblock* alone is no longer reachable.)
 * - **Needs your answer** (#816): *FRIEND REQUESTS · n* behind the header's envelope while a request
 *   waits, never on Home — *Not now* and *Accept* take the tile, and the last one closes the sheet
 *   and takes the envelope with it. A tile says who asks and their chip, and no where-line.
 *
 * **The friends routes are answered by a small fake of the server** (`friendServer`): an act changes
 * what the next read of Members, the record and Home says, as it would — so the pill that turns after
 * a press is the surface re-read, never this client guessing.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Dimensions, StyleSheet } from 'react-native';

import { BLOCKS_COPY, blockRowLabel } from '@/features/blocks/types';
import { OWN_RECORD_TITLE, RECORD_TITLE, recordCloseLabel } from '@/features/player_record/types';
import { proposalKeys } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import {
  ANIA,
  DECK_READ_AT,
  EWA,
  KAROL,
  deckCard,
  groupDeck,
  stubGroupDeck,
  youTile,
} from '@/test-support/groupDeck';
import {
  GATE_USER,
  HOME_PATH,
  NOTICES_PATH,
  SPORTS_SERVED,
  launchSignedIn,
  stubGate,
  stubHome,
  stubMyGroups,
  stubNotices,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { envelope, openNeedsYourAnswer, sheetTitle } from '@/test-support/needsYourAnswer';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import {
  FRIENDS_COPY,
  acceptLabel,
  addLabel,
  cancelTitle,
  notNowLabel,
  removeTitle,
  requestsHeading,
  wantsToBeYourFriend,
} from './friendsCopy';

const COPY = FRIENDS_COPY;

type Relation = Wire['FriendRelation'];

interface Person {
  readonly id: string;
  readonly name: string;
  readonly level: number;
  readonly score: number;
}

const person = (n: number, name: string, level: number, score: number): Person => ({
  id: `e0000000-0000-4000-8000-0000000000${String(n).padStart(2, '0')}`,
  name,
  level,
  score,
});

/** Nothing stands between them: **+ Add**, *Add friend*. */
const INES = person(1, 'ines.d', 3.4, 98);
/** Tomek asked, and it is open: *request sent*. */
const MICHAL = person(2, 'michal.r', 2.44, 48);
/** Friends: *friend*. */
const MAGDA = person(3, 'magda.p', 2.66, 97);
/** She asked Tomek: **Accept**. */
const ZOFIA = person(4, 'zofia.b', 2.69, 95);
/** Nothing between them, as INES. */
const KUBA = person(5, 'kuba.w', 2.8, 96);
const PEOPLE = [INES, MICHAL, MAGDA, ZOFIA, KUBA];

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

const PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://raketa.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [{ sport: 'PADEL', rated_count: 6, first_rated: [] }],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

const MEMBERS_PATH = `/api/v1/groups/${CREW.id}/members`;
const MEMBERS_ROUTE = `/play/group/${CREW.id}/members`;
const REQUESTS_PATH = '/api/v1/friends/requests';
const recordPath = (who: Person) => `/api/v1/players/${who.id}/record`;
const acceptPath = (who: Person) => `${REQUESTS_PATH}/${who.id}/acceptance`;
const setAsidePath = (who: Person) => `${REQUESTS_PATH}/${who.id}/set-aside`;
const cancelPath = (who: Person) => `${REQUESTS_PATH}/${who.id}`;
const removePath = (who: Person) => `/api/v1/friends/${who.id}`;

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.62,
    confidence: 28,
    range: { low: mu - 0.6, high: mu + 0.6 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

interface FriendServer {
  readonly relation: (who: Person) => Relation;
  /** The requests waiting on Tomek — open, not set aside, newest first. */
  readonly waiting: () => readonly Person[];
  /** `who` asks Tomek, as from their own phone: the next read of Home holds it. */
  readonly asks: (who: Person) => void;
}

/**
 * **The friends routes, faked** — the rules the routes document and nothing more: asking somebody
 * nothing stands between you and is `SENT`, or `FRIEND` when they had asked first; an accept answers
 * a request waiting on the reader, else `friend_request_not_found`; *Not now* keeps it open and takes
 * the card off Home; a cancel and a removal are 204 either way. Members, every record and Home read
 * the state.
 */
function friendServer(
  initially: Readonly<Record<string, Relation>> = {
    [INES.id]: 'NONE',
    [MICHAL.id]: 'SENT',
    [MAGDA.id]: 'FRIEND',
    [ZOFIA.id]: 'ASKED_YOU',
    [KUBA.id]: 'NONE',
  },
): FriendServer {
  const relations = new Map(Object.entries(initially));
  const setAside = new Set<string>();
  const relation = (who: Person): Relation => relations.get(who.id) ?? 'NONE';

  transport.on('POST', REQUESTS_PATH, (request) => {
    const { player_id: id } = request.body as Wire['AskToBeFriendsRequest'];
    const before = relations.get(id) ?? 'NONE';
    if (before === 'FRIEND') return errorResponse(409, 'already_friends');
    if (before === 'SENT') return errorResponse(409, 'friend_request_already_sent');
    const after: Relation = before === 'ASKED_YOU' ? 'FRIEND' : 'SENT';
    relations.set(id, after);
    return json<Wire['RelationResponse']>({ relation: after });
  });

  for (const who of PEOPLE) {
    transport.on('POST', acceptPath(who), () => {
      if (relation(who) !== 'ASKED_YOU') return errorResponse(404, 'friend_request_not_found');
      relations.set(who.id, 'FRIEND');
      return json<Wire['RelationResponse']>({ relation: 'FRIEND' });
    });
    transport.on('POST', setAsidePath(who), () => {
      if (relation(who) !== 'ASKED_YOU') return errorResponse(404, 'friend_request_not_found');
      setAside.add(who.id);
      return noContent();
    });
    transport.on('DELETE', cancelPath(who), () => {
      if (relation(who) === 'SENT') relations.set(who.id, 'NONE');
      return noContent();
    });
    transport.on('DELETE', removePath(who), () => {
      if (relation(who) === 'FRIEND') relations.set(who.id, 'NONE');
      return noContent();
    });
    transport.on('GET', recordPath(who), () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: relation(who),
        can_add_friend: true,
        nickname: who.name,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: who.level, band: 'Established' }],
        reliability: servedReliability({ player_score: who.score, is_new: false }),
      }),
    );
  }

  transport.on('GET', MEMBERS_PATH, () =>
    json<Wire['GroupMembersResponse']>({
      sport: 'PADEL',
      members: [
        {
          player_id: GATE_USER.id,
          nickname: GATE_USER.nickname ?? null,
          level: 2.71,
          player_score: 92,
          reliability_band: 'VERY_HIGH',
          is_owner: true,
          is_administrator: false,
          joined_at: '2026-09-01T10:00:00Z',
          relation: 'NONE',
        },
        ...PEOPLE.map((who) => ({
          player_id: who.id,
          nickname: who.name,
          level: who.level,
          player_score: who.score,
          reliability_band: 'VERY_HIGH' as const,
          is_owner: false,
          is_administrator: false,
          joined_at: '2026-09-10T10:00:00Z',
          relation: relation(who),
        })),
      ],
    }),
  );

  const waiting = () =>
    PEOPLE.filter((who) => relation(who) === 'ASKED_YOU' && !setAside.has(who.id));

  transport.on('GET', HOME_PATH, () =>
    json<Wire['HomeResponse']>({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [],
      friends_games: [],
      level_asks: [],
      friend_requests: waiting().map((who) => ({
        player_id: who.id,
        nickname: who.name,
        photo_id: null,
        photo_url: null,
        asked_at: '2026-10-01T07:00:00Z',
        by_link: false,
        from_ranking: false,
        from_new_players: false,
        from_same_level: false,
        from_same_vibe: false,
        group: { id: CREW.id, name: CREW.name },
        sport: 'PADEL',
        level: who.level,
        player_score: who.score,
        reliability_band: 'VERY_HIGH',
        percent_even: null,
        in_common: null,
      })),
    }),
  );

  const asks = (who: Person) => {
    relations.set(who.id, 'ASKED_YOU');
  };

  return { relation, waiting, asks };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [rating('PADEL', 2.71)], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubOwnRecord(transport);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Kazimierz crew's Members, for padel. */
async function openMembers() {
  await launchSignedIn();
  await screen.findByLabelText('Play');
  act(() => router.push(MEMBERS_ROUTE));
  await waitFor(() => expect(screen).toHavePathname(MEMBERS_ROUTE));
  expect(await screen.findByRole('header', { name: /^Members/ })).toBeTruthy();
  await screen.findByTestId(`member-${INES.id}`);
}

/** A row's right-hand end — the pill or the tag beside the row's own press. */
const end = (who: Person) => within(screen.getByTestId(`friend-row-${who.id}`));

/** Somebody's record, opened from their Members row. */
async function openRecordOf(who: Person) {
  await openMembers();
  fireEvent.press(screen.getByTestId(`member-${who.id}`));
  expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
  await waitFor(() => expect(transport.requestsTo('GET', recordPath(who)).length).toBe(1));
  // The record's answer drawn: its foot.
  await screen.findByRole('button', { name: blockRowLabel(who.name) });
}

const bellReads = () => transport.requestsTo('GET', NOTICES_PATH).length;

const asked = () => transport.requestsTo('POST', REQUESTS_PATH).map((request) => request.body);

/** An entry nothing on screen observes, seeded so nothing collects it before it is asked about. */
function seed(queryKey: readonly unknown[]) {
  queryClient.getQueryCache().build(queryClient, { queryKey, gcTime: Infinity });
  queryClient.setQueryData(queryKey, []);
}

/** Every read that draws a face and nothing on Members observes — a deck, a game, a booking. */
const FACES = [
  proposalKeys.deck(CREW.id, 'padel', 'competitive'),
  proposalKeys.proposal('f0000000-0000-4000-8000-000000000041'),
  proposalKeys.booking('e0000000-0000-4000-8000-000000000041'),
] as const;

const invalidated = (queryKey: readonly unknown[]) =>
  queryClient.getQueryState(queryKey)?.isInvalidated;

// ---------------------------------------------------------------------------
// Members (the screens §1; friends 1, 2)
// ---------------------------------------------------------------------------

describe('Members', () => {
  it('ends every row but yours in where you stand with them', async () => {
    friendServer();
    await openMembers();

    expect(end(INES).getByRole('button', { name: addLabel(INES.name) })).toBeTruthy();
    expect(end(INES).getByText(COPY.members.add)).toBeTruthy();
    expect(end(MICHAL).getByText(COPY.members.sent)).toBeTruthy();
    expect(end(MICHAL).queryByRole('button', { name: /^Add|^Accept/ })).toBeNull();
    expect(end(MAGDA).getByText(COPY.members.friend)).toBeTruthy();
    expect(end(ZOFIA).getByRole('button', { name: acceptLabel(ZOFIA.name) })).toBeTruthy();
    // Your own row ends in nothing, and the rows keep their design: the name, the chip, the line.
    expect(screen.queryByTestId(`friend-row-${GATE_USER.id}`)).toBeNull();
    expect(
      screen.getByLabelText(`${INES.name}, reliability 98, Very high, Padel 3,40`),
    ).toBeTruthy();
  });

  it('+ Add asks, naming the group and the sport, and the row turns request sent', async () => {
    const server = friendServer();
    await openMembers();

    fireEvent.press(end(INES).getByRole('button', { name: addLabel(INES.name) }));

    await waitFor(() => expect(asked()).toHaveLength(1));
    expect(asked()[0]).toEqual({
      player_id: INES.id,
      made_from: 'MEMBERS',
      group_id: CREW.id,
      sport: 'PADEL',
    });
    expect(await end(INES).findByText(COPY.members.sent)).toBeTruthy();
    expect(end(INES).queryByRole('button', { name: addLabel(INES.name) })).toBeNull();
    expect(server.relation(INES)).toBe('SENT');
  });

  it('Accept answers who asked you, and the row turns friend', async () => {
    friendServer();
    await openMembers();

    fireEvent.press(end(ZOFIA).getByRole('button', { name: acceptLabel(ZOFIA.name) }));

    await waitFor(() => expect(transport.requestsTo('POST', acceptPath(ZOFIA))).toHaveLength(1));
    expect(await end(ZOFIA).findByText(COPY.members.friend)).toBeTruthy();
  });

  // A friendship turning moves the friend tag on every face; a request moves none.
  it('re-reads every face when a friendship turns, and none on a request', async () => {
    friendServer();
    await openMembers();
    for (const key of FACES) seed(key);

    fireEvent.press(end(INES).getByRole('button', { name: addLabel(INES.name) }));
    expect(await end(INES).findByText(COPY.members.sent)).toBeTruthy();
    for (const key of FACES) expect(invalidated(key)).toBe(false);

    fireEvent.press(end(ZOFIA).getByRole('button', { name: acceptLabel(ZOFIA.name) }));
    expect(await end(ZOFIA).findByText(COPY.members.friend)).toBeTruthy();
    for (const key of FACES) expect(invalidated(key)).toBe(true);
  });

  it('opens the record from the rest of the row, and asks nobody', async () => {
    friendServer();
    await openMembers();

    fireEvent.press(screen.getByTestId(`member-${INES.id}`));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(asked()).toHaveLength(0);
  });

  it('says nothing of a refusal that is the state moving, and draws the new state', async () => {
    const server = friendServer();
    await openMembers();
    // She accepted on another phone meanwhile: the list still says + Add.
    transport.on('POST', REQUESTS_PATH, () => errorResponse(409, 'already_friends'));
    transport.on('GET', MEMBERS_PATH, () =>
      json<Wire['GroupMembersResponse']>({
        sport: 'PADEL',
        members: [
          {
            player_id: INES.id,
            nickname: INES.name,
            level: INES.level,
            player_score: INES.score,
            reliability_band: 'VERY_HIGH',
            is_owner: false,
            is_administrator: false,
            joined_at: '2026-09-10T10:00:00Z',
            relation: 'FRIEND',
          },
        ],
      }),
    );

    fireEvent.press(end(INES).getByRole('button', { name: addLabel(INES.name) }));

    expect(await end(INES).findByText(COPY.members.friend)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(server.relation(INES)).toBe('NONE');
  });

  it('says why where the pill was pressed, when the server refuses for a reason', async () => {
    friendServer();
    await openMembers();
    transport.on('POST', REQUESTS_PATH, () => errorResponse(409, 'unblock_them_first'));

    fireEvent.press(end(INES).getByRole('button', { name: addLabel(INES.name) }));

    expect(
      await end(INES).findByText(COPY.refused['unblock_them_first'] ?? 'missing'),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The record (the screens §2)
// ---------------------------------------------------------------------------

describe('the record’s foot', () => {
  it('nothing between you: Add friend beside Block, and Add friend asks from the record', async () => {
    friendServer();
    await openRecordOf(INES);

    const foot = within(screen.getByTestId('record-foot'));
    expect(foot.getByRole('button', { name: COPY.record.add })).toBeTruthy();
    expect(foot.getByRole('button', { name: blockRowLabel(INES.name) })).toBeTruthy();
    expect(foot.getByText(BLOCKS_COPY.row.block)).toBeTruthy();

    fireEvent.press(foot.getByRole('button', { name: COPY.record.add }));

    await waitFor(() => expect(asked()).toHaveLength(1));
    expect(asked()[0]).toEqual({
      player_id: INES.id,
      made_from: 'RECORD',
      group_id: CREW.id,
      sport: 'PADEL',
    });
    // The record re-read, and its foot is the server's next answer.
    expect(await screen.findByRole('button', { name: COPY.record.sent })).toBeTruthy();
    expect(transport.requestsTo('GET', recordPath(INES)).length).toBe(2);
    expect(screen.getByRole('button', { name: blockRowLabel(INES.name) })).toBeTruthy();
  });

  it('you asked: Request sent ▾ asks before cancelling, and Keep changes nothing', async () => {
    const server = friendServer();
    await openRecordOf(MICHAL);

    fireEvent.press(await screen.findByRole('button', { name: COPY.record.sent }));
    expect(await screen.findByRole('header', { name: cancelTitle(MICHAL.name) })).toBeTruthy();
    expect(screen.getByText(COPY.record.cancel.body)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.record.keep }));
    await waitFor(() =>
      expect(screen.queryByRole('header', { name: cancelTitle(MICHAL.name) })).toBeNull(),
    );
    expect(transport.requestsTo('DELETE', cancelPath(MICHAL))).toHaveLength(0);

    fireEvent.press(screen.getByRole('button', { name: COPY.record.sent }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.record.cancel.act }));

    await waitFor(() => expect(transport.requestsTo('DELETE', cancelPath(MICHAL))).toHaveLength(1));
    expect(await screen.findByRole('button', { name: COPY.record.add })).toBeTruthy();
    expect(screen.queryByRole('header', { name: cancelTitle(MICHAL.name) })).toBeNull();
    expect(server.relation(MICHAL)).toBe('NONE');
  });

  it('they asked: Accept, coral, makes you friends', async () => {
    friendServer();
    await openRecordOf(ZOFIA);

    const foot = within(screen.getByTestId('record-foot'));
    fireEvent.press(foot.getByRole('button', { name: COPY.record.accept }));

    await waitFor(() => expect(transport.requestsTo('POST', acceptPath(ZOFIA))).toHaveLength(1));
    expect(await screen.findByRole('button', { name: COPY.record.friend })).toBeTruthy();
    expect(screen.getByRole('button', { name: blockRowLabel(ZOFIA.name) })).toBeTruthy();
  });

  it('friends: Friend ✓ ▾ asks before removing, and removing tells nobody', async () => {
    const server = friendServer();
    await openRecordOf(MAGDA);

    fireEvent.press(await screen.findByRole('button', { name: COPY.record.friend }));
    expect(await screen.findByRole('header', { name: removeTitle(MAGDA.name) })).toBeTruthy();
    expect(screen.getByText(COPY.record.remove.body)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.record.remove.act }));

    await waitFor(() => expect(transport.requestsTo('DELETE', removePath(MAGDA))).toHaveLength(1));
    expect(await screen.findByRole('button', { name: COPY.record.add })).toBeTruthy();
    expect(server.relation(MAGDA)).toBe('NONE');
  });

  it('your own: neither button', async () => {
    friendServer();
    await openMembers();

    fireEvent.press(screen.getByTestId(`member-${GATE_USER.id}`));

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
    expect(screen.queryByTestId('record-foot')).toBeNull();
    expect(screen.queryByRole('button', { name: COPY.record.add })).toBeNull();
    expect(screen.queryByRole('button', { name: /^Block / })).toBeNull();
  });

  // The mechanics §3.2: a face on a game of a group asks from that group.
  it('opened from a deck tile, asks naming the deck’s group', async () => {
    friendServer();
    stubGroupDeck(
      transport,
      CREW.id,
      groupDeck({
        cards: [
          deckCard({
            sides: {
              yours: [
                youTile(),
                ANIA({ player_id: INES.id, nickname: INES.name, level: INES.level }),
              ],
              theirs: [KAROL(), EWA()],
            },
          }),
        ],
      }),
    );
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    fireEvent.press(await screen.findByLabelText(`${INES.name}, level 3,40`));
    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();

    fireEvent.press(await screen.findByRole('button', { name: COPY.record.add }));

    await waitFor(() => expect(asked()).toHaveLength(1));
    expect(asked()[0]).toEqual({
      player_id: INES.id,
      made_from: 'RECORD',
      group_id: CREW.id,
      sport: 'PADEL',
    });
  });

  it('closed, re-reads Members, whose row says what was pressed on it', async () => {
    friendServer();
    await openRecordOf(INES);

    fireEvent.press(
      within(screen.getByTestId('record-foot')).getByRole('button', {
        name: COPY.record.add,
      }),
    );
    expect(await screen.findByRole('button', { name: COPY.record.sent })).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: /^Close/ }));

    expect(await end(INES).findByText(COPY.members.sent)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// FRIEND REQUESTS in Needs your answer (#816; the screens §6.2; home refactor 2)
// ---------------------------------------------------------------------------

/** The width the rail hands a request's tile — read off the tile itself, which holds its `top`. */
function tileWidth(who: Person): unknown {
  let node = screen.getByTestId(`friend-request-${who.id}`).parent;
  while (node !== null && StyleSheet.flatten(node.props.style)?.width === undefined) {
    node = node.parent;
  }
  return node === null ? undefined : StyleSheet.flatten(node.props.style)?.width;
}

const content = () => Dimensions.get('window').width - 2 * theme.size.gutter;

/** A request waiting on Tomek, as Home's read serves it — found by `found`, in no group. */
function request(
  who: Person,
  found: Partial<Wire['HomeFriendRequestSchema']> = {},
): Wire['HomeFriendRequestSchema'] {
  return {
    player_id: who.id,
    nickname: who.name,
    photo_id: null,
    photo_url: null,
    asked_at: '2026-10-01T07:00:00Z',
    by_link: false,
    from_ranking: false,
    from_new_players: false,
    from_same_level: false,
    from_same_vibe: false,
    group: null,
    sport: 'PADEL',
    level: who.level,
    player_score: who.score,
    reliability_band: 'VERY_HIGH',
    percent_even: null,
    in_common: null,
    ...found,
  };
}

describe('FRIEND REQUESTS in Needs your answer', () => {
  it('waits behind the envelope, and is no longer on Home', async () => {
    friendServer();
    await launchSignedIn();

    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(screen.queryByTestId('friend-requests')).toBeNull();
    expect(screen.queryByText(wantsToBeYourFriend(ZOFIA.name))).toBeNull();

    await openNeedsYourAnswer();

    expect(screen.getByRole('header', { name: requestsHeading(1) })).toBeTruthy();
    expect(screen.getByTestId(`friend-request-${ZOFIA.id}`)).toBeTruthy();
  });

  it('says who asks in two lines at most, with their face and chip, and no where-line', async () => {
    friendServer();
    await launchSignedIn();
    await openNeedsYourAnswer();

    const tile = within(screen.getByTestId(`friend-request-${ZOFIA.id}`));
    expect(tile.getByRole('button', { name: ZOFIA.name })).toBeTruthy();
    expect(tile.getByText(wantsToBeYourFriend(ZOFIA.name)).props.numberOfLines).toBe(2);
    expect(tile.getByText('95')).toBeTruthy();
    // The group, the sport and the Level they were sent from are no longer drawn (ADR-0205 §1).
    expect(screen.queryByText(/With you in/)).toBeNull();
    expect(screen.queryByText(/Padel 2,69/)).toBeNull();
    expect(screen.getByRole('button', { name: notNowLabel(ZOFIA.name) })).toBeTruthy();
    expect(screen.getByRole('button', { name: acceptLabel(ZOFIA.name) })).toBeTruthy();
  });

  it('counts two on a wider rail, the next tile peeking, and says no found-by line', async () => {
    friendServer();
    stubHome(transport, {
      friend_requests: [
        request(ZOFIA, { by_link: true, sport: null, level: null }),
        request(INES, { from_ranking: true }),
      ],
    });
    await launchSignedIn();
    await openNeedsYourAnswer();

    expect(screen.getByRole('header', { name: requestsHeading(2) })).toBeTruthy();
    expect(tileWidth(ZOFIA)).toBeCloseTo(content() * theme.size.requestCardRatio);
    expect(tileWidth(INES)).toBeCloseTo(content() * theme.size.requestCardRatio);
    // Neither where they were found nor the sport they were asked from (ADR-0205 §1).
    expect(screen.queryByText('Invited you to Raketa')).toBeNull();
    expect(screen.queryByText('Found you in the padel ranking')).toBeNull();
    expect(screen.queryByText(/Padel 3,40/)).toBeNull();
  });

  it('draws a lone request at the content width — there is nothing to peek at', async () => {
    friendServer();
    await launchSignedIn();
    await openNeedsYourAnswer();

    expect(tileWidth(ZOFIA)).toBe(content());
  });

  it('Not now sets one aside: its tile leaves, the count drops, and the sheet stays', async () => {
    friendServer({ [ZOFIA.id]: 'ASKED_YOU', [KUBA.id]: 'ASKED_YOU' });
    stubNotices(transport, []);
    await launchSignedIn();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
    const bellBefore = bellReads();
    await openNeedsYourAnswer();
    expect(screen.getByRole('header', { name: requestsHeading(2) })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: notNowLabel(ZOFIA.name) }));

    await waitFor(() => expect(transport.requestsTo('POST', setAsidePath(ZOFIA))).toHaveLength(1));
    expect(await screen.findByRole('header', { name: requestsHeading(1) })).toBeTruthy();
    expect(screen.queryByTestId(`friend-request-${ZOFIA.id}`)).toBeNull();
    expect(screen.getByTestId(`friend-request-${KUBA.id}`)).toBeTruthy();
    expect(sheetTitle()).not.toBeNull();
    // Not now is not no: nothing is accepted.
    expect(transport.requestsTo('POST', acceptPath(ZOFIA))).toHaveLength(0);
    // The server took the request's row off the bell, and the bell reads again (the mechanics §12).
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
  });

  it('Accept on the last makes you friends, closes the sheet, and the envelope goes', async () => {
    const server = friendServer();
    stubNotices(transport, []);
    await launchSignedIn();
    await waitFor(() => expect(bellReads()).toBeGreaterThan(0));
    const bellBefore = bellReads();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: acceptLabel(ZOFIA.name) }));

    await waitFor(() => expect(transport.requestsTo('POST', acceptPath(ZOFIA))).toHaveLength(1));
    await waitFor(() => expect(sheetTitle()).toBeNull());
    expect(envelope()).toBeNull();
    expect(screen.queryByTestId('friend-requests')).toBeNull();
    expect(server.relation(ZOFIA)).toBe('FRIEND');
    await waitFor(() => expect(bellReads()).toBeGreaterThan(bellBefore));
  });

  it('is not there while no request waits — no envelope, no section', async () => {
    friendServer({ [ZOFIA.id]: 'NONE' });
    await launchSignedIn();

    await waitFor(() => expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(0));
    expect(await screen.findByRole('header', { name: /^Your games/ })).toBeTruthy();
    expect(envelope()).toBeNull();
    expect(screen.queryByTestId('friend-requests')).toBeNull();
  });

  it('shows a request that arrives while the sheet is open', async () => {
    const server = friendServer();
    await launchSignedIn();
    await openNeedsYourAnswer();
    expect(screen.queryByTestId(`friend-request-${INES.id}`)).toBeNull();

    // Inés asks while it is open, and Home reads again — a push, the app coming back, a pull.
    server.asks(INES);
    await act(() => queryClient.invalidateQueries({ queryKey: proposalKeys.home() }));

    expect(await screen.findByTestId(`friend-request-${INES.id}`)).toBeTruthy();
    expect(screen.getByRole('header', { name: requestsHeading(2) })).toBeTruthy();
  });

  it('opens their record over the sheet from the face, and the sheet is there when it closes', async () => {
    friendServer();
    await launchSignedIn();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: ZOFIA.name }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    // Her record's own answer, in its foot: she asked, so it offers Accept.
    const foot = within(await screen.findByTestId('record-foot'));
    expect(foot.getByRole('button', { name: COPY.record.accept })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: recordCloseLabel(false) }));

    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    expect(sheetTitle()).not.toBeNull();
    expect(screen.getByTestId(`friend-request-${ZOFIA.id}`)).toBeTruthy();
  });

  it('closes with the record when the last request was accepted from it', async () => {
    friendServer();
    await launchSignedIn();
    await openNeedsYourAnswer();
    fireEvent.press(screen.getByRole('button', { name: ZOFIA.name }));
    // The record's own Accept, in its foot — the tile's beside it reads Accept too.
    const foot = within(await screen.findByTestId('record-foot'));
    fireEvent.press(foot.getByRole('button', { name: COPY.record.accept }));
    await waitFor(() => expect(transport.requestsTo('POST', acceptPath(ZOFIA))).toHaveLength(1));
    // The record is still being read, and the sheet stays beneath it until it closes.
    expect(await screen.findByRole('button', { name: COPY.record.friend })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: recordCloseLabel(false) }));

    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    expect(sheetTitle()).toBeNull();
    expect(envelope()).toBeNull();
  });
});
