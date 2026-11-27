/**
 * **Rows stay alive — the cards that came on screen, reported** — walked through the real route tree
 * with the fake clock ([#804](https://github.com/Raketa02/Raketa/issues/804), PRD #789;
 * [#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0204, ADR-0205 §5; the Home rows
 * mechanics §9.2; the backend's #796).
 *
 * The phone tells the server which cards of *Same competitive level* and *Same vibe* came at least
 * half on screen, so that a card seen on five days without an add gives its place to a fresh match.
 *
 * - **On screen** is geometry: the page scrolled to the line, and the line's own rail scrolled to the
 *   card. Nothing is laid out under the harness, so the suite lays Home out as a phone would
 *   (`test-support/onScreen.ts`), each line below the fold until the page is scrolled to it.
 * - **Only an open line reports**: a closed line draws no card (FOR YOU, #820).
 * - **Once per card, row and Warsaw day**, batched, a failure carried into the next batch and never
 *   said; **See all** reports nothing.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { moveAppTo, stopWatchingAppState, watchAppState } from '@/test-support/appState';
import { lineHeader, openLine } from '@/test-support/forYou';
import {
  SAME_LEVEL_ALL_PATH,
  launchSignedIn,
  stubGate,
  stubSameLevel,
  stubSameVibe,
} from '@/test-support/onboardingRouter';
import {
  ON_SCREEN_PATH,
  PAGE_HEIGHT,
  layOutHome,
  pageAtRow,
  scrollHomeTo,
  scrollRowToCard,
} from '@/test-support/onScreen';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { REPORT_BATCH_MS } from '../domain/onScreen';
import { rereadDiscovery } from '../hooks/useNewInRakieta';

import { DISCOVERY_COPY } from './discoveryCopy';

const level = (n: number, nickname: string): Wire['SameLevelPlayerSchema'] => {
  const padel: Wire['SameLevelSportSchema'] = {
    sport: 'PADEL',
    your_level: 2.71,
    their_level: 2.69,
    percent_even: 91,
    level_gap: -0.02,
    your_band: { name: 'Established', lower: 2.65, upper: 3.85 },
  };
  return {
    player_id: `e0000000-0000-4000-8000-0000000004${String(n).padStart(2, '0')}`,
    nickname,
    photo_id: null,
    photo_url: null,
    shown: padel,
    sports: [padel],
    relation: 'NONE',
  };
};

const vibe = (n: number, nickname: string): Wire['SameVibePlayerSchema'] => ({
  player_id: `e0000000-0000-4000-8000-0000000005${String(n).padStart(2, '0')}`,
  nickname,
  photo_id: null,
  photo_url: null,
  vibe_percent: 75,
  in_common: 2,
  shared_tags: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN'],
  relation: 'NONE',
});

/** Same competitive level, in the read's order: Kuba first, then Zofia, Marek and Ola. */
const KUBA = level(1, 'kuba.w');
const ZOFIA = level(2, 'zofia.b');
const MAREK = level(3, 'marek.s');
const OLA = level(4, 'ola.n');
const SAME_LEVEL = [KUBA, ZOFIA, MAREK, OLA];

/** Same vibe: Karol first, then Ania. */
const KAROL = vibe(1, 'karol.t');
const ANIA = vibe(2, 'ania.k');
const SAME_VIBE = [KAROL, ANIA];

/** Where each row stands on Home's page — both well below the fold of a 700-tall page. */
const ROWS = { 'same-level': 1000, 'same-vibe': 1600 } as const;

/** Sunday 15 November 2026, 11:00 in Warsaw. */
const SUNDAY = '2026-11-15T10:00:00Z';
/** Monday 16 November, 11:00 in Warsaw. */
const MONDAY = '2026-11-16T10:00:00Z';

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  stopWatchingAppState();
  transport.restore();
  queryClient.clear();
  useToastQueue.setState({ queue: [] });
  resetSessionStatus();
  await clearStoredTokens();
});

type Report = Wire['OnScreenRequest'];
const reports = () =>
  transport.requestsTo('POST', ON_SCREEN_PATH).map((request) => request.body as Report);

/** The line each row is, by its test id. */
const TITLE = {
  'same-level': DISCOVERY_COPY.sameLevel.line,
  'same-vibe': DISCOVERY_COPY.sameVibe.line,
} as const;

/** Home with both lines shown, on Sunday — nothing open yet. */
async function homeClosed() {
  stubGate(transport, { hasPlayerProfile: true });
  stubSameLevel(transport, SAME_LEVEL);
  stubSameVibe(transport, SAME_VIBE);
  transport.on('POST', ON_SCREEN_PATH, () => noContent());
  await launchSignedIn();
  jest.setSystemTime(new Date(SUNDAY));
  await screen.findByRole('button', { name: TITLE['same-level'] });
  await screen.findByRole('button', { name: TITLE['same-vibe'] });
}

