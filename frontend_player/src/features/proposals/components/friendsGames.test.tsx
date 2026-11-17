/**
 * **A friends game in Needs your answer and in detail** ([#759](https://github.com/Raketa02/Raketa/issues/759),
 * [#817](https://github.com/Raketa02/Raketa/issues/817); ADR-0205 §1; the friends screens §6.1,
 * §6.3, §9; friends 12; home refactor 2; the words §29.8–§29.10).
 *
 * The real route tree, with the socket faked. **An invitation** waits on the reader — tomek.k's
 * Saturday 10:00 at Ogrody 33, Court 3, 25 zł a seat, magda.p In, ania.k still to answer, the
 * reader's 24 hours ending 1 h 35 after the read — in *FRIENDS GAME · 1*, **behind Home's envelope**
 * in the sheet it opens, after *TO CONFIRM* and before *FRIEND REQUESTS*. **The reader's own game**,
 * sent by them, sits in Your games with each seat's state. **Every read happens at
 * `HOME_READ_AT`**, Thursday 1 October 10:00 in Warsaw. Sending is the Friends tab's suite's
 * (`groups`' `friendsGame.test.tsx`).
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Dimensions, StyleSheet } from 'react-native';

import { PAYMENTS_COPY, paymentKeys } from '@/features/payments/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
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
import { envelope, openNeedsYourAnswer, sheetTitle } from '@/test-support/needsYourAnswer';
import {
  DEVICES_PATH,
  HOME_PATH,
  PAYMENTS_TO_CONFIRM_PATH,
  bookingPath,
  launchSignedIn,
  resetPayments,
  resetPush,
  stubGate,
  stubPaymentMethod,
  stubPayments,
  stubPaymentsToConfirm,
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

/** A second invitation, from magda.p, ending an hour after tomek.k's. */
const SECOND = 'b0000000-0000-4000-8000-000000000013';

/** Home with the invitation — and, once answered, without it. */
function stubInvitation(friendsGames: Wire['HomeFriendsGameSchema'][] = [invitation()]) {
  stubHomeGames(transport, [], { friends_games: friendsGames });
}

/** A friend request waiting on the reader beside the invitation — something else in the sheet. */
const ANIAS_REQUEST: Wire['HomeFriendRequestSchema'] = {
  player_id: ANIA,
  nickname: 'ania.k',
  photo_id: null,
  photo_url: null,
  asked_at: '2026-09-30T10:00:00Z',
  by_link: true,
  from_ranking: false,
  from_new_players: false,
  from_same_level: false,
  from_same_vibe: false,
  group: null,
  sport: null,
  level: null,
  player_score: 98,
  reliability_band: 'VERY_HIGH',
  percent_even: null,
  in_common: null,
};

/** A share refused while the reader was elsewhere, waiting in *TO CONFIRM*. */
const PAYMENT: Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'] = {
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
  confirm_by: null,
  time_to: null,
};

/** Needs your answer up — opened on the envelope unless it is up already — and its FRIENDS GAME. */
async function theCard() {
  if (sheetTitle() === null) await openNeedsYourAnswer();
  return screen.findByTestId('friends-games');
}

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

/** The width the rail hands an invitation's tile — read off the tile, which holds its top row. */
function tileWidth(bookingId: string): unknown {
  let node = screen.getByTestId(`friends-game-${bookingId}`).parent;
  while (node !== null && StyleSheet.flatten(node.props.style)?.width === undefined) {
    node = node.parent;
  }
  return node === null ? undefined : StyleSheet.flatten(node.props.style)?.width;
}

const content = () => Dimensions.get('window').width - 2 * theme.size.gutter;

// ---------------------------------------------------------------------------
// FRIENDS GAME · n
// ---------------------------------------------------------------------------

