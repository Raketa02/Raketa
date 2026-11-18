/**
 * **Top 10 on Home — FOR YOU's last line — walked through the real route tree**
 * ([#805](https://github.com/Raketa02/Raketa/issues/805), PRD #789; [#820](https://github.com/Raketa02/Raketa/issues/820),
 * [#821](https://github.com/Raketa02/Raketa/issues/821); ADR-0204, ADR-0205 §5; the Home rows
 * mechanics §3, §10, §12; the screens §7; the words §31.1, §31.11), with only `fetch` faked. Every
 * test opens the line first, as a player would: closed, it draws no card, no switcher and no link;
 * open, its foot holds the switcher, *Padel ›*, on the left, opening rightwards, and *Open the
 * rankings ›* on the right.
 *
 * Tomek is 7th of the ten in padel at 2,71, *▲ 1*; Inés leads at 3,40, *▼ 1*; **Marek, at 4th, and
 * Tomek have blocked each other** — the row shows him at his true place, and his record reads *This
 * record isn't available*. Two are ranked in squash, kuba.w and zofia.b; nobody in badminton; tennis
 * has a few. **The server falls through on `prefer`** as the backend does: the sport asked if anybody
 * is ranked there, else the next in the app's order where somebody is, going round.
 *
 * Every assertion is about what the player can see, or what left the device.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { RefreshControl, StyleSheet, type ViewStyle } from 'react-native';
import { Text as SvgText } from 'react-native-svg';

import { FRIENDS_COPY } from '@/features/friends/types';
import { OWN_RECORD_TITLE, RECORD_TITLE, RECORD_UNAVAILABLE } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { savePhonePreference } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import { footerParts, isOpen, lineHeader, lineTitles, openLine } from '@/test-support/forYou';
import {
  GATE_USER,
  HOME_PATH,
  HOTTEST_GROUPS_PATH,
  NEW_IN_RAKETA_PATH,
  OWN_RECORD_SERVED,
  SAME_LEVEL_PATH,
  SAME_VIBE_PATH,
  TOP_TEN_PATH,
  launchSignedIn,
  ratingGuideAlreadyShown,
  stubGate,
  stubHome,
  stubOwnRecord,
} from '@/test-support/onboardingRouter';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { TOP_TEN_COPY, nobodyRankedLine, topTenRankingsLabel } from './rankingsCopy';

const HIDDEN = { includeHiddenElements: true } as const;
const SPORT_ORDER = ['PADEL', 'TENNIS', 'SQUASH', 'BADMINTON'] as const;

const recordPath = (playerId: string) => `/api/v1/players/${playerId}/record`;
const rankingPath = (sport: Wire['Sport']) => `/api/v1/rankings/${sport}`;
const REQUESTS_PATH = '/api/v1/friends/requests';

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.7,
    confidence: 24,
    range: { low: mu - 0.7, high: mu + 0.7 },
    band: { name: 'Established', lower: 2.65, upper: 3.85 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-11-07T09:00:00Z',
  };
}

function card(
  place: number,
  nickname: string,
  level: number,
  over: Partial<Wire['TopTenPlayerSchema']> = {},
): Wire['TopTenPlayerSchema'] {
  return {
    place,
    player_id: `e0000000-0000-4000-8000-0000000805${String(place).padStart(2, '0')}`,
    nickname,
    photo_id: null,
    photo_url: null,
    level,
    chip: null,
    is_you: false,
    ...over,
  };
}

const INES = card(1, 'ines.d', 3.4, { chip: { kind: 'DOWN', places: 1 } });
const STAS = card(2, 'stas.w', 3.05, { chip: { kind: 'UP', places: 2 } });
const MAREK = card(4, 'marek.b', 2.92);
const TOMEK = card(7, GATE_USER.nickname ?? 'tomek.k', 2.71, {
  player_id: GATE_USER.id,
  chip: { kind: 'UP', places: 1 },
  is_you: true,
});
const MAGDA = card(10, 'magda.p', 2.66, { chip: { kind: 'UP', places: 3 } });
const PADEL: readonly Wire['TopTenPlayerSchema'][] = [
  INES,
  STAS,
  card(3, 'piotr.s', 2.95),
  MAREK,
  card(5, 'ewa.k', 2.8),
  card(6, 'karol.t', 2.75),
  TOMEK,
  card(8, 'zofia.b', 2.69, { chip: { kind: 'UP', places: 2 } }),
  card(9, 'ania.k', 2.68, { chip: { kind: 'DOWN', places: 1 } }),
  MAGDA,
];
const KUBA = card(1, 'kuba.w', 2.9, {
  player_id: 'e0000000-0000-4000-8000-000000080551',
});
const ZOFIA_SQUASH = card(2, 'zofia.b', 2.55, {
  player_id: 'e0000000-0000-4000-8000-000000080552',
});
const TENNIS: readonly Wire['TopTenPlayerSchema'][] = [
  card(1, 'kasia.m', 3.6, { player_id: 'e0000000-0000-4000-8000-000000080561' }),
  card(2, 'jan.k', 3.35, { player_id: 'e0000000-0000-4000-8000-000000080562' }),
];

let transport: Transport;

interface TopTenServer {
  /** Answer one sport's reads with these, from now on. */
  readonly rank: (sport: Wire['Sport'], players: readonly Wire['TopTenPlayerSchema'][]) => void;
  /** Hold the next reads until the returned release. */
  readonly hold: () => () => void;
  /** Refuse every read of this sport, named exactly, with this code. */
  readonly refuse: (sport: Wire['Sport']) => void;
}