/**
 * Home with one line open — *Same competitive level*'s, unless a test asks for *Same vibe*'s — laid
 * out below the fold, on Sunday. One line is open at a time, so the other draws no card.
 */
async function home(open: keyof typeof ROWS = 'same-level') {
  await homeClosed();
  await openLine(TITLE[open]);
  layOutHome(ROWS);
}

/**
 * **The batch window passes, and whatever it sent has reached the socket** — on the async clock, so
 * a report's own promises run between the timers, and a while after, so that *nothing more was
 * sent* is a fact and not a report still on its way.
 */
async function batchCloses() {
  await act(() => jest.advanceTimersByTimeAsync(REPORT_BATCH_MS));
  await act(() => jest.advanceTimersByTimeAsync(REPORT_BATCH_MS));
}

describe('a card on screen', () => {
  it('is reported once it comes at least half into view, and not before', async () => {
    await home();
    await batchCloses();
    expect(reports()).toEqual([]);

    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([{ row: 'SAME_LEVEL', player_ids: [KUBA.player_id] }]),
    );
  });

  it('is not reported again the same day, scrolled out and back in', async () => {
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));

    scrollHomeTo('same-level', 0);
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    scrollRowToCard('same-level', 1);
    scrollRowToCard('same-level', 0);
    await batchCloses();

    expect(reports()).toEqual([
      { row: 'SAME_LEVEL', player_ids: [KUBA.player_id] },
      { row: 'SAME_LEVEL', player_ids: [ZOFIA.player_id] },
    ]);
  });

  it('counts across the row’s own scroll: the card it is scrolled to, never the one peeking', async () => {
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    scrollRowToCard('same-level', 2);
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id, MAREK.player_id] },
      ]),
    );
  });

  it('counts a card only once at least half of it is up the screen', async () => {
    await home();
    const railRisen = (seen: number) => pageAtRow(ROWS['same-level']) - PAGE_HEIGHT + seen;

    // The rail is 240 tall: 100 of it up from the bottom of the page is under half.
    scrollHomeTo('same-level', railRisen(100));
    await batchCloses();
    expect(reports()).toEqual([]);

    // 130 of 240 is over half.
    scrollHomeTo('same-level', railRisen(130));
    await batchCloses();
    await waitFor(() =>
      expect(reports()).toEqual([{ row: 'SAME_LEVEL', player_ids: [KUBA.player_id] }]),
    );
  });
});

describe('a day', () => {
  it('reports the same card again the next day', async () => {
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));

    jest.setSystemTime(new Date(MONDAY));
    scrollHomeTo('same-level', 0);
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id] },
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id] },
      ]),
    );
  });

  it('is Warsaw’s: ten past midnight there is a new day, though it is still Sunday in UTC', async () => {
    await home();
    // 23:50 on Sunday in Warsaw.
    jest.setSystemTime(new Date('2026-11-15T22:50:00Z'));
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));

    // 00:10 on Monday in Warsaw — 23:10 on Sunday in UTC.
    jest.setSystemTime(new Date('2026-11-15T23:10:00Z'));
    scrollRowToCard('same-level', 1);
    scrollRowToCard('same-level', 0);
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id] },
        { row: 'SAME_LEVEL', player_ids: [ZOFIA.player_id, KUBA.player_id] },
      ]),
    );
  });
});

/**
 * **A closed line draws no card, so it reports nobody** (#820; ADR-0205 §5; the mechanics §9.2): the
 * page scrolled right through FOR YOU tells nothing until a line is open, and only that line's.
 */
describe('a line', () => {
  it('reports nothing while closed, scrolled through, and its cards once it is open', async () => {
    await homeClosed();
    layOutHome(ROWS);
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    scrollHomeTo('same-vibe', pageAtRow(ROWS['same-vibe']));
    await batchCloses();
    expect(reports()).toEqual([]);

    await openLine(TITLE['same-level']);
    layOutHome(ROWS);
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([{ row: 'SAME_LEVEL', player_ids: [KUBA.player_id] }]),
    );
  });

  it('reports nothing more once closed, the page scrolled back to it', async () => {
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));

    fireEvent.press(lineHeader(TITLE['same-level']));
    jest.setSystemTime(new Date(MONDAY));
    scrollHomeTo('same-level', 0);
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();

    expect(reports()).toHaveLength(1);
  });

  it('reports only the open line’s cards — another line’s are not drawn', async () => {
    await home();
    scrollHomeTo('same-vibe', pageAtRow(ROWS['same-vibe']));
    await batchCloses();

    expect(reports().map((report) => report.row)).not.toContain('SAME_VIBE');
  });
});

describe('a card never on screen', () => {
  it('is never reported — the rest of the row, and the row below the fold', async () => {
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    scrollRowToCard('same-level', 1);
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));
    await batchCloses();

    const told = reports().flatMap((report) => report.player_ids);
    expect(told).toEqual([KUBA.player_id, ZOFIA.player_id]);
    expect(told).not.toContain(MAREK.player_id);
    expect(told).not.toContain(OLA.player_id);
    expect(reports().map((report) => report.row)).not.toContain('SAME_VIBE');
  });
});

