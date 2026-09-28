/**
 * **Join a group, walked** — play mocks 23–37 through the real routes, with the socket and the
 * clipboard faked ([#512](https://github.com/Raketa02/Raketa/issues/512), PRD #500 stories 29–44).
 *
 * One field, a Paste chip that turns into ✕ while typing, and an answer on every keystroke: club
 * cards that are context rather than a choice, with each group's row and what the reader can do
 * about it, and three ways of saying there is nothing.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  launchSignedIn,
  resetClipboard,
  stubClipboard,
  stubGate,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, type FakeClipboard } from '@/test-support/platform';
import {
  installTransport,
  json,
  neverResponds,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { clubCardTestId } from './ClubResultCard';
import { GROUPS_COPY, noMatchFor } from './groupsPresentation';

const COPY = GROUPS_COPY.joinGroup;

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

const O3_CLUB: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000001',
  kind: 'PLAYER',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  sports: ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'],
  member_count: 11,
  join_policy: 'PEOPLE_I_APPROVE',
  owner_name: 'Coach Andrzej',
  administrator_name: null,
  is_administrator: false,
  relation: 'NONE',
};

const OPEN_PLAY: Wire['GroupAtClubSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000002',
  kind: 'PLAYER',
  name: 'Ogrody open play',
  monogram: { letters: 'Oo', colour: 0 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 7,
  join_policy: 'ANYONE',
  owner_name: 'Zofia Wiśniewska',
  administrator_name: null,
  is_administrator: false,
  relation: 'NONE',
};

const OGRODY: Wire['ClubCardSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000003',
  name: 'Ogrody 33',
  district: 'Grzegórzki',
  distance_km: 2.4,
  sports: ['TENNIS', 'PADEL'],
  groups: [O3_CLUB, OPEN_PLAY],
};

const ATLANTIC: Wire['ClubCardSchema'] = {
  id: 'c0000000-0000-4000-8000-000000000004',
  name: 'Atlantic Sports',
  district: 'Stare Miasto',
  distance_km: 1.6,
  sports: ['SQUASH', 'BADMINTON'],
  groups: [],
};

const LINK = 'https://raketa.app/join/K7PQ2MXA';
const DEAD_LINK = 'https://raketa.app/join/ZZZZZZZZ';

const JOIN_SEARCH = '/api/v1/join-search';

let transport: Transport;
let clipboard: FakeClipboard;

function queryOf(request: RecordedRequest) {
  const params = new URLSearchParams(request.path.split('?')[1] ?? '');
  return { q: params.get('q') ?? '', page: Number(params.get('page') ?? '1') };
}

const asked = () => transport.requestsTo('GET', JOIN_SEARCH).map((request) => queryOf(request).q);

/** Join search, answering each text from a table; anything else is text that matched nothing. */
function stubJoinSearch(answers: Readonly<Record<string, Wire['JoinSearchResponse']>>) {
  transport.on('GET', JOIN_SEARCH, (request) =>
    json<Wire['JoinSearchResponse']>(
      answers[queryOf(request).q] ?? { clubs: [], next_page: null, read_as: 'TEXT' },
    ),
  );
}

function text(clubs: readonly Wire['ClubCardSchema'][]): Wire['JoinSearchResponse'] {
  return { clubs: [...clubs], next_page: null, read_as: 'TEXT' };
}

beforeEach(() => {
  transport = installTransport();
  clipboard = fakeClipboard();
  stubClipboard(clipboard);
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubJoinSearch({
    o: text([ATLANTIC, OGRODY]),
    og: text([OGRODY]),
    ogrody: text([OGRODY]),
    'ogrody open play': text([{ ...OGRODY, groups: [OPEN_PLAY] }]),
    [LINK]: { clubs: [{ ...OGRODY, groups: [O3_CLUB] }], next_page: null, read_as: 'LINK' },
    [DEAD_LINK]: { clubs: [], next_page: null, read_as: 'LINK' },
  });
});

afterEach(async () => {
  transport.restore();
  resetClipboard();
  queryClient.clear();
  useToastQueue.getState().clear();
  resetSessionStatus();
  await clearStoredTokens();
});

async function openJoin() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.list.joinLabel }));
  await waitFor(() => expect(screen).toHavePathname('/play/join'));
  await screen.findByRole('header', { name: COPY.title });
}

const field = () => screen.getByLabelText(COPY.field);
const type = (value: string) => fireEvent.changeText(field(), value);
/** A club's card, once its header has been drawn — the header is the card's spoken name. */
async function clubCard(club: Wire['ClubCardSchema']) {
  await screen.findByLabelText(new RegExp(`^${club.name},`));
  return screen.getByTestId(clubCardTestId(club.id));
}