describe('FRIENDS GAME · n in Needs your answer (friends 12; home refactor 2)', () => {
  it('waits behind the envelope, and is no longer on Home', async () => {
    stubInvitation();
    await launchSignedIn();

    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(screen.queryByTestId('friends-games')).toBeNull();
    expect(screen.queryByText('tomek.k’s game')).toBeNull();

    await openNeedsYourAnswer();

    expect(screen.getByRole('header', { name: 'Friends game · 1' })).toBeTruthy();
    expect(screen.getByTestId(`friends-game-${INVITED}`)).toBeTruthy();
  });

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

  // ADR-0205 §1: TO CONFIRM, FRIENDS GAME, FRIEND REQUESTS, ASKED FOR A LEVEL — always in that order.
  it('stands after TO CONFIRM and before FRIEND REQUESTS', async () => {
    stubPaymentsToConfirm(transport, [PAYMENT]);
    stubHomeGames(transport, [homeGame()], {
      needing_you: 1,
      friends_games: [invitation()],
      friend_requests: [ANIAS_REQUEST],
    });
    await launchSignedIn();
    await theCard();
    await screen.findByTestId('to-confirm');

    const order = testIdsInOrder();
    const at = (id: string) => order.indexOf(id);
    expect(at('to-confirm')).toBeGreaterThan(-1);
    expect(at('to-confirm')).toBeLessThan(at('friends-games'));
    expect(at('friends-games')).toBeLessThan(at('friend-requests'));
    expect(screen.getByRole('header', { name: 'To confirm · 1' })).toBeTruthy();
  });

  // Q9, Q46: one big tile at a time, on the paging rail, the dots from two.
  it('draws one invitation as one big tile at the content width, with no dots', async () => {
    stubInvitation();
    await launchSignedIn();

    const row = await theCard();
    expect(tileWidth(INVITED)).toBe(content());
    expect(within(row).queryByTestId('pager-dots', { includeHiddenElements: true })).toBeNull();
  });

  it('pages two invitations one at a time, the dots under them', async () => {
    stubInvitation([
      invitation(),
      invitation({
        booking_id: SECOND,
        friends_game: invitedGame({
          sender_id: MAGDA,
          sender_nickname: 'magda.p',
          your_invitation_until: '2026-10-01T10:35:00Z',
        }),
      }),
    ]);
    await launchSignedIn();

    const row = await theCard();
    expect(within(row).getByText('Friends game · 2')).toBeTruthy();
    expect(tileWidth(INVITED)).toBe(content());
    expect(tileWidth(SECOND)).toBe(content());
    const dots = within(row).getByTestId('pager-dots', { includeHiddenElements: true });
    expect(dots.children).toHaveLength(2);
  });

  it('draws no section, and no envelope, while nothing waits', async () => {
    stubInvitation([]);
    await launchSignedIn();
    await screen.findByText('Your games · 0');

    expect(envelope()).toBeNull();
    expect(screen.queryByTestId('friends-games')).toBeNull();
    expect(screen.queryByText(/^Friends game/)).toBeNull();
  });

  it('takes a tile off at the instant its time runs out — and the sheet with it, if nothing else waits', async () => {
    stubInvitation();
    await launchSignedIn();
    await theCard();

    act(() => jest.advanceTimersByTime(96 * 60 * 1000));

    await waitFor(() => expect(screen.queryByTestId('friends-games')).toBeNull());
    await waitFor(() => expect(sheetTitle()).toBeNull());
    expect(envelope()).toBeNull();
  });
});

