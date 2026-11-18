/**
 * **FOR YOU on Home** — the five discovery rows folded into five quiet lines, walked through the real
 * route tree ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205 §5, §8; the Home rows
 * screens §1, §2; home refactor 3–13).
 *
 * What each line holds, its footer and its hidden states are its feature's suite's
 * (`hottestGroups`, `sameLevel`, `newInRaketa`, `sameVibe`, `topTen`), the on-screen reports
 * `onScreen`'s, and the frame's look `FoldingLine.test.tsx`'s. This is the shell's part: where FOR YOU
 * stands and in what order, which line is open — one at a time, switching by a fold and then an
 * unfold, closed only from its header, kept across tabs — every read running whether a line is open or
 * not, the pull, the page shown what opened, and Reduce motion.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { AccessibilityInfo, RefreshControl, type ScrollView } from 'react-native';

import { DISCOVERY_COPY } from '@/features/discovery/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { isOpen, lineHeader, lineTitles, openLine } from '@/test-support/forYou';
import {
  HOTTEST_GROUPS_PATH,
  NEW_IN_RAKETA_PATH,
  SAME_LEVEL_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
  launchSignedIn,
  stubGate,
  stubHottestGroups,
  stubMyGroups,
  stubNewInRaketa,
  stubSameLevel,
  stubSameVibe,
  stubTopTen,
} from '@/test-support/onboardingRouter';
import { scrollerOf } from '@/test-support/pinned';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { HOME_COPY } from './shellCopy';

const GROUPS = GROUPS_COPY.hottest.line;
const LEVEL = DISCOVERY_COPY.sameLevel.line;
const NEW = DISCOVERY_COPY.newInRaketa.line;
const VIBE = DISCOVERY_COPY.sameVibe.line;
const TOP = 'Top 10';

const HOT_GROUP: Wire['HottestGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000008201',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  join_policy: 'ANYONE',
  run_by: 'tomek.k',
  club: { id: 'c0000000-0000-4000-8000-000000008201', name: 'Kazimierz Padel' },
  games_this_week: 2,
  new_this_month: 1,
  heat_share: 1,
  tag: 'HOTTEST',
  faces: [],
  friends_count: 0,
  relation: 'NONE',
  is_administrator: false,
};

const PADEL: Wire['SameLevelSportSchema'] = {
  sport: 'PADEL',
  your_level: 2.71,
  their_level: 2.69,
  percent_even: 91,
  level_gap: -0.02,
  your_band: { name: 'Established', lower: 2.65, upper: 3.85 },
};

const AT_YOUR_LEVEL: Wire['SameLevelPlayerSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000008202',
  nickname: 'zofia.b',
  photo_id: null,
  photo_url: null,
  shown: PADEL,
  sports: [PADEL],
  relation: 'NONE',
};

const JOINER: Wire['NewInRaketaPlayerSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000008203',
  nickname: 'ola.n',
  photo_id: null,
  photo_url: null,
  joined_at: '2026-11-13T10:00:00Z',
  days_since_joined: 1,
  sports: [],
  relation: 'NONE',
};

const WITH_YOUR_VIBE: Wire['SameVibePlayerSchema'] = {
  player_id: 'e0000000-0000-4000-8000-000000008204',
  nickname: 'karol.t',
  photo_id: null,
  photo_url: null,
  vibe_percent: 75,
  in_common: 2,
  shared_tags: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN'],
  relation: 'NONE',
};

const RANKED: Wire['TopTenResponse'] = {
  sport: 'PADEL',
  anyone_listed: true,
  players: [
    {
      place: 1,
      player_id: 'e0000000-0000-4000-8000-000000008205',
      nickname: 'ines.d',
      photo_id: null,
      photo_url: null,
      level: 3.4,
      chip: null,
      is_you: false,
    },
  ],
};

/** The reader's one group, so nothing starts open by itself. */
const MINE: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000008209',
  kind: 'PLAYER',
  name: 'Podgórze',
  monogram: { letters: 'Po', colour: 2 },
  sports: ['PADEL'],
  member_count: 4,
  home_club: { id: 'c0000000-0000-4000-8000-000000008209', name: 'Podgórze Padel' },
};

let transport: Transport;

/** Every line with something to show, and the reader in a group. */
function everyLine() {
  stubGate(transport, { hasPlayerProfile: true });
  stubMyGroups(transport, [MINE]);
  stubHottestGroups(transport, [HOT_GROUP]);
  stubSameLevel(transport, [AT_YOUR_LEVEL]);
  stubNewInRaketa(transport, [JOINER]);
  stubSameVibe(transport, [WITH_YOUR_VIBE]);
  stubTopTen(transport, RANKED);
}

/** Home, every line shown — and closed. */
async function home() {
  everyLine();
  await launchSignedIn();
  await screen.findByRole('button', { name: TOP });
  await waitFor(() => expect(lineTitles()).toHaveLength(5));
}

