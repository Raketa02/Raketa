/**
 * **Block and Unblock, walked through the real route tree**
 * ([#587](https://github.com/Raketa02/Raketa/issues/587), PRD #571;
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
 *
 * The record a deck tile opens ends with *Block* and the person's name; the confirm sheet says what
 * a block does and offers *Block* and *Cancel*; once blocked, the record no longer opens — a blocked
 * pair's record is refused both ways since [#773](https://github.com/Raketa02/Raketa/issues/773)
 * (ADR-0203), so the record's re-read is refused. **You › Account › Blocked
 * players** lists everyone the reader blocked, each with *Unblock*, which is the way back. Your own
 * record ends in neither.
 *
 * **The blocks routes are answered by a small fake of the server** (`blockServer`): a block or an
 * unblock changes what the next read of the record and of the list says, as it would — so the row
 * that flips after a press is the record re-read, never this client guessing. The group's deck and
 * Fill in are observed while the record is open over them, so a refresh of them is a re-read counted
 * at the socket; the list is not observed there, so its refresh is the cache entry's flag
 * (`pin-invalidation`'s rule).
 */

import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import {
  FULL_RECORD,
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  OWN_RECORD_TITLE,
  RECORD_TITLE,
} from '@/features/player_record/types';
import { proposalKeys } from '@/features/proposals/types';
import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { POSTER_LABEL, doorRowLabel } from '@/shared/ui';
import {
  ANIA,
  DECK_READ_AT,
  EWA,
  KUBA,
  deckCard,
  deckPath,
  fillInPath,
  groupDeck,
  stubGroupDeck,
  youTile,
} from '@/test-support/groupDeck';
import {
  BLOCKED_PLAYERS_PATH,
  GATE_USER,
  HOME_PATH,
  OWN_RECORD_SERVED,
  SPORTS_SERVED,
  launchSignedIn,
  stubGate,
  stubMyGroups,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { blockKeys } from '../hooks/blockKeys';

import {
  BLOCKS_COPY,
  blockRowLabel,
  blockSheetBody,
  blockSheetTitle,
  blockedCountLine,
  unblockRowLabel,
} from './blocksCopy';

const COPY = BLOCKS_COPY;
/** A face is decoration, hidden from a screen reader — the name beside it is what is spoken. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;
const BLOCKS_PATH = BLOCKED_PLAYERS_PATH;

interface Person {
  readonly id: string;
  readonly name: string;
  readonly photoUrl?: string;
}

/** On the deck's card — and so the face whose record is opened. */
const KUBA_PERSON: Person = { id: KUBA().player_id, name: 'kuba.w' };
/** Not on any card: reachable only from the list. */
const ZOFIA: Person = {
  id: 'e0000000-0000-4000-8000-000000000031',
  name: 'Zofia Bąk',
  photoUrl: 'https://photos.example/zofia.jpg',
};
const PEOPLE = [KUBA_PERSON, ZOFIA];

const recordPath = (who: Person) => `/api/v1/players/${who.id}/record`;
const unblockPath = (who: Person) => `${BLOCKS_PATH}/${who.id}`;

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
  rated_by_sport: [
    {
      sport: 'PADEL',
      rated_count: 5,
      first_rated: [{ player_id: GATE_USER.id, nickname: 'ada' }],
    },
  ],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

/** Somebody's record as the route answers it, to a reader with no block between them. */
function recordOf(who: Person): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    relation: 'NONE',
    can_add_friend: true,
    nickname: who.name,
    area_code: 'A+050612+0019938',
    social_tags: [],
    sports: [{ sport: 'PADEL', level: 2.8, band: 'Established' }],
    reliability: servedReliability({ player_score: 96, is_new: false }),
  };
}

interface BlockServer {
  /** Whose blocks stand, newest first, as `GET /blocks` lists them. */
  readonly blocked: () => readonly string[];
}

/**
 * **The blocks routes, faked** — the rules the routes document and nothing more: a block is
 * idempotent and answers 204, an unblock lifts the reader's own block and never 404s, the list is
 * newest first, and a record is refused with `record_unavailable` while a block stands between the
 * two (#773), and with `block_state_unavailable` when `blocksUnreadable`, as the route refuses it
 * when it cannot read them.
 */
