/**
 * ***Leave the game*, walked** — from a booked game's details, before the club's cut-off, after it,
 * and while an On request club decides ([#557](https://github.com/Raketa02/Raketa/issues/557); the
 * screens A4.1, A4.2, details 10; the mechanics §12.3, §13; the backend's #543, #544).
 *
 * The real route tree from Home: *Open game* on the card, *Leave the game* under the details with
 * the line saying what it costs now, today's *Before you leave* sheet with the new words, and back to
 * Home once the player has left. What it costs is the read's (`leaving`); nothing here works out a
 * refund.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { LEAVE_THE_GAME } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  BOOKING,
  bookedMoney,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import {
  HOME_PATH,
  LIVE_YESES_PATH,
  RECEIPTS_PATH,
  bookingPath,
  launchSignedIn,
  stubGate,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { HOME_GAME_COPY } from './homeCopy';

const HOME = HOME_GAME_COPY;

const DEPARTURE = `${bookingPath(BOOKING)}/departure`;

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

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

/**
 * Home holding the game, its details as given, and the departure answering `left` — after which
 * Home no longer holds it.
 */
async function openDetails(
  details: Wire['BookingDetailsResponse'],
  left: () => Response = () =>
    json<Wire['DepartureResponse']>({ left: details.leaving?.kind ?? 'BEFORE_THE_CUT_OFF' }),
) {
  stubHomeGames(transport, [
    homeGame({ status: details.status, game_id: details.game_id, money: details.money }),
  ]);
  stubBooking(transport, details);
  transport.on('POST', DEPARTURE, () => {
    stubHomeGames(transport, []);
    return left();
  });
  await launchSignedIn();
  fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
  await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  await screen.findByRole('button', { name: LEAVE_THE_GAME });
}

/** *Leave the game* under the details, then the sheet's own act. */
function leave() {
  fireEvent.press(screen.getByRole('button', { name: LEAVE_THE_GAME }));
}

async function confirm() {
  const acts = await screen.findAllByRole('button', { name: LEAVE_THE_GAME });
  fireEvent.press(acts[acts.length - 1]!);
}

describe('before the club’s cut-off (§13)', () => {
  it('says the refund under the button, and the sheet says the rest before anything is sent', async () => {
    await openDetails(bookingDetails());

    expect(screen.getByText('Refunded 27,18 zł if you leave now')).toBeTruthy();

    leave();

    expect(await screen.findByText('Before you leave')).toBeTruthy();
    expect(
      screen.getByText('You’ll be refunded 27,18 zł now (the 0,82 zł card fee isn’t returned).'),
    ).toBeTruthy();
    expect(screen.getByText(HOME.leave.offered)).toBeTruthy();
    expect(screen.getByText(HOME.leave.onRecordIfCalledOff)).toBeTruthy();
    expect(transport.requestsTo('POST', DEPARTURE)).toHaveLength(0);
  });

  it('leaves, says the refund is on its way and when it lands, and goes back to a Home without it', async () => {
    await openDetails(bookingDetails());
    const receipts = transport.requestsTo('GET', RECEIPTS_PATH).length;

    leave();
    await confirm();

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('POST', DEPARTURE)).toHaveLength(1);
    expect(toasts()).toContainEqual([
      'You left the game. 27,18 zł is on its way back — BLIK within hours, cards up to two weeks.',
      'ok',
    ]);
    await waitFor(() => expect(screen.queryByTestId(`home-game-${BOOKING}`)).toBeNull());
    expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(1);
    // Payments is not on screen, so its receipts are marked stale rather than read now.
    expect(transport.requestsTo('GET', RECEIPTS_PATH)).toHaveLength(receipts);
  });

  it('sends nothing when the player stays in', async () => {
    await openDetails(bookingDetails());

    leave();
    fireEvent.press(await screen.findByRole('button', { name: 'Stay in' }));

    await waitFor(() => expect(screen.queryByText('Before you leave')).toBeNull());
    expect(transport.requestsTo('POST', DEPARTURE)).toHaveLength(0);
    expect(screen).toHavePathname(`/booking/${BOOKING}`);
  });
});

