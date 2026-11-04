/**
 * **The profile's rows on the You tab, walked the way a player walks them** — the real route
 * tree, the real bar, and only `fetch` and the device faked
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * Each screen is an onboarding step's control under the tab's chrome, and the steps' own
 * suites already prove the controls. What is proved here is what the tab added: **a draft
 * until the button** — the week writes only on *Save*, and the route's answer is
 * what the row's live line then says — and the area's press ending in the cold start's route,
 * with the step's permission states behind it. And, since 2026-09-18, that a *Save* with
 * nothing to send is drawn green and saying *Saved* (6.1 `settled`) — on opening, and again the
 * moment a save lands.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, theme } from '@/shared/ui';
import { fillOf } from '@/test-support/drawn';
import {
  PROFILE_SURFACE_PATH,
  launchSignedIn,
  profileSurface,
  resetLocation,
  stubGate,
  stubLocation,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { fakeLocation, type FakeLocation } from '@/test-support/platform';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  neverResponds,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';
import { paint } from '@/test-support/weekGridTouch';

import { availabilityFootnote } from './availabilityPresentation';
import {
  ACCESS_HOW_TO,
  ACCESS_TITLE,
  AREA_UPDATES_LINE,
  AREA_WRITE_REFUSAL,
  CHANGE_CLUB_LABEL,
  LOCATION_SAVED,
  OPEN_SETTINGS,
  PICK_A_CLUB,
  SAVING_WORD,
  USE_MY_LOCATION,
  pickClubLabel,
  pickedClubLabel,
} from './locationPresentation';
import {
  AREA_LINE,
  AREA_SET,
  CLEAR_ALL,
  SAVED,
  SAVE_YOUR_WEEK,
  WHERE_YOU_PLAY_TITLE,
  YOUR_WEEK_TITLE,
  weekLine,
} from './youProfilePresentation';

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

/** Two hours and one declaration — the profile as the tab opens on it. */
const SURFACE = profileSurface({
  weekly_hours: [
    { day: 2, hour: 19 },
    { day: 6, hour: 9 },
  ],
  play_intents: { PADEL: 'FOR_FUN' },
});

const WEEKLY_HOURS_PATH = '/api/v1/players/me/weekly-hours';
const LOCATION_PATH = '/api/v1/players/me/location';

const PRECISE = { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 };
const AREA_KEPT = { latitude: 41.39, longitude: 2.17 };

let transport: Transport;
let device: FakeLocation;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport, SURFACE);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
  device = fakeLocation({ state: 'granted', fix: PRECISE });
  stubLocation(device);
});

