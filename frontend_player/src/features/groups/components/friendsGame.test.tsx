/**
 * **A game with friends, built on a group's Friends tab** — the picker, the court, the card and
 * *Find a court* ([#757](https://github.com/Raketa02/Raketa/issues/757); the friends screens §4.2,
 * §7; friends 3, 6–11). Sending is #759's.
 *
 * The real route tree, with the socket faked: the friends read answers per sport, highest Level
 * first, as `GET /friends?sport=` does; the card answers the evenest sides — *You + ewa.m* against
 * *magda.p + ania.k* — or the sides a swap sent; and *Find a court* lists five rows, one of each
 * tint and a court at another club where the home club is full. **Every read happens at
 * `DECK_READ_AT`**, Wednesday 30 September 10:00 in Warsaw, so Saturday is *Saturday* and the
 * Saturday after it *Sat 10 Oct*.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { StyleSheet } from 'react-native';

import { FRIENDS_COPY } from '@/features/friends/types';
import { FRIENDS_CARD_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { DECK_READ_AT, deckPath, stubGroupDeck } from '@/test-support/groupDeck';
import {
  FRIENDS_PATH,
  GATE_USER,
  launchSignedIn,
  stubGate,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useFriendsGame } from '../store/friendsGame.store';
import { useGameIntent } from '../store/gameIntent.store';

import { GROUPS_COPY } from './groupsPresentation';

const COPY = GROUPS_COPY;
const CARD = FRIENDS_CARD_COPY;

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.62,
    confidence: 28,
    range: { low: mu - 0.6, high: mu + 0.6 },
    band: { name: 'Established', lower: 2.65, upper: 3.85 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

const ME = GATE_USER.id;

const GROUP: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000021',
  kind: 'PLAYER',
  name: 'Padel po pracy',
  monogram: { letters: 'Pp', colour: 2 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 8,
  home_club: { id: 'c0000000-0000-4000-8000-000000000033', name: 'Ogrody 33' },
};

const PAGE: Wire['GroupResponse'] = {
  ...GROUP,
  link: 'https://raketa.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [
    { sport: 'PADEL', rated_count: 1, first_rated: [{ player_id: ME, nickname: 'tomek.k' }] },
    { sport: 'TENNIS', rated_count: 1, first_rated: [{ player_id: ME, nickname: 'tomek.k' }] },
  ],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

const KAROL = 'f0000000-0000-4000-8000-000000000001';
const ANIA = 'f0000000-0000-4000-8000-000000000002';
const MAGDA = 'f0000000-0000-4000-8000-000000000003';
const EWA = 'f0000000-0000-4000-8000-000000000004';
const ZOFIA = 'f0000000-0000-4000-8000-000000000005';

const NAMES: Readonly<Record<string, string>> = {
  [KAROL]: 'karol.t',
  [ANIA]: 'ania.k',
  [MAGDA]: 'magda.p',
  [EWA]: 'ewa.m',
  [ZOFIA]: 'zofia.b',
};

function friend(
  id: string,
  sport: Wire['Sport'],
  level?: number,
  band = 'Established',
  askedIn: Wire['Sport'][] = [],
): Wire['FriendSchema'] {
  return {
    player_id: id,
    nickname: NAMES[id]!,
    photo_id: null,
    photo_url: null,
    friends_since: '2026-09-01T10:00:00Z',
    sports: level === undefined ? [] : [{ sport, level, band }],
    level_asked_in: askedIn,
  };
}

/** The picker's padel list, as the server orders it: highest Level first, the unrated last. */
const PADEL_FRIENDS = [
  friend(KAROL, 'PADEL', 2.75),
  friend(ANIA, 'PADEL', 2.68),
  friend(MAGDA, 'PADEL', 2.66),
  friend(EWA, 'PADEL', 2.6, 'Developing'),
  friend(ZOFIA, 'PADEL'),
];

const TENNIS_FRIENDS = [friend(EWA, 'TENNIS', 3.1), friend(MAGDA, 'TENNIS', 2.9)];

const HOME = { id: GROUP.home_club!.id, name: 'Ogrody 33' };
const WISLA = { id: 'c0000000-0000-4000-8000-000000000044', name: 'Wisła Park' };
const BONARKA = { id: 'c0000000-0000-4000-8000-000000000055', name: 'Bonarka Arena' };

