/**
 * **A booked For-fun game reads the same as before it was booked** ([#841](https://github.com/Rakieta02/Rakieta/issues/841);
 * ADR-0207 §5, §6) — walked the way a player walks it: the real route tree, the real shell, and only
 * `fetch` faked.
 *
 * Ada's padel four filled and the court is booked. Opening the game from Home, she no longer reads
 * a forecast and *A friendly — nothing moves.* under the game card: she reads the **Social vibe
 * card** her details opened on before the last yes — how much the whole court shares, and who
 * shares her tags, a column each, her first, then the others as the tiles above stand. On the day,
 * at the court, the same details — *Who's here* now their door — still say it. A competitive game
 * draws its forecast and its stakes, as it always did.
 *
 * The card is `shared/ui`'s (`SocialVibeCard.test.tsx` there); the kind's rule is `games`'
 * `pairingCardOf` and the columns' `vibeColumnsOf`; what is asserted here is that the booked game is
 * wired to them.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { BALANCE_FORECAST, gameKeys } from '@/features/games/types';
import { SAVE, TAGS_TITLE, tagsLine } from '@/features/player_profile/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, SOCIAL_VIBE_CARD } from '@/shared/ui';
import {
  COUNTED_GAME_SENTENCE,
  LOSE_TILE,
  WIN_TILE,
} from '@/shared/vocabulary/forecastPresentation';
import {
  BARTEK,
  BOOKED_GAME,
  BOOKING,
  INES,
  PIOTR,
  bookedGameOnTheList,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import {
  GATE_USER,
  launchSignedIn,
  pairingPath,
  PROFILE_OPTIONS_SERVED,
  PROFILE_SURFACE_SERVED,
  stubGames,
  stubGate,
  stubOwnRecord,
  stubPairing,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { HOME_GAME_COPY } from './homeCopy';

const ME = GATE_USER.id;
const HIDDEN = { includeHiddenElements: true } as const;

/** The friendly's sentence the forecast drew under its figure — never on screen any more. */
const A_FRIENDLY = 'A friendly — nothing moves.';

/** Saturday, two days before the game — and at the court, ten minutes into its hour. */
const READ_AT = '2026-10-01T08:00:00Z';
const AT_THE_COURT = '2026-10-03T14:10:00Z';

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

/**
 * Ada's three tags, each carried **in her direction**, as #835 serves them: her, piotr.s on her
 * side, then ines.d and bartek.l across the net.
 */
const VIBE: Wire['GamePairingVibeSchema'] = {
  pct: 67,
  rows: [
    { tag: 'STAYS_FOR_A_DRINK', carried_by: [ME, BARTEK] },
    { tag: 'GENEROUS_ON_LINE_CALLS', carried_by: [ME, PIOTR, INES] },
    { tag: 'HERE_FOR_A_REGULAR_GAME', carried_by: [ME] },
  ],
};

const seat = (playerId: string, level: number): Wire['GamePairingSeatSchema'] => ({
  player_id: playerId,
  level,
  band: 'Established',
  range: { low: level - 0.16, high: level + 0.16 },
  confidence: 74,
});

/** The court's pairing: the forecast and the split are **still sent** on For fun, for older apps. */
function pairing(over: Partial<Wire['GamePairingResponse']> = {}): Wire['GamePairingResponse'] {
  return {
    read_at: READ_AT,
    forecast: { pct: 90, sigma_group: 0.4, provisional: false, assumption: null },
    split: { your_side: 2.83, their_side: 2.88, gap: -0.05 },
    seats: [seat(ME, 2.71), seat(PIOTR, 2.95), seat(INES, 3.4), seat(BARTEK, 2.35)],
    vibe: VIBE,
    ...over,
  };
}

/**
 * The Game behind the booking, as `GET /games` lists it. **Its seats stand in another order than
 * the booking's tiles** — bartek.l before ines.d — so a column read off the Game, rather than off
 * the tiles, would show.
 */
