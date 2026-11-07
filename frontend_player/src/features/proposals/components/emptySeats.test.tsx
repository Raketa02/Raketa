/**
 * **A friends game's empty seats, and leaving it** ([#760](https://github.com/Raketa02/Raketa/issues/760),
 * over #752's routes; the friends screens §9; the mechanics §10–§12; the words §29.8–§29.10).
 *
 * The real route tree, with the socket faked. **The reader's own game** is Home's booked game — you
 * + piotr.s against ines.d + bartek.l at Bonarka Arena on Saturday 16:00, 28 zł a seat, the club's
 * cut-off Friday 16:00 — sent by the reader in the group *Ogrody*: piotr.s In, ines.d still to
 * answer, **bartek.l can't make it**, so his seat is empty. **Every read happens at
 * `HOME_READ_AT`**, Thursday 1 October 10:00 in Warsaw, before the cut-off. Sending and answering
 * are `friendsGames.test.tsx`'s.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ANIA,
  GROUP,
  MAGDA,
  ME,
  PADEL_RATING,
  TOMEK,
  VISA,
  invitation,
  invitedGame,
  seat,
  sentGame,
  tile,
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
  FRIENDS_PATH,
  bookingPath,
  launchSignedIn,
  resetPayments,
  resetPush,
  stubGate,
  stubPaymentMethod,
  stubPush,
} from '@/test-support/onboardingRouter';
import { fakePush, type FakePush } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { FRIENDS_GAME_COPY } from './friendsGameCopy';
import { LEAVE_SHEET_TITLE, LEAVE_THE_GAME } from './leaveSheetCopy';

const COPY = FRIENDS_GAME_COPY;

const KAROL = 'f0000000-0000-4000-8000-000000000010';
const ZOFIA = 'f0000000-0000-4000-8000-000000000011';

const OGRODY: Wire['GroupResponse'] = {
  id: GROUP,
  kind: 'PLAYER',
  name: 'Ogrody',
  monogram: { letters: 'Og', colour: 2 },
  sports: ['PADEL'],
  member_count: 8,
  home_club: { id: 'c0000000-0000-4000-8000-000000000033', name: 'Ogrody 33' },
  link: 'https://raketa.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

function friend(id: string, nickname: string, level?: number): Wire['FriendSchema'] {
  return {
    player_id: id,
    nickname,
    photo_id: null,
    photo_url: null,
    friends_since: '2026-09-01T10:00:00Z',
    sports: level === undefined ? [] : [{ sport: 'PADEL', level, band: 'Established' }],
    level_asked_in: [],
  };
}

/** The reader's padel friends: karol.t and piotr.s rated — piotr.s is on the game — zofia.b not. */
const FRIENDS = [
  friend(KAROL, 'karol.t', 2.75),
  friend(PIOTR, 'piotr.s', 2.95),
  friend(ZOFIA, 'zofia.b'),
];

/** bartek.l's seat, empty: the sender may invite and open it, piotr.s already invited into it. */
function bartekEmpty(extra: Partial<Wire['FriendsSeatSchema']> = {}): Wire['FriendsSeatSchema'] {
  return seat(BARTEK, 'CANT_MAKE_IT', {
    seat_of: BARTEK,
    can_invite: true,
    can_open: true,
    ...extra,
  });
}

/** The reader's own game, bartek.l's seat empty. */
function withAnEmptySeat(
  extra: Partial<Wire['FriendsGameSchema']> = {},
  empty: Partial<Wire['FriendsSeatSchema']> = {},
): Wire['FriendsGameSchema'] {
  return sentGame({
    seats: [
      seat(ME, 'IN'),
      seat(PIOTR, 'IN'),
      seat(INES, 'WAITING', { waiting_until: '2026-10-01T20:00:00Z' }),
      bartekEmpty(empty),
    ],
    ...extra,
  });
}

