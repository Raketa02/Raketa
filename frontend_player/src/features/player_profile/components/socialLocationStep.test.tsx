/**
 * The location step, driven through the real route tree with the socket and the device
 * faked — and nothing else.
 *
 * Two edges are outside the app and both are described per test: the network, through
 * `installTransport`, and the device's own position, through the app's **own port**. The
 * native module is never touched — it has no JS implementation a test could drive, which is
 * the whole reason `LocationPort` exists, and it is also why *granted* and *refused* can
 * both be exercised here at all. Everything between the two runs for real: the router, the
 * domain rule that coarsens a fix, the store and the screen.
 *
 * **The refusal is half the ticket.** The area is what every distance to a club is measured
 * from, so the step requires one — *Continue* is drawn only once there is an area — and a player
 * who says no is offered *Pick a club near where you play*, and the club she picks is her area
 * (ADR-0200 §10, #733). A suite that only walked the granted path would prove the case that was
 * never in doubt.
 *
 * Every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told — **with one deliberate exception**. The draft is read
 * directly once, because *the area is held in the part's draft* is a requirement of this
 * step and the commit that would make it observable is a later ticket. The figure on screen
 * is asserted separately, so the two together say the drawn area and the kept area are one
 * pair.
 */

import { focusManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  PROFILE_SURFACE_PATH,
  launchSignedIn,
  resetLocation,
  stubGate as stubGateWith,
  stubLocation,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { fakeLocation, type FakeLocation } from '@/test-support/platform';
import {
  installTransport,
  json,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useProfileDraft } from '../store/profileDraft.store';

import { FINISH_LABEL } from './commitPresentation';
import {
  ACCESS_HOW_TO,
  ACCESS_TITLE,
  CHANGE_CLUB_LABEL,
  CONTINUE,
  LOCATION_SAVED,
  MORE_CLUBS,
  NO_CLUB_NOTE,
  NO_FIX_BODY,
  NO_FIX_TITLE,
  OPEN_SETTINGS,
  PICK_A_CLUB,
  USE_MY_LOCATION,
  WHY_BODY,
  WHY_TITLE,
  pickClubLabel,
  pickedClubLabel,
} from './locationPresentation';

/** One rating: the first part is behind this player, and the second one is not. */
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

/**
 * A reading with metres in it, and the area it falls in.
 *
 * The two are stated separately on purpose: every assertion about what is *kept* names
 * `AREA_KEPT`, and `PRECISE` appears only where the point is that it is **not** there.
 */
const PRECISE = { latitude: 41.3874, longitude: 2.1686, accuracyMetres: 12 };
const AREA_KEPT = { latitude: 41.39, longitude: 2.17 };

/** Somewhere else entirely — what a player who travelled comes back to the app holding. */
const ELSEWHERE = { latitude: 40.4168, longitude: -3.7038, accuracyMetres: 20 };
const ELSEWHERE_KEPT = { latitude: 40.42, longitude: -3.7 };

/** A reading, as the draft holds one. */
const reading = (area: { latitude: number; longitude: number }) => ({ kind: 'reading', area });

const HOME_CLUBS = '/api/v1/home-clubs';

/**
 * Two clubs, as the home-club search answers a player with **no area yet**: A–Z, and no distance
 * — there is nothing to measure from (`distance_km` `null`). The groups at a club ride along on
 * the wire and are not drawn here.
 */
const BONARKA: Wire['ClubCardSchema'] = {
  id: '6f1c2a54-0a43-4a39-9d5e-0b5c6d7e8f90',
  name: 'Bonarka Arena',
  district: 'Podgórze',
  distance_km: null,
  sports: ['PADEL', 'TENNIS'],
  groups: [],
};
const BOREK: Wire['ClubCardSchema'] = {
  id: '7a2d3b65-1b54-4b4a-8e6f-1c6d7e8f9a01',
  name: 'Borek Padel',
  district: 'Borek Fałęcki',
  distance_km: null,
  sports: ['PADEL'],
  groups: [],
};

/** `q` and `page` off a recorded request — the transport routes on the path without them. */
function queryOf(request: RecordedRequest) {
  const params = new URLSearchParams(request.path.split('?')[1] ?? '');
  return { q: params.get('q') ?? '', page: Number(params.get('page') ?? '1') };
}

/** The home-club search, answering each text from a table of pages. */
function stubClubs(answers: Readonly<Record<string, readonly Wire['HomeClubPageResponse'][]>>) {
  transport.on('GET', HOME_CLUBS, (request) => {
    const { q, page } = queryOf(request);
    const pages = answers[q] ?? [{ clubs: [], next_page: null }];
    return json<Wire['HomeClubPageResponse']>(pages[page - 1] ?? { clubs: [], next_page: null });
  });
}

const searches = () => transport.requestsTo('GET', HOME_CLUBS).map(queryOf);

/** Type into the picker's one field — it is named by the offer itself. */
const searchFor = (text: string) => fireEvent.changeText(screen.getByLabelText(PICK_A_CLUB), text);

/** A club's card, by the name its head is spoken with. */
const clubCard = (club: Wire['ClubCardSchema'], line: string) =>
  screen.findByLabelText(pickClubLabel(club.name, line));

/** The commit, answered as the real route answers it, and the gate moved on as the server would. */
function stubCommit() {
  transport.on('POST', PROFILE_SURFACE_PATH, () => {
    stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: true });
    return json<Wire['PlayerProfileResponse']>(
      {
        player_id: '11111111-2222-4333-8444-555555555555',
        social_tag_ids: ['PLAYS_TO_WIN', 'HERE_TO_IMPROVE'],
        photo_ids: [],
        weekly_hours: [{ day: 3, hour: 19 }],
        location: { latitude: 50.03, longitude: 19.95 },
        created_at: '2026-11-04T10:00:00Z',
        updated_at: '2026-11-04T10:00:00Z',
      },
      201,
    );
  });
}

