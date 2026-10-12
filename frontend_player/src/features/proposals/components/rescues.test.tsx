/**
 * **Rescues, walked** — a booked game that lost a player, its open seat dealt as a *Seat open* card
 * and taken from the card or from its details seen from outside
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A2.3, A2.4, A4.3; mock 2; the
 * mechanics §10.1; the backend's #545).
 *
 * **What the share does** ([#645](https://github.com/Raketa02/Raketa/issues/645); Q113): before
 * the club's cut-off *I'm in · 27 zł* is said *held until the cut-off*, and once in, the rescuer
 * reads the game as everybody does — held, free to leave until the cut-off; after it, *paid now*.
 * **A rescuer whose card is refused** keeps the seat for 30 minutes (#640), told to fix the card
 * before the cut-off, to confirm the payment after it, *to take the seat*.
 *
 * The real route tree, from a group's Games tab, with the payment provider's phone half faked at the
 * platform edge. **The ten seconds are walked by advancing the fake clock past them, never by
 * polling** (`theFill.test.tsx`'s rule).
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { FILL_COPY, PROPOSALS_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ANIA,
  DECK_READ_AT,
  KAROL,
  groupDeck,
  rescueCard,
  rescueNoPath,
  seatsPath,
  stubGroupDeck,
  yesPath,
  youTile,
} from '@/test-support/groupDeck';
import {
  BOOKED_STARTS_AT,
  bookedMoney,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
  takenMoney,
} from '@/test-support/home';
import {
  PAYMENTS_TO_CONFIRM_PATH,
  bookingPath,
  launchSignedIn,
  resetClipboard,
  resetHaptics,
  resetPayments,
  resetShare,
  stubClipboard,
  stubGate,
  stubHaptics,
  stubMyGroups,
  stubPaymentMethod,
  stubPayments,
  stubProfileOptions,
  stubProfileSurface,
  stubShare,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, fakeHaptics, fakePayments, fakeShare } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

const COPY = PROPOSALS_COPY;
const FILL = FILL_COPY;

const PAST_THE_FLIGHT = 400;
const SECOND = 1_000;

/** *I'm in · 27 zł* aloud, before the club's cut-off and after it (Q113). */
const HELD_UNTIL_THE_CUT_OFF = 'I’m in, 27 zł held until the cut-off';
const PAID_NOW = 'I’m in, 27 zł paid now';

const HIDDEN_TOO = { includeHiddenElements: true } as const;

const VISA_4312: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };

const GAME_ID = 'a1000000-0000-4000-8000-000000000009';

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

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

const PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://raketa.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [{ sport: 'PADEL', rated_count: 5, first_rated: [] }],
  member_faces: [],
  administrator_name: null,
  is_administrator: false,
};

/** The seat taken — the booking and its Game, now on the reader's Home. */
const taken = (card: Wire['DeckCardSchema']): Wire['YesAnswerResponse'] => ({
  proposal_id: card.proposal_id,
  open_seats: 0,
  booked: { booking_id: card.proposal_id, game_id: GAME_ID },
  waiting_for_the_club: false,
  your_payment: null,
});

/** A booked tile, from the deck's — paid unless it is the reader's, which is the open seat. */
function bookedTile(tile: Wire['DeckTileSchema']): Wire['BookedTileSchema'] {
  return {
    player_id: tile.player_id,
    is_you: tile.is_you,
    name: tile.name,
    photo_id: tile.photo_id,
    photo_url: tile.photo_url,
    level: tile.level,
    paid: !tile.is_you,
  };
}

/**
 * **The rescue as its details read it from outside** — the card's game: you in the seat that opened
 * on Kuba's side, unpaid; Karol and Ania across, paid; Court 6 at Ogrody 33, fills by the cut-off.
 */