/**
 * **Tomek, rated in padel and tennis**, with Home's trophy as given, every sport as above, the records
 * a card opens, and the Rankings page `Open the rankings ›` lands on.
 */
function topTenServer({
  trophy = { sport: 'PADEL', general_place: 7, friends_place: null },
  ratings = [rating('PADEL', 2.71), rating('TENNIS', 3.1)],
  ranked = { PADEL: PADEL, TENNIS: TENNIS, SQUASH: [KUBA, ZOFIA_SQUASH], BADMINTON: [] },
}: {
  readonly trophy?: Wire['HomeRankingSchema'] | null;
  readonly ratings?: readonly Wire['RatingResponse'][];
  readonly ranked?: Readonly<Record<Wire['Sport'], readonly Wire['TopTenPlayerSchema'][]>>;
} = {}): TopTenServer {
  stubGate(transport, { ratings: [...ratings], hasPlayerProfile: true });
  stubHome(transport, { ranking: trophy });
  stubOwnRecord(transport, OWN_RECORD_SERVED);

  const lists = new Map<Wire['Sport'], readonly Wire['TopTenPlayerSchema'][]>(
    Object.entries(ranked) as [Wire['Sport'], readonly Wire['TopTenPlayerSchema'][]][],
  );
  const refused = new Set<Wire['Sport']>();
  let held: Promise<void> | undefined;

  transport.on('GET', TOP_TEN_PATH, async (request) => {
    if (held !== undefined) await held;
    const query = new URLSearchParams(request.path.split('?')[1] ?? '');
    const exactly = query.get('sport') as Wire['Sport'] | null;
    const preferred = query.get('prefer') as Wire['Sport'] | null;
    if (exactly !== null && refused.has(exactly)) return errorResponse(404, 'not_found');
    const anyone = [...lists.values()].some((players) => players.length > 0);
    let sport = (exactly ?? preferred)!;
    if (exactly === null && anyone) {
      const from = SPORT_ORDER.indexOf(sport);
      sport = [...SPORT_ORDER.slice(from), ...SPORT_ORDER.slice(0, from)].find(
        (each) => (lists.get(each) ?? []).length > 0,
      )!;
    }
    return json<Wire['TopTenResponse']>({
      sport,
      anyone_listed: anyone,
      players: [...(lists.get(sport) ?? [])],
    });
  });

  for (const player of [...PADEL, ...TENNIS, KUBA, ZOFIA_SQUASH]) {
    if (player.is_you || player === MAREK) continue;
    transport.on('GET', recordPath(player.player_id), () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'NONE',
        can_add_friend: true,
        nickname: player.nickname,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: player.level, band: 'Established' }],
        reliability: servedReliability({ player_score: 96, is_new: false }),
      }),
    );
  }
  // A block either way closes the record, with the one refusal that names nothing.
  transport.on('GET', recordPath(MAREK.player_id), () => errorResponse(404, 'record_unavailable'));
  transport.on('POST', REQUESTS_PATH, () => json<Wire['RelationResponse']>({ relation: 'SENT' }));

  // The page `Open the rankings ›` opens — what is on it is the Rankings suite's.
  for (const sport of SPORT_ORDER) {
    transport.on('GET', rankingPath(sport), () =>
      json<Wire['RankingResponse']>({
        sport,
        view: 'GENERAL',
        card: {
          state: 'NO_LEVEL',
          results: 0,
          results_to_enter: 5,
          place: null,
          of: null,
          level: null,
          chip: null,
          gap_line: null,
        },
        listed: 0,
        podium: [],
        rows: [],
        next: null,
      }),
    );
  }

  return {
    rank: (sport, players) => lists.set(sport, players),
    hold: () => {
      let release: () => void = () => {};
      held = new Promise<void>((resolve) => {
        release = () => {
          held = undefined;
          resolve();
        };
      });
      return release;
    },
    refuse: (sport) => refused.add(sport),
  };
}

