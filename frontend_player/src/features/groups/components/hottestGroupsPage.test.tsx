/**
 * **The Groups heating up page** — behind its line's *All groups ›*, walked through the real route
 * tree ([#823](https://github.com/Raketa02/Raketa/issues/823); ADR-0205 §7; the Home rows screens
 * §3.6; the mechanics §5.10; the words §31.14).
 *
 * - **The way in**: *All groups ›* pushes it over Home, the Home tab lit, titled *Groups heating up*.
 * - **The list**: every group in the served order, the line's first, the reader's own marked *You're
 *   in*, each card at the content's whole width; 20 to a page, the next read as the list nears its
 *   end, never twice, and nothing past the last — and read on past a page a write cancelled, or one
 *   that brought nothing new.
 * - **Its states**: reading, a first page refused with *Try again*, a later page refused under the
 *   list, and an empty list.
 * - **The taps**: a card opens the line's group sheet; *Join*, *Ask to join*, *Asked* and *You're
 *   in* act as on the line, and a write here moves the card on Home's line too.
 * - **Back** is Home, the line still open.
 *
 * **The routes are answered by a small fake of the server** (`heatingUpServer`): the row is the
 * list's first six, a page is 20 of it behind a cursor, and a join admits or asks by the group's
 * policy — so what the page and the line draw after a write is each read again, never this client
 * guessing.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Dimensions, FlatList } from 'react-native';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import { lineNamed, openLine } from '@/test-support/forYou';
import {
  HOME_PATH,
  HOTTEST_GROUPS_ALL_PATH,
  HOTTEST_GROUPS_PATH,
  MY_GROUPS_PATH,
  launchSignedIn,
  stubGate,
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

import type { HottestRow } from '../domain/group';
import { groupKeys } from '../hooks/groupKeys';

import { GROUPS_COPY } from './groupsCopy';
import { hottestChipLabel } from './groupsPresentation';
import { HottestGroupCard } from './HottestGroupCard';

const HOT = GROUPS_COPY.hottest;
const PAGE = HOT.page;

const face = (n: number, nickname: string): Wire['GroupPersonSchema'] => ({
  player_id: `f0000000-0000-4000-8000-0000000009${String(n).padStart(2, '0')}`,
  nickname,
});

/** The `n`th group in the row's order: an untagged *Anyone* group, its heat falling with `n`. */
function heated(
  n: number,
  overrides: Partial<Wire['HottestGroupSchema']> = {},
): Wire['HottestGroupSchema'] {
  return {
    id: `a0000000-0000-4000-8000-${String(n).padStart(12, '0')}`,
    kind: 'PLAYER',
    name: `Ladder ${n}`,
    monogram: { letters: `L${n % 10}`, colour: n % 8 },
    sports: ['PADEL'],
    member_count: 3 + (n % 9),
    join_policy: 'ANYONE',
    run_by: `owner.${n}`,
    club: { id: 'c0000000-0000-4000-8000-000000000901', name: 'Ogrody 33' },
    games_this_week: Math.max(0, 60 - n),
    new_this_month: 0,
    heat_share: 1 / n,
    tag: null,
    faces: [face(1, 'kuba.w'), face(2, 'ola.n')],
    friends_count: 0,
    relation: 'NONE',
    is_administrator: false,
    ...overrides,
  };
}

/** HOTTEST, official, *People I approve*: **Ask to join**. */
const OGRODY = heated(1, {
  kind: 'OFFICIAL',
  name: 'Ogrody 33 Club',
  monogram: { letters: 'O3', colour: 2 },
  join_policy: 'PEOPLE_I_APPROVE',
  run_by: 'Ogrody 33',
  tag: 'HOTTEST',
  friends_count: 7,
});
/** On the line, and *Anyone*: **Join**. */
const PODGORZE = heated(2, { name: 'Podgórze tennis ladder', sports: ['TENNIS'] });
/** The reader's own, on the line: **You're in**. */
const KAZIMIERZ = heated(3, { name: 'Kazimierz crew', tag: 'GROWING', relation: 'MEMBER' });
/** The reader's own too, past the line's six: only the page draws it. */
const NOWA_HUTA = heated(8, { name: 'Nowa Huta squash', sports: ['SQUASH'], relation: 'MEMBER' });
/** Waiting on an answer: **Asked**. */
const ASKED = heated(4, {
  name: 'Asked crew',
  join_policy: 'PEOPLE_I_APPROVE',
  relation: 'REQUESTED',
});

