/**
 * **Home and a booked game, walked the way a player walks them** — the real route tree, the real
 * shell, the real Home tab, and only `fetch` faked ([#556](https://github.com/Raketa02/Raketa/issues/556);
 * the screens A4.1, A4.4, A8; the mechanics §11.4, §14).
 *
 * **A payment to confirm waits in Needs your answer** since #817: a tile per payment, first in the
 * sheet the header's envelope opens, and Home's column still counts it.
 *
 * The acceptance criteria are assertions here: a Home card says its status and its money line, is
 * *new* until opened, carries *Open game* and the chat's bubble — a door straight into the room,
 * whose Back is Home (Q100, #619); the details draw the top bar, the game card with *paid* tiles
 * and the court facts, and the Game's forecast — and nothing to show at the desk (ADR-0195); and
 * the chat opened from the details, without the plan card or a *Details* button, goes back to them.
 *
 * The rules are `domain/home.test.ts`'s and the words `homePresentation.test.ts`'s; what is asserted
 * here is that the screens are wired to both.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Dimensions, RefreshControl, StyleSheet, type TextStyle } from 'react-native';
import { router } from 'expo-router';

import { OPEN_THE_CHAT } from '@/features/conversations/types';
import { BALANCE_FORECAST } from '@/features/games/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { PagerDots, theme } from '@/shared/ui';
import {
  BARTEK,
  BOOKED_GAME,
  BOOKED_ROOM,
  BOOKING,
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
  takenMoney,
  unheldMoney,
} from '@/test-support/home';
import { yesPath } from '@/test-support/groupDeck';
import { envelope, openNeedsYourAnswer, sheetTitle } from '@/test-support/needsYourAnswer';
import {
  CONVERSATIONS_PATH,
  GAMES_PATH,
  GATE_USER,
  HOME_PATH,
  HOME_TAB_LINE,
  PAYMENTS_TO_CONFIRM_PATH,
  bookingPath,
  launchSignedIn,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPairing,
  stubPaymentMethod,
  stubPaymentsToConfirm,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { proposalKeys } from '../hooks/proposalKeys';

import { FILL_COPY } from './fillCopy';
import { HOME_GAME_COPY } from './homeCopy';
import { LEAVE_THE_GAME } from './leaveSheetCopy';
import { PROPOSALS_COPY } from './proposalsCopy';

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
/** A second booking, still waiting for one payment. */
const SECOND_BOOKING = '3f2b8c1e-0000-4000-8000-0000000000b2';
/** A room filed under the second booking. */
const SECOND_ROOM = '3f2b8c1e-0000-4000-8000-0000000000c2';

const HOUR = 60 * 60 * 1000;

/**
 * **Story S-01E's game** (ADR-0196, #676) — Paula's yes completed Marta's game at Kazimierz Padel,
 * and no club confirms a game: booked at once on Court 3, each player's 25 zł held until the club's
 * cut-off.
 */
const bookedAtKazimierz = {
  status: 'BOOKED',
  court_name: 'Court 3',
  money: bookedMoney({ share_grosze: 2500 }),
} as const;

/** **A full game waiting for one payment** (#625): nobody has paid, no Game and no court yet. */
const waitingForAPayment = {
  status: 'WAITING_FOR_A_PAYMENT',
  game_id: null,
  court_name: null,
  indoor: null,
  money: unheldMoney({ share_grosze: 2500 }),
} as const;
const KAZIMIERZ = 'Kazimierz Padel';

/** Home's card at Kazimierz Padel, and the details' WHERE there. */
const AT_KAZIMIERZ = { club: { ...homeGame().club, name: KAZIMIERZ } } as const;
const WHERE_KAZIMIERZ = { where: { ...bookingDetails().where, name: KAZIMIERZ } } as const;

/**
 * **Story S-01B's fallen-back game** (#624, Q106) — Oscar left Friday's game at Kazimierz Padel while
 * one payment was awaited. Marta and the two others still In, one seat open, nobody paid, no Game
 * and no court; full again, it books at once.
 */
const fillingAgainAtKazimierz = {
  status: 'SEAT_OPEN',
  game_id: null,
  court_name: null,
  indoor: null,
  open_seats: 1,
  filling_again: true,
  sides: { ...bookedSides(), theirs: bookedSides().theirs.slice(0, 1) },
  money: unheldMoney({ share_grosze: 2500 }),
} as const;

/** Home is read again — what a notice arriving, or a foreground, does. */
function readHomeAgain() {
  act(() => void queryClient.invalidateQueries({ queryKey: proposalKeys.home() }));
}

/** **A cut-off an hour after the read** — Thursday 1 October, 11:00 in Warsaw: held until then. */
const ELEVEN = '2026-10-01T09:00:00Z';
const CUT_OFF_AT_ELEVEN = bookedMoney({ free_to_leave_until: ELEVEN, taken_at: ELEVEN });

/**
 * **A game filled far ahead** (Q113; the mechanics §12.2): the reader's card was only checked, and
 * the share is held at its Holding time — Thursday 1 October, 11:00 in Warsaw, an hour after the
 * read — then taken at the cut-off on Friday at 16:00.
 */
const CHECKED_UNTIL_ELEVEN = bookedMoney({ share_state: 'CHECKED', held_from: ELEVEN });

// ---------------------------------------------------------------------------
// Home
// ---------------------------------------------------------------------------