function theGame(kind: Wire['GameSchema']['kind']): Wire['GameSchema'] {
  return bookedGameOnTheList({
    kind,
    seats: [
      { side: 'A', player_id: ME, nickname: GATE_USER.nickname ?? 'Ada' },
      { side: 'A', player_id: PIOTR, nickname: 'piotr.s' },
      { side: 'B', player_id: BARTEK, nickname: 'bartek.l' },
      { side: 'B', player_id: INES, nickname: 'ines.d' },
    ],
  });
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

interface World {
  readonly kind?: 'FOR_FUN' | 'COMPETITIVE';
  readonly booking?: Partial<Wire['BookingDetailsResponse']>;
  readonly court?: Parameters<typeof stubPairing>[2];
  readonly readAt?: string;
}

/** In at the booked game's details, as Home's *Open game* pushes them. */
async function openTheGame({
  kind = 'FOR_FUN',
  booking = {},
  court = pairing(),
  readAt = READ_AT,
}: World = {}) {
  const details = bookingDetails({ kind, shows_forecast: true, read_at: readAt, ...booking });
  stubHomeGames(transport, [homeGame({ kind, status: details.status })]);
  stubBooking(transport, details);
  stubGames(transport, [theGame(kind === 'FOR_FUN' ? 'FRIENDLY' : 'COUNTED')], readAt);
  stubPairing(transport, BOOKED_GAME, court);

  await launchSignedIn(`/booking/${BOOKING}`);
  await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  await screen.findByLabelText('Back');
}

/**
 * **The pairing has answered and been drawn from** — an absence asserted before then would pass on
 * a screen that had not read it yet. The answer reaches the card on Query's next notify tick, a
 * timer under the harness's fake clock, so that tick is run too.
 */
async function pairingAnswered() {
  await waitFor(() =>
    expect(queryClient.getQueryState(gameKeys.pairing(BOOKED_GAME))?.status).toBe('success'),
  );
  act(() => jest.advanceTimersByTime(0));
}

const columns = () =>
  screen
    .getAllByTestId('social-vibe-column', HIDDEN)
    .map((column) => within(column).getByText(/.+/, HIDDEN).props.children as string);
const rows = () =>
  screen.getAllByTestId('social-vibe-row').map((row) => String(row.props.accessibilityLabel));
/** Which columns of a row carry a dot — one cell per column, in the columns' order. */
const dotted = (name: string) =>
  within(screen.getByLabelText(name))
    .getAllByTestId('social-vibe-cell', HIDDEN)
    .map((cell) => within(cell).queryByTestId('social-vibe-dot', HIDDEN) !== null);

describe('a booked For-fun game', () => {
  it('draws the Social vibe card, and no forecast or *A friendly — nothing moves.*', async () => {
    await openTheGame();

    const card = within(await screen.findByTestId(SOCIAL_VIBE_CARD));
    expect(card.getByRole('header', { name: 'Social vibe' })).toBeTruthy();
    expect(screen.getByLabelText('Social vibe, 67 percent, Good vibe')).toBeTruthy();
    expect(card.getByText('67%')).toBeTruthy();

    // The forecast still sent for older apps is ignored, its sentence with it.
    expect(screen.queryByText(A_FRIENDLY)).toBeNull();
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByText('90%')).toBeNull();
    expect(screen.queryByText(WIN_TILE)).toBeNull();
  });

  /** ADR-0207 §6: You first, then the others as the tiles above stand — not as the Game lists them. */
  it('heads its columns with You, then the others as the tiles stand', async () => {
    await openTheGame();

    await screen.findByTestId(SOCIAL_VIBE_CARD);
    expect(columns()).toEqual(['You', 'piotr.s', 'ines.d', 'bartek.l']);
  });

  it('draws your tags down the side, a dot under everybody who carries each', async () => {
    await openTheGame();

    await screen.findByTestId(SOCIAL_VIBE_CARD);
    expect(rows()).toEqual([
      'Stays for a drink: you, bartek.l',
      'Generous on line calls: you, piotr.s, ines.d',
      'Here for a regular game: you',
    ]);
    expect(dotted('Stays for a drink: you, bartek.l')).toEqual([true, false, false, true]);
    expect(dotted('Generous on line calls: you, piotr.s, ines.d')).toEqual([
      true,
      true,
      true,
      false,
    ]);
    expect(dotted('Here for a regular game: you')).toEqual([true, false, false, false]);
  });

  /** The forecast's split row said who partners whom; the vibe card does not, so the vs line does. */
  it('speaks who partners whom, since the vibe card does not', async () => {
    await openTheGame();

    await screen.findByTestId(SOCIAL_VIBE_CARD);
    expect(screen.getByLabelText('You and piotr.s against ines.d and bartek.l')).toBeTruthy();
  });

  /**
   * On the same occasions as the forecast: a booking that shows none mounts no card, so neither the
   * Game nor its pairing is asked for. The card is the details' one reader of the games list, and a
   * card mounted would put that read in the cache on its first render — before any answer — so its
   * absence there says the card was never mounted.
   */
  it('is not drawn, nor the pairing read, where the booking shows no forecast', async () => {
    await openTheGame({ booking: { shows_forecast: false } });

    await screen.findByLabelText('You and piotr.s against ines.d and bartek.l');
    act(() => jest.advanceTimersByTime(0));
    expect(queryClient.getQueryCache().find({ queryKey: gameKeys.list() })).toBeUndefined();
    expect(transport.requestsTo('GET', pairingPath(BOOKED_GAME))).toHaveLength(0);
    expect(screen.queryByTestId(SOCIAL_VIBE_CARD)).toBeNull();
  });

  /** A seat open, or nobody holding a tag that counts: no vibe, and the forecast does not stand in. */
  it('draws nothing in its place when the pairing sends no vibe', async () => {
    await openTheGame({ court: pairing({ vibe: undefined }) });

    await pairingAnswered();
    expect(screen.queryByTestId(SOCIAL_VIBE_CARD)).toBeNull();
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByText(A_FRIENDLY)).toBeNull();
    expect(screen.queryByText(/^\d+%$/)).toBeNull();
  });
});