function row(
  startsAt: string,
  club: { id: string; name: string },
  courtName: string,
  busy: readonly string[],
  overrides: Partial<Wire['FriendsCourtSchema']> = {},
): Wire['FriendsCourtSchema'] {
  return {
    starts_at: startsAt,
    club,
    court_id: `${club.id}-${courtName}`,
    court_name: courtName,
    indoor: true,
    share_grosze: 2500,
    home_club_full: false,
    free_count: 4 - busy.length,
    busy: [...busy],
    ...overrides,
  };
}

/** Saturday 3 October, 10:00 in Warsaw — the card's proposed court. */
const PROPOSED = row('2026-10-03T08:00:00Z', HOME, 'Court 3', []);

/** *Find a court*: tomorrow, two on Saturday — one at another club — Sunday, and a week on. */
const ROWS = [
  row('2026-10-01T17:00:00Z', BONARKA, 'Court 2', []),
  PROPOSED,
  row('2026-10-03T09:00:00Z', WISLA, 'Court 1', [ANIA], { home_club_full: true }),
  row('2026-10-04T13:00:00Z', HOME, 'Court 5', [MAGDA, ANIA]),
  row('2026-10-10T18:00:00Z', BONARKA, 'Court 1', [ME, EWA, ANIA]),
];

const OVERLAP: Wire['DeckOverlapSchema'] = {
  grade: 'SLIM',
  cells: [{ day: 6, range: 'MORNING', shade: 'BRIGHT' }],
  game: { day: 6, range: 'MORNING' },
};

const cardPath = `/api/v1/pools/${GROUP.id}/friends-card`;
const courtsPath = `/api/v1/pools/${GROUP.id}/friends-card/courts`;

function query(request: RecordedRequest): URLSearchParams {
  return new URL(`https://test${request.path}`).searchParams;
}

/**
 * The card: the evenest sides are you and ewa.m against the other two — or, after a swap, the
 * partner sent beside you. A court picked comes back as the card's.
 */
function cardFor(request: RecordedRequest): Wire['FriendsCardResponse'] {
  const asked = query(request);
  const friends = asked.getAll('friend_ids');
  const partner = asked.get('partner_id') ?? (friends.length > 1 ? EWA : undefined);
  const courtId = asked.get('court_id');
  const court = ROWS.find(
    (one) => one.court_id === courtId && one.starts_at === asked.get('starts_at'),
  );
  return {
    pool_id: GROUP.id,
    sport: asked.get('sport') as Wire['Sport'],
    kind: asked.get('kind') as Wire['SearchMode'],
    home_club: HOME,
    sides:
      partner === undefined
        ? { yours: [ME], theirs: friends }
        : { yours: [ME, partner], theirs: friends.filter((one) => one !== partner) },
    forecast: { pct: 87, provisional: false },
    court: court ?? PROPOSED,
    overlap: OVERLAP,
    cut_off: '2026-10-02T08:00:00Z',
  };
}

let transport: Transport;

