/**
 * **The notices, walked the way a player meets them** — the real route tree and the real bar, with
 * only `fetch` and the phone faked ([#559](https://github.com/Raketa02/Raketa/issues/559); the screens
 * A7.2, A9; mocks 50, 52, 53; the mechanics §17.2).
 *
 * The server is #549's: `GET`/`PUT /players/me/notifications` (a save answers the three it saved),
 * `POST /players/me/devices` and `…/removal` (the token in the body), and `GET /players/me/notices`
 * (newest first, each in the words it was pushed in and with where a tap opens it) — with #621's
 * bell: the number since the last visit, each row's `new` and `your_own`, and
 * `POST /players/me/notices/visit` (#627). The phone is `fakePush()`: a permission the suite sets, a
 * token, and pushes that arrive or are tapped when the suite says so.
 */

import { focusManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Linking } from 'react-native';

import {
  FRIENDS_COPY,
  friendKeys,
  requestsHeading,
  wantsToBeYourFriend,
} from '@/features/friends/types';
import { gameKeys } from '@/features/games/types';
import { GROUPS_COPY } from '@/features/groups/types';
import { RECORD_TITLE } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { doorRowLabel, theme } from '@/shared/ui';
import {
  deckCard,
  DECK_READ_AT,
  groupDeck,
  proposalDetails,
  stubGroupDeck,
  stubProposal,
} from '@/test-support/groupDeck';
import {
  BOOKING,
  INES,
  bookedGameOnTheList,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
  unheldMoney,
} from '@/test-support/home';
import {
  DEVICES_PATH,
  DEVICE_REMOVAL_PATH,
  FRIENDS_PATH,
  GATE_USER,
  launchSignedIn,
  NOTICES_PATH,
  NOTICES_VISIT_PATH,
  NOTIFICATION_CHOICES_PATH,
  resetPush,
  stubGate,
  stubMyGroups,
  stubNotices,
  stubNotificationChoices,
  stubOwnRecord,
  stubProfileOptions,
  stubGames,
  stubProfileSurface,
  stubPush,
  stubRunsInProgress,
} from '@/test-support/onboardingRouter';
import { fakePush, PUSH_TOKEN, type FakePush } from '@/test-support/platform';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  noContent,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import type { RecentNotices } from '../domain/notice';
import { notificationKeys } from '../hooks/notificationKeys';

import { NOTIFICATIONS_COPY, NOTIFICATIONS_TITLE } from './notificationsCopy';

const COPY = NOTIFICATIONS_COPY;

/** One rated sport — a player past onboarding, whom the gate lets into the app. */
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

/** The crew — the group a notice's pool is filed under. */
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

let given = 0;

/**
 * A notice as the list serves it — *It's a game!* about the booked game, seen and somebody else's,
 * unless told otherwise.
 */
function notice(extra: Partial<Wire['NoticeSchema']> = {}): Wire['NoticeSchema'] {
  given += 1;
  return {
    notice_id: `d0000000-0000-4000-8000-${String(given).padStart(12, '0')}`,
    kind: 'GAME_BOOKED',
    title: 'It’s a game! · 30 zł held',
    body: 'Padel · Sat 16:00 · Bonarka Arena',
    given_at: '2026-10-02T12:05:00Z',
    opens: 'BOOKING',
    game_id: BOOKING,
    pool_id: CREW_ID,
    sport: 'PADEL',
    game_kind: 'COMPETITIVE',
    gathered: 0,
    new: false,
    your_own: false,
    player_id: null,
    ...extra,
  };
}

/** What a push carries — the backend's seven keys (`pushing.py`), off a listed notice. */
function payloadOf(wire: Wire['NoticeSchema']) {
  return {
    notice_id: wire.notice_id,
    kind: wire.kind,
    opens: wire.opens,
    game_id: wire.game_id,
    pool_id: wire.pool_id,
    sport: wire.sport,
    game_kind: wire.game_kind,
  };
}

let transport: Transport;
let phone: FakePush;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
  transport.on('POST', DEVICES_PATH, () => noContent());
  phone = fakePush();
  stubPush(phone);
});

afterEach(async () => {
  transport.restore();
  resetPush();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  jest.restoreAllMocks();
});

const registrations = () =>
  transport.requestsTo('POST', DEVICES_PATH).map((request) => request.body);

const saves = () => transport.requestsTo('PUT', NOTIFICATION_CHOICES_PATH).map((r) => r.body);

/** The app went to the background and came back — every foreground answer runs. */
async function backAndForth() {
  await act(async () => focusManager.setFocused(false));
  await act(async () => focusManager.setFocused(true));
}

/**
 * The session's first read of the list has landed — what it has seen from then on, and the line a
 * notice must be newer than to be drawn as the banner. **And reached the session**: TanStack hands
 * an answer to its observers on the next tick, so the cache holding it is not yet the hook having
 * seen it — a launch reaches here a beat sooner since the gate reads the player alone (#730).
 */
async function sessionReadTheList() {
  await waitFor(() => expect(queryClient.getQueryData(notificationKeys.notices())).toBeDefined());
  await act(async () => jest.advanceTimersByTime(1));
}

/** The server holds the three choices; a save replaces them and answers them. */
function serveChoices(held: Wire['NotificationChoicesSchema']) {
  let saved = held;
  stubNotificationChoices(transport, saved);
  transport.on('PUT', NOTIFICATION_CHOICES_PATH, (request: RecordedRequest) => {
    saved = request.body as Wire['NotificationChoicesSchema'];
    stubNotificationChoices(transport, saved);
    return json(saved);
  });
}

const rowLabel = (line: string) => doorRowLabel(NOTIFICATIONS_TITLE, line);

/** A signed-in player on Notifications, the row's line read on the way. */
async function onNotifications(rowLine = 'You complete it · Challenges') {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  fireEvent.press(await screen.findByLabelText(rowLabel(rowLine)));
  await screen.findByText(COPY.alwaysOn.rows[0]);
}

/** A choice's switch, by its title. */
const choice = (title: string) => screen.getByRole('switch', { name: new RegExp(`^${title}\\.`) });

// ---------------------------------------------------------------------------
// The row
// ---------------------------------------------------------------------------