function blockServer(
  initially: readonly Person[] = [],
  { blocksUnreadable = false }: { readonly blocksUnreadable?: boolean } = {},
): BlockServer {
  const standing = initially.map((who) => who.id);
  const isBlocked = (who: Person) => standing.includes(who.id);

  transport.on('POST', BLOCKS_PATH, (request) => {
    const { player_id: playerId } = request.body as Wire['BlockPlayerRequest'];
    if (!standing.includes(playerId)) standing.unshift(playerId);
    return noContent();
  });
  transport.on('GET', BLOCKS_PATH, () =>
    json<Wire['BlockedPlayersResponse']>({
      players: standing.map((id) => {
        const who = PEOPLE.find((person) => person.id === id)!;
        return {
          player_id: who.id,
          nickname: who.name,
          ...(who.photoUrl === undefined
            ? {}
            : { photo_id: 'f0000000-0000-4000-8000-000000000001', photo_url: who.photoUrl }),
          blocked_at: '2026-10-06T09:00:00Z',
        };
      }),
    }),
  );
  for (const who of PEOPLE) {
    transport.on('DELETE', unblockPath(who), () => {
      const at = standing.indexOf(who.id);
      if (at >= 0) standing.splice(at, 1);
      return noContent();
    });
    transport.on('GET', recordPath(who), () => {
      if (blocksUnreadable) return errorResponse(503, 'block_state_unavailable');
      if (isBlocked(who)) return errorResponse(404, 'record_unavailable');
      return json(recordOf(who));
    });
  }

  return { blocked: () => [...standing] };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [rating('PADEL', 2.71)], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubOwnRecord(transport, OWN_RECORD_SERVED);
  transport.on('GET', '/api/v1/sports', () => json(SPORTS_SERVED));
});

