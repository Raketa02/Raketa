/**
 * **The moment a yes fills a game, walked** — the ten seconds of *Undo* in front of a yes that
 * moves money, *It's a game!*, a first yes with nothing saved, and a refused share confirmed on the
 * same payment ([#555](https://github.com/Raketa02/Raketa/issues/555); the screens A2.4; the
 * mechanics §6.5, §11, §12.2).
 *
 * The real route tree, from a group's Games tab, with the socket, the haptic motor and the payment
 * provider's phone half faked at the platform edge (`fakePayments()` answers as Stripe's test cards
 * do). **The ten seconds are walked by advancing the fake clock past them, never by polling**: the
 * toast's ring drains on the UI thread, and a poll would run it frame by frame (`router-harness`
 * memory).
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { ScrollView } from 'react-native';

import { gameKeys } from '@/features/games/types';
import { PAYMENTS_COPY } from '@/features/payments/types';
import { FILL_COPY, PROPOSALS_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { doorRowLabel } from '@/shared/ui';
import {
  ANIA,
  deckCard,
  DECK_READ_AT,
  EWA,
  groupDeck,
  KAROL,
  proposalDetails,
  rescueCard,
  seatsPath,
  stubGroupDeck,
  stubProposal,
  yesPath,
  youTile,
  ZOFIA,
} from '@/test-support/groupDeck';
import { bookingDetails, stubBooking } from '@/test-support/home';
import {
  HOME_PATH,
  PAYMENTS_TO_CONFIRM_PATH,
  PAYMENT_TERMS_IN_FORCE,
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
import {
  FAKE_CARD_NUMBER,
  TEST_CARDS,
  fakeClipboard,
  fakeHaptics,
  fakePayments,
  fakeShare,
  type FakePayments,
} from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  neverResponds,
  type Transport,
  type Wire,
} from '@/test-support/transport';

const COPY = PROPOSALS_COPY;
const FILL = FILL_COPY;

/** Past the card's flight, so the stage has told the deck it has gone. */
const PAST_THE_FLIGHT = 400;
const SECOND = 1_000;

const HIDDEN_TOO = { includeHiddenElements: true } as const;

const VISA_4312: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };

const GAME_ID = 'a1000000-0000-4000-8000-000000000001';
const SEAT_CHARGE = 'a2000000-0000-4000-8000-000000000001';

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
  administrator_nickname: null,
  is_administrator: false,
};

/** A card your yes completes, at a club that sells at once: *Book it now*. */
function bookItNow(extra: Partial<Wire['DeckCardSchema']> = {}): Wire['DeckCardSchema'] {
  return deckCard({
    in_count: 3,
    open_seats_after_your_yes: 0,
    court: 'BOOK_IT_NOW',
    sides: {
      yours: [youTile(), ZOFIA({ is_in: true, photo_url: 'https://photos.test/zofia.jpg' })],
      theirs: [ANIA({ is_in: true }), EWA({ is_in: true })],
    },
    ...extra,
  });
}

/** A yes's answers, as #541's route gives them. */
const counted = (card: Wire['DeckCardSchema'], open = 2): Wire['YesAnswerResponse'] => ({
  proposal_id: card.proposal_id,
  open_seats: open,
  booked: null,
  your_payment: null,
});
const booked = (card: Wire['DeckCardSchema']): Wire['YesAnswerResponse'] => ({
  proposal_id: card.proposal_id,
  open_seats: 0,
  booked: { booking_id: card.proposal_id, game_id: GAME_ID },
  your_payment: null,
});
const refused = (
  card: Wire['DeckCardSchema'],
  refusal: Wire['PaymentRefusal'],
): Wire['YesAnswerResponse'] => ({
  proposal_id: card.proposal_id,
  open_seats: 1,
  booked: null,
  your_payment: { seat_charge_id: SEAT_CHARGE, refusal },
});

const SEAT_CHARGE_PATH = `/api/v1/seat-charges/${SEAT_CHARGE}`;
const CONFIRMATION_PATH = `${SEAT_CHARGE_PATH}/confirmation`;