/** Eight groups: the line's six, then two only the page lists — the reader's own among both. */
const EIGHT = [OGRODY, PODGORZE, KAZIMIERZ, ASKED, heated(5), heated(6), heated(7), NOWA_HUTA];

const mineOf = (group: Wire['HottestGroupSchema']): Wire['MyGroupSchema'] => ({
  id: group.id,
  kind: group.kind,
  name: group.name,
  monogram: group.monogram,
  sports: group.sports,
  member_count: group.member_count,
  home_club: group.club,
});

const membershipPath = (id: string) => `/api/v1/groups/${id}/membership`;
const joinRequestPath = (id: string) => `/api/v1/groups/${id}/join-request`;

let transport: Transport;

/**
 * **The row's and the page's routes, faked** — the row is the list's first six and how many there
 * are; a page is `pageSize` of the list behind the cursor, which is where it starts. A join admits an
 * *Anyone* group (one more player) and leaves a request on a *People I approve* one; a withdraw takes
 * the request back. `refuseNextJoin` makes the next join fail with that code.
 */
function heatingUpServer(
  initially: readonly Wire['HottestGroupSchema'][],
  { pageSize = 20 }: { readonly pageSize?: number } = {},
) {
  let groups = [...initially];
  let refusal: string | undefined;
  let held: Promise<void> | undefined;
  let laterPagesHeld: Promise<void> | undefined;

  stubGate(transport, { hasPlayerProfile: true });
  stubMyGroups(transport, initially.filter((group) => group.relation === 'MEMBER').map(mineOf));
  transport.on('GET', HOTTEST_GROUPS_PATH, () =>
    json<Wire['HottestGroupsResponse']>({
      groups: groups.slice(0, 6),
      total: Math.min(groups.length, 100),
    }),
  );
  transport.on('GET', HOTTEST_GROUPS_ALL_PATH, async (request) => {
    const after = new URLSearchParams(request.path.split('?')[1] ?? '').get('after');
    if (after !== null && laterPagesHeld !== undefined) await laterPagesHeld;
    const from = after === null ? 0 : Number(after);
    return json<Wire['HottestGroupsPageResponse']>({
      groups: groups.slice(from, from + pageSize),
      next: from + pageSize < groups.length ? String(from + pageSize) : null,
      total: after === null ? Math.min(groups.length, 100) : null,
    });
  });

  for (const group of initially) {
    transport.on('POST', membershipPath(group.id), async () => {
      if (held !== undefined) await held;
      if (refusal !== undefined) {
        const code = refusal;
        refusal = undefined;
        return errorResponse(409, code);
      }
      const now = groups.find((each) => each.id === group.id) ?? group;
      const answered: Wire['HottestGroupSchema'] =
        now.join_policy === 'ANYONE' || now.is_administrator
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
    /** Joins wait for the returned release — so a suite can look at the chips before the answer. */
    holdJoins: () => {
      let release: () => void = () => {};
      held = new Promise<void>((resolve) => {
        release = resolve;
      });
      return release;
    },
    /** Every page after the first waits for the returned release — the first is never held. */
    holdLaterPages: () => {
      let release: () => void = () => {};
      laterPagesHeld = new Promise<void>((resolve) => {
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
  jest.useRealTimers();
  transport.restore();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  resetSessionStatus();
  await clearStoredTokens();
});

const reads = (path: string) => transport.requestsTo('GET', path).length;
const pageReads = () => transport.requestsTo('GET', HOTTEST_GROUPS_ALL_PATH);
const list = () => within(screen.getByTestId('hottest-groups-list'));
const line = () => within(screen.getByTestId('hottest-groups'));
const sheet = () => within(screen.getByTestId('bottom-sheet'));
const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);
/** The cards the page draws, top to bottom, by group. */
const listed = () =>
  list()
    .getAllByTestId(/^hottest-a0/)
    .map((node) => (node.props.testID as string).replace('hottest-', ''));
/** How many groups the page has read so far — the list FlatList draws as it scrolls. */
const held = () => (screen.UNSAFE_getByType(FlatList).props.data as readonly unknown[]).length;
const nearTheEnd = () => fireEvent(screen.UNSAFE_getByType(FlatList), 'endReached');
const chipOn = (
  where: ReturnType<typeof within>,
  group: Wire['HottestGroupSchema'],
  action: 'join' | 'ask' | 'requested' | 'in',
) => where.findByRole('button', { name: hottestChipLabel(action, group.name) });
/** A card's relation on Home's row, as the cache holds it — what the line under the page draws. */
const onTheRow = (group: Wire['HottestGroupSchema']) =>
  queryClient
    .getQueryData<HottestRow>(groupKeys.hottest())
    ?.groups.find((card) => card.id === group.id)?.relation;

async function homeWithTheLine() {
  await launchSignedIn();
  await openLine(HOT.line);
}

async function openThePage() {
  await homeWithTheLine();
  fireEvent.press(screen.getByRole('link', { name: HOT.allGroupsLabel }));
  await waitFor(() => expect(screen).toHavePathname('/hottest-groups'));
  await screen.findByTestId('hottest-groups-list');
}

describe('All groups ›', () => {
  it('pushes the page over Home, the Home tab still lit, titled Groups heating up', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();
    expect(screen.getByRole('header', { name: PAGE.title })).toBeTruthy();
    expect(screen.getByRole('button', { name: PAGE.back })).toBeTruthy();
    // The page has no filter: no sport pill in its header.
    expect(screen.queryByRole('button', { name: /^Sport:/ })).toBeNull();
  });

  it('is back to Home on its ‹, with the line still open', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    fireEvent.press(screen.getByRole('button', { name: PAGE.back }));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(
      await screen.findByRole('button', { name: lineNamed(HOT.line), expanded: true }),
    ).toBeTruthy();
    expect(line().getByTestId(`hottest-${OGRODY.id}`)).toBeTruthy();
  });
});

describe('the list', () => {
  /** ADR-0205 §7: every group of 3 or more, in the row's order — the row is the first six. */
  it('lists every group in the served order, the line’s six first', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    expect(listed()).toEqual(EIGHT.map((group) => group.id));
    expect(pageReads()[0]!.path).toBe(HOTTEST_GROUPS_ALL_PATH);
  });

  it('marks the reader’s own groups You’re in — on the line’s six and past them', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    expect(await chipOn(list(), KAZIMIERZ, 'in')).toBeTruthy();
    expect(await chipOn(list(), NOWA_HUTA, 'in')).toBeTruthy();
    expect(await chipOn(list(), OGRODY, 'ask')).toBeTruthy();
    expect(await chipOn(list(), PODGORZE, 'join')).toBeTruthy();
    expect(await chipOn(list(), ASKED, 'requested')).toBeTruthy();
  });

  /** The line's card, whole — at the content's width: the screen less a gutter each side. */
  it('draws the line’s card at the content’s whole width, with its tag and figures', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    const widths = within(screen.UNSAFE_getByType(FlatList))
      .UNSAFE_getAllByType(HottestGroupCard)
      .map((card) => card.props.width as number);
    expect(new Set(widths)).toEqual(
      new Set([Dimensions.get('window').width - 2 * theme.size.gutter]),
    );
    const ogrody = within(list().getByTestId(`hottest-${OGRODY.id}`));
    expect(ogrody.getByText(OGRODY.name)).toBeTruthy();
    expect(within(ogrody.getByTestId('hottest-games')).getByText('59')).toBeTruthy();
    expect(list().getByTestId('hottest-tag-HOTTEST', { includeHiddenElements: true })).toBeTruthy();
  });

  it('reads 20 to a page, the next as the list nears its end — never twice, nothing past the last', async () => {
    // The first is the reader's own: a reader in no group finds the line open from the start.
    const many = Array.from({ length: 45 }, (_, at) =>
      heated(10 + at, at === 0 ? { relation: 'MEMBER' } : {}),
    );
    heatingUpServer(many);
    await openThePage();
    expect(pageReads()).toHaveLength(1);
    expect(held()).toBe(20);

    nearTheEnd();
    nearTheEnd();
    await waitFor(() => expect(pageReads()).toHaveLength(2));
    expect(pageReads()[1]!.path).toContain('after=20');
    await waitFor(() => expect(held()).toBe(40));

    nearTheEnd();
    await waitFor(() => expect(pageReads()).toHaveLength(3));
    expect(pageReads()[2]!.path).toContain('after=40');
    await waitFor(() => expect(held()).toBe(45));

    // The last page named no cursor: the end asks for nothing.
    nearTheEnd();
    expect(pageReads()).toHaveLength(3);
  });

  /**
   * A join near the end cancels the page on its way, and its re-read reads only the pages drawn: the
   * list is as tall as before, so it would never reach its end again. The page is asked for again.
   */
  it('asks again for the next page a write cancelled, once the reads settle', async () => {
    const server = heatingUpServer(EIGHT, { pageSize: 4 });
    await openThePage();
    const release = server.holdLaterPages();

    nearTheEnd();
    await waitFor(() => expect(pageReads()).toHaveLength(2));
    fireEvent.press(await chipOn(list(), PODGORZE, 'join'));
    expect(await chipOn(list(), PODGORZE, 'in')).toBeTruthy();
    await act(async () => release());

    // No second end reached: the page behind the first is read again by itself.
    await waitFor(() => expect(listed()).toEqual(EIGHT.map((group) => group.id)));
    expect(pageReads().filter((read) => read.path.includes('after=4')).length).toBeGreaterThan(1);
  });

  /** The mechanics §5.10: a page can read again groups that cooled behind its cursor — all of them. */
  it('reads on past a page that brought nothing new', async () => {
    heatingUpServer(EIGHT, { pageSize: 4 });
    await openThePage();
    transport.on('GET', HOTTEST_GROUPS_ALL_PATH, (request) => {
      const after = new URLSearchParams(request.path.split('?')[1] ?? '').get('after');
      return json<Wire['HottestGroupsPageResponse']>(
        after === '4'
          ? { groups: EIGHT.slice(0, 4), next: 'cooled', total: null }
          : { groups: EIGHT.slice(4), next: null, total: null },
      );
    });

    nearTheEnd();

    await waitFor(() => expect(listed()).toEqual(EIGHT.map((group) => group.id)));
    expect(pageReads().at(-1)!.path).toContain('after=cooled');
  });

  it('says so, in place of the list, when no group is left to list', async () => {
    heatingUpServer(EIGHT);
    await homeWithTheLine();
    transport.on('GET', HOTTEST_GROUPS_ALL_PATH, () =>
      json<Wire['HottestGroupsPageResponse']>({ groups: [], next: null, total: 0 }),
    );

    fireEvent.press(screen.getByRole('link', { name: HOT.allGroupsLabel }));

    expect(await screen.findByText(PAGE.nobody)).toBeTruthy();
  });
});

