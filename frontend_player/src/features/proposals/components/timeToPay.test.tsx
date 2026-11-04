/**
 * **Time to pay, walked on the phone** ([#630](https://github.com/Raketa02/Raketa/issues/630); the
 * backend's #625 and #626; the mechanics §11, §12.2, §14.1, Q109–Q112; the screens A2.4, A7.3, A8).
 *
 * At 14:10 on Tuesday Ivan's yes fills the 19:00 at Bonarka Arena, but Paula's bank wants to check
 * her payment: she has until 14:40, the other three holds wait, and her seat is hers alone. Here the
 * story runs on the suites' own clocks — the deck read at 10:00 on Wednesday, Home at 10:00 on
 * Thursday — and the time to pay ends at 10:30.
 *
 * - **The last yes** sees *It's a game!* with *Waiting for one payment · until 10:30 · Nobody pays
 *   until it's in*; a refusal of his own is no screen, only his sheet, naming his time.
 * - **Home** reads *Waiting for one payment* to the others; the payer's card, *To confirm* row,
 *   details and sheet name the time.
 * - **Paying in time** shows the payer *It's a game!*, which they never saw; **out of time** the
 *   game is *Seat open* to the others and the payer's row loses its time.
 * - **Before the cut-off it is the time to fix the card** ([#643](https://github.com/Raketa02/Raketa/issues/643);
 *   Q113): nothing is being taken, so the payer is told to fix the card, never to pay — at the fill,
 *   and at the holding time of a game booked far ahead, which stays booked meanwhile. The others'
 *   words are the same in both windows.
 *
 * The real route tree, with `fetch`, the payment provider's phone half and the platform edges faked.
 * The notices themselves are the server's (#625, #626): what is asserted is that the phone draws
 * them and opens the game.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ANIA,
  deckCard,
  DECK_READ_AT,
  EWA,
  groupDeck,
  proposalDetails,
  stubGroupDeck,
  stubProposal,
  yesPath,
  youTile,
  ZOFIA,
} from '@/test-support/groupDeck';
import {
  BOOKING,
  HOME_READ_AT,
  bookedMoney,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
  unheldMoney,
} from '@/test-support/home';
import {
  HOME_PATH,
  NOTICES_PATH,
  PAYMENTS_TO_CONFIRM_PATH,
  launchSignedIn,
  resetClipboard,
  resetHaptics,
  resetPayments,
  resetShare,
  stubClipboard,
  stubGate,
  stubHaptics,
  stubMyGroups,
  stubNotices,
  stubPaymentMethod,
  stubPayments,
  stubShare,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, fakeHaptics, fakePayments, fakeShare } from '@/test-support/platform';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { FILL_COPY } from './fillCopy';
import { HOME_GAME_COPY } from './homeCopy';
import { LEAVE_THE_GAME } from './leaveSheetCopy';
import { PROPOSALS_COPY } from './proposalsCopy';

const FILL = FILL_COPY;
const HOME = HOME_GAME_COPY;

const HIDDEN_TOO = { includeHiddenElements: true } as const;

const SECOND = 1_000;
const MINUTE = 60 * SECOND;
/** Past the card's flight, so the stage has told the deck it has gone. */
const PAST_THE_FLIGHT = 400;

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

const CREW_ID = 'a0000000-0000-4000-8000-000000000005';
const CREW: Wire['MyGroupSchema'] = {
  id: CREW_ID,
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};
const CREW_PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://raketa.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [{ sport: 'PADEL', rated_count: 5, first_rated: [] }],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

const SEAT_CHARGE = 'a2000000-0000-4000-8000-000000000001';
const SEAT_CHARGE_PATH = `/api/v1/seat-charges/${SEAT_CHARGE}`;
const CONFIRMATION_PATH = `${SEAT_CHARGE_PATH}/confirmation`;
const GAME_ID = 'a1000000-0000-4000-8000-000000000001';

