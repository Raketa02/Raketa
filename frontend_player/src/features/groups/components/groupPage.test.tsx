/**
 * **A group's page, walked** — the fast filter, the tab bar, and the Games, Fill in and Friends
 * tabs in their starting states, and the Friends screen behind the court
 * ([#513](https://github.com/Raketa02/Raketa/issues/513), PRD #500 stories 51–70; play mocks
 * 14–17, 39–55). Info and Members are `groupInfo.test.tsx`'s.
 *
 * The real route tree, with the socket, the share sheet and the clipboard faked at the platform
 * edge. *A relaunch* is the process ending and a new one starting: the Query cache and the session
 * go, and what the phone keeps — the keychain and its preferences — stays.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { getAnimatedStyle } from 'react-native-reanimated';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { POSTER_LABEL, theme } from '@/shared/ui';
import {
  GATE_USER,
  launchSignedIn,
  OWN_RECORD_SERVED,
  resetClipboard,
  resetShare,
  stubClipboard,
  stubGate,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
  stubOwnRecord,
  stubShare,
} from '@/test-support/onboardingRouter';
import {
  fakeClipboard,
  fakeShare,
  type FakeClipboard,
  type FakeShare,
} from '@/test-support/platform';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { useGameIntent } from '../store/gameIntent.store';

import { GROUPS_COPY } from './groupsPresentation';

const COPY = GROUPS_COPY;

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

const PADEL = rating('PADEL', 2.71);
const TENNIS = rating('TENNIS', 3.1);
const SQUASH = rating('SQUASH', 2.3);
const BADMINTON = rating('BADMINTON', 2.05);

const LINK = 'https://raketa.app/join/K7PQ2MXA';

/** Tomek, as the group serves his face — the reader. */
const TOMEK: Wire['GroupPersonSchema'] = { player_id: GATE_USER.id, name: 'Tomek Kowal' };

function member(n: number): Wire['GroupPersonSchema'] {
  return { player_id: `e0000000-0000-4000-8000-00000000000${n}`, name: `Member ${n}` };
}

function roster(
  sport: Wire['Sport'],
  ratedCount: number,
  firstRated: readonly Wire['GroupPersonSchema'][] = ratedCount > 0 ? [TOMEK] : [],
): Wire['GroupSportSchema'] {
  return { sport, rated_count: ratedCount, first_rated: [...firstRated] };
}

const MY_RAKETA_GROUP: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000011',
  kind: 'PLAYER',
  name: 'my raketa group',
  monogram: { letters: 'mr', colour: 5 },
  sports: [],
  member_count: 1,
  home_club: { id: 'c0000000-0000-4000-8000-000000000007', name: 'Bonarka Arena' },
};

const KAZIMIERZ_CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

/** Just Tomek, rated in every sport he plays — the ticket's opening. */
const JUST_TOMEK = [
  roster('PADEL', 1),
  roster('TENNIS', 1),
  roster('SQUASH', 1),
  roster('BADMINTON', 1),
];

function pageOf(
  group: Wire['MyGroupSchema'],
  overrides: Partial<Wire['GroupResponse']> = {},
): Wire['GroupResponse'] {
  return {
    ...group,
    link: LINK,
    join_policy: 'ANYONE',
    is_owner: true,
    rated_by_sport: JUST_TOMEK,
    member_faces: [],
    administrator_name: null,
    is_administrator: false,
    ...overrides,
  };
}

let transport: Transport;
let share: FakeShare;
let clipboard: FakeClipboard;