function stubFriendsIn(
  lists: { padel?: Wire['FriendSchema'][]; tennis?: Wire['FriendSchema'][] } = {},
) {
  transport.on('GET', FRIENDS_PATH, (request) => {
    const sport = query(request).get('sport') as Wire['Sport'] | null;
    const friends =
      sport === 'TENNIS' ? (lists.tennis ?? TENNIS_FRIENDS) : (lists.padel ?? PADEL_FRIENDS);
    return json<Wire['FriendsResponse']>({ sport, friends });
  });
}

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, {
    ratings: [rating('PADEL', 2.71), rating('TENNIS', 3.0)],
    hasPlayerProfile: true,
  });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubMyGroups(transport, [GROUP]);
  transport.on('GET', `/api/v1/groups/${GROUP.id}`, () => json(PAGE));
  stubGroupDeck(transport, GROUP.id);
  stubFriendsIn();
  transport.on('GET', cardPath, (request) => json(cardFor(request)));
  transport.on('GET', courtsPath, () =>
    json<Wire['FriendsCourtsResponse']>({
      pool_id: GROUP.id,
      sport: 'PADEL',
      home_club: HOME,
      courts: ROWS,
    }),
  );
  useGameIntent.setState({ intent: 'competitive' });
  useFriendsGame.setState({ kind: 'competitive', lineUps: {} });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const tab = (name: string, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

/** Land on the group's Friends tab, for the sport the page opens on. */
async function openFriendsTab() {
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Padel po pracy,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP.id}`));
  fireEvent.press(await tab('Friends'));
  expect(await tab('Friends', true)).toBeTruthy();
}

const pickerRow = (id: string) => screen.findByTestId(`pick-${id}`);

/** Open the picker from + Friends, tick these friends in order, and press Done. */
async function seat(...ids: readonly string[]) {
  fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP.id}/friends`));
  for (const id of ids) fireEvent.press(await pickerRow(id));
  fireEvent.press(screen.getByRole('button', { name: FRIENDS_COPY.picker.done }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP.id}`));
}

const cardRequests = () => transport.requestsTo('GET', cardPath);
const lastCardAsked = () => query(cardRequests().at(-1)!);

const seatNamed = (label: string) => screen.findByRole('button', { name: label });

describe('the switch', () => {
  it('sets this game’s kind, and never the Games deck’s switch', async () => {
    await openFriendsTab();

    fireEvent.press(await tab(COPY.friends.forFun, false));

    expect(await tab(COPY.friends.forFun, true)).toBeTruthy();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');
    expect(lastCardAsked().get('kind')).toBe('FOR_FUN');

    // The deck still reads the kind it stood on.
    fireEvent.press(await tab('Games'));
    await waitFor(() => expect(transport.requestsTo('GET', deckPath(GROUP.id)).length).toBe(2));
    expect(
      transport
        .requestsTo('GET', deckPath(GROUP.id))
        .every((one) => one.path.includes('kind=COMPETITIVE')),
    ).toBe(true);
  });

  it('asks the card again for the other kind, and keeps the sides the court shows', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');

    fireEvent.press(await tab(COPY.friends.forFun, false));

    await waitFor(() => expect(lastCardAsked().get('kind')).toBe('FOR_FUN'));
    expect(lastCardAsked().get('partner_id')).toBe(EWA);
    expect(await seatNamed('Your side, your partner, ewa.m, level 2,60')).toBeTruthy();
  });
});

describe('the picker', () => {
  it('opens from an empty seat with no tabs, Done at its foot and + Add friends at its head', async () => {
    await openFriendsTab();

    fireEvent.press((await screen.findAllByRole('button', { name: /, empty$/ }))[0]!);

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP.id}/friends`));
    expect(await screen.findByRole('header', { name: FRIENDS_COPY.page.title })).toBeTruthy();
    expect(screen.getByRole('button', { name: FRIENDS_COPY.page.addLabel })).toBeTruthy();
    expect(screen.getByRole('button', { name: FRIENDS_COPY.picker.done })).toBeTruthy();
    expect(screen.queryByRole('button', { name: FRIENDS_COPY.page.tabs.ASKED_YOU })).toBeNull();
  });

  it('lists every friend in the sport, highest Level first, each with a circle', async () => {
    await openFriendsTab();
    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));

    await pickerRow(KAROL);
    expect(screen.getAllByRole('checkbox').map((one) => one.props.accessibilityLabel)).toEqual([
      'karol.t, 2,75 · established',
      'ania.k, 2,68 · established',
      'magda.p, 2,66 · established',
      'ewa.m, 2,60 · developing',
      'zofia.b, No padel level yet',
    ]);
    expect(transport.requestsTo('GET', FRIENDS_PATH).at(-1)!.path).toContain('sport=PADEL');
  });

  it('greys a friend with no Level in the sport', async () => {
    await openFriendsTab();
    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));

    expect(
      await screen.findByRole('checkbox', { name: /^zofia\.b/, disabled: true, checked: false }),
    ).toBeTruthy();
    expect(screen.getByText('No padel level yet')).toBeTruthy();
  });

  it('ticks a pick, and greys the rest once three are picked', async () => {
    await openFriendsTab();
    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));

    for (const id of [MAGDA, EWA, ANIA]) fireEvent.press(await pickerRow(id));

    expect(screen.getByRole('checkbox', { name: /^magda\.p/, checked: true })).toBeTruthy();
    expect(
      screen.getByRole('checkbox', {
        name: 'karol.t, 2,75 · established, the court is full',
        disabled: true,
      }),
    ).toBeTruthy();

    fireEvent.press(await pickerRow(ANIA));
    expect(screen.getByRole('checkbox', { name: /^karol\.t/, disabled: false })).toBeTruthy();
  });

  it('greys the rest after one pick on a singles court', async () => {
    useFriendsGame.setState({ kind: 'competitive', lineUps: {} });
    await openFriendsTab();
    fireEvent.press(await screen.findByRole('button', { name: 'Sport: Padel' }));
    fireEvent.press(await screen.findByRole('button', { name: 'Tennis' }));
    act(() => jest.advanceTimersByTime(theme.motion.unfold));
    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));

    fireEvent.press(await pickerRow(EWA));

    expect(screen.getByRole('checkbox', { name: /^magda\.p/, disabled: true })).toBeTruthy();
  });

  it('shows the group’s empty card when there are no friends yet', async () => {
    stubFriendsIn({ padel: [] });
    await openFriendsTab();

    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));

    expect(await screen.findByText(COPY.friends.nobody)).toBeTruthy();
  });
});

