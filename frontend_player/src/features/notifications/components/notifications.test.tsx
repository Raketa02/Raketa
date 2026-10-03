/**
 * **The notices, walked the way a player meets them** — the real route tree and the real bar, with
 * only `fetch` and the phone faked ([#559](https://github.com/Raketa02/Raketa/issues/559); the screens
 * A7.2, A9; mocks 50, 52, 53; the mechanics §17.2).
 *
 * The server is #549's: `GET`/`PUT /players/me/notifications` (a save answers the three it saved),
 * `POST /players/me/devices` and `…/removal` (the token in the body), and `GET /players/me/notices`
 * (newest first, each in the words it was pushed in and with where a tap opens it). The phone is
 * `fakePush()`: a permission the suite sets, a token, and pushes that arrive or are tapped when the
 * suite says so.
 */

import { focusManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Linking } from 'react-native';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, theme } from '@/shared/ui';
import {
  deckCard,
  DECK_READ_AT,
  groupDeck,
  proposalDetails,
  stubGroupDeck,
  stubProposal,
} from '@/test-support/groupDeck';
import { BOOKING, bookingDetails, stubBooking } from '@/test-support/home';
import {
  DEVICES_PATH,
  DEVICE_REMOVAL_PATH,
  launchSignedIn,
  NOTICES_PATH,
  NOTIFICATION_CHOICES_PATH,
  resetPush,
  stubGate,
  stubInterest,
  stubMyGroups,
  stubNotices,
  stubNotificationChoices,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
  stubPush,
} from '@/test-support/onboardingRouter';
import { fakePush, PUSH_TOKEN, type FakePush } from '@/test-support/platform';
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
  administrator_name: null,
  is_administrator: false,
};

let given = 0;

/** A notice as the list serves it — *It's a game!* about the booked game, unless told otherwise. */
function notice(extra: Partial<Wire['NoticeSchema']> = {}): Wire['NoticeSchema'] {
  given += 1;
  return {
    notice_id: `d0000000-0000-4000-8000-${String(given).padStart(12, '0')}`,
    kind: 'GAME_BOOKED',
    title: 'It’s a game! · you paid 30 zł',
    body: 'Padel · Sat 16:00 · Bonarka Arena',
    given_at: '2026-10-02T12:05:00Z',
    opens: 'BOOKING',
    game_id: BOOKING,
    pool_id: CREW_ID,
    sport: 'PADEL',
    game_kind: 'COMPETITIVE',
    gathered: 0,
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
  stubInterest(transport);
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
 * notice must be newer than to be drawn as the banner.
 */
async function sessionReadTheList() {
  await waitFor(() => expect(queryClient.getQueryData(['notifications', 'notices'])).toBeDefined());
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

  it('says only the seven always on are left once all three are off', async () => {
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
  it('lists the seven always on, each inert with its green tag (mock 52)', async () => {
    await onNotifications();

    for (const row of COPY.alwaysOn.rows) {
      const drawn = screen.getByText(row);
      expect(screen.getByLabelText(`${row.split(' · ').join(', ')}, always on`)).toBeTruthy();
      expect(drawn).toBeTruthy();
    }
    expect(screen.getAllByText(COPY.alwaysOn.tag)).toHaveLength(7);
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
          held.push(() => resolve(json<Wire['RecentNoticesResponse']>({ notices: [BOOKED] }))),
        ),
    );

    act(() => phone.receive({ title: BOOKED.title, body: BOOKED.body, data: payloadOf(BOOKED) }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.banner.close }));
    await waitFor(() => expect(held).toHaveLength(1));
    await act(async () => held.shift()?.());

    await waitFor(() =>
      expect(queryClient.getQueryData(['notifications', 'notices'])).toHaveLength(1),
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
