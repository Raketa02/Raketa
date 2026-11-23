/**
 * **A competitive game's details open on the full Balance forecast, with what is at stake**
 * ([#839](https://github.com/Raketa02/Raketa/issues/839); for fun 3–4; ADR-0207 §6) — walked the way
 * a player opens them: the real route tree, the real shell, and only `fetch` faked.
 *
 * Before saying yes, the reader reads both sides' levels and the gap, the bar with the sides' names,
 * the % and its word, *A counted game — a confirmed score moves everybody's level.*, and *If you win
 * / If you lose* — two tiles or none. The block is the booked game's own (`shared/ui`'s
 * `ForecastBlock`), drawn from the details read, and **never on For fun**.
 *
 * The screen is launched at its route: what opens it — the card, its **i**, a *You're In* row — is
 * `groups/components/groupGames.test.tsx`'s.
 */

import { screen, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { balanceLabel, balanceWord } from '@/shared/vocabulary/balancePresentation';
import {
  BALANCE_FORECAST,
  COUNTED_GAME_SENTENCE,
  GAP_WORD,
  LOSE_TILE,
  WIN_TILE,
} from '@/shared/vocabulary/forecastPresentation';
import {
  ANIA,
  deckCard,
  DETAILS_CARD,
  DETAILS_SCREEN,
  proposalDetails,
  stubProposal,
  youTile,
} from '@/test-support/groupDeck';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import { inOrder, partOf } from '@/test-support/readingOrder';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

/** The crew the details' game is dealt in — `proposalDetails`' own pool. */
const GROUP = 'a0000000-0000-4000-8000-000000000005';

const HIDDEN_TOO = { includeHiddenElements: true } as const;

/** Mock 3's figures: 2,65 against 2,74, a gap of −0,09, 73% — *Fairly even*. */
const FORECAST: Wire['DetailsForecastSchema'] = {
  pct: 73,
  provisional: false,
  your_side: 2.65,
  their_side: 2.74,
  gap: -0.09,
};

/** And what is at stake for you: *If you win +0,08 · If you lose −0,07*. */
const AT_STAKE: Wire['DetailsAtStakeSchema'] = { win_delta: 0.08, loss_delta: -0.07 };

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/**
 * A competitive game's details — the deck's own line-up, you and zofia.b against ania.k and ewa.m,
 * nobody In — with mock 3's forecast and stakes unless the suite says otherwise.
 */
function competitive(
  extra: Partial<Wire['ProposalDetailsResponse']> = {},
  card: Wire['DeckCardSchema'] = deckCard(),
): Wire['ProposalDetailsResponse'] {
  return proposalDetails(card, { forecast: FORECAST, at_stake: AT_STAKE, ...extra });
}

/** In at the details, as the deck pushes them: the group, the game, the sport and the kind. */
async function openDetails(
  read: Wire['ProposalDetailsResponse'],
  {
    sport = 'padel',
    kind = 'competitive',
  }: { readonly sport?: string; readonly kind?: string } = {},
) {
  stubProposal(transport, read.proposal_id, read);
  await launchSignedIn(`/play/group/${GROUP}/game/${read.proposal_id}?sport=${sport}&kind=${kind}`);
  await screen.findByTestId(DETAILS_CARD);
}

describe('the competitive details’ top card', () => {
  it('opens on both sides’ levels and the gap, the %, its word, the counted sentence and both stakes', async () => {
    await openDetails(competitive());

    expect(screen.getByRole('header', { name: BALANCE_FORECAST })).toBeTruthy();

    // The split row: your side left, theirs right, the gap between — signed, as served.
    const split = screen.getByLabelText('You and zofia.b 2,65, ania.k and ewa.m 2,74, gap −0,09');
    expect(within(split).getByText('2,65')).toBeTruthy();
    expect(within(split).getByText(GAP_WORD)).toBeTruthy();
    expect(within(split).getByText('−0,09')).toBeTruthy();
    expect(within(split).getByText('2,74')).toBeTruthy();

    // The figure, its word and the sentence — one element, the word first.
    const reading = screen.getByLabelText(`${balanceLabel(73)}. ${COUNTED_GAME_SENTENCE}`);
    expect(within(reading).getByText('73%')).toBeTruthy();
    expect(within(reading).getByText(balanceWord(73))).toBeTruthy();
    expect(within(reading).getByText(COUNTED_GAME_SENTENCE)).toBeTruthy();

    // Two tiles, as one element of two clauses.
    const stakes = screen.getByLabelText(`${WIN_TILE} +0,08, ${LOSE_TILE} −0,07`);
    expect(within(stakes).getByText(WIN_TILE)).toBeTruthy();
    expect(within(stakes).getByText('+0,08')).toBeTruthy();
    expect(within(stakes).getByText(LOSE_TILE)).toBeTruthy();
    expect(within(stakes).getByText('−0,07')).toBeTruthy();
  });

  /** The bar is drawn and hidden: the split row above it already speaks its three numbers. */
  it('draws the bar with the sides’ names, yours on the left', async () => {
    await openDetails(competitive());

    expect(screen.getByText('You + zofia', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('ania + ewa', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByLabelText(balanceLabel(73), HIDDEN_TOO)).toBeTruthy();
  });

  /** For fun 3: the forecast first, then the dark game card. */
  it('is read before the game card', async () => {
    await openDetails(competitive());

    const order = [
      `header:${BALANCE_FORECAST}`,
      '2,65',
      '73%',
      WIN_TILE,
      LOSE_TILE,
      'header:Filling · 0 of 4 in',
    ];
    expect(inOrder(partOf(screen.toJSON(), DETAILS_SCREEN), order)).toEqual(order);
    expect(within(screen.getByTestId(DETAILS_CARD)).queryByText(BALANCE_FORECAST)).toBeNull();
  });

  /** Two or none: the read sends no pair while a seat is open, or once the game isn't yours to play. */
  it('draws no stake tile when the read has none', async () => {
    await openDetails(competitive({ at_stake: null }));

    expect(screen.getByRole('header', { name: BALANCE_FORECAST })).toBeTruthy();
    expect(screen.getByText('73%')).toBeTruthy();
    expect(screen.getByText(COUNTED_GAME_SENTENCE)).toBeTruthy();
    expect(screen.queryByText(WIN_TILE)).toBeNull();
    expect(screen.queryByText(LOSE_TILE)).toBeNull();
  });

  /** And no block at all where the read could not forecast the game — with nothing said about why. */
  it('draws nothing above the game card when the read has no forecast', async () => {
    await openDetails(competitive({ forecast: null, at_stake: null }));

    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByText(/^\d+%$/)).toBeNull();
    expect(screen.queryByText(/forecast|unrated|cannot|could not|not available/i)).toBeNull();
  });

  it('names one person a side on a singles court', async () => {
    const singles = deckCard({ sides: { yours: [youTile()], theirs: [ANIA()] } });
    await openDetails(
      competitive(
        {
          sport: 'TENNIS',
          seats: 2,
          forecast: { pct: 90, provisional: false, your_side: 2.71, their_side: 2.68, gap: 0.03 },
        },
        singles,
      ),
      { sport: 'tennis' },
    );

    expect(screen.getByLabelText('You 2,71, ania.k 2,68, gap 0,03')).toBeTruthy();
    expect(screen.getByText('ania', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText(balanceWord(90))).toBeTruthy();
    expect(screen.getByLabelText(`${WIN_TILE} +0,08, ${LOSE_TILE} −0,07`)).toBeTruthy();
  });
});

describe('For fun', () => {
  /**
   * ADR-0207 §5: no forecast on For fun, anywhere. The server sends none there — and a read that
   * sent one anyway is still not drawn: the kind decides the top card, not what came with it.
   */
  it('never draws the forecast or the stakes, even when the read sends them', async () => {
    await openDetails(
      competitive({ kind: 'FOR_FUN' }, deckCard({ kind: 'FOR_FUN', forecast: null })),
      { kind: 'forFun' },
    );

    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
    expect(screen.queryByText('73%')).toBeNull();
    expect(screen.queryByText(COUNTED_GAME_SENTENCE)).toBeNull();
    expect(screen.queryByText(WIN_TILE)).toBeNull();
    expect(screen.queryByText(LOSE_TILE)).toBeNull();
  });
});