describe('the Notifications row, in the ACCOUNT group', () => {
  it('says the choices that are on — two of three until changed — under Payments', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    const row = await screen.findByLabelText(rowLabel('You complete it · Challenges'));
    const rows = screen.getAllByRole('button').map((button) => button.props.accessibilityLabel);
    expect(rows.indexOf(row.props.accessibilityLabel)).toBe(
      rows.indexOf(doorRowLabel('Payments', 'Not set up')) + 1,
    );
  });

  it('says all three once all three are on, in the screen’s order', async () => {
    stubNotificationChoices(transport, { fill_in_alerts: true });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    expect(
      await screen.findByLabelText(rowLabel('You complete it · Challenges · Fill in alerts')),
    ).toBeTruthy();
  });

  it('says only the ones always on are left once all three are off', async () => {
    stubNotificationChoices(transport, { you_complete_it: false, challenges_for_you: false });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    expect(await screen.findByLabelText(rowLabel(COPY.noneChosen))).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The screen
// ---------------------------------------------------------------------------

describe('the Notifications screen', () => {
  // The screens A7.2 as #620 amends it, Q113 adds Fix your card, #663 the five steps at the
  // court, and Q121 takes the club's answer away: §17.2's always-on notices.
  it('lists the sixteen always on, each inert with its green tag (mock 52, #677)', async () => {
    const rows = [
      'It’s a game! · held',
      'Waiting for one payment',
      'Fix your card by … to keep your seat',
      'Confirm your payment by … to keep your seat',
      'Game called off · nothing was taken, or with the refund',
      'Someone left your game · or it’s filling again',
      'You’ve been refunded',
      'Your new game',
      'A game moved to another court',
      'A game you left',
      'Your post didn’t fill',
      '… is at the club and you’re not there yet',
      '… is at the club · who you said isn’t here yet',
      'How did it go? · your game’s hour has ended',
      'Is that right? · … put a score up, or changed it',
      'Was … at the club? · they say they were',
    ];
    await onNotifications();

    for (const row of rows) expect(screen.getByText(row)).toBeTruthy();
    // In the table's order, each one element to a listener.
    expect(
      screen.getAllByLabelText(/, always on$/).map((row) => row.props.accessibilityLabel),
    ).toEqual(rows.map((row) => `${row.split(' · ').join(', ')}, always on`));
    expect(screen.getAllByText(COPY.alwaysOn.tag)).toHaveLength(rows.length);
    // Words and a tag — never a control.
    expect(screen.queryByRole('button', { name: /always on/ })).toBeNull();
  });

  it('draws the three choices as switches, on and off as saved (mock 53)', async () => {
    await onNotifications();

    expect(choice('You complete it').props.accessibilityState).toMatchObject({ checked: true });
    expect(choice('Challenges for you').props.accessibilityState).toMatchObject({ checked: true });
    expect(choice('Fill in alerts').props.accessibilityState).toMatchObject({ checked: false });
    expect(screen.getByText(COPY.yourChoice.rows.fillInAlerts.line)).toBeTruthy();
    expect(within(choice('Fill in alerts')).getByText('Off')).toBeTruthy();
  });

  it('saves all three on a tap, turns the chip before the answer, and says it on the row', async () => {
    let saved: Wire['NotificationChoicesSchema'] = {
      you_complete_it: true,
      challenges_for_you: true,
      fill_in_alerts: false,
    };
    const held: (() => void)[] = [];
    stubNotificationChoices(transport, saved);
    transport.on('PUT', NOTIFICATION_CHOICES_PATH, (request: RecordedRequest) => {
      saved = request.body as Wire['NotificationChoicesSchema'];
      stubNotificationChoices(transport, saved);
      return new Promise<Response>((resolve) => held.push(() => resolve(json(saved))));
    });
    await onNotifications();

    fireEvent.press(choice('Fill in alerts'));

    // Turned while the save is still out — nothing has answered yet.
    await waitFor(() =>
      expect(choice('Fill in alerts').props.accessibilityState).toMatchObject({ checked: true }),
    );
    expect(saves()).toEqual([
      { you_complete_it: true, challenges_for_you: true, fill_in_alerts: true },
    ]);
    await act(async () => held.shift()?.());

    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(rowLabel('You complete it · Challenges · Fill in alerts')),
    ).toBeTruthy();
  });

  it('turns from the last tap: twice on one chip is off and on again, saved in order', async () => {
    serveChoices({ you_complete_it: true, challenges_for_you: true, fill_in_alerts: false });
    await onNotifications();

    fireEvent.press(choice('You complete it'));
    fireEvent.press(choice('You complete it'));

    await waitFor(() =>
      expect(saves()).toEqual([
        { you_complete_it: false, challenges_for_you: true, fill_in_alerts: false },
        { you_complete_it: true, challenges_for_you: true, fill_in_alerts: false },
      ]),
    );
    expect(choice('You complete it').props.accessibilityState).toMatchObject({ checked: true });
  });

  it('says a refused save, and draws what is saved again', async () => {
    stubNotificationChoices(transport);
    transport.on('PUT', NOTIFICATION_CHOICES_PATH, () => errorResponse(500, 'internal_error'));
    await onNotifications();

    fireEvent.press(choice('Challenges for you'));

    expect(await screen.findByRole('alert')).toBeTruthy();
    await waitFor(() =>
      expect(choice('Challenges for you').props.accessibilityState).toMatchObject({
        checked: true,
      }),
    );
  });
});

// ---------------------------------------------------------------------------
// The permission
// ---------------------------------------------------------------------------

describe('asking to show notifications', () => {
  it('offers Allow notifications at the top while the phone has not been asked', async () => {
    await onNotifications();

    expect(await screen.findByText(COPY.permission.ask.line)).toBeTruthy();
    expect(screen.getByRole('button', { name: COPY.permission.ask.button })).toBeTruthy();
  });

  it('asks only when pressed — never on launch, never on the way in', async () => {
    await onNotifications();
    await screen.findByText(COPY.permission.ask.line);

    expect(phone.state).toBe('undetermined');
    expect(registrations()).toEqual([]);
  });

  it('a yes takes the line away and registers this phone at once', async () => {
    await onNotifications();

    fireEvent.press(await screen.findByRole('button', { name: COPY.permission.ask.button }));

    await waitFor(() => expect(screen.queryByText(COPY.permission.ask.line)).toBeNull());
    expect(phone.state).toBe('granted');
    await waitFor(() => expect(registrations()).toEqual([{ token: PUSH_TOKEN }]));
  });

  it('a no keeps the line, and registers nothing', async () => {
    phone.answer = 'denied';
    await onNotifications();

    fireEvent.press(await screen.findByRole('button', { name: COPY.permission.ask.button }));

    await waitFor(() => expect(phone.state).toBe('denied'));
    expect(screen.getByText(COPY.permission.ask.line)).toBeTruthy();
    expect(registrations()).toEqual([]);
  });

  it('sends a phone that will never ask again to its settings, and reads it again on return', async () => {
    const settings = jest.spyOn(Linking, 'openSettings').mockResolvedValue(undefined);
    phone.state = 'blocked';
    await onNotifications();

    fireEvent.press(await screen.findByRole('button', { name: COPY.permission.blocked.button }));
    expect(settings).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button', { name: COPY.permission.ask.button })).toBeNull();

    // Switched on in Settings, and back.
    phone.state = 'granted';
    await backAndForth();

    await waitFor(() => expect(screen.queryByText(COPY.permission.blocked.line)).toBeNull());
    await waitFor(() => expect(registrations()).toEqual([{ token: PUSH_TOKEN }]));
  });

  it('draws no line for a phone that already may', async () => {
    phone.state = 'granted';
    await onNotifications();

    expect(screen.queryByText(COPY.permission.ask.line)).toBeNull();
    expect(screen.queryByText(COPY.permission.blocked.line)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The registration
// ---------------------------------------------------------------------------

describe('this phone, registered', () => {
  it('once on the way in when the phone may show a notice — the token in the body', async () => {
    phone.state = 'granted';
    await launchSignedIn();

    await waitFor(() => expect(registrations()).toEqual([{ token: PUSH_TOKEN }]));
    await backAndForth();
    expect(registrations()).toHaveLength(1);
  });

  it('never while the phone may not', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');
    await backAndForth();

    expect(phone.tokenReads).toBe(0);
    expect(registrations()).toEqual([]);
  });

  it('never for a phone with no token to give — no Expo project, an iPhone build without push', async () => {
    phone.state = 'granted';
    phone.token = null;
    await launchSignedIn();
    await waitFor(() => expect(phone.tokenReads).toBeGreaterThan(0));

    expect(registrations()).toEqual([]);
  });

  it('again when the system replaces the token', async () => {
    phone.state = 'granted';
    await launchSignedIn();
    await waitFor(() => expect(registrations()).toHaveLength(1));

    await act(async () => phone.rotate('ExponentPushToken[fake-phone-0002]'));

    await waitFor(() =>
      expect(registrations()).toEqual([
        { token: PUSH_TOKEN },
        { token: 'ExponentPushToken[fake-phone-0002]' },
      ]),
    );
  });

  it('again on the next return to the app when it failed', async () => {
    phone.state = 'granted';
    transport.on('POST', DEVICES_PATH, networkFailure());
    await launchSignedIn();
    await waitFor(() => expect(registrations()).toHaveLength(1));

    transport.on('POST', DEVICES_PATH, () => noContent());
    await backAndForth();

    await waitFor(() => expect(registrations()).toHaveLength(2));
  });

  it('is let go at sign-out, before the session ends', async () => {
    phone.state = 'granted';
    transport.on('POST', DEVICE_REMOVAL_PATH, () => noContent());
    transport.on('POST', '/api/v1/auth/logout', () => json({ message: 'Logged out successfully' }));
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    fireEvent.press(await screen.findByRole('button', { name: 'Sign out' }));

    await waitFor(() =>
      expect(transport.requestsTo('POST', DEVICE_REMOVAL_PATH).map((r) => r.body)).toEqual([
        { token: PUSH_TOKEN },
      ]),
    );
  });
});

// ---------------------------------------------------------------------------
// The banner
// ---------------------------------------------------------------------------

describe('a push while the app is open', () => {
  const BOOKED = notice();

  it('is drawn as a banner at the top, in the push’s own words', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() => phone.receive({ title: BOOKED.title, body: BOOKED.body, data: payloadOf(BOOKED) }));

    expect(await screen.findByText(BOOKED.title)).toBeTruthy();
    expect(screen.getByText(BOOKED.body)).toBeTruthy();
  });

  // Both reads are held for the session — Home's by the bar, the list by the banner — so each is
  // read again at once rather than marked for later.
  it('re-reads the list behind the bell and Home', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();
    const homeReads = transport.requestsTo('GET', '/api/v1/home').length;
    const listReads = transport.requestsTo('GET', NOTICES_PATH).length;

    act(() => phone.receive({ title: BOOKED.title, body: BOOKED.body, data: payloadOf(BOOKED) }));

    await waitFor(() =>
      expect(transport.requestsTo('GET', '/api/v1/home').length).toBeGreaterThan(homeReads),
    );
    await waitFor(() =>
      expect(transport.requestsTo('GET', NOTICES_PATH).length).toBeGreaterThan(listReads),
    );
  });

  it('is drawn once — the list read again after it does not draw it a second time', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();
    // The server lists it from now on — and answers the push's re-read only once it is told to.
    const held: (() => void)[] = [];
    transport.on(
      'GET',
      NOTICES_PATH,
      () =>
        new Promise<Response>((resolve) =>
          held.push(() =>
            resolve(
              json<Wire['RecentNoticesResponse']>({
                notices: [BOOKED],
                new_count: 0,
                last_opened_at: null,
              }),
            ),
          ),
        ),
    );

    act(() => phone.receive({ title: BOOKED.title, body: BOOKED.body, data: payloadOf(BOOKED) }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.banner.close }));
    await waitFor(() => expect(held).toHaveLength(1));
    await act(async () => held.shift()?.());

    await waitFor(() =>
      expect(
        queryClient.getQueryData<RecentNotices>(notificationKeys.notices())?.notices,
      ).toHaveLength(1),
    );
    // The read's answer handed to its observers — TanStack notifies on the next tick — and drawn.
    await act(async () => jest.advanceTimersByTime(1));
    expect(screen.queryByText(BOOKED.title)).toBeNull();
  });

  it('opens the game it is about when pressed — a booked game’s details', async () => {
    stubBooking(transport, bookingDetails());
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() => phone.receive({ title: BOOKED.title, body: BOOKED.body, data: payloadOf(BOOKED) }));
    fireEvent.press(await screen.findByRole('button', { name: `${BOOKED.title}. ${BOOKED.body}` }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(screen.queryByText(BOOKED.body)).toBeNull();
  });

  it('closes on its close control, and goes by itself after its time', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() => phone.receive({ title: BOOKED.title, body: BOOKED.body, data: payloadOf(BOOKED) }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.banner.close }));
    expect(screen.queryByText(BOOKED.title)).toBeNull();

    act(() => phone.receive({ title: BOOKED.title, body: BOOKED.body, data: payloadOf(BOOKED) }));
    expect(await screen.findByText(BOOKED.title)).toBeTruthy();
    act(() => jest.advanceTimersByTime(theme.motion.hold.notice));
    expect(screen.queryByText(BOOKED.title)).toBeNull();
  });

  it('opens nothing for a payload that is not a notice’s — and still says it', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() => phone.receive({ title: 'Raketa', body: 'Something', data: { opens: '../admin' } }));

    expect(await screen.findByText('Raketa')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Raketa. Something' })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The banner with no push
// ---------------------------------------------------------------------------

/**
 * A9 gives the in-app banner its own column beside the push: a player who never allowed
 * notifications — or on a phone that cannot be pushed yet, which today is every phone — is still told
 * while the app is open. The list behind the bell is the banner's second source.
 */
describe('a notice while the app is open, on a phone not pushed', () => {
  const LEFT = notice({ kind: 'SOMEONE_LEFT', title: 'Someone left your game' });

  it('is drawn from the list, read again within the minute', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();

    stubNotices(transport, [LEFT]);
    await act(async () => jest.advanceTimersByTime(60_000));

    expect(await screen.findByText(LEFT.title)).toBeTruthy();
    expect(screen.getByRole('button', { name: `${LEFT.title}. ${LEFT.body}` })).toBeTruthy();
  });

  it('is drawn on the way back to the app', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();

    // Away for longer than the list stays fresh, and back.
    stubNotices(transport, [LEFT]);
    await act(async () => jest.advanceTimersByTime(31_000));
    await backAndForth();

    expect(await screen.findByText(LEFT.title)).toBeTruthy();
  });

  it('draws nothing on launch for what was told while the app was closed', async () => {
    stubNotices(transport, [LEFT]);
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();
    await act(async () => jest.advanceTimersByTime(1));

    expect(screen.queryByText(LEFT.title)).toBeNull();
  });

  // Q101: the bell's number is the catch-up now — the line above, kept, and the number beside it.
  it('draws nothing on launch — the bell carries the count instead', async () => {
    stubNotices(transport, [{ ...LEFT, new: true }]);
    await launchSignedIn();
    await sessionReadTheList();

    expect(await screen.findByRole('button', { name: 'Recent notifications, 1 new' })).toBeTruthy();
    await act(async () => jest.advanceTimersByTime(1));
    expect(screen.queryByText(LEFT.title)).toBeNull();
  });

  // Q102: the yes that filled the game saw It's a game!; somebody else's act is still told.
  it('never draws the player’s own — the newest of somebody else’s is drawn instead', async () => {
    const OWN = notice({ title: 'It’s a game! · 40 zł held', your_own: true });
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();

    stubNotices(transport, [OWN, { ...LEFT, new: true }]);
    await act(async () => jest.advanceTimersByTime(60_000));

    expect(await screen.findByText(LEFT.title)).toBeTruthy();
    expect(screen.queryByText(OWN.title)).toBeNull();
  });

  it('lists the player’s own, and never draws it as the banner', async () => {
    const OWN = notice({ title: 'It’s a game! · 40 zł held', your_own: true });
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();

    stubNotices(transport, [OWN]);
    await act(async () => jest.advanceTimersByTime(60_000));
    await waitFor(() =>
      expect(
        queryClient.getQueryData<RecentNotices>(notificationKeys.notices())?.notices,
      ).toHaveLength(1),
    );
    await act(async () => jest.advanceTimersByTime(1));
    expect(screen.queryByText(OWN.title)).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: COPY.bell }));
    expect(await screen.findByText(OWN.title)).toBeTruthy();
  });

  // Q103: the minute's read used to leave Home as it was until the app had been away for longer
  // than Home stays fresh — the game a notice is about is there before it is tapped now.
  it('re-reads Home — the game a notice is about is on Home without leaving the app', async () => {
    const MATCHED = notice({
      title: 'It’s a game! · 25 zł held',
      body: 'Padel · Fri 19:00 at Kazimierz Padel.',
      new: true,
    });
    await launchSignedIn();
    await screen.findByLabelText('You');
    await sessionReadTheList();
    expect(screen.queryByTestId(`home-game-${BOOKING}`)).toBeNull();

    stubHomeGames(transport, [homeGame()]);
    stubNotices(transport, [MATCHED]);
    await act(async () => jest.advanceTimersByTime(60_000));

    expect(await screen.findByTestId(`home-game-${BOOKING}`)).toBeTruthy();
  });

  it('is not read every minute on a phone that is pushed', async () => {
    phone.state = 'granted';
    await launchSignedIn();
    await waitFor(() => expect(registrations()).toHaveLength(1));
    const listReads = transport.requestsTo('GET', NOTICES_PATH).length;

    await act(async () => jest.advanceTimersByTime(120_000));

    expect(transport.requestsTo('GET', NOTICES_PATH)).toHaveLength(listReads);
  });
});