const commits = () => transport.requestsTo('POST', PROFILE_SURFACE_PATH);

/**
 * Whether the step is holding an area, read the way a player reads it: off the one control
 * that asks for one.
 *
 * **Nothing on this screen prints a coordinate any more**, so the control's own words are
 * where the state is legible — `Use my location` before, `Location saved` after. That is
 * also the assertion the design system wants made: the green fill is never the whole fact,
 * so a suite that could only see the fill would be testing the wrong half.
 */
const areaShown = () => screen.queryByLabelText(LOCATION_SAVED) !== null;

/** What the draft is holding. The only place an area is observable now, so it is read. */
const areaKept = () => useProfileDraft.getState().draft?.location;

let transport: Transport;
let device: FakeLocation;

/** A launch by a player the gate owes the second part to, walked as far as step four. */
async function reachTheLocationStep() {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);
  stubLocation(device);

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));
  await waitFor(() => expect(screen).toHavePathname('/intro'));

  // Nothing written: the intro is optional, and *Next* on an empty box carries none.
  fireEvent.press(screen.getByLabelText('Next'));
  await waitFor(() => expect(screen).toHavePathname('/photos'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/availability'));
  // The week has a floor of one since ADR-0102, so walking past this step means answering
  // it. A single cell is the whole of what it asks for.
  fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/location'));
  await screen.findByText('Where do you play?');
}

/** Press the one control that reaches the device, and let the permission and the fix land. */
async function askTheDevice() {
  fireEvent.press(screen.getByLabelText(USE_MY_LOCATION));
  // The permission and the fix are both promises, and the screen is redrawn as each lands.
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

/** What the OS does when the player leaves the app and comes back to it. */
async function leaveAndReturn() {
  await act(async () => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
    await Promise.resolve();
    await Promise.resolve();
  });
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useProfileDraft.getState().reset();
  focusManager.setFocused(true);
  // The ordinary device: never asked, would say yes, and knows where it is. Every case that
  // wants another answer says so before launching.
  device = fakeLocation({ fix: PRECISE });
});