afterEach(async () => {
  transport.restore();
  resetLocation();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const TWO_HOURS = weekLine([
  { day: 2, hour: 19 },
  { day: 6, hour: 9 },
]);

/** A signed-in player standing on the You tab, with the profile read in. */
async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  await screen.findByLabelText(doorRowLabel(YOUR_WEEK_TITLE, TWO_HOURS));
}

const row = (title: string, line: string) => screen.getByLabelText(doorRowLabel(title, line));

// ---------------------------------------------------------------------------
// Your week
// ---------------------------------------------------------------------------

describe('Your week', () => {
  async function openTheWeek() {
    await onYou();
    fireEvent.press(row(YOUR_WEEK_TITLE, TWO_HOURS));
    await screen.findByRole('header', { name: YOUR_WEEK_TITLE });
    await screen.findByLabelText('Tuesday 19:00');
  }

  /** The hours ticked, in the order the grid draws them: 07:00 first, Monday first along it. */
  const ticked = () =>
    screen
      .getAllByRole('checkbox')
      .filter((cell) => cell.props.accessibilityState?.checked === true)
      .map((cell) => String(cell.props.accessibilityLabel));

  it('opens on the week the profile holds, with the count under the grid', async () => {
    await openTheWeek();

    expect(ticked()).toEqual(['Saturday 09:00', 'Tuesday 19:00']);
    expect(screen.getByText(availabilityFootnote({ kind: 'ticked', count: 2 }))).toBeTruthy();
    // Nothing has changed, and the button says so rather than merely being grey — and is
    // green, whole, because the state is the message.
    expect(screen.getByLabelText(SAVED).props.accessibilityState?.disabled).toBe(true);
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);
  });

  it('writes nothing on a tap, and the whole week on Save — then draws the route’s answer', async () => {
    // The route collapses and re-orders: what the screen draws afterwards is this, not the draft.
    transport.on('PUT', WEEKLY_HOURS_PATH, () =>
      json<Wire['WeeklyHoursResponse']>({
        weekly_hours: [
          { day: 2, hour: 19 },
          { day: 3, hour: 19 },
          { day: 6, hour: 9 },
        ],
      }),
    );
    await openTheWeek();

    fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
    expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)).toHaveLength(0);
    expect(screen.getByText(availabilityFootnote({ kind: 'ticked', count: 3 }))).toBeTruthy();
    // Something to send: the accent, and the act's own words.
    expect(fillOf(screen.getByLabelText(SAVE_YOUR_WEEK))).toBe(theme.color.coralInk);

    fireEvent.press(screen.getByLabelText(SAVE_YOUR_WEEK));

    await waitFor(() => expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)[0]?.body).toEqual({
      weekly_hours: [
        { day: 2, hour: 19 },
        { day: 6, hour: 9 },
        { day: 3, hour: 19 },
      ],
    });
    // Saved: the draft is dropped and the grid is the cache, which is the route's week — and
    // the button has turned green under the word.
    expect(await screen.findByLabelText(SAVED)).toBeTruthy();
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);
    expect(ticked()).toEqual(['Saturday 09:00', 'Tuesday 19:00', 'Wednesday 19:00']);

    // And the row's live line follows the cache on the way back.
    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(
          YOUR_WEEK_TITLE,
          weekLine([
            { day: 2, hour: 19 },
            { day: 3, hour: 19 },
            { day: 6, hour: 9 },
          ]),
        ),
      ),
    ).toBeTruthy();
  });

  it('paints a run by dragging, writes nothing until Save, and then sends the painted week', async () => {
    transport.on('PUT', WEEKLY_HOURS_PATH, () =>
      json<Wire['WeeklyHoursResponse']>({
        weekly_hours: [
          { day: 2, hour: 19 },
          { day: 5, hour: 17 },
          { day: 5, hour: 18 },
          { day: 5, hour: 19 },
          { day: 5, hour: 20 },
          { day: 6, hour: 9 },
        ],
      }),
    );
    await openTheWeek();

    // Friday, 17:00 down to 20:00, sampled at the ends.
    paint({ day: 5, hour: 17 }, { day: 5, hour: 20 });

    expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)).toHaveLength(0);
    expect(ticked()).toEqual([
      'Saturday 09:00',
      'Friday 17:00',
      'Friday 18:00',
      'Tuesday 19:00',
      'Friday 19:00',
      'Friday 20:00',
    ]);
    expect(screen.getByText(availabilityFootnote({ kind: 'ticked', count: 6 }))).toBeTruthy();

    fireEvent.press(screen.getByLabelText(SAVE_YOUR_WEEK));

    await waitFor(() => expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)[0]?.body).toEqual({
      weekly_hours: [
        { day: 2, hour: 19 },
        { day: 6, hour: 9 },
        { day: 5, hour: 17 },
        { day: 5, hour: 18 },
        { day: 5, hour: 19 },
        { day: 5, hour: 20 },
      ],
    });
    expect(await screen.findByLabelText(SAVED)).toBeTruthy();
  });

  it('clears a run by dragging from an hour already ticked, and Save is shut again once the week is back', async () => {
    await openTheWeek();

    paint({ day: 2, hour: 17 }, { day: 2, hour: 21 });
    expect(screen.getByLabelText(SAVE_YOUR_WEEK).props.accessibilityState?.disabled).toBe(false);

    // Begun on 19:00, which is ticked: this one clears — and takes the profile's own 19:00
    // with it, which is a change of its own.
    paint({ day: 2, hour: 19 }, { day: 2, hour: 17 });
    expect(ticked()).toEqual(['Saturday 09:00', 'Tuesday 20:00', 'Tuesday 21:00']);

    paint({ day: 2, hour: 20 }, { day: 2, hour: 21 });
    fireEvent.press(screen.getByLabelText('Tuesday 19:00'));

    // Back to the week the profile holds, by a different road: nothing to send.
    expect(ticked()).toEqual(['Saturday 09:00', 'Tuesday 19:00']);
    expect(screen.getByLabelText(SAVED).props.accessibilityState?.disabled).toBe(true);
  });

  it('lets an empty week be saved — the commit’s floor does not bind here', async () => {
    transport.on('PUT', WEEKLY_HOURS_PATH, () =>
      json<Wire['WeeklyHoursResponse']>({ weekly_hours: [] }),
    );
    await openTheWeek();

    fireEvent.press(screen.getByLabelText(CLEAR_ALL));

    expect(ticked()).toEqual([]);
    expect(screen.getByText(availabilityFootnote({ kind: 'empty' }))).toBeTruthy();
    expect(screen.getByLabelText(SAVE_YOUR_WEEK).props.accessibilityState?.disabled).toBe(false);

    fireEvent.press(screen.getByLabelText(SAVE_YOUR_WEEK));

    await waitFor(() => expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('PUT', WEEKLY_HOURS_PATH)[0]?.body).toEqual({ weekly_hours: [] });
    fireEvent.press(await screen.findByLabelText('Back'));
    expect(await screen.findByLabelText(doorRowLabel(YOUR_WEEK_TITLE, weekLine([])))).toBeTruthy();
  });

  it('keeps the draft and says why when the save is refused', async () => {
    transport.on('PUT', WEEKLY_HOURS_PATH, () => errorResponse(403, 'forbidden'));
    await openTheWeek();

    fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
    fireEvent.press(screen.getByLabelText(SAVE_YOUR_WEEK));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(ticked()).toContain('Wednesday 19:00');
    expect(screen.getByLabelText(SAVE_YOUR_WEEK)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Where you play
// ---------------------------------------------------------------------------

describe('Where you play', () => {
  const HOME_CLUBS = '/api/v1/home-clubs';

  /** A club as the search answers a player who holds an area: nearest first, with its distance. */
  const BONARKA: Wire['ClubCardSchema'] = {
    id: '6f1c2a54-0a43-4a39-9d5e-0b5c6d7e8f90',
    name: 'Bonarka Arena',
    district: 'Podgórze',
    distance_km: 2.4,
    sports: ['PADEL'],
    groups: [],
  };
  const BONARKA_LINE = 'Podgórze · 2,4 km · Padel';
  const PICKED = { id: BONARKA.id, name: BONARKA.name, district: BONARKA.district };

  function stubClubs() {
    transport.on('GET', HOME_CLUBS, (request: RecordedRequest) => {
      const q = new URLSearchParams(request.path.split('?')[1] ?? '').get('q') ?? '';
      return json<Wire['HomeClubPageResponse']>({
        clubs: q === 'bon' ? [BONARKA] : [],
        next_page: null,
      });
    });
  }

  async function openTheArea() {
    await onYou();
    fireEvent.press(row(WHERE_YOU_PLAY_TITLE, AREA_LINE));
    await screen.findByRole('header', { name: WHERE_YOU_PLAY_TITLE });
  }

  async function press(label: string) {
    fireEvent.press(screen.getByLabelText(label));
    // The permission, the fix and the write are promises, and the screen is redrawn as each
    // lands.
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
  }

  async function pickBonarka() {
    fireEvent.changeText(screen.getByLabelText(PICK_A_CLUB), 'bon');
    fireEvent.press(await screen.findByLabelText(pickClubLabel(BONARKA.name, BONARKA_LINE)));
  }

  /**
   * The cold-start refresh reads the phone once on the way into the app and puts the cell
   * (ADR-0174 §6) — that read and that write are the launch's, so what the screen does is
   * measured from where they left off.
   */
  const puts = () => transport.requestsTo('PUT', LOCATION_PATH);

  it('says the area is set and how it moves, offers both ways, and reads nothing until pressed', async () => {
    transport.on('PUT', LOCATION_PATH, () => noContent());
    await openTheArea();
    const readsOnArrival = device.reads;
    const putsOnArrival = puts().length;

    expect(screen.getByText(AREA_SET)).toBeTruthy();
    expect(screen.getByText(AREA_UPDATES_LINE)).toBeTruthy();
    // ADR-0200 §10: *You › Where you play offers both ways*, whatever the phone has said.
    expect(screen.getByLabelText(USE_MY_LOCATION)).toBeTruthy();
    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
    // The group this screen sits in, as its eyebrow — *Finding players* no more.
    expect(screen.getByText('Your games')).toBeTruthy();
    expect(screen.queryByText(/Finding players/i)).toBeNull();
    // Arriving on the screen is not a press: the launch's one read is the only one so far.
    expect(readsOnArrival).toBeLessThanOrEqual(1);
    await act(async () => {
      await Promise.resolve();
    });
    expect(device.reads).toBe(readsOnArrival);
    expect(puts()).toHaveLength(putsOnArrival);
  });

  it('reads the phone once on the press, coarsens the fix, and puts the cell', async () => {
    transport.on('PUT', LOCATION_PATH, () => noContent());
    await openTheArea();
    const readsBefore = device.reads;
    const putsBefore = puts().length;

    await press(USE_MY_LOCATION);

    await waitFor(() => expect(puts()).toHaveLength(putsBefore + 1));
    expect(device.reads).toBe(readsBefore + 1);
    // The cell, never the fix: two decimal places, and the precise reading nowhere.
    expect(puts()[putsBefore]?.body).toEqual(AREA_KEPT);
    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
    expect(screen.queryByText(String(PRECISE.latitude))).toBeNull();
  });

  it('picks a club: puts its id, draws it chosen, and offers Change', async () => {
    transport.on('PUT', LOCATION_PATH, () => noContent());
    stubClubs();
    await openTheArea();
    const putsBefore = puts().length;

    await pickBonarka();

    await waitFor(() => expect(puts()).toHaveLength(putsBefore + 1));
    // The id alone, as the commit sends it — never a reading beside it.
    expect(puts()[putsBefore]?.body).toEqual({ club_id: BONARKA.id });
    expect(await screen.findByLabelText(pickedClubLabel(PICKED))).toBeTruthy();
    expect(screen.getByLabelText(CHANGE_CLUB_LABEL)).toBeTruthy();
    expect(screen.queryByLabelText(PICK_A_CLUB)).toBeNull();
    // The phone did not produce this area, so its control does not claim it.
    expect(screen.queryByLabelText(LOCATION_SAVED)).toBeNull();
  });

  it('says it is saving a pick while the write is on its way', async () => {
    transport.on('PUT', LOCATION_PATH, neverResponds());
    stubClubs();
    await openTheArea();

    await pickBonarka();

    expect(await screen.findByLabelText(pickedClubLabel(PICKED))).toBeTruthy();
    expect(screen.getByText(SAVING_WORD)).toBeTruthy();
  });

  it('lets the phone’s reading replace a picked club, on screen as on the server', async () => {
    transport.on('PUT', LOCATION_PATH, () => noContent());
    stubClubs();
    await openTheArea();
    await pickBonarka();
    await screen.findByLabelText(pickedClubLabel(PICKED));
    const putsBefore = puts().length;

    await press(USE_MY_LOCATION);

    await waitFor(() => expect(puts()).toHaveLength(putsBefore + 1));
    expect(puts()[putsBefore]?.body).toEqual(AREA_KEPT);
    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
    expect(screen.queryByLabelText(pickedClubLabel(PICKED))).toBeNull();
    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
  });

  it('lets go of a club the server no longer knows, and says so in its own sentence', async () => {
    transport.on('PUT', LOCATION_PATH, () => errorResponse(400, 'location_club_unknown'));
    stubClubs();
    await openTheArea();

    await pickBonarka();

    // Read off the code: *check the details above* would point at a club already let go of.
    expect(await screen.findByText(AREA_WRITE_REFUSAL.location_club_unknown ?? '')).toBeTruthy();
    expect(screen.queryByLabelText(pickedClubLabel(PICKED))).toBeNull();
    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
  });

  it('reads the profile again once a pick lands, so the tab follows the area', async () => {
    // The You tab under this screen observes the read for the whole visit, so the invalidation
    // refetches at once and the re-read is what is counted.
    transport.on('PUT', LOCATION_PATH, () => noContent());
    stubClubs();
    await openTheArea();
    await act(async () => {
      await Promise.resolve();
    });
    const readsBefore = transport.requestsTo('GET', PROFILE_SURFACE_PATH).length;

    await pickBonarka();

    await waitFor(() =>
      expect(transport.requestsTo('GET', PROFILE_SURFACE_PATH).length).toBeGreaterThan(readsBefore),
    );
  });

  it('draws the step’s refusal — undo it or pick a club — and nothing about finishing setting up', async () => {
    device.state = 'undetermined';
    device.answer = 'denied';
    await openTheArea();

    await press(USE_MY_LOCATION);

    expect(await screen.findByText(ACCESS_TITLE.refused)).toBeTruthy();
    expect(screen.getByText(ACCESS_HOW_TO.refused)).toBeTruthy();
    expect(screen.queryByText(/finish setting up/)).toBeNull();
    expect(screen.getByLabelText(USE_MY_LOCATION)).toBeTruthy();
    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
    expect(puts()).toHaveLength(0);
  });

  it('sends a player whose permission is off in Settings there, rather than to a prompt', async () => {
    device.state = 'blocked';
    await openTheArea();

    await press(USE_MY_LOCATION);

    expect(await screen.findByText(ACCESS_TITLE.blocked)).toBeTruthy();
    expect(screen.getByLabelText(OPEN_SETTINGS)).toBeTruthy();
    expect(screen.queryByLabelText(USE_MY_LOCATION)).toBeNull();
    // The club is still there: Settings is one way back to an area, not the only one.
    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
  });

  it('says so when the write is refused, with the control still offered', async () => {
    transport.on('PUT', LOCATION_PATH, () => errorResponse(403, 'forbidden'));
    await openTheArea();

    await press(USE_MY_LOCATION);

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByLabelText(USE_MY_LOCATION)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The live lines while a read is not in
// ---------------------------------------------------------------------------

describe('a row whose read has not answered', () => {
  it('is spoken as its title alone, and says why once the read has failed', async () => {
    transport.on('GET', PROFILE_SURFACE_PATH, () => errorResponse(403, 'forbidden'));
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('You'));

    // The failure names the recovery, on the row, rather than the row going quiet.
    expect(await screen.findByLabelText(`${YOUR_WEEK_TITLE}, `, { exact: false })).toBeTruthy();
    expect(screen.queryByLabelText(doorRowLabel(YOUR_WEEK_TITLE, TWO_HOURS))).toBeNull();
  });
});