beforeEach(async () => {
  transport = installTransport();
  await ratingGuideAlreadyShown();
});

afterEach(async () => {
  jest.useRealTimers();
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

// ---------------------------------------------------------------------------
// Walking
// ---------------------------------------------------------------------------

const reads = () => transport.requestsTo('GET', TOP_TEN_PATH).map((request) => request.url);
const row = () => within(screen.getByTestId('top-ten'));
const cardOf = (player: Wire['TopTenPlayerSchema']) =>
  screen.getByTestId(`top-ten-card-${player.player_id}`);
/** The cards drawn, left to right, by player. */
const cardsDrawn = () =>
  screen
    .queryAllByTestId(/^top-ten-card-/)
    .map((node) => (node.props.testID as string).replace('top-ten-card-', ''));
const pill = (sport: string) => row().getByRole('button', { name: `Sport: ${sport}` });
/** What stands in the open line's footer, left to right — the switcher, the link. */
const footer = () =>
  footerParts(row().getByTestId('folding-line-footer'), (part) =>
    within(part).queryByRole('button', { name: /^Sport:/ }) === null
      ? 'something else'
      : 'switcher',
  );

async function homeWithTheRow() {
  await launchSignedIn();
  await openLine(TOP_TEN_COPY.line);
}

function unfold(current: string) {
  fireEvent.press(pill(current));
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
}

function pickOnThePill(current: string, sport: string) {
  unfold(current);
  fireEvent.press(within(screen.getByTestId('sport-bar')).getByRole('button', { name: sport }));
}

/** The fills of a card's numeral, each figure's — a gradient's url, or a colour. */
function numeralFills(player: Wire['TopTenPlayerSchema']): string[] {
  return within(cardOf(player))
    .UNSAFE_getAllByType(SvgText)
    .map((figure) => figure.props.fill as string)
    .filter((fill) => fill !== 'none');
}

// ---------------------------------------------------------------------------
// The line
// ---------------------------------------------------------------------------

describe('the line on Home', () => {
  it('stands last of FOR YOU’s lines, closed — no card, no switcher, no Open the rankings ›', async () => {
    topTenServer();
    await launchSignedIn();

    await screen.findByRole('button', { name: TOP_TEN_COPY.line });
    expect(lineTitles().at(-1)).toBe(TOP_TEN_COPY.line);
    expect(isOpen(TOP_TEN_COPY.line)).toBe(false);
    expect(cardsDrawn()).toEqual([]);
    expect(row().queryByRole('button', { name: /^Sport:/ })).toBeNull();
    expect(row().queryByRole('link')).toBeNull();
    expect(row().queryByText(TOP_TEN_COPY.rankings)).toBeNull();
  });

  /**
   * ADR-0205 §5, #821, home refactor 12, 13: the switcher, *Padel ›*, at the open line's foot on the
   * left, and *Open the rankings ›* on the right.
   */
  it('opens onto the cards, Padel › at its foot’s left and Open the rankings › at its right', async () => {
    topTenServer();
    await homeWithTheRow();

    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));
    const switcher = await row().findByRole('button', { name: 'Sport: Padel' });
    expect(within(switcher).getByText('Padel')).toBeTruthy();
    expect(within(switcher).getByText('›', HIDDEN)).toBeTruthy();
    const link = row().getByRole('link', { name: 'Open the rankings in padel' });
    expect(within(link).getByText('Open the rankings')).toBeTruthy();
    expect(within(link).getByText('›', HIDDEN)).toBeTruthy();
    // The switcher first, at the footer's left; the link ends the row, at its right.
    expect(footer()).toEqual(['switcher', 'link']);
    expect(StyleSheet.flatten(link.props.style as ViewStyle)).toMatchObject({ marginLeft: 'auto' });
  });

  it('is hidden while nobody is ranked in any sport', async () => {
    topTenServer({ ranked: { PADEL: [], TENNIS: [], SQUASH: [], BADMINTON: [] } });
    await launchSignedIn();

    await waitFor(() => expect(reads().length).toBeGreaterThan(0));
    await screen.findByText(/^Your games/);
    expect(screen.queryByRole('button', { name: TOP_TEN_COPY.line })).toBeNull();
  });

  it('is left out when its read fails, and the rest of Home stands', async () => {
    topTenServer();
    transport.on('GET', TOP_TEN_PATH, () => errorResponse(404, 'not_found'));
    await launchSignedIn();

    await waitFor(() => expect(reads().length).toBeGreaterThan(0));
    expect(await screen.findByText(/^Your games/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: TOP_TEN_COPY.line })).toBeNull();
  });
});

