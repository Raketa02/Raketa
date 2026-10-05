/**
 * **You › Account › Games & money, walked the way a player walks it** — the real route tree and
 * the real bar, with only `fetch` faked ([#554](https://github.com/Raketa02/Raketa/issues/554); the
 * screens A7, A7.1; mocks 37–39).
 *
 * The server is `GET` and `PUT …/games-and-money` as #539 serves them: a save answers the pair it
 * saved, and the next read answers it too. What the suite proves is the screen's side of *changes
 * save as you tap* — each tap sends both limits, the saves go one at a time in the order tapped,
 * the stepper stops at the range the server offers, and the row and the bound say what is saved.
 */

import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel } from '@/shared/ui';
import {
  GAMES_AND_MONEY_PATH,
  gamesAndMoney,
  launchSignedIn,
  stubGamesAndMoney,
  stubGate,
  stubInterest,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { proposalKeys } from '../hooks/proposalKeys';

import {
  GAMES_AND_MONEY_COPY,
  GAMES_AND_MONEY_TITLE,
  boundText,
  ceilingLine,
  gamesLine,
  gamesSpoken,
} from './gamesAndMoneyCopy';

const COPY = GAMES_AND_MONEY_COPY;

/** One rated sport — a player past onboarding, whom the gate lets into the app. */
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

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

type Saved = Pick<Wire['GamesAndMoneyResponse'], 'games_per_week' | 'most_ill_pay_grosze'>;

/**
 * The server: it holds `held`, and a save replaces it and answers it — so the read after a save is
 * the server's too. A save can be `hold`-ed, answered only once the suite releases it.
 */
function serve(held: Saved, { hold = false }: { readonly hold?: boolean } = {}) {
  let saved = held;
  const waiting: (() => void)[] = [];
  stubGamesAndMoney(transport, saved);
  transport.on('PUT', GAMES_AND_MONEY_PATH, (request: RecordedRequest) => {
    saved = request.body as Saved;
    stubGamesAndMoney(transport, saved);
    const answer = json<Wire['GamesAndMoneyResponse']>(gamesAndMoney(saved));
    if (!hold) return answer;
    return new Promise<Response>((resolve) => waiting.push(() => resolve(answer)));
  });
  return {
    /** Answer the oldest save still held. */
    release: () => act(() => waiting.shift()?.()),
  };
}

const rowLabel = (line: string) => doorRowLabel(GAMES_AND_MONEY_TITLE, line);

const saves = () => transport.requestsTo('PUT', GAMES_AND_MONEY_PATH).map((r) => r.body);

const press = (label: string) => fireEvent.press(screen.getByLabelText(label));

/** Whether the control with this name is shut, as a screen reader hears it. */
const shut = (label: string): boolean =>
  screen.getByLabelText(label).props.accessibilityState.disabled === true;

/** The stepper's value, as either key carries it. */
const stepperValue = (): string =>
  screen.getByLabelText(COPY.games.more).props.accessibilityValue.text as string;

/** A signed-in player on Games & money, the row's line read on the way. */
async function onGamesAndMoney(rowLine: string) {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(await screen.findByLabelText(rowLabel(rowLine)));
  await screen.findByLabelText(COPY.games.more);
}

// ---------------------------------------------------------------------------
// The row
// ---------------------------------------------------------------------------

describe('the Games & money row, in the ACCOUNT group', () => {
  it('says the games a week — two until changed — above Payments', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    const row = await screen.findByLabelText(rowLabel('At most 2 games a week'));
    const rows = screen.getAllByRole('button').map((button) => button.props.accessibilityLabel);
    expect(rows.indexOf(row.props.accessibilityLabel)).toBe(
      rows.indexOf(doorRowLabel('Payments', 'Not set up')) - 1,
    );
  });

  it('repeats the week’s money bound once a ceiling is set', async () => {
    stubGamesAndMoney(transport, { games_per_week: 4, most_ill_pay_grosze: 4500 });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    expect(
      await screen.findByLabelText(rowLabel('At most 4 games a week · up to 180 zł')),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The screen
// ---------------------------------------------------------------------------

describe('the screen — mock 38', () => {
  it('draws the stepper, the chips, their lines and the bound', async () => {
    serve({ games_per_week: 4, most_ill_pay_grosze: null });
    await onGamesAndMoney('At most 4 games a week');

    expect(screen.getByText(COPY.games.title)).toBeTruthy();
    expect(screen.getByText('Mon–Sun · 1 to 7')).toBeTruthy();
    expect(stepperValue()).toBe('4 games a week');
    expect(screen.getByText(gamesLine(4))).toBeTruthy();

    expect(screen.getByText(COPY.ceiling.title)).toBeTruthy();
    expect(screen.getByText(COPY.ceiling.line)).toBeTruthy();
    for (const chip of ['Off', '35 zł', '45 zł', '60 zł']) {
      expect(screen.getByLabelText(chip)).toBeTruthy();
    }
    expect(screen.getByLabelText('Off').props.accessibilityState.selected).toBe(true);
    expect(screen.getByLabelText('45 zł').props.accessibilityState.selected).toBe(false);
    expect(screen.getByText(ceilingLine(null))).toBeTruthy();

    expect(screen.getByLabelText('Your bound: at most 4 games a week.')).toBeTruthy();
    expect(saves()).toEqual([]);
  });
});

describe('the stepper — every tap saves both limits', () => {
  it('moves at once, sends the pair, and the lines follow', async () => {
    serve({ games_per_week: 4, most_ill_pay_grosze: 3500 });
    await onGamesAndMoney('At most 4 games a week · up to 140 zł');

    press(COPY.games.more);

    // Drawn a tick after the tap — TanStack notifies on the next timer.
    await waitFor(() => expect(stepperValue()).toBe(gamesSpoken(5)));
    await waitFor(() =>
      expect(saves()).toEqual([{ games_per_week: 5, most_ill_pay_grosze: 3500 }]),
    );
    expect(
      screen.getByLabelText(boundText({ gamesPerWeek: 5, mostIllPayGrosze: 3500 })),
    ).toBeTruthy();

    press(COPY.games.fewer);
    press(COPY.games.fewer);

    await waitFor(() => expect(saves()).toHaveLength(3));
    expect(saves().slice(1)).toEqual([
      { games_per_week: 4, most_ill_pay_grosze: 3500 },
      { games_per_week: 3, most_ill_pay_grosze: 3500 },
    ]);
    expect(stepperValue()).toBe(gamesSpoken(3));
  });

  it('is shut at the top of the range, and at the bottom, where the line turns singular', async () => {
    serve({ games_per_week: 7, most_ill_pay_grosze: null });
    await onGamesAndMoney('At most 7 games a week');

    expect(shut(COPY.games.more)).toBe(true);
    press(COPY.games.more);
    expect(saves()).toEqual([]);

    for (let taps = 0; taps < 6; taps += 1) press(COPY.games.fewer);

    await waitFor(() => expect(shut(COPY.games.fewer)).toBe(true));
    expect(stepperValue()).toBe('1 game a week');
    expect(screen.getByText(gamesLine(1))).toBeTruthy();
    expect(screen.getByLabelText('Your bound: at most 1 game a week.')).toBeTruthy();
    await waitFor(() => expect(saves()).toHaveLength(6));
    expect(saves().at(-1)).toEqual({ games_per_week: 1, most_ill_pay_grosze: null });
  });

  it('sends one save at a time, in the order tapped, and keeps the last', async () => {
    const server = serve({ games_per_week: 2, most_ill_pay_grosze: null }, { hold: true });
    await onGamesAndMoney('At most 2 games a week');

    press(COPY.games.more);
    press(COPY.games.more);

    // The second waits for the first: one save on the wire, and the stepper already at four.
    await waitFor(() => expect(stepperValue()).toBe(gamesSpoken(4)));
    expect(saves()).toHaveLength(1);

    server.release();
    await waitFor(() => expect(saves()).toHaveLength(2));
    // The first answer does not pull the stepper back to three while the second is out.
    expect(stepperValue()).toBe(gamesSpoken(4));

    server.release();
    // Nothing left to save: the last answer is the one drawn.
    await waitFor(() => expect(queryClient.isMutating()).toBe(0));
    expect(saves()).toEqual([
      { games_per_week: 3, most_ill_pay_grosze: null },
      { games_per_week: 4, most_ill_pay_grosze: null },
    ]);
    expect(stepperValue()).toBe(gamesSpoken(4));
  });
});

describe('the saves and the reads around them', () => {
  it('holds a tap while offline, says so, and sends it on reconnect', async () => {
    serve({ games_per_week: 2, most_ill_pay_grosze: null });
    await onGamesAndMoney('At most 2 games a week');

    act(() => onlineManager.setOnline(false));
    try {
      press(COPY.games.more);

      expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
      expect(stepperValue()).toBe(gamesSpoken(3));
      expect(saves()).toEqual([]);
    } finally {
      act(() => onlineManager.setOnline(true));
    }

    await waitFor(() =>
      expect(saves()).toEqual([{ games_per_week: 3, most_ill_pay_grosze: null }]),
    );
    await waitFor(() => expect(screen.queryByText(offlineMessage('resumes'))).toBeNull());
  });

  it('does not let a read begun before the last save landed undo it', async () => {
    const server = serve({ games_per_week: 2, most_ill_pay_grosze: null }, { hold: true });
    await onGamesAndMoney('At most 2 games a week');

    press(COPY.games.more);
    await waitFor(() => expect(saves()).toHaveLength(1));
    // A read the server answers late, with the pair it held when it was asked — a focus refetch,
    // begun after the tap.
    let answerTheRead: (() => void) | undefined;
    transport.on(
      'GET',
      GAMES_AND_MONEY_PATH,
      () =>
        new Promise<Response>((resolve) => {
          answerTheRead = () => resolve(json(gamesAndMoney({ games_per_week: 2 })));
        }),
    );
    act(() => void queryClient.refetchQueries({ queryKey: proposalKeys.gamesAndMoney() }));
    await waitFor(() => expect(answerTheRead).toBeDefined());

    server.release();
    await waitFor(() => expect(queryClient.isMutating()).toBe(0));
    act(() => answerTheRead?.());

    await waitFor(() => expect(stepperValue()).toBe(gamesSpoken(3)));
    expect(queryClient.getQueryData(proposalKeys.gamesAndMoney())).toMatchObject({
      gamesPerWeek: 3,
    });
  });
});

describe('the most I’ll pay chips', () => {
  it('saves a ceiling with the games as they stand, and Off takes it away', async () => {
    serve({ games_per_week: 4, most_ill_pay_grosze: null });
    await onGamesAndMoney('At most 4 games a week');

    press('45 zł');

    await waitFor(() =>
      expect(screen.getByLabelText('45 zł').props.accessibilityState.selected).toBe(true),
    );
    expect(screen.getByText(ceilingLine(4500))).toBeTruthy();
    expect(
      screen.getByLabelText('Your bound: at most 4 games · up to 180 zł a week.'),
    ).toBeTruthy();
    await waitFor(() =>
      expect(saves()).toEqual([{ games_per_week: 4, most_ill_pay_grosze: 4500 }]),
    );

    press('Off');

    expect(await screen.findByText(ceilingLine(null))).toBeTruthy();
    await waitFor(() =>
      expect(saves().at(-1)).toEqual({ games_per_week: 4, most_ill_pay_grosze: null }),
    );
  });

  it('is on the row when the player comes back', async () => {
    serve({ games_per_week: 3, most_ill_pay_grosze: null });
    await onGamesAndMoney('At most 3 games a week');

    press('35 zł');
    await waitFor(() => expect(saves()).toHaveLength(1));
    fireEvent.press(screen.getByLabelText('Back'));

    expect(
      await screen.findByLabelText(rowLabel('At most 3 games a week · up to 105 zł')),
    ).toBeTruthy();
  });
});

describe('a refused save', () => {
  it('says why under the bound, and draws the saved pair again', async () => {
    serve({ games_per_week: 4, most_ill_pay_grosze: null });
    transport.on('PUT', GAMES_AND_MONEY_PATH, () =>
      errorResponse(400, 'games_per_week_out_of_range'),
    );
    await onGamesAndMoney('At most 4 games a week');
    const reads = transport.requestsTo('GET', GAMES_AND_MONEY_PATH).length;

    press(COPY.games.more);

    expect(
      await screen.findByText(COPY.refused.games_per_week_out_of_range as string),
    ).toBeTruthy();
    await waitFor(() => expect(stepperValue()).toBe(gamesSpoken(4)));
    expect(transport.requestsTo('GET', GAMES_AND_MONEY_PATH).length).toBeGreaterThan(reads);
  });
});

describe('a changed limit bounds every deck', () => {
  it('marks every group’s decks to be read again once the last save settles', async () => {
    serve({ games_per_week: 2, most_ill_pay_grosze: null });
    await onGamesAndMoney('At most 2 games a week');
    const deck = proposalKeys.deck('a0000000-0000-4000-8000-000000000005', 'padel', 'competitive');
    // Seeded where no navigation's timer flush can collect it: nothing observes a deck here.
    queryClient.getQueryCache().build(queryClient, { queryKey: deck, gcTime: Infinity });
    queryClient.setQueryData(deck, { cards: [] });

    press(COPY.games.more);

    await waitFor(() => expect(queryClient.getQueryState(deck)?.isInvalidated).toBe(true));
  });
});