// ---------------------------------------------------------------------------
// The bell's number, and the visit that clears it
// ---------------------------------------------------------------------------

/**
 * Q101: the bell counts the notices since the player last opened the list — the server's number,
 * the same on every phone. Opening the list clears it, and the rows that came since the last visit
 * stand out on that visit.
 */
describe('the bell’s number', () => {
  /**
   * The server's bell, as #621 keeps it: the notices in the order they reached the list, and how
   * many of them the last visit had listed. A row is new past that place unless it is the player's
   * own, and the number counts the new ones.
   */
  function serveTheBell(...told: Wire['NoticeSchema'][]) {
    const reached = [...told];
    let seenThrough = 0;
    transport.on('GET', NOTICES_PATH, () => {
      const notices = reached
        .map((row, place) => ({ ...row, new: place >= seenThrough && !row.your_own }))
        .reverse();
      return json<Wire['RecentNoticesResponse']>({
        notices,
        new_count: notices.filter((row) => row.new).length,
        last_opened_at: null,
      });
    });
    transport.on('POST', NOTICES_VISIT_PATH, () => {
      seenThrough = reached.length;
      return noContent();
    });
    return {
      /** Opened on another phone, before this one was picked up. */
      visited: () => {
        seenThrough = reached.length;
      },
      tell: (row: Wire['NoticeSchema']) => reached.push(row),
    };
  }

  const visits = () => transport.requestsTo('POST', NOTICES_VISIT_PATH).length;
  const heldList = () => queryClient.getQueryData<RecentNotices>(notificationKeys.notices());
  const bell = (named: string) => screen.findByRole('button', { name: named });
  /** The figure drawn on the bell — hidden from a listener, who hears it on the bell's name. */
  const drawnOn = (button: ReturnType<typeof screen.getByRole>) =>
    within(button).queryAllByText(/^\d+\+?$/, { includeHiddenElements: true });

  /** The rows of the open list, as a listener hears them. */
  const rowsHeard = async () =>
    (await screen.findAllByRole('button', { name: /Padel/ })).map(
      (row) => row.props.accessibilityLabel as string,
    );

  // Marta's morning (S-01B): one left overnight, two more by lunchtime.
  const MONDAY = notice({ title: 'You’ve been refunded', body: 'Padel · Mon 19:00 · 27,18 zł' });
  const IVAN_LEFT = notice({ title: 'Someone left your game', body: 'Padel · Tue 19:00' });
  const FILLED = notice({ title: 'Your seat is filled again', body: 'Padel · Tue 19:00' });
  const SEAT_OPEN = notice({ title: 'A seat opened', body: 'Padel · Thu 18:00' });

  it('shows nothing while nothing is new — however much is listed', async () => {
    serveTheBell(MONDAY).visited();
    await launchSignedIn();
    await sessionReadTheList();
    await act(async () => jest.advanceTimersByTime(1));

    expect(drawnOn(await bell(COPY.bell))).toHaveLength(0);
  });

  it('counts what reached the list since the last visit — 1 at eight, 3 by lunchtime', async () => {
    const server = serveTheBell(MONDAY);
    server.visited();
    server.tell(IVAN_LEFT);
    await launchSignedIn();

    const morning = await bell('Recent notifications, 1 new');
    expect(drawnOn(morning).map((figure) => figure.props.children)).toEqual(['1']);

    server.tell(FILLED);
    server.tell(SEAT_OPEN);
    await act(async () => jest.advanceTimersByTime(60_000));

    const lunchtime = await bell('Recent notifications, 3 new');
    expect(drawnOn(lunchtime).map((figure) => figure.props.children)).toEqual(['3']);
  });

  it('writes 99+ above 99, and says the exact number', async () => {
    stubNotices(transport, [{ ...IVAN_LEFT, new: true }], { newCount: 120 });
    await launchSignedIn();

    const button = await bell('Recent notifications, 120 new');
    expect(drawnOn(button).map((figure) => figure.props.children)).toEqual(['99+']);
  });

  it('is cleared by opening the list — whose rows since the last visit stand out on that visit and not on the next', async () => {
    const server = serveTheBell(MONDAY);
    server.visited();
    server.tell(IVAN_LEFT);
    server.tell(FILLED);
    await launchSignedIn();

    fireEvent.press(await bell('Recent notifications, 2 new'));
    await waitFor(() => expect(screen).toHavePathname('/notices'));
    // The visit has landed: none is new to the server any more, and the two still stand out for
    // as long as the list is open.
    await waitFor(() => expect(visits()).toBe(1));
    await waitFor(() => expect(heldList()?.newCount).toBe(0));
    expect(heldList()?.notices.some((row) => row.isNew)).toBe(false);
    await act(async () => jest.advanceTimersByTime(1));
    expect(await rowsHeard()).toEqual([
      expect.stringMatching(/^New\. Your seat is filled again\./),
      expect.stringMatching(/^New\. Someone left your game\./),
      expect.stringMatching(/^You’ve been refunded\./),
    ]);

    fireEvent.press(await screen.findByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(drawnOn(await bell(COPY.bell))).toHaveLength(0);

    fireEvent.press(await bell(COPY.bell));
    await waitFor(() => expect(visits()).toBe(2));
    expect(await rowsHeard()).toEqual([
      expect.stringMatching(/^Your seat is filled again\./),
      expect.stringMatching(/^Someone left your game\./),
      expect.stringMatching(/^You’ve been refunded\./),
    ]);
  });

  it('stays clear for a notice that reaches the open list — it stands out there instead', async () => {
    const server = serveTheBell(MONDAY);
    await launchSignedIn();
    fireEvent.press(await bell('Recent notifications, 1 new'));
    await waitFor(() => expect(visits()).toBe(1));

    server.tell(IVAN_LEFT);
    await act(async () => jest.advanceTimersByTime(60_000));

    await waitFor(() => expect(visits()).toBe(2));
    // It comes down as the banner too, over the list, as it would over any screen.
    fireEvent.press(await screen.findByRole('button', { name: COPY.banner.close }));
    expect(await rowsHeard()).toEqual([
      expect.stringMatching(/^New\. Someone left your game\./),
      expect.stringMatching(/^New\. You’ve been refunded\./),
    ]);
    fireEvent.press(await screen.findByLabelText('Back'));
    expect(drawnOn(await bell(COPY.bell))).toHaveLength(0);
  });

  it('keeps its number when the read the list opens on fails — no visit is sent', async () => {
    const server = serveTheBell(MONDAY);
    server.visited();
    server.tell(IVAN_LEFT);
    await launchSignedIn();
    await bell('Recent notifications, 1 new');

    transport.on('GET', NOTICES_PATH, () => errorResponse(503, 'unavailable'));
    fireEvent.press(await bell('Recent notifications, 1 new'));
    // Past the read's two retries, each armed once the one before it has failed.
    for (let retry = 0; retry < 3; retry += 1) {
      await act(async () => jest.advanceTimersByTime(8_000));
    }
    await waitFor(() =>
      expect(queryClient.getQueryState(notificationKeys.notices())?.status).toBe('error'),
    );
    // The failure handed to the open list — TanStack notifies on the next tick.
    await act(async () => jest.advanceTimersByTime(1));

    expect(visits()).toBe(0);
    fireEvent.press(await screen.findByLabelText('Back'));
    expect(await bell('Recent notifications, 1 new')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The list behind the bell
// ---------------------------------------------------------------------------

describe('the recent notices, behind the bell on Home', () => {
  /** On the list, read at `now` — set once the harness's clock is the suite's. */
  async function onTheList(now = Date.parse('2026-10-02T16:30:00Z')) {
    await launchSignedIn();
    jest.setSystemTime(now);
    fireEvent.press(await screen.findByRole('button', { name: COPY.bell }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));
  }

  it('lists them newest first, in the words they were pushed in, with when', async () => {
    stubNotices(transport, [
      notice({
        title: 'Someone left your game',
        body: 'Padel · Sat 16:00',
        given_at: '2026-10-02T12:05:00Z',
      }),
      notice({
        title: 'You’ve been refunded',
        body: '27,18 zł back',
        given_at: '2026-10-01T20:00:00Z',
      }),
    ]);
    await onTheList();

    const rows = await screen.findAllByRole('button', { name: /Padel · Sat 16:00|zł back/ });
    expect(rows.map((row) => row.props.accessibilityLabel)).toEqual([
      'Someone left your game. Padel · Sat 16:00. 14:05',
      'You’ve been refunded. 27,18 zł back. Yesterday 22:00',
    ]);
  });

  it('says so when nothing has been told yet', async () => {
    await onTheList();

    expect(await screen.findByText(COPY.list.empty)).toBeTruthy();
  });

  it('opens a booked game’s details over the list — back is the list', async () => {
    stubNotices(transport, [notice()]);
    stubBooking(transport, bookingDetails());
    await onTheList();

    fireEvent.press(await screen.findByRole('button', { name: /^It’s a game!/ }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    fireEvent.press(await screen.findByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/notices'));
  });

  it('opens a game still filling in its group — or one that did not fill', async () => {
    const card = deckCard();
    stubNotices(transport, [
      notice({
        kind: 'POST_DID_NOT_FILL',
        title: 'Your post didn’t fill',
        opens: 'PROPOSAL',
        game_id: card.proposal_id,
      }),
    ]);
    stubProposal(transport, card.proposal_id, proposalDetails(card, { pool_id: CREW_ID }));
    stubGroupDeck(transport, CREW_ID, groupDeck({ cards: [card] }));
    await onTheList();

    fireEvent.press(await screen.findByRole('button', { name: /^Your post didn’t fill/ }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${card.proposal_id}`),
    );
  });

  it('opens the group’s deck with the card on top — You complete it', async () => {
    const first = deckCard();
    const waiting = deckCard({ open_seats_after_your_yes: 0, court: 'BOOK_IT_NOW' });
    stubNotices(transport, [
      notice({
        kind: 'YOU_COMPLETE_IT',
        title: 'You complete it',
        opens: 'DECK',
        game_id: waiting.proposal_id,
      }),
    ]);
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW_ID}`, () => json(CREW_PAGE));
    stubGroupDeck(transport, CREW_ID, groupDeck({ cards: [first, waiting] }));
    stubProposal(transport, waiting.proposal_id, proposalDetails(waiting, { pool_id: CREW_ID }));
    await onTheList(DECK_READ_AT);

    fireEvent.press(await screen.findByRole('button', { name: /^You complete it/ }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}`));

    // The card the notice was about is the one on top: its details are the ones the deck opens.
    fireEvent.press(await screen.findByRole('button', { name: 'Game details' }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${waiting.proposal_id}`),
    );
  });

  // Q125: Info is pushed over the page, so the deck it was opened at is still the page under it.
  it('keeps the deck at the card under Info — back from Info, the card is still on top', async () => {
    const first = deckCard();
    const waiting = deckCard({ open_seats_after_your_yes: 0, court: 'BOOK_IT_NOW' });
    stubNotices(transport, [
      notice({
        kind: 'YOU_COMPLETE_IT',
        title: 'You complete it',
        opens: 'DECK',
        game_id: waiting.proposal_id,
      }),
    ]);
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW_ID}`, () => json(CREW_PAGE));
    stubGroupDeck(transport, CREW_ID, groupDeck({ cards: [first, waiting] }));
    stubProposal(transport, waiting.proposal_id, proposalDetails(waiting, { pool_id: CREW_ID }));
    await onTheList(DECK_READ_AT);
    fireEvent.press(await screen.findByRole('button', { name: /^You complete it/ }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}`));

    fireEvent.press(await screen.findByHintText(GROUPS_COPY.group.openInfo));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}/info`));
    fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.info.back }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}`));

    expect(await screen.findByRole('button', { name: /^Games/, selected: true })).toBeTruthy();
    fireEvent.press(await screen.findByRole('button', { name: 'Game details' }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${waiting.proposal_id}`),
    );
  });

  it('opens a Challenge in the kind it was dealt in, the card on top — the switch moved to it', async () => {
    const first = deckCard({ kind: 'FOR_FUN' });
    const challenge = deckCard({ kind: 'FOR_FUN', type: 'CHALLENGE' });
    stubNotices(transport, [
      notice({
        kind: 'CHALLENGE',
        title: 'Ola challenges you',
        opens: 'DECK',
        game_id: challenge.proposal_id,
        game_kind: 'FOR_FUN',
      }),
    ]);
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW_ID}`, () => json(CREW_PAGE));
    stubGroupDeck(transport, CREW_ID, (kind) =>
      groupDeck({
        kind: kind ?? 'COMPETITIVE',
        segments: [
          { kind: 'COMPETITIVE', count: 0 },
          { kind: 'FOR_FUN', count: 2 },
        ],
        cards: kind === 'FOR_FUN' ? [first, challenge] : [],
      }),
    );
    stubProposal(
      transport,
      challenge.proposal_id,
      proposalDetails(challenge, { pool_id: CREW_ID }),
    );
    await onTheList(DECK_READ_AT);

    fireEvent.press(await screen.findByRole('button', { name: /^Ola challenges you/ }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}`));

    expect(
      await screen.findByRole('button', { name: 'For fun, 2 games', selected: true }),
    ).toBeTruthy();
    fireEvent.press(await screen.findByRole('button', { name: 'Game details' }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${challenge.proposal_id}`),
    );
  });

  // Sent as BOOKING — the booked game — to a reader who is not in it: its open seat, from outside.
  it('opens a Fill in alert’s open seat, seen from outside, in its group', async () => {
    stubNotices(transport, [
      notice({ kind: 'FILL_IN_ALERT', title: 'A game you fit needs one more' }),
    ]);
    stubBooking(transport, bookingDetails());
    await onTheList();

    fireEvent.press(await screen.findByRole('button', { name: /^A game you fit needs one more/ }));

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}/rescue/${BOOKING}`));
  });

  it('lists a notice about a sport this build cannot name, and opens nothing', async () => {
    stubNotices(transport, [notice({ sport: 'PICKLEBALL' as Wire['Sport'] })]);
    await onTheList();

    expect(await screen.findByText(notice().title)).toBeTruthy();
    expect(screen.queryByRole('button', { name: /^It’s a game!/ })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// It's a game! while one payment is awaited, and the new card after a club's cancel
// ---------------------------------------------------------------------------

/**
 * Q110 and Q107 (#622, #625): the four matched while one payment is missing are told *It's a game! ·
 * waiting for one payment …*, which opens the game — still the proposal's, nobody paid; and after a
 * club's cancel called a game off, the new card first is told as *Your new game*, which opens the
 * deck with it on top. Each is opened the same way from the banner and from its row behind the bell.
 */
describe('It’s a game! while one payment is awaited, and Your new game (Q110, Q107)', () => {
  const MATCHED = deckCard({
    in_count: 4,
    open_seats_after_your_yes: 0,
    club: { id: 'c0000000-0000-4000-8000-000000000009', name: 'Kazimierz Padel' },
  });
  const AWAITED = notice({
    kind: 'WAITING_FOR_A_PAYMENT',
    title: 'It’s a game! · waiting for one payment until 14:40',
    body: 'Padel · Fri 19:00 at Kazimierz Padel. Nobody pays until it’s in.',
    opens: 'PROPOSAL',
    game_id: MATCHED.proposal_id,
    new: true,
  });

  const FIRST = deckCard();
  const REDEALT = deckCard({ open_seats_after_your_yes: 1 });
  const NEW_GAME = notice({
    kind: 'NEW_GAME',
    title: 'Your new game · Fri 19:00 at Bonarka Arena',
    body: 'The same players · 40 zł a share — say yes to book it.',
    opens: 'DECK',
    game_id: REDEALT.proposal_id,
    new: true,
  });

  beforeEach(() => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW_ID}`, () => json(CREW_PAGE));
    stubGroupDeck(transport, CREW_ID, groupDeck({ cards: [FIRST, REDEALT] }));
    stubProposal(
      transport,
      MATCHED.proposal_id,
      proposalDetails(MATCHED, {
        pool_id: CREW_ID,
        status: 'WAITING_FOR_A_PAYMENT',
        actions: ['LEAVE'],
      }),
    );
    stubProposal(transport, REDEALT.proposal_id, proposalDetails(REDEALT, { pool_id: CREW_ID }));
  });

  /** Signed in on Home at the deck's read, the list read once, and then told this. */
  async function told(wire: Wire['NoticeSchema']) {
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    await screen.findByLabelText('You');
    await sessionReadTheList();
    stubNotices(transport, [wire], { newCount: 1 });
    await act(async () => jest.advanceTimersByTime(60_000));
  }

  /** The card on top is the one the notice was about: its details are the ones the deck opens. */
  async function onTopOfTheDeck(card: Wire['DeckCardSchema']) {
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}`));
    fireEvent.press(await screen.findByRole('button', { name: 'Game details' }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${card.proposal_id}`),
    );
  }

  it('the banner It’s a game! · waiting for one payment opens the game, nobody paid yet', async () => {
    await told(AWAITED);

    fireEvent.press(
      await screen.findByRole('button', { name: `${AWAITED.title}. ${AWAITED.body}` }),
    );

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${MATCHED.proposal_id}`),
    );
    expect(await screen.findByRole('header', { name: 'Waiting for one payment' })).toBeTruthy();
  });

  it('its row behind the bell opens the game too — back is the list', async () => {
    stubNotices(transport, [AWAITED], { newCount: 1 });
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));

    fireEvent.press(await screen.findByRole('button', { name: /^New\. It’s a game! · waiting/ }));

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${MATCHED.proposal_id}`),
    );
    expect(await screen.findByRole('header', { name: 'Waiting for one payment' })).toBeTruthy();
    fireEvent.press(await screen.findByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/notices'));
  });

  it('the banner Your new game opens the deck with the new card on top', async () => {
    await told(NEW_GAME);

    fireEvent.press(
      await screen.findByRole('button', { name: `${NEW_GAME.title}. ${NEW_GAME.body}` }),
    );

    await onTopOfTheDeck(REDEALT);
  });

  it('its row behind the bell opens the deck with the new card on top', async () => {
    stubNotices(transport, [NEW_GAME], { newCount: 1 });
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));

    fireEvent.press(await screen.findByRole('button', { name: /^New\. Your new game/ }));

    await onTopOfTheDeck(REDEALT);
  });

  it('a push of either, tapped, opens the same place', async () => {
    phone.tap(payloadOf(NEW_GAME));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);

    await onTopOfTheDeck(REDEALT);

    act(() => phone.tap(payloadOf(AWAITED)));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW_ID}/game/${MATCHED.proposal_id}`),
    );
  });
});

// ---------------------------------------------------------------------------
// Each step at the court
// ---------------------------------------------------------------------------

/**
 * #663's five, about a Competitive booked game — *isn't here yet*, *they're at the club*, *How did it
 * go?*, *Is that right?* and *were they there?* — each opening the game's result screen, where the
 * person it waits on acts: from a row behind the bell, the banner, or the phone's own notification.
 * Saturday 3 October, padel 16:00–17:00 at Bonarka Arena; the words are the backend's (`words.py`).
 */
describe('each step at the court opens the game’s result screen (#663)', () => {
  const RESULT = `/booking/${BOOKING}/result`;

  /** 16:10 in Warsaw — the first half hour; 17:05, the hour just ended; the next morning. */
  const AT_THE_COURT = '2026-10-03T14:10:00Z';
  const HOUR_ENDED = '2026-10-03T15:05:00Z';
  const NEXT_MORNING = '2026-10-04T07:00:00Z';

  const NOT_HERE_YET = notice({
    kind: 'NOT_HERE_YET',
    opens: 'RESULT',
    title: "ines.d is at Bonarka Arena and you're not there yet",
    body: "Tap I'm here when you arrive — Padel · Sat 16:00.",
  });
  const AT_THE_CLUB = notice({
    kind: 'AT_THE_CLUB',
    opens: 'RESULT',
    title: 'bartek.l is at Bonarka Arena',
    body: 'Padel · Sat 16:00 — arrived at 16:12.',
  });
  const HOW_DID_IT_GO = notice({
    kind: 'HOW_DID_IT_GO',
    opens: 'RESULT',
    title: 'How did it go?',
    body: 'Padel · Sat 16:00 · Bonarka Arena — put the score up.',
  });
  const IS_THAT_RIGHT = notice({
    kind: 'IS_THAT_RIGHT',
    opens: 'RESULT',
    title: 'Is that right? · ines.d put a score up',
    body: 'Padel · Sat 16:00 at Bonarka Arena. If nobody answers by 17:30 tomorrow, it becomes the result — saying nothing costs nothing.',
  });
  const WERE_THEY_THERE = notice({
    kind: 'WERE_THEY_THERE',
    opens: 'RESULT',
    title: 'Was bartek.l at Bonarka Arena?',
    body: 'bartek.l tapped I was there for Padel · Sat 16:00 — confirm it by 16:30 tomorrow if so.',
  });
  const STEPS = [NOT_HERE_YET, AT_THE_CLUB, HOW_DID_IT_GO, IS_THAT_RIGHT, WERE_THEY_THERE];

  /** A row's name begins with its notice's words, which carry `?` and `.` — matched as written. */
  const startingWith = (words: string) =>
    new RegExp(`^${words.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`);

  /** Inés's 6–4 6–3, waiting for the reader's side until 17:30 tomorrow. */
  const INES_SCORE: Wire['StandingProposalSchema'] = {
    side: 'B',
    proposed_by: INES,
    score: {
      sets: [
        { a: 6, b: 4 },
        { a: 6, b: 3 },
      ],
    },
    proposed_at: '2026-10-03T15:30:00Z',
    answer_by: '2026-10-04T15:30:00Z',
  };

  /** The server at 17:05: the hour just ended, its result still to be put up. */
  function hourJustEnded() {
    stubBooking(transport, bookingDetails({ status: 'NEEDS_RESULT', read_at: HOUR_ENDED }));
    stubGames(transport, [bookedGameOnTheList()], HOUR_ENDED);
  }

  it('lists all five, each opening the game’s result screen — back is the list', async () => {
    stubNotices(transport, STEPS);
    hourJustEnded();
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: COPY.bell }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));

    for (const step of STEPS) {
      fireEvent.press(await screen.findByRole('button', { name: startingWith(step.title) }));
      await waitFor(() => expect(screen).toHavePathname(RESULT));
      fireEvent.press(await screen.findByLabelText('Back'));
      await waitFor(() => expect(screen).toHavePathname('/notices'));
    }
  });

  it('the banner Isn’t here yet opens the result screen with I’m here ready', async () => {
    stubBooking(transport, bookingDetails({ status: 'NEEDS_RESULT', read_at: AT_THE_COURT }));
    stubGames(
      transport,
      [
        bookedGameOnTheList({
          standing: 'NOT_HERE_YET',
          attendance: [
            {
              player_id: GATE_USER.id,
              nickname: GATE_USER.nickname ?? 'Ada',
              state: 'WAITING',
              noted_at: '2026-10-03T14:05:00Z',
              arrive_by: '2026-10-03T14:30:00Z',
              arrived_at: null,
              claim_by: '2026-10-04T14:30:00Z',
              claimed_at: null,
              confirmed_at: null,
            },
          ],
        }),
      ],
      AT_THE_COURT,
    );
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() =>
      phone.receive({
        title: NOT_HERE_YET.title,
        body: NOT_HERE_YET.body,
        data: payloadOf(NOT_HERE_YET),
      }),
    );
    fireEvent.press(
      await screen.findByRole('button', { name: `${NOT_HERE_YET.title}. ${NOT_HERE_YET.body}` }),
    );

    await waitFor(() => expect(screen).toHavePathname(RESULT));
    expect(await screen.findByRole('header', { name: 'Are you here?' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'I’m here' })).toBeTruthy();
  });

  // The result screen read the game before the score went up, and that read is held fresh past
  // every clock jump the harness makes on a navigation — so only the tap marking it stale draws the
  // score Is that right? is about.
  it('a push of Is that right?, tapped, opens the score put up — not the read from before it', async () => {
    stubNotices(transport, [HOW_DID_IT_GO]);
    hourJustEnded();
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: COPY.bell }));
    fireEvent.press(await screen.findByRole('button', { name: startingWith(HOW_DID_IT_GO.title) }));
    await waitFor(() => expect(screen).toHavePathname(RESULT));
    expect(await screen.findByRole('button', { name: /Send this score/ })).toBeTruthy();
    const before = queryClient.getQueryData(gameKeys.list());
    fireEvent.press(await screen.findByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/notices'));
    queryClient.removeQueries({ queryKey: gameKeys.list() });
    queryClient.getQueryCache().build(queryClient, { queryKey: gameKeys.list(), gcTime: Infinity });
    queryClient.setQueryData(gameKeys.list(), before, { updatedAt: Date.now() + 10 * 60_000 });

    stubBooking(
      transport,
      bookingDetails({ status: 'CONFIRM_THE_RESULT', needs_you: true, read_at: NEXT_MORNING }),
    );
    stubGames(
      transport,
      [
        bookedGameOnTheList({
          standing: 'AWAITING_ANSWER',
          played_at: '2026-10-03T15:30:00Z',
          entry_closes_at: null,
          proposals: [INES_SCORE],
        }),
      ],
      NEXT_MORNING,
    );
    act(() => phone.tap(payloadOf(IS_THAT_RIGHT)));

    await waitFor(() => expect(screen).toHavePathname(RESULT));
    expect(await screen.findByText('That’s right')).toBeTruthy();
  });

  it('a push of Were they there?, tapped, opens the result screen once the app is in', async () => {
    hourJustEnded();
    phone.tap(payloadOf(WERE_THEY_THERE));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(RESULT));
  });
});

// ---------------------------------------------------------------------------
// A push tapped
// ---------------------------------------------------------------------------

describe('a push tapped on the phone', () => {
  it('opens its game once the app is in — the tap that started it', async () => {
    stubBooking(transport, bookingDetails());
    phone.tap(payloadOf(notice()));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  });

  it('opens its game over wherever the player is', async () => {
    stubBooking(transport, bookingDetails());
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    await waitFor(() => expect(screen).toHavePathname('/you'));

    act(() => phone.tap(payloadOf(notice())));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    fireEvent.press(await screen.findByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/you'));
  });

  it('opens nothing for a payload that is not a notice’s', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() => phone.tap({ opens: 'BOOKING', game_id: 'not-a-game' }));

    expect(screen).toHavePathname('/');
  });
});

// ---------------------------------------------------------------------------
// Game moved (#677)
// ---------------------------------------------------------------------------

describe('Game moved — a club moved the booked game to another court (#677)', () => {
  const MOVED = notice({
    kind: 'GAME_MOVED',
    title: 'Bonarka Arena moved your game to Court 3 · Thu 19:00',
    body: 'Court 2 can’t be played · Padel · indoor · nothing else changes',
    opens: 'BOOKING',
    game_id: BOOKING,
    new: true,
  });

  beforeEach(() => {
    stubBooking(transport, bookingDetails());
  });

  it('the banner opens the booked game, on the court it moved to', async () => {
    stubBooking(transport, bookingDetails({ court_name: 'Court 3', indoor: true }));
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() => phone.receive({ title: MOVED.title, body: MOVED.body, data: payloadOf(MOVED) }));
    fireEvent.press(await screen.findByRole('button', { name: `${MOVED.title}. ${MOVED.body}` }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(await screen.findByText(/Court 3 · indoor/)).toBeTruthy();
  });

  it('its row behind the bell opens the booked game too — back is the list', async () => {
    stubNotices(transport, [MOVED], { newCount: 1 });
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));

    fireEvent.press(await screen.findByRole('button', { name: /^New\. Bonarka Arena moved/ }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    fireEvent.press(await screen.findByLabelText('Back'));
    await waitFor(() => expect(screen).toHavePathname('/notices'));
  });

  it('a push of it, tapped, opens the booked game', async () => {
    await launchSignedIn();
    await screen.findByLabelText('You');

    act(() => phone.tap(payloadOf(MOVED)));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
  });
});

// ---------------------------------------------------------------------------
// Get your level (#727, #731)
// ---------------------------------------------------------------------------

/**
 * **A notice about no game opens Home** (#731; ADR-0200 §7; the screens A9): *Get your level so your
 * groups can deal you games.*, told once per account to a member of a group still rated in nothing,
 * lands on Home — where the card is that opens the picker. The backend pushes three keys for it
 * (`pushing.py`): its id, its kind and Home, and no game.
 */
describe('Get your level — a notice about no game, opening Home', () => {
  const LEVEL = notice({
    kind: 'GET_YOUR_LEVEL',
    title: 'Get your level so your groups can deal you games.',
    body: 'Pick the sports you play — a few questions each.',
    opens: 'HOME',
    game_id: null,
    pool_id: null,
    sport: null,
    game_kind: null,
    new: true,
  });

  const PUSHED = { notice_id: LEVEL.notice_id, kind: LEVEL.kind, opens: 'HOME' };

  /** Ania, rated in nothing, in the crew — Home's card is drawn for her. */
  beforeEach(() => {
    stubGate(transport, { ratings: [], hasPlayerProfile: true });
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW_ID}`, () => json(CREW_PAGE));
  });

  it('its row behind the bell opens Home, on its card', async () => {
    stubNotices(transport, [LEVEL], { newCount: 1 });
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));

    fireEvent.press(await screen.findByRole('button', { name: /^New\. Get your level so/ }));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByText('Get your level')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Pick your sports' })).toBeTruthy();
    // Home itself, not a second Home pushed over the list: there is nothing to go back to.
    expect(screen.queryByLabelText('Back')).toBeNull();
  });

  it('the banner opens Home, from wherever she is', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    await waitFor(() => expect(screen).toHavePathname('/play'));

    act(() => phone.receive({ title: LEVEL.title, body: LEVEL.body, data: PUSHED }));
    fireEvent.press(await screen.findByRole('button', { name: `${LEVEL.title}. ${LEVEL.body}` }));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByRole('button', { name: 'Pick your sports' })).toBeTruthy();
  });

  it('a push of it, tapped, opens Home over wherever she is', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    await waitFor(() => expect(screen).toHavePathname('/you'));

    act(() => phone.tap(PUSHED));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByRole('button', { name: 'Pick your sports' })).toBeTruthy();
  });

  it('a push of it, tapped, opens the app on Home', async () => {
    phone.tap(PUSHED);

    await launchSignedIn();

    expect(await screen.findByRole('button', { name: 'Pick your sports' })).toBeTruthy();
    expect(screen).toHavePathname('/');
  });
});