describe('after the cut-off (§12.3)', () => {
  const late = () =>
    bookingDetails({
      money: bookedMoney({ free_to_leave_until: null }),
      leaving: { kind: 'AFTER_THE_CUT_OFF', refund_grosze: 2718, card_fee_grosze: 82 },
    });

  it('says the refund waits for somebody to take the seat, and so does the sheet', async () => {
    await openDetails(late());

    expect(screen.getByText('Refunded 27,18 zł only if someone takes your seat')).toBeTruthy();

    leave();

    expect(
      await screen.findByText(
        'You’ll be refunded 27,18 zł when someone takes it; if nobody does, you won’t be.',
      ),
    ).toBeTruthy();
    expect(screen.getByText(HOME.leave.onRecordIfNobody)).toBeTruthy();
  });

  it('says the seat is offered once the player has left', async () => {
    await openDetails(late());

    leave();
    await confirm();

    await waitFor(() =>
      expect(toasts()).toContainEqual(['You left the game. Your seat is offered to others.', 'ok']),
    );
  });
});

describe('while an On request club decides (A4.2, §13)', () => {
  const waiting = () =>
    bookingDetails({
      status: 'WAITING_FOR_THE_CLUB',
      game_id: null,
      court_name: null,
      money: bookedMoney({ paid: false, free_to_leave_until: null }),
      leaving: { kind: 'WHILE_WAITING_FOR_THE_CLUB', refund_grosze: 0, card_fee_grosze: 0 },
    });

  it('says nobody has paid, and leaving withdraws the yes', async () => {
    await openDetails(waiting());

    expect(screen.getByText('Waiting for the club')).toBeTruthy();
    expect(screen.getByText(HOME.leave.nobodyPaidYet)).toBeTruthy();

    leave();

    expect(await screen.findByText('Nobody has paid yet.')).toBeTruthy();
    expect(screen.getByText(HOME.leave.withdrawsYourYes)).toBeTruthy();
  });

  it('withdraws the yes and reads the live yeses again, the game filling again for the rest', async () => {
    await openDetails(waiting());
    const yeses = transport.requestsTo('GET', LIVE_YESES_PATH).length;
    // Unobserved here, so seeded where the navigation's timer flush cannot collect it.
    queryClient
      .getQueryCache()
      .build(queryClient, { queryKey: ['proposals', 'live-yeses'], gcTime: Infinity })
      .setData({ yeses: [] });

    leave();
    await confirm();

    await waitFor(() =>
      expect(toasts()).toContainEqual(['You left the game. Your yes is withdrawn.', 'ok']),
    );
    expect(queryClient.getQueryState(['proposals', 'live-yeses'])?.isInvalidated).toBe(true);
    expect(transport.requestsTo('GET', LIVE_YESES_PATH)).toHaveLength(yeses);
  });
});

describe('a departure the server refuses', () => {
  it('says why on the sheet, keeps the act, and reads the game again', async () => {
    await openDetails(bookingDetails(), () => errorResponse(409, 'game_has_started'));
    const reads = transport.requestsTo('GET', bookingPath(BOOKING)).length;

    leave();
    await confirm();

    expect(
      await screen.findByText('The game has started, so there’s nothing to leave now.'),
    ).toBeTruthy();
    expect(screen.getAllByRole('button', { name: LEAVE_THE_GAME }).length).toBeGreaterThan(0);
    expect(screen).toHavePathname(`/booking/${BOOKING}`);
    await waitFor(() =>
      expect(transport.requestsTo('GET', bookingPath(BOOKING)).length).toBeGreaterThan(reads),
    );
  });
});

describe('no door where there is nothing to leave', () => {
  it('draws no Leave once the read gives no button — the hour has come', async () => {
    stubHomeGames(transport, [homeGame({ status: 'NEEDS_RESULT', needs_you: true })]);
    stubBooking(transport, bookingDetails({ status: 'NEEDS_RESULT', leaving: null }));
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));

    await screen.findByText('Padel · needs result');
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });
});
