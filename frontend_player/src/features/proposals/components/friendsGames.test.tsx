/**
 * **A friends game on Home and in detail** ([#759](https://github.com/Raketa02/Raketa/issues/759);
 * the friends screens §6.1, §6.3, §9; friends 12; the words §29.8–§29.10).
 *
 * The real route tree, with the socket faked. **An invitation** waits on the reader — tomek.k's
 * Saturday 10:00 at Ogrody 33, Court 3, 25 zł a seat, magda.p In, ania.k still to answer, the
 * reader's 24 hours ending 1 h 35 after the read — in *FRIENDS GAME · 1*. **The reader's own game**,
 * sent by them, sits in Your games with each seat's state. **Every read happens at
 * `HOME_READ_AT`**, Thursday 1 October 10:00 in Warsaw. Sending is the Friends tab's suite's
 * (`groups`' `friendsGame.test.tsx`).
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { PAYMENTS_COPY } from '@/features/payments/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ANIA,
  ANSWER_BY,
  GROUP,
  INVITED,
  MAGDA,
  ME,
  PADEL_RATING,
  SATURDAY_10,
  TOMEK,
  VISA,
  invitation,
  invitedGame,
  seat,
  sentGame,
} from '@/test-support/friendsGame';
import {
  BARTEK,
  BOOKING,
  HOME_READ_AT,
  INES,
  PIOTR,
  bookedSides,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import {
  DEVICES_PATH,
  HOME_PATH,
  bookingPath,
  launchSignedIn,
  resetPayments,
  resetPush,
  stubGate,
  stubPaymentMethod,
  stubPayments,
  stubPush,
} from '@/test-support/onboardingRouter';
import { fakePayments, fakePush, type FakePush } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FILL_COPY } from './fillCopy';
import { FRIENDS_GAME_COPY } from './friendsGameCopy';

const COPY = FRIENDS_GAME_COPY;

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubPaymentMethod(transport, VISA);
  jest.setSystemTime(Date.parse(HOME_READ_AT));
});

afterEach(async () => {
  transport.restore();
  resetPayments();
  resetPush();
  useToastQueue.setState({ queue: [] });
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);
const acceptPath = `${bookingPath(INVITED)}/invitation/acceptance`;
const declinePath = `${bookingPath(INVITED)}/invitation/decline`;

/** Home with the invitation — and, once answered, without it. */
function stubInvitation(friendsGames: Wire['HomeFriendsGameSchema'][] = [invitation()]) {
  stubHomeGames(transport, [], { friends_games: friendsGames });
}

const theCard = () => screen.findByTestId('friends-games');

/** Every `testID` on screen, in the order the tree draws them — top of Home first. */
function testIdsInOrder(): readonly string[] {
  const ids: string[] = [];
  const walk = (node: unknown) => {
    if (node === null || typeof node !== 'object') return;
    if (Array.isArray(node)) {
      node.forEach(walk);
      return;
    }
    const { props, children } = node as {
      readonly props?: { readonly testID?: unknown };
      readonly children?: unknown;
    };
    if (typeof props?.testID === 'string') ids.push(props.testID);
    walk(children);
  };
  walk(screen.toJSON());
  return ids;
}

// ---------------------------------------------------------------------------
// FRIENDS GAME · n
// ---------------------------------------------------------------------------