describe('which sport it opens on', () => {
  it('asks for the trophy’s sport as the preferred one', async () => {
    topTenServer({ trophy: { sport: 'TENNIS', general_place: 3, friends_place: null } });
    await homeWithTheRow();

    expect(reads()[0]).toContain('prefer=TENNIS');
    expect(reads()[0]).not.toContain('sport=');
    expect(await row().findByRole('button', { name: 'Sport: Tennis' })).toBeTruthy();
    expect(cardsDrawn()).toEqual(TENNIS.map((player) => player.player_id));
  });

  it('falls through to the next sport where somebody is ranked, and the pill says which', async () => {
    topTenServer({
      trophy: { sport: 'BADMINTON', general_place: null, friends_place: null },
    });
    await homeWithTheRow();

    expect(reads()[0]).toContain('prefer=BADMINTON');
    // Badminton is empty, and the order goes round to padel.
    expect(await row().findByRole('button', { name: 'Sport: Padel' })).toBeTruthy();
    expect(cardsDrawn()).toHaveLength(10);
  });

  it('is the deck’s last sport when the trophy names none', async () => {
    topTenServer({ trophy: null, ratings: [rating('PADEL', 2.71), rating('SQUASH', 2.4)] });
    await savePhonePreference(GATE_USER.id, 'lastSport', 'squash');
    await homeWithTheRow();

    expect(reads()[0]).toContain('prefer=SQUASH');
    expect(await row().findByRole('button', { name: 'Sport: Squash' })).toBeTruthy();
  });

  it('is padel with no level anywhere', async () => {
    topTenServer({ trophy: null, ratings: [] });
    await homeWithTheRow();

    expect(reads()[0]).toContain('prefer=PADEL');
  });

  it('asks for nothing until Home has said the trophy’s sport', async () => {
    topTenServer();
    let answer = () => {};
    const homeHeld = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('GET', HOME_PATH, async () => {
      await homeHeld;
      return json<Wire['HomeResponse']>({
        read_at: '2026-11-15T08:00:00Z',
        payments_to_confirm: [],
        needs_your_answer: { new_count: 0, watermark: null },
        needing_you: 0,
        games: [],
        friend_requests: [],
        friends_games: [],
        level_asks: [],
        ranking: { sport: 'TENNIS', general_place: 3, friends_place: null },
      });
    });
    await launchSignedIn();
    await waitFor(() => expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(0));

    // Nothing read for the deck's sport while the trophy's is on its way.
    expect(reads()).toHaveLength(0);

    // The launch's clock outruns the held read, which times out and is asked again: the row still
    // waits, and reads once Home has answered (the retry needs the async clock).
    await act(async () => answer());
    await act(async () => {
      await jest.advanceTimersByTimeAsync(20_000);
    });

    await waitFor(() => expect(reads()).toHaveLength(1));
    expect(reads()[0]).toContain('prefer=TENNIS');
  });
});