describe('answering an invitation in Needs your answer', () => {
  it('accepts with Split — the tile leaves, the game is in Your games, and the emptied sheet closes', async () => {
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
    await waitFor(() => expect(sheetTitle()).toBeNull());
    expect(envelope()).toBeNull();
    expect(await screen.findByTestId(`home-game-${INVITED}`)).toBeTruthy();
    expect(transport.requestsTo('POST', acceptPath)).toHaveLength(1);
    expect(toasts()).toEqual([[COPY.invitation.accepted, 'ok']]);
    expect(screen.queryByTestId('its-a-game')).toBeNull();
  });

  /** It's a game! closes the sheet for good, whatever still waits in it (#817; Q24). */
  it('is It’s a game! when the accept takes the last seat — and the sheet does not come back', async () => {
    stubHomeGames(transport, [], {
      friends_games: [invitation()],
      friend_requests: [ANIAS_REQUEST],
    });
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
    fireEvent.press(screen.getByRole('button', { name: FILL_COPY.itsAGame.later }));

    await waitFor(() => expect(screen.queryByTestId('its-a-game')).toBeNull());
    expect(sheetTitle()).toBeNull();
    // ania.k's request still waits: the envelope stays, and the sheet is the player's to open again.
    expect(envelope()).not.toBeNull();
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

  it('confirms a share the bank wants confirmed in the app, over the sheet, and the accept lands', async () => {
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
    transport.on('POST', '/api/v1/seat-charges/sc-ewa/confirmation', () => {
      // The server accepts the invitation with the payment: Home's next read no longer lists it.
      stubInvitation([]);
      return json<Wire['YesAnswerResponse']>({
        proposal_id: INVITED,
        open_seats: 0,
        booked: { booking_id: INVITED, game_id: 'g-1' },
        your_payment: null,
      });
    });
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
    // The confirmation was the fill's, over the sheet: nothing closed under it, and once it closed
    // on the accept, nothing waited — the sheet and the envelope went with it.
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: FILL_COPY.confirm.check })).toBeNull(),
    );
    await waitFor(() => expect(sheetTitle()).toBeNull());
    expect(envelope()).toBeNull();
  });

  /** Q24: the bank's confirmation is a sheet over the sheet; closed, it hands back to the sheet. */
  it('hands back to the sheet when the bank’s confirmation is closed unconfirmed', async () => {
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
    transport.on('POST', acceptPath, () =>
      json<Wire['FriendsGameAnswerResponse']>({
        booking_id: INVITED,
        accepted: false,
        whole: false,
        your_payment: {
          seat_charge_id: 'sc-ewa',
          refusal: 'AUTHENTICATION_REQUIRED',
          confirm_by: ANSWER_BY,
          time_to: 'FIX_THE_CARD',
        },
      }),
    );
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    );
    fireEvent.press(await screen.findByRole('button', { name: FILL_COPY.confirm.close }));

    await waitFor(() =>
      expect(screen.queryByRole('button', { name: FILL_COPY.confirm.close })).toBeNull(),
    );
    expect(sheetTitle()).not.toBeNull();
    expect(screen.getByTestId(`friends-game-${INVITED}`)).toBeTruthy();
  });

  /** Q24: the card setup is a sheet opened from the sheet — over it, and back to it on close. */
  it('opens the payment setup over the sheet with nothing saved, and hands back to it on close', async () => {
    stubPaymentMethod(transport, null);
    stubInvitation();
    await launchSignedIn();
    const row = await theCard();
    // The card reads whether a method is saved as it is drawn — in the sheet, once it opens — and is
    // told the answer on Query's next tick.
    await waitFor(() => expect(queryClient.getQueryData(paymentKeys.current())).toBeDefined());
    act(() => jest.advanceTimersByTime(0));

    fireEvent.press(
      within(row).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    );

    expect(await screen.findByText(PAYMENTS_COPY.setupSheet.title)).toBeTruthy();
    expect(transport.requestsTo('POST', acceptPath)).toHaveLength(0);

    fireEvent.press(screen.getByRole('button', { name: PAYMENTS_COPY.setupSheet.close }));

    await waitFor(() => expect(screen.queryByText(PAYMENTS_COPY.setupSheet.title)).toBeNull());
    expect(sheetTitle()).not.toBeNull();
    expect(screen.getByTestId(`friends-game-${INVITED}`)).toBeTruthy();
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
  ])('says %s on the tile, which stays', async (code, details, sentence) => {
    stubInvitation();
    transport.on('POST', acceptPath, () =>
      json<Wire['ErrorResponse']>({ code, message: 'refused', trace_id: 't', details }, 409),
    );
    await launchSignedIn();

    const row = await theCard();
    fireEvent.press(within(row).getByRole('button', { name: /^Accept and pay 25 zł/ }));

    expect(await within(row).findByText(sentence)).toBeTruthy();
    expect(screen.getByTestId('friends-games')).toBeTruthy();
    expect(sheetTitle()).not.toBeNull();
  });

  it('says an invitation that ended, and Home read again takes its tile off', async () => {
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

  it('takes the tile off on Not this time, and the sheet stays while something else waits', async () => {
    stubHomeGames(transport, [], {
      friends_games: [invitation()],
      friend_requests: [ANIAS_REQUEST],
    });
    transport.on('POST', declinePath, () => {
      stubHomeGames(transport, [], { friends_games: [], friend_requests: [ANIAS_REQUEST] });
      return noContent();
    });
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Not this time, tomek.k’s game' }),
    );

    await waitFor(() => expect(screen.queryByTestId('friends-games')).toBeNull());
    expect(transport.requestsTo('POST', declinePath)).toHaveLength(1);
    expect(sheetTitle()).not.toBeNull();
    expect(screen.getByTestId(`friend-request-${ANIA}`)).toBeTruthy();
  });

  it('closes the sheet on Not this time for the last thing waiting, and the envelope goes', async () => {
    stubInvitation();
    transport.on('POST', declinePath, () => {
      stubInvitation([]);
      return noContent();
    });
    await launchSignedIn();

    fireEvent.press(
      within(await theCard()).getByRole('button', { name: 'Not this time, tomek.k’s game' }),
    );

    await waitFor(() => expect(sheetTitle()).toBeNull());
    expect(envelope()).toBeNull();
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

  /** #817, ADR-0205 §1: the invitation's notice lands on the sheet it waits in. */
  it('opens Home with Needs your answer up on the invitation, from another tab', async () => {
    stubInvitation();
    await launchSignedIn();
    await waitFor(() => expect(envelope()).not.toBeNull());
    act(() => router.push('/you'));
    await waitFor(() => expect(screen).toHavePathname('/you'));
    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    const toConfirmReads = transport.requestsTo('GET', PAYMENTS_TO_CONFIRM_PATH).length;

    act(() => phone.tap(push('FRIENDS_GAME_INVITATION', 'HOME', INVITED)));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByRole('header', { name: 'Needs your answer' })).toBeTruthy();
    expect(screen.getByTestId(`friends-game-${INVITED}`)).toBeTruthy();
    // The two reads the sheet is drawn from, read again: it opened on what they said.
    expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads);
    expect(transport.requestsTo('GET', PAYMENTS_TO_CONFIRM_PATH).length).toBeGreaterThan(
      toConfirmReads,
    );
  });

  it('opens Needs your answer on Home too, where the player already is', async () => {
    stubInvitation();
    await launchSignedIn();
    await waitFor(() => expect(envelope()).not.toBeNull());
    expect(sheetTitle()).toBeNull();

    act(() => phone.tap(push('FRIENDS_GAME_INVITATION', 'HOME', INVITED)));

    expect(await screen.findByRole('header', { name: 'Needs your answer' })).toBeTruthy();
    expect(screen.getByTestId('friends-games')).toBeTruthy();
  });

  /** Answered on another phone, or run out: Home as it is — the sheet is never shown empty. */
  it('opens Home as it is when nothing waits by the time Home is read again', async () => {
    stubInvitation();
    await launchSignedIn();
    await waitFor(() => expect(envelope()).not.toBeNull());
    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    stubInvitation([]);

    act(() => phone.tap(push('FRIENDS_GAME_INVITATION', 'HOME', INVITED)));

    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads),
    );
    await waitFor(() => expect(envelope()).toBeNull());
    expect(sheetTitle()).toBeNull();
    expect(screen).toHavePathname('/');
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