afterEach(() => {
  transport.restore();
  resetLocation();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// Before anybody is asked anything
// ---------------------------------------------------------------------------

describe('arriving on the step', () => {
  it('explains what the area is for before the phone asks for anything', async () => {
    await reachTheLocationStep();

    expect(screen.getByText(WHY_TITLE)).toBeTruthy();
    expect(screen.getByText(WHY_BODY)).toBeTruthy();

    // Story 54, and the assertion that makes it a fact: an untouched permission is a
    // permission nobody prompted for. iOS shows its dialog once per install, so a prompt
    // that arrives before the sentence spends the only ask this app gets.
    expect(device.state).toBe('undetermined');
    expect(device.reads).toBe(0);
  });

  it('reads nothing until the player presses, and the control says which act it offers', async () => {
    await reachTheLocationStep();

    expect(areaShown()).toBe(false);
    expect(screen.getByLabelText(USE_MY_LOCATION)).toBeTruthy();
  });

  it('draws no Continue, and no club to pick, before anything has been asked', async () => {
    // ADR-0200 §10: *Continue* appears only once an area is set, and the club is the answer to a
    // refusal — not a second question put to somebody whose phone has not been asked yet.
    await reachTheLocationStep();

    expect(screen.queryByLabelText(CONTINUE)).toBeNull();
    expect(screen.queryByLabelText(/without/i)).toBeNull();
    expect(screen.queryByLabelText(PICK_A_CLUB)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The player says yes
// ---------------------------------------------------------------------------

describe('granting the permission', () => {
  it('captures one fix and says so on the control that asked for it', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(device.state).toBe('granted');
    // One fix. Nothing here watches, polls or subscribes — a stream of positions is a
    // movement trail, which is a different privacy class from the one that was asked about.
    expect(device.reads).toBe(1);
    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
  });

  /**
   * Story 55, and now the stronger claim: **no reading of any kind reaches the screen.** The
   * precise fix never left the hook and the coarse pair is not printed either — a player has
   * no use for their own latitude, and a screen of figures reads as *this is what we took*
   * rather than *this is what we rounded away*.
   */
  it('draws no coordinate at all, coarse or precise', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByLabelText(LOCATION_SAVED);

    expect(screen.queryByText(/3874|1686/)).toBeNull();
    expect(screen.queryByText(/12 m|accuracy/i)).toBeNull();
    // The coarse pair, in every shape this app would have written it in.
    expect(screen.queryByText(/41,39|2,17|41\.39|2\.17/)).toBeNull();
    expect(screen.queryByText(/degrees/i)).toBeNull();
  });

  it('holds the coarse area in the part draft, and only the coarse one', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByLabelText(LOCATION_SAVED);

    // The draft is where an area is observable now, and what is kept is the rounded pair —
    // which is also the pair the commit will send.
    expect(areaKept()).toEqual(reading(AREA_KEPT));
  });

  it('continues plainly once there is an area', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByLabelText(LOCATION_SAVED);

    fireEvent.press(screen.getByLabelText(CONTINUE));

    await waitFor(() => expect(screen).toHavePathname('/gender'));
  });
});

// ---------------------------------------------------------------------------
// The player says no
// ---------------------------------------------------------------------------

describe('refusing the permission', () => {
  beforeEach(() => {
    device = fakeLocation({ answer: 'denied', fix: PRECISE });
  });

  it('says how to undo it, or pick a club, and offers the club', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(await screen.findByText(ACCESS_TITLE.refused)).toBeTruthy();
    expect(screen.getByText(ACCESS_HOW_TO.refused)).toBeTruthy();
    // No fix was read: the port answers none without a permission, and the control does not
    // pretend otherwise by claiming to have saved something.
    expect(areaShown()).toBe(false);
    // The other way in, drawn as the one field it is.
    expect(screen.getByText(PICK_A_CLUB)).toBeTruthy();
    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
  });

  /**
   * The step requires an area — but it does not hold anybody hostage either: a player stuck
   * behind a permission she does not want to give has the club, and nothing else is a way past.
   */
  it('lets nobody past without an area — no Continue until a club is picked', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.refused);

    expect(screen.queryByLabelText(CONTINUE)).toBeNull();
    // Nothing was claimed on their behalf. An unanswered location is absent, never a zero
    // pair.
    expect(areaKept()).toBeUndefined();
  });

  it('offers the prompt again on the next press', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.refused);

    // The player changed their mind, which is the whole reason a refused permission is not
    // a permanent one: the next press shows the OS dialog again.
    device.answer = 'granted';
    await askTheDevice();

    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
    expect(screen.queryByText(ACCESS_TITLE.refused)).toBeNull();
    // The phone answered, so the club is no longer the question.
    expect(screen.queryByLabelText(PICK_A_CLUB)).toBeNull();
  });

  /** A return to the app is not a press. Re-prompting on every foreground is a wall. */
  it('does not ask again when the app comes back', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.refused);

    device.answer = 'granted';
    await leaveAndReturn();

    expect(device.state).toBe('denied');
    expect(device.reads).toBe(0);
    expect(areaShown()).toBe(false);
  });
});