describe('Home — a booked game’s card (A8)', () => {
  it('lets the player remove a called-off game from Home, and offers that on no other card', async () => {
    stubHomeGames(transport, [
      homeGame({
        status: 'CALLED_OFF',
        called_off_reason: 'CANCELLED_BY_THE_CLUB',
        money: unheldMoney(),
      }),
    ]);
    await launchSignedIn();
    await card();

    fireEvent.press(screen.getByRole('button', { name: 'Remove from Home' }));

    await waitFor(() =>
      expect(screen.queryByText('Bonarka Arena cancelled it · Nothing was taken')).toBeNull(),
    );
  });

  it('offers no removal on a game still on', async () => {
    stubHomeGames(transport, [homeGame()]);
    await launchSignedIn();
    await card();

    expect(screen.queryByRole('button', { name: 'Remove from Home' })).toBeNull();
  });

  it('re-reads Home when the player pulls it down', async () => {
    stubHomeGames(transport, [homeGame()]);
    await launchSignedIn();
    await card();
    const homeReads = () => transport.requestsTo('GET', HOME_PATH).length;
    const before = homeReads();

    fireEvent(screen.UNSAFE_getByType(RefreshControl), 'refresh');

    await waitFor(() => expect(homeReads()).toBeGreaterThan(before));
  });

  it('draws the status, the court, the day and the money line, with Open game', async () => {
    stubHomeGames(transport, [homeGame()]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status.BOOKED)).toBeTruthy();
    expect(within(drawn).getByText('Bonarka Arena')).toBeTruthy();
    expect(within(drawn).getByText('Saturday')).toBeTruthy();
    expect(within(drawn).getByText('28 zł · free to leave until Fri 16:00')).toBeTruthy();
    expect(screen.getByRole('button', { name: HOME.openGame })).toBeTruthy();
    expect(screen.getByText('Your games · 1')).toBeTruthy();
  });

  it('draws the booked court with its kind — Court 2 · indoor (#677)', async () => {
    stubHomeGames(transport, [homeGame({ court_name: 'Court 2', indoor: true })]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText('Court 2 · indoor')).toBeTruthy();
  });

  /** Q113: held at the fill and taken at the cut-off — leaving before it takes nothing. */
  it('says the share is free to leave until the cut-off, and Paid from it by itself', async () => {
    stubHomeGames(transport, [homeGame({ money: CUT_OFF_AT_ELEVEN })]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText('28 zł · free to leave until Thu 11:00')).toBeTruthy();
    expect(screen.getByLabelText(/28 zł, free to leave until Thu 11:00\./)).toBeTruthy();

    // The read's clock runs on while the cut-off is ahead, so the line turns at it by itself.
    act(() => jest.advanceTimersByTime(HOUR));
    expect(await within(await card()).findByText('Paid · 28 zł')).toBeTruthy();
    expect(screen.queryByText(/free to leave/)).toBeNull();
  });

  it('says the same while the reader’s card was only checked, the share to be held later', async () => {
    stubHomeGames(transport, [homeGame({ money: CHECKED_UNTIL_ELEVEN })]);
    await launchSignedIn();

    expect(
      await within(await card()).findByText('28 zł · free to leave until Fri 16:00'),
    ).toBeTruthy();
  });

  it('reads Paid once the read says the share was taken', async () => {
    stubHomeGames(transport, [
      homeGame({ money: takenMoney(), sides: bookedSides({ paid: true }) }),
    ]);
    await launchSignedIn();

    expect(await within(await card()).findByText('Paid · 28 zł')).toBeTruthy();
    expect(screen.queryByText(/free to leave|back if you leave/)).toBeNull();
  });

  it.each<[Wire['HomeStatus'], Partial<Wire['HomeGameSchema']>, string | undefined]>([
    [
      'WAITING_FOR_A_PAYMENT',
      { game_id: null, court_name: null, indoor: null, money: unheldMoney() },
      'Waiting for one payment · Nobody pays until it’s in',
    ],
    [
      'SEAT_OPEN',
      { open_seats: 2, sides: { ...bookedSides(), theirs: [] } },
      '2 seats open · fills by Fri 16:00 or the game is off and nothing is taken',
    ],
    [
      'SEAT_OPEN',
      { open_seats: 1, money: takenMoney() },
      '1 seat open · offered to others · the game goes ahead',
    ],
    ['NEEDS_RESULT', { needs_you: true }, undefined],
    ['CONFIRM_THE_RESULT', {}, undefined],
    ['COUNTED', {}, undefined],
    // A full game nobody recorded (#655) — *Never played* and its line are gone.
    ['PLAYED_NO_SCORE', { money: takenMoney() }, undefined],
    [
      'UNCOUNTED',
      { uncounted_reason: 'SEAT_EMPTY', money: takenMoney() },
      'A seat was empty · no Level moved',
    ],
    [
      'CALLED_OFF',
      { called_off_reason: 'SHORT_AT_THE_CUT_OFF', money: unheldMoney() },
      'A seat was still empty at the cut-off · Nothing was taken',
    ],
    [
      'CALLED_OFF',
      { called_off_reason: 'CANCELLED_BY_THE_CLUB', money: unheldMoney() },
      'Bonarka Arena cancelled it · Nothing was taken',
    ],
    [
      'CALLED_OFF',
      {
        called_off_reason: 'CANCELLED_BY_THE_CLUB',
        money: unheldMoney({ paid: true, refunded_grosze: 2800 }),
      },
      'Bonarka Arena cancelled it · Refunded 28 zł',
    ],
    [
      'CALLED_OFF',
      { called_off_reason: 'PAYMENT_NOT_IN_TIME', game_id: null, money: unheldMoney() },
      'A payment didn’t go through in time · Nobody paid',
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

  /** **For fun asks nothing** (#656): its card reads *Played* after the hour — scored or not. */
  it.each<Wire['HomeStatus']>(['NEEDS_RESULT', 'COUNTED'])(
    'draws a For fun game’s %s as Played',
    async (status) => {
      stubHomeGames(transport, [homeGame({ kind: 'FOR_FUN', status, money: takenMoney() })]);
      await launchSignedIn();

      const drawn = await card();
      expect(within(drawn).getByText(HOME.status.PLAYED)).toBeTruthy();
      expect(within(drawn).queryByText(HOME.status[status])).toBeNull();
    },
  );

  it('names no court on a game waiting for one payment, which has no Game yet', async () => {
    stubHomeGames(transport, [homeGame({ ...waitingForAPayment })]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText('Bonarka Arena')).toBeTruthy();
    expect(within(drawn).queryByText(/Court/)).toBeNull();
  });

  /** No club confirms a game (ADR-0196, #676): a full game at Kazimierz Padel is simply booked. */
  it('reads a full game at Kazimierz Padel as booked, its 25 zł held — nothing waits for the club', async () => {
    stubHomeGames(transport, [homeGame({ ...bookedAtKazimierz, ...AT_KAZIMIERZ })]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status.BOOKED)).toBeTruthy();
    expect(within(drawn).getByText(KAZIMIERZ)).toBeTruthy();
    expect(within(drawn).getByText('25 zł · free to leave until Fri 16:00')).toBeTruthy();
    expect(
      screen.getByLabelText(/^Booked, new\. Padel\. Kazimierz Padel, Court 3, indoor\./),
    ).toBeTruthy();
    expect(screen.queryByText(/answers by|confirms|Nobody pays|waiting for the club/i)).toBeNull();
  });

  it('is new until its details are opened, and stays opened', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    await launchSignedIn();

    expect(within(await card()).getByText(HOME.new)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    await screen.findByText('Padel');
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

  /**
   * **The bubble is a door** (Q100; the design system's 6.14): it opens the game's room straight
   * over Home, with no details pushed under it, so Back is Home — and the room is where the
   * details' *Chat* leads, so Home stays the lit column while it is open (`shellTabs`).
   */
  it('opens the chat straight over Home from the bubble, and Back lands on Home (Q100)', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    stubConversations(transport, [bookedRoomRow()]);
    stubConversation(transport, bookedRoom());
    stubEntries(transport, BOOKED_ROOM);
    await launchSignedIn();

    await card();
    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(await screen.findByTestId('conversation-stream')).toBeTruthy();
    expect(screen.getByText('Padel · booked')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: DETAILS.back }));
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await card()).toBeTruthy();
    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();
  });

  it('clears New once the chat is opened from the bubble, as opening the details does', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    stubConversations(transport, [bookedRoomRow()]);
    stubConversation(transport, bookedRoom());
    stubEntries(transport, BOOKED_ROOM);
    await launchSignedIn();

    expect(within(await card()).getByText(HOME.new)).toBeTruthy();
    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    fireEvent.press(await screen.findByRole('button', { name: DETAILS.back }));

    await waitFor(() => expect(screen).toHavePathname('/'));
    await waitFor(() =>
      expect(within(screen.getByTestId(`home-game-${BOOKING}`)).queryByText(HOME.new)).toBeNull(),
    );
  });

  it('is its own button, named as the details’ Chat — the card’s name no longer says it', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    await card();
    expect(await screen.findByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
    expect(
      screen.getByLabelText(/^Booked, new\. Padel\. .* free to leave until Fri 16:00\.$/),
    ).toBeTruthy();
    expect(screen.queryByLabelText(/Chat open/)).toBeNull();
  });

  it('has no bubble with no room', async () => {
    stubHomeGames(transport, [homeGame()]);
    await launchSignedIn();

    await card();
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });

  it('keeps the bubble past the result while the room lives (§14.3: it closes as today)', async () => {
    stubHomeGames(transport, [homeGame({ status: 'COUNTED' })]);
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    await card();
    expect(await screen.findByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
  });

  it.each<[string, Partial<Wire['HomeGameSchema']>]>([
    ['waiting for one payment', waitingForAPayment],
    ['called off', { status: 'CALLED_OFF', called_off_reason: 'SHORT_AT_THE_CUT_OFF' }],
    // The chat opens when the game is booked (Q106), as on Waiting for one payment.
    ['gone back to filling', fillingAgainAtKazimierz],
  ])('has no bubble on a game %s, whatever the list still holds', async (_, extra) => {
    stubHomeGames(transport, [homeGame(), homeGame({ booking_id: SECOND_BOOKING, ...extra })]);
    stubConversations(transport, [
      bookedRoomRow(),
      { ...bookedRoomRow(), conversation_id: SECOND_ROOM, booking_id: SECOND_BOOKING },
    ]);
    await launchSignedIn();

    // The booked card's door says the list has answered; the other card still draws none.
    expect(await screen.findByTestId(`home-game-chat-${BOOKING}`)).toBeTruthy();
    expect(screen.queryByTestId(`home-game-chat-${SECOND_BOOKING}`)).toBeNull();
    expect(screen.getAllByRole('button', { name: OPEN_THE_CHAT })).toHaveLength(1);
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
      homeGame({ booking_id: SECOND_BOOKING, ...waitingForAPayment }),
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
            { side: 'A', player_id: GATE_USER.id, nickname: GATE_USER.nickname },
            { side: 'A', player_id: PIOTR, nickname: 'piotr.s' },
            { side: 'B', player_id: INES, nickname: 'ines.d' },
            { side: 'B', player_id: null, nickname: null },
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

  it('says a read that failed, rather than drawing no games', async () => {
    // A refusal the player can retry, and Query does not retry by itself.
    transport.on('GET', HOME_PATH, () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();

    expect(await screen.findByRole('alert')).toBeTruthy();
  });
});

/**
 * **TO CONFIRM waits in Needs your answer** ([#817](https://github.com/Raketa02/Raketa/issues/817);
 * ADR-0205 §1, §3): a tile per refused share, first in the sheet the header's envelope opens, where
 * Home's one card of rows used to stand above the rail. Every read is at `HOME_READ_AT`, 10:00 in
 * Warsaw; Bonarka Arena's Saturday 15:00, 32 zł, the time to pay ending at 14:40.
 */
describe('TO CONFIRM in Needs your answer (#817)', () => {
  const CHARGE = 'f1000000-0000-4000-8000-000000000001';
  const SECOND_CHARGE = 'f1000000-0000-4000-8000-000000000011';
  const BY_14_40 = '2026-10-01T12:40:00Z';

  function payment(
    extra: Partial<
      Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema']
    > = {},
  ): Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'] {
    return {
      seat_charge_id: CHARGE,
      refusal: 'AUTHENTICATION_REQUIRED',
      proposal_id: 'f1000000-0000-4000-8000-000000000002',
      pool_id: 'f1000000-0000-4000-8000-000000000003',
      sport: 'PADEL',
      kind: 'COMPETITIVE',
      starts_at: '2026-10-03T13:00:00Z',
      club: { id: 'f1000000-0000-4000-8000-000000000004', name: 'Bonarka Arena' },
      share_grosze: 3200,
      book_by: '2026-10-02T11:00:00Z',
      confirm_by: BY_14_40,
      time_to: 'PAY',
      ...extra,
    };
  }

  /**
   * Signed in at Thursday's 10:00 — the time to pay is read against the phone's clock, which the
   * harness fakes from the launch on — and the sheet opened on the envelope.
   */
  async function inTheSheet() {
    await launchSignedIn();
    jest.setSystemTime(Date.parse(HOME_READ_AT));
    await openNeedsYourAnswer();
  }

  const tile = (charge = CHARGE) => within(screen.getByTestId(`to-confirm-${charge}`));
  const colourOf = (node: { props: { style: unknown } }) =>
    StyleSheet.flatten(node.props.style as TextStyle).color;

  /** The width the rail hands a tile — read off the tile, which holds its words. */
  function tileWidth(charge: string): unknown {
    let node = screen.getByTestId(`to-confirm-${charge}`).parent;
    while (node !== null && StyleSheet.flatten(node.props.style)?.width === undefined) {
      node = node.parent;
    }
    return node === null ? undefined : StyleSheet.flatten(node.props.style)?.width;
  }

  it('waits behind the envelope, and is no longer on Home — Home’s column still counts it', async () => {
    stubPaymentsToConfirm(transport, [payment()]);
    stubHomeGames(transport, [], { needing_you: 1 });
    await launchSignedIn();

    // Home's tab badge counts what it counted: the payments to confirm among what needs you.
    expect(await screen.findByLabelText('Home, 1 game waiting on you')).toBeTruthy();
    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(screen.queryByTestId('to-confirm')).toBeNull();
    expect(screen.queryByText(/^To confirm/)).toBeNull();

    await openNeedsYourAnswer();

    expect(screen.getByRole('header', { name: 'To confirm · 1' })).toBeTruthy();
    expect(screen.getByTestId(`to-confirm-${CHARGE}`)).toBeTruthy();
  });

  it('draws the game, the club and the share, the time to pay in amber, and Confirm', async () => {
    stubPaymentsToConfirm(transport, [payment()]);
    stubHomeGames(transport, [], { needing_you: 1 });
    await inTheSheet();

    expect(tile().getByText('Padel · Saturday 15:00').props.numberOfLines).toBe(2);
    expect(tile().getByText('Bonarka Arena · 32 zł')).toBeTruthy();
    const time = tile().getByText('Confirm your payment by 14:40');
    expect(colourOf(time)).toBe(theme.color.amber);
    expect(screen.queryByText(FILL_COPY.toConfirm.nothingPaidNow)).toBeNull();
    expect(
      screen.getByRole('button', {
        name: 'Confirm your payment for Padel · Saturday 15:00 at Bonarka Arena, 32 zł',
      }),
    ).toBeTruthy();
    expect(screen.getByText(FILL_COPY.toConfirm.action.PAY)).toBeTruthy();
  });

  it('says Fix your card by 14:40 and that nothing is paid now, with Fix — before the cut-off', async () => {
    stubPaymentsToConfirm(transport, [payment({ time_to: 'FIX_THE_CARD' })]);
    stubHomeGames(transport, [], { needing_you: 1 });
    await inTheSheet();

    expect(colourOf(tile().getByText('Fix your card by 14:40'))).toBe(theme.color.amber);
    expect(tile().getByText(FILL_COPY.toConfirm.nothingPaidNow)).toBeTruthy();
    expect(
      screen.getByRole('button', {
        name: 'Fix your card for Padel · Saturday 15:00 at Bonarka Arena, 32 zł',
      }),
    ).toBeTruthy();
    expect(screen.queryByText(/Confirm your payment/)).toBeNull();
  });

  /** As the row did: the seat is open to others then, and still theirs to take back while free. */
  it('takes the time off a tile at its deadline, and keeps the tile', async () => {
    stubPaymentsToConfirm(transport, [payment()]);
    stubHomeGames(transport, [], { needing_you: 1 });
    await inTheSheet();
    expect(tile().getByText('Confirm your payment by 14:40')).toBeTruthy();

    act(() => jest.advanceTimersByTime(4 * HOUR + 41 * 60 * 1000));

    expect(await tile().findByText(FILL_COPY.toConfirm.open)).toBeTruthy();
    expect(screen.queryByText('Confirm your payment by 14:40')).toBeNull();
    expect(screen.getByRole('button', { name: /^Confirm your payment for Padel/ })).toBeTruthy();
  });

  it('lays two payments on the peeking rail, a tile each, each button at its tile’s foot', async () => {
    stubPaymentsToConfirm(transport, [
      payment(),
      payment({ seat_charge_id: SECOND_CHARGE, time_to: 'FIX_THE_CARD' }),
    ]);
    stubHomeGames(transport, [], { needing_you: 2 });
    await launchSignedIn();
    await openNeedsYourAnswer();

    expect(screen.getByRole('header', { name: 'To confirm · 2' })).toBeTruthy();
    const content = Dimensions.get('window').width - 2 * theme.size.gutter;
    expect(tileWidth(CHARGE)).toBeCloseTo(content * theme.size.railCardRatio);
    expect(tileWidth(SECOND_CHARGE)).toBeCloseTo(content * theme.size.railCardRatio);
    expect(
      screen.getAllByRole('button', { name: /^(Confirm your payment|Fix your card) for/ }),
    ).toHaveLength(2);
  });

  /** ADR-0205 §3: a failed read counts nothing, and Home's usual re-reads retry. */
  it('draws no envelope for a To confirm read that failed', async () => {
    transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () => errorResponse(429, 'rate_limited'));
    stubHomeGames(transport, [], { needing_you: 1 });
    await launchSignedIn();

    await waitFor(() =>
      expect(transport.requestsTo('GET', PAYMENTS_TO_CONFIRM_PATH).length).toBeGreaterThan(0),
    );
    await screen.findByText('Your games · 0');
    expect(envelope()).toBeNull();
    expect(screen.queryByTestId('to-confirm')).toBeNull();
  });

  /** Q24: the confirmation is a sheet opened from the sheet — over it, and back to it on close. */
  it('opens the confirmation over the sheet, and closing it hands back to the sheet', async () => {
    stubPaymentsToConfirm(transport, [payment()]);
    stubHomeGames(transport, [], { needing_you: 1 });
    await launchSignedIn();
    await openNeedsYourAnswer();

    fireEvent.press(screen.getByRole('button', { name: /^Confirm your payment for Padel/ }));

    const close = await screen.findByRole('button', { name: FILL_COPY.confirm.close });
    fireEvent.press(close);

    await waitFor(() =>
      expect(screen.queryByRole('button', { name: FILL_COPY.confirm.close })).toBeNull(),
    );
    expect(sheetTitle()).not.toBeNull();
    expect(screen.getByTestId(`to-confirm-${CHARGE}`)).toBeTruthy();
  });

  /** You › Payments keeps its card of rows (#555), unchanged. */
  it('is still You › Payments’ card of rows', async () => {
    stubPaymentMethod(transport, { brand: 'visa', last_four: '4312', wallet: null });
    stubPaymentsToConfirm(transport, [payment()]);
    stubHomeGames(transport, [], { needing_you: 1 });
    await launchSignedIn();

    act(() => router.push('/you/payments'));

    expect(await screen.findByRole('header', { name: FILL_COPY.toConfirm.title })).toBeTruthy();
    expect(screen.getByTestId(`to-confirm-${CHARGE}`)).toBeTruthy();
    expect(screen.queryByRole('header', { name: 'To confirm · 1' })).toBeNull();
  });
});