function stubAPlayer(ratings: readonly Wire['RatingResponse'][]) {
  stubGate(transport, { ratings, hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
}

beforeEach(() => {
  transport = installTransport();
  stubAPlayer([PADEL, TENNIS]);
  share = fakeShare();
  stubShare(share);
  clipboard = fakeClipboard();
  stubClipboard(clipboard);
  useGameIntent.setState({ intent: 'competitive' });
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  resetShare();
  resetClipboard();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const cardNamed = (name: string) => screen.findByRole('button', { name: new RegExp(`^${name},`) });

/** Serve these groups on the list and each one's page, and land on the list. */
async function openGroups(
  ...pages: readonly [Wire['MyGroupSchema'], Wire['GroupResponse']][]
): Promise<void> {
  stubMyGroups(
    transport,
    pages.map(([group]) => group),
  );
  for (const [group, page] of pages) {
    transport.on('GET', `/api/v1/groups/${group.id}`, () => json(page));
  }
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

async function enter(group: Wire['MyGroupSchema']) {
  fireEvent.press(await cardNamed(group.name));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${group.id}`));
}

async function openGroup(
  group: Wire['MyGroupSchema'] = MY_RAKETA_GROUP,
  page: Wire['GroupResponse'] = pageOf(group),
) {
  await openGroups([group, page]);
  await enter(group);
}

async function relaunch() {
  screen.unmount();
  queryClient.clear();
  resetSessionStatus();
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

const pill = (sport: string) => screen.findByRole('button', { name: `Sport: ${sport}` });

/** The bar's options, left to right, as a listener meets them. */
function barOptions(): string[] {
  const bar = screen.getByTestId('sport-bar');
  return within(bar)
    .getAllByRole('button')
    .map((option) => option.props.accessibilityLabel as string);
}

/** Past the unfold, so nothing is still moving when the suite looks. */
function settleTheUnfold() {
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
}

async function unfold(sport: string) {
  fireEvent.press(await pill(sport));
  await screen.findByTestId('sport-bar');
  settleTheUnfold();
}

const tab = (name: string, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

async function openTab(name: string) {
  fireEvent.press(await tab(name));
  expect(await tab(name, true)).toBeTruthy();
}

const faces = () => screen.queryAllByTestId(/^games-face-/, { includeHiddenElements: true });
const emptyGamesSeats = () =>
  screen.queryAllByTestId('games-empty-seat', { includeHiddenElements: true });

describe('the fast filter', () => {
  it('opens on the first sport the player is rated in, drawn as a pill', async () => {
    stubAPlayer([TENNIS, PADEL]);
    await openGroup();

    expect(await pill('Padel')).toBeTruthy();
  });

  it('unfolds into the other rated sports, with the current one last and chosen', async () => {
    await openGroup();

    await unfold('Padel');

    expect(barOptions()).toEqual(['Tennis', 'Padel']);
    expect(
      within(screen.getByTestId('sport-bar')).getByRole('button', {
        name: 'Padel',
        selected: true,
      }),
    ).toBeTruthy();
  });

  it('lists only the sports the player is rated in, in the order padel › tennis › squash › badminton', async () => {
    stubAPlayer([BADMINTON, SQUASH, PADEL, TENNIS]);
    await openGroup();

    await unfold('Padel');

    expect(barOptions()).toEqual(['Tennis', 'Squash', 'Badminton', 'Padel']);
  });

  it('re-filters the page by the sport tapped, and folds', async () => {
    await openGroup();
    expect(await screen.findByText(/once 4 who play padel are in/)).toBeTruthy();
    await unfold('Padel');

    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Tennis' }),
    );

    expect(await pill('Tennis')).toBeTruthy();
    expect(screen.queryByTestId('sport-bar')).toBeNull();
    expect(await screen.findByText(/once 2 who play tennis are in/)).toBeTruthy();
  });

  describe('open, against the group’s tile', () => {
    // An iPhone's width: the bar's right end is the gutter less its inset, the tile at the lead.
    const HEADER = 393;
    const TILE = { x: 32, width: 36 };
    const RIGHT_END = HEADER - (theme.size.gutter - theme.size.groupPage.filterPad);

    async function openBarOver(rowWidth: number): Promise<number | undefined> {
      stubAPlayer([BADMINTON, SQUASH, PADEL, TENNIS]);
      await openGroup();
      // The header draws its tile and its pill once the group is read.
      const closed = await pill('Padel');
      fireEvent(screen.getByTestId('sport-filter-header'), 'layout', {
        nativeEvent: { layout: { x: 0, y: 0, width: HEADER, height: 66 } },
      });
      fireEvent(
        screen.getByTestId('sport-filter-cover', { includeHiddenElements: true }),
        'layout',
        {
          nativeEvent: { layout: { x: TILE.x, y: 15, width: TILE.width, height: 36 } },
        },
      );
      fireEvent.press(closed);
      const bar = await screen.findByTestId('sport-bar');
      fireEvent(within(bar).getByRole('button', { name: 'Padel' }), 'layout', {
        nativeEvent: { layout: { x: 0, y: 0, width: 80, height: 27 } },
      });
      fireEvent(screen.getByTestId('sport-bar-row'), 'layout', {
        nativeEvent: { layout: { x: 0, y: 0, width: rowWidth, height: 27 } },
      });
      act(() => jest.advanceTimersByTime(theme.motion.unfold + 16));
      return (getAnimatedStyle(screen.getByTestId('sport-bar')) as { width?: number }).width;
    }

    // #529 E2: the tile's edge showed past the open bar's end.
    it('covers the tile whole, stopping short of the back arrow, once the sports reach it', async () => {
      const pad = theme.size.groupPage.filterPad;
      // The sports alone would end 19 points into the tile.
      expect(await openBarOver(RIGHT_END - (TILE.x + 17) - 2 * pad)).toBe(
        RIGHT_END - (TILE.x - theme.space.xs),
      );
    });

    it('ends where the sports end when they stop short of the tile', async () => {
      expect(await openBarOver(150)).toBe(150 + 2 * theme.size.groupPage.filterPad);
    });
  });

  it('folds without changing anything when the player taps elsewhere', async () => {
    await openGroup();
    await unfold('Padel');

    fireEvent.press(screen.getByTestId('sport-filter-backdrop', { includeHiddenElements: true }));

    expect(await pill('Padel')).toBeTruthy();
    expect(screen.queryByTestId('sport-bar')).toBeNull();
    expect(screen.getByText(/once 4 who play padel are in/)).toBeTruthy();
  });

  it('folds without changing anything when the current sport is tapped', async () => {
    await openGroup();
    await unfold('Padel');

    fireEvent.press(within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Padel' }));

    expect(await pill('Padel')).toBeTruthy();
    expect(screen.queryByTestId('sport-bar')).toBeNull();
  });

  it('is folded again when the player comes back to the page', async () => {
    await openGroup();
    await unfold('Padel');

    act(() => router.push('/play/join'));
    await waitFor(() => expect(screen).toHavePathname('/play/join'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${MY_RAKETA_GROUP.id}`));

    expect(await pill('Padel')).toBeTruthy();
    expect(screen.queryByTestId('sport-bar')).toBeNull();
  });

  it('is a plain label, with nothing to unfold, for a player rated in one sport', async () => {
    stubAPlayer([TENNIS]);
    await openGroup();

    const label = await screen.findByLabelText('Sport: Tennis');
    expect(screen.queryByRole('button', { name: 'Sport: Tennis' })).toBeNull();
    expect(within(label).getByText('Tennis')).toBeTruthy();
    expect(
      within(label).queryByText(COPY.filter.unfold, { includeHiddenElements: true }),
    ).toBeNull();
  });

  it('opens every group on the sport last picked, even after the app is closed', async () => {
    await openGroups(
      [MY_RAKETA_GROUP, pageOf(MY_RAKETA_GROUP)],
      [KAZIMIERZ_CREW, pageOf(KAZIMIERZ_CREW)],
    );
    await enter(MY_RAKETA_GROUP);
    await unfold('Padel');
    fireEvent.press(
      within(screen.getByTestId('sport-bar')).getByRole('button', { name: 'Tennis' }),
    );
    expect(await pill('Tennis')).toBeTruthy();

    await relaunch();
    await enter(KAZIMIERZ_CREW);

    expect(await pill('Tennis')).toBeTruthy();
  });

  // ADR-0188 §4: a sport the player is no longer rated in falls back to the default.
  it('opens on the first rated sport when the one last picked is no longer rated', async () => {
    await savePhonePreference(GATE_USER.id, 'lastSport', 'squash');

    await openGroup();

    expect(await pill('Padel')).toBeTruthy();
  });
});

