/**
 * The one line on Now that is about the player, driven through the real route tree
 * and the network boundary.
 *
 * `ADR-0070` puts exactly one viewer fact on the envelope beside the three regions,
 * and every assertion below is about the same three things: an amount, a currency
 * and one boolean. What is being proved is that the client **renders** them and
 * decides nothing — the presence of the line is the server's, the consequence is
 * the server's, and nothing else on the screen moves because of either.
 *
 * **What the server sends today is `null`, always.** `ComposeNow` has never
 * populated the field (`Raketa02/Raketa#108`), so no running app can reach this
 * rendering — which is exactly why it is asserted against a contract-typed fixture
 * here rather than left to be discovered when the composer lands.
 */

import { focusManager, onlineManager } from '@tanstack/react-query';
import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  clubCard,
  debt,
  emptyNow,
  matchCard,
  personCard,
  seatPath,
  seatWrite,
  shelf,
  stubNow,
} from '@/test-support/now';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { useSportFilterStore } from '../store/sportFilter.store';

import { DEBT_LINE_ID } from './DebtLine';
import { REGION_ID } from './NowRegions';
import { DEBT_CONSEQUENCE, DEBT_STILL_OPEN } from './nowCopy';

const MATCH = '3a2e0000-0000-4000-8000-000000000001';

