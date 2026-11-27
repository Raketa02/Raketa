/**
 * **Groups heating up on Home** — FOR YOU's first line, walked through the real route tree
 * ([#800](https://github.com/Raketa02/Raketa/issues/800), PRD #789; [#820](https://github.com/Raketa02/Raketa/issues/820);
 * ADR-0204 §3, ADR-0205 §5; the Home rows screens §3; the mechanics §5; the words §31.1–§31.4).
 *
 * - **The line**: first under FOR YOU, just below *Your games*, closed; open, its cards and *All
 *   groups ›* at the foot (#823 — the page is `hottestGroupsPage.test.tsx`);
 *   hidden while the read is empty or failed, and closed and gone when it empties while open.
 * - **The card**: the tag, the figures, the growth, the faces, and the chip for each relation.
 * - **The chip's taps**: Join → *You're in* at once; Ask to join → *Asked*; Asked → the withdraw
 *   sheet; You're in → the group's page. A refusal puts the chip back and says why.
 * - **The group sheet**: its title and one button, the identity line, the two stat cards, the faces
 *   (not buttons) and the friends line.
 * - **Withdraw**: *Waiting for Ogrody 33 to answer* · **Withdraw request**, and the card asks again.
 * - **A reader in no group**: the groupless line under *Your games*, and the line open from the start.
 *
 * **The routes are answered by a small fake of the server** (`hottestServer`): a join admits or asks
 * by the group's policy and a withdraw takes the request back, so what the line draws after a write is
 * the line read again, never this client guessing — the guess is only what the chip says before the
 * answer lands.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { RefreshControl, StyleSheet, type ViewStyle } from 'react-native';

import { HOME_COPY } from '@/features/shell/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import { footerParts, lineNamed, lineTitles, openLine } from '@/test-support/forYou';
import { markerAtRest, markerCentre, markerUnder, slideFromNow } from '@/test-support/tabBarReach';
import {
  HOME_PATH,
  HOTTEST_GROUPS_PATH,
  MY_GROUPS_PATH,
  launchSignedIn,
  stubGate,
  stubHottestGroups,
  stubMyGroups,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from './groupsCopy';
import { hottestChipLabel } from './groupsPresentation';
import { hottestCardHeight } from './HottestGroupCard';
import { SportDots } from './SportDots';

const HOT = GROUPS_COPY.hottest;

/** The band, the tag, the bar and the card's faces are pictures, hidden from a listener on purpose. */
const HIDDEN = { includeHiddenElements: true } as const;

const face = (n: number, nickname: string): Wire['GroupPersonSchema'] => ({
  player_id: `f0000000-0000-4000-8000-0000000008${String(n).padStart(2, '0')}`,
  nickname,
});

const SIX_FACES = [
  face(1, 'kuba.w'),
  face(2, 'ola.n'),
  face(3, 'zofia.b'),
  face(4, 'ania.k'),
  face(5, 'marek.z'),
  face(6, 'monika.p'),
];

/** Ogrody 33 Club — HOTTEST, official, People I approve: *Ask to join*. */
const OGRODY: Wire['HottestGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000801',
  kind: 'OFFICIAL',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  sports: ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'],
  member_count: 11,
  join_policy: 'PEOPLE_I_APPROVE',
  run_by: 'Ogrody 33',
  club: { id: 'c0000000-0000-4000-8000-000000000801', name: 'Ogrody 33' },
  games_this_week: 14,
  new_this_month: 3,
  heat_share: 1,
  tag: 'HOTTEST',
  faces: SIX_FACES,
  friends_count: 7,
  relation: 'NONE',
  is_administrator: false,
};

/** Kazimierz crew — GROWING, and the reader is in it: *You're in*. */
const KAZIMIERZ: Wire['HottestGroupSchema'] = {
  ...OGRODY,
  id: 'a0000000-0000-4000-8000-000000000802',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 10,
  join_policy: 'PEOPLE_I_APPROVE',
  run_by: 'tomek.k',
  club: { id: 'c0000000-0000-4000-8000-000000000802', name: 'Kazimierz Padel' },
  games_this_week: 11,
  new_this_month: 4,
  heat_share: 44 / 48,
  tag: 'GROWING',
  faces: SIX_FACES.slice(0, 4),
  friends_count: 1,
  relation: 'MEMBER',
};