describe('its states', () => {
  it('spins, named, while the first page reads', async () => {
    heatingUpServer(EIGHT);
    await homeWithTheLine();
    // Every read waits until answered — the navigation runs every pending timer, so the first one
    // times out and is asked again: each is answered, and any after them at once.
    let answered = false;
    const waiting: (() => void)[] = [];
    const page = () =>
      json<Wire['HottestGroupsPageResponse']>({ groups: EIGHT, next: null, total: 8 });
    transport.on('GET', HOTTEST_GROUPS_ALL_PATH, () =>
      answered ? page() : new Promise((resolve) => waiting.push(() => resolve(page()))),
    );

    fireEvent.press(screen.getByRole('link', { name: HOT.allGroupsLabel }));

    expect(await screen.findByLabelText(PAGE.reading)).toBeTruthy();
    expect(screen.queryByTestId('hottest-groups-list')).toBeNull();
    await act(async () => {
      answered = true;
      for (const answer of waiting) answer();
    });
    // Past a retry's backoff, should the first read have timed out.
    await act(() => jest.advanceTimersByTimeAsync(2_000));

    expect(await screen.findByTestId('hottest-groups-list')).toBeTruthy();
    expect(screen.queryByLabelText(PAGE.reading)).toBeNull();
  });

  it('says a first page’s failure, and Try again reads it again', async () => {
    jest.useFakeTimers();
    heatingUpServer(EIGHT);
    transport.on('GET', HOTTEST_GROUPS_ALL_PATH, () => errorResponse(503, 'service_unavailable'));
    await homeWithTheLine();
    fireEvent.press(screen.getByRole('link', { name: HOT.allGroupsLabel }));
    // Through the automatic retries the error model allows.
    await act(() => jest.advanceTimersByTimeAsync(30_000));

    const again = await screen.findByRole('button', { name: GROUPS_COPY.retry });
    expect(screen.getByRole('alert')).toBeTruthy();

    heatingUpServer(EIGHT);
    fireEvent.press(again);
    expect(await screen.findByTestId('hottest-groups-list')).toBeTruthy();
    expect(listed()).toEqual(EIGHT.map((group) => group.id));
  });

  it('says a later page’s failure under the list, and its own Try again reads it again', async () => {
    jest.useFakeTimers();
    heatingUpServer(EIGHT, { pageSize: 4 });
    await openThePage();
    expect(listed()).toHaveLength(4);
    transport.on('GET', HOTTEST_GROUPS_ALL_PATH, () => errorResponse(503, 'service_unavailable'));

    nearTheEnd();
    await act(() => jest.advanceTimersByTimeAsync(30_000));

    const again = await list().findByRole('button', { name: GROUPS_COPY.retry });
    expect(list().getByRole('alert')).toBeTruthy();
    // The page read stands while the next is refused.
    expect(listed()).toHaveLength(4);

    heatingUpServer(EIGHT, { pageSize: 4 });
    fireEvent.press(again);
    await waitFor(() => expect(listed()).toEqual(EIGHT.map((group) => group.id)));
    expect(list().queryByRole('alert')).toBeNull();
  });
});

