/**
 * **Who's here — caught at the court, one tap while you wait and one when they walk in**
 * ([#658](https://github.com/Raketa02/Raketa/issues/658); ADR-0195 §3; the backend's #657), walked
 * the way a player walks it: the real route tree and shell, only `fetch` and the phone's position
 * faked.
 *
 * Saturday 3 October, padel 16:00–17:00 at Bonarka Arena. In the first half hour the booked details'
 * door reads *Who's here*; on the result screen a player at the club taps *Bartek Lis isn't here
 * yet* — one press, no sheet — and the phone reads its position at that press and sends it. The
 * fake server judges it as the backend does, by distance from the club: **the fake location port
 * places the phone at the club or away**. Bartek reads that the others are waiting, with *I'm
 * here*; anybody says *Bartek Lis is here* when he walks in. Afterwards he may say *I was there*
 * for a day, and somebody else confirms it.
 *
 * The rules are `games`' `attendance.test.ts` and `resultArgument.test.ts`, and the words
 * `gamePresentation.test.ts`; what is asserted here is that the screens are wired to them.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import type { LocationFix } from '@/shared/lib/platform';
import { queryClient } from '@/shared/lib/query-client';
import { offlineMessage } from '@/shared/errors';
import {
  BARTEK,
  BOOKED_GAME,
  BOOKING,
  INES,
  bookedGameOnTheList,
  bookedRoomRow,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import {
  GATE_USER,
  HOME_PATH,
  bookingPath,
  launchSignedIn,
  resetLocation,
  stubConversations,
  stubGames,
  stubGate,
  stubLocation,
} from '@/test-support/onboardingRouter';
import { fakeLocation, type FakeLocation } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { HOME_GAME_COPY } from './homeCopy';

const HOME = HOME_GAME_COPY;

/** 16:10 in Warsaw — the first half hour, twenty minutes of it left. */
const AT_THE_COURT = '2026-10-03T14:10:00Z';
/** 16:30, the half hour's end, and the day after it in which *I was there* may be said. */
const ARRIVE_BY = '2026-10-03T14:30:00Z';
const CLAIM_BY = '2026-10-04T14:30:00Z';
/** The next morning, 09:00 in Warsaw — inside the late claim's day. */
const NEXT_MORNING = '2026-10-04T07:00:00Z';

/** Bonarka Arena's map point, as the backend knows it; the phone never does. */
const CLUB = { latitude: 50.0275, longitude: 19.95 };
/** The phone 40 m from the club, and at home in Warsaw. */
const AT_THE_CLUB: LocationFix = { latitude: 50.0278, longitude: 19.9502, accuracyMetres: 9 };
const AWAY: LocationFix = { latitude: 52.2297, longitude: 21.0122, accuracyMetres: 12 };

const NOT_HERE_YET_PATH = `/api/v1/games/${BOOKED_GAME}/attendance/not-here-yet`;
const ARRIVAL_PATH = `/api/v1/games/${BOOKED_GAME}/attendance/arrival`;
const CLAIM_PATH = `/api/v1/games/${BOOKED_GAME}/attendance/claim`;
const CONFIRMATION_PATH = `/api/v1/games/${BOOKED_GAME}/attendance/confirmation`;
const LOCATION_PATH = '/api/v1/players/me/location';

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
let phone: FakeLocation;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  // A phone whose location is allowed already re-reads the area on a cold start (ADR-0174 §6).
  transport.on('PUT', LOCATION_PATH, () => noContent());
  phone = fakeLocation({ state: 'granted', fix: AT_THE_CLUB });
  stubLocation(phone);
});

afterEach(async () => {
  transport.restore();
  resetLocation();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  await forgetPhonePreferences();
});

/**
 * **The backend's verdict, faked by distance** — within about 300 m of the club's point is *at the
 * club*. Coarse on purpose: the real measure is the backend's, and what is proven here is that the
 * phone sends the position it read, and says what the answer was.
 */