describe('the tab bar', () => {
  it('is Games · Fill in · Friends · Info, with no counts, and opens on Games', async () => {
    await openGroup();

    expect(await tab('Games', true)).toBeTruthy();
    expect(await tab('Fill in', false)).toBeTruthy();
    expect(await tab('Friends', false)).toBeTruthy();
    expect(await tab('Info', false)).toBeTruthy();
  });
});

describe('Games', () => {
  it.each([
    ['Padel', [PADEL], 4, 3],
    ['Tennis', [TENNIS], 2, 1],
    ['Squash', [SQUASH], 2, 1],
    ['Badminton', [BADMINTON], 4, 3],
  ] as const)(
    'is just you so far on %s — your face and the seats still empty',
    async (sport, ratings, seats, empty) => {
      stubAPlayer(ratings);
      await openGroup();

      expect(await screen.findByText(COPY.games.justYou)).toBeTruthy();
      expect(faces().map((face) => face.props.testID)).toEqual([`games-face-${GATE_USER.id}`]);
      expect(emptyGamesSeats()).toHaveLength(empty);
      expect(screen.getByLabelText(`${sport}, 1 of ${seats} seats filled.`)).toBeTruthy();
      expect(
        screen.getByText(
          `The app picks games here once ${seats} who play ${sport.toLowerCase()} are in and a court at Bonarka Arena is free. Send the link — it all starts when they arrive.`,
        ),
      ).toBeTruthy();
    },
  );

  it('counts the ones who play the sport against the seats, their faces in joining order', async () => {
    await openGroup(
      MY_RAKETA_GROUP,
      pageOf(MY_RAKETA_GROUP, {
        member_count: 4,
        rated_by_sport: [roster('PADEL', 3, [TOMEK, member(2), member(3)]), roster('TENNIS', 1)],
      }),
    );

    expect(await screen.findByText('3 of 4')).toBeTruthy();
    expect(faces().map((face) => face.props.testID)).toEqual([
      `games-face-${GATE_USER.id}`,
      `games-face-${member(2).player_id}`,
      `games-face-${member(3).player_id}`,
    ]);
    expect(emptyGamesSeats()).toHaveLength(1);
    expect(screen.getByText(/once 4 who play padel are in/)).toBeTruthy();
  });

  it('says nothing is picked once the seats could be filled', async () => {
    await openGroup(
      MY_RAKETA_GROUP,
      pageOf(MY_RAKETA_GROUP, {
        member_count: 6,
        rated_by_sport: [
          roster('PADEL', 5, [TOMEK, member(2), member(3), member(4)]),
          roster('TENNIS', 1),
        ],
      }),
    );

    expect(await screen.findByText(COPY.games.nothingPicked)).toBeTruthy();
    expect(faces()).toHaveLength(4);
    expect(emptyGamesSeats()).toHaveLength(0);
    // The seats are there; what the app is waiting for is not people.
    expect(screen.queryByText(/who play padel are in/)).toBeNull();
  });

  it('opens the share sheet with the group link', async () => {
    await openGroup();

    fireEvent.press(await screen.findByRole('button', { name: COPY.link.share }));

    await waitFor(() => expect(share.shared).toEqual([`Join my raketa group on Raketa: ${LINK}`]));
  });

  it('copies the link, and says so', async () => {
    await openGroup();

    fireEvent.press(await screen.findByRole('button', { name: COPY.link.copy }));

    await waitFor(() => expect(clipboard.text).toBe(LINK));
    await waitFor(() =>
      expect(useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone])).toEqual([
        [COPY.link.copied, 'ok'],
      ]),
    );
  });

  it('says so when the phone would not take the link', async () => {
    clipboard.writable = false;
    await openGroup();

    fireEvent.press(await screen.findByRole('button', { name: COPY.link.copy }));

    await waitFor(() =>
      expect(useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone])).toEqual([
        [COPY.link.notCopied, 'bad'],
      ]),
    );
  });
});

