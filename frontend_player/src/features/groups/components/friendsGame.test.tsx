/**
 * **A game with friends, built on a group's Friends tab** — the picker, the court, the card and
 * *Find a court* ([#757](https://github.com/Rakieta02/Rakieta/issues/757); the friends screens §4.2,
 * §7; friends 3, 6–11), and sending it ([#759](https://github.com/Rakieta02/Rakieta/issues/759)).
 *
 * The real route tree, with the socket faked: the friends read answers per sport, highest Level
 * first, as `GET /friends?sport=` does; the card answers the evenest sides — *You + ewa.m* against
 * *magda.p + ania.k* — or the sides a swap sent; and *Find a court* lists five rows, one of each
 * tint and a court at another club where the home club is full. **Every read happens at
 * `DECK_READ_AT`**, Wednesday 30 September 10:00 in Warsaw, so Saturday is *Saturday* and the
 * Saturday after it *Sat 10 Oct*.
 *
 * **Sending** (#759; the screens §8) closes the suite: the card's *Send game and pay 25 zł* opens
 * the send sheet, and what each answer does — booked, a method to save, payments to confirm with
 * the bank, the court gone, and each refusal's sentence.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { StyleSheet } from 'react-native';

import { FRIENDS_COPY } from '@/features/friends/types';
import { PAYMENTS_COPY } from '@/features/payments/types';
import { FILL_COPY, FRIENDS_CARD_COPY, FRIENDS_GAME_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import { DECK_READ_AT, deckPath, stubGroupDeck } from '@/test-support/groupDeck';
import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import {
  FRIENDS_PATH,
  GATE_USER,
  launchSignedIn,
  resetPayments,
  stubGate,
  stubMyGroups,
  stubPaymentMethod,
  stubPayments,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakePayments } from '@/test-support/platform';
import { menuLine, menuTab, openTabMenu, pickKind } from '@/test-support/tabMenu';
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

import { groupFriendsRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsPresentation';

const COPY = GROUPS_COPY;
const KINDS = COPY.group.kinds;
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
  link: 'https://rakieta.app/join/K7PQ2MXA',
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

/** The line-up's Social vibe on For fun (#834) — *Good vibe*, whoever stands beside whom. */
const LINE_UP_VIBE = 67;

/**
 * The card: the evenest sides are you and ewa.m against the other two — or, after a swap, the
 * partner sent beside you. A court picked comes back as the card's. **Each kind says its own
 * number**, as the server does (#834): *87%* on Competitive, the Social vibe and no forecast on For
 * fun.
 */