/** Podgórze tennis ladder — no tag, Anyone, no growth, one game: *Join*. */
const PODGORZE: Wire['HottestGroupSchema'] = {
  ...OGRODY,
  id: 'a0000000-0000-4000-8000-000000000803',
  kind: 'PLAYER',
  name: 'Podgórze tennis ladder',
  monogram: { letters: 'Pt', colour: 5 },
  sports: ['TENNIS'],
  member_count: 3,
  join_policy: 'ANYONE',
  run_by: 'bartek.l',
  games_this_week: 1,
  new_this_month: 0,
  heat_share: 0.4,
  tag: null,
  faces: SIX_FACES.slice(0, 2),
  friends_count: 0,
};

const KAZIMIERZ_MINE: Wire['MyGroupSchema'] = {
  id: KAZIMIERZ.id,
  kind: 'PLAYER',
  name: KAZIMIERZ.name,
  monogram: KAZIMIERZ.monogram,
  sports: KAZIMIERZ.sports,
  member_count: KAZIMIERZ.member_count,
  home_club: KAZIMIERZ.club,
};

const membershipPath = (id: string) => `/api/v1/groups/${id}/membership`;
const joinRequestPath = (id: string) => `/api/v1/groups/${id}/join-request`;

let transport: Transport;

/**
 * **The row's routes, faked** — a join admits an Anyone group (and grows it by one) and leaves a
 * request on a People I approve one; a withdraw takes the request back. `refuse` makes the next join
 * fail with that code. The row's total is the groups served, or what `total` says at each read (#822).
 */
function hottestServer(
  initially: readonly Wire['HottestGroupSchema'][],
  {
    mine = [KAZIMIERZ_MINE],
    total,
  }: { readonly mine?: readonly Wire['MyGroupSchema'][]; readonly total?: () => number } = {},
) {
  let groups = [...initially];
  let refusal: string | undefined;
  let held: Promise<void> | undefined;

  stubGate(transport, { hasPlayerProfile: true });
  stubMyGroups(transport, mine);
  transport.on('GET', HOTTEST_GROUPS_PATH, () =>
    json<Wire['HottestGroupsResponse']>({
      groups: [...groups],
      total: total?.() ?? groups.length,
    }),
  );

  for (const group of initially) {
    transport.on('POST', membershipPath(group.id), async () => {
      if (held !== undefined) await held;
      if (refusal !== undefined) {
        const code = refusal;
        refusal = undefined;
        return errorResponse(409, code);
      }
      const now = groups.find((each) => each.id === group.id) ?? group;
      const admits = now.join_policy === 'ANYONE' || now.is_administrator;
      const answered: Wire['HottestGroupSchema'] = admits
        ? { ...now, relation: 'MEMBER', member_count: now.member_count + 1 }
        : { ...now, relation: 'REQUESTED' };
      groups = groups.map((each) => (each.id === group.id ? answered : each));
      return json<Wire['GroupAtClubSchema']>({
        id: answered.id,
        kind: answered.kind,
        name: answered.name,
        monogram: answered.monogram,
        sports: answered.sports,
        member_count: answered.member_count,
        join_policy: answered.join_policy,
        owner_nickname: answered.kind === 'PLAYER' ? answered.run_by : null,
        administrator_nickname: null,
        is_administrator: answered.is_administrator,
        relation: answered.relation,
      });
    });
    transport.on('DELETE', joinRequestPath(group.id), () => {
      groups = groups.map((each) =>
        each.id === group.id && each.relation === 'REQUESTED'
          ? { ...each, relation: 'NONE' }
          : each,
      );
      return noContent();
    });
    transport.on('GET', `/api/v1/groups/${group.id}`, () => errorResponse(404, 'group_not_found'));
  }

  return {
    refuseNextJoin: (code: string) => {
      refusal = code;
    },
    /** Joins wait for the returned release — so a suite can look at the chip before the answer. */
    holdJoins: () => {
      let release: () => void = () => {};
      held = new Promise<void>((resolve) => {
        release = resolve;
      });
      return release;
    },
  };
}

beforeEach(() => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  resetSessionStatus();
  await clearStoredTokens();
});

const card = (group: Wire['HottestGroupSchema']) =>
  screen.getByRole('button', { name: new RegExp(`^${group.name},`) });
const chip = (group: Wire['HottestGroupSchema'], action: 'join' | 'ask' | 'requested' | 'in') =>
  screen.findByRole('button', { name: hottestChipLabel(action, group.name) });