describe('the same game at the court', () => {
  /** Ten minutes into the hour: the details' door is *Who's here*, and the card is still theirs. */
  it('draws the Social vibe card over the Who’s here door', async () => {
    await openTheGame({
      readAt: AT_THE_COURT,
      booking: { status: 'NEEDS_RESULT', needs_you: true, leaving: null },
      court: pairing({ read_at: AT_THE_COURT }),
    });

    expect(
      await screen.findByRole('button', { name: HOME_GAME_COPY.details.resultAct['whos-here'] }),
    ).toBeTruthy();
    expect(await screen.findByTestId(SOCIAL_VIBE_CARD)).toBeTruthy();
    expect(screen.getByLabelText('Social vibe, 67 percent, Good vibe')).toBeTruthy();
    expect(rows()).toHaveLength(3);
    expect(screen.queryByText(A_FRIENDLY)).toBeNull();
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
  });
});

describe('a booked competitive game', () => {
  /** Unchanged: the forecast, the counted sentence and the stakes — and a vibe sent anyway, never. */
  it('draws the forecast and the stakes as today, and no Social vibe', async () => {
    await openTheGame({
      kind: 'COMPETITIVE',
      court: pairing({ at_stake: { win_delta: 0.08, loss_delta: -0.08 } }),
    });

    expect(await screen.findByText(BALANCE_FORECAST)).toBeTruthy();
    expect(screen.getByText('90%')).toBeTruthy();
    expect(screen.getByText(COUNTED_GAME_SENTENCE)).toBeTruthy();
    expect(screen.getByText(WIN_TILE)).toBeTruthy();
    expect(screen.getByText('+0,08')).toBeTruthy();
    expect(screen.getByText(LOSE_TILE)).toBeTruthy();
    expect(screen.queryByTestId(SOCIAL_VIBE_CARD)).toBeNull();
    // The forecast's split row says the sides, so the vs line stays a drawing.
    expect(screen.queryByLabelText('You and piotr.s against ines.d and bartek.l')).toBeNull();
  });
});