/** The refused share, as `GET /seat-charges/{id}` answers while it waits for its player. */
function seatCharge(
  card: Wire['DeckCardSchema'],
  refusal: Wire['FailureReason'],
): Wire['SeatChargeResponse'] {
  return {
    seat_charge_id: SEAT_CHARGE,
    proposal_id: card.proposal_id,
    status: 'FAILED',
    refusal,
    amount_grosze: card.share_grosze,
    sport: 'PADEL',
    starts_at: card.starts_at,
    club: card.club,
    to_confirm: {
      client_secret: 'pi_1_secret_abc',
      connected_account_id: 'acct_bonarka',
      publishable_key: 'pk_test_raketa',
    },
  };
}

let transport: Transport;
let phone: FakePayments;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
  stubHaptics(fakeHaptics());
  phone = fakePayments();
  stubPayments(phone);
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

/** Land on the crew's Games tab, its deck dealing these cards until a yes is answered. */
async function openGames(
  cards: readonly Wire['DeckCardSchema'][],
  answer: (card: Wire['DeckCardSchema']) => Wire['YesAnswerResponse'] = (card) => counted(card),
) {
  let dealt = [...cards];
  for (const card of cards) {
    transport.on('POST', yesPath(card.proposal_id), () => {
      dealt = dealt.filter((held) => held.proposal_id !== card.proposal_id);
      return json(answer(card));
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

const yeses = (card: Wire['DeckCardSchema']) =>
  transport.requestsTo('POST', yesPath(card.proposal_id));
const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

/** *I'm in* with the ball, and the card's flight landed. */
function sayYes() {
  fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
  act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
}

/** The rest of the ten seconds, from a yes just said. */
const theRestOfTheTenSeconds = () =>
  act(() => jest.advanceTimersByTime(10 * SECOND - PAST_THE_FLIGHT));

// ---------------------------------------------------------------------------
// Undo
// ---------------------------------------------------------------------------

describe('a yes that moves money waits ten seconds behind Undo (§6.5)', () => {
  it('says Booking in 10 s with Undo, counts down, and sends the yes only when the ten seconds pass', async () => {
    const card = bookItNow();
    await openGames([card]);

    sayYes();

    expect(screen.getByText('Booking in 10 s')).toBeTruthy();
    expect(screen.getByRole('button', { name: FILL.undo.actionSpoken })).toBeTruthy();
    expect(yeses(card)).toHaveLength(0);

    act(() => jest.advanceTimersByTime(5 * SECOND));
    expect(screen.getByText('Booking in 5 s')).toBeTruthy();
    expect(yeses(card)).toHaveLength(0);

    act(() => jest.advanceTimersByTime(5 * SECOND - PAST_THE_FLIGHT));
    await waitFor(() => expect(yeses(card)).toHaveLength(1));
    expect(screen.queryByTestId('undo-toast')).toBeNull();
  });

  it('takes the yes back on Undo — nothing is ever sent, and the card is dealt again on top', async () => {
    const card = bookItNow();
    await openGames([card, deckCard()]);

    sayYes();
    expect(screen.queryByTestId(`game-card-${card.proposal_id}`)).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: FILL.undo.actionSpoken }));

    expect(screen.queryByTestId('undo-toast')).toBeNull();
    expect(await screen.findByTestId(`game-card-${card.proposal_id}`)).toBeTruthy();
    act(() => jest.advanceTimersByTime(15 * SECOND));
    expect(yeses(card)).toHaveLength(0);
  });

  it('holds every rescue join the same way, not only the last seat (Q74)', async () => {
    const rescue = rescueCard({ open_seats_after_your_yes: 1 });
    transport.on('POST', seatsPath(rescue.proposal_id), () => json(counted(rescue, 1)));
    await openGames([rescue]);

    // On a Seat open card, I'm in says what the share does (#645; Q113).
    fireEvent.press(screen.getByRole('button', { name: 'I’m in, 27 zł held until the cut-off' }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    expect(screen.getByText('Booking in 10 s')).toBeTruthy();
    theRestOfTheTenSeconds();
    await waitFor(() =>
      expect(transport.requestsTo('POST', seatsPath(rescue.proposal_id))).toHaveLength(1),
    );
  });

  it('sends a free vote at once, with no toast', async () => {
    const vote = deckCard();
    await openGames([vote]);

    sayYes();

    await waitFor(() => expect(yeses(vote)).toHaveLength(1));
    expect(screen.queryByTestId('undo-toast')).toBeNull();
  });

  it('takes a free vote while a booking counts down, and holds a second booking with a toast', async () => {
    const card = bookItNow();
    const second = bookItNow();
    const vote = deckCard();
    await openGames([card, second, vote]);

    sayYes();
    await screen.findByTestId(`game-card-${second.proposal_id}`);

    sayYes();
    expect(toasts()).toEqual([[FILL.undo.oneAtATime, 'base']]);
    // A refusal the player must read: held long, and closable — in its neutral colour.
    expect(useToastQueue.getState().queue[0]?.hold).toBe('read');
    expect(screen.getByTestId(`game-card-${second.proposal_id}`)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await screen.findByTestId(`game-card-${vote.proposal_id}`);
    sayYes();

    await waitFor(() => expect(yeses(vote)).toHaveLength(1));
    expect(yeses(card)).toHaveLength(0);
    expect(screen.getByText(/^Booking in \d+ s$/)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// It's a game!
// ---------------------------------------------------------------------------

describe('It’s a game! — for the player whose yes filled the game (§11.3)', () => {
  const sentence = 'It’s a game! You and zofia.b against ania.k and ewa.m';

  it('covers the phone with the faces, the word, Open game and Later', async () => {
    const card = bookItNow();
    await openGames([card], booked);

    sayYes();
    theRestOfTheTenSeconds();

    expect(await screen.findByRole('header', { name: sentence })).toBeTruthy();
    expect(screen.getByText(FILL.itsAGame.word)).toBeTruthy();
    // Booked and held at once — at every club, none confirms a game (#676): nothing is still
    // missing, so no line under the word (Q103), and no club's *answers by*.
    expect(screen.queryByText(/Nobody pays|answers by/)).toBeNull();
    expect(screen.getByTestId('yes-tile-photo')).toBeTruthy();
    expect(screen.getAllByTestId('yes-tile-poster')).toHaveLength(3);
    expect(screen.getByRole('button', { name: FILL.itsAGame.open })).toBeTruthy();
    expect(screen.getByRole('button', { name: FILL.itsAGame.later })).toBeTruthy();
  });

  it('Later takes it away and leaves the player on the deck', async () => {
    const card = bookItNow();
    await openGames([card], booked);
    sayYes();
    theRestOfTheTenSeconds();

    fireEvent.press(await screen.findByRole('button', { name: FILL.itsAGame.later }));

    await waitFor(() => expect(screen.queryByTestId('its-a-game')).toBeNull());
    expect(screen).toHavePathname(`/play/group/${CREW.id}`);
  });

  it('Open game lays Home down and opens the booked game over it', async () => {
    const card = bookItNow();
    await openGames([card], booked);
    sayYes();
    theRestOfTheTenSeconds();

    stubBooking(transport, bookingDetails({ booking_id: card.proposal_id, game_id: GAME_ID }));
    fireEvent.press(await screen.findByRole('button', { name: FILL.itsAGame.open }));

    // The booked game's details (#556), not the Classic game screen.
    await waitFor(() => expect(screen).toHavePathname(`/booking/${card.proposal_id}`));
    expect(screen.queryByTestId('its-a-game')).toBeNull();
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
  });

  it('comes for a yes the card called a free vote, when the others got there first', async () => {
    const vote = deckCard();
    await openGames([vote], booked);

    sayYes();

    expect(await screen.findByText(FILL.itsAGame.word)).toBeTruthy();
  });

  /**
   * Home's read is held by the shell all session, so it is re-read at once. The games list is
   * read only by a booked game's result screen, which nothing holds here — so what is asserted for
   * it is the cache flag, on an entry seeded where the navigation's timer flush cannot collect it.
   */
  it('re-reads Home’s games, and marks the games list stale, so the booked game is there', async () => {
    const card = bookItNow();
    await openGames([card], booked);
    queryClient
      .getQueryCache()
      .build(queryClient, { queryKey: gameKeys.list(), gcTime: Infinity })
      .setData([]);
    const homeBefore = transport.requestsTo('GET', HOME_PATH).length;

    sayYes();
    theRestOfTheTenSeconds();
    await screen.findByText(FILL.itsAGame.word);

    // The booking itself is Home's own read (#556).
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeBefore),
    );
    expect(queryClient.getQueryState(gameKeys.list())?.isInvalidated).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// The setup, before a first yes
// ---------------------------------------------------------------------------

describe('a first yes with nothing saved opens the payment setup (§6.1, §12.5)', () => {
  const SETUP_PATH = '/api/v1/players/me/payment-methods/setup';
  const TERMS_PATH = '/api/v1/players/me/payment-methods/terms';
  const SAVE_PATH = '/api/v1/players/me/payment-methods/confirmation';

  beforeEach(() => {
    stubPaymentMethod(transport, null);
    transport.on('POST', SETUP_PATH, () =>
      json<Wire['PaymentSetupResponse']>(
        {
          setup_id: 'seti_1',
          publishable_key: 'pk_test_raketa',
          terms_version: PAYMENT_TERMS_IN_FORCE,
        },
        201,
      ),
    );
    transport.on('POST', TERMS_PATH, () =>
      json<Wire['PaymentTermsResponse']>({ client_secret: 'seti_1_secret' }),
    );
    transport.on('POST', SAVE_PATH, () => {
      const saved = { ...VISA_4312, last_four: '4242' };
      stubPaymentMethod(transport, saved);
      return json<Wire['PaymentMethodResponse']>({
        method: saved,
        terms_needed: false,
        terms_version: PAYMENT_TERMS_IN_FORCE,
      });
    });
  });

  /** The four steps with Stripe's saving test card, as You › Payments walks them. */
  async function saveACard() {
    fireEvent.press(await screen.findByLabelText('Card'));
    fireEvent.press(screen.getByLabelText(PAYMENTS_COPY.continue));
    fireEvent.changeText(await screen.findByLabelText(FAKE_CARD_NUMBER), TEST_CARDS.saves);
    fireEvent.press(screen.getByLabelText(PAYMENTS_COPY.saveTheCard));
    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.accept));
  }

  it('opens over the deck instead of the yes, and sends nothing', async () => {
    const vote = deckCard();
    await openGames([vote]);

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));

    expect(await screen.findByText(PAYMENTS_COPY.setupSheet.title)).toBeTruthy();
    expect(screen.getByText(PAYMENTS_COPY.setupSheet.line)).toBeTruthy();
    expect(yeses(vote)).toHaveLength(0);
  });

  it('keeps the keyboard on a tap anywhere in the sheet, so the card field is never blurred natively', async () => {
    await openGames([deckCard()]);
    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));

    const sheet = await screen.findByTestId('bottom-sheet');
    // A tap on the sheet's words with the card field focused closed the app on iOS (#3 on the
    // bug list): `handled` sends the field a native blur, and Stripe's field traps on it.
    expect(within(sheet).UNSAFE_getByType(ScrollView).props.keyboardShouldPersistTaps).toBe(
      'always',
    );
  });

  it('lands the yes the moment a card is saved', async () => {
    const vote = deckCard();
    await openGames([vote]);
    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));

    await saveACard();

    await waitFor(() => expect(yeses(vote)).toHaveLength(1));
    expect(screen.queryByText(PAYMENTS_COPY.setupSheet.title)).toBeNull();
    expect(transport.requestsTo('POST', SAVE_PATH)).toHaveLength(1);
  });

  it('puts a Book it now yes behind its ten seconds once the card is saved', async () => {
    const card = bookItNow();
    await openGames([card], booked);
    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));

    await saveACard();

    expect(await screen.findByText('Booking in 10 s')).toBeTruthy();
    expect(yeses(card)).toHaveLength(0);
    act(() => jest.advanceTimersByTime(10 * SECOND));
    expect(await screen.findByText(FILL.itsAGame.word)).toBeTruthy();
  });

  it('counts a Book it now yes’s ten seconds again when the server asked for a method first', async () => {
    stubPaymentMethod(transport, VISA_4312);
    const card = bookItNow();
    await openGames([card], booked);
    let asked = false;
    transport.on('POST', yesPath(card.proposal_id), () => {
      if (asked) return json(booked(card));
      asked = true;
      return errorResponse(409, 'payment_method_required');
    });
    sayYes();
    theRestOfTheTenSeconds();

    await saveACard();

    expect(await screen.findByText('Booking in 10 s')).toBeTruthy();
    expect(yeses(card)).toHaveLength(1);
    act(() => jest.advanceTimersByTime(10 * SECOND));
    expect(await screen.findByText(FILL.itsAGame.word)).toBeTruthy();
    expect(yeses(card)).toHaveLength(2);
  });

  it('drops the yes when the sheet is closed, and leaves the card where it was', async () => {
    const vote = deckCard();
    await openGames([vote]);
    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));

    fireEvent.press(await screen.findByLabelText(PAYMENTS_COPY.setupSheet.close));

    await waitFor(() => expect(screen.queryByText(PAYMENTS_COPY.setupSheet.title)).toBeNull());
    expect(screen.getByTestId(`game-card-${vote.proposal_id}`)).toBeTruthy();
    expect(yeses(vote)).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// A refused share, and the confirmation that keeps the seat
// ---------------------------------------------------------------------------

describe('a payment that did not go through is confirmed on the same payment (§12.2)', () => {
  it('says so, and the bank’s check over the card on file books the game', async () => {
    const card = bookItNow();
    await openGames([card], (said) => refused(said, 'AUTHENTICATION_REQUIRED'));
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge(card, 'AUTHENTICATION_REQUIRED')));
    transport.on('POST', CONFIRMATION_PATH, () => json(booked(card)));

    sayYes();
    theRestOfTheTenSeconds();

    await waitFor(() => expect(toasts()).toEqual([[FILL.refused.yours.PAY, 'bad']]));
    expect(await screen.findByText(FILL.confirm.title.PAY)).toBeTruthy();
    expect(await screen.findByText('32 zł to Bonarka Arena')).toBeTruthy();
    expect(screen.getByText('Padel · Saturday · 16:00')).toBeTruthy();
    expect(screen.getByText(FILL.confirm.checkLine.PAY)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: FILL.confirm.check }));

    expect(await screen.findByText(FILL.itsAGame.word)).toBeTruthy();
    expect(phone.payments).toEqual([
      { accountId: 'acct_bonarka', clientSecret: 'pi_1_secret_abc', with: 'onFile' },
    ]);
    expect(transport.requestsTo('POST', CONFIRMATION_PATH)).toHaveLength(1);
    expect(screen.queryByText(FILL.confirm.title.PAY)).toBeNull();
  });

  it('pays a declined share with another card typed into the fields', async () => {
    const card = bookItNow();
    // After the cut-off, where the share is taken at once: its time to pay (Q113).
    await openGames([card], (said) => ({
      ...refused(said, 'DECLINED'),
      your_payment: {
        seat_charge_id: SEAT_CHARGE,
        refusal: 'DECLINED',
        confirm_by: new Date(DECK_READ_AT + 30 * 60 * SECOND).toISOString(),
        time_to: 'PAY',
      },
    }));
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge(card, 'DECLINED')));
    transport.on('POST', CONFIRMATION_PATH, () => json(booked(card)));

    sayYes();
    theRestOfTheTenSeconds();

    expect(await screen.findByText(FILL.confirm.declinedLine.PAY)).toBeTruthy();
    expect(
      screen.getByRole('button', { name: FILL.confirm.withThisCard.PAY, disabled: true }),
    ).toBeTruthy();

    fireEvent.changeText(screen.getByLabelText(FAKE_CARD_NUMBER), TEST_CARDS.saves);
    fireEvent.press(screen.getByRole('button', { name: FILL.confirm.withThisCard.PAY }));

    expect(await screen.findByText(FILL.itsAGame.word)).toBeTruthy();
    expect(phone.payments.map((asked) => asked.with)).toEqual(['typed']);
  });

  it('says what the bank said, and keeps the sheet for another try, when the check was closed', async () => {
    const card = bookItNow();
    await openGames([card], (said) => refused(said, 'AUTHENTICATION_REQUIRED'));
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge(card, 'AUTHENTICATION_REQUIRED')));
    phone.bank = 'closes';

    sayYes();
    theRestOfTheTenSeconds();
    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.check }));

    expect(await screen.findByText(FILL.confirm.phone.cancelled)).toBeTruthy();
    expect(transport.requestsTo('POST', CONFIRMATION_PATH)).toHaveLength(0);
    expect(screen.getByText(FILL.confirm.title.PAY)).toBeTruthy();
  });

  it('says the server’s refusal when somebody else took the seat first', async () => {
    const card = bookItNow();
    await openGames([card], (said) => refused(said, 'AUTHENTICATION_REQUIRED'));
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge(card, 'AUTHENTICATION_REQUIRED')));
    transport.on('POST', CONFIRMATION_PATH, () => errorResponse(409, 'proposal_is_full'));

    sayYes();
    theRestOfTheTenSeconds();
    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.check }));

    expect(await screen.findByText(FILL.confirm.refused.proposal_is_full)).toBeTruthy();
    expect(screen.queryByText(FILL.itsAGame.word)).toBeNull();
  });

  it('closes and says you are In again when the payment holds but the game is still short', async () => {
    const card = bookItNow();
    await openGames([card], (said) => refused(said, 'AUTHENTICATION_REQUIRED'));
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge(card, 'AUTHENTICATION_REQUIRED')));
    transport.on('POST', CONFIRMATION_PATH, () => json(counted(card, 1)));

    sayYes();
    theRestOfTheTenSeconds();
    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.check }));

    await waitFor(() => expect(screen.queryByText(FILL.confirm.title.PAY)).toBeNull());
    expect(toasts()).toContainEqual([FILL.confirm.kept, 'ok']);
  });

  it('opens on the payment a plain yes is refused for, when one waits on the game', async () => {
    const card = bookItNow();
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge(card, 'AUTHENTICATION_REQUIRED')));
    await openGames([card]);
    transport.on('POST', yesPath(card.proposal_id), () =>
      json(
        {
          code: 'payment_to_confirm',
          message: 'confirm',
          trace_id: 'trace-test',
          details: { seat_charge_id: SEAT_CHARGE },
        },
        409,
      ),
    );

    sayYes();
    theRestOfTheTenSeconds();

    expect(await screen.findByText(FILL.confirm.title.PAY)).toBeTruthy();
    expect(await screen.findByText('32 zł to Bonarka Arena')).toBeTruthy();
  });

  it('names You › Payments when the card’s new brand needs the terms again', async () => {
    const card = bookItNow();
    await openGames([card], (said) => refused(said, 'TERMS_NEEDED'));

    sayYes();
    theRestOfTheTenSeconds();

    await waitFor(() => expect(toasts()).toEqual([[FILL.termsAgain, 'bad']]));
    expect(screen.queryByText(FILL.confirm.title.PAY)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The game's details
// ---------------------------------------------------------------------------

describe('Pay on a game’s details, where the yes takes the last seat (Q124)', () => {
  /** Q113: the fill holds every share and books the court; the club's cut-off takes them. */
  it('draws no paragraph about what a yes costs on a filling game: the share line says it', async () => {
    const card = bookItNow();
    stubProposal(transport, card.proposal_id, proposalDetails(card));
    await openGames([card]);
    fireEvent.press(screen.getByRole('button', { name: COPY.details }));

    expect(await screen.findByText(/Filling · \d of \d in/)).toBeTruthy();
    expect(screen.queryByText(/costs nothing until everybody is in/)).toBeNull();
    expect(screen.queryByText(/charged/)).toBeNull();
  });

  it('counts down too, and a booked game leaves the details for the deck under It’s a game!', async () => {
    const card = bookItNow({
      sides: {
        yours: [youTile(), KAROL({ is_in: true })],
        theirs: [ANIA({ is_in: true }), EWA({ is_in: true })],
      },
    });
    stubProposal(transport, card.proposal_id, proposalDetails(card));
    await openGames([card], booked);
    fireEvent.press(screen.getByRole('button', { name: COPY.details }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW.id}/game/${card.proposal_id}`),
    );

    // The last seat's yes books the game and moves money, so it says Pay with the share.
    expect(await screen.findByText('Pay 32 zł')).toBeTruthy();
    expect(screen.queryByRole('button', { name: COPY.yes })).toBeNull();
    fireEvent.press(screen.getByRole('button', { name: 'Pay 32 zł' }));

    expect(screen.getByText('Booking in 10 s')).toBeTruthy();
    expect(screen.getByRole('button', { name: FILL.undo.booking })).toBeTruthy();
    expect(yeses(card)).toHaveLength(0);

    act(() => jest.advanceTimersByTime(10 * SECOND));

    expect(await screen.findByText(FILL.itsAGame.word, HIDDEN_TOO)).toBeTruthy();
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
  });

  it('leaves the details, and says so, when the counted yes finds the game gone', async () => {
    const card = bookItNow();
    stubProposal(transport, card.proposal_id, proposalDetails(card));
    await openGames([card]);
    transport.on('POST', yesPath(card.proposal_id), () => errorResponse(409, 'proposal_is_full'));
    fireEvent.press(screen.getByRole('button', { name: COPY.details }));
    fireEvent.press(await screen.findByRole('button', { name: 'Pay 32 zł' }));

    act(() => jest.advanceTimersByTime(10 * SECOND));

    await waitFor(() => expect(toasts()).toEqual([[COPY.refused.proposal_is_full, 'bad']]));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
  });

  // `docs/specs/busy-indicator/decisions.md` §3.3: at zero the button went back to *Pay 32 zł* while
  // the booking — money — was still on its way, a press that looked like it would send it again.
  it('stays Booking… after the ten seconds, while the yes is on its way, and takes no press', async () => {
    const card = bookItNow();
    stubProposal(transport, card.proposal_id, proposalDetails(card));
    await openGames([card]);
    transport.on('POST', yesPath(card.proposal_id), neverResponds());
    fireEvent.press(screen.getByRole('button', { name: COPY.details }));
    fireEvent.press(await screen.findByRole('button', { name: 'Pay 32 zł' }));

    act(() => jest.advanceTimersByTime(10 * SECOND));
    await waitFor(() => expect(yeses(card)).toHaveLength(1));

    const sending = screen.getByRole('button', { name: FILL.undo.booking });
    expect(sending.props.accessibilityState).toMatchObject({ busy: true });
    expect(screen.queryByRole('button', { name: 'Pay 32 zł' })).toBeNull();
    fireEvent.press(sending);
    expect(yeses(card)).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// TO CONFIRM, on You › Payments
// ---------------------------------------------------------------------------

describe('a share refused while the player was elsewhere waits on You › Payments', () => {
  const waiting = (card: Wire['DeckCardSchema']) => ({
    seat_charge_id: SEAT_CHARGE,
    refusal: 'AUTHENTICATION_REQUIRED' as const,
    proposal_id: card.proposal_id,
    pool_id: CREW.id,
    sport: 'PADEL' as const,
    kind: 'COMPETITIVE' as const,
    starts_at: card.starts_at,
    club: card.club,
    share_grosze: card.share_grosze,
    book_by: card.deadline,
    confirm_by: null,
    time_to: null,
  });

  async function onPayments() {
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('You'));
    fireEvent.press(await screen.findByLabelText(doorRowLabel('Payments', 'Card •••• 4312')));
  }

  // Q110: the payment that completes the game shows its payer It's a game!, which they never saw —
  // its faces read off the booking, since a row holds no card.
  it('lists it under TO CONFIRM, and Confirm books the game on the same payment — It’s a game!', async () => {
    const card = bookItNow();
    let confirmed = false;
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
      json<Wire['PaymentsToConfirmResponse']>({ payments: confirmed ? [] : [waiting(card)] }),
    );
    transport.on('GET', SEAT_CHARGE_PATH, () => json(seatCharge(card, 'AUTHENTICATION_REQUIRED')));
    transport.on('POST', CONFIRMATION_PATH, () => {
      confirmed = true;
      return json(booked(card));
    });
    stubBooking(transport, bookingDetails({ booking_id: card.proposal_id, game_id: GAME_ID }));
    await onPayments();

    expect(await screen.findByRole('header', { name: FILL.toConfirm.title })).toBeTruthy();
    expect(screen.getByText(FILL.toConfirm.open)).toBeTruthy();
    fireEvent.press(
      screen.getByRole('button', {
        name: 'Confirm your payment for Padel · Saturday 16:00 at Bonarka Arena, 32 zł',
      }),
    );
    fireEvent.press(await screen.findByRole('button', { name: FILL.confirm.check }));

    expect(
      await screen.findByRole('header', {
        name: 'It’s a game! You and piotr.s against ines.d and bartek.l',
      }),
    ).toBeTruthy();
    expect(toasts()).toEqual([]);
    await waitFor(() => expect(screen.queryByTestId(`to-confirm-${SEAT_CHARGE}`)).toBeNull());
  });

  it('draws nothing when nothing waits', async () => {
    await onPayments();

    await screen.findByText(PAYMENTS_COPY.method.heldAndTaken);
    expect(screen.queryByText(FILL.toConfirm.title)).toBeNull();
  });
});