describe('opening Join a group', () => {
  it('is a back arrow, the title and one field with a Paste chip — nothing else', async () => {
    await openJoin();

    expect(field().props.placeholder).toBe(COPY.field);
    expect(screen.getByRole('button', { name: COPY.pasteLabel })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.back })).toBeTruthy();
    expect(screen.queryByRole('button', { name: COPY.clearLabel })).toBeNull();
    expect(asked()).toEqual([]);
  });
});

describe('the field', () => {
  it('asks again on every keystroke', async () => {
    await openJoin();

    type('o');
    await clubCard(ATLANTIC);
    type('og');
    await waitFor(() => expect(screen.queryByText('Atlantic Sports')).toBeNull());

    expect(asked()).toEqual(['o', 'og']);
  });

  it('turns Paste into ✕ while typing, and ✕ clears the text and the results', async () => {
    await openJoin();
    type('o');
    await clubCard(OGRODY);
    expect(screen.queryByRole('button', { name: COPY.pasteLabel })).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: COPY.clearLabel }));

    expect(field().props.value).toBe('');
    expect(screen.queryByText('Ogrody 33')).toBeNull();
    expect(screen.getByRole('button', { name: COPY.pasteLabel })).toBeTruthy();
  });

  // Story 31: cleared means cleared — the next letter never brings the old answer back.
  it('does not bring the cleared answer back while the next text is being asked', async () => {
    await openJoin();
    type('o');
    await clubCard(OGRODY);
    fireEvent.press(screen.getByRole('button', { name: COPY.clearLabel }));

    transport.on('GET', JOIN_SEARCH, neverResponds());
    type('b');

    await waitFor(() => expect(asked()).toEqual(['o', 'b']));
    expect(screen.queryByText('Ogrody 33')).toBeNull();
    expect(screen.queryByText('Atlantic Sports')).toBeNull();
  });

  it('pastes a link from the clipboard and finds exactly its group', async () => {
    clipboard.text = LINK;
    await openJoin();

    fireEvent.press(screen.getByRole('button', { name: COPY.pasteLabel }));

    await waitFor(() => expect(field().props.value).toBe(LINK));
    const card = await clubCard(OGRODY);
    expect(within(card).getByText('Ogrody 33 Club')).toBeTruthy();
    expect(within(card).queryByText('Ogrody open play')).toBeNull();
    expect(asked()).toEqual([LINK]);
  });

  it('pastes nothing when the clipboard is empty', async () => {
    await openJoin();

    fireEvent.press(screen.getByRole('button', { name: COPY.pasteLabel }));

    await waitFor(() => expect(screen.getByRole('button', { name: COPY.pasteLabel })).toBeTruthy());
    expect(field().props.value ?? '').toBe('');
    expect(asked()).toEqual([]);
  });
});

describe('the answers', () => {
  it('draws each club with its district, distance and sports, and is not a button', async () => {
    await openJoin();

    type('o');

    const card = await clubCard(OGRODY);
    expect(within(card).getByText('Grzegórzki · 2,4 km · Tennis, Padel')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^Ogrody 33,/ })).toBeNull();
  });

  it('says a club with no groups has none yet', async () => {
    await openJoin();

    type('o');

    const card = await clubCard(ATLANTIC);
    expect(within(card).getByText(COPY.noGroupsHere)).toBeTruthy();
  });

  it('draws each group with its count, who approves, and what the reader can do', async () => {
    await openJoin();

    type('ogrody');

    expect(await screen.findByText('11 members · Coach Andrzej approves joins')).toBeTruthy();
    expect(screen.getByText('7 members · anyone can join')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Ask to join Ogrody 33 Club' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Join Ogrody open play' })).toBeTruthy();
    // The dots have no words of their own; the row speaks the sports by name.
    expect(
      screen.getByLabelText(
        'Ogrody 33 Club, 11 members · Coach Andrzej approves joins, plays Padel, Tennis, Squash, Badminton',
      ),
    ).toBeTruthy();
  });

  it('shows you’re in and requested · waiting where they apply', async () => {
    stubJoinSearch({
      ogrody: text([
        {
          ...OGRODY,
          groups: [
            { ...O3_CLUB, relation: 'REQUESTED' },
            { ...OPEN_PLAY, relation: 'MEMBER' },
          ],
        },
      ]),
    });
    await openJoin();

    type('ogrody');

    expect(await screen.findByText(GROUPS_COPY.action.requested)).toBeTruthy();
    expect(screen.getByText(GROUPS_COPY.action.in)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /join/i })).toBeNull();
  });

  // Story 28: nothing pretends to know where a player with no Location area is.
  it('leaves the distance out when the reader’s location is unknown', async () => {
    stubJoinSearch({ o: text([{ ...ATLANTIC, distance_km: null }]) });
    await openJoin();

    type('o');

    const card = await clubCard(ATLANTIC);
    expect(within(card).getByText('Stare Miasto · Squash, Badminton')).toBeTruthy();
  });

  it('says there is nothing at a link that leads nowhere', async () => {
    await openJoin();

    type(DEAD_LINK);

    expect(await screen.findByText(COPY.nothingAtLink)).toBeTruthy();
  });

  it('says there is no match for text that found nothing', async () => {
    await openJoin();

    type('co');

    expect(await screen.findByText(noMatchFor('co'))).toBeTruthy();
  });
});