/**
 * **A full game that falls back stays on Home** (#629; the mechanics Q106; story S-01B's
 * F-HOME-10.1, F-REQUEST-31.1): Oscar left Friday's 19:00 at Kazimierz Padel while one payment was
 * awaited, and the game stays on Marta's Home as *Seat open* rather than vanishing.
 */
describe('Home — a full game gone back to filling (Q106)', () => {
  it('stays as Seat open, booked when it is full, nobody paid', async () => {
    stubHomeGames(transport, [homeGame({ ...fillingAgainAtKazimierz, ...AT_KAZIMIERZ })]);
    await launchSignedIn();

    const drawn = await card();
    expect(within(drawn).getByText(HOME.status.SEAT_OPEN)).toBeTruthy();
    expect(
      within(drawn).getByText('1 seat open · books when it’s full · nobody paid'),
    ).toBeTruthy();
    // No court until it is booked, and not *new*: it is not full any more.
    expect(within(drawn).queryByText(/Court/)).toBeNull();
    expect(within(drawn).queryByText(HOME.new)).toBeNull();
    expect(
      screen.getByLabelText(/^Seat open\. Padel\. Kazimierz Padel\. .*nobody paid\.$/),
    ).toBeTruthy();
  });

  /**
   * **The count is the read's** (`needing_you`), which leaves the game out (#624): the phone counts
   * nothing of its own — no card on the rail adds to the column, this one included.
   */
  it('is not counted on Home’s column — it asks nothing of you', async () => {
    stubHomeGames(transport, [homeGame({ ...fillingAgainAtKazimierz, ...AT_KAZIMIERZ })], {
      needing_you: 0,
    });
    await launchSignedIn();

    await card();
    expect(screen.getByRole('tab', { name: 'Home' })).toBeTruthy();
    expect(screen.queryByLabelText(/waiting on you/)).toBeNull();
  });

  it.each<[string, Partial<Wire['HomeGameSchema']>, string, string]>([
    [
      'Booked once it is full again',
      { ...bookedAtKazimierz },
      HOME.status.BOOKED,
      '25 zł · free to leave until Fri 16:00',
    ],
    [
      'Called off once its last moment to book passes first',
      {
        ...fillingAgainAtKazimierz,
        status: 'CALLED_OFF',
        called_off_reason: 'BOOK_BY_PASSED',
        open_seats: 0,
      },
      HOME.status.CALLED_OFF,
      'A seat was open past its last moment to book · Nobody paid',
    ],
    [
      'Called off once its court goes to another game',
      {
        ...fillingAgainAtKazimierz,
        status: 'CALLED_OFF',
        called_off_reason: 'COURT_HOUR_LOST',
        open_seats: 0,
      },
      HOME.status.CALLED_OFF,
      'Its court went to another game before it filled again · Nobody paid',
    ],
  ])('turns into %s, as the read says', async (_, after, status, line) => {
    stubHomeGames(transport, [homeGame({ ...fillingAgainAtKazimierz, ...AT_KAZIMIERZ })]);
    await launchSignedIn();
    expect(within(await card()).getByText(HOME.status.SEAT_OPEN)).toBeTruthy();

    stubHomeGames(transport, [homeGame({ ...after, ...AT_KAZIMIERZ })]);
    readHomeAgain();

    expect(await within(await card()).findByText(status)).toBeTruthy();
    expect(within(await card()).getByText(line)).toBeTruthy();
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

    expect(await screen.findByText('piotr.s, ines.d, bartek.l')).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.getByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
  });

  it('draws the game card: the status, the tiles with paid, the vs line and the court', async () => {
    await openDetails(bookingDetails({ money: takenMoney(), sides: bookedSides({ paid: true }) }));

    expect(await screen.findByRole('header', { name: HOME.status.BOOKED })).toBeTruthy();
    expect(screen.getByLabelText('You, level 2,71, paid')).toBeTruthy();
    expect(screen.getByLabelText('piotr.s, level 2,95, paid')).toBeTruthy();
    expect(screen.getByTestId(`game-tile-${INES}`)).toBeTruthy();
    expect(screen.getByTestId(`game-tile-${BARTEK}`)).toBeTruthy();
    // Decorative to a listener — every tile names its person.
    expect(screen.getByText('You + piotr vs ines + bartek', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByLabelText('Where, Bonarka Arena, Court 2 · indoor · 3,1 km')).toBeTruthy();
    expect(screen.getByLabelText('Day, Saturday, 3 Oct')).toBeTruthy();
    expect(screen.getByLabelText('Time, 16:00, until 17:00')).toBeTruthy();
    expect(screen.getByLabelText('Paid, 28 zł, Paid')).toBeTruthy();
  });

  /** #753 (Q68, applying since Q128): a booked game's tiles mark the reader's own friends. */
  it('tags the reader’s own friends FRIEND on the tiles, and nobody else', async () => {
    const sides = bookedSides({ paid: true });
    await openDetails(
      bookingDetails({
        money: takenMoney(),
        sides: {
          ...sides,
          theirs: sides.theirs.map((seat) =>
            seat.player_id === INES ? { ...seat, friend: true } : seat,
          ),
        },
      }),
    );

    expect(await screen.findByLabelText('ines.d, level 3,40, paid, friend')).toBeTruthy();
    expect(within(screen.getByTestId(`game-tile-${INES}`)).getByText('FRIEND')).toBeTruthy();
    expect(screen.getAllByText('FRIEND')).toHaveLength(1);
    expect(screen.getByLabelText('piotr.s, level 2,95, paid')).toBeTruthy();
  });

  /** Q113: the money row says when the share is held and when it is taken. */
  it('says the share is held on the card, when it is taken, and free to leave until then', async () => {
    await openDetails();

    expect(
      await screen.findByLabelText(
        'Your share, 28 zł, Held on your card · taken Fri 16:00 · free to leave until then',
      ),
    ).toBeTruthy();
    // Held is not paid: no tile says so before the cut-off.
    expect(screen.getByLabelText('You, level 2,71')).toBeTruthy();
    expect(screen.queryByText(/back if you leave|card fee/)).toBeNull();
  });

  it('says when a checked share is held, and turns to held on the card at that time by itself', async () => {
    await openDetails(bookingDetails({ money: CHECKED_UNTIL_ELEVEN }));

    expect(
      await screen.findByLabelText('Your share, 28 zł, Held from Thu 11:00 · taken Fri 16:00'),
    ).toBeTruthy();

    act(() => jest.advanceTimersByTime(HOUR));
    expect(
      await screen.findByLabelText(
        'Your share, 28 zł, Held on your card · taken Fri 16:00 · free to leave until then',
      ),
    ).toBeTruthy();
  });

  it('turns to Paid at the cut-off by itself', async () => {
    await openDetails(bookingDetails({ money: CUT_OFF_AT_ELEVEN }));

    expect(
      await screen.findByLabelText(
        'Your share, 28 zł, Held on your card · taken Thu 11:00 · free to leave until then',
      ),
    ).toBeTruthy();

    act(() => jest.advanceTimersByTime(HOUR));
    expect(await screen.findByLabelText('Paid, 28 zł, Paid')).toBeTruthy();
    expect(screen.queryByText(/free to leave/)).toBeNull();
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
        'Your share, 28 zł, 1 seat open · fills by Fri 16:00 or the game is off and nothing is taken',
      ),
    ).toBeTruthy();
    expect(screen.queryByText(BALANCE_FORECAST)).toBeNull();
  });

  it('says why a game was called off at its cut-off, and that nothing was taken', async () => {
    await openDetails(
      bookingDetails({
        status: 'CALLED_OFF',
        called_off_reason: 'SHORT_AT_THE_CUT_OFF',
        money: unheldMoney(),
        shows_forecast: false,
        leaving: null,
      }),
      [],
    );

    expect(await screen.findByRole('header', { name: HOME.status.CALLED_OFF })).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Your share, 28 zł, A seat was still empty at the cut-off · nothing was taken',
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/Refunded/)).toBeNull();
  });

  it('says what came back from a game its club cancelled after the cut-off', async () => {
    await openDetails(
      bookingDetails({
        status: 'CALLED_OFF',
        called_off_reason: 'CANCELLED_BY_THE_CLUB',
        money: unheldMoney({ paid: true, refunded_grosze: 2800 }),
        shows_forecast: false,
        leaving: null,
      }),
      [],
    );

    expect(
      await screen.findByLabelText('Refunded, 28 zł, Bonarka Arena cancelled it'),
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

    await screen.findByText('Padel');
    expect(screen.queryByRole('header', { name: BALANCE_FORECAST })).toBeNull();
  });

  it('has nothing to show at the desk on the game’s day — they walk straight to the court', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails({ read_at: '2026-10-03T08:00:00Z' }));
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    const open = await screen.findByRole('button', { name: HOME.openGame });
    expect(screen.queryByText(/desk/i)).toBeNull();
    fireEvent.press(open);

    await screen.findByText('Padel');
    expect(screen.queryByText(/desk/i)).toBeNull();
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

  /**
   * **A full game nobody recorded reads Played · no score** (#655, #656) — on the details' tag and
   * its second line, with no door to a result nobody is asked for.
   */
  it('says Played · no score on a full game nobody recorded, and asks for nothing', async () => {
    await openDetails(bookingDetails({ status: 'PLAYED_NO_SCORE', money: takenMoney() }));

    expect(await screen.findByRole('header', { name: 'Played · no score' })).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.queryByText(/Never played|never played/)).toBeNull();
    expect(screen.queryByRole('button', { name: DETAILS.resultAct['we-played'] })).toBeNull();
  });

  /**
   * **For fun asks nothing** (#656): after its hour a For fun game reads *Played*, not *Needs result*,
   * and its door adds a score if anybody wants to — onto the result screen, which asks nobody.
   */
  it('reads a For fun game Played after its hour, with a score to add if you like', async () => {
    stubGames(transport, [bookedGameOnTheList({ kind: 'FRIENDLY' })], HOME_READ_AT);
    await openDetails(bookingDetails({ kind: 'FOR_FUN', status: 'NEEDS_RESULT', needs_you: true }));

    expect(await screen.findByRole('header', { name: 'Played' })).toBeTruthy();
    expect(screen.getByText('Padel · For fun')).toBeTruthy();
    expect(screen.queryByText(/Needs result|needs result/)).toBeNull();
    expect(screen.queryByRole('button', { name: DETAILS.resultAct['we-played'] })).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: DETAILS.resultAct['add-score'] }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/result`));
    expect(await screen.findByText('Send this score')).toBeTruthy();
    expect(screen.getByText('Played')).toBeTruthy();
    expect(screen.queryByText('How did it go?')).toBeNull();
  });

  it('offers no result act before the hour', async () => {
    await openDetails();

    await screen.findByText('Padel');
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

  /** No club confirms a game (ADR-0196, #676): Marta's game at Kazimierz Padel is booked in full. */
  it('reads a full game at Kazimierz Padel as booked in detail, its 25 zł held on the card', async () => {
    await openDetails(bookingDetails({ ...bookedAtKazimierz, ...WHERE_KAZIMIERZ }));

    expect(await screen.findByRole('header', { name: HOME.status.BOOKED })).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.getByLabelText('Where, Kazimierz Padel, Court 3 · indoor · 3,1 km')).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Your share, 25 zł, Held on your card · taken Fri 16:00 · free to leave until then',
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/answers by|confirms|Nobody pays|waiting for the club/i)).toBeNull();
  });
});

/**
 * **A full game gone back to filling, in detail** (#629; Q106): *Seat open* with the card's line
 * under the share, and the way out a game still filling has — *Withdraw*, free and never on the
 * record — where a booked game has *Leave the game*.
 */
describe('a full game gone back to filling, in detail (Q106)', () => {
  const filling = (extra: Partial<Wire['BookingDetailsResponse']> = {}) =>
    bookingDetails({
      ...fillingAgainAtKazimierz,
      ...WHERE_KAZIMIERZ,
      shows_forecast: false,
      leaving: null,
      ...extra,
    });

  it('says Seat open, the share nobody pays over the card’s line, with no court and no Chat', async () => {
    await openDetails(filling());

    expect(await screen.findByRole('header', { name: HOME.status.SEAT_OPEN })).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.getByTestId('game-tile-empty')).toBeTruthy();
    expect(screen.getByLabelText('Where, Kazimierz Padel, 3,1 km')).toBeTruthy();
    expect(
      screen.getByLabelText('Your share, 25 zł, 1 seat open · books when it’s full · nobody paid'),
    ).toBeTruthy();
    // The chat opens when the game is booked — though the rooms list still holds one.
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });

  it('offers Withdraw in place of Leave the game', async () => {
    await openDetails(filling());

    expect(await screen.findByRole('button', { name: PROPOSALS_COPY.game.withdraw })).toBeTruthy();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });

  it('takes the yes back with Withdraw, and the game leaves Home', async () => {
    transport.on('DELETE', yesPath(BOOKING), () => {
      stubHomeGames(transport, []);
      return noContent();
    });
    await openDetails(filling());

    fireEvent.press(await screen.findByRole('button', { name: PROPOSALS_COPY.game.withdraw }));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('DELETE', yesPath(BOOKING))).toHaveLength(1);
    expect(transport.requestsTo('POST', `${bookingPath(BOOKING)}/departure`)).toHaveLength(0);
    expect(await screen.findByText('Your games · 0')).toBeTruthy();
    expect(screen.queryByTestId(`home-game-${BOOKING}`)).toBeNull();
  });

  it('says why a refused Withdraw was refused, and draws the game as it is now', async () => {
    transport.on('DELETE', yesPath(BOOKING), () => {
      stubBooking(
        transport,
        filling({ status: 'CALLED_OFF', called_off_reason: 'BOOK_BY_PASSED', open_seats: 0 }),
      );
      return errorResponse(409, 'proposal_is_over');
    });
    await openDetails(filling());

    fireEvent.press(await screen.findByRole('button', { name: PROPOSALS_COPY.game.withdraw }));

    expect(await screen.findByRole('header', { name: HOME.status.CALLED_OFF })).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Your share, 25 zł, A seat was open past its last moment to book · nobody paid',
      ),
    ).toBeTruthy();
    expect(screen).toHavePathname(`/booking/${BOOKING}`);
    // Its way out went with it: the read still marks it filling again, and it is over.
    expect(screen.queryByRole('button', { name: PROPOSALS_COPY.game.withdraw })).toBeNull();
  });

  it('offers nothing on a game gone back to filling that was called off', async () => {
    await openDetails(
      filling({ status: 'CALLED_OFF', called_off_reason: 'COURT_HOUR_LOST', open_seats: 0 }),
    );

    expect(await screen.findByRole('header', { name: HOME.status.CALLED_OFF })).toBeTruthy();
    expect(screen.queryByRole('button', { name: PROPOSALS_COPY.game.withdraw })).toBeNull();
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The chat
// ---------------------------------------------------------------------------

describe('the chat — from the details (A4.4)', () => {
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

  it('names no court while the game waits for one payment, and has no Chat', async () => {
    await openDetails(
      bookingDetails({
        ...waitingForAPayment,
        money: unheldMoney(),
        leaving: { kind: 'WHILE_WAITING_FOR_A_PAYMENT', refund_grosze: 0, card_fee_grosze: 0 },
      }),
      [bookedRoomRow()],
    );

    await screen.findByText('Padel');
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
    expect(screen.getByLabelText('Where, Bonarka Arena, 3,1 km')).toBeTruthy();
  });

  it('keeps Chat past the result while the room lives, and has none once it has closed', async () => {
    await openDetails(bookingDetails({ status: 'COUNTED', shows_forecast: false }));

    await screen.findByText('Padel');
    expect(screen.getByRole('button', { name: OPEN_THE_CHAT })).toBeTruthy();
  });

  it('has no Chat once the room has closed', async () => {
    await openDetails(bookingDetails({ status: 'COUNTED', shows_forecast: false }), []);

    await screen.findByText('Padel');
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
  });

  it('says why the rooms could not be read, with the retry, rather than that there is no chat', async () => {
    // The rooms refused: the details draw no door, and a way straight into the room says why.
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    transport.on('GET', CONVERSATIONS_PATH, () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
    await screen.findByText('Padel');
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
    expect(await screen.findByTestId(`home-game-chat-${BOOKING}`)).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: HOME.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(await screen.findByTestId('conversation-stream')).toBeTruthy();
  });

  it('finds no room filed under another booking, though it names this game', async () => {
    await openDetails(bookingDetails(), [{ ...bookedRoomRow(), booking_id: SECOND_BOOKING }]);
    await screen.findByText('Padel');

    // The list has answered once the chat says it holds no room — then neither door is drawn.
    act(() => router.push(`/booking/${BOOKING}/chat`));
    expect(await screen.findByText(DETAILS.noRoom)).toBeTruthy();
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(screen.queryByRole('button', { name: OPEN_THE_CHAT })).toBeNull();
    act(() => router.back());
    await card();
    expect(screen.queryByTestId(`home-game-chat-${BOOKING}`)).toBeNull();
  });
});
