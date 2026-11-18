/**
 * **Groups heating up on Home** — FOR YOU's first line, walked through the real route tree
 * ([#800](https://github.com/Raketa02/Raketa/issues/800), PRD #789; [#820](https://github.com/Raketa02/Raketa/issues/820);
 * ADR-0204 §3, ADR-0205 §5; the Home rows screens §3; the mechanics §5; the words §31.1–§31.4).
 *
 * - **The line**: first under FOR YOU, just below *Your games*, closed; open, its cards and no footer;
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

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { RefreshControl } from 'react-native';

import { HOME_COPY } from '@/features/shell/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { lineTitles, openLine } from '@/test-support/forYou';
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
import { hottestCardLabel, hottestChipLabel } from './groupsPresentation';

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
 * fail with that code.
 */
function hottestServer(
  initially: readonly Wire['HottestGroupSchema'][],
  { mine = [KAZIMIERZ_MINE] }: { readonly mine?: readonly Wire['MyGroupSchema'][] } = {},
) {
  let groups = [...initially];
  let refusal: string | undefined;
  let held: Promise<void> | undefined;

  stubGate(transport, { hasPlayerProfile: true });
  stubMyGroups(transport, mine);
  transport.on('GET', HOTTEST_GROUPS_PATH, () =>
    json<Wire['HottestGroupsResponse']>({ groups: [...groups], total: groups.length }),
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
const sheet = () => within(screen.getByTestId('bottom-sheet'));
const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

/** The section headings Home draws, top to bottom. */
const headings = () =>
  screen
    .getAllByRole('header')
    .map((node) => node.props.children as string)
    .filter((text) => typeof text === 'string');

const line = () => screen.findByRole('button', { name: HOT.line });

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

  /** No footer until the Groups heating up page has one to open (#823). */
  it('opens onto the cards in the read’s order, with no footer', async () => {
    hottestServer([OGRODY, KAZIMIERZ, PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    const names = within(screen.getByTestId('hottest-groups'))
      .getAllByRole('button', { name: /,/ })
      .map((node) => node.props.accessibilityLabel as string);
    expect(names.map((label) => label.split(',')[0])).toEqual([
      OGRODY.name,
      KAZIMIERZ.name,
      PODGORZE.name,
    ]);
    expect(within(screen.getByTestId('hottest-groups')).queryByRole('link')).toBeNull();
  });

  it('is hidden while the read holds nothing', async () => {
    hottestServer([]);
    await launchSignedIn();

    await waitFor(() => expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(0));
    await screen.findByText(/^Your games/);
    expect(screen.queryByRole('button', { name: HOT.line })).toBeNull();
  });

  it('is left out when its read fails, and the rest of Home stands', async () => {
    hottestServer([OGRODY]);
    transport.on('GET', HOTTEST_GROUPS_PATH, () => errorResponse(500, 'internal_error'));
    await launchSignedIn();

    await waitFor(() => expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(0));
    expect(await screen.findByText(/^Your games/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: HOT.line })).toBeNull();
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
    await waitFor(() => expect(screen.queryByRole('button', { name: HOT.line })).toBeNull());

    stubHottestGroups(transport, [OGRODY]);
    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });
    expect((await line()).props.accessibilityState).toEqual({ expanded: false });
  });
});

describe('the card', () => {
  it('draws the tag, the figures, the growth and four faces', async () => {
    hottestServer([OGRODY, KAZIMIERZ, PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    const ogrody = within(screen.getByTestId(`hottest-${OGRODY.id}`));
    expect(ogrody.getByText(OGRODY.name)).toBeTruthy();
    expect(ogrody.getByText('Padel · Tennis · Squash · Badminton')).toBeTruthy();
    expect(ogrody.getByText('14')).toBeTruthy();
    expect(ogrody.getByText('games this week')).toBeTruthy();
    expect(ogrody.getByText('11')).toBeTruthy();
    expect(ogrody.getByText('+3')).toBeTruthy();
    expect(screen.getByTestId('hottest-tag-HOTTEST', HIDDEN)).toBeTruthy();
    expect(screen.getByTestId('hottest-tag-GROWING', HIDDEN)).toBeTruthy();
    // Four of the six faces on the card; the sheet draws the six.
    expect(screen.getAllByTestId(new RegExp(`^hottest-face-${OGRODY.id}-`), HIDDEN)).toHaveLength(
      4,
    );
    expect(card(OGRODY).props.accessibilityLabel).toBe(
      hottestCardLabel({
        name: OGRODY.name,
        tag: 'HOTTEST',
        gamesThisWeek: 14,
        memberCount: 11,
        newThisMonth: 3,
      }),
    );
  });

  it('writes one game in the singular, no growth at nought, and no tag on an untagged card', async () => {
    hottestServer([PODGORZE]);
    await launchSignedIn();
    await openLine(HOT.line);

    const podgorze = within(await screen.findByTestId(`hottest-${PODGORZE.id}`));
    expect(podgorze.getByText('game this week')).toBeTruthy();
    expect(podgorze.queryByText(/this month/)).toBeNull();
    expect(screen.queryByTestId('hottest-tag-HOTTEST', HIDDEN)).toBeNull();
    expect(screen.queryByTestId('hottest-tag-GROWING', HIDDEN)).toBeNull();
    // A three-member group draws the faces it has.
    expect(screen.getAllByTestId(new RegExp(`^hottest-face-${PODGORZE.id}-`), HIDDEN)).toHaveLength(
      2,
    );
  });

  it('fills the heat bar to the served share', async () => {
    hottestServer([KAZIMIERZ]);
    await launchSignedIn();
    await openLine(HOT.line);

    const fill = await screen.findByTestId('heat-fill', HIDDEN);
    expect(fill.props.style).toEqual(
      expect.arrayContaining([expect.objectContaining({ width: `${(44 / 48) * 100}%` })]),
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
});

describe('the group sheet', () => {
  it('opens on a tap on the card, with the group’s fields and its one button', async () => {
    hottestServer([OGRODY, KAZIMIERZ]);
    await launchSignedIn();
    await openLine(HOT.line);

    fireEvent.press(await screen.findByRole('button', { name: new RegExp(`^${OGRODY.name},`) }));

    expect(await screen.findByRole('header', { name: OGRODY.name })).toBeTruthy();
    const opened = sheet();
    expect(opened.getByRole('button', { name: hottestChipLabel('ask', OGRODY.name) })).toBeTruthy();
    expect(opened.getByText('Closed group · run by Ogrody 33 · Ogrody 33')).toBeTruthy();
    expect(opened.getByText('Padel · Tennis · Squash · Badminton')).toBeTruthy();
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
    expect(await screen.findByRole('button', { name: HOT.line, expanded: true })).toBeTruthy();
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
    expect(screen.getByRole('button', { name: HOT.line }).props.accessibilityState).toEqual({
      expanded: true,
    });
  });

  it('closes it like any line, from its header', async () => {
    hottestServer([OGRODY], { mine: [] });
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: HOT.line, expanded: true }));

    expect(await screen.findByRole('button', { name: HOT.line, expanded: false })).toBeTruthy();
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