function cardFor(request: RecordedRequest): Wire['FriendsCardResponse'] {
  const asked = query(request);
  const friends = asked.getAll('friend_ids');
  const partner = asked.get('partner_id') ?? (friends.length > 1 ? EWA : undefined);
  const courtId = asked.get('court_id');
  const court = ROWS.find(
    (one) => one.court_id === courtId && one.starts_at === asked.get('starts_at'),
  );
  const kind = asked.get('kind') as Wire['SearchMode'];
  return {
    pool_id: GROUP.id,
    sport: asked.get('sport') as Wire['Sport'],
    kind,
    home_club: HOME,
    sides:
      partner === undefined
        ? { yours: [ME], theirs: friends }
        : { yours: [ME, partner], theirs: friends.filter((one) => one !== partner) },
    forecast: kind === 'FOR_FUN' ? null : { pct: 87, provisional: false },
    vibe: kind === 'FOR_FUN' ? { pct: LINE_UP_VIBE } : null,
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
  resetPayments();
  useToastQueue.setState({ queue: [] });
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
  expect(await menuTab('Friends')).toBeTruthy();
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

/** Friends' chevron, wherever it is drawn — a mark, never spoken. */
const chevron = () =>
  screen.queryByTestId('segment-chevron-friends', { includeHiddenElements: true });
/** The menu, as a finger and a listener reach it — not while it folds away. */
const menu = () => screen.queryByTestId('tab-menu');

/**
 * **The Friends tab's menu** (#861, PRD #859; the friends screens §7.1): the row above the court is
 * gone, and the kind of the game being built is picked from a menu hanging from the selected tab.
 */
describe('the tab’s menu, opening and shutting', () => {
  afterEach(() => stopWatchingHardwareBack());

  it('draws no row over the court, and a chevron on the selected tab — spoken with the kind', async () => {
    await openFriendsTab();

    expect(chevron()).toBeTruthy();
    expect(screen.queryByRole('button', { name: KINDS.competitive })).toBeNull();
    expect(screen.queryByRole('button', { name: KINDS.forFun })).toBeNull();
    const friends = await menuTab('Friends');
    expect(friends.props.accessibilityLabel).toBe('Friends, Competitive');
    expect(friends.props.accessibilityState).toEqual({ selected: true, expanded: false });
  });

  it('draws none on Friends while another tab is selected, nor ever on Fill in or You’re in', async () => {
    await openFriendsTab();

    for (const other of ['Games', 'Fill in', 'You’re in']) {
      fireEvent.press(await tab(other));
      expect(
        await screen.findByRole('button', { name: new RegExp(`^${other}`), selected: true }),
      ).toBeTruthy();
      expect(chevron()).toBeNull();
      // Nothing on the bar says a menu but the selected Games tab's own (#862), and Friends is its
      // name alone.
      for (const one of screen.getAllByRole('button', {
        name: /^(Games|Fill in|You’re in|Friends)/,
      })) {
        const gamesOwn = other === 'Games' && one.props.accessibilityLabel === 'Games, Competitive';
        expect(one.props.accessibilityState?.expanded).toBe(gamesOwn ? false : undefined);
      }
      expect(screen.getByRole('button', { name: 'Friends', selected: false })).toBeTruthy();
    }
  });

  it('opens on a press on the selected tab: Competitive then For fun, the kind ticked, no counts', async () => {
    await openFriendsTab();
    const asked = cardRequests().length;

    const open = await openTabMenu('Friends');

    expect(await menuTab('Friends', true)).toBeTruthy();
    expect(
      within(open)
        .getAllByRole('button')
        .map((one) => one.props.accessibilityLabel),
    ).toEqual(['Competitive', 'For fun']);
    expect((await menuLine(KINDS.competitive)).props.accessibilityState).toEqual({
      selected: true,
    });
    expect((await menuLine(KINDS.forFun)).props.accessibilityState).toEqual({ selected: false });
    expect(
      within(await menuLine(KINDS.competitive)).getByTestId('tab-menu-tick', {
        includeHiddenElements: true,
      }),
    ).toBeTruthy();
    // No counts and no door: two words, both live.
    expect(within(open).queryAllByText(/[0-9]/, { includeHiddenElements: true })).toEqual([]);
    // Nothing else moved.
    expect(screen).toHavePathname(`/play/group/${GROUP.id}`);
    expect(cardRequests()).toHaveLength(asked);
  });

  it('shuts on a second press on the tab, with nothing changed', async () => {
    await openFriendsTab();
    await openTabMenu('Friends');

    fireEvent.press(await menuTab('Friends', true));

    expect(menu()).toBeNull();
    expect(await menuTab('Friends')).toBeTruthy();
    expect(useFriendsGame.getState().kind).toBe('competitive');
  });

  it('shuts on a press anywhere on the page, which does nothing else — no seat, no card button', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');
    const asked = cardRequests().length;
    await openTabMenu('Friends');

    // Under the menu the page takes no touch at all: a seat, the card's buttons, + Friends' seat.
    fireEvent.press(await seatNamed('Their side, magda.p, level 2,66'));
    fireEvent.press(screen.getByRole('button', { name: CARD.pickACourt }));
    fireEvent.press(screen.getByRole('button', { name: 'Remove ania.k from their side' }));
    expect(menu()).toBeTruthy();

    // The catcher over the page takes the press, and shuts the menu.
    fireEvent.press(screen.getByTestId('tab-menu-catcher-below'));

    expect(menu()).toBeNull();
    expect(screen).toHavePathname(`/play/group/${GROUP.id}`);
    expect(
      (await seatNamed('Their side, magda.p, level 2,66')).props.accessibilityState,
    ).toMatchObject({ selected: false });
    expect(screen.getByRole('button', { name: 'Remove ania.k from their side' })).toBeTruthy();
    expect(cardRequests()).toHaveLength(asked);
  });

  it('shuts on a press over the header, which opens neither Info nor the sport bar', async () => {
    await openFriendsTab();
    await openTabMenu('Friends');

    fireEvent.press(screen.getByTestId('tab-menu-catcher-above'));

    expect(menu()).toBeNull();
    expect(screen).toHavePathname(`/play/group/${GROUP.id}`);
    expect(screen.queryByTestId('sport-bar')).toBeNull();
  });

  it('goes to another tab in one press, and the menu goes with the tab', async () => {
    await openFriendsTab();
    await openTabMenu('Friends');

    fireEvent.press(await tab('Fill in'));

    expect(await tab('Fill in', true)).toBeTruthy();
    expect(menu()).toBeNull();
    // Back on Friends, it is shut until asked.
    fireEvent.press(await tab('Friends'));
    expect(await menuTab('Friends')).toBeTruthy();
    expect(menu()).toBeNull();
  });

  it('shuts on Android back, and the page stays where it was', async () => {
    watchHardwareBack();
    await openFriendsTab();
    await openTabMenu('Friends');

    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });

    expect(claimed).toBe(true);
    expect(menu()).toBeNull();
    expect(screen).toHavePathname(`/play/group/${GROUP.id}`);
    expect(await menuTab('Friends')).toBeTruthy();
  });

  it('shuts when the sport changes under it', async () => {
    await openFriendsTab();
    await openTabMenu('Friends');

    // The catcher keeps a finger off the pill; the page's rule holds for any way the sport moves.
    fireEvent.press(await screen.findByRole('button', { name: 'Sport: Padel' }));
    fireEvent.press(await screen.findByRole('button', { name: 'Tennis' }));
    act(() => jest.advanceTimersByTime(theme.motion.unfold));

    expect(await screen.findByRole('button', { name: 'Sport: Tennis' })).toBeTruthy();
    expect(menu()).toBeNull();
    expect(await menuTab('Friends')).toBeTruthy();
    // Back on padel, the menu it was opened on is forgotten — never open on its own.
    fireEvent.press(await screen.findByRole('button', { name: 'Sport: Tennis' }));
    fireEvent.press(await screen.findByRole('button', { name: 'Padel' }));
    act(() => jest.advanceTimersByTime(theme.motion.unfold));
    expect(await screen.findByRole('button', { name: 'Sport: Padel' })).toBeTruthy();
    expect(menu()).toBeNull();
  });

  it('shuts when a screen is pushed over the page, and is shut on the way back', async () => {
    await openFriendsTab();
    await openTabMenu('Friends');

    act(() => router.push(groupFriendsRoute(GROUP.id, 'padel')));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP.id}/friends`));
    fireEvent.press(screen.getByRole('button', { name: FRIENDS_COPY.picker.done }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP.id}`));

    expect(await menuTab('Friends')).toBeTruthy();
    expect(menu()).toBeNull();
  });

  it('leaves the app’s bottom bar working while it is open', async () => {
    await openFriendsTab();
    await openTabMenu('Friends');

    fireEvent.press(screen.getByLabelText('You'));

    await waitFor(() => expect(screen).toHavePathname('/you'));
  });
});