/** The same game read by piotr.s's friend on it — In, not the sender: Invite a friend only. */
function asAFriendIn(): Wire['FriendsGameSchema'] {
  return withAnEmptySeat(
    {
      sender_id: PIOTR,
      sender_nickname: 'piotr.s',
      you_are_the_sender: false,
      can_call_off: false,
    },
    { can_open: false },
  );
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubPaymentMethod(transport, VISA);
  transport.on('GET', `/api/v1/groups/${GROUP}`, () => json(OGRODY));
  transport.on('GET', FRIENDS_PATH, () =>
    json<Wire['FriendsResponse']>({ sport: 'PADEL', friends: FRIENDS }),
  );
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
const invitePath = `${bookingPath(BOOKING)}/seats/${BARTEK}/invitations`;
const openPath = `${bookingPath(BOOKING)}/seats/${BARTEK}/opening`;
const callOffPath = `${bookingPath(BOOKING)}/call-off`;
const departurePath = `${bookingPath(BOOKING)}/departure`;

const INVITE = 'Invite a friend, bartek.l’s seat';
const OPEN = 'Open to Ogrody, bartek.l’s seat';

function stubTheGame(
  friendsGame: Wire['FriendsGameSchema'],
  extra: Partial<Wire['BookingDetailsResponse']> = {},
) {
  stubHomeGames(transport, [homeGame({ friends_game: friendsGame })]);
  stubBooking(
    transport,
    bookingDetails({ friends_game: friendsGame, leaving: null, sides: bookedSides(), ...extra }),
  );
}

async function openDetails(
  friendsGame: Wire['FriendsGameSchema'],
  extra: Partial<Wire['BookingDetailsResponse']> = {},
) {
  stubTheGame(friendsGame, extra);
  await launchSignedIn();
  fireEvent.press(await screen.findByRole('button', { name: 'Open game' }));
  await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  return screen.findByTestId('friends-seats');
}

// ---------------------------------------------------------------------------
// An empty seat, on the details
// ---------------------------------------------------------------------------

describe('an empty seat on the details (the screens §9)', () => {
  it('offers the sender Invite a friend and Open to the group by its name, on the empty seat only', async () => {
    const seats = await openDetails(withAnEmptySeat());

    expect(await within(seats).findByRole('button', { name: OPEN })).toBeTruthy();
    expect(within(seats).getByRole('button', { name: INVITE })).toBeTruthy();
    expect(within(seats).getByText('Open to Ogrody')).toBeTruthy();
    expect(within(seats).getAllByRole('button')).toHaveLength(2);
  });

  it('offers a friend In Invite a friend alone — opening is the sender’s', async () => {
    const seats = await openDetails(asAFriendIn());

    expect(within(seats).getByRole('button', { name: INVITE })).toBeTruthy();
    expect(within(seats).queryByRole('button', { name: /^Open to/ })).toBeNull();
    expect(transport.requestsTo('GET', `/api/v1/groups/${GROUP}`)).toHaveLength(0);
  });

  it('says who is invited into the seat and how long they have', async () => {
    const seats = await openDetails(
      withAnEmptySeat(
        {},
        {
          invitations: [
            {
              player_id: KAROL,
              nickname: 'karol.t',
              until: '2026-10-02T04:00:00Z',
              invited_by_you: true,
            },
          ],
        },
      ),
    );

    expect(within(seats).getByText('karol.t invited · 20 h 00 left')).toBeTruthy();
  });

  it('reads a seat open to the group, after the cut-off a leaver’s, with Invite a friend still', async () => {
    const seats = await openDetails(
      withAnEmptySeat({ can_call_off: false }, { state: 'SEAT_OPEN', can_open: false }),
      { leaving: { kind: 'AFTER_THE_CUT_OFF', refund_grosze: null, card_fee_grosze: null } },
    );

    expect(within(seats).getByLabelText('bartek.l, Seat open')).toBeTruthy();
    expect(within(seats).getByRole('button', { name: INVITE })).toBeTruthy();
    expect(within(seats).queryByRole('button', { name: /^Open to/ })).toBeNull();
  });

  it('offers nothing on a seat the server gives the reader no action on', async () => {
    const seats = await openDetails(withAnEmptySeat({}, { can_invite: false, can_open: false }));

    expect(within(seats).queryAllByRole('button')).toHaveLength(0);
  });
});

describe('Open to the group', () => {
  it('asks first that a stranger can then take it, and opens nothing on Not yet', async () => {
    const seats = await openDetails(withAnEmptySeat());

    fireEvent.press(await within(seats).findByRole('button', { name: OPEN }));
    const sheet = await screen.findByTestId('open-seat-sheet');
    expect(
      within(sheet).getByText('Anyone in Ogrody who fits can take it and pay 28 zł.'),
    ).toBeTruthy();
    expect(screen.getByText('Open this seat to Ogrody?')).toBeTruthy();

    fireEvent.press(within(sheet).getByRole('button', { name: COPY.open.notYet }));

    await waitFor(() => expect(screen.queryByTestId('open-seat-sheet')).toBeNull());
    expect(transport.requestsTo('POST', openPath)).toHaveLength(0);
  });

  it('opens the seat, says so, and the details read it as Seat open', async () => {
    transport.on('POST', openPath, () => {
      stubTheGame(withAnEmptySeat({}, { state: 'SEAT_OPEN', can_open: false }));
      return noContent();
    });
    const seats = await openDetails(withAnEmptySeat());

    fireEvent.press(await within(seats).findByRole('button', { name: OPEN }));
    const sheet = await screen.findByTestId('open-seat-sheet');
    fireEvent.press(within(sheet).getByRole('button', { name: 'Open to Ogrody' }));

    await waitFor(() => expect(transport.requestsTo('POST', openPath)).toHaveLength(1));
    await waitFor(() =>
      expect(toasts()).toEqual([['Seat open — anyone in Ogrody who fits can take it.', 'ok']]),
    );
    expect(await screen.findByLabelText('bartek.l, Seat open')).toBeTruthy();
    expect(screen.queryByRole('button', { name: OPEN })).toBeNull();
  });

  it('says the cut-off opened it already, and reads the game again', async () => {
    transport.on('POST', openPath, () => errorResponse(409, 'cut_off_has_passed'));
    const seats = await openDetails(withAnEmptySeat());
    const reads = transport.requestsTo('GET', bookingPath(BOOKING)).length;

    fireEvent.press(await within(seats).findByRole('button', { name: OPEN }));
    fireEvent.press(
      within(await screen.findByTestId('open-seat-sheet')).getByRole('button', {
        name: 'Open to Ogrody',
      }),
    );

    await waitFor(() => expect(toasts()).toEqual([[COPY.open.refused.cut_off_has_passed, 'bad']]));
    await waitFor(() => expect(screen.queryByTestId('open-seat-sheet')).toBeNull());
    await waitFor(() =>
      expect(transport.requestsTo('GET', bookingPath(BOOKING)).length).toBeGreaterThan(reads),
    );
  });
});

// ---------------------------------------------------------------------------
// Invite a friend: the picker with one seat
// ---------------------------------------------------------------------------

describe('Invite a friend', () => {
  async function openThePicker(friendsGame = withAnEmptySeat()) {
    const seats = await openDetails(friendsGame);
    fireEvent.press(await within(seats).findByRole('button', { name: INVITE }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/invite`));
    return screen.findByTestId(`pick-${KAROL}`);
  }

  it('opens the picker with one seat, leaving out who is on the game already', async () => {
    const karol = await openThePicker();

    expect(screen.queryByTestId(`pick-${PIOTR}`)).toBeNull();
    expect(screen.getByRole('checkbox', { name: /^zofia\.b/, disabled: true })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Invite a friend', disabled: true })).toBeTruthy();

    fireEvent.press(karol);

    expect(screen.getByRole('button', { name: 'Invite karol.t', disabled: false })).toBeTruthy();
    expect(screen.getByRole('checkbox', { name: /^karol\.t/, checked: true })).toBeTruthy();
  });

  it('invites the friend picked into that seat, and goes back to the game told so', async () => {
    transport.on('POST', invitePath, () => noContent());
    fireEvent.press(await openThePicker());

    fireEvent.press(screen.getByRole('button', { name: 'Invite karol.t' }));

    await waitFor(() => expect(transport.requestsTo('POST', invitePath)).toHaveLength(1));
    expect(transport.requestsTo('POST', invitePath)[0]!.body).toEqual({ friend_id: KAROL });
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(toasts()).toEqual([['Invitation sent to karol.t.', 'ok']]);
  });

  it('says a refusal about the friend on the picker, the pick still there to change', async () => {
    transport.on('POST', invitePath, () => errorResponse(409, 'friend_plays_then'));
    fireEvent.press(await openThePicker());

    fireEvent.press(screen.getByRole('button', { name: 'Invite karol.t' }));

    expect(await screen.findByText('karol.t already has a game at 16:00.')).toBeTruthy();
    expect(screen).toHavePathname(`/booking/${BOOKING}/invite`);
    expect(screen.getByRole('checkbox', { name: /^karol\.t/, checked: true })).toBeTruthy();
  });

  it('goes back to the game when the seat was taken first, saying so', async () => {
    transport.on('POST', invitePath, () => errorResponse(409, 'seat_just_taken'));
    fireEvent.press(await openThePicker());

    fireEvent.press(screen.getByRole('button', { name: 'Invite karol.t' }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(toasts()).toEqual([['Someone took that seat first.', 'bad']]);
  });

  it('is a friend In’s too', async () => {
    transport.on('POST', invitePath, () => noContent());
    fireEvent.press(await openThePicker(asAFriendIn()));

    fireEvent.press(screen.getByRole('button', { name: 'Invite karol.t' }));

    await waitFor(() => expect(transport.requestsTo('POST', invitePath)).toHaveLength(1));
  });
});

// ---------------------------------------------------------------------------
// Leaving
// ---------------------------------------------------------------------------

describe('the sender leaving (the mechanics §11.2)', () => {
  const beforeTheCutOff: Partial<Wire['BookingDetailsResponse']> = {
    leaving: { kind: 'BEFORE_THE_CUT_OFF', refund_grosze: null, card_fee_grosze: null },
  };

  async function openTheSheet(friendsGame: Wire['FriendsGameSchema']) {
    await openDetails(friendsGame, beforeTheCutOff);
    fireEvent.press(await screen.findByRole('button', { name: LEAVE_THE_GAME }));
    return screen.findByTestId('senders-leave-sheet');
  }

  it('offers two ways with Split, each saying what it means for the money', async () => {
    const sheet = await openTheSheet(withAnEmptySeat());

    expect(
      within(sheet).getByText(
        'Everyone is told, nobody pays, and the court goes back to Bonarka Arena.',
      ),
    ).toBeTruthy();
    expect(
      within(sheet).getByText(
        'You pay nothing. Your friends keep the court; a seat still empty on Fri 16:00 calls the game off and nobody pays.',
      ),
    ).toBeTruthy();
    expect(
      within(sheet).getByRole('button', {
        name: 'Call it off for everyone. Everyone is told, nobody pays, and the court goes back to Bonarka Arena.',
      }),
    ).toBeTruthy();
    expect(
      within(sheet).getByRole('button', {
        name: 'Leave · the others play on. You pay nothing. Your friends keep the court; a seat still empty on Fri 16:00 calls the game off and nobody pays.',
      }),
    ).toBeTruthy();
  });

  it('says with Whole court that the sender still pays the court and is paid back', async () => {
    const sheet = await openTheSheet(withAnEmptySeat({ pay_mode: 'WHOLE_COURT' }));

    expect(
      within(sheet).getByText(
        'You still pay the court. Whoever takes your seat pays you 28 zł back.',
      ),
    ).toBeTruthy();
  });

  it('leaves and lets the others play on, told by the pay mode, back to Home', async () => {
    transport.on('POST', departurePath, () =>
      json<Wire['DepartureResponse']>({ left: 'BEFORE_THE_CUT_OFF' }),
    );
    const sheet = await openTheSheet(withAnEmptySeat({ pay_mode: 'WHOLE_COURT' }));

    fireEvent.press(within(sheet).getByRole('button', { name: /^Leave · the others play on/ }));

    await waitFor(() => expect(transport.requestsTo('POST', departurePath)).toHaveLength(1));
    await waitFor(() =>
      expect(toasts()).toEqual([['You left — the others play on. You still pay the court.', 'ok']]),
    );
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('POST', callOffPath)).toHaveLength(0);
  });

  it('calls it off for everyone from the same sheet', async () => {
    transport.on('POST', callOffPath, () => noContent());
    const sheet = await openTheSheet(withAnEmptySeat());

    fireEvent.press(within(sheet).getByRole('button', { name: /^Call it off for everyone/ }));

    await waitFor(() => expect(transport.requestsTo('POST', callOffPath)).toHaveLength(1));
    await waitFor(() => expect(toasts()).toEqual([[COPY.callOff.done, 'ok']]));
    expect(transport.requestsTo('POST', departurePath)).toHaveLength(0);
  });

  it('says a refused leave on the sheet, the two ways still there', async () => {
    transport.on('POST', departurePath, () => errorResponse(409, 'game_has_started'));
    const sheet = await openTheSheet(withAnEmptySeat());

    fireEvent.press(within(sheet).getByRole('button', { name: /^Leave · the others play on/ }));

    expect(await within(sheet).findByRole('alert')).toBeTruthy();
    expect(within(sheet).getByRole('button', { name: /^Call it off for everyone/ })).toBeTruthy();
  });

  it('is the ordinary late leave after the cut-off', async () => {
    await openDetails(withAnEmptySeat({ can_call_off: false }), {
      leaving: { kind: 'AFTER_THE_CUT_OFF', refund_grosze: 2700, card_fee_grosze: 100 },
    });

    fireEvent.press(await screen.findByRole('button', { name: LEAVE_THE_GAME }));

    expect(await screen.findByText(LEAVE_SHEET_TITLE)).toBeTruthy();
    expect(screen.queryByTestId('senders-leave-sheet')).toBeNull();
    expect(screen.queryByRole('button', { name: /^Leave · the others play on/ })).toBeNull();
    expect(screen.getAllByRole('button', { name: LEAVE_THE_GAME }).length).toBeGreaterThan(0);
  });

  it('turns ordinary at the cut-off on the read’s clock, Open and Call it off going with it', async () => {
    const lastMinute = '2026-10-02T13:59:00Z';
    jest.setSystemTime(Date.parse(lastMinute));
    const seats = await openDetails(withAnEmptySeat(), { ...beforeTheCutOff, read_at: lastMinute });
    expect(await within(seats).findByRole('button', { name: OPEN })).toBeTruthy();

    act(() => jest.advanceTimersByTime(2 * 60 * 1000));

    await waitFor(() => expect(screen.queryByRole('button', { name: OPEN })).toBeNull());
    expect(screen.getByRole('button', { name: INVITE })).toBeTruthy();
    expect(screen.queryByRole('button', { name: COPY.callOff.action })).toBeNull();
    fireEvent.press(screen.getByRole('button', { name: LEAVE_THE_GAME }));
    expect(await screen.findByText(LEAVE_SHEET_TITLE)).toBeTruthy();
    expect(screen.queryByTestId('senders-leave-sheet')).toBeNull();
  });

  it('is the ordinary leave for a friend on the game', async () => {
    await openDetails(asAFriendIn(), beforeTheCutOff);

    fireEvent.press(await screen.findByRole('button', { name: LEAVE_THE_GAME }));

    expect(await screen.findByText(LEAVE_SHEET_TITLE)).toBeTruthy();
    expect(screen.queryByTestId('senders-leave-sheet')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// A seat invitation on Home
// ---------------------------------------------------------------------------

describe('a seat invitation on Home', () => {
  it('shows in FRIENDS GAME like any invitation, the reader in the seat they are invited into', async () => {
    stubHomeGames(transport, [], {
      friends_games: [
        invitation({
          friends_game: invitedGame({
            seats: [
              seat(TOMEK, 'IN'),
              seat(ME, 'CANT_MAKE_IT', { seat_of: ANIA }),
              seat(MAGDA, 'IN'),
              seat(KAROL, 'IN'),
            ],
            friends_in: 2,
          }),
          sides: {
            yours: [tile(ME, 'ada', { is_you: true, friend: false }), tile(TOMEK, 'tomek.k')],
            theirs: [tile(MAGDA, 'magda.p'), tile(KAROL, 'karol.t', { friend: false })],
          },
        }),
      ],
    });
    await launchSignedIn();

    const row = await screen.findByTestId('friends-games');
    expect(within(row).getByText('tomek.k’s game')).toBeTruthy();
    expect(within(row).getByLabelText('tomek.k, in. magda.p, in. karol.t, in. You')).toBeTruthy();
    expect(
      within(row).getByRole('button', { name: 'Accept and pay 25 zł, tomek.k’s game' }),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Notices
// ---------------------------------------------------------------------------

describe('the notices that open the game (the mechanics §12)', () => {
  let phone: FakePush;

  beforeEach(() => {
    transport.on('POST', DEVICES_PATH, () => noContent());
    phone = fakePush();
    stubPush(phone);
  });

  const push = (kind: string) => ({
    notice_id: 'd0000000-0000-4000-8000-000000000760',
    kind,
    opens: 'BOOKING',
    game_id: BOOKING,
    pool_id: GROUP,
    sport: 'PADEL',
    game_kind: 'COMPETITIVE',
  });

  it('opens the cover warning on the game, with its three actions', async () => {
    stubTheGame(withAnEmptySeat());
    await launchSignedIn();

    act(() => phone.tap(push('COVER_WARNING')));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(await screen.findByRole('button', { name: INVITE })).toBeTruthy();
    expect(await screen.findByRole('button', { name: OPEN })).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.callOff.action })).toBeTruthy();
  });

  it('opens the game for somebody who left', async () => {
    stubTheGame(withAnEmptySeat({}, { state: 'EMPTY' }));
    await launchSignedIn();

    act(() => phone.tap(push('SOMEONE_LEFT')));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(await screen.findByLabelText('bartek.l, empty')).toBeTruthy();
  });

  it('opens the game for a seat taken first, as the friend once invited reads it', async () => {
    // karol.t took the seat the reader was invited into: every seat In, nothing the reader may do.
    const taken = withAnEmptySeat(
      {
        sender_id: PIOTR,
        sender_nickname: 'piotr.s',
        you_are_the_sender: false,
        can_call_off: false,
        seats: [seat(PIOTR, 'IN'), seat(INES, 'IN'), seat(BARTEK, 'IN'), seat(KAROL, 'IN')],
        friends_in: 3,
      },
      {},
    );
    stubHomeGames(transport, []);
    stubBooking(
      transport,
      bookingDetails({
        friends_game: taken,
        leaving: null,
        shows_forecast: false,
        sides: {
          yours: [tile(PIOTR, 'piotr.s'), tile(INES, 'ines.d')],
          theirs: [tile(BARTEK, 'bartek.l'), tile(KAROL, 'karol.t')],
        },
      }),
    );
    await launchSignedIn();

    act(() => phone.tap(push('INVITED_SEAT_TAKEN')));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    const seats = await screen.findByTestId('friends-seats');
    expect(within(seats).getByLabelText('karol.t, In')).toBeTruthy();
    expect(within(seats).queryAllByRole('button')).toHaveLength(0);
    expect(screen.queryByRole('button', { name: LEAVE_THE_GAME })).toBeNull();
  });
});
