/**
 * **You › Payments' LIVE YESES, walked** — the real route tree, with only `fetch` faked
 * ([#554](https://github.com/Raketa02/Raketa/issues/554); the screens A7.3; mock 48).
 *
 * The list is `GET /players/me/live-yeses` as #539 serves it; a row opens the deck's own details
 * screen for the group, sport and kind the yes was said in, drawn from the game's own read (`GET
 * /proposals/{id}`, #557): everybody In, the open seats empty, and *Withdraw* — and once withdrawn,
 * the two answers back.
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
  ANIA,
  deckCard,
  DECK_READ_AT,
  EWA,
  liveYes,
  proposalDetails,
  proposalPath,
  stubProposal,
  yesPath,
  youTile,
  ZOFIA,
} from '@/test-support/groupDeck';
import {
  LIVE_YESES_PATH,
  launchSignedIn,
  resetPayments,
  stubGate,
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

import { liveYesesHeader, LIVE_YESES_TITLE } from './liveYesesPresentation';
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

    expect(await screen.findByRole('header', { name: liveYesesHeader(2) })).toBeTruthy();
    // There is no live-yes cap (removed 2026-10-05), so nothing counts against one.
    expect(screen.queryByText(/per sport/)).toBeNull();

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

      // TO CONFIRM above it and RECEIPTS under it say the same of their own reads (#555): one note
      // per section.
      expect(await screen.findAllByText(offlineMessage('resumes'))).toHaveLength(3);
      expect(screen.getByText(LIVE_YESES_TITLE)).toBeTruthy();
      expect(transport.requestsTo('GET', LIVE_YESES_PATH)).toHaveLength(0);
    } finally {
      act(() => onlineManager.setOnline(true));
    }

    expect(await screen.findByRole('button', { name: ROW })).toBeTruthy();
  });
});

describe('a row opens the game’s details', () => {
  /**
   * The yes's game, read in detail — you and Zofia In, its other two seats open — and, after a
   * withdraw, the same game with only Zofia In and the two answers back.
   */
  function gameOf(yes: Wire['LiveYesSchema']) {
    const card = deckCard({
      proposal_id: yes.proposal_id,
      starts_at: yes.starts_at,
      share_grosze: yes.share_grosze,
      deadline: yes.book_by,
      in_count: 2,
      sides: { yours: [youTile({ is_in: true }), ZOFIA({ is_in: true })], theirs: [] },
    });
    const inIt = proposalDetails(card, { pool_id: POOL });
    const out = proposalDetails(card, {
      pool_id: POOL,
      in_count: 1,
      actions: ['YES', 'NO'],
      sides: { yours: [youTile(), ZOFIA({ is_in: true })], theirs: [ANIA(), EWA()] },
    });
    return { inIt, out };
  }

  /** The yes on the list and its game in detail, the details following a withdraw and a yes. */
  function stubTheGame(yes: Wire['LiveYesSchema']) {
    const { inIt, out } = gameOf(yes);
    let youAreIn = true;
    stubLiveYeses(transport, [yes]);
    stubProposal(transport, yes.proposal_id, () => (youAreIn ? inIt : out));
    transport.on('DELETE', yesPath(yes.proposal_id), () => {
      youAreIn = false;
      stubLiveYeses(transport, []);
      return noContent();
    });
    transport.on('POST', yesPath(yes.proposal_id), () => {
      youAreIn = true;
      stubLiveYeses(transport, [yes]);
      return json<Wire['YesAnswerResponse']>({
        proposal_id: yes.proposal_id,
        open_seats: 2,
      });
    });
  }

  it('draws the game from its own read — who is In, the club and its distance, the book-by — with Withdraw', async () => {
    const yes = liveYes();
    stubTheGame(yes);
    await onPayments();

    fireEvent.press(await screen.findByRole('button', { name: ROW }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${POOL}/game/${yes.proposal_id}`),
    );
    expect(await screen.findByText('Filling · 2 of 4 in')).toBeTruthy();
    expect(screen.getByLabelText('Zofia Bielecka, level 2,69, In')).toBeTruthy();
    // The header names the others; the tile names her too.
    expect(screen.getAllByText('Zofia Bielecka')).toHaveLength(2);
    expect(screen.getAllByTestId('game-tile-empty')).toHaveLength(2);
    expect(screen.getByLabelText('Where, Bonarka Arena, 3,1 km')).toBeTruthy();
    expect(screen.getByLabelText('Day, Saturday, 3 Oct')).toBeTruthy();
    expect(screen.getByLabelText('Time, 15:00, until 16:00')).toBeTruthy();
    expect(
      screen.getByLabelText('Your share, 28 zł, if it fills · book by Thu 10:00'),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.game.withdraw })).toBeTruthy();
    expect(transport.requestsTo('GET', proposalPath(yes.proposal_id)).length).toBeGreaterThan(0);
  });

  it('withdraws the yes, and the details, read again, put the answers back', async () => {
    const yes = liveYes();
    stubTheGame(yes);
    await onPayments();

    fireEvent.press(await screen.findByRole('button', { name: ROW }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.game.withdraw }));

    expect(await screen.findByRole('button', { name: COPY.yes })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.no })).toBeTruthy();
    expect(screen.getByText('Filling · 1 of 4 in')).toBeTruthy();
    expect(transport.requestsTo('DELETE', yesPath(yes.proposal_id))).toHaveLength(1);

    // Back on Payments, the list has been read again and the section is gone with the yes.
    fireEvent.press(screen.getByLabelText(COPY.game.back));
    expect(await screen.findByText('Card •••• 4312')).toBeTruthy();
    await waitFor(() => expect(screen.queryByRole('button', { name: ROW })).toBeNull());
  });

  it('says yes again from the details, and the list under them is read again', async () => {
    const yes = liveYes();
    stubTheGame(yes);
    await onPayments();
    fireEvent.press(await screen.findByRole('button', { name: ROW }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.game.withdraw }));
    await screen.findByRole('button', { name: COPY.yes });
    // Payments stays mounted under the details and keeps the list observed, so a re-read of it
    // happens at once and is counted rather than flagged.
    const reads = transport.requestsTo('GET', LIVE_YESES_PATH).length;

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));

    expect(await screen.findByRole('button', { name: COPY.game.withdraw })).toBeTruthy();
    expect(screen.getByText('Filling · 2 of 4 in')).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', LIVE_YESES_PATH).length).toBeGreaterThan(reads),
    );
  });

  it('says so in one sentence for a game the reader was never dealt', async () => {
    const yes = liveYes();
    stubLiveYeses(transport, [yes]);
    transport.on('GET', proposalPath(yes.proposal_id), () =>
      errorResponse(404, 'proposal_not_found'),
    );
    await onPayments();

    fireEvent.press(await screen.findByRole('button', { name: ROW }));

    expect(await screen.findByText(COPY.game.gone)).toBeTruthy();
  });
});