describe('the tab’s menu, picking a kind', () => {
  it('sets this game’s kind, and never the Games deck’s switch', async () => {
    await openFriendsTab();

    await pickKind('Friends', KINDS.forFun);

    expect(await tab('Friends, For fun', true)).toBeTruthy();
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

    await pickKind('Friends', KINDS.forFun);

    await waitFor(() => expect(lastCardAsked().get('kind')).toBe('FOR_FUN'));
    expect(lastCardAsked().get('partner_id')).toBe(EWA);
    expect(await seatNamed('Your side, your partner, ewa.m, level 2,60')).toBeTruthy();
  });

  // #842 (ADR-0207 §5): the card's number is the kind's own, and the switch flips it.
  it('flips the card’s number with the kind — the forecast on Competitive, the Social vibe on For fun', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);

    let card = await screen.findByTestId('friends-card');
    expect(within(card).getByTestId('friends-card-forecast')).toBeTruthy();
    expect(within(card).getByText('87%')).toBeTruthy();
    expect(within(card).queryByLabelText(VIBE_SPOKEN)).toBeNull();

    await pickKind('Friends', KINDS.forFun);

    expect(await screen.findByLabelText(VIBE_SPOKEN)).toBeTruthy();
    card = screen.getByTestId('friends-card');
    expect(within(card).getByText('67%')).toBeTruthy();
    expect(within(card).queryByTestId('friends-card-forecast')).toBeNull();
    expect(within(card).queryByText('87%')).toBeNull();

    await pickKind('Friends', KINDS.competitive);

    expect(await screen.findByTestId('friends-card-forecast')).toBeTruthy();
    expect(within(screen.getByTestId('friends-card')).getByText('87%')).toBeTruthy();
    expect(screen.queryByLabelText(VIBE_SPOKEN)).toBeNull();
  });

  it('folds away on the other kind, and the tab says it', async () => {
    await openFriendsTab();

    await pickKind('Friends', KINDS.forFun);

    expect(menu()).toBeNull();
    expect(await tab('Friends, For fun', true)).toBeTruthy();
    await openTabMenu('Friends');
    expect((await menuLine(KINDS.forFun)).props.accessibilityState).toEqual({ selected: true });
  });

  it('just shuts on the kind it already is — the card is not asked again', async () => {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    await screen.findByTestId('friends-card');
    const asked = cardRequests().length;

    await pickKind('Friends', KINDS.competitive);

    expect(menu()).toBeNull();
    expect(await tab('Friends, Competitive', true)).toBeTruthy();
    expect(cardRequests()).toHaveLength(asked);
  });

  it('never moves with the Games deck’s kind', async () => {
    await openFriendsTab();
    fireEvent.press(await tab('Games'));

    // The Games tab's own menu (#862) moves the deck, and never the game being built.
    await pickKind('Games', KINDS.forFun);
    await waitFor(() => expect(useGameIntent.getState().intent).toBe('forFun'));

    fireEvent.press(await tab('Friends'));
    expect(await tab('Friends, Competitive', true)).toBeTruthy();
  });
});

