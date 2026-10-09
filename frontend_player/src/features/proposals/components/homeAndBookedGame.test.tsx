/**
 * **Home and a booked game, walked the way a player walks them** — the real route tree, the real
 * shell, the real Home tab, and only `fetch` faked ([#556](https://github.com/Raketa02/Raketa/issues/556);
 * the screens A4.1, A4.4, A8; the mechanics §11.4, §14).
 *
 * The acceptance criteria are assertions here: a Home card says its status and its money line, is
 * *new* until opened, carries *Open game* and the chat's bubble — which is not a door; the details
 * draw the top bar, the game card with *paid* tiles and the court facts, the Game's forecast and the
 * code to show at the desk on the day; and the chat is reached from the details only, without the
 * plan card or a *Details* button, its back chevron returning to the details.
 *
 * The rules are `domain/home.test.ts`'s and the words `homePresentation.test.ts`'s; what is asserted
 * here is that the screens are wired to both.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { router } from 'expo-router';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { BALANCE_FORECAST } from '@/features/games/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { PagerDots } from '@/shared/ui';
import {
  BARTEK,
  BOOKED_GAME,
  BOOKED_ROOM,
  BOOKING,
  CLUB_ANSWERS_BY,
  HOME_READ_AT,
  INES,
  PIOTR,
  bookedGameOnTheList,
  bookedMoney,
  bookedRoom,
  bookedRoomRow,
  bookedSides,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import {
  CONVERSATIONS_PATH,
  GAMES_PATH,
  GATE_USER,
  HOME_PATH,
  HOME_TAB_LINE,
  bookingPath,
  launchSignedIn,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPairing,
  stubPaymentsToConfirm,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FILL_COPY } from './fillCopy';
import { HOME_GAME_COPY } from './homeCopy';

const HOME = HOME_GAME_COPY;
const HIDDEN_TOO = { includeHiddenElements: true } as const;
const DETAILS = HOME_GAME_COPY.details;

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
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  // What this phone kept as opened would make the next suite's game not new.
  await forgetPhonePreferences();
});

const card = () => screen.findByTestId(`home-game-${BOOKING}`);

/** A Game no booking stands for — what the old loop left on `GET /games`. */
const OLD_LOOP_GAME = '3f2b8c1e-0000-4000-8000-0000000000f1';
/** A second booking, still waiting for its club. */
const SECOND_BOOKING = '3f2b8c1e-0000-4000-8000-0000000000b2';

const HOUR = 60 * 60 * 1000;

/**
 * **Story S-01A's waiting game** — full, at an On request club with an hour to answer, read at
 * 10:00: nobody has paid, there is no Game and no court yet, and the club answers by 11:00.
 */
const waitingForKazimierz = {
  status: 'WAITING_FOR_THE_CLUB',
  game_id: null,
  court_name: null,
  money: bookedMoney({ share_grosze: 2500, paid: false, free_to_leave_until: null }),
  answer_by: CLUB_ANSWERS_BY,
} as const;
const KAZIMIERZ = 'Kazimierz Padel';

// ---------------------------------------------------------------------------
// Home
// ---------------------------------------------------------------------------