describe('picking a club near where you play', () => {
  beforeEach(() => {
    device = fakeLocation({ answer: 'denied', fix: PRECISE });
  });

  /** The step, refused, with the club field on screen. */
  async function refuseAndOfferTheClub() {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByLabelText(PICK_A_CLUB);
  }

  it('searches the clubs by what is typed, and lists them as the search answers — A–Z, no distance', async () => {
    stubClubs({ bo: [{ clubs: [BONARKA, BOREK], next_page: null }] });
    await refuseAndOfferTheClub();

    searchFor('bo');

    // The home-club search, asked with the text — a player with no area gets the clubs A–Z,
    // and no distance is drawn because there is nothing yet to measure one from.
    expect(await clubCard(BONARKA, 'Podgórze · Padel, Tennis')).toBeTruthy();
    expect(await clubCard(BOREK, 'Borek Fałęcki · Padel')).toBeTruthy();
    expect(searches()).toContainEqual({ q: 'bo', page: 1 });
    expect(screen.queryByText(/km/)).toBeNull();
    // A club's groups are New group's question, not this one's.
    expect(screen.queryByText(/members/)).toBeNull();
    expect(screen.queryByLabelText(CONTINUE)).toBeNull();
  });

  it('takes the club as the area, draws it chosen, and shows Continue', async () => {
    stubClubs({ bon: [{ clubs: [BONARKA], next_page: null }] });
    await refuseAndOfferTheClub();

    searchFor('bon');
    fireEvent.press(await clubCard(BONARKA, 'Podgórze · Padel, Tennis'));

    const club = { id: BONARKA.id, name: BONARKA.name, district: BONARKA.district };
    expect(await screen.findByLabelText(pickedClubLabel(club))).toBeTruthy();
    expect(screen.queryByLabelText(PICK_A_CLUB)).toBeNull();
    expect(areaKept()).toEqual({ kind: 'club', club });
    // The phone's control did not produce this area, so it does not claim it.
    expect(areaShown()).toBe(false);
    expect(screen.getByLabelText(CONTINUE)).toBeTruthy();
  });

  /** The acceptance walk: refused, a club picked, and the commit carrying it as `club_id`. */
  it('sends the club as the location when the part is finished', async () => {
    stubClubs({ bon: [{ clubs: [BONARKA], next_page: null }] });
    stubCommit();
    await refuseAndOfferTheClub();

    searchFor('bon');
    fireEvent.press(await clubCard(BONARKA, 'Podgórze · Padel, Tennis'));
    fireEvent.press(await screen.findByLabelText(CONTINUE));
    await waitFor(() => expect(screen).toHavePathname('/gender'));
    fireEvent.press(screen.getByLabelText('Woman'));
    fireEvent.press(screen.getByLabelText(FINISH_LABEL));

    await waitFor(() => expect(commits()).toHaveLength(1));
    // The id alone: the server rounds the club's point to the cell, and the name and the
    // district the step drew stay on the phone. No reading rides beside it.
    expect((commits()[0]?.body as Wire['CommitPlayerProfileRequest']).location).toEqual({
      club_id: BONARKA.id,
    });
  });

  it('lets go of the club on Change, and offers the search again', async () => {
    stubClubs({ bon: [{ clubs: [BONARKA], next_page: null }] });
    await refuseAndOfferTheClub();
    searchFor('bon');
    fireEvent.press(await clubCard(BONARKA, 'Podgórze · Padel, Tennis'));
    await screen.findByLabelText(CONTINUE);

    fireEvent.press(screen.getByLabelText(CHANGE_CLUB_LABEL));

    expect(await screen.findByLabelText(PICK_A_CLUB)).toBeTruthy();
    expect(screen.queryByLabelText(CONTINUE)).toBeNull();
    expect(areaKept()).toBeUndefined();
  });

  it('says so when no club is called that, and what can be picked', async () => {
    stubClubs({});
    await refuseAndOfferTheClub();

    searchFor('zzz');

    expect(await screen.findByText('No club called “zzz”')).toBeTruthy();
    expect(screen.getByText(NO_CLUB_NOTE)).toBeTruthy();
  });

  it('asks for the next twenty when there are more', async () => {
    const page2: Wire['ClubCardSchema'] = { ...BOREK, id: 'c0ffee00-0000-4000-8000-000000000021' };
    stubClubs({
      bo: [
        { clubs: [BONARKA], next_page: 2 },
        { clubs: [page2], next_page: null },
      ],
    });
    await refuseAndOfferTheClub();
    searchFor('bo');
    await clubCard(BONARKA, 'Podgórze · Padel, Tennis');

    fireEvent.press(screen.getByLabelText(MORE_CLUBS));

    expect(await clubCard(page2, 'Borek Fałęcki · Padel')).toBeTruthy();
    expect(searches()).toContainEqual({ q: 'bo', page: 2 });
    expect(screen.queryByLabelText(MORE_CLUBS)).toBeNull();
  });

  it('finds the club still chosen after walking on and back', async () => {
    stubClubs({ bon: [{ clubs: [BONARKA], next_page: null }] });
    await refuseAndOfferTheClub();
    searchFor('bon');
    fireEvent.press(await clubCard(BONARKA, 'Podgórze · Padel, Tennis'));
    fireEvent.press(await screen.findByLabelText(CONTINUE));
    await waitFor(() => expect(screen).toHavePathname('/gender'));

    fireEvent.press(screen.getByLabelText('Back to Where do you play?'));
    await waitFor(() => expect(screen).toHavePathname('/location'));

    // Nobody refused anything on this visit — the club is drawn because it is the answer.
    const club = { id: BONARKA.id, name: BONARKA.name, district: BONARKA.district };
    expect(await screen.findByLabelText(pickedClubLabel(club))).toBeTruthy();
    expect(screen.getByLabelText(CONTINUE)).toBeTruthy();
  });

  /**
   * ADR-0200 §10: once the phone may be read, its reading replaces a club picked by hand. The
   * player allowed location in Settings and came back; the step's own foreground re-read does it.
   */
  it('gives way to the phone’s reading once the permission exists', async () => {
    stubClubs({ bon: [{ clubs: [BONARKA], next_page: null }] });
    await refuseAndOfferTheClub();
    searchFor('bon');
    fireEvent.press(await clubCard(BONARKA, 'Podgórze · Padel, Tennis'));
    await screen.findByLabelText(CONTINUE);

    device.state = 'granted';
    await leaveAndReturn();

    await waitFor(() => expect(areaKept()).toEqual(reading(AREA_KEPT)));
    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
    expect(screen.getByLabelText(CONTINUE)).toBeTruthy();
  });
});