function atTheClub(request: RecordedRequest): boolean {
  const body = request.body as { location?: Wire['LocationFixSchema'] } | undefined;
  const at = body?.location;
  if (at === undefined) return false;
  return (
    Math.abs(at.latitude - CLUB.latitude) < 0.003 && Math.abs(at.longitude - CLUB.longitude) < 0.004
  );
}

/** One row of `attendance`, as `GET /games` carries it. */
function row(
  playerId: string,
  name: string,
  extra: Partial<Wire['AttendanceSchema']> = {},
): Wire['AttendanceSchema'] {
  return {
    player_id: playerId,
    name,
    state: 'WAITING',
    noted_at: '2026-10-03T14:05:00Z',
    arrive_by: ARRIVE_BY,
    arrived_at: null,
    claim_by: CLAIM_BY,
    claimed_at: null,
    confirmed_at: null,
    ...extra,
  };
}

/** The booked Game in its first half hour, as the list reads it — nothing entered unless said. */
function theGame(extra: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return bookedGameOnTheList({ entry_closes_at: '2026-10-04T15:00:00Z', ...extra });
}

/** The booking's details at `readAt`, its hour come. */
function details(
  readAt: string,
  extra: Partial<Wire['BookingDetailsResponse']> = {},
): Wire['BookingDetailsResponse'] {
  return bookingDetails({
    status: 'NEEDS_RESULT',
    needs_you: true,
    read_at: readAt,
    leaving: null,
    shows_forecast: false,
    ...extra,
  });
}