/**
 * **Live** (ADR-0207 §2): a booked game's vibe is worked out on every read from everybody's tags
 * now. Ada adds 🔥 *Here to compete* in the You tab; the pairing she read is marked stale — not read
 * again under the edit, since the server's copy of the tags is written after the save answers — and
 * back on the game, it shows her new row and the new number.
 */
describe('a tag edit', () => {
  const TAGS_PATH = '/api/v1/players/me/social-tags';
  const HELD = PROFILE_SURFACE_SERVED.social_tags;
  const MAXIMUM = PROFILE_OPTIONS_SERVED.social_tag_selection.maximum_tags;
  const OTHERS: Readonly<Partial<Record<Wire['SocialTag'], readonly string[]>>> = {
    STAYS_FOR_A_DRINK: [BARTEK],
    HERE_TO_IMPROVE: [INES],
    HERE_TO_COMPETE: [PIOTR],
  };

  /** The court's vibe for the tags Ada holds now: her rows, and a % that moves with them. */
  const vibeOf = (tags: readonly Wire['SocialTag'][]): Wire['GamePairingVibeSchema'] => ({
    pct: tags.length === HELD.length ? 40 : 72,
    rows: tags.map((tag) => ({ tag, carried_by: [ME, ...(OTHERS[tag] ?? [])] })),
  });

  it('marks the pairing stale, and the game reopened shows the new row and number', async () => {
    let held: readonly Wire['SocialTag'][] = HELD;
    stubProfileSurface(transport);
    stubProfileOptions(transport);
    stubOwnRecord(transport);
    transport.on('PUT', TAGS_PATH, (request) => {
      // The request spells a tag as a string; this fake serves back what it was sent.
      held = (request.body as Wire['ChangeSocialTagsRequest']).social_tags as Wire['SocialTag'][];
      return json<Wire['SocialTagsResponse']>({ social_tags: [...held] });
    });
    await openTheGame({ court: pairing() });
    // From here on the court's vibe follows the tags Ada holds.
    transport.on('GET', pairingPath(BOOKED_GAME), () => json(pairing({ vibe: vibeOf(held) })));
    await screen.findByTestId(SOCIAL_VIBE_CARD);
    const court = gameKeys.pairing(BOOKED_GAME);
    const read = queryClient.getQueryData(court);

    // To You, and its Tags: Ada adds Here to compete.
    fireEvent.press(screen.getByRole('tab', { name: 'You' }));
    fireEvent.press(
      await screen.findByLabelText(doorRowLabel(TAGS_TITLE, tagsLine(HELD, MAXIMUM))),
    );
    await screen.findByLabelText('Plays to win');
    fireEvent.press(screen.getByLabelText('Here to compete'));

    // What a phone holds a minute later: the pairing as she read it. The harness runs every pending
    // timer on a navigation, the five-minute gc among them, so it is put back as it was.
    queryClient.setQueryData(court, read);
    const reads = transport.requestsTo('GET', pairingPath(BOOKED_GAME)).length;
    fireEvent.press(screen.getByLabelText(SAVE));

    await waitFor(() => expect(transport.requestsTo('PUT', TAGS_PATH)).toHaveLength(1));
    await waitFor(() => expect(queryClient.getQueryState(court)?.isInvalidated).toBe(true));
    // Marked, not read: the server's copy of the tags may not have the edit yet.
    expect(transport.requestsTo('GET', pairingPath(BOOKED_GAME))).toHaveLength(reads);

    // Back on Home, she opens the game again: read again, her new row and the new number.
    fireEvent.press(screen.getByRole('tab', { name: 'Home' }));
    act(() => router.push({ pathname: '/booking/[bookingId]', params: { bookingId: BOOKING } }));
    expect(await screen.findByLabelText('Here to compete: you, piotr.s')).toBeTruthy();
    expect(screen.getByLabelText('Social vibe, 72 percent, Great vibe')).toBeTruthy();
    expect(dotted('Here to compete: you, piotr.s')).toEqual([true, true, false, false]);
  });
});