/**
 * **Ask a friend with no Level to get one** (#758; the screens §4.2; the words §29.3): a greyed
 * no-Level row has *Ask zofia.b to get a padel level* under it, and *Asked* once asked — once per
 * sport, ever, as the read's `level_asked_in` says.
 */
describe('asking a friend to get a Level, from the picker', () => {
  const askPath = `${FRIENDS_PATH}/${ZOFIA}/level-asks`;
  const ASK = 'Ask zofia.b to get a padel level';
  const ASKED_ZOFIA = [
    ...PADEL_FRIENDS.slice(0, 4),
    friend(ZOFIA, 'PADEL', undefined, '', ['PADEL']),
  ];

  async function openPicker() {
    await openFriendsTab();
    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));
    await pickerRow(KAROL);
  }

  it('offers the ask under a greyed no-Level row, and on no other row', async () => {
    await openPicker();

    expect(await screen.findByRole('button', { name: ASK })).toBeTruthy();
    expect(screen.getAllByRole('button', { name: /^Ask .* level$/ })).toHaveLength(1);
    expect(screen.queryByText(FRIENDS_COPY.picker.asked)).toBeNull();
  });

  it('reads Asked where the read says it was asked, with no button', async () => {
    stubFriendsIn({ padel: ASKED_ZOFIA });
    await openPicker();

    expect(await screen.findByText(FRIENDS_COPY.picker.asked)).toBeTruthy();
    expect(screen.getByLabelText('Asked zofia.b to get a padel level')).toBeTruthy();
    expect(screen.queryByRole('button', { name: ASK })).toBeNull();
  });

  it('asks in the picker’s sport from this group, and reads Asked on the server’s answer', async () => {
    transport.on('POST', askPath, () => {
      stubFriendsIn({ padel: ASKED_ZOFIA });
      return noContent();
    });
    await openPicker();

    fireEvent.press(await screen.findByRole('button', { name: ASK }));

    expect(await screen.findByText(FRIENDS_COPY.picker.asked)).toBeTruthy();
    expect(transport.requestsTo('POST', askPath).map((one) => one.body)).toEqual([
      { sport: 'PADEL', group_id: GROUP.id },
    ]);
    expect(screen.queryByRole('button', { name: ASK })).toBeNull();
    // Still greyed: asked for is not got.
    expect(screen.getByRole('checkbox', { name: /^zofia\.b/, disabled: true })).toBeTruthy();
  });

  it('says nothing when it was asked already from another phone — the row reads Asked', async () => {
    transport.on('POST', askPath, () => {
      stubFriendsIn({ padel: ASKED_ZOFIA });
      return errorResponse(409, 'level_already_asked');
    });
    await openPicker();

    fireEvent.press(await screen.findByRole('button', { name: ASK }));

    expect(await screen.findByText(FRIENDS_COPY.picker.asked)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('says where it was pressed when the group is no longer the player’s', async () => {
    transport.on('POST', askPath, () => errorResponse(404, 'not_one_of_your_groups'));
    await openPicker();

    fireEvent.press(await screen.findByRole('button', { name: ASK }));

    expect(await screen.findByText(FRIENDS_COPY.refused.not_one_of_your_groups!)).toBeTruthy();
    expect(screen.getByRole('button', { name: ASK })).toBeTruthy();
  });
});

describe('the court', () => {
  it('seats the picks in the card’s evenest sides on Done', async () => {
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    expect(await seatNamed('Your side, your partner, ewa.m, level 2,60')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Their side, magda.p, level 2,66' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Their side, ania.k, level 2,68' })).toBeTruthy();
    expect(lastCardAsked().getAll('friend_ids')).toEqual([MAGDA, EWA, ANIA]);
    expect(lastCardAsked().get('partner_id')).toBeNull();
    expect(screen.getByLabelText('Padel, 4 of 4 seats filled.')).toBeTruthy();
  });

  it('swaps two faces tapped one after the other, and reads the card for those sides', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');

    fireEvent.press(await seatNamed('Their side, magda.p, level 2,66'));
    expect(screen.getByRole('button', { name: /magda\.p/, selected: true })).toBeTruthy();
    fireEvent.press(
      screen.getByRole('button', { name: 'Your side, your partner, ewa.m, level 2,60' }),
    );

    expect(await seatNamed('Your side, your partner, magda.p, level 2,66')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Their side, ewa.m, level 2,60' })).toBeTruthy();
    await waitFor(() => expect(lastCardAsked().get('partner_id')).toBe(MAGDA));
    expect(
      await screen.findByText('You + magda vs ewa + ania', { includeHiddenElements: true }),
    ).toBeTruthy();
  });

  it('takes a face off with its ×, says how many more to seat, and draws no card', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');

    fireEvent.press(screen.getByRole('button', { name: 'Remove ania.k from their side' }));

    expect(await screen.findByText('Seat 1 more friend')).toBeTruthy();
    expect(screen.queryByTestId('friends-card')).toBeNull();
    expect(screen.getByRole('button', { name: 'Their side, empty' })).toBeTruthy();
  });

  it('opens the picker with the seated friends ticked, and seats the one picked again', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    fireEvent.press(await screen.findByRole('button', { name: 'Remove ania.k from their side' }));

    fireEvent.press(await screen.findByRole('button', { name: 'Their side, empty' }));
    expect(await screen.findByRole('checkbox', { name: /^ewa\.m/, checked: true })).toBeTruthy();
    expect(screen.getByRole('checkbox', { name: /^magda\.p/, checked: true })).toBeTruthy();
    fireEvent.press(await pickerRow(ANIA));
    fireEvent.press(screen.getByRole('button', { name: FRIENDS_COPY.picker.done }));

    expect(await screen.findByTestId('friends-card')).toBeTruthy();
    expect(screen.queryByText('Seat 1 more friend')).toBeNull();
  });

  it('draws a singles court with one friend, and the card names the two of you', async () => {
    await openFriendsTab();
    fireEvent.press(await screen.findByRole('button', { name: 'Sport: Padel' }));
    fireEvent.press(await screen.findByRole('button', { name: 'Tennis' }));
    act(() => jest.advanceTimersByTime(theme.motion.unfold));

    await seat(EWA);

    expect(await seatNamed('Their side, ewa.m, level 3,10')).toBeTruthy();
    expect(await screen.findByText('You vs ewa', { includeHiddenElements: true })).toBeTruthy();
    expect(lastCardAsked().get('sport')).toBe('TENNIS');
    expect(lastCardAsked().getAll('friend_ids')).toEqual([EWA]);
  });

  it('forgets the line-up when the page goes, and keeps the kind', async () => {
    await openFriendsTab();
    fireEvent.press(await tab(COPY.friends.forFun, false));
    await seat(MAGDA, EWA, ANIA);

    fireEvent.press(screen.getByRole('button', { name: COPY.group.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Padel po pracy,/ }));
    fireEvent.press(await tab('Friends'));

    expect(await screen.findByText('Seat 3 more friends')).toBeTruthy();
    expect(await tab(COPY.friends.forFun, true)).toBeTruthy();
  });
});

