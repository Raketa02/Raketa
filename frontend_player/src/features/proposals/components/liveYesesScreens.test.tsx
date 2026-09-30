/**
 * **You › Payments' LIVE YESES, walked** — the real route tree, with only `fetch` faked
 * ([#554](https://github.com/Raketa02/Raketa/issues/554); the screens A7.3; mock 48).
 *
 * The list is `GET /players/me/live-yeses` as #539 serves it; a row opens the deck's own details
 * screen for the group, sport and kind the yes was said in. **The deck never deals a game the
 * reader is In on**, so what the details draw is the yes itself — until a withdraw, after which the
 * deck deals the game again with everything on it.
 *
 * **The list is read at `DECK_READ_AT`**, Wednesday 30 September 2026 at 10:00 in Warsaw, so a
 * Saturday game is *Saturday* and its book-by is Thursday.
 */

import { onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel } from '@/shared/ui';
import {
  deckCard,
  deckPath,
  DECK_READ_AT,
  groupDeck,
  liveYes,
  stubGroupDeck,
  yesPath,
} from '@/test-support/groupDeck';
import {
  LIVE_YESES_PATH,
  launchSignedIn,
  resetPayments,
  stubGate,
  stubInterest,
  stubLiveYeses,
  stubOwnRecord,
  stubPaymentMethod,
  stubPayments,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakePayments } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { liveYesesCapLine, liveYesesHeader, LIVE_YESES_TITLE } from './liveYesesPresentation';
import { PROPOSALS_COPY } from './proposalsCopy';

const COPY = PROPOSALS_COPY;

const VISA_4312: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };

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

/** The crew the yeses were said in — its pool is filed under its id. */
const POOL = 'a0000000-0000-4000-8000-000000000005';

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
  stubPayments(fakePayments());
  stubPaymentMethod(transport, VISA_4312);
});