afterEach(async () => {
  onlineManager.setOnline(true);
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** The crew's Games tab, dealing one card Kuba is on. */
async function openTheDeck() {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(
    transport,
    CREW.id,
    groupDeck({
      cards: [deckCard({ sides: { yours: [youTile(), KUBA()], theirs: [ANIA(), EWA()] } })],
    }),
  );
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
}

/** Kuba's record, opened from his tile on the top card. */
async function openKubasRecord() {
  await openTheDeck();
  fireEvent.press(await screen.findByLabelText(`${KUBA_PERSON.name}, level 2,80`));
  expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
}

/** The You tab, its *Blocked players* row drawn with this line. */
async function openYou(line: string) {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  return screen.findByLabelText(doorRowLabel(COPY.blockedPlayers.title, line));
}

/** *Blocked players*, from its row on the You tab. */
async function openBlockedPlayers(line: string) {
  fireEvent.press(await openYou(line));
  await waitFor(() => expect(screen).toHavePathname('/you/blocked-players'));
  expect(await screen.findByRole('header', { name: COPY.blockedPlayers.title })).toBeTruthy();
}

const deckReads = () => transport.requestsTo('GET', deckPath(CREW.id)).length;
const fillInReads = () => transport.requestsTo('GET', fillInPath(CREW.id)).length;
const recordReads = (who: Person) => transport.requestsTo('GET', recordPath(who)).length;
const blockRow = (who: Person) => screen.queryByRole('button', { name: blockRowLabel(who.name) });
const unblockRow = (who: Person) =>
  screen.queryByRole('button', { name: unblockRowLabel(who.name) });
const sheetTitle = (who: Person) =>
  screen.queryByRole('header', { name: blockSheetTitle(who.name) });

/** An entry nothing on screen observes, seeded so nothing collects it before it is asked about. */
function seed(queryKey: readonly unknown[]) {
  queryClient.getQueryCache().build(queryClient, { queryKey, gcTime: Infinity });
  queryClient.setQueryData(queryKey, []);
}

/**
 * What a block's withdrawal moves (ADR-0193 §4) and nothing on the deck observes: the live yeses,
 * a game still filling in detail, a booking in detail. Home is held by the shell, so it is counted.
 */
const WITHDRAWAL_READS = [
  proposalKeys.liveYeses(),
  proposalKeys.proposal('f0000000-0000-4000-8000-000000000041'),
  proposalKeys.booking('e0000000-0000-4000-8000-000000000041'),
] as const;

/** The list's entry, and the withdrawal's reads, seeded before a press. */
function seedTheList() {
  seed(blockKeys.list());
  for (const key of WITHDRAWAL_READS) seed(key);
}

const invalidated = (queryKey: readonly unknown[]) =>
  queryClient.getQueryState(queryKey)?.isInvalidated;
const homeReads = () => transport.requestsTo('GET', HOME_PATH).length;

describe('Block, on the record', () => {
  it('ends the record with Block and the name, and blocks through the confirm sheet', async () => {
    const server = blockServer();
    await openKubasRecord();
    seedTheList();

    const row = await screen.findByRole('button', { name: blockRowLabel(KUBA_PERSON.name) });
    const deckBefore = deckReads();
    const fillInBefore = fillInReads();
    const recordBefore = recordReads(KUBA_PERSON);
    const homeBefore = homeReads();
    fireEvent.press(row);

    // The sheet says what a block does, before it does it.
    expect(
      await screen.findByRole('header', { name: blockSheetTitle(KUBA_PERSON.name) }),
    ).toBeTruthy();
    expect(screen.getByText(blockSheetBody(KUBA_PERSON.name))).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.sheet.cancel })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.sheet.block }));

    // One request, naming the other player and nothing else.
    await waitFor(() => expect(transport.requestsTo('POST', BLOCKS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', BLOCKS_PATH)[0]!.body).toEqual({
      player_id: KUBA_PERSON.id,
    });
    expect(server.blocked()).toEqual([KUBA_PERSON.id]);

    // The sheet goes, and the record is read again — and refused: a blocked pair's record never
    // opens (#773), and the way back is You › Blocked players. The record already drawn stays
    // drawn under a refused re-read; closing it once the block is made is #779's.
    await waitFor(() => expect(sheetTitle(KUBA_PERSON)).toBeNull());
    await waitFor(() => expect(recordReads(KUBA_PERSON)).toBeGreaterThan(recordBefore));
    expect(unblockRow(KUBA_PERSON)).toBeNull();
    // The group's deck and Fill in are read again: the next card already respects the block.
    expect(deckReads()).toBeGreaterThan(deckBefore);
    expect(fillInReads()).toBeGreaterThan(fillInBefore);
    // And the list will be, wherever it is next drawn.
    expect(invalidated(blockKeys.list())).toBe(true);
    // So will what the withdrawal moved — yeses taken back, a waiting game filling again.
    expect(homeReads()).toBeGreaterThan(homeBefore);
    for (const key of WITHDRAWAL_READS) expect(invalidated(key)).toBe(true);
  });

  it('changes nothing on Cancel', async () => {
    const server = blockServer();
    await openKubasRecord();

    fireEvent.press(await screen.findByRole('button', { name: blockRowLabel(KUBA_PERSON.name) }));
    await screen.findByRole('header', { name: blockSheetTitle(KUBA_PERSON.name) });

    fireEvent.press(screen.getByRole('button', { name: COPY.sheet.cancel }));

    await waitFor(() => expect(sheetTitle(KUBA_PERSON)).toBeNull());
    expect(transport.requestsTo('POST', BLOCKS_PATH)).toHaveLength(0);
    expect(server.blocked()).toEqual([]);
    // The record is still open, still offering the block.
    expect(screen.getByText(RECORD_TITLE)).toBeTruthy();
    expect(blockRow(KUBA_PERSON)).toBeTruthy();
  });

  it('waits for the network offline, and closing the sheet takes the block back', async () => {
    const server = blockServer();
    await openKubasRecord();
    fireEvent.press(await screen.findByRole('button', { name: blockRowLabel(KUBA_PERSON.name) }));
    await screen.findByRole('header', { name: blockSheetTitle(KUBA_PERSON.name) });

    act(() => onlineManager.setOnline(false));
    fireEvent.press(screen.getByRole('button', { name: COPY.sheet.block }));

    // Held, and said so where the press was.
    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.sheet.blocking })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.sheet.cancel }));
    await waitFor(() => expect(sheetTitle(KUBA_PERSON)).toBeNull());

    // The connection comes back, and the block that was taken back is not sent.
    await act(async () => {
      onlineManager.setOnline(true);
      await Promise.resolve();
      jest.advanceTimersByTime(1_000);
    });
    expect(transport.requestsTo('POST', BLOCKS_PATH)).toHaveLength(0);
    expect(server.blocked()).toEqual([]);
    expect(blockRow(KUBA_PERSON)).toBeTruthy();
  });

  it('draws no row where the blocks could not be read: the record itself is refused', async () => {
    blockServer([], { blocksUnreadable: true });
    await openKubasRecord();

    // Since #773 the route answers `503` rather than a record with no block state in it, so no row
    // is drawn because no record is.
    await waitFor(() =>
      expect(transport.requestsTo('GET', recordPath(KUBA_PERSON)).length).toBe(1),
    );
    expect(blockRow(KUBA_PERSON)).toBeNull();
    expect(unblockRow(KUBA_PERSON)).toBeNull();
  });

  it('draws no row on your own record', async () => {
    blockServer();
    await openYou(blockedCountLine(0));

    fireEvent.press(
      screen.getByLabelText(doorRowLabel(HOW_OTHERS_SEE_YOU_TITLE, HOW_OTHERS_SEE_YOU_LINE)),
    );

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
    // The record is in — its fold is drawn — and it ends in neither row.
    expect(await screen.findByRole('button', { name: FULL_RECORD })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^(Block|Unblock) / })).toBeNull();
  });
});