// ---------------------------------------------------------------------------
// A friend's notices (#753, on #745's)
// ---------------------------------------------------------------------------

/**
 * **A friend request opens Home, and *You're friends* opens the friend's record** (the friends
 * mechanics §12). The backend pushes the person each names as `player_id` — a request opens Home,
 * where its card is; *You're friends* opens `RECORD`, a sheet drawn over wherever the player is,
 * since a record is not a screen.
 */
describe('a friend’s notices', () => {
  const ASKED: Wire['HomeFriendRequestSchema'] = {
    player_id: INES,
    nickname: 'ines.d',
    photo_id: null,
    photo_url: null,
    asked_at: '2026-10-02T12:00:00Z',
    by_link: false,
    group: { id: CREW_ID, name: 'Kazimierz crew' },
    sport: 'PADEL',
    level: 3.4,
    player_score: 98,
    reliability_band: 'VERY_HIGH',
  };
  const REQUEST = notice({
    kind: 'FRIEND_REQUEST',
    title: 'ines.d wants to be your friend',
    body: 'With you in Kazimierz crew · Padel',
    opens: 'HOME',
    game_id: null,
    pool_id: CREW_ID,
    sport: null,
    game_kind: null,
    player_id: INES,
    new: true,
  });
  const MADE = notice({
    kind: 'FRIENDS_MADE',
    title: 'ines.d said yes — you’re friends',
    body: 'Find ines.d in You › Friends.',
    opens: 'RECORD',
    game_id: null,
    pool_id: null,
    sport: null,
    game_kind: null,
    player_id: INES,
    new: true,
  });
  const MADE_PUSHED = {
    notice_id: MADE.notice_id,
    kind: 'FRIENDS_MADE',
    opens: 'RECORD',
    player_id: INES,
  };

  beforeEach(() => {
    stubHomeGames(transport, [], { friend_requests: [ASKED] });
    transport.on('GET', `/api/v1/players/${INES}/record`, () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'FRIEND',
        blocked_by_you: false,
        nickname: 'ines.d',
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: 3.4, band: 'Established' }],
        reliability: servedReliability({ player_score: 98, is_new: false }),
      }),
    );
  });

  it('a request’s row behind the bell opens Home, on its card', async () => {
    stubNotices(transport, [REQUEST], { newCount: 1 });
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));

    fireEvent.press(await screen.findByRole('button', { name: /^New\. ines\.d wants to be/ }));

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(await screen.findByRole('header', { name: requestsHeading(1) })).toBeTruthy();
    expect(screen.getByText(wantsToBeYourFriend('ines.d'))).toBeTruthy();
    expect(screen.queryByLabelText('Back')).toBeNull();
  });

  it('You’re friends, behind the bell, opens the friend’s record over the list', async () => {
    stubNotices(transport, [MADE], { newCount: 1 });
    await launchSignedIn();
    fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
    await waitFor(() => expect(screen).toHavePathname('/notices'));

    fireEvent.press(await screen.findByRole('button', { name: /^New\. ines\.d said yes/ }));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(await screen.findByRole('button', { name: FRIENDS_COPY.record.friend })).toBeTruthy();
    // A sheet over the list, not a screen pushed: the list is still where the player is.
    expect(screen).toHavePathname('/notices');
  });

  it('You’re friends, pushed and tapped, opens the record over wherever the player is', async () => {
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));
    await waitFor(() => expect(screen).toHavePathname('/you'));

    act(() => phone.tap(MADE_PUSHED));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', `/api/v1/players/${INES}/record`)).toHaveLength(1),
    );
    expect(screen).toHavePathname('/you');
  });
});