describe('a permission that was turned off in Settings', () => {
  beforeEach(() => {
    device = fakeLocation({ state: 'blocked', fix: PRECISE });
  });

  /**
   * The OS resolves a blocked permission itself, instantly and negatively, without showing
   * the player anything — so *press again* is the one sentence this screen must not say.
   */
  it('sends the player to Settings rather than to a prompt that will not appear', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(await screen.findByText(ACCESS_TITLE.blocked)).toBeTruthy();
    expect(screen.getByText(ACCESS_HOW_TO.blocked)).toBeTruthy();
    expect(screen.getByLabelText(OPEN_SETTINGS)).toBeTruthy();
    expect(device.reads).toBe(0);
  });

  it('offers the club, and nothing else past the step', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByText(ACCESS_TITLE.blocked);

    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
    expect(screen.queryByLabelText(CONTINUE)).toBeNull();
  });
});

describe('a phone that cannot place itself', () => {
  beforeEach(() => {
    // Allowed, asked, and no fix — indoors, underground, or a device with no signal.
    device = fakeLocation({ fix: null });
  });

  it('says so rather than leaving the press looking ignored', async () => {
    await reachTheLocationStep();

    await askTheDevice();

    expect(await screen.findByText(NO_FIX_TITLE)).toBeTruthy();
    expect(screen.getByText(NO_FIX_BODY)).toBeTruthy();
    // The third refusal, answered as the other two are: the club, and no way past without one.
    expect(screen.getByLabelText(PICK_A_CLUB)).toBeTruthy();
    expect(screen.queryByLabelText(CONTINUE)).toBeNull();
  });

  /**
   * The silent read on arrival found nothing, and nobody asked for it. So the control still
   * says *use my location* — claiming an area would be a lie — and nothing scolds, because
   * a walk past a basement is not something the player did.
   */
  it('says nothing at all about a read nobody asked for', async () => {
    device = fakeLocation({ state: 'granted', fix: null });

    await reachTheLocationStep();

    await waitFor(() => expect(device.reads).toBe(1));
    expect(areaShown()).toBe(false);
    expect(screen.getByLabelText(USE_MY_LOCATION)).toBeTruthy();
    expect(screen.queryByText(NO_FIX_TITLE)).toBeNull();
    // Nobody asked, so nothing was refused: the club is not offered for a read nobody saw.
    expect(screen.queryByLabelText(PICK_A_CLUB)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Coming back to the app
// ---------------------------------------------------------------------------

describe('foregrounding the app with the permission granted', () => {
  it('re-reads the fix, so what is held is near where the player is', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByLabelText(LOCATION_SAVED);

    // The player went somewhere and came back. Story 58: the moment an area can silently
    // stop being true is the one where they were elsewhere in between. With nothing drawn,
    // the draft is where the replacement is observable — so it is read here.
    device.fix = ELSEWHERE;
    await leaveAndReturn();

    await waitFor(() => expect(areaKept()).toEqual(reading(ELSEWHERE_KEPT)));
    expect(device.reads).toBe(2);
    // And the control does not flicker back: it was settled and it stays settled.
    expect(areaShown()).toBe(true);
  });

  it('re-reads on arrival too, when the permission is already granted', async () => {
    device = fakeLocation({ state: 'granted', fix: PRECISE });

    await reachTheLocationStep();

    // Nobody was prompted — the permission was already there — and the control is already
    // settled without the player having had to press anything.
    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
    expect(device.reads).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// The area inside the part
// ---------------------------------------------------------------------------

describe('walking away from the step and back', () => {
  it('finds the same area, without asking the device again', async () => {
    await reachTheLocationStep();
    await askTheDevice();
    await screen.findByLabelText(LOCATION_SAVED);

    fireEvent.press(screen.getByLabelText(CONTINUE));
    await waitFor(() => expect(screen).toHavePathname('/gender'));

    fireEvent.press(screen.getByLabelText('Back to Where do you play?'));
    await waitFor(() => expect(screen).toHavePathname('/location'));

    expect(await screen.findByLabelText(LOCATION_SAVED)).toBeTruthy();
    expect(areaKept()).toEqual(reading(AREA_KEPT));
    // The permission is granted by now, so arriving re-reads — and the pair is the same
    // one, which is why nothing about the screen changed.
    expect(device.state).toBe('granted');
  });
});