/** 10:30 on Thursday in Warsaw — the end of the time to pay, half an hour after Home's read. */
const DUE = '2026-10-01T08:30:00Z';

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
  stubHaptics(fakeHaptics());
  stubPayments(fakePayments());
  stubPaymentMethod(transport, VISA_4312);
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW_ID}`, () => json(CREW_PAGE));
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  resetShare();
  resetClipboard();
  resetHaptics();
  resetPayments();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);
const card = () => screen.findByTestId(`home-game-${BOOKING}`);

/** The refused share, as `GET /seat-charges/{id}` answers while it waits for its player. */
function seatCharge(extra: Partial<Wire['SeatChargeResponse']> = {}): Wire['SeatChargeResponse'] {
  return {
    seat_charge_id: SEAT_CHARGE,
    proposal_id: BOOKING,
    status: 'FAILED',
    refusal: 'AUTHENTICATION_REQUIRED',
    amount_grosze: 4000,
    sport: 'PADEL',
    starts_at: homeGame().starts_at,
    club: { id: homeGame().club.id, name: 'Bonarka Arena' },
    to_confirm: {
      client_secret: 'pi_1_secret_abc',
      connected_account_id: 'acct_bonarka',
      publishable_key: 'pk_test_raketa',
    },
    ...extra,
  };
}

/** The payer's *To confirm* row for the game — their time to pay running to 10:30 unless said. */
function toConfirmRow(
  extra: Partial<
    Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema']
  > = {},
): Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'] {
  return {
    seat_charge_id: SEAT_CHARGE,
    refusal: 'AUTHENTICATION_REQUIRED',
    proposal_id: BOOKING,
    pool_id: CREW_ID,
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    starts_at: homeGame().starts_at,
    club: { id: homeGame().club.id, name: 'Bonarka Arena' },
    share_grosze: 4000,
    book_by: '2026-10-02T14:00:00Z',
    confirm_by: DUE,
    time_to: 'PAY',
    ...extra,
  };
}

/**
 * **The game waiting for one payment, on Home** — full at Bonarka Arena, 40 zł a share, nobody
 * paid, no Game and no court: *until 10:30*. The payer's card names their own time too.
 */
function waitingForAPayment(extra: Partial<Wire['HomeGameSchema']> = {}): Wire['HomeGameSchema'] {
  return homeGame({
    status: 'WAITING_FOR_A_PAYMENT',
    game_id: null,
    court_name: null,
    money: unheldMoney({ share_grosze: 4000 }),
    payment_due_by: DUE,
    ...extra,
  });
}

/** The same game in detail, as Home's *Open game* reads it. */
function waitingDetails(
  extra: Partial<Wire['BookingDetailsResponse']> = {},
): Wire['BookingDetailsResponse'] {
  return bookingDetails({
    status: 'WAITING_FOR_A_PAYMENT',
    game_id: null,
    court_name: null,
    money: unheldMoney({ share_grosze: 4000 }),
    shows_forecast: false,
    leaving: { kind: 'WHILE_WAITING_FOR_A_PAYMENT', refund_grosze: 0, card_fee_grosze: 0 },
    payment_due_by: DUE,
    ...extra,
  });
}

/** Signed in, on Home at Thursday's 10:00 — the clock every read here is folded on. */
async function onHome() {
  await launchSignedIn();
  jest.setSystemTime(Date.parse(HOME_READ_AT));
}

/**
 * Home, the session's first read of the notices landed — what it has seen is every id in it — and
 * then told this one by the next minute's read.
 */
async function told(notice: Wire['NoticeSchema']) {
  await waitFor(() => expect(transport.requestsTo('GET', NOTICES_PATH).length).toBeGreaterThan(0));
  await act(async () => jest.advanceTimersByTime(1));
  stubNotices(transport, [notice], { newCount: 1 });
  await act(async () => jest.advanceTimersByTime(MINUTE));
}

function notice(extra: Partial<Wire['NoticeSchema']>): Wire['NoticeSchema'] {
  return {
    notice_id: 'd0000000-0000-4000-8000-000000000001',
    kind: 'WAITING_FOR_A_PAYMENT',
    title: '',
    body: '',
    given_at: '2026-10-01T08:00:30Z',
    opens: 'PROPOSAL',
    game_id: BOOKING,
    pool_id: CREW_ID,
    sport: 'PADEL',
    game_kind: 'COMPETITIVE',
    gathered: 0,
    new: true,
    your_own: false,
    ...extra,
  };
}

// ---------------------------------------------------------------------------
// The last yes
// ---------------------------------------------------------------------------

describe('the last yes, when another player’s share is refused (Q110)', () => {
  /** Ivan's card: his yes completes it. */
  const lastSeat = deckCard({
    in_count: 3,
    open_seats_after_your_yes: 0,
    court: 'BOOK_IT_NOW',
    sides: {
      yours: [youTile(), ZOFIA({ is_in: true })],
      theirs: [ANIA({ is_in: true }), EWA({ is_in: true })],
    },
  });
  /** Half an hour after the deck's read: 10:30 on Wednesday. */
  const until = new Date(DECK_READ_AT + 30 * MINUTE).toISOString();
  const matched = 'It’s a game! You and zofia.b against ania.k and ewa.m';

  /** Land on the crew's Games tab, say yes to the last seat, and let the ten seconds pass. */
  async function fillIt(answer: Wire['YesAnswerResponse']) {
    let dealt = [lastSeat];
    transport.on('POST', yesPath(lastSeat.proposal_id), () => {
      dealt = [];
      return json(answer);
    });
    stubGroupDeck(transport, CREW_ID, () => groupDeck({ cards: dealt }));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    await screen.findByTestId(`game-card-${lastSeat.proposal_id}`);
    const home = transport.requestsTo('GET', HOME_PATH).length;

    fireEvent.press(screen.getByRole('button', { name: PROPOSALS_COPY.yes }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    act(() => jest.advanceTimersByTime(10 * SECOND - PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', yesPath(lastSeat.proposal_id))).toHaveLength(1),
    );
    return home;
  }

  it('ends on It’s a game! with until when — no toast, and the game is on Home waiting', async () => {
    const home = await fillIt({
      proposal_id: lastSeat.proposal_id,
      open_seats: 0,
      booked: null,
      your_payment: null,
      payment_awaited_until: until,
    });

    expect(
      await screen.findByRole('header', {
        name: `${matched}. Waiting for one payment until 10:30. Nobody pays until it’s in`,
      }),
    ).toBeTruthy();
    expect(
      screen.getByText('Waiting for one payment · until 10:30 · Nobody pays until it’s in'),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: FILL.itsAGame.open })).toBeTruthy();
    expect(toasts()).toEqual([]);
    // The game is on Home now, waiting for one payment — Home's own read, held by the shell.
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(home),
    );
  });

  it('a refusal of his own is no screen — his sheet opens, naming his time (Q109)', async () => {
    transport.on('GET', SEAT_CHARGE_PATH, () =>
      json(
        seatCharge({
          proposal_id: lastSeat.proposal_id,
          amount_grosze: lastSeat.share_grosze,
          starts_at: lastSeat.starts_at,
          club: lastSeat.club,
        }),
      ),
    );
    await fillIt({
      proposal_id: lastSeat.proposal_id,
      open_seats: 0,
      booked: null,
      your_payment: {
        seat_charge_id: SEAT_CHARGE,
        refusal: 'AUTHENTICATION_REQUIRED',
        confirm_by: until,
        time_to: 'PAY',
      },
      payment_awaited_until: until,
    });

    expect(await screen.findByText(FILL.confirm.title.PAY)).toBeTruthy();
    expect(await screen.findByText('Confirm your payment by 10:30 to keep your seat')).toBeTruthy();
    expect(screen.getByText('32 zł to Bonarka Arena')).toBeTruthy();
    expect(toasts()).toEqual([
      ['Your payment didn’t go through — confirm it to keep your seat', 'bad'],
    ]);
    expect(screen.queryByText(FILL.confirm.onlyPlacedAgain)).toBeNull();
    expect(screen.queryByTestId('its-a-game')).toBeNull();
  });

  // Q113: before the cut-off nothing is being taken — the payer is told to fix the card, not to pay.
  it('before the cut-off, tells him to fix his card — nothing is paid now (#643)', async () => {
    transport.on('GET', SEAT_CHARGE_PATH, () =>
      json(
        seatCharge({
          proposal_id: lastSeat.proposal_id,
          amount_grosze: lastSeat.share_grosze,
          starts_at: lastSeat.starts_at,
          club: lastSeat.club,
        }),
      ),
    );
    await fillIt({
      proposal_id: lastSeat.proposal_id,
      open_seats: 0,
      booked: null,
      your_payment: {
        seat_charge_id: SEAT_CHARGE,
        refusal: 'AUTHENTICATION_REQUIRED',
        confirm_by: until,
        time_to: 'FIX_THE_CARD',
      },
      payment_awaited_until: until,
    });

    expect(await screen.findByText('Fix your card')).toBeTruthy();
    expect(await screen.findByText('Fix your card by 10:30 to keep your seat')).toBeTruthy();
    expect(
      screen.getByText('Nothing is paid now — fixing your card only places the hold again.'),
    ).toBeTruthy();
    expect(
      screen.getByText('Your bank wants you to confirm the hold on your card yourself.'),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: FILL.confirm.check })).toBeTruthy();
    expect(toasts()).toEqual([
      ['Your card didn’t go through — fix it to keep your seat. Nothing is paid now.', 'bad'],
    ]);
    expect(screen.queryByText(/Confirm your payment/)).toBeNull();
    expect(screen.queryByTestId('its-a-game')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Home
// ---------------------------------------------------------------------------

describe('Home while one payment is awaited (Q111)', () => {
  it('reads Waiting for one payment to the others, until when — and the time leaves at the deadline', async () => {
    stubHomeGames(transport, [waitingForAPayment()]);
    await onHome();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status.WAITING_FOR_A_PAYMENT)).toBeTruthy();
    expect(
      within(drawn).getByText('Waiting for one payment · until 10:30 · Nobody pays until it’s in'),
    ).toBeTruthy();
    // Nobody paid and nothing is booked: no chat yet.
    expect(screen.queryByTestId(`home-game-chat-${BOOKING}`)).toBeNull();

    act(() => jest.advanceTimersByTime(30 * MINUTE));
    expect(
      await within(drawn).findByText('Waiting for one payment · Nobody pays until it’s in'),
    ).toBeTruthy();
    expect(within(drawn).queryByText(/until 10:30/)).toBeNull();
  });

  it('opens the details: no court, the share nobody pays yet over until when, and Leave the game', async () => {
    stubHomeGames(transport, [waitingForAPayment()]);
    stubBooking(transport, waitingDetails());
    await onHome();

    await card();
    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(await screen.findByText(HOME.status.WAITING_FOR_A_PAYMENT)).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Your share, 40 zł, Waiting for one payment · until 10:30 · Nobody pays until it’s in',
      ),
    ).toBeTruthy();
    expect(screen.getByLabelText('Where, Bonarka Arena, 3,1 km')).toBeTruthy();
    expect(screen.getByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();
    expect(screen.queryByRole('button', { name: FILL.confirm.title.PAY })).toBeNull();
  });

  it('names the payer’s time on their card, their To confirm row, the details and the sheet', async () => {
    stubHomeGames(transport, [waitingForAPayment({ your_payment_due_by: DUE })], {
      needing_you: 1,
    });
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({ payments: [toConfirmRow()] }),
    );
    stubBooking(transport, waitingDetails({ your_payment_due_by: DUE }));
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge()));
    await onHome();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status.WAITING_FOR_A_PAYMENT)).toBeTruthy();
    expect(within(drawn).getByText('Confirm your payment by 10:30')).toBeTruthy();
    const row = await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`);
    expect(within(row).getByText('Confirm your payment by 10:30')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(
      await screen.findByLabelText('Your share, 40 zł, Confirm your payment by 10:30'),
    ).toBeTruthy();

    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.title.PAY }));
    expect(await screen.findByText('Confirm your payment by 10:30 to keep your seat')).toBeTruthy();
    expect(screen.getByText('40 zł to Bonarka Arena')).toBeTruthy();
  });

  it('names it on the game’s details a notice opens too — and Confirm there names it on the sheet', async () => {
    const game = deckCard({ proposal_id: BOOKING, in_count: 4 });
    stubProposal(
      transport,
      BOOKING,
      proposalDetails(game, {
        pool_id: CREW_ID,
        status: 'WAITING_FOR_A_PAYMENT',
        actions: ['LEAVE', 'CONFIRM_PAYMENT'],
        payment_due_by: DUE,
        read_at: HOME_READ_AT,
        your_payment: {
          seat_charge_id: SEAT_CHARGE,
          refusal: 'AUTHENTICATION_REQUIRED',
          confirm_by: DUE,
        },
      }),
    );
    stubGroupDeck(transport, CREW_ID, groupDeck());
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge()));
    await onHome();
    act(() =>
      router.push({
        pathname: '/play/group/[groupId]/game/[proposalId]',
        params: { groupId: CREW_ID, proposalId: BOOKING, sport: 'padel', kind: 'competitive' },
      }),
    );

    expect(await screen.findByText(PROPOSALS_COPY.game.status.WAITING_FOR_A_PAYMENT)).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.getByLabelText('Your share, 32 zł, Confirm your payment by 10:30')).toBeTruthy();
    expect(screen.getByRole('button', { name: LEAVE_THE_GAME })).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: FILL.confirm.title.PAY }));
    expect(await screen.findByText('Confirm your payment by 10:30 to keep your seat')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Before the cut-off: time to fix the card
// ---------------------------------------------------------------------------

describe('before the cut-off, the time to fix the card (#643; Q113)', () => {
  it('names the payer’s time to fix the card on their card, their To confirm row, the details and the sheet', async () => {
    stubHomeGames(
      transport,
      [waitingForAPayment({ your_payment_due_by: DUE, time_to: 'FIX_THE_CARD' })],
      { needing_you: 1 },
    );
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({
        payments: [toConfirmRow({ time_to: 'FIX_THE_CARD' })],
      }),
    );
    stubBooking(transport, waitingDetails({ your_payment_due_by: DUE, time_to: 'FIX_THE_CARD' }));
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge()));
    await onHome();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status.WAITING_FOR_A_PAYMENT)).toBeTruthy();
    expect(within(drawn).getByText('Fix your card by 10:30')).toBeTruthy();
    const row = await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`);
    expect(within(row).getByText('Fix your card by 10:30')).toBeTruthy();
    expect(within(row).getByText('Nothing is paid now')).toBeTruthy();
    expect(within(row).getByText('Fix')).toBeTruthy();
    expect(
      within(row).getByRole('button', { name: /^Fix your card for Padel · Saturday 16:00 at/ }),
    ).toBeTruthy();
    expect(screen.queryByText(/Confirm your payment/)).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(await screen.findByLabelText('Your share, 40 zł, Fix your card by 10:30')).toBeTruthy();

    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.title.FIX_THE_CARD }));
    expect(await screen.findByText('Fix your card by 10:30 to keep your seat')).toBeTruthy();
    expect(screen.getByText(FILL.confirm.onlyPlacedAgain)).toBeTruthy();
  });

  it('reads Waiting for one payment to the others, as after the cut-off — never whose', async () => {
    stubHomeGames(transport, [waitingForAPayment({ time_to: 'FIX_THE_CARD' })]);
    await onHome();

    const drawn = await card();
    expect(
      within(drawn).getByText('Waiting for one payment · until 10:30 · Nobody pays until it’s in'),
    ).toBeTruthy();
    expect(screen.queryByText(/Fix your card/)).toBeNull();
  });

  // §12.2: before the cut-off nobody is asked to pay — and once the time ran out the read names no
  // window, so the words say confirm, never pay.
  it('out of time, the row loses its time and its sheet names no window — confirm, never pay', async () => {
    let ranOut = false;
    transport.on('GET', HOME_PATH, () =>
      json<Wire['HomeResponse']>({ read_at: HOME_READ_AT, needing_you: 1, games: [] }),
    );
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({
        payments: [
          toConfirmRow({
            refusal: 'DECLINED',
            ...(ranOut ? { confirm_by: null, time_to: null } : { time_to: 'FIX_THE_CARD' }),
          }),
        ],
      }),
    );
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge({ refusal: 'DECLINED' })));
    await onHome();
    const row = await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`);
    expect(within(row).getByText('Fix your card by 10:30')).toBeTruthy();

    ranOut = true;
    await told(
      notice({
        kind: 'TIME_TO_FIX_RAN_OUT',
        title: 'Your time to fix your card ran out · Sat 16:00',
        body: 'Your seat is open to others now — you owe nothing, and you can still take it back while it’s free.',
      }),
    );

    expect(await screen.findByText('Your time to fix your card ran out · Sat 16:00')).toBeTruthy();
    const after = await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`);
    expect(await within(after).findByText(FILL.toConfirm.open)).toBeTruthy();
    expect(within(after).queryByText('Nothing is paid now')).toBeNull();

    fireEvent.press(within(after).getByRole('button', { name: /^Confirm your payment for Padel/ }));
    expect(
      await screen.findByText(
        'Your bank declined the card on file. Use another card for this share.',
      ),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Use this card', disabled: true })).toBeTruthy();
    expect(screen.queryByText(/Pay this share|Pay with this card/)).toBeNull();
  });
});

describe('a card refused at the holding time (#639, #643; Q113)', () => {
  const OTHER = 'f3000000-0000-4000-8000-000000000001';
  /** Checked when it filled, far ahead; its holding, at 10:00, refused — the game stays booked. */
  const checked = bookedMoney({ share_state: 'CHECKED', held_from: HOME_READ_AT });

  it('leaves the game booked, and only its player’s card reads their time to fix it', async () => {
    stubHomeGames(
      transport,
      [
        homeGame({ money: checked, your_payment_due_by: DUE, time_to: 'FIX_THE_CARD' }),
        homeGame({ booking_id: OTHER }),
      ],
      { needing_you: 1 },
    );
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({
        payments: [toConfirmRow({ time_to: 'FIX_THE_CARD', share_grosze: 2800 })],
      }),
    );
    await onHome();

    const refused = await card();
    expect(within(refused).getByText(HOME.status.BOOKED)).toBeTruthy();
    expect(within(refused).getByText('Fix your card by 10:30')).toBeTruthy();
    const other = await screen.findByTestId(`home-game-${OTHER}`);
    expect(within(other).getByText(HOME.status.BOOKED)).toBeTruthy();
    expect(within(other).getByText(/free to leave until/, HIDDEN_TOO)).toBeTruthy();
    expect(within(other).queryByText(/Fix your card/, HIDDEN_TOO)).toBeNull();
    const row = await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`);
    expect(within(row).getByText('Fix your card by 10:30')).toBeTruthy();
    expect(within(row).getByText('Nothing is paid now')).toBeTruthy();
  });

  it('says what is at stake on the details, and the confirmation fixes the card with another', async () => {
    stubHomeGames(
      transport,
      [homeGame({ money: checked, your_payment_due_by: DUE, time_to: 'FIX_THE_CARD' })],
      { needing_you: 1 },
    );
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({
        payments: [
          toConfirmRow({ time_to: 'FIX_THE_CARD', refusal: 'DECLINED', share_grosze: 2800 }),
        ],
      }),
    );
    stubBooking(
      transport,
      bookingDetails({ money: checked, your_payment_due_by: DUE, time_to: 'FIX_THE_CARD' }),
    );
    transport.on('GET', SEAT_CHARGE_PATH, () =>
      json(seatCharge({ refusal: 'DECLINED', amount_grosze: 2800 })),
    );
    await onHome();

    await card();
    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(await screen.findByText(HOME.status.BOOKED)).toBeTruthy();
    expect(
      screen.getByLabelText('Your share, 28 zł, Fix your card by 10:30 to keep your seat'),
    ).toBeTruthy();

    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.title.FIX_THE_CARD }));
    expect(
      await screen.findByText(
        'Your bank declined the hold on the card on file. Fix it with another card.',
      ),
    ).toBeTruthy();
    // The sheet's note says it as the money row behind it does.
    expect(screen.getAllByText('Fix your card by 10:30 to keep your seat')).toHaveLength(2);
    expect(screen.getByRole('button', { name: 'Use this card', disabled: true })).toBeTruthy();
    expect(screen.queryByText(/Pay this share/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Paying in time, and out of time
// ---------------------------------------------------------------------------

describe('paying in time (Q110)', () => {
  it('books the game, and its payer sees It’s a game! — which they never saw — then Booked on Home', async () => {
    let paid = false;
    transport.on('GET', HOME_PATH, () =>
      json<Wire['HomeResponse']>({
        read_at: HOME_READ_AT,
        needing_you: paid ? 0 : 1,
        games: [
          paid
            ? homeGame({ booking_id: BOOKING, game_id: GAME_ID })
            : waitingForAPayment({ your_payment_due_by: DUE }),
        ],
      }),
    );
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({ payments: paid ? [] : [toConfirmRow()] }),
    );
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge()));
    transport.on('POST', CONFIRMATION_PATH, () => {
      paid = true;
      return json<Wire['YesAnswerResponse']>({
        proposal_id: BOOKING,
        open_seats: 0,
        booked: { booking_id: BOOKING, game_id: GAME_ID },
        your_payment: null,
        payment_awaited_until: null,
      });
    });
    stubBooking(transport, bookingDetails({ game_id: GAME_ID }));
    await onHome();

    const row = await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`);
    fireEvent.press(within(row).getByRole('button', { name: /^Confirm your payment for Padel/ }));
    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.check }));

    expect(
      await screen.findByRole('header', {
        name: 'It’s a game! You and piotr.s against ines.d and bartek.l',
      }),
    ).toBeTruthy();
    expect(toasts()).toEqual([]);

    fireEvent.press(screen.getByRole('button', { name: FILL.itsAGame.later }));
    await waitFor(() => expect(screen.queryByTestId('its-a-game')).toBeNull());
    expect(await within(await card()).findByText(HOME.status.BOOKED)).toBeTruthy();
    await waitFor(() => expect(screen.queryByTestId(`to-confirm-${SEAT_CHARGE}`)).toBeNull());
  });
});

describe('out of time (Q109, Q111)', () => {
  it('turns the others’ game into Seat open — told by the server, re-read by the phone', async () => {
    let ranOut = false;
    transport.on('GET', HOME_PATH, () =>
      json<Wire['HomeResponse']>({
        read_at: HOME_READ_AT,
        needing_you: 0,
        games: [
          ranOut
            ? waitingForAPayment({
                status: 'SEAT_OPEN',
                open_seats: 1,
                payment_due_by: null,
                filling_again: true,
              })
            : waitingForAPayment(),
        ],
      }),
    );
    await onHome();
    expect(await within(await card()).findByText(HOME.status.WAITING_FOR_A_PAYMENT)).toBeTruthy();

    ranOut = true;
    await told(
      notice({
        kind: 'SOMEONE_LEFT',
        title: 'Your Sat 16:00 is filling again',
        body: 'Padel at Bonarka Arena — a seat opened.',
      }),
    );

    expect(await screen.findByText('Your Sat 16:00 is filling again')).toBeTruthy();
    const drawn = await card();
    expect(await within(drawn).findByText(HOME.status.SEAT_OPEN)).toBeTruthy();
    expect(
      within(drawn).getByText('1 seat open · books when it’s full · nobody paid'),
    ).toBeTruthy();
  });

  it('takes the time off the payer’s To confirm row, and its notice opens the game to take the seat back', async () => {
    let ranOut = false;
    transport.on('GET', HOME_PATH, () =>
      json<Wire['HomeResponse']>({
        read_at: HOME_READ_AT,
        needing_you: 1,
        games: ranOut ? [] : [waitingForAPayment({ your_payment_due_by: DUE })],
      }),
    );
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({
        payments: [toConfirmRow(ranOut ? { confirm_by: null } : {})],
      }),
    );
    const game = deckCard({ proposal_id: BOOKING, in_count: 3, open_seats_after_your_yes: 0 });
    stubProposal(
      transport,
      BOOKING,
      proposalDetails(game, {
        pool_id: CREW_ID,
        read_at: HOME_READ_AT,
        actions: ['CONFIRM_PAYMENT'],
        your_payment: {
          seat_charge_id: SEAT_CHARGE,
          refusal: 'AUTHENTICATION_REQUIRED',
          confirm_by: null,
        },
      }),
    );
    stubGroupDeck(transport, CREW_ID, groupDeck());
    await onHome();
    const row = await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`);
    expect(within(row).getByText('Confirm your payment by 10:30')).toBeTruthy();

    ranOut = true;
    const timeRanOut = notice({
      kind: 'TIME_TO_PAY_RAN_OUT',
      title: 'Your time to pay ran out · Sat 16:00',
      body: 'Your seat is open to others now — confirm your payment to take it back while it’s free.',
    });
    await told(timeRanOut);

    // The row stays, without a time, while the seat is still free to take back.
    expect(
      await within(await screen.findByTestId(`to-confirm-${SEAT_CHARGE}`)).findByText(
        FILL.toConfirm.open,
      ),
    ).toBeTruthy();
    expect(screen.queryByText('Confirm your payment by 10:30')).toBeNull();

    fireEvent.press(
      await screen.findByRole('button', { name: `${timeRanOut.title}. ${timeRanOut.body}` }),
    );
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${BOOKING}`));
    expect(await screen.findByRole('button', { name: FILL.confirm.title.PAY })).toBeTruthy();
    expect(screen.queryByText(/Confirm your payment by/)).toBeNull();
  });
});
