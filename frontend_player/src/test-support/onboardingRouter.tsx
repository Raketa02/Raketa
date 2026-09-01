/**
 * The onboarding route tree, as a test harness.
 *
 * Onboarding is driven through the **real router** — the same route files `src/app/`
 * ships, the same layouts, the same redirects — with only `fetch` faked. So every suite
 * that walks the flow needs the same tree and the same providers, and a second copy of
 * either is a second answer to "what does this app's routing look like".
 *
 * Tests live outside `src/app/` and import the route files, per docs/architecture.md
 * Part 16. Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

import { QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { Slot } from 'expo-router';
import { renderRouter } from 'expo-router/testing-library';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import AppLayout from '@/app/(app)/_layout';
import TabsLayout from '@/app/(app)/(tabs)/_layout';
import AroundRoute from '@/app/(app)/(tabs)/around';
import ChatsRoute from '@/app/(app)/(tabs)/chats';
import NowRoute from '@/app/(app)/(tabs)/index';
import BuilderRoute from '@/app/(app)/(tabs)/play/builder';
import DeckRoute from '@/app/(app)/(tabs)/play/deck';
import PoolRoute from '@/app/(app)/(tabs)/play/pool';
import FindAGameRoute from '@/app/(app)/(tabs)/play/index';
import YouRoute from '@/app/(app)/(tabs)/you';
import AuthLayout from '@/app/(auth)/_layout';
import SignInRoute from '@/app/(auth)/sign-in';
import AvailabilityRoute from '@/app/(onboarding)/availability';
import DataRoute from '@/app/(onboarding)/data';
import DoneRoute from '@/app/(onboarding)/done';
import LocationRoute from '@/app/(onboarding)/location';
import OnboardingLayout from '@/app/(onboarding)/_layout';
import OptInRoute from '@/app/(onboarding)/opt-in';
import PhotosRoute from '@/app/(onboarding)/photos';
import QuestionRoute from '@/app/(onboarding)/question/[assessmentId]';
import GenderRoute from '@/app/(onboarding)/gender';
import RadiusRoute from '@/app/(onboarding)/radius';
import ResultRoute from '@/app/(onboarding)/result/[assessmentId]';
import ReviewRoute from '@/app/(onboarding)/review/[assessmentId]';
import SportsRoute from '@/app/(onboarding)/sports';
import TagsRoute from '@/app/(onboarding)/tags';
import WelcomeRoute from '@/app/(onboarding)/welcome';
import { PLACEHOLDER_COPY } from '@/features/shell/types';
import { beginSession } from '@/shared/lib/auth';
import {
  ImagePickingProvider,
  LocationProvider,
  type ImagePickingPort,
  type LocationPort,
} from '@/shared/lib/platform';
import { queryClient } from '@/shared/lib/query-client';

import { json, type Transport, type Wire } from './transport';

/**
 * The Now tab's one line — which is what *the player is in the app* looks like on screen.
 *
 * The gate's fourth destination is the shell's root, and the shell's root is the Now tab, so
 * every suite that asserts a launch, a finish or a commit landed in the app is asserting this
 * sentence. Taken from the shell's own copy rather than spelled here, because a placeholder is
 * exactly the kind of sentence that gets reworded and eight suites holding a string literal is
 * eight red tests for a wording change.
 */
export const NOW_TAB_LINE = PLACEHOLDER_COPY.now.line;

export const ONBOARDING_ROUTES = {
  _layout: TestRoot,
  '(app)/_layout': AppLayout,
  '(app)/(tabs)/_layout': TabsLayout,
  // The five-tab shell. Play is a directory because the deck, the builder and the pool
  // land under it, and the bar reads its active column off that first segment.
  '(app)/(tabs)/index': NowRoute,
  '(app)/(tabs)/around': AroundRoute,
  '(app)/(tabs)/play/index': FindAGameRoute,
  '(app)/(tabs)/play/deck': DeckRoute,
  '(app)/(tabs)/play/builder': BuilderRoute,
  '(app)/(tabs)/play/pool': PoolRoute,
  '(app)/(tabs)/chats': ChatsRoute,
  '(app)/(tabs)/you': YouRoute,
  '(auth)/_layout': AuthLayout,
  '(auth)/sign-in': SignInRoute,
  '(onboarding)/_layout': OnboardingLayout,
  '(onboarding)/welcome': WelcomeRoute,
  '(onboarding)/sports': SportsRoute,
  '(onboarding)/question/[assessmentId]': QuestionRoute,
  '(onboarding)/review/[assessmentId]': ReviewRoute,
  '(onboarding)/result/[assessmentId]': ResultRoute,
  '(onboarding)/done': DoneRoute,
  '(onboarding)/data': DataRoute,
  // The second part, in order. They are routes rather than one route with a param so the
  // sequence is visible in the file tree, the way the authorization boundary is.
  '(onboarding)/tags': TagsRoute,
  '(onboarding)/photos': PhotosRoute,
  '(onboarding)/availability': AvailabilityRoute,
  '(onboarding)/location': LocationRoute,
  '(onboarding)/radius': RadiusRoute,
  '(onboarding)/gender': GenderRoute,
  '(onboarding)/opt-in': OptInRoute,
};

