/**
 * **FOR YOU on Home** — the five discovery rows folded into five quiet lines, walked through the real
 * route tree ([#820](https://github.com/Rakieta02/Rakieta/issues/820); ADR-0205 §5, §8; the Home rows
 * screens §1, §2; home refactor 3–13).
 *
 * What each line holds, its footer and its hidden states are its feature's suite's
 * (`hottestGroups`, `sameLevel`, `newInRakieta`, `sameVibe`, `topTen`), the on-screen reports
 * `onScreen`'s, and the frame's look `FoldingLine.test.tsx`'s. This is the shell's part: where FOR YOU
 * stands and in what order, which line is open — one at a time, switching by a fold and then an
 * unfold, closed only from its header, kept across tabs — every read running whether a line is open or
 * not, the pull, the page shown what opened, Reduce motion, and the four lines' counts (#822).
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
import {
  isOpen,
  lineHeader,
  lineNamed,
  lineNames,
  lineTitles,
  openLine,
} from '@/test-support/forYou';
import {
  HOTTEST_GROUPS_PATH,
  NEW_IN_RAKIETA_PATH,
  SAME_LEVEL_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
  launchSignedIn,
  stubGate,
  stubHottestGroups,
  stubMyGroups,
  stubNewInRakieta,
  stubSameLevel,
  stubSameVibe,
  stubTopTen,
} from '@/test-support/onboardingRouter';
import { layOutHomeParts } from '@/test-support/onScreen';
import { scrollerOf } from '@/test-support/pinned';
import { PLAYERS_BAR } from '@/test-support/tabBarReach';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { HOME_COPY } from './shellCopy';

const GROUPS = GROUPS_COPY.hottest.line;
const LEVEL = DISCOVERY_COPY.sameLevel.line;
const NEW = DISCOVERY_COPY.newInRakieta.line;
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

const JOINER: Wire['NewInRakietaPlayerSchema'] = {
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
  stubNewInRakieta(transport, [JOINER]);
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
  NEW_IN_RAKIETA_PATH,
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

    expect(screen.getByRole('button', { name: lineNamed(LEVEL), expanded: false })).toBeTruthy();
    await openLine(LEVEL);
    expect(screen.getByRole('button', { name: lineNamed(LEVEL), expanded: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: lineNamed(NEW), expanded: false })).toBeTruthy();
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
    transport.on('GET', NEW_IN_RAKIETA_PATH, async () => {
      await answered;
      return json<Wire['NewInRakietaResponse']>({ players: [JOINER], total: 1 });
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
    layOutHomeParts();
    act(() => {
      // 700 shows above the bar; the scroller runs under it to the phone's foot (#881).
      fireEvent(page as never, 'layout', layout(0, 700 + PLAYERS_BAR));
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
    await screen.findByRole('button', { name: lineNamed(GROUPS), expanded: true });
    const page = scrollerOf(screen.getByTestId('for-you')) as unknown as {
      readonly instance: ScrollView;
    };
    const scrollTo = jest.spyOn(page.instance, 'scrollTo');
    scrollTo.mockClear();
    const layout = (y: number, height: number) => ({
      nativeEvent: { layout: { x: 0, y, width: 390, height } },
    });

    layOutHomeParts();
    act(() => {
      // 700 shows above the bar; the scroller runs under it to the phone's foot (#881).
      fireEvent(page as never, 'layout', layout(0, 700 + PLAYERS_BAR));
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

/**
 * **The counts** ([#822](https://github.com/Rakieta02/Rakieta/issues/822); ADR-0205 §5, §6; home
 * refactor 3, 4, 7): how many there are to explore on four lines — a grey pill between the title and
 * the chevron, the served total, *99+* past 99 — said in the line's name, carried into the people
 * lines' *See all N ›*, and moving whenever the line's read does.
 */