/** The line-up's Social vibe as its row says it — the figure, then the band's word. */
const VIBE_SPOKEN = `Social vibe, ${LINE_UP_VIBE} percent, Good vibe`;

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
    await pickKind('Friends', KINDS.forFun);
    await seat(MAGDA, EWA, ANIA);

    fireEvent.press(screen.getByRole('button', { name: COPY.group.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Padel po pracy,/ }));
    fireEvent.press(await tab('Friends'));

    expect(await screen.findByText('Seat 3 more friends')).toBeTruthy();
    expect(await tab('Friends, For fun', true)).toBeTruthy();
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

  // #842 (ADR-0207 §5): For fun's card says the line-up's Social vibe, and draws no forecast.
  it('on For fun, draws the Social vibe row where the forecast stood, and says the sides itself', async () => {
    useFriendsGame.setState({ kind: 'forFun', lineUps: {} });
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    const card = await screen.findByTestId('friends-card');
    expect(within(card).getByLabelText(VIBE_SPOKEN)).toBeTruthy();
    expect(within(card).getByText('67%')).toBeTruthy();
    expect(within(card).queryByTestId('friends-card-forecast')).toBeNull();
    expect(within(card).queryByText('Very even')).toBeNull();
    // With no forecast to name them, the vs line says the sides to a listener.
    expect(within(card).getByLabelText('You and ewa.m against magda.p and ania.k')).toBeTruthy();
    // The rest of the card is the competitive one's.
    expect(within(card).getByTestId('overlap-grid')).toBeTruthy();
    expect(within(card).getByText(CARD.courtAvailable)).toBeTruthy();
    expect(within(card).getByRole('button', { name: CARD.pickACourt })).toBeTruthy();
  });

  it('on Competitive, leaves the vs line a drawing — the forecast’s name says the sides', async () => {
    await openFriendsTab();

    await seat(MAGDA, EWA, ANIA);

    const card = await screen.findByTestId('friends-card');
    expect(within(card).queryByLabelText('You and ewa.m against magda.p and ania.k')).toBeNull();
    expect(within(card).getByTestId('friends-card-forecast').props.accessibilityLabel).toContain(
      'You + ewa against magda + ania',
    );
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

    await pickKind('Friends', KINDS.forFun);

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
    await pickKind('Friends', KINDS.forFun);
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
    await pickKind('Friends', KINDS.forFun);
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

/**
 * **Sending** (#759; the friends screens §8; the mechanics §8; the words §29.7): *Send game and pay
 * 25 zł* under the card opens the send sheet — *Split the cost* first and chosen, *Pay the whole
 * court* beside it — and its order books the court at once. The card's court is Saturday 10:00 at
 * Ogrody 33, 25 zł a seat, the club's cut-off Friday 10:00.
 */
describe('sending', () => {
  const sendPath = `/api/v1/pools/${GROUP.id}/friends-games`;
  const BOOKING = 'b0000000-0000-4000-8000-000000000759';
  const VISA: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };
  const SEND = FRIENDS_GAME_COPY.send;
  const COVER =
    'We hold 100 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł for any seat still empty then.';

  const booked = (): Wire['FriendsGameSentResponse'] => ({
    booking_id: BOOKING,
    booked: { booking_id: BOOKING, game_id: 'g0000000-0000-4000-8000-000000000759' },
    your_payments: [],
  });
  const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);
  const sends = () => transport.requestsTo('POST', sendPath).map((one) => one.body);

  beforeEach(() => {
    stubPaymentMethod(transport, VISA);
  });

  /** The card for magda.p, ewa.m and ania.k, and its send sheet open. */
  async function openTheSheet() {
    await openFriendsTab();
    await seat(MAGDA, EWA, ANIA);
    const card = await screen.findByTestId('friends-card');
    fireEvent.press(within(card).getByRole('button', { name: 'Send game and pay 25 zł' }));
    return screen.findByTestId('send-sheet');
  }

  const order = (label: string) =>
    fireEvent.press(within(screen.getByTestId('send-sheet')).getByRole('button', { name: label }));

  it('opens the sheet with Split first and chosen, its maximum right above the order', async () => {
    const sheet = await openTheSheet();

    expect(screen.getByText(SEND.title)).toBeTruthy();
    expect(
      within(sheet)
        .getAllByRole('button', { name: /^(Split the cost|Pay the whole court),/ })
        .map((one) => [one.props.accessibilityLabel, one.props.accessibilityState?.selected]),
    ).toEqual([
      ['Split the cost, 25 zł', true],
      ['Pay the whole court, 100 zł', false],
    ]);
    expect(within(sheet).getByText(COVER)).toBeTruthy();
    expect(within(sheet).getByRole('button', { name: 'Send game and pay 25 zł' })).toBeTruthy();
  });

  it('turns the order to the whole court, with no cover line, once Whole court is chosen', async () => {
    const sheet = await openTheSheet();

    fireEvent.press(within(sheet).getByRole('button', { name: 'Pay the whole court, 100 zł' }));

    expect(
      within(sheet).getByRole('button', { name: 'Pay the whole court, 100 zł', selected: true }),
    ).toBeTruthy();
    expect(within(sheet).queryByText(COVER)).toBeNull();
    expect(within(sheet).getByRole('button', { name: 'Send game and pay 100 zł' })).toBeTruthy();
  });

  it('sends the card as it was read with Split, then empties the court and says where the game is', async () => {
    transport.on('POST', sendPath, () => json(booked()));
    await openTheSheet();

    order('Send game and pay 25 zł');

    expect(await screen.findByText('Seat 3 more friends')).toBeTruthy();
    expect(screen.queryByTestId('friends-card')).toBeNull();
    expect(screen.queryByTestId('send-sheet')).toBeNull();
    expect(sends()).toEqual([
      {
        sport: 'PADEL',
        kind: 'COMPETITIVE',
        friend_ids: [MAGDA, EWA, ANIA],
        partner_id: null,
        court_id: PROPOSED.court_id,
        starts_at: PROPOSED.starts_at,
        pay_mode: 'SPLIT_THE_COST',
        booking_id: null,
      },
    ]);
    expect(toasts()).toEqual([[SEND.sent, 'ok']]);
  });

  it('sends Whole court as the sheet chose it', async () => {
    transport.on('POST', sendPath, () => json(booked()));
    const sheet = await openTheSheet();

    fireEvent.press(within(sheet).getByRole('button', { name: 'Pay the whole court, 100 zł' }));
    order('Send game and pay 100 zł');

    await screen.findByText('Seat 3 more friends');
    expect(sends()).toEqual([expect.objectContaining({ pay_mode: 'WHOLE_COURT' })]);
  });

  it('opens the payment setup first with nothing saved, and sends nothing until a method is', async () => {
    stubPaymentMethod(transport, null);
    await openTheSheet();

    order('Send game and pay 25 zł');

    expect(await screen.findByText(PAYMENTS_COPY.setupSheet.title)).toBeTruthy();
    expect(sends()).toEqual([]);
  });

  it('opens the setup when the server says a method is needed', async () => {
    transport.on('POST', sendPath, () => errorResponse(409, 'payment_method_required'));
    await openTheSheet();

    order('Send game and pay 25 zł');

    expect(await screen.findByText(PAYMENTS_COPY.setupSheet.title)).toBeTruthy();
    expect(screen.queryByTestId('send-sheet')).toBeNull();
  });

  it('confirms each payment the bank wants confirmed in the app, then sends again under the same booking', async () => {
    const payments = fakePayments();
    stubPayments(payments);
    const charges = ['sc-share', 'sc-cover'];
    for (const id of charges) {
      transport.on('GET', `/api/v1/seat-charges/${id}`, () =>
        json<Wire['SeatChargeResponse']>({
          seat_charge_id: id,
          proposal_id: BOOKING,
          status: 'FAILED',
          refusal: 'AUTHENTICATION_REQUIRED',
          amount_grosze: 2500,
          sport: 'PADEL',
          starts_at: PROPOSED.starts_at,
          club: HOME,
          to_confirm: {
            client_secret: `${id}_secret`,
            connected_account_id: 'acct_ogrody',
            publishable_key: 'pk_test_rakieta',
          },
        }),
      );
      transport.on('POST', `/api/v1/seat-charges/${id}/confirmation`, () =>
        json<Wire['YesAnswerResponse']>({
          proposal_id: BOOKING,
          open_seats: 0,
          booked: null,
          your_payment: null,
        }),
      );
    }
    let sent = 0;
    transport.on('POST', sendPath, () => {
      sent += 1;
      if (sent > 1) return json(booked());
      return json<Wire['FriendsGameSentResponse']>({
        booking_id: BOOKING,
        booked: null,
        your_payments: charges.map((id) => ({
          seat_charge_id: id,
          refusal: 'AUTHENTICATION_REQUIRED',
          confirm_by: null,
          time_to: null,
        })),
      });
    });
    await openTheSheet();

    order('Send game and pay 25 zł');
    fireEvent.press(await screen.findByRole('button', { name: FILL_COPY.confirm.check }));
    await waitFor(() =>
      expect(
        transport.requestsTo('POST', '/api/v1/seat-charges/sc-share/confirmation'),
      ).toHaveLength(1),
    );
    fireEvent.press(await screen.findByRole('button', { name: FILL_COPY.confirm.check }));

    expect(await screen.findByText('Seat 3 more friends')).toBeTruthy();
    expect(transport.requestsTo('POST', '/api/v1/seat-charges/sc-cover/confirmation')).toHaveLength(
      1,
    );
    expect(payments.payments.map((one) => one.clientSecret)).toEqual([
      'sc-share_secret',
      'sc-cover_secret',
    ]);
    expect(sends().map((one) => (one as { booking_id: string | null }).booking_id)).toEqual([
      null,
      BOOKING,
    ]);
    expect(toasts()).toEqual([[SEND.sent, 'ok']]);
  });

  it('reads the card again with the court’s sentence when another game took it first', async () => {
    transport.on('POST', sendPath, () => errorResponse(409, 'court_just_taken'));
    await openTheSheet();
    const asked = cardRequests().length;

    order('Send game and pay 25 zł');

    expect(
      await screen.findByText(
        'That court was just booked by another game. Nothing was charged — try again.',
      ),
    ).toBeTruthy();
    expect(screen.queryByTestId('send-sheet')).toBeNull();
    await waitFor(() => expect(cardRequests().length).toBeGreaterThan(asked));
    expect(await screen.findByTestId('friends-card')).toBeTruthy();
  });

  it('lets a court no longer for sale go — the card proposes another, and says why', async () => {
    transport.on('POST', sendPath, () => errorResponse(409, 'court_hour_not_for_sale'));
    await openTheSheet();
    const asked = cardRequests().length;

    order('Send game and pay 25 zł');

    expect(await screen.findByText(SEND.refused.courtGone)).toBeTruthy();
    expect(screen.queryByTestId('send-sheet')).toBeNull();
    await waitFor(() => expect(cardRequests().length).toBeGreaterThan(asked));
  });

  it('names You › Payments when the card’s terms must be accepted again, and books nothing', async () => {
    transport.on('POST', sendPath, () =>
      json<Wire['FriendsGameSentResponse']>({
        booking_id: BOOKING,
        booked: null,
        your_payments: [
          { seat_charge_id: 'sc-terms', refusal: 'TERMS_NEEDED', confirm_by: null, time_to: null },
        ],
      }),
    );
    await openTheSheet();

    order('Send game and pay 25 zł');

    await waitFor(() => expect(toasts()).toEqual([[FILL_COPY.termsAgain, 'bad']]));
    expect(screen.queryByTestId('send-sheet')).toBeNull();
    expect(screen.getByTestId('friends-card')).toBeTruthy();
  });

  it('sends again under the booking a refused send answered, at the next press', async () => {
    let sent = 0;
    transport.on('POST', sendPath, () => {
      sent += 1;
      return sent === 1
        ? json<Wire['FriendsGameSentResponse']>({
            booking_id: BOOKING,
            booked: null,
            your_payments: [],
          })
        : json(booked());
    });
    const sheet = await openTheSheet();

    order('Send game and pay 25 zł');
    await within(sheet).findByRole('alert');
    order('Send game and pay 25 zł');

    expect(await screen.findByText('Seat 3 more friends')).toBeTruthy();
    expect(sends().map((one) => (one as { booking_id: string | null }).booking_id)).toEqual([
      null,
      BOOKING,
    ]);
  });

  it.each([
    [
      'friends_games_waiting',
      { cap: 2 },
      'You have 2 friends games waiting for answers. Send this one once one of them is settled.',
    ],
    ['you_play_then', {}, 'You already have a game at 10:00.'],
    [
      'games_per_week_booked',
      { games_per_week: 3, week: '2026-09-28' },
      'Your week is full: 3 games, the most you set in Games & money.',
    ],
  ])('says %s in the sheet, the order still there', async (code, details, sentence) => {
    transport.on('POST', sendPath, () =>
      json<Wire['ErrorResponse']>({ code, message: 'refused', trace_id: 't', details }, 409),
    );
    const sheet = await openTheSheet();

    order('Send game and pay 25 zł');

    expect(await within(sheet).findByText(sentence)).toBeTruthy();
    expect(within(sheet).getByRole('button', { name: 'Send game and pay 25 zł' })).toBeTruthy();
    expect(screen.getByTestId('friends-card')).toBeTruthy();
  });
});