/** Land on Home, open the game's details, and take the result door they offer. */
async function openResult(booking: Wire['BookingDetailsResponse'], door: string) {
  stubHomeGames(transport, [
    homeGame({
      status: booking.status,
      uncounted_reason: booking.uncounted_reason,
      needs_you: booking.needs_you,
    }),
  ]);
  stubBooking(transport, booking);
  stubConversations(transport, [bookedRoomRow()]);
  await launchSignedIn();

  fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
  fireEvent.press(await screen.findByRole('button', { name: door }));
  await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/result`));
}

// ---------------------------------------------------------------------------
// The door
// ---------------------------------------------------------------------------

describe('the booked details’ door, once the hour has come', () => {
  it('is Who’s here in the first half hour, and We played after it', async () => {
    stubGames(transport, [theGame()], AT_THE_COURT);
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    expect(await screen.findByRole('header', { name: 'Who’s here' })).toBeTruthy();
  });

  it('is We played once the half hour is over', async () => {
    stubHomeGames(transport, [homeGame({ status: 'NEEDS_RESULT', needs_you: true })]);
    stubBooking(transport, details('2026-10-03T14:45:00Z'));
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
    expect(
      await screen.findByRole('button', { name: HOME.details.resultAct['we-played'] }),
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: HOME.details.resultAct['whos-here'] })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Isn't here yet
// ---------------------------------------------------------------------------

describe('isn’t here yet, from the court', () => {
  it('is one tap per other player, with no sheet, and the score still the screen’s', async () => {
    stubGames(transport, [theGame()], AT_THE_COURT);
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    for (const name of ['Piotr Sowa', 'Inés Díaz', 'Bartek Lis']) {
      expect(await screen.findByRole('button', { name: `${name} isn’t here yet` })).toBeTruthy();
    }
    expect(screen.queryByRole('button', { name: /^You isn’t/ })).toBeNull();
    expect(screen.getByText(/It works only from the club/)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Send this score/ })).toBeTruthy();
  });

  it('reads the phone’s position at the tap, sends it, and the screen then waits for them', async () => {
    stubGames(transport, [theGame()], AT_THE_COURT);
    transport.on('POST', NOT_HERE_YET_PATH, (request) => {
      if (!atTheClub(request)) return errorResponse(409, 'not_at_the_club');
      const awaited = theGame({
        standing: 'NOT_HERE_YET',
        attendance: [row(BARTEK, 'Bartek Lis')],
      });
      stubGames(transport, [awaited], AT_THE_COURT);
      return json(awaited);
    });
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    const areaReads = phone.reads;
    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    const bookingReads = transport.requestsTo('GET', bookingPath(BOOKING)).length;
    expect(phone.preciseReads).toBe(0);
    fireEvent.press(await screen.findByRole('button', { name: 'Bartek Lis isn’t here yet' }));

    // One press, and it is sent: no sheet stands in front of it.
    await waitFor(() => expect(transport.requestsTo('POST', NOT_HERE_YET_PATH)).toHaveLength(1));
    expect(screen.queryByTestId('bottom-sheet')).toBeNull();
    expect(transport.requestsTo('POST', NOT_HERE_YET_PATH)[0]?.body).toEqual({
      player_id: BARTEK,
      location: { latitude: 50.0278, longitude: 19.9502, accuracy_m: 9 },
    });
    // One precise read, at the tap — and the area's own read untouched.
    expect(phone.preciseReads).toBe(1);
    expect(phone.reads).toBe(areaReads);

    expect(await screen.findByRole('header', { name: 'Not here yet' })).toBeTruthy();
    expect(screen.getByText('Waiting for Bartek Lis.')).toBeTruthy();
    expect(screen.getByLabelText(/^20 minutes left for them to arrive/)).toBeTruthy();
    // They can be said to be here now; the others can still be tapped; no score goes in meanwhile.
    expect(screen.getByRole('button', { name: 'Bartek Lis is here' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Piotr Sowa isn’t here yet' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Send this score/ })).toBeNull();
    // Home's badge and the details under this screen are read again.
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads),
    );
    expect(transport.requestsTo('GET', bookingPath(BOOKING)).length).toBeGreaterThan(bookingReads);
  });

  it('says so in a sentence when the tap is made away from the club', async () => {
    phone.fix = AWAY;
    stubGames(transport, [theGame()], AT_THE_COURT);
    transport.on('POST', NOT_HERE_YET_PATH, (request) =>
      atTheClub(request) ? json(theGame()) : errorResponse(409, 'not_at_the_club'),
    );
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Bartek Lis isn’t here yet' }));

    expect(await screen.findByText('You can say so only from Bonarka Arena.')).toBeTruthy();
    expect(transport.requestsTo('POST', NOT_HERE_YET_PATH)[0]?.body).toMatchObject({
      location: { latitude: 52.2297, longitude: 21.0122 },
    });
  });

  /**
   * **Precise Location off** (iOS) or approximate location (Android): the phone hands over a fix a
   * few kilometres wide, the backend cannot place it at the club, and the player standing there is
   * told why — and where the setting is — rather than that they are somewhere else.
   */
  it('says the phone’s position was too rough, and offers Settings, when only a rough fix went', async () => {
    phone.fix = { latitude: 50.05, longitude: 19.98, accuracyMetres: 3000 };
    stubGames(transport, [theGame()], AT_THE_COURT);
    transport.on('POST', NOT_HERE_YET_PATH, (request) =>
      atTheClub(request) ? json(theGame()) : errorResponse(409, 'not_at_the_club'),
    );
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Bartek Lis isn’t here yet' }));

    expect(
      await screen.findByText(/Your phone could only tell roughly where you are/),
    ).toBeTruthy();
    expect(screen.queryByText('You can say so only from Bonarka Arena.')).toBeNull();
    expect(screen.getByRole('button', { name: 'Open Settings' })).toBeTruthy();
  });

  it('asks for the location at the tap, and says why when the player says no', async () => {
    phone = fakeLocation({ state: 'undetermined', answer: 'denied', fix: AT_THE_CLUB });
    stubLocation(phone);
    stubGames(transport, [theGame()], AT_THE_COURT);
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Bartek Lis isn’t here yet' }));

    expect(
      await screen.findByText(
        'Raketa needs your location to check you’re at the club. Allow it when your phone asks, then tap again.',
      ),
    ).toBeTruthy();
    expect(phone.preciseReads).toBe(0);
    expect(transport.requestsTo('POST', NOT_HERE_YET_PATH)).toHaveLength(0);
  });

  it('sends a player whose location is off for good to Settings, and reads nothing', async () => {
    phone = fakeLocation({ state: 'blocked', fix: AT_THE_CLUB });
    stubLocation(phone);
    stubGames(transport, [theGame()], AT_THE_COURT);
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa isn’t here yet' }));

    expect(await screen.findByText(/Location is off for Raketa/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Open Settings' })).toBeTruthy();
    expect(phone.preciseReads).toBe(0);
    expect(transport.requestsTo('POST', NOT_HERE_YET_PATH)).toHaveLength(0);
  });

  it('says so when the phone cannot tell where it is', async () => {
    phone.fix = null;
    stubGames(transport, [theGame()], AT_THE_COURT);
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa isn’t here yet' }));

    expect(
      await screen.findByText('Your phone couldn’t tell where you are. Try again in a moment.'),
    ).toBeTruthy();
    expect(transport.requestsTo('POST', NOT_HERE_YET_PATH)).toHaveLength(0);
  });

  it('says the half hour is over when the tap lands after it', async () => {
    stubGames(transport, [theGame()], AT_THE_COURT);
    transport.on('POST', NOT_HERE_YET_PATH, () => errorResponse(409, 'the_tap_window_has_closed'));
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa isn’t here yet' }));

    expect(
      await screen.findByText(
        'The first half hour is over, so it’s too late to say who’s here. A later arrival can’t be noted.',
      ),
    ).toBeTruthy();
  });

  /** When an arrival lands decides what it was, so a tap at the court is never queued for later. */
  it('fails at once with no connection, and says it was not sent', async () => {
    stubGames(transport, [theGame()], AT_THE_COURT);
    transport.on('POST', NOT_HERE_YET_PATH, () => {
      throw new TypeError('Network request failed');
    });
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa isn’t here yet' }));

    expect(await screen.findByText(offlineMessage('does-not-resume'))).toBeTruthy();
  });

  it('clears a refused tap’s sentence once the next tap goes through', async () => {
    phone.fix = AWAY;
    stubGames(transport, [theGame()], AT_THE_COURT);
    transport.on('POST', NOT_HERE_YET_PATH, (request) =>
      atTheClub(request) ? json(theGame()) : errorResponse(409, 'not_at_the_club'),
    );
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Piotr Sowa isn’t here yet' }));
    expect(await screen.findByText('You can say so only from Bonarka Arena.')).toBeTruthy();

    // Into the club, and again.
    phone.fix = AT_THE_CLUB;
    fireEvent.press(screen.getByRole('button', { name: 'Piotr Sowa isn’t here yet' }));

    await waitFor(() => expect(transport.requestsTo('POST', NOT_HERE_YET_PATH)).toHaveLength(2));
    await waitFor(() =>
      expect(screen.queryByText('You can say so only from Bonarka Arena.')).toBeNull(),
    );
  });
});

// ---------------------------------------------------------------------------
// The arrival
// ---------------------------------------------------------------------------

describe('the arrival', () => {
  const meAwaited = () =>
    theGame({
      standing: 'NOT_HERE_YET',
      attendance: [row(GATE_USER.id, GATE_USER.name ?? 'Ada')],
    });

  it('tells the player awaited who is waiting, with I’m here pinned', async () => {
    stubGames(transport, [meAwaited()], AT_THE_COURT);
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    expect(await screen.findByRole('header', { name: 'Are you here?' })).toBeTruthy();
    expect(
      screen.getByText('Piotr Sowa, Inés Díaz and Bartek Lis are waiting for you.'),
    ).toBeTruthy();
    expect(screen.getByLabelText(/^20 minutes left to arrive/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'I’m here' })).toBeTruthy();
    // Awaited themselves, they say nothing about anybody else.
    expect(screen.queryByRole('button', { name: /isn’t here yet/ })).toBeNull();
  });

  it('says I’m here with their own id and the position read at the tap', async () => {
    stubGames(transport, [meAwaited()], AT_THE_COURT);
    transport.on('POST', ARRIVAL_PATH, (request) => {
      if (!atTheClub(request)) return errorResponse(409, 'not_at_the_club');
      const late = theGame({
        attendance: [
          row(GATE_USER.id, GATE_USER.name ?? 'Ada', {
            state: 'CAME_LATE',
            arrived_at: '2026-10-03T14:22:00Z',
          }),
        ],
      });
      stubGames(transport, [late], '2026-10-03T14:22:00Z');
      return json(late);
    });
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'I’m here' }));

    await waitFor(() => expect(transport.requestsTo('POST', ARRIVAL_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', ARRIVAL_PATH)[0]?.body).toEqual({
      player_id: GATE_USER.id,
      location: { latitude: 50.0278, longitude: 19.9502, accuracy_m: 9 },
    });
    // Came late: the game goes on, and the block says so.
    expect(await screen.findByText('You came late')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'I’m here' })).toBeNull();
    expect(screen.getByRole('button', { name: /Send this score/ })).toBeTruthy();
  });

  it('says I’m here from home was not at the club', async () => {
    phone.fix = AWAY;
    stubGames(transport, [meAwaited()], AT_THE_COURT);
    transport.on('POST', ARRIVAL_PATH, (request) =>
      atTheClub(request) ? json(meAwaited()) : errorResponse(409, 'not_at_the_club'),
    );
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'I’m here' }));

    expect(await screen.findByText('You can say so only from Bonarka Arena.')).toBeTruthy();
  });

  it('lets a courtmate say they’re here, and the tap vanishes when they were on time', async () => {
    const bartekAwaited = theGame({
      standing: 'NOT_HERE_YET',
      attendance: [row(BARTEK, 'Bartek Lis')],
    });
    stubGames(transport, [bartekAwaited], AT_THE_COURT);
    transport.on('POST', ARRIVAL_PATH, () => {
      const onTime = theGame({
        attendance: [row(BARTEK, 'Bartek Lis', { state: 'ON_TIME', arrived_at: AT_THE_COURT })],
      });
      stubGames(transport, [onTime], AT_THE_COURT);
      return json(onTime);
    });
    await openResult(
      details(AT_THE_COURT, { needs_you: false }),
      HOME.details.resultAct['whos-here'],
    );

    fireEvent.press(await screen.findByRole('button', { name: 'Bartek Lis is here' }));

    await waitFor(() => expect(transport.requestsTo('POST', ARRIVAL_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', ARRIVAL_PATH)[0]?.body).toMatchObject({
      player_id: BARTEK,
    });
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: 'Bartek Lis is here' })).toBeNull(),
    );
    // On time vanishes: nothing is said of him, and he cannot be tapped again.
    expect(screen.queryByText(/Bartek Lis came late/)).toBeNull();
    expect(screen.queryByRole('button', { name: 'Bartek Lis isn’t here yet' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Piotr Sowa isn’t here yet' })).toBeTruthy();
  });

  it('says a second arrival was already noted', async () => {
    stubGames(
      transport,
      [theGame({ standing: 'NOT_HERE_YET', attendance: [row(BARTEK, 'Bartek Lis')] })],
      AT_THE_COURT,
    );
    transport.on('POST', ARRIVAL_PATH, () => errorResponse(409, 'already_arrived'));
    await openResult(details(AT_THE_COURT), HOME.details.resultAct['whos-here']);

    fireEvent.press(await screen.findByRole('button', { name: 'Bartek Lis is here' }));

    expect(
      await screen.findByText('That arrival is already noted — the first one counts.'),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Afterwards: Didn't come, I was there, and Yes, they were here
// ---------------------------------------------------------------------------

describe('after the half hour', () => {
  const uncounted = (needsYou: boolean) =>
    details(NEXT_MORNING, {
      status: 'UNCOUNTED',
      uncounted_reason: 'DIDNT_COME',
      needs_you: needsYou,
    });
  const iDidntCome = (extra: Partial<Wire['AttendanceSchema']> = {}) =>
    theGame({
      standing: 'DIDNT_COME',
      entry_closes_at: null,
      attendance: [row(GATE_USER.id, GATE_USER.name ?? 'Ada', { state: 'DIDNT_COME', ...extra })],
    });

  it('says on Home’s card that somebody didn’t come, and to say who was there', async () => {
    stubHomeGames(transport, [
      homeGame({ status: 'UNCOUNTED', uncounted_reason: 'DIDNT_COME', needs_you: true }),
    ]);
    await launchSignedIn();

    const card = await screen.findByTestId(`home-game-${BOOKING}`);
    expect(within(card).getByText('Somebody didn’t come · say who was there')).toBeTruthy();
  });

  it('opens Say who was there, and offers the player who didn’t come I was there', async () => {
    stubGames(transport, [iDidntCome()], NEXT_MORNING);
    transport.on('POST', CLAIM_PATH, () => {
      const claimed = iDidntCome({ state: 'CLAIMED', claimed_at: NEXT_MORNING });
      stubGames(transport, [claimed], NEXT_MORNING);
      return json(claimed);
    });
    await openResult(uncounted(true), HOME.details.resultAct['who-was-there']);

    expect(await screen.findByRole('header', { name: 'Were you there?' })).toBeTruthy();
    expect(screen.getByText('You didn’t come.')).toBeTruthy();
    expect(screen.getByLabelText(/^7 hours left to say you were there/)).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: 'I was there' }));

    await waitFor(() => expect(transport.requestsTo('POST', CLAIM_PATH)).toHaveLength(1));
    // A day later, from anywhere: no position is read or sent.
    expect(transport.requestsTo('POST', CLAIM_PATH)[0]?.body).toBeUndefined();
    expect(phone.preciseReads).toBe(0);
    expect(await screen.findByText(/You said you were there/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'I was there' })).toBeNull();
  });

  it('says so when the day to claim it has passed meanwhile', async () => {
    stubGames(transport, [iDidntCome()], NEXT_MORNING);
    transport.on('POST', CLAIM_PATH, () => errorResponse(409, 'the_late_claim_has_closed'));
    await openResult(uncounted(true), HOME.details.resultAct['who-was-there']);

    fireEvent.press(await screen.findByRole('button', { name: 'I was there' }));

    expect(
      await screen.findByText('The day to say you were there has passed, so Didn’t come stands.'),
    ).toBeTruthy();
  });

  it('offers somebody else on the court Yes, they were here, which makes it Came late', async () => {
    const bartekClaimed = () =>
      theGame({
        standing: 'DIDNT_COME',
        entry_closes_at: null,
        attendance: [row(BARTEK, 'Bartek Lis', { state: 'CLAIMED', claimed_at: NEXT_MORNING })],
      });
    stubGames(transport, [bartekClaimed()], NEXT_MORNING);
    transport.on('POST', CONFIRMATION_PATH, () => {
      const confirmed = theGame({
        entry_closes_at: '2026-10-04T15:00:00Z',
        attendance: [
          row(BARTEK, 'Bartek Lis', {
            state: 'CONFIRMED',
            claimed_at: NEXT_MORNING,
            confirmed_at: '2026-10-04T07:05:00Z',
          }),
        ],
      });
      stubGames(transport, [confirmed], NEXT_MORNING);
      return json(confirmed);
    });
    await openResult(uncounted(true), HOME.details.resultAct['who-was-there']);

    expect(await screen.findByText('Bartek Lis didn’t come.')).toBeTruthy();
    expect(screen.getByText('Bartek Lis says they were there')).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: 'Yes, Bartek Lis was here' }));

    await waitFor(() => expect(transport.requestsTo('POST', CONFIRMATION_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', CONFIRMATION_PATH)[0]?.body).toEqual({ player_id: BARTEK });
    expect(phone.preciseReads).toBe(0);
    expect(await screen.findByText('Bartek Lis came late')).toBeTruthy();
    expect(screen.getByRole('header', { name: 'Who was there' })).toBeTruthy();
  });

  it('says the day to confirm has passed, in the words of the one confirming', async () => {
    stubGames(
      transport,
      [
        theGame({
          standing: 'DIDNT_COME',
          entry_closes_at: null,
          attendance: [row(BARTEK, 'Bartek Lis', { state: 'CLAIMED', claimed_at: NEXT_MORNING })],
        }),
      ],
      NEXT_MORNING,
    );
    transport.on('POST', CONFIRMATION_PATH, () => errorResponse(409, 'the_late_claim_has_closed'));
    await openResult(uncounted(true), HOME.details.resultAct['who-was-there']);

    fireEvent.press(await screen.findByRole('button', { name: 'Yes, Bartek Lis was here' }));

    expect(
      await screen.findByText(
        'The day to confirm they were there has passed, so Didn’t come stands.',
      ),
    ).toBeTruthy();
  });

  it('offers nobody the door a late claim does not wait on', async () => {
    stubGames(
      transport,
      [
        theGame({
          standing: 'DIDNT_COME',
          entry_closes_at: null,
          attendance: [row(INES, 'Inés Díaz', { state: 'DIDNT_COME' })],
        }),
      ],
      NEXT_MORNING,
    );
    stubHomeGames(transport, [homeGame({ status: 'UNCOUNTED', uncounted_reason: 'DIDNT_COME' })]);
    stubBooking(transport, uncounted(false));
    stubConversations(transport, [bookedRoomRow()]);
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: HOME.openGame }));
    await screen.findByText('Padel · uncounted');
    expect(
      screen.queryByRole('button', { name: HOME.details.resultAct['who-was-there'] }),
    ).toBeNull();
    expect(
      screen.getByLabelText('Paid, 28 zł, Somebody didn’t come · no Level moved'),
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Every act on a booked game's result re-reads its booking
// ---------------------------------------------------------------------------

/**
 * **Home and the details follow every act on the result screen** — a score agreed as much as a tap
 * (#560, #658): the booking's reads are the composer's, handed to the Game's writes.
 */
describe('an act on a booked game’s result', () => {
  it('re-reads Home and the details once a score is agreed with', async () => {
    const theirs: Wire['StandingProposalSchema'] = {
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
    stubGames(
      transport,
      [
        theGame({
          standing: 'AWAITING_ANSWER',
          played_at: '2026-10-03T15:30:00Z',
          entry_closes_at: null,
          proposals: [theirs],
        }),
      ],
      NEXT_MORNING,
    );
    const ACCEPTANCE_PATH = `/api/v1/games/${BOOKED_GAME}/result/acceptance`;
    transport.on('POST', ACCEPTANCE_PATH, () => json(theGame()));
    await openResult(
      details(NEXT_MORNING, { status: 'CONFIRM_THE_RESULT' }),
      HOME.details.resultAct.confirm,
    );

    const homeReads = transport.requestsTo('GET', HOME_PATH).length;
    const bookingReads = transport.requestsTo('GET', bookingPath(BOOKING)).length;
    fireEvent.press(await screen.findByText('That’s right'));

    await waitFor(() => expect(transport.requestsTo('POST', ACCEPTANCE_PATH)).toHaveLength(1));
    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(homeReads),
    );
    expect(transport.requestsTo('GET', bookingPath(BOOKING)).length).toBeGreaterThan(bookingReads);
  });
});