describe('the card', () => {
  it('is its frame and a quiet line while it is read, with nothing to press', async () => {
    // Never answered: the assertion is about the beat before the card lands.
    transport.on('GET', cardPath, () => new Promise<Response>(() => {}));
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    expect(await screen.findByLabelText(CARD.building)).toBeTruthy();
    expect(screen.getByTestId('friends-card-building')).toBeTruthy();
    expect(screen.queryByRole('button', { name: CARD.pickACourt })).toBeNull();
  });

  it('draws the sides, the balance, the overlap and the court with its share', async () => {
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    const card = await screen.findByTestId('friends-card');
    expect(
      within(card).getByText('You + ewa vs magda + ania', { includeHiddenElements: true }),
    ).toBeTruthy();
    expect(within(card).getByText('87%')).toBeTruthy();
    expect(within(card).getByText('Very even')).toBeTruthy();
    expect(within(card).getByTestId('overlap-grid')).toBeTruthy();
    expect(within(card).getByText(CARD.courtAvailable)).toBeTruthy();
    expect(within(card).getByText('25 zł each')).toBeTruthy();
    expect(within(card).getByText('Saturday 10:00 · Ogrody 33 · Court 3 · indoor')).toBeTruthy();
    expect(within(card).getByRole('button', { name: CARD.pickACourt })).toBeTruthy();
  });

  it('says so in one line when no court is free in the next 14 days', async () => {
    transport.on('GET', cardPath, (request) =>
      json({ ...cardFor(request), court: null, overlap: null, cut_off: null }),
    );
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    expect(await screen.findByText(CARD.noCourt)).toBeTruthy();
    expect(screen.queryByRole('button', { name: CARD.pickACourt })).toBeNull();
  });

  it('says four can’t play together for a blocked pair, naming nobody', async () => {
    transport.on('GET', cardPath, () => errorResponse(409, 'cannot_play_together'));
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    expect(await screen.findByText(CARD.refused.blockedDoubles)).toBeTruthy();
    expect(screen.queryByRole('button', { name: CARD.pickACourt })).toBeNull();
  });

  it('says somebody has no padel level yet, and reads the friends again', async () => {
    transport.on('GET', cardPath, () => errorResponse(409, 'no_level'));
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    expect(
      await screen.findByText('Somebody here has no padel level yet. Swap someone.'),
    ).toBeTruthy();
  });

  it('empties the seat of somebody no longer a friend', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');
    stubFriendsIn({ padel: PADEL_FRIENDS.filter((one) => one.player_id !== ANIA) });
    transport.on('GET', cardPath, () => errorResponse(409, 'not_a_friend'));

    fireEvent.press(await tab(COPY.friends.forFun, false));

    expect(await screen.findByText('Seat 1 more friend')).toBeTruthy();
    expect(screen.queryByRole('button', { name: /ania\.k/ })).toBeNull();
  });
});