const reads = (path: string) => transport.requestsTo('GET', path).length;
/** The card's two figures, left to right, by what they count. */
const figureRow = (group: Wire['HottestGroupSchema']) =>
  within(screen.getByTestId(`hottest-${group.id}`))
    .getAllByTestId(/^hottest-(games|players)$/)
    .map((node) => node.props.testID as string);
const alignOf = (node: { readonly props: { readonly style?: unknown } }) =>
  StyleSheet.flatten(node.props.style as ViewStyle).alignItems;
const sheet = () => within(screen.getByTestId('bottom-sheet'));
const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

/** The section headings Home draws, top to bottom. */
const headings = () =>
  screen
    .getAllByRole('header')
    .map((node) => node.props.children as string)
    .filter((text) => typeof text === 'string');

const line = () => screen.findByRole('button', { name: lineNamed(HOT.line) });

describe('the line on Home', () => {
  /** ADR-0205 §5: FOR YOU just below *Your games*, Groups heating up its first line, closed. */
  it('stands first under FOR YOU, just below Your games, closed and drawing no card', async () => {
    hottestServer([OGRODY, KAZIMIERZ, PODGORZE]);
    await launchSignedIn();

    expect((await line()).props.accessibilityState).toEqual({ expanded: false });
    const order = headings();
    const games = order.findIndex((text) => text.startsWith('Your games'));
    expect(games).toBeGreaterThanOrEqual(0);
    expect(order[games + 1]).toBe(HOME_COPY.forYou);
    expect(lineTitles()[0]).toBe(HOT.line);
    expect(screen.queryByTestId(`hottest-${OGRODY.id}`)).toBeNull();
  });

  /** #823: *All groups ›* at the foot, alone at its right end — the page is its own suite. */
  it('opens onto the cards in the read’s order, All groups › at the foot', async () => {
    hottestServer([OGRODY, KAZIMIERZ, PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    // In what the line holds: its header's name has a comma too, before its count (#822).
    const names = within(screen.getByTestId('hottest-groups-content'))
      .getAllByRole('button', { name: /,/ })
      .map((node) => node.props.accessibilityLabel as string);
    expect(names.map((label) => label.split(',')[0])).toEqual([
      OGRODY.name,
      KAZIMIERZ.name,
      PODGORZE.name,
    ]);
    const footer = within(screen.getByTestId('hottest-groups')).getByTestId('folding-line-footer');
    expect(footerParts(footer, () => 'something else')).toEqual(['link']);
    const link = within(footer).getByRole('link', { name: HOT.allGroupsLabel });
    expect(within(link).getByText(HOT.allGroups)).toBeTruthy();
  });

  it('is hidden while the read holds nothing', async () => {
    hottestServer([]);
    await launchSignedIn();

    await waitFor(() => expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(0));
    await screen.findByText(/^Your games/);
    expect(screen.queryByRole('button', { name: lineNamed(HOT.line) })).toBeNull();
  });

  it('is left out when its read fails, and the rest of Home stands', async () => {
    hottestServer([OGRODY]);
    transport.on('GET', HOTTEST_GROUPS_PATH, () => errorResponse(500, 'internal_error'));
    await launchSignedIn();

    await waitFor(() => expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(0));
    expect(await screen.findByText(/^Your games/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: lineNamed(HOT.line) })).toBeNull();
  });

  /** Q21: a line that empties while open closes and goes — and comes back closed. */
  it('closes and goes when it empties while open, and comes back closed', async () => {
    hottestServer([OGRODY]);
    await launchSignedIn();
    await openLine(HOT.line);

    stubHottestGroups(transport, []);
    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: lineNamed(HOT.line) })).toBeNull(),
    );

    stubHottestGroups(transport, [OGRODY]);
    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });
    expect((await line()).props.accessibilityState).toEqual({ expanded: false });
  });
});

