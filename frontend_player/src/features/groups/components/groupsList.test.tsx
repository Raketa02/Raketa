/**
 * **Play › Groups and a group's page, walked** — the list (play 1, 38) and the page's header
 * (play 40) through the real routes, with only the socket faked
 * ([#512](https://github.com/Raketa02/Raketa/issues/512), PRD #500 stories 1, 5–8, 50).
 */

import { router } from 'expo-router';
import { StyleSheet, type ViewStyle } from 'react-native';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { MONOGRAM_HUES } from '@/shared/ui';
import {
  launchSignedIn,
  MY_GROUPS_PATH,
  stubGate,
  stubMyGroups,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from './groupsPresentation';

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

const OGRODY_OPEN_PLAY: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000002',
  name: 'Ogrody open play',
  monogram: { letters: 'Oo', colour: 0 },
  sports: ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'],
  member_count: 8,
  home_club: { id: 'c0000000-0000-4000-8000-000000000003', name: 'Ogrody 33' },
};

const KAZIMIERZ_CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

function pageOf(
  group: Wire['MyGroupSchema'],
  overrides: Partial<Wire['GroupResponse']> = {},
): Wire['GroupResponse'] {
  return {
    ...group,
    link: 'https://raketa.app/join/K7PQ2MXA',
    join_policy: 'ANYONE',
    is_owner: false,
    rated_by_sport: [],
    ...overrides,
  };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

async function openGroups() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
}

/**
 * The tiles a monogram's letters are drawn on — every one on screen, since a page pushed over the
 * list leaves the list's card mounted under it. The tile is hidden from assistive technology (the
 * name beside it says what it pictures), so it is found by its letters and read by its colour.
 */
type Node = ReturnType<typeof screen.getByText>;

function tilesOf(letters: string): readonly ViewStyle[] {
  return screen.getAllByText(letters, { includeHiddenElements: true }).map((text) => {
    let node: Node | null = text;
    while (node !== null) {
      const style = StyleSheet.flatten(node.props.style as ViewStyle | undefined);
      if (node.type === 'View' && style?.backgroundColor !== undefined) return style;
      node = node.parent;
    }
    throw new Error(`no tile under ${letters}`);
  });
}

const cardNamed = (name: string) => screen.findByRole('button', { name: new RegExp(`^${name},`) });

describe('the Groups list', () => {
  it('offers + New and Join', async () => {
    await openGroups();

    expect(
      await screen.findByRole('button', { name: GROUPS_COPY.list.newGroupLabel }),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: GROUPS_COPY.list.joinLabel })).toBeTruthy();
    expect(screen.getByText(GROUPS_COPY.list.newGroup)).toBeTruthy();
  });

  it('draws a card per group — name, members and home club — in the order served', async () => {
    stubMyGroups(transport, [OGRODY_OPEN_PLAY, KAZIMIERZ_CREW]);
    await openGroups();

    const first = await cardNamed('Ogrody open play');
    expect(within(first).getByText('8 members')).toBeTruthy();
    expect(within(first).getByText('Ogrody 33')).toBeTruthy();
    const second = await cardNamed('Kazimierz crew');
    expect(within(second).getByText('Centrum Ruchu')).toBeTruthy();

    // Newest joined first is the server's order, and the list keeps it.
    const names = screen
      .getAllByRole('button', { name: /members/ })
      .map((card) => card.props.accessibilityLabel as string);
    expect(names).toEqual([
      'Ogrody open play, 8 members, plays Padel, Tennis, Squash, Badminton, Ogrody 33',
      'Kazimierz crew, 6 members, plays Padel, Tennis, Squash, Badminton, Centrum Ruchu',
    ]);
  });

  // Story 9: the backend's letters, as typed, on the hue its colour key names.
  it('draws each group’s tile — its letters on the colour its key names', async () => {
    stubMyGroups(transport, [OGRODY_OPEN_PLAY, KAZIMIERZ_CREW]);
    await openGroups();
    await cardNamed('Ogrody open play');

    expect(tilesOf('Oo')).toEqual([expect.objectContaining({ backgroundColor: MONOGRAM_HUES[0] })]);
    expect(tilesOf('Kc')).toEqual([expect.objectContaining({ backgroundColor: MONOGRAM_HUES[1] })]);
  });

  // Story 6: a long name ends in an ellipsis rather than wrapping.
  it('keeps a long name to one line', async () => {
    const long = { ...OGRODY_OPEN_PLAY, name: 'Wednesday night padel for the whole of Kraków' };
    stubMyGroups(transport, [long]);
    await openGroups();

    const card = await cardNamed(long.name);

    expect(within(card).getByText(long.name).props.numberOfLines).toBe(1);
  });

  it('says what to do when the player has no groups', async () => {
    await openGroups();

    expect(await screen.findByText(GROUPS_COPY.list.empty)).toBeTruthy();
  });

  it('says why when the list cannot be read, and reads it again', async () => {
    // A refusal the player retries themselves — a network failure is retried unattended first.
    transport.on('GET', MY_GROUPS_PATH, () => errorResponse(429, 'too_many_requests'));
    await openGroups();

    const retry = await screen.findByRole('button', { name: GROUPS_COPY.retry });
    stubMyGroups(transport, [OGRODY_OPEN_PLAY]);
    fireEvent.press(retry);

    expect(await cardNamed('Ogrody open play')).toBeTruthy();
  });
});