describe('joining', () => {
  it('puts the reader into an Anyone group at once, and the group onto their list', async () => {
    transport.on('POST', `/api/v1/groups/${OPEN_PLAY.id}/membership`, () =>
      json<Wire['GroupAtClubSchema']>({ ...OPEN_PLAY, relation: 'MEMBER', member_count: 8 }),
    );
    await openJoin();
    type('ogrody open play');

    stubMyGroups(transport, [
      {
        id: OPEN_PLAY.id,
        kind: 'PLAYER',
        name: OPEN_PLAY.name,
        monogram: OPEN_PLAY.monogram,
        sports: OPEN_PLAY.sports,
        member_count: 8,
        home_club: { id: OGRODY.id, name: OGRODY.name },
      },
    ]);
    fireEvent.press(await screen.findByRole('button', { name: 'Join Ogrody open play' }));

    expect(await screen.findByText(GROUPS_COPY.action.in)).toBeTruthy();
    expect(screen.getByText('8 members · anyone can join')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(
      await screen.findByRole('button', { name: /^Ogrody open play, 8 members/ }),
    ).toBeTruthy();
  });

  it('turns Ask to join into requested · waiting', async () => {
    transport.on('POST', `/api/v1/groups/${O3_CLUB.id}/membership`, () =>
      json<Wire['GroupAtClubSchema']>({ ...O3_CLUB, relation: 'REQUESTED' }),
    );
    await openJoin();
    type(LINK);

    fireEvent.press(await screen.findByRole('button', { name: 'Ask to join Ogrody 33 Club' }));

    expect(await screen.findByText(GROUPS_COPY.action.requested)).toBeTruthy();
  });

  it('says so when a join fails, and leaves the button to try again', async () => {
    transport.on('POST', `/api/v1/groups/${OPEN_PLAY.id}/membership`, () =>
      Promise.reject(new TypeError('Network request failed')),
    );
    await openJoin();
    type('ogrody open play');

    fireEvent.press(await screen.findByRole('button', { name: 'Join Ogrody open play' }));

    await waitFor(() =>
      expect(useToastQueue.getState().queue.map((toast) => toast.tone)).toEqual(['bad']),
    );
    expect(await screen.findByRole('button', { name: 'Join Ogrody open play' })).toBeTruthy();
  });
});

describe('a relation that changed on another phone', () => {
  const waiting = { ...O3_CLUB, relation: 'REQUESTED' as const };
  const member = { ...O3_CLUB, relation: 'MEMBER' as const };
  const answers = (row: Wire['GroupAtClubSchema']) => ({
    og: text([{ ...OGRODY, groups: [row] }]),
    ogr: text([ATLANTIC, { ...OGRODY, groups: [row] }]),
  });

  // #529 D6: approved on the Owner's phone, the row flipped between requested · waiting and you're
  // in as the reader typed — every text drew the answer it had been given before, then asked again.
  it('is never drawn from an answer read before it changed', async () => {
    stubJoinSearch(answers(waiting));
    await openJoin();
    type('og');
    expect(await screen.findByText(GROUPS_COPY.action.requested)).toBeTruthy();
    type('ogr');
    await clubCard(ATLANTIC);

    // The Owner lets them in.
    stubJoinSearch(answers(member));
    type('og');
    expect(await screen.findByText(GROUPS_COPY.action.in)).toBeTruthy();
    type('ogr');

    expect(screen.queryByText(GROUPS_COPY.action.requested)).toBeNull();
    await clubCard(ATLANTIC);
    expect(screen.queryByText(GROUPS_COPY.action.requested)).toBeNull();
    expect(screen.getByText(GROUPS_COPY.action.in)).toBeTruthy();
  });
});

describe('going back to the Groups list', () => {
  const MINE: Wire['MyGroupSchema'] = {
    id: O3_CLUB.id,
    kind: 'PLAYER',
    name: O3_CLUB.name,
    monogram: O3_CLUB.monogram,
    sports: O3_CLUB.sports,
    member_count: 12,
    home_club: { id: OGRODY.id, name: OGRODY.name },
  };

  // #529: asked from here, let in by the Owner while still here — and back on Groups the list was
  // the one read before, without the group, until a switch to Explore and back remounted it.
  it('re-reads it, so a group the reader was let into meanwhile is on it', async () => {
    stubMyGroups(transport, []);
    await openJoin();

    // The Owner approves on their phone.
    stubMyGroups(transport, [MINE]);
    fireEvent.press(screen.getByRole('button', { name: COPY.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));

    expect(await screen.findByRole('button', { name: /^Ogrody 33 Club,/ })).toBeTruthy();
  });
});