describe('the card', () => {
  /** Home refactor 5.1 (#821): the band, the tag, the shield, the name, two figures, faces, the chip. */
  it('draws the tag, N games this week on the left, N players on the right, and four faces', async () => {
    hottestServer([OGRODY, KAZIMIERZ, PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    const ogrody = within(screen.getByTestId(`hottest-${OGRODY.id}`));
    expect(ogrody.getByText(OGRODY.name)).toBeTruthy();
    // The shield's monogram, a picture of the group and hidden from a listener.
    expect(ogrody.getByText(OGRODY.monogram.letters, HIDDEN)).toBeTruthy();
    const games = within(ogrody.getByTestId('hottest-games'));
    expect(games.getByText('14')).toBeTruthy();
    expect(games.getByText('games this week')).toBeTruthy();
    const players = within(ogrody.getByTestId('hottest-players'));
    expect(players.getByText('11')).toBeTruthy();
    expect(players.getByText('players')).toBeTruthy();
    // Games on the left, the players held against the card's right edge.
    expect(figureRow(OGRODY)).toEqual(['hottest-games', 'hottest-players']);
    expect(alignOf(ogrody.getByTestId('hottest-players'))).toBe('flex-end');
    expect(screen.getByTestId('hottest-tag-HOTTEST', HIDDEN)).toBeTruthy();
    expect(screen.getByTestId('hottest-tag-GROWING', HIDDEN)).toBeTruthy();
    // Four of the six faces on the card; the sheet draws the six.
    expect(screen.getAllByTestId(new RegExp(`^hottest-face-${OGRODY.id}-`), HIDDEN)).toHaveLength(
      4,
    );
    // Spoken as drawn: no growth, which the card no longer carries.
    expect(card(OGRODY).props.accessibilityLabel).toBe(
      'Ogrody 33 Club, hottest, 14 games this week, 11 players',
    );
  });

  /**
   * 2026-11-26: on the line the card is `lineCardRatio` of the line's content, a little wider than the
   * page's 0,74, and keeps its shape — every vertical gap grows by the width's factor onto the 3pt
   * grid, so it stands as much taller as it stands wider, as near as the grid comes: within half a
   * step. The page keeps its own.
   */
  it('stands as much taller on the line as it stands wider, through its gaps alone', async () => {
    hottestServer([OGRODY, KAZIMIERZ, PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    const gapOf = (testID: string) =>
      StyleSheet.flatten(
        within(screen.getByTestId(`hottest-${OGRODY.id}`)).getByTestId(testID).props
          .style as ViewStyle,
      ).gap;
    // A number over its words, 3 apart on the page: 6 on the line.
    expect(gapOf('hottest-games')).toBe(theme.space.xs);

    const grown = theme.size.lineCardRatio / theme.size.railCardRatio;
    const page = hottestCardHeight(1, 'page');
    expect(Math.abs(hottestCardHeight(1, 'row') - page * grown)).toBeLessThanOrEqual(
      theme.space.xxs / 2,
    );
    expect(hottestCardHeight(1, 'row')).toBeGreaterThan(page);
  });

  /** ADR-0205 §5, Q22: the heat bar, *+N this month* and the sport line leave the card. */
  it('draws no heat bar, no +N this month and no sport line — dots or names', async () => {
    hottestServer([OGRODY, KAZIMIERZ]);
    await launchSignedIn();
    await openLine(HOT.line);

    for (const group of [OGRODY, KAZIMIERZ]) {
      const drawn = within(screen.getByTestId(`hottest-${group.id}`));
      expect(drawn.queryByText(/^\+\d/, HIDDEN)).toBeNull();
      expect(drawn.queryByText(/this month/, HIDDEN)).toBeNull();
      expect(drawn.queryByText(/Padel|Tennis/, HIDDEN)).toBeNull();
    }
    expect(screen.UNSAFE_queryAllByType(SportDots)).toHaveLength(0);
    expect(screen.queryByTestId('heat-bar', HIDDEN)).toBeNull();
    expect(screen.queryByTestId('heat-fill', HIDDEN)).toBeNull();
  });

  it('writes one game in the singular, and no tag on an untagged card', async () => {
    hottestServer([PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    const podgorze = within(await screen.findByTestId(`hottest-${PODGORZE.id}`));
    expect(podgorze.getByText('game this week')).toBeTruthy();
    expect(screen.queryByTestId('hottest-tag-HOTTEST', HIDDEN)).toBeNull();
    expect(screen.queryByTestId('hottest-tag-GROWING', HIDDEN)).toBeNull();
    // A three-member group draws the faces it has.
    expect(screen.getAllByTestId(new RegExp(`^hottest-face-${PODGORZE.id}-`), HIDDEN)).toHaveLength(
      2,
    );
  });

  it('offers each relation its chip', async () => {
    hottestServer([
      OGRODY,
      KAZIMIERZ,
      PODGORZE,
      {
        ...OGRODY,
        id: 'a0000000-0000-4000-8000-000000000804',
        name: 'Asked crew',
        tag: null,
        relation: 'REQUESTED',
      },
    ]);
    await launchSignedIn();
    await openLine(HOT.line);

    expect(await chip(OGRODY, 'ask')).toBeTruthy();
    expect(await chip(KAZIMIERZ, 'in')).toBeTruthy();
    expect(await chip(PODGORZE, 'join')).toBeTruthy();
    expect(
      await screen.findByRole('button', { name: hottestChipLabel('requested', 'Asked crew') }),
    ).toBeTruthy();
  });

  // The mechanics §5.7: an Administrator who runs an official group joins it directly.
  it('offers Join to the Administrator who runs a People I approve group', async () => {
    hottestServer([{ ...OGRODY, is_administrator: true }]);
    await launchSignedIn();
    await openLine(HOT.line);

    expect(await chip(OGRODY, 'join')).toBeTruthy();
  });
});

describe('the chip', () => {
  it('Join makes the reader a member at once, and the row, the list and Home are read again', async () => {
    const server = hottestServer([OGRODY, PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);
    await waitFor(() => expect(reads(MY_GROUPS_PATH)).toBeGreaterThan(0));
    const before = {
      hottest: reads(HOTTEST_GROUPS_PATH),
      mine: reads(MY_GROUPS_PATH),
      home: reads(HOME_PATH),
    };
    const release = server.holdJoins();

    fireEvent.press(await chip(PODGORZE, 'join'));

    // Before the server has answered.
    expect(await chip(PODGORZE, 'in')).toBeTruthy();
    expect(reads(HOTTEST_GROUPS_PATH)).toBe(before.hottest);
    await act(async () => release());

    await waitFor(() => {
      expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(before.hottest);
      expect(reads(MY_GROUPS_PATH)).toBeGreaterThan(before.mine);
      expect(reads(HOME_PATH)).toBeGreaterThan(before.home);
    });
    // The re-read is drawn: one more player.
    expect(await within(screen.getByTestId(`hottest-${PODGORZE.id}`)).findByText('4')).toBeTruthy();
    expect(await chip(PODGORZE, 'in')).toBeTruthy();
  });

  /** #822: the count is the server's — the join's re-read moves it, never the card's guess. */
  it('moves the line’s count with the re-read a join asks for, and not before', async () => {
    let pool = 12;
    const server = hottestServer([OGRODY, PODGORZE], { total: () => pool });
    await launchSignedIn();
    await openLine(HOT.line);
    const named = (count: number) => ({ name: `${HOT.line}, ${count}`, expanded: true });
    expect(screen.getByRole('button', named(12))).toBeTruthy();
    const release = server.holdJoins();
    pool = 13;

    fireEvent.press(await chip(PODGORZE, 'join'));

    expect(await chip(PODGORZE, 'in')).toBeTruthy();
    expect(screen.getByRole('button', named(12))).toBeTruthy();
    await act(async () => release());
    expect(await screen.findByRole('button', named(13))).toBeTruthy();
  });

  it('Ask to join leaves a request at once: Asked', async () => {
    hottestServer([OGRODY]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await chip(OGRODY, 'ask'));

    expect(await chip(OGRODY, 'requested')).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('POST', membershipPath(OGRODY.id))).toHaveLength(1),
    );
  });

  it('a refused join puts the chip back and says why', async () => {
    const server = hottestServer([PODGORZE]);
    server.refuseNextJoin('group_not_found');
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await chip(PODGORZE, 'join'));

    expect(await chip(PODGORZE, 'join')).toBeTruthy();
    await waitFor(() => expect(toasts()).toHaveLength(1));
    expect(toasts()[0]?.[1]).toBe('bad');
  });

  /**
   * #822: the guess cancelled any read in flight — a pull's, a return's — so a refusal reads the row
   * again, or its cards and its count would stand as they were before that read.
   */
  it('a refused join reads the row again, so a read the guess cancelled is not lost', async () => {
    let pool = 12;
    const server = hottestServer([PODGORZE], { total: () => pool });
    server.refuseNextJoin('group_not_found');
    await launchSignedIn();
    await openLine(HOT.line);
    const before = reads(HOTTEST_GROUPS_PATH);
    pool = 13;

    fireEvent.press(await chip(PODGORZE, 'join'));

    await waitFor(() => expect(toasts()).toHaveLength(1));
    await waitFor(() => expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(before));
    expect(
      await screen.findByRole('button', { name: `${HOT.line}, 13`, expanded: true }),
    ).toBeTruthy();
  });

  it('Asked opens the withdraw sheet, and Withdraw request turns the card back to Ask to join', async () => {
    hottestServer([{ ...OGRODY, relation: 'REQUESTED' }]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await chip(OGRODY, 'requested'));

    expect(
      await screen.findByRole('header', { name: 'Waiting for Ogrody 33 to answer' }),
    ).toBeTruthy();
    fireEvent.press(sheet().getByRole('button', { name: HOT.withdraw }));

    expect(await chip(OGRODY, 'ask')).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('DELETE', joinRequestPath(OGRODY.id))).toHaveLength(1),
    );
    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());
    // Nothing is said: withdrawing tells nobody, the reader included.
    expect(toasts()).toEqual([]);
  });

  it('You’re in opens the group’s page', async () => {
    hottestServer([KAZIMIERZ]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await chip(KAZIMIERZ, 'in'));

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${KAZIMIERZ.id}`));
  });

  /**
   * **The group lives under Play** (`/play/group/{id}`), so opening it from Home lights Play, and the
   * selection marker travels there — and back home with the page (ADR-0210 §8, #884). Each slide
   * starts on the frame after its navigation, whose own flush ran every pending timer.
   */
  it('You’re in carries the selection marker from Home to Play, and back takes it home', async () => {
    const slide = theme.motion.tabMarker.slide;
    hottestServer([KAZIMIERZ]);
    await launchSignedIn();
    await openLine(HOT.line);
    expect(markerUnder()).toBe('Home');

    fireEvent.press(await chip(KAZIMIERZ, 'in'));
    const there = slideFromNow();
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${KAZIMIERZ.id}`));
    there(60);
    expect(markerUnder()).toBeUndefined();
    expect(markerCentre()).toBeGreaterThan(0.5);
    there(60 + slide);
    expect(markerUnder()).toBe('Play');
    expect(markerAtRest()).toBe(true);

    act(() => router.back());
    const back = slideFromNow();
    await waitFor(() => expect(screen).toHavePathname('/'));
    back(60);
    expect(markerUnder()).toBeUndefined();
    expect(markerCentre()).toBeLessThan(1.5);
    back(60 + slide);
    expect(markerUnder()).toBe('Home');
    expect(markerAtRest()).toBe(true);
  });
});