describe('FRIENDS GAME · n on Home (friends 12)', () => {
  it('draws whose game, the clock, the four faces, the line with its kind, and the two answers', async () => {
    stubInvitation();
    await launchSignedIn();

    const row = await theCard();
    expect(within(row).getByText('Friends game · 1')).toBeTruthy();
    expect(within(row).getByText('tomek.k’s game')).toBeTruthy();
    expect(within(row).getByText('1 h 35')).toBeTruthy();
    expect(
      within(row).getByLabelText('tomek.k, in. magda.p, in. ania.k, still to answer. You'),
    ).toBeTruthy();
    expect(within(row).getByTestId(`face-in-${TOMEK}`)).toBeTruthy();
    expect(within(row).getByTestId(`face-in-${MAGDA}`)).toBeTruthy();
    expect(within(row).queryByTestId(`face-in-${ANIA}`)).toBeNull();
    expect(
      within(row).getByText('Saturday 10:00 · Ogrody 33 · Court 3 · Padel · Competitive'),
    ).toBeTruthy();
    expect(within(row).getByRole('button', { name: 'Not this time, tomek.k’s game' })).toBeTruthy();
    expect(
      within(row).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    ).toBeTruthy();
    expect(within(row).queryByText('tomek.k paid the court')).toBeNull();
  });

  it('reads Accept with who paid the court under Whole court', async () => {
    stubInvitation([invitation({ friends_game: invitedGame({ pay_mode: 'WHOLE_COURT' }) })]);
    await launchSignedIn();

    const row = await theCard();
    expect(within(row).getByText('tomek.k paid the court')).toBeTruthy();
    expect(within(row).getByRole('button', { name: 'Accept, tomek.k’s game' })).toBeTruthy();
  });

  it('sits above FRIEND REQUESTS and Your games', async () => {
    stubHomeGames(transport, [homeGame()], {
      friends_games: [invitation()],
      friend_requests: [
        {
          player_id: ANIA,
          nickname: 'ania.k',
          photo_id: null,
          photo_url: null,
          asked_at: '2026-09-30T10:00:00Z',
          by_link: true,
          from_ranking: false,
          group: null,
          sport: null,
          level: null,
          player_score: 98,
          reliability_band: 'VERY_HIGH',
        },
      ],
    });
    await launchSignedIn();
    await theCard();

    await screen.findByTestId('friend-requests');
    const order = testIdsInOrder();
    const at = (id: string) => order.indexOf(id);
    expect(at('friends-games')).toBeGreaterThan(-1);
    expect(at('friends-games')).toBeLessThan(at('friend-requests'));
    expect(at('friend-requests')).toBeLessThan(at(`home-game-${BOOKING}`));
  });

  it('draws no row and no title while nothing waits', async () => {
    stubInvitation([]);
    await launchSignedIn();
    await screen.findByText('Your games · 0');

    expect(screen.queryByTestId('friends-games')).toBeNull();
    expect(screen.queryByText(/^Friends game/)).toBeNull();
  });

  it('takes a card off at the instant its time runs out', async () => {
    stubInvitation();
    await launchSignedIn();
    await theCard();

    act(() => jest.advanceTimersByTime(96 * 60 * 1000));

    await waitFor(() => expect(screen.queryByTestId('friends-games')).toBeNull());
  });
});