describe('the counts', () => {
  /** Pools larger than the one card each row serves: the count is the pool, never the cards. */
  async function counted({ hottest = 6, level = 14, joined = 6, vibe = 14 } = {}) {
    everyLine();
    stubHottestGroups(transport, [HOT_GROUP], hottest);
    stubSameLevel(transport, [AT_YOUR_LEVEL], level);
    stubNewInRakieta(transport, [JOINER], joined);
    stubSameVibe(transport, [WITH_YOUR_VIBE], vibe);
    await launchSignedIn();
    await screen.findByRole('button', { name: TOP });
    await waitFor(() => expect(lineTitles()).toHaveLength(5));
  }

  const pill = (line: string) =>
    screen.queryByTestId(`${line}-count`, { includeHiddenElements: true });
  /** What a line's pill writes. */
  const drawn = (line: string) =>
    within(pill(line)!).getByText(/./, { includeHiddenElements: true }).props.children as string;
  const footer = (line: string) =>
    within(within(screen.getByTestId(line)).getByTestId('folding-line-footer'));

  it('draws each line’s total in its pill — the pool, not the cards the row holds', async () => {
    await counted({ hottest: 6, level: 14, joined: 9, vibe: 37 });

    expect(drawn('hottest-groups')).toBe('6');
    expect(drawn('same-level')).toBe('14');
    expect(drawn('new-in-rakieta')).toBe('9');
    expect(drawn('same-vibe')).toBe('37');
  });

  it('draws no pill on Top 10', async () => {
    await counted();

    expect(pill('top-ten')).toBeNull();
  });

  /** ADR-0205 §6: the server counts up to 100, *100 or more*, drawn 99+. */
  it('writes 99+ past 99, and 99 as served', async () => {
    await counted({ hottest: 99, level: 100, joined: 100, vibe: 100 });

    expect(drawn('hottest-groups')).toBe('99');
    expect(drawn('same-level')).toBe('99+');
    expect(drawn('new-in-rakieta')).toBe('99+');
    expect(drawn('same-vibe')).toBe('99+');
  });

  /** ADR-0205 §5: the count pill stays when the line opens. */
  it('stays when the line opens', async () => {
    await counted();

    await openLine(LEVEL);

    expect(isOpen(LEVEL)).toBe(true);
    expect(drawn('same-level')).toBe('14');
  });

  /** #822's *Players at your level, 14, collapsed*. */
  it('is said in the line’s name, before whether it is expanded — and Top 10 says none', async () => {
    await counted({ level: 100 });

    expect(lineNames()).toEqual([`${GROUPS}, 6`, `${LEVEL}, 99+`, `${NEW}, 6`, `${VIBE}, 14`, TOP]);
    expect(screen.getByRole('button', { name: `${LEVEL}, 99+`, expanded: false })).toBeTruthy();
    await openLine(VIBE);
    expect(screen.getByRole('button', { name: `${VIBE}, 14`, expanded: true })).toBeTruthy();
  });

  /** Q34: *See all N ›* carries the line's figure, though See all shows one sport at a time. */
  it('reads See all N in each people line’s footer, the pill’s figure, 99+ included', async () => {
    await counted({ level: 14, joined: 100, vibe: 37 });

    for (const [title, line, words, label] of [
      [LEVEL, 'same-level', 'See all 14', DISCOVERY_COPY.sameLevel.seeAllLabel],
      [NEW, 'new-in-rakieta', 'See all 99+', DISCOVERY_COPY.newInRakieta.seeAllLabel],
      [VIBE, 'same-vibe', 'See all 37', DISCOVERY_COPY.sameVibe.seeAllLabel],
    ] as const) {
      await openLine(title);
      expect(footer(line).getByText(words)).toBeTruthy();
      // The link keeps its spoken name: the line's own has just said the count.
      expect(footer(line).getByRole('link', { name: label })).toBeTruthy();
    }
  });

  /** ADR-0205 §6: they refresh when the line's read does — here, the pull. Nothing new polls. */
  it('moves with a re-read: the pull brings each line’s new figure, in the pill and in See all', async () => {
    await counted();
    await openLine(LEVEL);
    stubHottestGroups(transport, [HOT_GROUP], 7);
    stubSameLevel(transport, [AT_YOUR_LEVEL], 100);
    stubNewInRakieta(transport, [JOINER], 5);
    stubSameVibe(transport, [WITH_YOUR_VIBE], 15);

    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });

    await waitFor(() => expect(drawn('same-level')).toBe('99+'));
    expect(footer('same-level').getByText('See all 99+')).toBeTruthy();
    expect(drawn('hottest-groups')).toBe('7');
    expect(drawn('new-in-rakieta')).toBe('5');
    expect(drawn('same-vibe')).toBe('15');
    expect(lineNames()[1]).toBe(`${LEVEL}, 99+`);
  });

  /**
   * Q22: coming back to Home re-reads a line read more than thirty seconds ago. Only that half can be
   * walked here: the harness runs every pending timer on a navigation, so its clock is always past the
   * app's `staleTime` by the time Home is back — a return within thirty seconds is Query's to hold.
   */
  it('moves on a return to Home once the read is older than thirty seconds', async () => {
    await counted();
    await openLine(VIBE);
    stubSameVibe(transport, [WITH_YOUR_VIBE], 15);

    fireEvent.press(screen.getByRole('link', { name: DISCOVERY_COPY.sameVibe.seeAllLabel }));
    await waitFor(() => expect(screen).toHavePathname('/same-vibe'));
    act(() => jest.advanceTimersByTime(31_000));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));

    await waitFor(() => expect(drawn('same-vibe')).toBe('15'));
    expect(footer('same-vibe').getByText('See all 15')).toBeTruthy();
  });
});