describe('the switcher', () => {
  /**
   * #821 (ADR-0205 §5, Q19, Q37): it slides open to the right — the current sport at the bar's left
   * end, where the pill stood, its chevron turned back, and the others after it.
   */
  it('slides open to the right: the current sport first, where the pill stood, then the other three', async () => {
    topTenServer();
    await homeWithTheRow();
    fireEvent(await row().findByTestId('row-sport-pill'), 'layout', {
      nativeEvent: { layout: { x: 0, y: 7, width: 90, height: 30 } },
    });

    unfold('Padel');

    const bar = within(screen.getByTestId('sport-bar'));
    expect(
      bar.getAllByRole('button').map((option) => option.props.accessibilityLabel as string),
    ).toEqual(['Padel', 'Tennis', 'Squash', 'Badminton']);
    expect(within(bar.getByRole('button', { name: 'Padel' })).getByText('‹', HIDDEN)).toBeTruthy();
    expect(
      StyleSheet.flatten(screen.getByTestId('row-sport-bar-slot').props.style as ViewStyle),
    ).toMatchObject({
      left: -theme.size.groupPage.filterPad,
      right: 0,
      top: 7,
      alignItems: 'flex-start',
    });
    // Open, it lies over the footer, and a tap on it folds the bar rather than leaving Home.
    fireEvent.press(screen.getByTestId('sport-filter-backdrop', HIDDEN));
    expect(screen.queryByTestId('sport-bar')).toBeNull();
    expect(screen).toHavePathname('/');
  });

  it('a pick reads that sport exactly, and nothing else on Home', async () => {
    const server = topTenServer();
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));
    const others = () =>
      [HOME_PATH, HOTTEST_GROUPS_PATH, NEW_IN_RAKETA_PATH, SAME_LEVEL_PATH, SAME_VIBE_PATH].map(
        (path) => transport.requestsTo('GET', path).length,
      );
    const before = others();
    const release = server.hold();

    pickOnThePill('Padel', 'Squash');

    // The pill says squash at once, and the padel cards stay until the squash ones land.
    expect(await row().findByRole('button', { name: 'Sport: Squash' })).toBeTruthy();
    expect(cardsDrawn()).toHaveLength(10);
    await act(async () => release());

    await waitFor(() => expect(cardsDrawn()).toEqual([KUBA.player_id, ZOFIA_SQUASH.player_id]));
    expect(reads().at(-1)).toContain('sport=SQUASH');
    expect(reads().at(-1)).not.toContain('prefer=');
    expect(others()).toEqual(before);
    expect(isOpen(TOP_TEN_COPY.line)).toBe(true);
  });

  it('reads Nobody ranked in badminton yet for a sport with nobody in it', async () => {
    topTenServer();
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));

    pickOnThePill('Padel', 'Badminton');

    expect(await row().findByText(nobodyRankedLine('badminton'))).toBeTruthy();
    expect(cardsDrawn()).toEqual([]);
    // The line, the switcher and Open the rankings › stay.
    expect(row().getByRole('button', { name: 'Sport: Badminton' })).toBeTruthy();
    expect(row().getByRole('link', { name: topTenRankingsLabel('badminton') })).toBeTruthy();
  });

  /**
   * A second pick cancels the first's read, so when the second is refused the pick it goes back to has
   * nothing read yet: the cards drawn stay, and the line stays open under the reader (#820).
   */
  it('stays open on a second pick before the first lands, the second refused', async () => {
    const server = topTenServer();
    server.refuse('TENNIS');
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));
    const release = server.hold();

    pickOnThePill('Padel', 'Squash');
    pickOnThePill('Squash', 'Tennis');
    await act(async () => release());

    await waitFor(() => expect(reads().some((url) => url.includes('sport=TENNIS'))).toBe(true));
    expect(await row().findByRole('button', { name: 'Sport: Squash' })).toBeTruthy();
    await waitFor(() => expect(cardsDrawn()).toEqual([KUBA.player_id, ZOFIA_SQUASH.player_id]));
    expect(isOpen(TOP_TEN_COPY.line)).toBe(true);
  });

  /** The pick is the line's, not what it unfolds: held while Home is up, a close included. */
  it('keeps the sport picked across a close and an open', async () => {
    topTenServer();
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));
    pickOnThePill('Padel', 'Squash');
    await waitFor(() => expect(cardsDrawn()).toEqual([KUBA.player_id, ZOFIA_SQUASH.player_id]));

    fireEvent.press(lineHeader(TOP_TEN_COPY.line));
    await waitFor(() => expect(cardsDrawn()).toEqual([]));
    await openLine(TOP_TEN_COPY.line);

    expect(await row().findByRole('button', { name: 'Sport: Squash' })).toBeTruthy();
    expect(cardsDrawn()).toEqual([KUBA.player_id, ZOFIA_SQUASH.player_id]);
  });

  it('puts the pill back, the cards never having left, when a pick cannot be read', async () => {
    const server = topTenServer();
    server.refuse('SQUASH');
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));

    pickOnThePill('Padel', 'Squash');

    await waitFor(() => expect(reads().at(-1)).toContain('sport=SQUASH'));
    expect(await row().findByRole('button', { name: 'Sport: Padel' })).toBeTruthy();
    expect(cardsDrawn()).toHaveLength(10);
  });
});