function rescueDetails(card: Wire['DeckCardSchema']): Wire['BookingDetailsResponse'] {
  return bookingDetails({
    booking_id: card.proposal_id,
    game_id: GAME_ID,
    pool_id: CREW.id,
    read_at: new Date(DECK_READ_AT).toISOString(),
    status: 'SEAT_OPEN',
    open_seats: 1,
    starts_at: card.starts_at,
    ends_at: '2026-10-03T15:00:00Z',
    where: { id: card.club.id, name: card.club.name, distance_km: 3.1 },
    court_name: 'Court 6',
    sides: {
      yours: card.sides.yours.map(bookedTile),
      theirs: card.sides.theirs.map(bookedTile),
    },
    money: {
      share_grosze: card.share_grosze,
      paid: false,
      share_state: null,
      held_from: null,
      taken_at: null,
      free_to_leave_until: null,
      refunded_grosze: null,
    },
    shows_forecast: false,
    leaving: null,
    rescue: { deadline: card.deadline, fills_by_the_cut_off: true },
  });
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
  stubHaptics(fakeHaptics());
  stubPayments(fakePayments());
  stubPaymentMethod(transport, VISA_4312);
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
});

/** Land on the crew's Games tab, its deck dealing these cards until one is answered. */
async function openGames(
  cards: readonly Wire['DeckCardSchema'][],
  join: (card: Wire['DeckCardSchema']) => ReturnType<typeof json> = (card) => json(taken(card)),
) {
  let dealt = [...cards];
  const answered = (card: Wire['DeckCardSchema']) => {
    dealt = dealt.filter((held) => held.proposal_id !== card.proposal_id);
  };
  for (const card of cards) {
    transport.on('POST', seatsPath(card.proposal_id), () => {
      answered(card);
      return join(card);
    });
    transport.on('POST', rescueNoPath(card.proposal_id), () => {
      answered(card);
      return noContent();
    });
  }
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, () => groupDeck({ cards: dealt }));
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
  const first = cards[0];
  if (first !== undefined) await screen.findByTestId(`game-card-${first.proposal_id}`);
}

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

/** A rescue after the club's cut-off: offered until the start, and paid at once. */
const lateRescue = () => rescueCard({ no_free_cancellation: true, deadline: BOOKED_STARTS_AT });

/** The ten seconds, from a yes just said. */
const theTenSeconds = () => act(() => jest.advanceTimersByTime(10 * SECOND));

// ---------------------------------------------------------------------------
// The card
// ---------------------------------------------------------------------------