describe('Home — a booked game’s card (A8)', () => {
  it('draws the status, the court, the day and the money line, with Open game', async () => {
    stubHomeGames(transport, [homeGame()]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status.BOOKED)).toBeTruthy();
    expect(within(drawn).getByText('Bonarka Arena')).toBeTruthy();
    expect(within(drawn).getByText('Saturday')).toBeTruthy();
    expect(within(drawn).getByText('Paid · 28 zł · free to leave until Fri 16:00')).toBeTruthy();
    expect(screen.getByRole('button', { name: HOME.openGame })).toBeTruthy();
    expect(screen.getByText('Your games · 1')).toBeTruthy();
  });

  it.each<[Wire['HomeStatus'], Partial<Wire['HomeGameSchema']>, string | undefined]>([
    [
      'WAITING_FOR_THE_CLUB',
      {
        game_id: null,
        court_name: null,
        money: bookedMoney({ paid: false, free_to_leave_until: null }),
      },
      'Nobody pays until Bonarka Arena confirms',
    ],
    [
      'SEAT_OPEN',
      { open_seats: 2, sides: { ...bookedSides(), theirs: [] } },
      '2 seats open · fills by Fri 16:00 or the game is off and everyone is refunded',
    ],
    [
      'SEAT_OPEN',
      { open_seats: 1, money: bookedMoney({ free_to_leave_until: null }) },
      '1 seat open · offered to others · the game goes ahead',
    ],
    ['NEEDS_RESULT', { needs_you: true }, undefined],
    ['CONFIRM_THE_RESULT', {}, undefined],
    ['COUNTED', {}, undefined],
    [
      'UNCOUNTED',
      { uncounted_reason: 'SEAT_EMPTY', money: bookedMoney({ free_to_leave_until: null }) },
      'A seat was empty · no Level moved',
    ],
    [
      'CALLED_OFF',
      {
        called_off_reason: 'SHORT_AT_THE_CUT_OFF',
        money: bookedMoney({ free_to_leave_until: null, refunded_grosze: 2800 }),
      },
      'A seat was still empty at the cut-off · Refunded 28 zł',
    ],
    [
      'CALLED_OFF',
      {
        called_off_reason: 'REFUSED',
        game_id: null,
        money: bookedMoney({ paid: false, free_to_leave_until: null }),
      },
      'Bonarka Arena couldn’t take it · Nobody paid',
    ],
    [
      'CALLED_OFF',
      {
        called_off_reason: 'NO_ANSWER',
        game_id: null,
        money: bookedMoney({ paid: false, free_to_leave_until: null }),
      },
      'Bonarka Arena didn’t answer in time · Nobody paid',
    ],
  ])('draws %s with its line', async (status, extra, line) => {
    stubHomeGames(transport, [homeGame({ status, ...extra })]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status[status])).toBeTruthy();
    if (line === undefined) {
      expect(within(drawn).queryByText(/zł|Nobody|seat open|seat was/)).toBeNull();
    } else {
      expect(within(drawn).getByText(line)).toBeTruthy();
    }
  });

  it('names no court on a game waiting for the club, which has no Game yet', async () => {
    stubHomeGames(transport, [
      homeGame({
        status: 'WAITING_FOR_THE_CLUB',
        game_id: null,
        court_name: null,
        money: bookedMoney({ paid: false, free_to_leave_until: null }),
      }),
    ]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText('Bonarka Arena')).toBeTruthy();
    expect(within(drawn).queryByText(/Court/)).toBeNull();
    expect(within(drawn).queryByTestId('home-game-chat')).toBeNull();
  });

  it('says when the club answers, and drops it once that has passed (Q98)', async () => {
    const home = homeGame({ ...waitingForKazimierz });
    stubHomeGames(transport, [{ ...home, club: { ...home.club, name: KAZIMIERZ } }]);
    await launchSignedIn();

    const drawn = await card();
    expect(
      within(drawn).getByText('Kazimierz Padel answers by 11:00 · Nobody pays until it confirms'),
    ).toBeTruthy();
    // Said as part of the line, its dots commas.
    expect(
      screen.getByLabelText(/Kazimierz Padel answers by 11:00, Nobody pays until it confirms\./),
    ).toBeTruthy();

    // The read's clock runs on while the deadline is ahead, so the clause leaves by itself.
    act(() => jest.advanceTimersByTime(HOUR));
    expect(
      await within(await card()).findByText('Nobody pays until Kazimierz Padel confirms'),
    ).toBeTruthy();
    expect(screen.queryByText(/answers by/)).toBeNull();
  });

  it('is new until its details are opened, and stays opened', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    await launchSignedIn();

    expect(within(await card()).getByText(HOME.new)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    await screen.findByText('Padel · booked');
    act(() => router.back());

    await waitFor(() => expect(screen).toHavePathname('/'));
    await waitFor(() =>
      expect(within(screen.getByTestId(`home-game-${BOOKING}`)).queryByText(HOME.new)).toBeNull(),
    );
  });

  it('is not new once its hour has come', async () => {
    stubHomeGames(transport, [homeGame({ status: 'NEEDS_RESULT' })]);
    await launchSignedIn();

    expect(within(await card()).queryByText(HOME.new)).toBeNull();
  });

  it('carries the bubble while the game’s chat is open — and the bubble is not a door', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    await card();
    expect(await screen.findByTestId('home-game-chat')).toBeTruthy();
    expect(screen.getByLabelText(/Chat open\.$/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });

  it('has no bubble with no room', async () => {
    stubHomeGames(transport, [homeGame()]);
    await launchSignedIn();

    await card();
    expect(screen.queryByTestId('home-game-chat')).toBeNull();
  });

  it('keeps the bubble past the result while the room lives (§14.3: it closes as today)', async () => {
    stubHomeGames(transport, [homeGame({ status: 'COUNTED' })]);
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    await card();
    expect(await screen.findByTestId('home-game-chat')).toBeTruthy();
  });

  it('has no bubble on a called-off game, whatever the list still holds', async () => {
    stubHomeGames(transport, [homeGame({ status: 'CALLED_OFF' })]);
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    await card();
    expect(screen.queryByTestId('home-game-chat')).toBeNull();
  });

  /**
   * **Home is booked games only** (#576): a game on `GET /games` that no booking stands for — the
   * old loop's — is not drawn, and Home does not even ask for that list.
   */
  it('draws booked games only, and never reads the old games list', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubGames(
      transport,
      [bookedGameOnTheList(), bookedGameOnTheList({ game_id: OLD_LOOP_GAME })],
      HOME_READ_AT,
    );
    await launchSignedIn();

    await card();
    expect(screen.getByText('Your games · 1')).toBeTruthy();
    expect(screen.getAllByRole('button', { name: HOME.openGame })).toHaveLength(1);
    expect(transport.requestsTo('GET', GAMES_PATH)).toHaveLength(0);
  });

  it('says what Home is, with no booked games, and pages through none', async () => {
    stubHomeGames(transport, []);
    await launchSignedIn();

    expect(await screen.findByText('Your games · 0')).toBeTruthy();
    expect(screen.getByText(HOME_TAB_LINE)).toBeTruthy();
    expect(screen.queryByTestId(`home-game-${BOOKING}`)).toBeNull();
  });

  it('pages through two booked games, one card at a time, with the dots', async () => {
    stubHomeGames(transport, [
      homeGame(),
      homeGame({ booking_id: SECOND_BOOKING, game_id: null, status: 'WAITING_FOR_THE_CLUB' }),
    ]);
    await launchSignedIn();

    await card();
    expect(screen.getByText('Your games · 2')).toBeTruthy();
    expect(screen.getByTestId(`home-game-${SECOND_BOOKING}`)).toBeTruthy();
    // The dots are hidden from the reader on purpose (7.18) — the count is the heading's — so they
    // are read off the drawn row: one per card, the first one current.
    expect(screen.UNSAFE_getByType(PagerDots).props).toMatchObject({ count: 2, current: 0 });
  });

  it('leaves an ended game a day after its hour', async () => {
    stubHomeGames(transport, [homeGame({ status: 'COUNTED', starts_at: '2026-09-29T14:00:00Z' })]);
    await launchSignedIn();

    await screen.findByText('Your games · 0');
    expect(screen.queryByTestId(`home-game-${BOOKING}`)).toBeNull();
  });

  it('counts the booked games that need you on Home’s column — Home’s own count', async () => {
    stubHomeGames(transport, [homeGame({ status: 'NEEDS_RESULT', needs_you: true })], {
      needing_you: 2,
    });
    await launchSignedIn();

    expect(await screen.findByLabelText('Home, 2 games waiting on you')).toBeTruthy();
  });

  it('counts nothing on the old games list, though a game there has a seat open', async () => {
    stubHomeGames(transport, [homeGame({ status: 'NEEDS_RESULT', needs_you: true })], {
      needing_you: 1,
    });
    // On the games list, an open seat was the old loop's *Needs a player* — which its badge counted.
    stubGames(
      transport,
      [
        bookedGameOnTheList({
          game_id: OLD_LOOP_GAME,
          seats: [
            { side: 'A', player_id: GATE_USER.id, name: GATE_USER.name },
            { side: 'A', player_id: PIOTR, name: 'Piotr Sowa' },
            { side: 'B', player_id: INES, name: 'Inés Díaz' },
            { side: 'B', player_id: null, name: null },
          ],
        }),
      ],
      HOME_READ_AT,
    );
    await launchSignedIn();

    expect(await screen.findByLabelText('Home, 1 game waiting on you')).toBeTruthy();
  });

  it('draws no count on Home’s column when nothing needs you', async () => {
    stubHomeGames(transport, [homeGame()], { needing_you: 0 });
    await launchSignedIn();

    await card();
    expect(screen.getByRole('tab', { name: 'Home' })).toBeTruthy();
  });

  it('lists a payment to confirm above the rail, since Home’s count names it', async () => {
    stubPaymentsToConfirm(transport, [
      {
        seat_charge_id: 'f1000000-0000-4000-8000-000000000001',
        refusal: 'AUTHENTICATION_REQUIRED',
        proposal_id: 'f1000000-0000-4000-8000-000000000002',
        pool_id: 'f1000000-0000-4000-8000-000000000003',
        sport: 'PADEL',
        kind: 'COMPETITIVE',
        starts_at: '2026-10-03T14:00:00Z',
        club: { id: 'f1000000-0000-4000-8000-000000000004', name: 'Bonarka Arena' },
        share_grosze: 3200,
        book_by: '2026-10-02T11:00:00Z',
      },
    ]);
    stubHomeGames(transport, [], { needing_you: 1 });
    await launchSignedIn();

    expect(
      await screen.findByRole('header', {
        name: `${FILL_COPY.toConfirm.title}, ${FILL_COPY.toConfirm.line}`,
      }),
    ).toBeTruthy();
  });

  it('says a read that failed, rather than drawing no games', async () => {
    // A refusal the player can retry, and Query does not retry by itself.
    transport.on('GET', HOME_PATH, () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();

    expect(await screen.findByRole('alert')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The details
// ---------------------------------------------------------------------------

/** Land on Home with the game, and open it. */
async function openDetails(
  details: Wire['BookingDetailsResponse'] = bookingDetails(),
  rooms: readonly Wire['ConversationRowSchema'][] = [bookedRoomRow()],
) {
  stubHomeGames(transport, [homeGame({ status: details.status })]);
  stubBooking(transport, details);
  stubConversations(transport, rooms);
  await launchSignedIn();

  fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
  await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
}

describe('a booked game’s details (A4.1)', () => {
  it('draws the top bar: the others named whole, Padel · booked, and Chat', async () => {
    await openDetails();

    expect(await screen.findByText('Piotr Sowa, Inés Díaz, Bartek Lis')).toBeTruthy();
    expect(screen.getByText('Padel · booked')).toBeTruthy();
    expect(screen.getByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
  });

  it('draws the game card: the status, the tiles with paid, the vs line and the court', async () => {
    await openDetails();

    expect(await screen.findByRole('header', { name: HOME.status.BOOKED })).toBeTruthy();
    expect(screen.getByLabelText('You, level 2,71, paid')).toBeTruthy();
    expect(screen.getByLabelText('Piotr Sowa, level 2,95, paid')).toBeTruthy();
    expect(screen.getByTestId(`game-tile-${INES}`)).toBeTruthy();
    expect(screen.getByTestId(`game-tile-${BARTEK}`)).toBeTruthy();
    // Decorative to a listener — every tile names its person.
    expect(screen.getByText('You + Piotr vs Inés + Bartek', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByLabelText('Where, Bonarka Arena, Court 2 · 3,1 km')).toBeTruthy();
    expect(screen.getByLabelText('Day, Saturday, 3 Oct')).toBeTruthy();
    expect(screen.getByLabelText('Time, 16:00, until 17:00')).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Paid, 28 zł, your share · to the club · free to leave until Fri 16:00',
      ),
    ).toBeTruthy();
  });

  it('says the seat open and when it must fill, the leaver’s seat empty (§14.1)', async () => {
    await openDetails(
      bookingDetails({
        status: 'SEAT_OPEN',
        open_seats: 1,
        shows_forecast: false,
        sides: { ...bookedSides(), theirs: bookedSides().theirs.slice(0, 1) },
      }),
    );

    expect(await screen.findByRole('header', { name: HOME.status.SEAT_OPEN })).toBeTruthy();
    expect(screen.getByTestId('game-tile-empty')).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Paid, 28 zł, 1 seat open · fills by Fri 16:00 or the game is off and everyone is refunded',
      ),
    ).toBeTruthy();
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
  });

  it('says why a game was called off, and what came back', async () => {
    await openDetails(
      bookingDetails({
        status: 'CALLED_OFF',
        called_off_reason: 'SHORT_AT_THE_CUT_OFF',
        money: bookedMoney({ free_to_leave_until: null, refunded_grosze: 2800 }),
        shows_forecast: false,
        leaving: null,
      }),
      [],
    );

    expect(await screen.findByRole('header', { name: HOME.status.CALLED_OFF })).toBeTruthy();
    expect(
      screen.getByLabelText('Refunded, 28 zł, A seat was still empty at the cut-off'),
    ).toBeTruthy();
  });

  it('draws the Game’s own balance forecast while the booking shows one', async () => {
    stubGames(transport, [bookedGameOnTheList()], HOME_READ_AT);
    stubPairing(transport, BOOKED_GAME, {
      read_at: HOME_READ_AT,
      forecast: { pct: 90, sigma_group: 0.4, provisional: false, assumption: null },
      split: { your_side: 2.83, their_side: 2.88, gap: -0.05 },
      at_stake: { win_delta: 0.1, loss_delta: -0.06 },
      seats: [],
    });
    await openDetails();

    expect(await screen.findByRole('header', { name: BALANCE_FORECAST })).toBeTruthy();
  });

  it('draws no forecast once the booking says not to', async () => {
    stubGames(transport, [bookedGameOnTheList()], HOME_READ_AT);
    await openDetails(bookingDetails({ shows_forecast: false }));

    await screen.findByText('Padel · booked');
    expect(screen.queryByRole('header', { name: BALANCE_FORECAST })).toBeNull();
  });

  it('shows the QR and the short code at the desk on the game’s day', async () => {
    await openDetails(
      bookingDetails({
        check_in: {
          short_code: 'K7M2QX',
          qr_payload: `RAKETA-CHECK-IN:1:${BOOKING}:${GATE_USER.id}:K7M2QX`,
        },
      }),
    );

    expect(await screen.findByRole('header', { name: DETAILS.showAtTheDesk })).toBeTruthy();
    expect(screen.getByTestId('check-in-qr')).toBeTruthy();
    expect(screen.getByText('K7M2QX')).toBeTruthy();
    expect(screen.getByLabelText(`${DETAILS.codeSpoken}: K 7 M 2 Q X`)).toBeTruthy();
  });

  it('has nothing to show at the desk on any other day', async () => {
    await openDetails();

    await screen.findByText('Padel · booked');
    expect(screen.queryByText(DETAILS.showAtTheDesk)).toBeNull();
  });

  it('offers today’s result once the hour has come, on today’s game screen', async () => {
    stubGames(transport, [bookedGameOnTheList()], HOME_READ_AT);
    await openDetails(bookingDetails({ status: 'NEEDS_RESULT', needs_you: true }));

    fireEvent.press(await screen.findByRole('button', { name: DETAILS.resultAct['we-played'] }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/result`));
    // Today's score grid, led with — the game screen's own button for it.
    expect(await screen.findByText('Send this score')).toBeTruthy();
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  });

  it('offers no result act before the hour', async () => {
    await openDetails();

    await screen.findByText('Padel · booked');
    expect(screen.queryByRole('button', { name: DETAILS.resultAct['we-played'] })).toBeNull();
    expect(screen.queryByRole('button', { name: DETAILS.resultAct.confirm })).toBeNull();
  });

  it('says so in one sentence for a game that is not the reader’s', async () => {
    stubHomeGames(transport, [homeGame()]);
    transport.on('GET', bookingPath(BOOKING), () => errorResponse(404, 'booking_not_found'));
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));

    expect(await screen.findByText(DETAILS.gone)).toBeTruthy();
  });

  it('says beside the share when the club answers, until that has passed (Q98)', async () => {
    const details = bookingDetails({
      ...waitingForKazimierz,
      leaving: { kind: 'WHILE_WAITING_FOR_THE_CLUB', refund_grosze: 0, card_fee_grosze: 0 },
    });
    await openDetails({ ...details, where: { ...details.where, name: KAZIMIERZ } });

    expect(
      await screen.findByLabelText(
        'Your share, 25 zł, nobody pays until Kazimierz Padel confirms · Kazimierz Padel answers by 11:00',
      ),
    ).toBeTruthy();

    act(() => jest.advanceTimersByTime(HOUR));
    expect(
      await screen.findByLabelText('Your share, 25 zł, nobody pays until Kazimierz Padel confirms'),
    ).toBeTruthy();
    expect(screen.queryByText(/answers by/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The chat
// ---------------------------------------------------------------------------

describe('the chat — reached from the details only (A4.4)', () => {
  it('opens the room without the plan card or a Details button, and back is the details', async () => {
    stubConversation(transport, bookedRoom());
    stubEntries(transport, BOOKED_ROOM);
    await openDetails();

    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(await screen.findByTestId('conversation-stream')).toBeTruthy();
    expect(screen.getByText('Padel · booked')).toBeTruthy();
    expect(screen.queryByText('Details')).toBeNull();
    expect(screen.queryByText(/of 3 set/)).toBeNull();
    // The composer replaces the bar, as in every room.
    expect(screen.queryByLabelText('Home')).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: DETAILS.back }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  });

  it('names no court while the game waits for the club, and has no Chat', async () => {
    await openDetails(
      bookingDetails({
        status: 'WAITING_FOR_THE_CLUB',
        game_id: null,
        court_name: null,
        money: bookedMoney({ paid: false, free_to_leave_until: null }),
        leaving: { kind: 'WHILE_WAITING_FOR_THE_CLUB', refund_grosze: 0, card_fee_grosze: 0 },
      }),
      [bookedRoomRow()],
    );

    await screen.findByText('Padel · waiting for the club');
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
    expect(screen.getByLabelText('Where, Bonarka Arena, 3,1 km')).toBeTruthy();
  });

  it('keeps Chat past the result while the room lives, and has none once it has closed', async () => {
    await openDetails(bookingDetails({ status: 'COUNTED', shows_forecast: false }));

    await screen.findByText('Padel · counted');
    expect(screen.getByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
  });

  it('has no Chat once the room has closed', async () => {
    await openDetails(bookingDetails({ status: 'COUNTED', shows_forecast: false }), []);

    await screen.findByText('Padel · counted');
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });

  it('says why the rooms could not be read, with the retry, rather than that there is no chat', async () => {
    // The rooms refused: the details draw no door, and a way straight into the room says why.
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    transport.on('GET', CONVERSATIONS_PATH, () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
    await screen.findByText('Padel · booked');
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
    act(() => router.push(`/booking/${BOOKING}/chat`));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.queryByText(DETAILS.noRoom)).toBeNull();
  });
});

/**
 * **A booked game's room is found by the booking it is filed under, and by nothing else**
 * ([#577](https://github.com/Raketa02/Raketa/issues/577)) — the wire's `booking_id`, which #575
 * renamed from `challenge_id`. Each room here disagrees with its booking about the game, so a join
 * still keyed by the game finds the wrong answer in both.
 */
describe('the chat — found by its booking', () => {
  it('opens the room filed under the booking from Home’s card and from the details', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    stubConversations(transport, [{ ...bookedRoomRow(), game_id: null }]);
    stubConversation(transport, bookedRoom());
    stubEntries(transport, BOOKED_ROOM);
    await launchSignedIn();

    await card();
    expect(await screen.findByTestId('home-game-chat')).toBeTruthy();
    expect(screen.getByLabelText(/Chat open\.$/)).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));
    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(await screen.findByTestId('conversation-stream')).toBeTruthy();
  });

  it('finds no room filed under another booking, though it names this game', async () => {
    await openDetails(bookingDetails(), [{ ...bookedRoomRow(), booking_id: SECOND_BOOKING }]);
    await screen.findByText('Padel · booked');

    // The list has answered once the chat says it holds no room — then neither door is drawn.
    act(() => router.push(`/booking/${BOOKING}/chat`));
    expect(await screen.findByText(DETAILS.noRoom)).toBeTruthy();
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
    act(() => router.back());
    await card();
    expect(screen.queryByTestId('home-game-chat')).toBeNull();
    expect(screen.queryByLabelText(/Chat open\.$/)).toBeNull();
  });
});