describe('Fill in', () => {
  it('is just you while nobody else has joined, with the link and the button to come', async () => {
    await openGroup();

    await openTab('Fill in');

    expect(await screen.findByText('No games yet — it’s just you')).toBeTruthy();
    expect(
      screen.getByText(
        'Post the first game and it is the first thing people see when they arrive with the link. Or send the link and let somebody else post.',
      ),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.link.share })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.link.copy })).toBeTruthy();
    // Drawn, and inert: nobody can post a game yet.
    expect(
      screen.getByRole('button', { name: COPY.fillIn.postAGame, disabled: true }),
    ).toBeTruthy();
  });

  it('drops “just you” once others have joined', async () => {
    await openGroup(MY_RAKETA_GROUP, pageOf(MY_RAKETA_GROUP, { member_count: 3 }));

    await openTab('Fill in');

    expect(await screen.findByText('No games yet')).toBeTruthy();
    expect(screen.queryByText('No games yet — it’s just you')).toBeNull();
  });

  it('shares the link from here too', async () => {
    await openGroup();
    await openTab('Fill in');

    fireEvent.press(await screen.findByRole('button', { name: COPY.link.share }));

    await waitFor(() => expect(share.shared).toHaveLength(1));
  });
});

describe('Friends', () => {
  const emptySeats = () => screen.queryAllByRole('button', { name: /, empty$/ });

  it('switches between Competitive and For fun, and keeps the switch while the app is open', async () => {
    await openGroup();
    await openTab('Friends');
    expect(await tab(COPY.friends.competitive, true)).toBeTruthy();

    fireEvent.press(await tab(COPY.friends.forFun, false));
    expect(await tab(COPY.friends.forFun, true)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.group.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    await enter(MY_RAKETA_GROUP);
    await openTab('Friends');

    expect(await tab(COPY.friends.forFun, true)).toBeTruthy();
  });

  it.each([
    ['Padel', [PADEL], '2,71', 4, true],
    ['Tennis', [TENNIS], '3,10', 2, false],
    ['Squash', [SQUASH], '2,30', 2, false],
    ['Badminton', [BADMINTON], '2,05', 4, true],
  ] as const)(
    'draws the %s court — you, your level, and a + on every empty seat',
    async (sport, ratings, level, seats, sides) => {
      stubAPlayer(ratings);
      await openGroup();

      await openTab('Friends');

      expect(await screen.findByLabelText(`${sport}, 1 of ${seats} seats filled.`)).toBeTruthy();
      // The seat is spoken whole, and drawn as its three letters over the Level (play 50).
      const you = screen.getByLabelText(`Your side, you, level ${level}`);
      expect(within(you).getByText(COPY.friends.you, { includeHiddenElements: true })).toBeTruthy();
      expect(within(you).getByText(level, { includeHiddenElements: true })).toBeTruthy();
      expect(emptySeats()).toHaveLength(seats - 1);
      expect(
        screen.queryAllByText(COPY.friends.theirSide, { includeHiddenElements: true }),
      ).toHaveLength(sides ? 1 : 0);
    },
  );

  it('names every empty seat by where it is on the court', async () => {
    await openGroup();

    await openTab('Friends');

    await screen.findByLabelText('Padel, 1 of 4 seats filled.');
    expect(emptySeats().map((seat) => seat.props.accessibilityLabel)).toEqual([
      'Your side, your partner, empty',
      'Their side, empty',
      'Their side, empty',
    ]);
  });

  it('draws your own photograph when you joined after a court’s worth of players', async () => {
    const photo = 'https://photos.test/tomek.jpg';
    stubOwnRecord(transport, { ...OWN_RECORD_SERVED, photo_id: 'f1', photo_url: photo });
    await openGroup(
      MY_RAKETA_GROUP,
      pageOf(MY_RAKETA_GROUP, {
        member_count: 6,
        rated_by_sport: [
          roster('PADEL', 5, [member(2), member(3), member(4), member(5)]),
          roster('TENNIS', 1),
        ],
      }),
    );

    await openTab('Friends');

    const you = await screen.findByLabelText('Your side, you, level 2,71');
    await waitFor(() =>
      expect(
        within(you).queryByLabelText(POSTER_LABEL, { includeHiddenElements: true }),
      ).toBeNull(),
    );
  });

  it('opens Friends from an empty seat — the sport, how many are picked, and nobody yet', async () => {
    await openGroup();
    await openTab('Friends');

    fireEvent.press((await screen.findAllByRole('button', { name: /, empty$/ }))[0]!);

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${MY_RAKETA_GROUP.id}/friends`));
    expect(await screen.findByRole('header', { name: COPY.friends.title })).toBeTruthy();
    expect(screen.getByText('Padel · 0 of 3 picked')).toBeTruthy();
    expect(screen.getByText(COPY.friends.nobody)).toBeTruthy();
    expect(
      screen.getByText('Friends who join my raketa group with the link show up on this page.'),
    ).toBeTruthy();
  });

  it('opens Friends from + Friends, for the sport on the court', async () => {
    stubAPlayer([TENNIS]);
    await openGroup();
    await openTab('Friends');

    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));

    expect(await screen.findByRole('header', { name: COPY.friends.title })).toBeTruthy();
    expect(screen.getByText('Tennis · 0 of 1 picked')).toBeTruthy();
  });

  it('shares and copies the link from Friends, and goes back to the court', async () => {
    await openGroup();
    await openTab('Friends');
    fireEvent.press(await screen.findByRole('button', { name: COPY.friends.addFriendsLabel }));
    await screen.findByText(COPY.friends.nobody);

    fireEvent.press(screen.getByRole('button', { name: COPY.link.share }));
    await waitFor(() => expect(share.shared).toEqual([`Join my raketa group on Raketa: ${LINK}`]));
    fireEvent.press(screen.getByRole('button', { name: COPY.link.copy }));
    await waitFor(() => expect(clipboard.text).toBe(LINK));

    fireEvent.press(screen.getByRole('button', { name: COPY.friends.back }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${MY_RAKETA_GROUP.id}`));
    expect(await tab('Friends', true)).toBeTruthy();
  });
});