describe('a Seat open card in the deck (A2.3, mock 2)', () => {
  it('draws the players paid, your dashed seat, the court booked with its number and the price on the stamp', async () => {
    await openGames([rescueCard()]);

    expect(await screen.findByRole('header', { name: /^Seat open · court booked/ })).toBeTruthy();
    expect(screen.getByLabelText('Karol Tomaszewski, level 2,75, paid')).toBeTruthy();
    expect(screen.getByLabelText('Kuba Wiśniewski, level 2,80, paid')).toBeTruthy();
    expect(screen.getByLabelText('Your seat: you complete it, 27 zł, court booked')).toBeTruthy();
    expect(screen.getByText('27 zł · court booked')).toBeTruthy();
    expect(
      screen.getByLabelText('Booked, 27 zł, Saturday 16:00 · Ogrody 33 · Court 6'),
    ).toBeTruthy();
    expect(screen.getByText('I’m in · 27 zł', HIDDEN_TOO)).toBeTruthy();
  });

  it('says You? with the share while another seat is open too', async () => {
    await openGames([
      rescueCard({
        open_seats_after_your_yes: 1,
        sides: { yours: [youTile()], theirs: [KAROL({ paid: true }), ANIA({ paid: true })] },
      }),
    ]);

    expect(await screen.findByLabelText('Your seat, 27 zł')).toBeTruthy();
    expect(screen.getByText(COPY.youQuestion)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Taking the seat from the card
// ---------------------------------------------------------------------------

describe('taking the seat from the card (A2.4)', () => {
  it('counts ten seconds, then takes the booking’s seat, and It’s a game! opens it from Home', async () => {
    const card = rescueCard();
    await openGames([card]);

    fireEvent.press(screen.getByRole('button', { name: HELD_UNTIL_THE_CUT_OFF }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    expect(screen.getByText('Booking in 10 s')).toBeTruthy();
    expect(transport.requestsTo('POST', seatsPath(card.proposal_id))).toHaveLength(0);

    theTenSeconds();

    await waitFor(() =>
      expect(transport.requestsTo('POST', seatsPath(card.proposal_id))).toHaveLength(1),
    );
    expect(transport.requestsTo('POST', yesPath(card.proposal_id))).toHaveLength(0);
    expect(
      await screen.findByRole('header', {
        name: 'It’s a game! You and Kuba Wiśniewski against Karol Tomaszewski and Ania Kowalska',
      }),
    ).toBeTruthy();

    stubBooking(
      transport,
      bookingDetails({ booking_id: card.proposal_id, game_id: GAME_ID, pool_id: CREW.id }),
    );
    fireEvent.press(screen.getByRole('button', { name: FILL.itsAGame.open }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${card.proposal_id}`));
  });

  it('says no to the booking, and the card does not come back', async () => {
    const card = rescueCard();
    await openGames([card]);

    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    await waitFor(() =>
      expect(transport.requestsTo('POST', rescueNoPath(card.proposal_id))).toHaveLength(1),
    );
    expect(transport.requestsTo('POST', `/api/v1/proposals/${card.proposal_id}/no`)).toHaveLength(
      0,
    );
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
  });

  it('says Someone just took it when another join won the race, and lets the card go', async () => {
    const card = rescueCard();
    await openGames([card], () => errorResponse(409, 'seat_just_taken'));

    fireEvent.press(screen.getByRole('button', { name: HELD_UNTIL_THE_CUT_OFF }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    theTenSeconds();

    await waitFor(() => expect(toasts()).toContainEqual(['Someone just took it.', 'bad']));
    expect(screen.queryByTestId('its-a-game')).toBeNull();
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The rescue seen from outside
// ---------------------------------------------------------------------------

describe('the rescue seen from outside (A4.3)', () => {
  async function openRescue(card = rescueCard()) {
    stubBooking(transport, rescueDetails(card));
    await openGames([card]);
    fireEvent.press(await screen.findByRole('button', { name: COPY.details }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW.id}/rescue/${card.proposal_id}`),
    );
    await screen.findByLabelText('Your seat: you complete it, 27 zł, court booked');
    return card;
  }

  it('opens from the i: the players paid, your dashed seat, the court, how long it is offered, and I’m in — no Chat, no Leave', async () => {
    await openRescue();

    expect(screen.getByText('Seat open')).toBeTruthy();
    expect(screen.getByText('Padel · seat open')).toBeTruthy();
    expect(screen.getByLabelText('Karol Tomaszewski, level 2,75, paid')).toBeTruthy();
    expect(screen.getByLabelText('Where, Ogrody 33, Court 6 · 3,1 km')).toBeTruthy();
    // The card's deadline is the cut-off, 21 hours after the read: Thursday 07:00 in Warsaw.
    expect(screen.getByLabelText('Your share, 27 zł, fills by Thu 07:00')).toBeTruthy();
    expect(screen.getByRole('button', { name: HELD_UNTIL_THE_CUT_OFF })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Chat' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Leave the game' })).toBeNull();
  });

  it('takes the seat from there: ten seconds, the booking’s seat, It’s a game!, and back to the group', async () => {
    const card = await openRescue();

    fireEvent.press(screen.getByRole('button', { name: HELD_UNTIL_THE_CUT_OFF }));

    expect(screen.getByText('Booking in 10 s')).toBeTruthy();
    expect(screen.getByRole('button', { name: FILL.undo.booking })).toBeTruthy();
    theTenSeconds();

    await waitFor(() =>
      expect(transport.requestsTo('POST', seatsPath(card.proposal_id))).toHaveLength(1),
    );
    expect(await screen.findByText(FILL.itsAGame.word)).toBeTruthy();
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
  });

  it('says the seat is gone when it was taken before the details were read', async () => {
    const card = rescueCard();
    await openGames([card]);
    transport.on('GET', bookingPath(card.proposal_id), () =>
      errorResponse(404, 'booking_not_found'),
    );

    fireEvent.press(await screen.findByRole('button', { name: COPY.details }));

    expect(await screen.findByText('This seat isn’t offered to you any more.')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// What taking the seat does with the share (#645; Q113)
// ---------------------------------------------------------------------------

describe('what taking the seat does with the share (#645; Q113)', () => {
  it('says I’m in on the card is held until the cut-off before it, and paid now after it', async () => {
    await openGames([rescueCard()]);
    expect(screen.getByRole('button', { name: HELD_UNTIL_THE_CUT_OFF })).toBeTruthy();
    expect(screen.queryByRole('button', { name: PAID_NOW })).toBeNull();
  });

  it('says paid now on a seat offered after the cut-off — the card and its details', async () => {
    const card = lateRescue();
    stubBooking(transport, {
      ...rescueDetails(card),
      rescue: { deadline: card.deadline, fills_by_the_cut_off: false },
    });
    await openGames([card]);
    expect(screen.getByRole('button', { name: PAID_NOW })).toBeTruthy();

    fireEvent.press(await screen.findByRole('button', { name: COPY.details }));
    expect(await screen.findByLabelText('Your share, 27 zł, offered until the start')).toBeTruthy();
    expect(screen.getByRole('button', { name: PAID_NOW })).toBeTruthy();
  });

  /** Once in, the rescuer is any player: held until the cut-off, and free to leave until then. */
  it('reads the joined game as everybody does — held, and free to leave until the cut-off', async () => {
    const card = rescueCard();
    const joined = { booking_id: card.proposal_id, money: bookedMoney({ share_grosze: 2700 }) };
    await openGames([card]);
    stubHomeGames(transport, [homeGame(joined)]);
    stubBooking(transport, bookingDetails({ ...joined, game_id: GAME_ID, pool_id: CREW.id }));

    fireEvent.press(screen.getByRole('button', { name: HELD_UNTIL_THE_CUT_OFF }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    theTenSeconds();
    fireEvent.press(await screen.findByRole('button', { name: FILL.itsAGame.open }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${card.proposal_id}`));
    expect(
      await screen.findByLabelText(
        'Your share, 27 zł, Held on your card · taken Fri 16:00 · free to leave until then',
      ),
    ).toBeTruthy();
    act(() => router.back());
    const drawn = await screen.findByTestId(`home-game-${card.proposal_id}`);
    expect(within(drawn).getByText('27 zł · free to leave until Fri 16:00')).toBeTruthy();
  });

  it('reads it paid once joined after the cut-off', async () => {
    const card = lateRescue();
    const joined = { booking_id: card.proposal_id, money: takenMoney({ share_grosze: 2700 }) };
    await openGames([card]);
    stubHomeGames(transport, [homeGame(joined)]);
    stubBooking(transport, bookingDetails({ ...joined, game_id: GAME_ID, pool_id: CREW.id }));

    fireEvent.press(screen.getByRole('button', { name: PAID_NOW }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    theTenSeconds();
    fireEvent.press(await screen.findByRole('button', { name: FILL.itsAGame.open }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${card.proposal_id}`));
    expect(await screen.findByLabelText('Paid, 27 zł, Paid')).toBeTruthy();
    act(() => router.back());
    const drawn = await screen.findByTestId(`home-game-${card.proposal_id}`);
    expect(within(drawn).getByText('Paid · 27 zł')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// A refused rescuer keeps the seat (#640, #645)
// ---------------------------------------------------------------------------

describe('a rescuer whose card is refused keeps the seat for 30 minutes (#640, #645)', () => {
  const SEAT_CHARGE = 'a2000000-0000-4000-8000-000000000007';
  /** Half an hour after the deck's read: 10:30 on Wednesday, the end of the kept seat. */
  const KEPT_UNTIL = new Date(DECK_READ_AT + 30 * 60 * SECOND).toISOString();

  const refused = (
    card: Wire['DeckCardSchema'],
    timeTo: Wire['TimeTo'],
  ): Wire['YesAnswerResponse'] => ({
    proposal_id: card.proposal_id,
    open_seats: 1,
    booked: null,
    waiting_for_the_club: false,
    your_payment: {
      seat_charge_id: SEAT_CHARGE,
      refusal: 'AUTHENTICATION_REQUIRED',
      confirm_by: KEPT_UNTIL,
      time_to: timeTo,
    },
    payment_awaited_until: null,
  });

  function stubSeatCharge(card: Wire['DeckCardSchema']) {
    transport.on('GET', `/api/v1/seat-charges/${SEAT_CHARGE}`, () =>
      json<Wire['SeatChargeResponse']>({
        seat_charge_id: SEAT_CHARGE,
        proposal_id: card.proposal_id,
        status: 'FAILED',
        refusal: 'AUTHENTICATION_REQUIRED',
        amount_grosze: card.share_grosze,
        sport: 'PADEL',
        starts_at: card.starts_at,
        club: card.club,
        to_confirm: {
          client_secret: 'pi_1_secret_abc',
          connected_account_id: 'acct_ogrody',
          publishable_key: 'pk_test_raketa',
        },
      }),
    );
  }

  it('before the cut-off, is told to fix the card to take the seat — nothing paid, the seat kept', async () => {
    const card = rescueCard();
    stubSeatCharge(card);
    await openGames([card], () => json(refused(card, 'FIX_THE_CARD')));

    fireEvent.press(screen.getByRole('button', { name: HELD_UNTIL_THE_CUT_OFF }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    theTenSeconds();

    expect(
      await screen.findByText(
        'Fix your card by 10:30 to take the seat — it’s kept for you until then',
      ),
    ).toBeTruthy();
    expect(screen.getByText(FILL.confirm.title.FIX_THE_CARD)).toBeTruthy();
    expect(screen.getByText(FILL.confirm.onlyPlacedAgain)).toBeTruthy();
    expect(toasts()).toEqual([
      ['Your card didn’t go through — fix it to take the seat. Nothing is paid now.', 'bad'],
    ]);
    expect(screen.queryByTestId('its-a-game')).toBeNull();
  });

  it('after the cut-off, is told to confirm the payment to take the seat', async () => {
    const card = lateRescue();
    stubSeatCharge(card);
    await openGames([card], () => json(refused(card, 'PAY')));

    fireEvent.press(screen.getByRole('button', { name: PAID_NOW }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    theTenSeconds();

    expect(
      await screen.findByText(
        'Confirm your payment by 10:30 to take the seat — it’s kept for you until then',
      ),
    ).toBeTruthy();
    expect(screen.getByText(FILL.confirm.title.PAY)).toBeTruthy();
    expect(screen.queryByText(FILL.confirm.onlyPlacedAgain)).toBeNull();
    expect(toasts()).toEqual([
      ['Your payment didn’t go through — confirm it to take the seat', 'bad'],
    ]);
  });

  it('reads the kept seat on the rescue’s details, its confirmation where I’m in stood', async () => {
    const card = rescueCard();
    stubSeatCharge(card);
    stubBooking(transport, {
      ...rescueDetails(card),
      your_payment_due_by: KEPT_UNTIL,
      time_to: 'FIX_THE_CARD',
    });
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({
        payments: [
          {
            seat_charge_id: SEAT_CHARGE,
            refusal: 'AUTHENTICATION_REQUIRED',
            proposal_id: card.proposal_id,
            pool_id: CREW.id,
            sport: 'PADEL',
            kind: 'COMPETITIVE',
            starts_at: card.starts_at,
            club: card.club,
            share_grosze: card.share_grosze,
            book_by: card.deadline,
            confirm_by: KEPT_UNTIL,
            time_to: 'FIX_THE_CARD',
          },
        ],
      }),
    );
    await openGames([card]);

    fireEvent.press(await screen.findByRole('button', { name: COPY.details }));
    expect(
      await screen.findByLabelText('Your share, 27 zł, Fix your card by 10:30 to take the seat'),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: HELD_UNTIL_THE_CUT_OFF })).toBeNull();
    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.title.FIX_THE_CARD }));

    expect(
      await screen.findByText(
        'Fix your card by 10:30 to take the seat — it’s kept for you until then',
      ),
    ).toBeTruthy();
  });
});