describe('answering an invitation', () => {
  it('accepts with Split — the card moves to Your games, told so', async () => {
    stubInvitation();
    transport.on('POST', acceptPath, () => {
      stubHomeGames(transport, [homeGame({ booking_id: INVITED })], { friends_games: [] });
      return json<Wire['FriendsGameAnswerResponse']>({
        booking_id: INVITED,
        accepted: true,
        whole: false,
        your_payment: null,
      });
    });
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    );

    await waitFor(() => expect(screen.queryByTestId('friends-games')).toBeNull());
    expect(await screen.findByTestId(`home-game-${INVITED}`)).toBeTruthy();
    expect(transport.requestsTo('POST', acceptPath)).toHaveLength(1);
    expect(toasts()).toEqual([[COPY.invitation.accepted, 'ok']]);
    expect(screen.queryByTestId('its-a-game')).toBeNull();
  });

  it('is It’s a game! when the accept takes the last seat', async () => {
    stubInvitation();
    stubBooking(transport, bookingDetails({ booking_id: INVITED }));
    transport.on('POST', acceptPath, () =>
      json<Wire['FriendsGameAnswerResponse']>({
        booking_id: INVITED,
        accepted: true,
        whole: true,
        your_payment: null,
      }),
    );
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    );

    expect(await screen.findByTestId('its-a-game')).toBeTruthy();
  });

  it('is It’s a game! under Whole court too, the last seat taken with nothing held', async () => {
    stubPaymentMethod(transport, null);
    stubInvitation([invitation({ friends_game: invitedGame({ pay_mode: 'WHOLE_COURT' }) })]);
    stubBooking(transport, bookingDetails({ booking_id: INVITED }));
    transport.on('POST', acceptPath, () =>
      json<Wire['FriendsGameAnswerResponse']>({
        booking_id: INVITED,
        accepted: true,
        whole: true,
        your_payment: null,
      }),
    );
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept, tomek.k’s game' }),
    );

    expect(await screen.findByTestId('its-a-game')).toBeTruthy();
  });

  it('confirms a share the bank wants confirmed in the app, and the accept lands', async () => {
    const payments = fakePayments();
    stubPayments(payments);
    stubInvitation();
    transport.on('GET', '/api/v1/seat-charges/sc-ewa', () =>
      json<Wire['SeatChargeResponse']>({
        seat_charge_id: 'sc-ewa',
        proposal_id: INVITED,
        status: 'FAILED',
        refusal: 'AUTHENTICATION_REQUIRED',
        amount_grosze: 2500,
        sport: 'PADEL',
        starts_at: SATURDAY_10,
        club: { id: 'c0000000-0000-4000-8000-000000000033', name: 'Ogrody 33' },
        to_confirm: {
          client_secret: 'sc-ewa_secret',
          connected_account_id: 'acct_ogrody',
          publishable_key: 'pk_test_raketa',
        },
      }),
    );
    transport.on('POST', '/api/v1/seat-charges/sc-ewa/confirmation', () =>
      json<Wire['YesAnswerResponse']>({
        proposal_id: INVITED,
        open_seats: 0,
        booked: { booking_id: INVITED, game_id: 'g-1' },
        your_payment: null,
      }),
    );
    let accepted = 0;
    transport.on('POST', acceptPath, () => {
      accepted += 1;
      return json<Wire['FriendsGameAnswerResponse']>(
        accepted === 1
          ? {
              booking_id: INVITED,
              accepted: false,
              whole: false,
              your_payment: {
                seat_charge_id: 'sc-ewa',
                refusal: 'AUTHENTICATION_REQUIRED',
                confirm_by: ANSWER_BY,
                time_to: 'FIX_THE_CARD',
              },
            }
          : { booking_id: INVITED, accepted: true, whole: false, your_payment: null },
      );
    });
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    );
    fireEvent.press(await screen.findByRole('button', { name: FILL_COPY.confirm.check }));

    await waitFor(() => expect(toasts()).toEqual([[COPY.invitation.accepted, 'ok']]));
    expect(payments.payments.map((one) => one.clientSecret)).toEqual(['sc-ewa_secret']);
    expect(transport.requestsTo('POST', '/api/v1/seat-charges/sc-ewa/confirmation')).toHaveLength(
      1,
    );
    expect(transport.requestsTo('POST', acceptPath)).toHaveLength(2);
  });

  it('opens the payment setup first with nothing saved, under Split', async () => {
    stubPaymentMethod(transport, null);
    stubInvitation();
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    );

    expect(await screen.findByText(PAYMENTS_COPY.setupSheet.title)).toBeTruthy();
    expect(transport.requestsTo('POST', acceptPath)).toHaveLength(0);
  });

  it('accepts at once under Whole court with nothing saved — nothing is held', async () => {
    stubPaymentMethod(transport, null);
    stubInvitation([invitation({ friends_game: invitedGame({ pay_mode: 'WHOLE_COURT' }) })]);
    transport.on('POST', acceptPath, () =>
      json<Wire['FriendsGameAnswerResponse']>({
        booking_id: INVITED,
        accepted: true,
        whole: false,
        your_payment: null,
      }),
    );
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept, tomek.k’s game' }),
    );

    await waitFor(() => expect(transport.requestsTo('POST', acceptPath)).toHaveLength(1));
    expect(screen.queryByText(PAYMENTS_COPY.setupSheet.title)).toBeNull();
  });

  it.each([
    ['you_play_then', null, 'You already have a game at 10:00.'],
    [
      'games_per_week_booked',
      { games_per_week: 3 },
      'Your week is full: 3 games, the most you set in Games & money.',
    ],
    [
      'games_per_week_booked',
      { games_per_week: 1 },
      'Your week is full: 1 game, the most you set in Games & money.',
    ],
  ])('says %s on the card, which stays', async (code, details, sentence) => {
    stubInvitation();
    transport.on('POST', acceptPath, () =>
      json<Wire['ErrorResponse']>({ code, message: 'refused', trace_id: 't', details }, 409),
    );
    await launchSignedIn();

    const row = await theCard();
    fireEvent.press(within(row).getByRole('button', { name: /^Accept and pay 25 zł/ }));

    expect(await within(row).findByText(sentence)).toBeTruthy();
    expect(screen.getByTestId('friends-games')).toBeTruthy();
  });

  it('says an invitation that ended, and Home read again takes its card off', async () => {
    stubInvitation();
    transport.on('POST', acceptPath, () => {
      stubInvitation([]);
      return errorResponse(409, 'invitation_not_waiting');
    });
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    );

    await waitFor(() => expect(screen.queryByTestId('friends-games')).toBeNull());
    expect(toasts()).toEqual([[COPY.invitation.refused.invitation_not_waiting, 'bad']]);
  });

  it('takes the card off on Not this time', async () => {
    stubInvitation();
    transport.on('POST', declinePath, () => {
      stubInvitation([]);
      return noContent();
    });
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Not this time, tomek.k’s game' }),
    );

    await waitFor(() => expect(screen.queryByTestId('friends-games')).toBeNull());
    expect(transport.requestsTo('POST', declinePath)).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// Your games, and the details
// ---------------------------------------------------------------------------

describe('the sender’s game in Your games (the screens §6.3)', () => {
  it('says how many friends are in and who it waits for, and a seat empty', async () => {
    stubHomeGames(transport, [homeGame({ friends_game: sentGame() })]);
    await launchSignedIn();

    const card = await screen.findByTestId(`home-game-${BOOKING}`);
    expect(
      within(card).getByText('1 of 3 friends in · waiting for ines.d · 1 seat empty'),
    ).toBeTruthy();
  });

  it('says only who it waits for while nobody is In yet', async () => {
    stubHomeGames(transport, [
      homeGame({
        friends_game: sentGame({
          seats: [
            seat(ME, 'IN'),
            seat(PIOTR, 'WAITING', { waiting_until: '2026-10-01T20:00:00Z' }),
            seat(INES, 'WAITING', { waiting_until: '2026-10-01T20:00:00Z' }),
            seat(BARTEK, 'WAITING', { waiting_until: '2026-10-01T20:00:00Z' }),
          ],
          friends_in: 0,
        }),
      }),
    ]);
    await launchSignedIn();

    expect(await screen.findByText('Waiting for piotr.s, ines.d and bartek.l')).toBeTruthy();
  });

  it('draws the ordinary row once every seat is In, and nothing for a friend’s own card', async () => {
    const allIn = sentGame({
      seats: [ME, PIOTR, INES, BARTEK].map((id) => seat(id, 'IN')),
      friends_in: 3,
    });
    stubHomeGames(transport, [
      homeGame({ friends_game: allIn }),
      homeGame({ booking_id: INVITED, friends_game: sentGame({ you_are_the_sender: false }) }),
    ]);
    await launchSignedIn();
    await screen.findByTestId(`home-game-${BOOKING}`);

    expect(screen.queryByText(/friends in/)).toBeNull();
    expect(screen.queryByText(/^Waiting for/)).toBeNull();
  });

  it('says who paid the court on a friend’s Whole-court game, in place of a share', async () => {
    stubHomeGames(transport, [
      homeGame({
        friends_game: invitedGame({
          pay_mode: 'WHOLE_COURT',
          your_invitation_until: null,
          seats: [seat(TOMEK, 'IN'), seat(ME, 'IN')],
        }),
      }),
    ]);
    await launchSignedIn();

    const card = await screen.findByTestId(`home-game-${BOOKING}`);
    expect(
      within(card).getByText('tomek.k paid the court · free to leave until Fri 16:00'),
    ).toBeTruthy();
    expect(within(card).queryByText(/28 zł/)).toBeNull();
  });
});

describe('a friends game’s details (the screens §9)', () => {
  async function openDetails(friendsGame: Wire['FriendsGameSchema']) {
    stubHomeGames(transport, [homeGame({ friends_game: friendsGame })]);
    stubBooking(
      transport,
      bookingDetails({ friends_game: friendsGame, leaving: null, sides: bookedSides() }),
    );
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: 'Open game' }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  }

  it('reads each seat’s state, the waiting one counting down, and Split under the price', async () => {
    await openDetails(sentGame());

    const seats = await screen.findByTestId('friends-seats');
    expect(within(seats).getByLabelText('You, In')).toBeTruthy();
    expect(within(seats).getByLabelText('piotr.s, In')).toBeTruthy();
    expect(within(seats).getByLabelText('ines.d, waiting · 12 h 00 left')).toBeTruthy();
    expect(within(seats).getByLabelText('bartek.l, can’t make it')).toBeTruthy();
    expect(screen.getByText(/· Split$/)).toBeTruthy();
  });

  it('reads didn’t answer for a seat whose time ran out', async () => {
    await openDetails(
      sentGame({
        seats: [seat(ME, 'IN'), seat(PIOTR, 'DIDNT_ANSWER')],
        friends_seated: 1,
      }),
    );

    expect(await screen.findByLabelText('piotr.s, didn’t answer')).toBeTruthy();
  });

  it('reads You paid the court under the price on the sender’s Whole-court game', async () => {
    await openDetails(sentGame({ pay_mode: 'WHOLE_COURT' }));
    expect(await screen.findByText(/· You paid the court$/)).toBeTruthy();
  });

  it('reads who paid the court to a friend on a Whole-court game, in place of the share’s hold', async () => {
    await openDetails(
      invitedGame({
        pay_mode: 'WHOLE_COURT',
        your_invitation_until: null,
        seats: [seat(TOMEK, 'IN'), seat(ME, 'IN')],
        friends_seated: 1,
      }),
    );

    expect(
      await screen.findByText('tomek.k paid the court · free to leave until Fri 16:00'),
    ).toBeTruthy();
    expect(screen.queryByText(/Held on your card/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Notices
// ---------------------------------------------------------------------------

describe('a friends game’s notices, tapped (the mechanics §12)', () => {
  let phone: FakePush;

  beforeEach(() => {
    transport.on('POST', DEVICES_PATH, () => noContent());
    phone = fakePush();
    stubPush(phone);
  });

  const push = (kind: string, opens: string, gameId: string | null) => ({
    notice_id: 'd0000000-0000-4000-8000-000000000759',
    kind,
    opens,
    game_id: gameId,
    pool_id: GROUP,
    sport: 'PADEL',
    game_kind: 'COMPETITIVE',
  });

  it('opens Home on the invitation', async () => {
    stubInvitation();
    await launchSignedIn();
    await theCard();
    const homeReads = transport.requestsTo('GET', HOME_PATH).length;

    act(() => phone.tap(push('FRIENDS_GAME_INVITATION', 'HOME', INVITED)));

    await waitFor(() => expect(screen).toHavePathname('/'));
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads),
    );
    expect(screen.getByTestId('friends-games')).toBeTruthy();
  });

  it.each([
    ['CANT_MAKE_IT', 'GAME_CALLED_OFF'],
    ['DIDNT_ANSWER', 'GAME_CALLED_OFF'],
  ])('opens the game for %s, as for %s', async (first, second) => {
    stubHomeGames(transport, [homeGame({ friends_game: sentGame() })]);
    stubBooking(transport, bookingDetails({ friends_game: sentGame(), leaving: null }));
    await launchSignedIn();

    act(() => phone.tap(push(first, 'BOOKING', BOOKING)));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(await screen.findByTestId('friends-seats')).toBeTruthy();

    act(() => phone.tap(push(second, 'BOOKING', BOOKING)));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  });
});
