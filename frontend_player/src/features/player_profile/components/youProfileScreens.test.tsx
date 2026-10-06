/**
 * **The profile's rows on the You tab, walked the way a player walks them** — the real route
 * tree, the real bar, and only `fetch` and the device faked
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * Each screen is an onboarding step's control under the tab's chrome, and the steps' own
 * suites already prove the controls. What is proved here is what the tab added: **a draft
 * until the button** — the week and the radius write only on *Save*, and the route's answer is
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
  type Transport,
  type Wire,
} from '@/test-support/transport';
import { paint } from '@/test-support/weekGridTouch';

import { availabilityFootnote } from './availabilityPresentation';
import {
  ACCESS_HOW_TO,
  ACCESS_TITLE,
  AREA_UPDATES_LINE,
  LOCATION_SAVED,
  OPEN_SETTINGS,
  USE_MY_LOCATION,
} from './locationPresentation';
import { RADIUS_LABEL } from './radiusPresentation';
import {
  AREA_LINE,
  AREA_SET,
  CLEAR_ALL,
  HOW_FAR_TO_LOOK_TITLE,
  READ_AGAIN,
  SAVE,
  SAVED,
  SAVE_YOUR_WEEK,
  WHERE_YOU_PLAY_TITLE,
  YOUR_WEEK_TITLE,
  radiusLine,
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

/** Two hours and a twelve-kilometre radius — the profile as the tab opens on it. */
const SURFACE = profileSurface({
  weekly_hours: [
    { day: 2, hour: 19 },
    { day: 6, hour: 9 },
  ],
  search_radius_km: 12,
  play_intents: { PADEL: 'FOR_FUN' },
});

const WEEKLY_HOURS_PATH = '/api/v1/players/me/weekly-hours';
const RADIUS_PATH = '/api/v1/players/me/search-radius';
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
// How far to look
// ---------------------------------------------------------------------------

describe('How far to look', () => {
  const theSlider = () => screen.getByLabelText(RADIUS_LABEL);
  const step = (action: 'increment' | 'decrement') =>
    fireEvent(theSlider(), 'accessibilityAction', { nativeEvent: { actionName: action } });

  async function openTheRadius() {
    await onYou();
    fireEvent.press(row(HOW_FAR_TO_LOOK_TITLE, radiusLine(12)));
    await screen.findByRole('header', { name: HOW_FAR_TO_LOOK_TITLE });
    await screen.findByLabelText(RADIUS_LABEL);
  }

  it('opens at the profile’s radius, with Saved shut', async () => {
    await openTheRadius();

    expect(theSlider().props.accessibilityValue.now).toBe(12);
    expect(screen.getByLabelText(SAVED).props.accessibilityState?.disabled).toBe(true);
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);
  });

  it('writes nothing as the slider moves, and the number on Save — then draws the route’s answer', async () => {
    // The write path re-snaps: it answers with the radius as held, which is what is drawn.
    transport.on('PUT', RADIUS_PATH, () =>
      json<Wire['SearchRadiusResponse']>({ search_radius_km: 15 }),
    );
    await openTheRadius();

    step('increment');
    step('increment');
    expect(theSlider().props.accessibilityValue.now).toBe(14);
    expect(transport.requestsTo('PUT', RADIUS_PATH)).toHaveLength(0);

    fireEvent.press(screen.getByLabelText(SAVE));

    await waitFor(() => expect(transport.requestsTo('PUT', RADIUS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('PUT', RADIUS_PATH)[0]?.body).toEqual({ search_radius_km: 14 });
    expect(await screen.findByLabelText(SAVED)).toBeTruthy();
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);
    expect(theSlider().props.accessibilityValue.now).toBe(15);

    fireEvent.press(screen.getByLabelText('Back'));
    expect(
      await screen.findByLabelText(doorRowLabel(HOW_FAR_TO_LOOK_TITLE, radiusLine(15))),
    ).toBeTruthy();
  });

  it('shuts Save again when the slider is moved back to the number held', async () => {
    await openTheRadius();

    step('increment');
    expect(screen.getByLabelText(SAVE)).toBeTruthy();
    expect(fillOf(screen.getByLabelText(SAVE))).toBe(theme.color.coralInk);
    step('decrement');

    expect(screen.getByLabelText(SAVED).props.accessibilityState?.disabled).toBe(true);
    expect(fillOf(screen.getByLabelText(SAVED))).toBe(theme.color.mintInk);
    expect(transport.requestsTo('PUT', RADIUS_PATH)).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// Where you play
// ---------------------------------------------------------------------------

describe('Where you play', () => {
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

  /**
   * The cold-start refresh reads the phone once on the way into the app and puts the cell
   * (ADR-0174 §6) — that read and that write are the launch's, so what the screen does is
   * measured from where they left off.
   */
  const puts = () => transport.requestsTo('PUT', LOCATION_PATH);

  it('says the area is set and how it moves, and reads nothing until pressed', async () => {
    transport.on('PUT', LOCATION_PATH, () => noContent());
    await openTheArea();
    const readsOnArrival = device.reads;
    const putsOnArrival = puts().length;

    expect(screen.getByText(AREA_SET)).toBeTruthy();
    expect(screen.getByText(AREA_UPDATES_LINE)).toBeTruthy();
    expect(screen.getByLabelText(READ_AGAIN)).toBeTruthy();
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

    await press(READ_AGAIN);

    await waitFor(() => expect(puts()).toHaveLength(putsBefore + 1));
    expect(device.reads).toBe(readsBefore + 1);
    // The cell, never the fix: two decimal places, and the precise reading nowhere.
    expect(puts()[putsBefore]?.body).toEqual(AREA_KEPT);
    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
    expect(screen.queryByText(String(PRECISE.latitude))).toBeNull();
  });

  it('draws the step’s refusal, without the step’s clause about finishing setting up', async () => {
    device.state = 'undetermined';
    device.answer = 'denied';
    await openTheArea();

    await press(READ_AGAIN);

    expect(await screen.findByText(ACCESS_TITLE.refused)).toBeTruthy();
    expect(screen.getByText(ACCESS_HOW_TO.refused)).toBeTruthy();
    expect(screen.queryByText(/finish setting up/)).toBeNull();
    // The note names *Use my location*, so that is what the control now says.
    expect(screen.getByLabelText(USE_MY_LOCATION)).toBeTruthy();
    expect(puts()).toHaveLength(0);
  });

  it('sends a player whose permission is off in Settings there, rather than to a prompt', async () => {
    device.state = 'blocked';
    await openTheArea();

    await press(READ_AGAIN);

    expect(await screen.findByText(ACCESS_TITLE.blocked)).toBeTruthy();
    expect(screen.getByLabelText(OPEN_SETTINGS)).toBeTruthy();
    expect(screen.queryByLabelText(READ_AGAIN)).toBeNull();
  });

  it('says so when the write is refused, with the control still offered', async () => {
    transport.on('PUT', LOCATION_PATH, () => errorResponse(403, 'forbidden'));
    await openTheArea();

    await press(READ_AGAIN);

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByLabelText(READ_AGAIN)).toBeTruthy();
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