describe('a seat somebody no longer holds', () => {
  async function refusedNotAFriend() {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');
    stubFriendsIn({ padel: PADEL_FRIENDS.filter((one) => one.player_id !== ANIA) });
    transport.on('GET', cardPath, () => errorResponse(409, 'not_a_friend'));
    fireEvent.press(await tab(COPY.friends.forFun, false));
    await screen.findByText('Seat 1 more friend');
    transport.on('GET', cardPath, (request) => json(cardFor(request)));
  }

  it('is free to fill: the picker counts only the friends still seated', async () => {
    await refusedNotAFriend();

    fireEvent.press(await screen.findByRole('button', { name: 'Their side, empty' }));

    expect(await screen.findByRole('checkbox', { name: /^ewa\.m/, checked: true })).toBeTruthy();
    expect(screen.getByRole('checkbox', { name: /^karol\.t/, disabled: false })).toBeTruthy();
    fireEvent.press(await pickerRow(KAROL));
    fireEvent.press(screen.getByRole('button', { name: FRIENDS_COPY.picker.done }));

    expect(await screen.findByTestId('friends-card')).toBeTruthy();
    expect(lastCardAsked().getAll('friend_ids').sort()).toEqual([EWA, KAROL, MAGDA].sort());
  });

  it('can be emptied in the picker when its friend lost their Level in the sport', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');
    stubFriendsIn({
      padel: PADEL_FRIENDS.map((one) => (one.player_id === ANIA ? friend(ANIA, 'PADEL') : one)),
    });
    transport.on('GET', cardPath, () => errorResponse(409, 'no_level'));
    fireEvent.press(await tab(COPY.friends.forFun, false));
    await screen.findByText('Somebody here has no padel level yet. Swap someone.');
    fireEvent.press(screen.getByRole('button', { name: 'Remove magda.p from their side' }));

    fireEvent.press(await screen.findByRole('button', { name: /, empty$/ }));
    const ania = await screen.findByRole('checkbox', { name: /^ania\.k/, checked: true });
    expect(ania.props.accessibilityState).toMatchObject({ disabled: false });
    fireEvent.press(ania);

    expect(
      screen.getByRole('checkbox', { name: /^ania\.k/, checked: false, disabled: true }),
    ).toBeTruthy();
  });
});