const reads = (path: string) => transport.requestsTo('GET', path).length;
const LINE_READS = [
  HOTTEST_GROUPS_PATH,
  SAME_LEVEL_PATH,
  NEW_IN_RAKETA_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
];

/** Press one of the three columns by the name the bar gives it. */
function pressTab(label: string) {
  fireEvent.press(screen.getByLabelText(label));
}

beforeEach(() => {
  transport = installTransport();
});

afterEach(async () => {
  jest.restoreAllMocks();
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

describe('FOR YOU', () => {
  /** ADR-0205 §5's table: under *Your games*, the eyebrow and the five lines, in the rows' order. */
  it('stands below Your games: its eyebrow, then its five lines in order, every one closed', async () => {
    await home();

    const headings = screen
      .getAllByRole('header')
      .map((node) => node.props.children as string)
      .filter((text) => typeof text === 'string');
    const games = headings.findIndex((text) => text.startsWith('Your games'));
    expect(headings[games + 1]).toBe(HOME_COPY.forYou);
    expect(lineTitles()).toEqual([GROUPS, LEVEL, NEW, VIBE, TOP]);
    for (const title of lineTitles()) expect(isOpen(title)).toBe(false);
  });

  /** ADR-0205 §8: each line is a button that says its title and whether it is open. */
  it('names each line by its title, and says whether it is expanded or collapsed', async () => {
    await home();

    expect(screen.getByRole('button', { name: LEVEL, expanded: false })).toBeTruthy();
    await openLine(LEVEL);
    expect(screen.getByRole('button', { name: LEVEL, expanded: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: NEW, expanded: false })).toBeTruthy();
  });

  /** Q23: every line's read runs when Home opens, open or not — its hiding needs it. */
  it('reads every line when Home opens, though none is open', async () => {
    await home();

    for (const path of LINE_READS) expect(reads(path)).toBeGreaterThan(0);
  });

  /** Q21: with all five hidden, FOR YOU goes too. */
  it('is hidden whole while every line is', async () => {
    stubGate(transport, { hasPlayerProfile: true });
    await launchSignedIn();

    await waitFor(() => {
      for (const path of LINE_READS) expect(reads(path)).toBeGreaterThan(0);
    });
    expect(await screen.findByText(/^Your games/)).toBeTruthy();
    expect(screen.queryByRole('header', { name: HOME_COPY.forYou })).toBeNull();
    expect(screen.queryByTestId('for-you')).toBeNull();
  });

  /** A line shows only once its read has returned something: never while it loads. */
  it('shows a line only once its read has returned, the others standing meanwhile', async () => {
    everyLine();
    // Every attempt waits on one gate, so a retry behind a timeout is answered with the first.
    let answer: () => void = () => {};
    const answered = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('GET', NEW_IN_RAKETA_PATH, async () => {
      await answered;
      return json<Wire['NewInRaketaResponse']>({ players: [JOINER], total: 1 });
    });
    await launchSignedIn();
    await screen.findByRole('button', { name: TOP });

    expect(lineTitles()).toEqual([GROUPS, LEVEL, VIBE, TOP]);
    await act(async () => answer());

    await waitFor(() => expect(lineTitles()).toEqual([GROUPS, LEVEL, NEW, VIBE, TOP]));
  });

  it('re-reads every line on the pull', async () => {
    await home();
    const before = LINE_READS.map(reads);

    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });

    LINE_READS.forEach((path, at) => expect(reads(path)).toBeGreaterThan(before[at]!));
  });
});

describe('which line is open', () => {
  /** Q12: only the header closes it — Top 10's pill, inside, does not. */
  it('opens on a tap, and closes only from its header', async () => {
    await home();
    await openLine(TOP);

    fireEvent.press(
      await within(screen.getByTestId('top-ten')).findByRole('button', { name: /^Sport:/ }),
    );
    act(() => jest.advanceTimersByTime(theme.motion.unfold));
    expect(screen.getByTestId('sport-bar')).toBeTruthy();
    expect(isOpen(TOP)).toBe(true);

    fireEvent.press(lineHeader(TOP));

    expect(isOpen(TOP)).toBe(false);
    await waitFor(() =>
      expect(screen.queryByTestId(`top-ten-card-${RANKED.players[0]!.player_id}`)).toBeNull(),
    );
  });

  /** Q10 and the brief: one line at a time — the first folds, then the second unfolds. */
  it('is one at a time: another line folds the first, then unfolds', async () => {
    await home();
    await openLine(LEVEL);

    fireEvent.press(lineHeader(VIBE));

    // The first folds at once; the second waits for the fold.
    expect(isOpen(LEVEL)).toBe(false);
    expect(isOpen(VIBE)).toBe(false);
    act(() => jest.advanceTimersByTime(theme.motion.lineFold));
    expect(isOpen(VIBE)).toBe(true);
    expect(screen.queryByTestId(`same-level-${AT_YOUR_LEVEL.player_id}`)).toBeNull();
    expect(screen.getByTestId(`same-vibe-${WITH_YOUR_VIBE.player_id}`)).toBeTruthy();
  });

  /** An unfold never runs beside a fold: a third press while the first folds waits for it too. */
  it('waits for the fold when a third line is pressed mid-switch, and opens that one', async () => {
    await home();
    await openLine(LEVEL);

    fireEvent.press(lineHeader(VIBE));
    fireEvent.press(lineHeader(TOP));

    for (const title of [LEVEL, VIBE, TOP]) expect(isOpen(title)).toBe(false);
    act(() => jest.advanceTimersByTime(theme.motion.lineFold));
    expect(isOpen(TOP)).toBe(true);
    expect(isOpen(VIBE)).toBe(false);
  });

  /** Q10: kept while the app lives — Home stays mounted under every tab (#809). */
  it('keeps the open line across a tab switch', async () => {
    await home();
    await openLine(NEW);

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    pressTab('Home');
    await waitFor(() => expect(screen).toHavePathname('/'));

    expect(isOpen(NEW)).toBe(true);
    expect(screen.getByTestId(`joiner-${JOINER.player_id}`)).toBeTruthy();
  });

  it('keeps it under a screen pushed over Home, and back', async () => {
    await home();
    await openLine(LEVEL);

    fireEvent.press(screen.getByRole('link', { name: DISCOVERY_COPY.sameLevel.seeAllLabel }));
    await waitFor(() => expect(screen).toHavePathname('/same-level'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));

    expect(isOpen(LEVEL)).toBe(true);
  });
});