// ---------------------------------------------------------------------------
// An ask for a Level (#758, on #749's)
// ---------------------------------------------------------------------------

/**
 * ***Level asked* opens the sport's questionnaire, and *Level got* the asker's picker** (the friends
 * mechanics §12; the words §29.5). The backend pushes the sport each names, and *Level got* the group
 * the ask was made from as `pool_id`. *Level asked* walks in through the level pass, begun from Home
 * — its usual return, since a notice names no group to go back to; *Level got* lays the group's
 * page on Friends under its picker, so Done and *back* land on the court.
 */
describe('an ask for a Level', () => {
  const TOMEK = 'f0000000-0000-4000-8000-000000000011';
  const ZOFIA = 'f0000000-0000-4000-8000-000000000012';
  const RUN = 'e0000000-0000-4000-8000-000000000758';
  const ASSESSMENTS_PATH = '/api/v1/assessments';

  const ASKED = notice({
    kind: 'LEVEL_ASKED',
    title: 'tomek.k wants to play padel with you.',
    body: 'Get your padel level so tomek.k can add you.',
    opens: 'QUESTIONNAIRE',
    game_id: null,
    pool_id: null,
    sport: 'PADEL',
    game_kind: null,
    player_id: TOMEK,
    new: true,
  });
  const ASKED_PUSHED = {
    notice_id: ASKED.notice_id,
    kind: 'LEVEL_ASKED',
    opens: 'QUESTIONNAIRE',
    player_id: TOMEK,
    sport: 'PADEL',
  };
  const GOT = notice({
    kind: 'LEVEL_GOT',
    title: 'zofia.b has a padel level — you can seat zofia.b now.',
    body: 'In Kazimierz crew, on the Friends tab.',
    opens: 'PICKER',
    game_id: null,
    pool_id: CREW_ID,
    sport: 'PADEL',
    game_kind: null,
    player_id: ZOFIA,
    new: true,
  });
  const GOT_PUSHED = {
    notice_id: GOT.notice_id,
    kind: 'LEVEL_GOT',
    opens: 'PICKER',
    player_id: ZOFIA,
    pool_id: CREW_ID,
    sport: 'PADEL',
  };

  const QUESTION: Wire['QuestionResponse'] = {
    id: 'q-played',
    category: 'Recent activity',
    tier: null,
    situation: 'Before anything else',
    text: 'Have you played padel before?',
    qualifier: 'Any level counts',
    options: [
      { id: 'never', text: 'Never played' },
      { id: 'regular', text: 'I play most weeks' },
    ],
  };
  const OPENING: Wire['AssessmentStepResponse'] = {
    assessment_id: RUN,
    status: 'in_progress',
    questions_asked: 0,
    transcript: [],
    question: QUESTION,
  };

  /** zofia.b, as the picker reads her — with her new padel Level. */
  const ZOFIA_RATED: Wire['FriendSchema'] = {
    player_id: ZOFIA,
    nickname: 'zofia.b',
    photo_id: null,
    photo_url: null,
    friends_since: '2026-09-01T10:00:00Z',
    sports: [{ sport: 'PADEL', level: 2.4, band: 'Developing' }],
    level_asked_in: ['PADEL'],
  };

  describe('Level asked — Zofia, unrated at padel', () => {
    beforeEach(() => {
      stubGate(transport, { ratings: [{ ...RATING, sport: 'TENNIS' }], hasPlayerProfile: true });
      transport.on('POST', ASSESSMENTS_PATH, () => {
        stubRunsInProgress(transport, [{ assessment_id: RUN, sport: 'PADEL' }]);
        return json(OPENING, 201);
      });
      transport.on('GET', `${ASSESSMENTS_PATH}/${RUN}`, () => json(OPENING));
    });

    /** On the question, she leaves for later — and the pass lands where it began, Home. */
    async function continueLater() {
      fireEvent.press(screen.getByLabelText('Leave this rating'));
      fireEvent.press(await screen.findByLabelText(/^Continue later\./));
      await waitFor(() => expect(screen).toHavePathname('/'));
      expect(screen.queryByText(QUESTION.text)).toBeNull();
    }

    it('its row behind the bell opens the padel questionnaire, and its return is Home', async () => {
      stubNotices(transport, [ASKED], { newCount: 1 });
      await launchSignedIn();
      fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
      await waitFor(() => expect(screen).toHavePathname('/notices'));

      fireEvent.press(await screen.findByRole('button', { name: /^New\. tomek\.k wants to play/ }));

      await waitFor(() => expect(screen).toHavePathname(`/question/${RUN}`));
      expect(await screen.findByText(QUESTION.text)).toBeTruthy();
      expect(transport.requestsTo('POST', ASSESSMENTS_PATH).map((one) => one.body)).toEqual([
        { sport: 'PADEL' },
      ]);
      await continueLater();
    });

    it('a push of it, tapped, opens the questionnaire from wherever she is', async () => {
      await launchSignedIn();
      fireEvent.press(await screen.findByLabelText('You'));
      await waitFor(() => expect(screen).toHavePathname('/you'));

      act(() => phone.tap(ASKED_PUSHED));

      await waitFor(() => expect(screen).toHavePathname(`/question/${RUN}`));
      expect(await screen.findByText(QUESTION.text)).toBeTruthy();
      await continueLater();
    });

    it('says she has the Level already when she got one since, and opens nothing', async () => {
      transport.on('POST', ASSESSMENTS_PATH, () => errorResponse(409, 'sport_already_rated'));
      stubNotices(transport, [ASKED], { newCount: 1 });
      await launchSignedIn();
      fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
      await waitFor(() => expect(screen).toHavePathname('/notices'));

      useToastQueue.setState({ queue: [] });
      fireEvent.press(await screen.findByRole('button', { name: /^New\. tomek\.k wants to play/ }));

      await waitFor(() =>
        expect(useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone])).toEqual([
          ['You have a padel level already.', 'base'],
        ]),
      );
      expect(screen).toHavePathname('/notices');
      useToastQueue.setState({ queue: [] });
    });
  });

  describe('Level got — Tomek, who asked from the crew', () => {
    beforeEach(() => {
      stubMyGroups(transport, [CREW]);
      transport.on('GET', `/api/v1/groups/${CREW_ID}`, () => json(CREW_PAGE));
      stubGroupDeck(transport, CREW_ID);
      transport.on('GET', FRIENDS_PATH, () =>
        json<Wire['FriendsResponse']>({ sport: 'PADEL', friends: [ZOFIA_RATED] }),
      );
    });

    afterEach(() => queryClient.setQueryDefaults(friendKeys.all, {}));

    it('its row behind the bell opens the crew’s picker, over its Friends tab, where she can be picked', async () => {
      stubNotices(transport, [GOT], { newCount: 1 });
      await launchSignedIn();
      // The picker as it was read before her Level arrived: greyed, asked — and never stale nor
      // collected on its own (the harness runs timers on a push), so only the notice marking it
      // stale reads it again.
      queryClient.setQueryDefaults(friendKeys.all, { staleTime: Infinity, gcTime: Infinity });
      queryClient.setQueryData(friendKeys.listIn('padel'), [
        { playerId: ZOFIA, nickname: 'zofia.b', sports: [], askedIn: ['padel'] },
      ]);
      fireEvent.press(await screen.findByRole('button', { name: 'Recent notifications, 1 new' }));
      await waitFor(() => expect(screen).toHavePathname('/notices'));

      fireEvent.press(await screen.findByRole('button', { name: /^New\. zofia\.b has a padel/ }));

      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}/friends`));
      // Read again: the row is hers with her Level, pickable — never the read from before it.
      expect(
        await screen.findByRole('checkbox', {
          name: 'zofia.b, 2,40 · developing',
          disabled: false,
        }),
      ).toBeTruthy();

      // Done lands on the crew’s Friends tab, in padel — the page under the picker.
      fireEvent.press(screen.getByRole('button', { name: FRIENDS_COPY.picker.done }));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}`));
      expect(await screen.findByRole('button', { name: 'Friends', selected: true })).toBeTruthy();
      // And back from the page is the list the notice was opened from.
      fireEvent.press(await screen.findByLabelText(GROUPS_COPY.group.back));
      await waitFor(() => expect(screen).toHavePathname('/notices'));
    });

    it('a push of it, tapped, opens the picker over wherever he is — back is the crew’s Friends tab', async () => {
      await launchSignedIn();
      fireEvent.press(await screen.findByLabelText('You'));
      await waitFor(() => expect(screen).toHavePathname('/you'));

      act(() => phone.tap(GOT_PUSHED));

      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}/friends`));
      expect(await screen.findByRole('checkbox', { name: /^zofia\.b/ })).toBeTruthy();
      fireEvent.press(await screen.findByLabelText('Back'));
      await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW_ID}`));
      expect(await screen.findByRole('button', { name: 'Friends', selected: true })).toBeTruthy();
    });
  });
});