describe('Find a court', () => {
  async function openFindACourt() {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    fireEvent.press(await screen.findByRole('button', { name: CARD.pickACourt }));
    return screen.findByRole('header', { name: CARD.findACourt.title });
  }

  const rowOf = (court: Wire['FriendsCourtSchema']) =>
    screen.getByTestId(`find-a-court-${court.court_id}-${court.starts_at}`);

  /** The list is virtualised: the rows past its first screenful are drawn once it is scrolled. */
  function scrollToTheEnd() {
    const list = screen.getByTestId('find-a-court-list');
    fireEvent(list, 'layout', { nativeEvent: { layout: { x: 0, y: 0, width: 360, height: 600 } } });
    fireEvent(list, 'contentSizeChange', 360, 1600);
    fireEvent.scroll(list, {
      nativeEvent: {
        contentOffset: { x: 0, y: 1200 },
        contentSize: { width: 360, height: 1600 },
        layoutMeasurement: { width: 360, height: 600 },
      },
    });
    act(() => jest.runOnlyPendingTimers());
  }

  it('lists every court by day, each with its hour, its court, who is free and the share', async () => {
    await openFindACourt();

    expect(await screen.findByText('Tomorrow')).toBeTruthy();
    expect(screen.getByText('Saturday')).toBeTruthy();
    expect(screen.getByText('Sunday')).toBeTruthy();
    scrollToTheEnd();
    expect(await screen.findByText('Sat 10 Oct')).toBeTruthy();
    expect(
      screen.getByRole('button', {
        name: '19:00, Bonarka Arena · Court 2, Everybody free, 25 zł each',
      }),
    ).toBeTruthy();
    expect(screen.getByText('magda.p and ania.k busy')).toBeTruthy();
    expect(screen.getByText('You, ewa.m and ania.k busy')).toBeTruthy();
  });

  it('tints each row by how many are free — brightest for all four, then three, two, one', async () => {
    await openFindACourt();
    await screen.findByText('Tomorrow');
    scrollToTheEnd();
    await screen.findByText('Sat 10 Oct');

    const bed = (court: Wire['FriendsCourtSchema']) =>
      StyleSheet.flatten(rowOf(court).props.style).backgroundColor;
    const edge = (court: Wire['FriendsCourtSchema']) =>
      StyleSheet.flatten(rowOf(court).props.style).borderColor;

    expect([bed(ROWS[0]!), edge(ROWS[0]!)]).toEqual([theme.color.mintSoft, theme.color.mint]);
    expect([bed(ROWS[2]!), edge(ROWS[2]!)]).toEqual([theme.color.surface, theme.color.mintLine]);
    expect([bed(ROWS[3]!), edge(ROWS[3]!)]).toEqual([theme.color.surface, theme.color.line]);
    expect([bed(ROWS[4]!), edge(ROWS[4]!)]).toEqual([theme.color.paper2, theme.color.line]);
  });

  it('marks another club’s court at the hour the home club is full', async () => {
    await openFindACourt();

    expect(await screen.findByText('Ogrody 33 is full at 11:00')).toBeTruthy();
    expect(screen.getByText('ania.k busy')).toBeTruthy();
  });

  it('rings the card’s own court', async () => {
    await openFindACourt();
    await screen.findByText('Tomorrow');

    expect(screen.getByRole('button', { name: /, picked$/, selected: true })).toBe(rowOf(PROPOSED));
  });

  it('puts the row picked on the card, even one where somebody is busy', async () => {
    await openFindACourt();
    await screen.findByText('Sunday');

    fireEvent.press(rowOf(ROWS[3]!));

    await waitFor(() => expect(lastCardAsked().get('court_id')).toBe(ROWS[3]!.court_id));
    expect(lastCardAsked().get('starts_at')).toBe(ROWS[3]!.starts_at);
    expect(lastCardAsked().get('partner_id')).toBe(EWA);
    expect(await screen.findByText('Sunday 15:00 · Ogrody 33 · Court 5 · indoor')).toBeTruthy();
  });
});
