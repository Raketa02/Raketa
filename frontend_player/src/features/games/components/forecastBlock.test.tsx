/**
 * **The forecast block on a booked game's details, walked the way a player walks it**: the real
 * route tree, the real shell, and only `fetch` faked.
 *
 * [#415](https://github.com/Raketa02/Raketa/issues/415)'s acceptance criteria for the block are
 * assertions in this file and opinions nowhere else — present with a forecast and absent without
 * one with no sentence saying why, the gap's sign as served, the bar's labels for doubles and
 * singles, the word and the tone per band, the counted and the friendly sentence, two stake tiles
 * or none, and a read that never fires on a result arm. The words are `gamePresentation.ts`' and
 * `shared/vocabulary/balancePresentation.ts`'.
 *
 * It walked the old loop's game screen at `/games/[id]` until that route was removed
 * ([#576](https://github.com/Raketa02/Raketa/issues/576)); the block is the same one, drawn on a
 * booked game's details (#556), so the walk is the details' now.
 */

import { screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { BALANCE_INK } from '@/shared/ui/BalanceBar';
import { balanceLabel, balanceTone, balanceWord } from '@/shared/vocabulary/balancePresentation';
import {
  BOOKED_GAME,
  BOOKING,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import {
  GATE_USER,
  launchSignedIn,
  pairingPath,
  stubGames,
  stubGate,
  stubPairing,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import {
  BALANCE_FORECAST,
  GAP_WORD,
  LOSE_TILE,
  WIN_TILE,
  forecastSentence,
} from './gamePresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const KASIA = 'cccccccc-0000-4000-8000-000000000003';
const MAREK = 'dddddddd-0000-4000-8000-000000000004';

const GAME = BOOKED_GAME;

/** Saturday the 12th of September 2026, 11:00 in Warsaw — the instant every fold here is against. */
const READ_AT = '2026-09-12T09:00:00Z';
const PLANNED_AT = '2026-09-08T09:00:00Z';

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

const SINGLES_SEATS: Wire['GameSchema']['seats'] = [
  { side: 'A', player_id: ME, name: 'me_' },
  { side: 'B', player_id: TOMEK, name: 'tomek.p' },
];

const DOUBLES_SEATS: Wire['GameSchema']['seats'] = [
  { side: 'A', player_id: ME, name: 'me_' },
  { side: 'A', player_id: KASIA, name: 'kasia.w' },
  { side: 'B', player_id: TOMEK, name: 'tomek.p' },
  { side: 'B', player_id: MAREK, name: 'marek b' },
];

function game(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: GAME,
    booking_id: BOOKING,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: PLANNED_AT,
    entry_closes_at: '2026-09-20T09:00:00Z',
    seats: SINGLES_SEATS,
    proposals: [],
    no_shows: [],
    ...over,
  };
}

const seat = (playerId: string, level: number): Wire['GamePairingSeatSchema'] => ({
  player_id: playerId,
  level,
  band: 'Established',
  range: { low: level - 0.16, high: level + 0.16 },
  confidence: 74,
});

/** Mock 7's own figures: 2,70 against 2,71, a gap of −0,01, 90 % even, ±0,08 at stake. */
function pairing(over: Partial<Wire['GamePairingResponse']> = {}): Wire['GamePairingResponse'] {
  return {
    read_at: READ_AT,
    forecast: { pct: 90, sigma_group: 0.4, provisional: false, assumption: null },
    split: { your_side: 2.7, their_side: 2.71, gap: -0.01 },
    at_stake: { win_delta: 0.08, loss_delta: -0.08 },
    seats: [seat(ME, 2.7), seat(TOMEK, 2.71)],
    ...over,
  };
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

/** The booking, the Game behind it on the games list, and the pairing beside the game. */
function stubTheWorld({
  games = [game()],
  court = pairing(),
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly court?: Parameters<typeof stubPairing>[2];
} = {}) {
  stubHomeGames(transport, [homeGame()]);
  stubBooking(transport, bookingDetails({ shows_forecast: true }));
  stubGames(transport, games, READ_AT);
  stubPairing(transport, GAME, court);
}

/** In at the booked game's details, which draw the forecast while the booking shows one. */
async function openTheGame(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn(`/booking/${BOOKING}`);
  await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  await screen.findByLabelText('Back');
}

/** The figure's ink, read off the one `Text` that prints it. */
function inkOf(figure: string): string | undefined {
  const text = screen.getByText(figure);
  const style = [text.props.style].flat(Infinity) as ({ color?: string } | undefined)[];
  return style.reduce<string | undefined>((found, one) => one?.color ?? found, undefined);
}

describe('present and absent', () => {
  /** Mock 7: the eyebrow, the two strengths, the gap, the bar, the figure, the word, the sentence. */
  it('draws the block when the pairing carries a forecast', async () => {
    await openTheGame();

    expect(await screen.findByText(BALANCE_FORECAST)).toBeTruthy();
    // The strengths, read in the block's own split: a tile above prints a Level too (Q113 left a
    // held share's tile without *paid*, so the reader's reads a bare 2,71).
    const split = screen.getByLabelText(/, gap −0,01$/);
    expect(within(split).getByText('2,70')).toBeTruthy();
    expect(within(split).getByText('2,71')).toBeTruthy();
    expect(screen.getByText(GAP_WORD)).toBeTruthy();
    expect(screen.getByText('90%')).toBeTruthy();
    expect(screen.getByText(balanceWord(90))).toBeTruthy();
    expect(screen.getByText(forecastSentence('COUNTED')!)).toBeTruthy();
  });

  /**
   * ADR-0161 §4: the forecast and the split are omitted together when the pairing cannot be
   * computed, and **there is deliberately no reason beside the absence** — the block is absent
   * entirely, and nothing on the screen says why.
   */
  it('draws nothing, and says nothing about why, when the pairing carries no forecast', async () => {
    await openTheGame({ court: pairing({ forecast: undefined, split: undefined }) });

    await screen.findByLabelText('Back');
    await waitFor(() => expect(transport.requestsTo('GET', pairingPath(GAME))).toHaveLength(1));

    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    // A bare percentage is the forecast's figure; the players card's `74% sure` is not one.
    expect(screen.queryByText(/^\d+%$/)).toBeNull();
    expect(screen.queryByText(/forecast|unrated|cannot|could not|not available/i)).toBeNull();
    // The tiles go with the block: the pair is drawn under the figure or not at all.
    expect(screen.queryByText(WIN_TILE)).toBeNull();
  });

  /** The route's refusal by name is the same absence, and the same silence. */
  it('draws nothing when the route refuses by name', async () => {
    await openTheGame({ court: { refused: 409, code: 'pairing_is_history' } });

    await screen.findByLabelText('Back');
    await waitFor(() => expect(transport.requestsTo('GET', pairingPath(GAME))).toHaveLength(1));

    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByRole('alert')).toBeNull();
  });
});

describe('the figures, as served', () => {
  /**
   * The gap is `your_side − their_side`, signed by the engine and read in the reader's direction.
   * It is printed with its sign — U+2212, the level formatter's own — and never subtracted here.
   */
  it('prints the gap with the sign it was served with', async () => {
    await openTheGame();

    expect(await screen.findByText('−0,01')).toBeTruthy();
  });

  it('prints a gap in your favour with no sign, as the formatter draws a positive level', async () => {
    await openTheGame({
      court: pairing({ split: { your_side: 2.9, their_side: 2.6, gap: 0.3 } }),
    });

    expect(await screen.findByText('0,30')).toBeTruthy();
    expect(screen.getByText('2,90')).toBeTruthy();
    expect(screen.getByText('2,60')).toBeTruthy();
  });

  /** §B9's word and 7.11's tone, per band — the word steps in four and the tone in three. */
  it.each([
    [90, 'Very even', 'ok'],
    [72, 'Fairly even', 'ok'],
    [60, 'One side favoured', 'warn'],
    [40, 'Lopsided', 'bad'],
  ] as const)('reads %s%% as %s in the %s tone', async (pct, word, tone) => {
    await openTheGame({
      court: pairing({ forecast: { pct, sigma_group: 0.4, provisional: false, assumption: null } }),
    });

    expect(await screen.findByText(word)).toBeTruthy();
    expect(balanceTone(pct)).toBe(tone);
    expect(inkOf(`${pct}%`)).toBe(BALANCE_INK[tone]);
  });
});

describe('the bar', () => {
  /**
   * The bar is drawn and **hidden**: the split row above it speaks all three of its numbers, so
   * its own name would be the fourth reading of one fact. What is asserted is the drawing.
   */
  const drawn = { includeHiddenElements: true };

  /** Doubles: `You + {partner stem}` against `{stem} + {stem}`, cut at the first word break. */
  it('labels the two sides with stems on a doubles court', async () => {
    await openTheGame({
      games: [game({ seats: DOUBLES_SEATS })],
      court: pairing({
        seats: [seat(ME, 2.7), seat(KASIA, 2.7), seat(TOMEK, 2.71), seat(MAREK, 2.71)],
      }),
    });

    expect(await screen.findByText('You + kasia', drawn)).toBeTruthy();
    expect(screen.getByText('tomek + marek', drawn)).toBeTruthy();
    // The row above speaks the handles whole, over *and* — a sentence never truncates.
    expect(
      screen.getByLabelText('You and kasia.w 2,70, tomek.p and marek b 2,71, gap −0,01'),
    ).toBeTruthy();
  });

  it('labels the two sides You and one stem on a singles court', async () => {
    await openTheGame();

    await screen.findByText(BALANCE_FORECAST);
    // Three *You*s on the screen: the reader's tile on the details, the bar's label and the tab.
    // The bar's is the hidden one.
    expect(screen.getAllByText('You', drawn)).toHaveLength(3);
    expect(screen.getByText('tomek', drawn)).toBeTruthy();
    expect(screen.getByLabelText('You 2,70, tomek.p 2,71, gap −0,01')).toBeTruthy();
  });

  /**
   * The bar is a colour and the word carries the meaning: §20.4 makes it one `image` element
   * named by the word and the figure — kept on the element even though the subtree is hidden,
   * so the one thing a query could reach there says the right thing.
   */
  it('is named by the balance word and its figure', async () => {
    await openTheGame();

    await screen.findByText(BALANCE_FORECAST);
    expect(screen.getByLabelText(balanceLabel(90), drawn)).toBeTruthy();
    // And the reading beside it is one element: the word, the figure, then the sentence.
    expect(
      screen.getByLabelText(`${balanceLabel(90)}. ${forecastSentence('COUNTED')}`),
    ).toBeTruthy();
  });
});

describe('the sentence, and the tiles', () => {
  it('says a counted game moves everybody, over two tiles', async () => {
    await openTheGame();

    expect(await screen.findByText(forecastSentence('COUNTED')!)).toBeTruthy();
    expect(screen.getByText(WIN_TILE)).toBeTruthy();
    expect(screen.getByText('+0,08')).toBeTruthy();
    expect(screen.getByText(LOSE_TILE)).toBeTruthy();
    expect(screen.getByText('−0,08')).toBeTruthy();
  });

  /** A friendly: the sentence says nothing moves, and no tile is drawn — the wire omits the pair. */
  it('says a friendly moves nothing, and draws no tile', async () => {
    await openTheGame({
      games: [game({ kind: 'FRIENDLY' })],
      court: pairing({ at_stake: undefined }),
    });

    expect(await screen.findByText(forecastSentence('FRIENDLY')!)).toBeTruthy();
    expect(screen.queryByText(WIN_TILE)).toBeNull();
    expect(screen.queryByText(LOSE_TILE)).toBeNull();
  });

  /** Two or none, never one: the pair is the fact, and the contract sends it together. */
  it('draws no tile on a counted game the wire could not price', async () => {
    await openTheGame({ court: pairing({ at_stake: undefined }) });

    expect(await screen.findByText(forecastSentence('COUNTED')!)).toBeTruthy();
    expect(screen.queryByText(WIN_TILE)).toBeNull();
  });
});

describe('when the read is made', () => {
  /**
   * The route answers only while the game is `AWAITING_ENTRY` and refuses by name after it
   * (ADR-0161 §1), so a result arm never asks: the pairing of a game that has happened is a claim
   * about people made from a record that has moved on.
   */
  it('never asks for the pairing on a result arm', async () => {
    await openTheGame({
      games: [
        game({
          standing: 'CONFIRMED',
          played_at: READ_AT,
          entry_closes_at: null,
          score: { sets: [{ a: 6, b: 4 }] },
          outcome: 'WIN',
        }),
      ],
    });

    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/games')).toHaveLength(1));
    expect(transport.requestsTo('GET', pairingPath(GAME))).toHaveLength(0);
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
  });
});