describe('Blocked players, under You › Account', () => {
  it('says how many on the row, and lists each with their face, name and Unblock', async () => {
    blockServer([ZOFIA, KUBA_PERSON]);
    await openBlockedPlayers(blockedCountLine(2));

    // The server's order — newest first.
    const rows = await screen.findAllByTestId(/^blocked-/);
    expect(rows.map((row) => row.props.testID)).toEqual([
      `blocked-${ZOFIA.id}`,
      `blocked-${KUBA_PERSON.id}`,
    ]);
    expect(within(rows[0]!).getByText(ZOFIA.name)).toBeTruthy();
    expect(within(rows[1]!).getByText(KUBA_PERSON.name)).toBeTruthy();
    // *Unblock* drawn, and spoken with whose it is.
    expect(within(rows[0]!).getByText(COPY.blockedPlayers.unblock)).toBeTruthy();
    expect(
      within(rows[0]!).getByRole('button', { name: unblockRowLabel(ZOFIA.name) }),
    ).toBeTruthy();
    expect(
      within(rows[1]!).getByRole('button', { name: unblockRowLabel(KUBA_PERSON.name) }),
    ).toBeTruthy();
    // Zofia's photograph; Kuba has none, and his face is his poster.
    expect(within(rows[0]!).queryByLabelText(POSTER_LABEL, HIDDEN_TOO)).toBeNull();
    expect(within(rows[1]!).getByLabelText(POSTER_LABEL, HIDDEN_TOO)).toBeTruthy();
  });

  it('unblocks from the list, and the row on You says so', async () => {
    const server = blockServer([ZOFIA, KUBA_PERSON]);
    await openBlockedPlayers(blockedCountLine(2));
    // The crew's deck and Fill in, unobserved here, and what a withdrawal moved (#775: the record's
    // Unblock is gone since #773, so the list is where an unblock's reads are proven).
    const deck = proposalKeys.deck(CREW.id, 'padel', 'competitive');
    const fillIn = proposalKeys.fillIn(CREW.id, 'padel');
    seed(deck);
    seed(fillIn);
    seedTheList();
    const homeBefore = homeReads();

    fireEvent.press(await screen.findByRole('button', { name: unblockRowLabel(KUBA_PERSON.name) }));

    await waitFor(() =>
      expect(transport.requestsTo('DELETE', unblockPath(KUBA_PERSON))).toHaveLength(1),
    );
    expect(server.blocked()).toEqual([ZOFIA.id]);
    // The next deck and Fill in are read again, and the list; nothing comes back with an unblock,
    // so nothing the withdrawal moved is.
    await waitFor(() => expect(invalidated(deck)).toBe(true));
    expect(invalidated(fillIn)).toBe(true);
    expect(homeReads()).toBe(homeBefore);
    for (const key of WITHDRAWAL_READS) expect(invalidated(key)).toBe(false);
    await waitFor(() => expect(screen.queryByTestId(`blocked-${KUBA_PERSON.id}`)).toBeNull());
    expect(screen.getByTestId(`blocked-${ZOFIA.id}`)).toBeTruthy();

    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(doorRowLabel(COPY.blockedPlayers.title, blockedCountLine(1))),
    ).toBeTruthy();
  });

  it('says plainly that nobody is blocked', async () => {
    blockServer();
    await openBlockedPlayers(blockedCountLine(0));

    expect(await screen.findByText(COPY.blockedPlayers.empty)).toBeTruthy();
    expect(screen.queryAllByTestId(/^blocked-/)).toHaveLength(0);
  });
});