describe('the cards', () => {
  it('draws the ten in order, each with its numeral, nickname and level — 10 in two figures', async () => {
    topTenServer();
    await homeWithTheRow();

    await waitFor(() => expect(cardsDrawn()).toEqual(PADEL.map((one) => one.player_id)));
    const ines = within(cardOf(INES));
    expect(ines.getByText('ines.d')).toBeTruthy();
    expect(ines.getByText('3,40')).toBeTruthy();
    expect(
      within(cardOf(INES)).getByTestId('top-ten-numeral', HIDDEN).props.accessibilityLabel,
    ).toBeUndefined();
    expect(
      within(cardOf(INES))
        .UNSAFE_getAllByType(SvgText)
        .map((figure) => figure.props.children),
    ).toContain('1');
    const tenFigures = within(cardOf(MAGDA))
      .UNSAFE_getAllByType(SvgText)
      .map((figure) => figure.props.children as string);
    expect(new Set(tenFigures)).toEqual(new Set(['1', '0']));
    expect(
      screen.getByRole('button', { name: '1st, ines.d, 3,40, down 1 this week' }),
    ).toBeTruthy();
  });

  it('draws one or two cards when only one or two are ranked', async () => {
    topTenServer({ trophy: { sport: 'SQUASH', general_place: null, friends_place: null } });
    await homeWithTheRow();

    await waitFor(() => expect(cardsDrawn()).toEqual([KUBA.player_id, ZOFIA_SQUASH.player_id]));
    expect(row().getByText('kuba.w')).toBeTruthy();
    expect(row().getByText('zofia.b')).toBeTruthy();
  });

  it('draws a lone card when only one is ranked', async () => {
    topTenServer({
      trophy: { sport: 'SQUASH', general_place: null, friends_place: null },
      ranked: { PADEL: PADEL, TENNIS: TENNIS, SQUASH: [KUBA], BADMINTON: [] },
    });
    await homeWithTheRow();

    await waitFor(() => expect(cardsDrawn()).toEqual([KUBA.player_id]));
    expect(row().getByRole('button', { name: '1st, kuba.w, 2,90' })).toBeTruthy();
  });

  it('reads You on the reader’s own card, its numeral volt and the card ringed in volt', async () => {
    topTenServer();
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));

    const mine = within(cardOf(TOMEK));
    expect(mine.getByText('You')).toBeTruthy();
    expect(mine.queryByText(TOMEK.nickname)).toBeNull();
    expect(numeralFills(TOMEK).every((fill) => fill === theme.color.volt)).toBe(true);
    expect(
      StyleSheet.flatten(mine.getByTestId('top-ten-ring', HIDDEN).props.style as ViewStyle),
    ).toMatchObject({ borderColor: theme.color.volt, borderWidth: theme.size.topTen.ring });

    // Anybody else's: the gradient, and no ring.
    expect(numeralFills(INES).every((fill) => fill.startsWith('url(#'))).toBe(true);
    expect(within(cardOf(INES)).queryByTestId('top-ten-ring', HIDDEN)).toBeNull();
  });

  it('draws ▲ and ▼ with their counts, and no chip for no change or New', async () => {
    topTenServer();
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));

    const down = within(cardOf(INES)).getByTestId('top-ten-chip-DOWN', HIDDEN);
    expect(within(down).getByText('1', HIDDEN)).toBeTruthy();
    const up = within(cardOf(STAS)).getByTestId('top-ten-chip-UP', HIDDEN);
    expect(within(up).getByText('2', HIDDEN)).toBeTruthy();
    expect(within(cardOf(MAREK)).queryByTestId(/^top-ten-chip-/, HIDDEN)).toBeNull();
  });
});