describe('the page', () => {
  /** The brief: if the opened content would be cut off, the page scrolls just enough to show it. */
  it('scrolls just enough to show a line that unfolds below its foot', async () => {
    await home();
    const page = scrollerOf(screen.getByTestId('for-you')) as unknown as {
      readonly instance: ScrollView;
      readonly props: { readonly onLayout: (event: unknown) => void };
    };
    // The harness's `ScrollView` shares one mock `scrollTo` across instances, so it starts clean.
    const scrollTo = jest.spyOn(page.instance, 'scrollTo');
    scrollTo.mockClear();
    const layout = (y: number, height: number) => ({
      nativeEvent: { layout: { x: 0, y, width: 390, height } },
    });
    act(() => {
      fireEvent(page as never, 'layout', layout(0, 700));
      fireEvent(screen.getByTestId('for-you'), 'layout', layout(500, 400));
      fireEvent(screen.getByTestId('same-vibe'), 'layout', layout(150, 46));
      fireEvent(lineHeader(VIBE), 'layout', layout(0, 44));
    });

    await openLine(VIBE);
    act(() => {
      fireEvent(screen.getByTestId('same-vibe-content'), 'layout', layout(0, 254));
    });

    // The line stands 650 down, 300 tall once open: its foot at 950, 250 below the page's 700.
    expect(scrollTo).toHaveBeenCalledTimes(1);
    expect(scrollTo).toHaveBeenCalledWith({ y: 250, animated: true });
  });

  /** Groups heating up, open by itself for a player in no group, never scrolls Home under them. */
  it('stays where it is when a line opens by itself', async () => {
    everyLine();
    stubMyGroups(transport, []);
    await launchSignedIn();
    await screen.findByRole('button', { name: GROUPS, expanded: true });
    const page = scrollerOf(screen.getByTestId('for-you')) as unknown as {
      readonly instance: ScrollView;
    };
    const scrollTo = jest.spyOn(page.instance, 'scrollTo');
    scrollTo.mockClear();
    const layout = (y: number, height: number) => ({
      nativeEvent: { layout: { x: 0, y, width: 390, height } },
    });

    act(() => {
      fireEvent(page as never, 'layout', layout(0, 700));
      fireEvent(screen.getByTestId('for-you'), 'layout', layout(500, 400));
      fireEvent(screen.getByTestId('hottest-groups'), 'layout', layout(30, 46));
      fireEvent(lineHeader(GROUPS), 'layout', layout(0, 44));
      fireEvent(screen.getByTestId('hottest-groups-content'), 'layout', layout(0, 254));
    });

    expect(scrollTo).not.toHaveBeenCalled();
  });
});

/** ADR-0205 §8: under Reduce motion, everything is instant — the scroll into view included. */
describe('under Reduce motion', () => {
  beforeEach(() => {
    jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
  });

  it('switches lines at once, with no fold to wait for', async () => {
    await home();
    await openLine(LEVEL);

    fireEvent.press(lineHeader(VIBE));

    expect(isOpen(LEVEL)).toBe(false);
    expect(isOpen(VIBE)).toBe(true);
    expect(screen.queryByTestId(`same-level-${AT_YOUR_LEVEL.player_id}`)).toBeNull();
  });

  it('closes a line at once, drawing nothing it held', async () => {
    await home();
    await openLine(NEW);

    fireEvent.press(lineHeader(NEW));

    expect(
      screen.queryByTestId(`joiner-${JOINER.player_id}`, { includeHiddenElements: true }),
    ).toBeNull();
  });
});