const RATING: Wire['RatingResponse'] = {
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

const TAKE_IT = 'Take the seat · 38,00 zł, Sunset Padel';

let transport: Transport;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useSportFilterStore.getState().reset();
  focusManager.setFocused(true);
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

/** An offer card: the situation the cascade composes, and the act it arrives with. */
function offer(): Wire['MatchCardResponse'] {
  return matchCard({
    matchId: MATCH,
    situation: 'seatOpened',
    clock: '2099-01-01T18:00:00Z',
    act: 'takeSeat',
  });
}

/**
 * A screen with something in all three regions, so *at most once* is a claim about
 * a populated screen rather than about an empty one.
 */
function busyScreen(owing: Wire['NowResponse']['debt']): Wire['NowResponse'] {
  return {
    ...emptyNow(),
    debt: owing,
    offers: { stamp: 1, cards: [offer()] },
    your_matches: {
      stamp: 1,
      cards: [matchCard({ matchId: 'a4b70000-0000-4000-8000-000000000002', mayDepart: true })],
    },
    shelves: {
      stamp: 1,
      shelves: [
        shelf('bestFit', [matchCard({ matchId: 'feed-1', situation: 'forming' })]),
        shelf('newPlayers', [personCard('p-1', 'ada')]),
        shelf('newClubs', [clubCard('c-9', 'Kraków Padel')]),
      ],
    },
  };
}

async function launchOnNow(body: Wire['NowResponse']) {
  stubGate(transport, { ratings: [RATING] });
  stubNow(transport, body);

  await launchSignedIn();
  await screen.findByTestId(REGION_ID.yourMatches);
}

describe('a player who owes nothing', () => {
  it('is told nothing, and the slot is not furniture', async () => {
    // `ADR-0050` stands: a row that is neither a thing the player is in nor a thing
    // she could join is furniture. The line earns its place on a specific argument,
    // and a player with no debt is not in it.
    await launchOnNow(busyScreen(null));

    expect(screen.queryByTestId(DEBT_LINE_ID)).toBeNull();
  });
});

describe('a player who owes money and is blocked by it', () => {
  it('gets one line, naming the amount and both acts it costs her', async () => {
    await launchOnNow(busyScreen(debt(11200, true)));

    const line = await screen.findByTestId(DEBT_LINE_ID);

    expect(line).toBeTruthy();
    expect(screen.getByText('You owe 112,00 zł.')).toBeTruthy();
    expect(screen.getByText(DEBT_CONSEQUENCE)).toBeTruthy();
  });

  it('gets it once on a screen holding all three regions', async () => {
    // *At most once* is the acceptance criterion and it is about a screen, not
    // about a card: the tempting shape is a line per region or a line per card,
    // both of which draw one sentence a dozen times on a busy screen.
    await launchOnNow(busyScreen(debt(11200, true)));

    expect(screen.getAllByTestId(DEBT_LINE_ID)).toHaveLength(1);
    expect(screen.getAllByText('You owe 112,00 zł.')).toHaveLength(1);
  });

  it('is drawn above all three regions', async () => {
    // It is a fact about *her*, and the regions below it are about matches. A line
    // explaining why the create tab will refuse her, sitting under five shelves, is
    // a line she meets after the refusal rather than before it.
    await launchOnNow(busyScreen(debt(11200, true)));

    const drawn = screen
      .getAllByTestId(/^now-(debt-line|region-)/)
      .map((node) => String(node.props.testID));

    expect(drawn).toEqual([
      DEBT_LINE_ID,
      REGION_ID.offers,
      REGION_ID.yourMatches,
      REGION_ID.shelves,
    ]);
  });

  it('is not announced as an alert', async () => {
    // A note with the `alert` role announces itself when it **appears**, and this
    // one appears with the screen — on arrival, on every pull, on each of
    // `ADR-0054`'s four asks. A standing fact announced that way would interrupt
    // her every time she came back to a screen she already knew it from. The card's
    // own rescue strip keeps the role, because that one is news.
    await launchOnNow(busyScreen(debt(11200, true)));

    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('shares a screen with a card that is announced, which is what makes the last claim mean anything', async () => {
    // The positive control, and it was missing from this app entirely: nothing
    // asserted that the three rescue-window situations announce their strip, so
    // *the debt line is not an alert* was a constant compared against nothing —
    // true, and equally true of a build where the role had been deleted.
    await launchOnNow({
      ...busyScreen(debt(11200, true)),
      your_matches: {
        stamp: 1,
        cards: [
          matchCard({ matchId: 'a4b70000-0000-4000-8000-000000000003', situation: 'rescue' }),
        ],
      },
    });

    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getAllByRole('alert')).toHaveLength(1);
  });

  it('is told in the same breath that a seat in someone else’s match is still open', async () => {
    await launchOnNow(busyScreen(debt(11200, true)));

    expect(screen.getByText(DEBT_STILL_OPEN)).toBeTruthy();
  });

  it('can still take that seat, and the write goes out', async () => {
    // The half that is behaviour rather than copy, and the one that matters:
    // being cut off must not make her less likely to pay. Nothing on this screen
    // is withheld from her — the offer card's act is drawn and it works.
    await launchOnNow(busyScreen(debt(11200, true)));
    transport.on('POST', seatPath(MATCH), () =>
      json(
        seatWrite({
          claimed: true,
          update: matchCard({ matchId: MATCH, situation: 'confirmed', act: 'finishPaying' }),
          offers: [],
          yourMatches: [matchCard({ matchId: MATCH, situation: 'confirmed', act: 'finishPaying' })],
        }),
      ),
    );

    const button = screen.getByLabelText(TAKE_IT);

    expect(button.props.accessibilityState.disabled).toBeFalsy();

    fireEvent.press(button);

    await waitFor(() => expect(transport.requestsTo('POST', seatPath(MATCH))).toHaveLength(1));
    expect(await screen.findByText(/^Finish paying/)).toBeTruthy();
  });

  it('keeps the line while an act off Now rewrites a card', async () => {
    // An update carries one card (`ADR-0074`) and the debt is not a card. A cache
    // write that dropped it would take the explanation away at the exact moment she
    // is spending money, and she would meet the block later with nothing said.
    await launchOnNow(busyScreen(debt(11200, true)));
    transport.on('POST', seatPath(MATCH), () =>
      json(
        seatWrite({
          claimed: true,
          update: matchCard({ matchId: MATCH, situation: 'confirmed', act: 'finishPaying' }),
          offers: [],
          yourMatches: [matchCard({ matchId: MATCH, situation: 'confirmed', act: 'finishPaying' })],
        }),
      ),
    );

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(/^Finish paying/);

    expect(screen.getAllByTestId(DEBT_LINE_ID)).toHaveLength(1);
    expect(screen.getByText('You owe 112,00 zł.')).toBeTruthy();
  });
});

describe('a player who owes money and is blocked by nothing', () => {
  it('is told the amount and promised no consequence', async () => {
    // The boolean is the server's and the client reads it in one direction as
    // faithfully as in the other. A line that printed the consequence off the
    // amount would be the phone holding the rule (`ADR-0053`), and the failure is
    // invisible from a screen where the two happen to agree.
    await launchOnNow(busyScreen(debt(11200, false)));

    expect(await screen.findByTestId(DEBT_LINE_ID)).toBeTruthy();
    expect(screen.getByText('You owe 112,00 zł.')).toBeTruthy();
    expect(screen.queryByText(DEBT_CONSEQUENCE)).toBeNull();
    expect(screen.queryByText(DEBT_STILL_OPEN)).toBeNull();
  });

  it('still has the seat act, exactly as she would with no debt at all', async () => {
    await launchOnNow(busyScreen(debt(11200, false)));

    expect(screen.getByLabelText(TAKE_IT).props.accessibilityState.disabled).toBeFalsy();
  });
});