afterEach(async () => {
  transport.restore();
  resetPayments();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A signed-in player on You › Payments, read at the suite's instant. */
async function onPayments(row = 'Card •••• 4312') {
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(await screen.findByLabelText(doorRowLabel('Payments', row)));
}

const ROW = 'Padel · Saturday 15:00, Bonarka Arena, 28 zł if it fills';

describe('the section on Payments — mock 48', () => {
  it('counts every live yes under its head, says the cap, and lists them soonest first', async () => {
    stubLiveYeses(transport, [
      liveYes(),
      liveYes({
        sport: 'TENNIS',
        starts_at: '2026-10-04T16:00:00Z',
        club: { id: 'b0000000-0000-4000-8000-000000000002', name: 'Centrum Ruchu' },
        share_grosze: 3150,
      }),
    ]);
    await onPayments();

    expect(await screen.findByText(liveYesesHeader(2))).toBeTruthy();
    expect(screen.getByText(liveYesesCapLine(10))).toBeTruthy();
    expect(
      screen.getByRole('header', { name: `${liveYesesHeader(2)}, up to 10 per sport` }),
    ).toBeTruthy();

    const rows = screen.getAllByRole('button', { name: /if it fills$/ });
    expect(rows.map((row) => row.props.accessibilityLabel)).toEqual([
      ROW,
      'Tennis · Sunday 18:00, Centrum Ruchu, 31,50 zł if it fills',
    ]);
    // The share is drawn in grey beside the words, as mock 48 draws it.
    expect(screen.getByText('28 zł')).toBeTruthy();
    expect(screen.getByText('Padel · Saturday 15:00')).toBeTruthy();
    expect(screen.getByText('Bonarka Arena')).toBeTruthy();
  });

  it('is hidden when there are none', async () => {
    await onPayments();

    expect(await screen.findByText('Card •••• 4312')).toBeTruthy();
    await waitFor(() => expect(transport.requestsTo('GET', LIVE_YESES_PATH)).toHaveLength(1));
    expect(screen.queryByText(LIVE_YESES_TITLE, { exact: false })).toBeNull();
  });

  it('is not asked for with nothing saved, where no yes can be live', async () => {
    stubPaymentMethod(transport);
    await onPayments('Not set up');

    expect(await screen.findByLabelText(/^Step 1 of 4/)).toBeTruthy();
    expect(transport.requestsTo('GET', LIVE_YESES_PATH)).toHaveLength(0);
  });

  it('says why the list could not be read, under its name, with the retry', async () => {
    // A refusal the player can retry, and Query does not retry by itself.
    transport.on('GET', LIVE_YESES_PATH, () => errorResponse(429, 'rate_limited'));
    await onPayments();

    expect(await screen.findByText(LIVE_YESES_TITLE)).toBeTruthy();
    expect(screen.getByRole('alert')).toBeTruthy();
    stubLiveYeses(transport, [liveYes()]);
    fireEvent.press(screen.getByRole('button', { name: COPY.readAgain }));

    expect(await screen.findByRole('button', { name: ROW })).toBeTruthy();
  });
});

describe('the section offline', () => {
  it('says the list resumes when its first read is held, rather than drawing nothing', async () => {
    stubLiveYeses(transport, [liveYes()]);
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('You'));
    // The method is read on the tab, so Payments opens on state B with the connection gone.
    const row = await screen.findByLabelText(doorRowLabel('Payments', 'Card •••• 4312'));

    act(() => onlineManager.setOnline(false));
    try {
      fireEvent.press(row);

      expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
      expect(screen.getByText(LIVE_YESES_TITLE)).toBeTruthy();
      expect(transport.requestsTo('GET', LIVE_YESES_PATH)).toHaveLength(0);
    } finally {
      act(() => onlineManager.setOnline(true));
    }

    expect(await screen.findByRole('button', { name: ROW })).toBeTruthy();
  });
});

describe('a row opens the game’s details', () => {
  it('draws the game from the yes — the deck no longer deals it — with Withdraw', async () => {
    const yes = liveYes();
    stubLiveYeses(transport, [yes]);
    stubGroupDeck(transport, POOL, groupDeck());
    await onPayments();

    fireEvent.press(await screen.findByRole('button', { name: ROW }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${POOL}/game/${yes.proposal_id}`),
    );
    expect(await screen.findByLabelText('Where, Bonarka Arena')).toBeTruthy();
    // The club is the title: who else is In is not on the yes.
    expect(screen.getByRole('header', { name: 'Bonarka Arena' })).toBeTruthy();
    expect(screen.getByText(COPY.game.filling)).toBeTruthy();
    expect(screen.getByLabelText('Day, Saturday, 3 Oct')).toBeTruthy();
    expect(screen.getByLabelText('Time, 15:00, until 16:00')).toBeTruthy();
    expect(
      screen.getByLabelText('Your share, 28 zł, if it fills · book by Thu 10:00'),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.game.withdraw })).toBeTruthy();
    expect(screen.queryByText(COPY.game.gone)).toBeNull();
    expect(transport.requestsTo('GET', deckPath(POOL)).length).toBeGreaterThan(0);
  });

  it('withdraws the yes, and the deck, read again, deals the game with everything on it', async () => {
    const yes = liveYes();
    stubLiveYeses(transport, [yes]);
    stubGroupDeck(transport, POOL, groupDeck());
    transport.on('DELETE', yesPath(yes.proposal_id), () => {
      // A withdrawn yes is dealt again (#539), and is no longer live.
      stubGroupDeck(
        transport,
        POOL,
        groupDeck({
          cards: [deckCard({ proposal_id: yes.proposal_id, starts_at: yes.starts_at })],
        }),
      );
      stubLiveYeses(transport, []);
      return noContent();
    });
    await onPayments();

    fireEvent.press(await screen.findByRole('button', { name: ROW }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.game.withdraw }));

    expect(await screen.findByRole('button', { name: COPY.yes })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.no })).toBeTruthy();
    expect(await screen.findByText('Filling · 0 of 4 in')).toBeTruthy();
    expect(transport.requestsTo('DELETE', yesPath(yes.proposal_id))).toHaveLength(1);

    // Back on Payments, the list has been read again and the section is gone with the yes.
    fireEvent.press(screen.getByLabelText(COPY.game.back));
    expect(await screen.findByText('Card •••• 4312')).toBeTruthy();
    await waitFor(() => expect(screen.queryByRole('button', { name: ROW })).toBeNull());
  });

  it('says yes again from the details, and the list under them is read again', async () => {
    const yes = liveYes();
    stubLiveYeses(transport, [yes]);
    stubGroupDeck(transport, POOL, groupDeck());
    transport.on('DELETE', yesPath(yes.proposal_id), () => {
      stubGroupDeck(
        transport,
        POOL,
        groupDeck({
          cards: [deckCard({ proposal_id: yes.proposal_id, starts_at: yes.starts_at })],
        }),
      );
      stubLiveYeses(transport, []);
      return noContent();
    });
    transport.on('POST', yesPath(yes.proposal_id), () => {
      stubLiveYeses(transport, [yes]);
      return json<Wire['YesAnswerResponse']>({ proposal_id: yes.proposal_id, open_seats: 2 });
    });
    await onPayments();
    fireEvent.press(await screen.findByRole('button', { name: ROW }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.game.withdraw }));
    await screen.findByRole('button', { name: COPY.yes });
    // Payments stays mounted under the details and keeps the list observed, so a re-read of it
    // happens at once and is counted rather than flagged.
    const reads = transport.requestsTo('GET', LIVE_YESES_PATH).length;

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));

    expect(await screen.findByRole('button', { name: COPY.game.withdraw })).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', LIVE_YESES_PATH).length).toBeGreaterThan(reads),
    );
  });

  it('keeps the game it found when the yes leaves the list meanwhile', async () => {
    const yes = liveYes();
    stubLiveYeses(transport, [yes]);
    stubGroupDeck(transport, POOL, groupDeck());
    await onPayments();
    fireEvent.press(await screen.findByRole('button', { name: ROW }));
    await screen.findByRole('button', { name: COPY.game.withdraw });

    // Filled elsewhere meanwhile: gone from the list, and the screen keeps what it found.
    stubLiveYeses(transport, []);
    await queryClient.invalidateQueries();

    expect(screen.getByRole('button', { name: COPY.game.withdraw })).toBeTruthy();
    expect(screen.queryByText(COPY.game.gone)).toBeNull();
  });
});