describe('the group sheet', () => {
  /**
   * Unchanged by the card's slimming (#821, ADR-0205 §5): the sheet keeps the sports, dots and names,
   * and *new this month* with its *+3*, which the card no longer draws.
   */
  it('opens on a tap on the card, with every one of the group’s fields and its one button', async () => {
    hottestServer([OGRODY, KAZIMIERZ]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${OGRODY.name},`) }));

    expect(await screen.findByRole('header', { name: OGRODY.name })).toBeTruthy();
    const opened = sheet();
    expect(opened.getByRole('button', { name: hottestChipLabel('ask', OGRODY.name) })).toBeTruthy();
    expect(opened.getByText('Closed group · run by Ogrody 33 · Ogrody 33')).toBeTruthy();
    expect(opened.getByText('Padel · Tennis · Squash · Badminton')).toBeTruthy();
    expect(opened.UNSAFE_getAllByType(SportDots)).toHaveLength(1);
    expect(opened.getByText('14')).toBeTruthy();
    expect(opened.getByText('games this week')).toBeTruthy();
    expect(opened.getByText('11')).toBeTruthy();
    expect(opened.getByText('+3')).toBeTruthy();
    expect(opened.getByText('players · new this month')).toBeTruthy();
    expect(opened.getByText('7 of your friends play here')).toBeTruthy();
    expect(opened.getAllByTestId(new RegExp(`^group-sheet-face-${OGRODY.id}-`))).toHaveLength(6);
    // The faces are a picture of the group: the button and the close are all that press.
    expect(opened.getAllByRole('button').map((node) => node.props.accessibilityLabel)).toEqual([
      hottestChipLabel('ask', OGRODY.name),
      `Close ${OGRODY.name}`,
    ]);
  });

  it('says one friend, or the players, and names a Player group’s Owner', async () => {
    hottestServer([KAZIMIERZ, PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${KAZIMIERZ.name},`) }));
    expect(await sheet().findByText('1 of your friends plays here')).toBeTruthy();
    expect(sheet().getByText('Closed group · run by tomek.k · Kazimierz Padel')).toBeTruthy();
    fireEvent.press(sheet().getByRole('button', { name: `Close ${KAZIMIERZ.name}` }));
    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());

    fireEvent.press(screen.getByRole('button', { name: new RegExp(`^${PODGORZE.name},`) }));
    expect(await sheet().findByText('3 players')).toBeTruthy();
    expect(sheet().getByText('Open group · run by bartek.l · Ogrody 33')).toBeTruthy();
  });

  it('Join on the sheet makes the reader a member, and the button opens the group', async () => {
    hottestServer([PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${PODGORZE.name},`) }));
    fireEvent.press(
      await sheet().findByRole('button', { name: hottestChipLabel('join', PODGORZE.name) }),
    );

    const open = await sheet().findByRole('button', { name: HOT.openGroup });
    fireEvent.press(open);

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${PODGORZE.id}`));
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
  });

  it('Asked on the sheet turns it into the withdraw sheet', async () => {
    hottestServer([{ ...OGRODY, relation: 'REQUESTED' }]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${OGRODY.name},`) }));
    fireEvent.press(
      await sheet().findByRole('button', { name: hottestChipLabel('requested', OGRODY.name) }),
    );

    expect(
      await screen.findByRole('header', { name: 'Waiting for Ogrody 33 to answer' }),
    ).toBeTruthy();
    expect(sheet().getByRole('button', { name: HOT.withdraw })).toBeTruthy();
  });
});

describe('a reader in no group', () => {
  /** Q38: joining a group is their next step, so the line just below says so and is open. */
  it('reads the groupless line under Your games, and finds Groups heating up open', async () => {
    hottestServer([OGRODY], { mine: [] });
    await launchSignedIn();

    expect(await screen.findByText(HOT.groupless)).toBeTruthy();
    expect(screen.queryByText('Play finds you one.')).toBeNull();
    expect(
      await screen.findByRole('button', { name: lineNamed(HOT.line), expanded: true }),
    ).toBeTruthy();
    expect(screen.getByTestId(`hottest-${OGRODY.id}`)).toBeTruthy();
  });

  it('keeps Play finds you one. for a member of a group, and every line closed', async () => {
    hottestServer([OGRODY]);
    await launchSignedIn();

    await waitFor(() => expect(reads(MY_GROUPS_PATH)).toBeGreaterThan(0));
    expect(await screen.findByText('Play finds you one.')).toBeTruthy();
    expect(screen.queryByText(HOT.groupless)).toBeNull();
    expect((await line()).props.accessibilityState).toEqual({ expanded: false });
  });

  it('turns to Play finds you one. once a join from the line makes them a member — the line kept open', async () => {
    hottestServer([PODGORZE], { mine: [] });
    await launchSignedIn();

    expect(await screen.findByText(HOT.groupless)).toBeTruthy();
    stubMyGroups(transport, [{ ...KAZIMIERZ_MINE, id: PODGORZE.id, name: PODGORZE.name }]);
    fireEvent.press(await chip(PODGORZE, 'join'));

    expect(await screen.findByText('Play finds you one.')).toBeTruthy();
    expect(
      screen.getByRole('button', { name: lineNamed(HOT.line) }).props.accessibilityState,
    ).toEqual({
      expanded: true,
    });
  });

  it('closes it like any line, from its header', async () => {
    hottestServer([OGRODY], { mine: [] });
    await launchSignedIn();

    fireEvent.press(
      await screen.findByRole('button', { name: lineNamed(HOT.line), expanded: true }),
    );

    expect(
      await screen.findByRole('button', { name: lineNamed(HOT.line), expanded: false }),
    ).toBeTruthy();
  });
});

describe('the pull', () => {
  it('reads the row again, and the groups the groupless line is drawn from', async () => {
    hottestServer([OGRODY]);
    await launchSignedIn();
    await openLine(HOT.line);

    await waitFor(() => expect(reads(MY_GROUPS_PATH)).toBeGreaterThan(0));
    const before = reads(HOTTEST_GROUPS_PATH);
    const mine = reads(MY_GROUPS_PATH);
    stubHottestGroups(transport, [{ ...OGRODY, games_this_week: 15 }]);
    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });

    expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(before);
    expect(reads(MY_GROUPS_PATH)).toBeGreaterThan(mine);
    expect(await within(screen.getByTestId(`hottest-${OGRODY.id}`)).findByText('15')).toBeTruthy();
  });
});