describe('the taps', () => {
  it('a card opens the line’s group sheet, every field and its one button', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    fireEvent.press(list().getByRole('button', { name: new RegExp(`^${OGRODY.name},`) }));

    expect(await screen.findByRole('header', { name: OGRODY.name })).toBeTruthy();
    expect(sheet().getByText('Closed group · run by Ogrody 33 · Ogrody 33')).toBeTruthy();
    expect(sheet().getByText('7 of your friends play here')).toBeTruthy();
    expect(
      sheet()
        .getAllByRole('button')
        .map((node) => node.props.accessibilityLabel),
    ).toEqual([hottestChipLabel('ask', OGRODY.name), `Close ${OGRODY.name}`]);
  });

  it('a card past the line’s six opens its sheet too, which opens the group for a member', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    fireEvent.press(list().getByRole('button', { name: new RegExp(`^${NOWA_HUTA.name},`) }));
    fireEvent.press(await sheet().findByRole('button', { name: HOT.openGroup }));

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${NOWA_HUTA.id}`));
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
  });

  /** A re-read that drops the card closes its sheet — and one that brings it back opens nothing. */
  it('closes a card’s sheet when a read drops the card, and never opens it again by itself', async () => {
    heatingUpServer(EIGHT);
    await openThePage();
    const serve = (groups: readonly Wire['HottestGroupSchema'][]) =>
      transport.on('GET', HOTTEST_GROUPS_ALL_PATH, () =>
        json<Wire['HottestGroupsPageResponse']>({ groups: [...groups], next: null, total: 8 }),
      );
    const pull = () =>
      act(async () => {
        await (screen
          .UNSAFE_getByType(FlatList)
          .props.refreshControl.props.onRefresh() as Promise<void>);
      });

    fireEvent.press(list().getByRole('button', { name: new RegExp(`^${NOWA_HUTA.name},`) }));
    expect(await screen.findByRole('header', { name: NOWA_HUTA.name })).toBeTruthy();

    serve(EIGHT.filter((group) => group.id !== NOWA_HUTA.id));
    await pull();
    await waitFor(() => expect(screen.queryByTestId('bottom-sheet')).toBeNull());

    serve(EIGHT);
    await pull();
    await waitFor(() => expect(listed()).toContain(NOWA_HUTA.id));
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
  });

  /** ADR-0205 §7: the same write, the same guess, the same re-reads — and the line agrees. */
  it('Join is You’re in at once, here and on Home’s line, and every read showing it is read again', async () => {
    const server = heatingUpServer(EIGHT);
    await openThePage();
    const before = {
      row: reads(HOTTEST_GROUPS_PATH),
      page: pageReads().length,
      mine: reads(MY_GROUPS_PATH),
      home: reads(HOME_PATH),
    };
    const release = server.holdJoins();

    fireEvent.press(await chipOn(list(), PODGORZE, 'join'));

    // Before the server has answered: the page's chip, and the card on the line under it.
    expect(await chipOn(list(), PODGORZE, 'in')).toBeTruthy();
    expect(onTheRow(PODGORZE)).toBe('MEMBER');
    await act(async () => release());

    await waitFor(() => {
      expect(reads(HOTTEST_GROUPS_PATH)).toBeGreaterThan(before.row);
      expect(pageReads().length).toBeGreaterThan(before.page);
      expect(reads(MY_GROUPS_PATH)).toBeGreaterThan(before.mine);
      expect(reads(HOME_PATH)).toBeGreaterThan(before.home);
    });
    // The re-read is drawn: one more player.
    const podgorze = within(list().getByTestId(`hottest-${PODGORZE.id}`));
    expect(await podgorze.findByText(String(PODGORZE.member_count + 1))).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: PAGE.back }));
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await chipOn(line(), PODGORZE, 'in')).toBeTruthy();
  });

  it('Ask to join is Asked at once, here and on Home’s line', async () => {
    const server = heatingUpServer(EIGHT);
    await openThePage();
    const release = server.holdJoins();

    fireEvent.press(await chipOn(list(), OGRODY, 'ask'));

    expect(await chipOn(list(), OGRODY, 'requested')).toBeTruthy();
    expect(onTheRow(OGRODY)).toBe('REQUESTED');
    await act(async () => release());
    await waitFor(() =>
      expect(transport.requestsTo('POST', membershipPath(OGRODY.id))).toHaveLength(1),
    );

    fireEvent.press(screen.getByRole('button', { name: PAGE.back }));
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await chipOn(line(), OGRODY, 'requested')).toBeTruthy();
  });

  it('a join on a card only the page lists moves it at once, and leaves the line alone', async () => {
    const server = heatingUpServer([...EIGHT.slice(0, 7), heated(9)]);
    await openThePage();
    const ninth = heated(9);
    const release = server.holdJoins();

    fireEvent.press(await chipOn(list(), ninth, 'join'));

    expect(await chipOn(list(), ninth, 'in')).toBeTruthy();
    expect(onTheRow(ninth)).toBeUndefined();
    await act(async () => release());
    expect(await chipOn(list(), ninth, 'in')).toBeTruthy();
  });

  it('a refused join puts the chip back here and on the line, and says why', async () => {
    const server = heatingUpServer(EIGHT);
    server.refuseNextJoin('group_not_found');
    await openThePage();
    const release = server.holdJoins();

    fireEvent.press(await chipOn(list(), PODGORZE, 'join'));

    // The guess first, on both — then the refusal takes it back.
    expect(await chipOn(list(), PODGORZE, 'in')).toBeTruthy();
    expect(onTheRow(PODGORZE)).toBe('MEMBER');
    await act(async () => release());
    expect(await chipOn(list(), PODGORZE, 'join')).toBeTruthy();
    await waitFor(() => expect(toasts()).toHaveLength(1));
    expect(toasts()[0]?.[1]).toBe('bad');
    expect(onTheRow(PODGORZE)).toBe('NONE');
  });

  it('Asked opens the withdraw sheet, and Withdraw request turns the card back to Ask to join', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    fireEvent.press(await chipOn(list(), ASKED, 'requested'));

    expect(
      await screen.findByRole('header', { name: 'Waiting for owner.4 to answer' }),
    ).toBeTruthy();
    fireEvent.press(sheet().getByRole('button', { name: HOT.withdraw }));

    expect(await chipOn(list(), ASKED, 'ask')).toBeTruthy();
    expect(onTheRow(ASKED)).toBe('NONE');
    await waitFor(() =>
      expect(transport.requestsTo('DELETE', joinRequestPath(ASKED.id))).toHaveLength(1),
    );
  });

  it('You’re in opens the group’s page', async () => {
    heatingUpServer(EIGHT);
    await openThePage();

    fireEvent.press(await chipOn(list(), KAZIMIERZ, 'in'));

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${KAZIMIERZ.id}`));
  });
});