describe('a card opens the record', () => {
  it('opens a stranger’s record on the row’s sport, and asks from the ranking', async () => {
    topTenServer();
    await homeWithTheRow();

    fireEvent.press(await screen.findByRole('button', { name: /^2nd, stas\.w/ }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', recordPath(STAS.player_id))).toHaveLength(1),
    );
    expect(transport.requestsTo('GET', recordPath(STAS.player_id))[0]!.url).toContain(
      'sport=PADEL',
    );

    fireEvent.press(await screen.findByRole('button', { name: FRIENDS_COPY.record.add }));

    await waitFor(() =>
      expect(transport.requestsTo('POST', REQUESTS_PATH).map((one) => one.body)).toEqual([
        { player_id: STAS.player_id, made_from: 'RANKING', sport: 'PADEL' },
      ]),
    );
  });

  it('reads This record isn’t available across a block', async () => {
    topTenServer();
    await homeWithTheRow();

    fireEvent.press(await screen.findByRole('button', { name: /^4th, marek\.b/ }));

    expect(await screen.findByText(RECORD_UNAVAILABLE)).toBeTruthy();
  });

  it('opens the reader’s own record from their own card', async () => {
    topTenServer();
    await homeWithTheRow();

    fireEvent.press(await screen.findByRole('button', { name: /^7th, You/ }));

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
    expect(transport.requestsTo('GET', recordPath(TOMEK.player_id))).toHaveLength(0);
  });
});

describe('Open the rankings ›', () => {
  it('opens the Rankings page on the row’s sport, in General, with the Home tab lit', async () => {
    topTenServer();
    // Friends was the last look; Top 10 is drawn from General, so the page opens there.
    await savePhonePreference(GATE_USER.id, 'rankingView', 'FRIENDS');
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));
    pickOnThePill('Padel', 'Squash');
    await waitFor(() => expect(cardsDrawn()).toHaveLength(2));

    // Named by what it opens, in the sport picked.
    fireEvent.press(row().getByRole('link', { name: 'Open the rankings in squash' }));

    await waitFor(() => expect(screen).toHavePathname('/rankings'));
    await waitFor(() =>
      expect(transport.requestsTo('GET', rankingPath('SQUASH')).length).toBeGreaterThan(0),
    );
    expect(transport.requestsTo('GET', rankingPath('SQUASH'))[0]!.url).toContain('view=GENERAL');
    expect(transport.requestsTo('GET', rankingPath('PADEL'))).toHaveLength(0);
    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();
  });
});

describe('reading it again', () => {
  it('reads the row again on Home’s pull, in the sport it is on', async () => {
    topTenServer();
    await homeWithTheRow();
    await waitFor(() => expect(cardsDrawn()).toHaveLength(10));
    const before = reads().length;

    await act(async () => {
      fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');
    });

    await waitFor(() => expect(reads().length).toBeGreaterThan(before));
    expect(reads().at(-1)).toContain('prefer=PADEL');
  });
});