describe('a group’s page', () => {
  async function openGroup(group: Wire['MyGroupSchema'], page = pageOf(group)) {
    stubMyGroups(transport, [group]);
    transport.on('GET', `/api/v1/groups/${group.id}`, () => json(page));
    await openGroups();
    fireEvent.press(await cardNamed(group.name));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${group.id}`));
  }

  it('is headed by the name and N members · home club, each on one line', async () => {
    await openGroup(OGRODY_OPEN_PLAY);

    const header = await screen.findByRole('header', { name: /Ogrody open play/ });
    expect(within(header).getByText('Ogrody open play').props.numberOfLines).toBe(1);
    expect(within(header).getByText('8 members · Ogrody 33').props.numberOfLines).toBe(1);
  });

  it('draws the group’s tile beside its name', async () => {
    await openGroup(OGRODY_OPEN_PLAY);
    await screen.findByText('8 members · Ogrody 33');

    // The list's card under the page, and the page's own header.
    expect(tilesOf('Oo')).toEqual([
      expect.objectContaining({ backgroundColor: MONOGRAM_HUES[0] }),
      expect.objectContaining({ backgroundColor: MONOGRAM_HUES[0] }),
    ]);
  });

  it('counts one member in the singular', async () => {
    await openGroup(OGRODY_OPEN_PLAY, pageOf(OGRODY_OPEN_PLAY, { member_count: 1 }));

    expect(await screen.findByText('1 member · Ogrody 33')).toBeTruthy();
  });

  it('goes back to the Groups list', async () => {
    await openGroup(OGRODY_OPEN_PLAY);
    await screen.findByText('8 members · Ogrody 33');

    fireEvent.press(screen.getByRole('button', { name: GROUPS_COPY.group.back }));

    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(await cardNamed('Ogrody open play')).toBeTruthy();
  });

  it('says a group that is not one of yours is not', async () => {
    stubMyGroups(transport, [OGRODY_OPEN_PLAY]);
    transport.on('GET', `/api/v1/groups/${OGRODY_OPEN_PLAY.id}`, () =>
      errorResponse(404, 'group_not_found'),
    );
    await openGroups();
    fireEvent.press(await cardNamed('Ogrody open play'));

    expect(await screen.findByText(GROUPS_COPY.group.refused.group_not_found)).toBeTruthy();
    // The same answer however often it is asked for, so nothing offers to ask again.
    expect(screen.queryByRole('button', { name: GROUPS_COPY.retry })).toBeNull();
  });

  it('sends an address with no group behind it back to Play', async () => {
    await openGroups();

    act(() =>
      router.push({ pathname: '/play/group/[groupId]', params: { groupId: 'not-a-group' } }),
    );

    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(transport.requestsTo('GET', '/api/v1/groups/not-a-group')).toEqual([]);
  });
});