/**
 * The photo library this tree runs against, for the suite that is about one.
 *
 * A module-level value rather than a parameter, because the route map `renderRouter` takes
 * is static: `TestRoot` is a component in a table, not something a test constructs. Set it
 * with `stubImagePicking` before launching and clear it with `resetImagePicking` in
 * teardown, beside `transport.restore()` and for the same reason.
 *
 * Unset means the real device port, which is what production gets — and in a test that is
 * a native module jest has mocked into a picker nobody described, so a screen that opened
 * one without saying so gets nothing back rather than a picture from nowhere.
 */
let imagePicking: ImagePickingPort | undefined;

/** Run the tree against this photo library. Call before `launchSignedIn`. */
export function stubImagePicking(port: ImagePickingPort): void {
  imagePicking = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetImagePicking(): void {
  imagePicking = undefined;
}

/**
 * The device whose position this tree reads, for the suites that walk as far as step four.
 *
 * Same shape and same reasons as the photo library above. Unset means the real port over a
 * native module jest has mocked, which answers a device nobody described — so a suite that
 * reaches the location step without saying what the phone knows gets an answer it did not
 * choose, which is exactly the surprise this stub exists to remove.
 */
let location: LocationPort | undefined;

/** Run the tree against this device. Call before `launchSignedIn`. */
export function stubLocation(port: LocationPort): void {
  location = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetLocation(): void {
  location = undefined;
}

/**
 * The providers the real root layout composes, without the bootstrap sequence — fonts, the
 * splash screen and config validation are the launch path's business and have their own
 * tests.
 */
function TestRoot() {
  return (
    <SafeAreaProvider
      initialMetrics={{
        frame: { x: 0, y: 0, width: 390, height: 844 },
        insets: { top: 0, left: 0, right: 0, bottom: 0 },
      }}
    >
      <QueryClientProvider client={queryClient}>
        <WithPorts>
          <Slot />
        </WithPorts>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

/**
 * The two ports, wrapped only where a suite said what they are.
 *
 * Composed here rather than in `TestRoot` so adding a third port is one entry rather than a
 * fourth level of nesting and a second conditional.
 */
function WithPorts({ children }: { readonly children: ReactNode }) {
  const withLocation =
    location === undefined ? (
      children
    ) : (
      <LocationProvider port={location}>{children}</LocationProvider>
    );

  return imagePicking === undefined ? (
    withLocation
  ) : (
    <ImagePickingProvider port={imagePicking}>{withLocation}</ImagePickingProvider>
  );
}

/** The four sports the backend serves, as the registry route answers. */
export const SPORTS_SERVED: Wire['SportsResponse'] = {
  sports: [
    { sport: 'PADEL', players: 4, durations: [60, 90, 120] },
    { sport: 'TENNIS', players: 2, durations: [60, 90] },
    { sport: 'SQUASH', players: 2, durations: [45, 60, 90] },
    { sport: 'BADMINTON', players: 4, durations: [60, 90] },
  ],
};

export const RUNS_IN_PROGRESS_PATH = '/api/v1/assessments/in-progress';

export const PROFILE_OPTIONS_PATH = '/api/v1/player-profile/options';

/**
 * The nineteen Social tags in their three groups, the selection bounds and the radius
 * bounds — as `GET /player-profile/options` answers.
 *
 * The order here is the order the picker must render, because the picker renders what it
 * is served and sorts nothing. A suite that wants a shorter vocabulary passes its own.
 */
export const PROFILE_OPTIONS_SERVED: Wire['PlayerProfileOptionsResponse'] = {
  social_tag_groups: [
    {
      group: 'AFTER_THE_MATCH',
      tags: [
        { id: 'STAYS_FOR_A_DRINK' },
        { id: 'STRAIGHT_HOME_AFTER' },
        { id: 'TALKS_THROUGH_THE_MATCH' },
        { id: 'SETTLES_UP_ON_THE_SPOT' },
        { id: 'BOOKS_THE_NEXT_ONE' },
        { id: 'SHARES_A_LIFT' },
      ],
    },
    {
      group: 'ON_THE_COURT',
      tags: [
        { id: 'PLAYS_TO_WIN' },
        { id: 'LAUGHS_OFF_MISTAKES' },
        { id: 'ENCOURAGES_A_PARTNER' },
        { id: 'GENEROUS_ON_LINE_CALLS' },
        { id: 'QUIET_AND_FOCUSED' },
        { id: 'WARMS_UP_PROPERLY' },
      ],
    },
    {
      group: 'WHY_YOU_ARE_HERE',
      tags: [
        { id: 'HERE_TO_IMPROVE' },
        { id: 'HERE_TO_COMPETE' },
        { id: 'HERE_FOR_THE_EXERCISE' },
        { id: 'HERE_TO_MEET_PLAYERS' },
        { id: 'HERE_FOR_A_REGULAR_GAME' },
        { id: 'HERE_TO_GET_BACK_INTO_IT' },
        { id: 'OPEN_TO_MEET_SOMEONE' },
      ],
    },
  ],
  social_tag_selection: { minimum_tags: 2, maximum_tags: 6 },
  search_radius: { minimum_km: 1, maximum_km: 50, step_km: 1, default_km: 10 },
};

export const PROFILE_SURFACE_PATH = '/api/v1/players/me/profile';

/**
 * The three facts Play's search screen opens on: a week, a radius and one declaration.
 *
 * A padel declaration is in it because *rated and undeclared* is a **different screen** —
 * ADR-0094's one-tap interstitial — so a suite that wants the ordinary case has to say a
 * declaration exists, and a suite that wants the interstitial passes a surface without one.
 */
export const PROFILE_SURFACE_SERVED: Wire['PlayerProfileReadResponse'] = {
  availability: [
    { day: 2, part: 'EVENING' },
    { day: 6, part: 'MORNING' },
  ],
  search_radius_km: 12,
  play_intents: { PADEL: 'FOR_FUN' },
};

/**
 * The profile surface, for any suite that renders a screen inside ⚡Play.
 *
 * Separate from `stubGate` for the reason the options are: the gate does not read it. It is
 * the shell's business only because Play's tab is now a screen rather than a placeholder, and
 * a screen that reads three routes is a screen a harness has to describe.
 */
export function stubProfileSurface(
  transport: Transport,
  served: Wire['PlayerProfileReadResponse'] = PROFILE_SURFACE_SERVED,
) {
  transport.on('GET', PROFILE_SURFACE_PATH, () => json(served));
}

/**
 * What the profile steps are drawn from.
 *
 * Separate from `stubGate` because the gate does not read it: the vocabulary is wanted by
 * the first social step, and a suite that never enters the part never asks for it.
 */
export function stubProfileOptions(
  transport: Transport,
  served: Wire['PlayerProfileOptionsResponse'] = PROFILE_OPTIONS_SERVED,
) {
  transport.on('GET', PROFILE_OPTIONS_PATH, () => json(served));
}

/**
 * Your own *Let's play* yeses — the read behind the **Match me count** on Play's segment.
 *
 * Separate from the three above and defaulted to nothing outstanding, because every Play
 * screen draws the segment and almost no suite is about the number on it: a count that has
 * not landed draws no count, which is the same thing the segment says at nought.
 */
export function stubInterest(
  transport: Transport,
  served: Wire['InterestListResponse'] = { outgoing: [], mutual: [], outstanding: [] },
) {
  transport.on('GET', '/api/v1/interest', () => json(served));
}

export interface GateStub {
  readonly ratings?: readonly Wire['RatingResponse'][];
  /**
   * The runs this player left unfinished, in the order the server sends them — sport
   * registry order. A single run is the ordinary case; two is what proves which one the
   * gate picks.
   */
  readonly runs?: readonly Wire['InProgressAssessmentResponse'][];
  /**
   * Whether onboarding's second part has been committed — the gate's fourth branch.
   *
   * Defaults to **false**, which is the answer that goes with the default of no ratings: a
   * player who has been rated at nothing has committed nothing either. It is only consulted
   * once a rating exists, so most suites never have to state it.
   */
  readonly hasPlayerProfile?: boolean;
}

/** The signed-in player, as `GET /users/me` answers. Identity is filler; the flag is not. */
export const GATE_USER: Wire['UserResponse'] = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  nickname: 'ada',
  authority: 'player',
  is_admin: false,
  is_active: true,
  has_player_profile: false,
  created_at: '2026-08-13T10:00:00Z',
};

/**
 * The gate's three reads: what this player is rated at, what they left unfinished, and who
 * they are — which is where *does a Player profile exist* is served from.
 *
 * The unfinished-run read is **one** request covering every sport. An empty list is the
 * answer for a player with nothing outstanding — a 200, not a 204 and not a failure.
 */
export function stubGate(
  transport: Transport,
  { ratings = [], runs = [], hasPlayerProfile = false }: GateStub = {},
) {
  transport.on('GET', '/api/v1/ratings', () =>
    json<Wire['RatingsResponse']>({ ratings: [...ratings] }),
  );

  transport.on('GET', '/api/v1/users/me', () =>
    json<Wire['UserResponse']>({ ...GATE_USER, has_player_profile: hasPlayerProfile }),
  );

  stubRunsInProgress(transport, runs);
}

/** Replace the gate's unfinished-run answer — what the server says *now*. */
export function stubRunsInProgress(
  transport: Transport,
  runs: readonly Wire['InProgressAssessmentResponse'][],
) {
  transport.on('GET', RUNS_IN_PROGRESS_PATH, () =>
    json<Wire['InProgressAssessmentsResponse']>({ assessments: [...runs] }),
  );
}

/** One unfinished run, as the collection reports it: the id and its sport, nothing else. */
export function runInProgress(
  sport: Wire['Sport'],
  assessmentId: string,
): Wire['InProgressAssessmentResponse'] {
  return { assessment_id: assessmentId, sport };
}

/** A cold launch with credentials already in the keychain. */
export async function launchSignedIn(initialUrl = '/') {
  await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  renderRouter(ONBOARDING_ROUTES, { initialUrl });
}