describe('the reports', () => {
  it('are batched: the cards a scroll brings on screen go in one report', async () => {
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    scrollRowToCard('same-level', 1);
    scrollRowToCard('same-level', 2);
    expect(reports()).toEqual([]);

    await batchCloses();
    await waitFor(() =>
      expect(reports()).toEqual([
        {
          row: 'SAME_LEVEL',
          player_ids: [KUBA.player_id, ZOFIA.player_id, MAREK.player_id],
        },
      ]),
    );
  });

  it('keep each row’s own count: a Same vibe tile is told as Same vibe’s', async () => {
    await home('same-vibe');
    scrollHomeTo('same-vibe', pageAtRow(ROWS['same-vibe']));
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([{ row: 'SAME_VIBE', player_ids: [KAROL.player_id] }]),
    );
  });

  it('carry a failed report into the next batch, and never say a thing', async () => {
    await home();
    let refused = true;
    transport.on('POST', ON_SCREEN_PATH, () =>
      refused ? errorResponse(503, 'block_state_unavailable') : noContent(),
    );
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));
    await act(async () => {
      await Promise.resolve();
    });

    refused = false;
    scrollRowToCard('same-level', 1);
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id] },
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id, ZOFIA.player_id] },
      ]),
    );
    expect(useToastQueue.getState().queue).toEqual([]);
    expect(screen.queryByText(/try again/i)).toBeNull();

    // Both are told now: neither goes again today.
    scrollRowToCard('same-level', 0);
    scrollRowToCard('same-level', 1);
    await batchCloses();
    expect(reports()).toHaveLength(2);
  });
});

describe('a Home out of view', () => {
  /** Same level's See all, pushed over Home — every card of the row on a page of its own. */
  async function openSeeAll() {
    transport.on('GET', SAME_LEVEL_ALL_PATH, () =>
      json<Wire['SameLevelPageResponse']>({ players: SAME_LEVEL, next: null, sports: ['PADEL'] }),
    );
    fireEvent.press(screen.getByRole('link', { name: DISCOVERY_COPY.sameLevel.seeAllLabel }));
    await waitFor(() => expect(screen).toHavePathname('/same-level'));
    await screen.findByTestId('same-level-list');
  }

  it('See all reports nothing, every card on it in view and scrolled through', async () => {
    await home();
    await openSeeAll();

    const list = screen.getByTestId('same-level-list');
    fireEvent(list, 'layout', { nativeEvent: { layout: { x: 0, y: 0, width: 390, height: 700 } } });
    fireEvent.scroll(list, {
      nativeEvent: {
        contentOffset: { x: 0, y: 400 },
        layoutMeasurement: { width: 390, height: 700 },
        contentSize: { width: 390, height: 1400 },
      },
    });
    await batchCloses();
    await batchCloses();

    expect(reports()).toEqual([]);
  });

  it('counts nothing that comes into a row under a pushed screen, until Home is back', async () => {
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));
    await openSeeAll();

    // Monday, and the row reads Ola first while See all covers it.
    jest.setSystemTime(new Date(MONDAY));
    stubSameLevel(transport, [OLA, KUBA, ZOFIA, MAREK]);
    await act(() => rereadDiscovery(queryClient));
    await batchCloses();
    expect(reports()).toHaveLength(1);

    fireEvent.press(screen.getByRole('button', { name: DISCOVERY_COPY.sameLevel.back }));
    await waitFor(() => expect(screen).toHavePathname('/'));
    await batchCloses();

    await waitFor(() =>
      expect(reports()).toEqual([
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id] },
        { row: 'SAME_LEVEL', player_ids: [OLA.player_id] },
      ]),
    );
  });

  it('counts nothing that comes into a row while the app is in the background, until it is back', async () => {
    watchAppState();
    await home();
    scrollHomeTo('same-level', pageAtRow(ROWS['same-level']));
    await batchCloses();
    await waitFor(() => expect(reports()).toHaveLength(1));

    // The phone goes to the home screen overnight; Monday's re-read lands behind it.
    act(() => moveAppTo('background'));
    jest.setSystemTime(new Date(MONDAY));
    stubSameLevel(transport, [OLA, KUBA, ZOFIA, MAREK]);
    await act(() => rereadDiscovery(queryClient));
    await batchCloses();
    expect(reports()).toHaveLength(1);

    act(() => moveAppTo('active'));
    await batchCloses();
    await waitFor(() =>
      expect(reports()).toEqual([
        { row: 'SAME_LEVEL', player_ids: [KUBA.player_id] },
        { row: 'SAME_LEVEL', player_ids: [OLA.player_id] },
      ]),
    );
  });
});
