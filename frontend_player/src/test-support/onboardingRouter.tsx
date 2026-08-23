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
import { Slot } from 'expo-router';
import { renderRouter } from 'expo-router/testing-library';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import AccountRoute from '@/app/(app)/(tabs)/account';
import AppLayout from '@/app/(app)/_layout';
import CreateRoute from '@/app/(app)/(tabs)/create';
import DepartureRoute from '@/app/(app)/matches/[matchId]/departure';
import FindRoute from '@/app/(app)/(tabs)/find';
import InboxRoute from '@/app/(app)/(tabs)/inbox';
import TabsLayout from '@/app/(app)/(tabs)/_layout';
import HomeRoute from '@/app/(app)/(tabs)/index';
import AuthLayout from '@/app/(auth)/_layout';
import SignInRoute from '@/app/(auth)/sign-in';
import DataRoute from '@/app/(onboarding)/data';
import DoneRoute from '@/app/(onboarding)/done';
import OnboardingLayout from '@/app/(onboarding)/_layout';
import QuestionRoute from '@/app/(onboarding)/question/[assessmentId]';
import TakeUpSportRoute from '@/app/(onboarding)/rate/[sport]';
import ResultRoute from '@/app/(onboarding)/result/[assessmentId]';
import ReviewRoute from '@/app/(onboarding)/review/[assessmentId]';
import SportsRoute from '@/app/(onboarding)/sports';
import WelcomeRoute from '@/app/(onboarding)/welcome';
import { beginSession } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';

import { stubNow } from './now';
import { json, type Transport, type Wire } from './transport';

export const ONBOARDING_ROUTES = {
  _layout: TestRoot,
  '(app)/_layout': AppLayout,
  '(app)/(tabs)/_layout': TabsLayout,
  '(app)/(tabs)/index': HomeRoute,
  // The tab bar reaches all five, so all five are in the tree a test drives — a bar drawn
  // over a tree that holds one of them is a bar whose presses cannot be exercised.
  '(app)/(tabs)/find': FindRoute,
  '(app)/(tabs)/create': CreateRoute,
  '(app)/(tabs)/inbox': InboxRoute,
  '(app)/(tabs)/account': AccountRoute,
  // Pushed over the tab tree rather than into it, which is what a test needs in
  // order to press an exit on Now and land somewhere real.
  '(app)/matches/[matchId]/departure': DepartureRoute,
  '(auth)/_layout': AuthLayout,
  '(auth)/sign-in': SignInRoute,
  '(onboarding)/_layout': OnboardingLayout,
  '(onboarding)/welcome': WelcomeRoute,
  '(onboarding)/sports': SportsRoute,
  '(onboarding)/question/[assessmentId]': QuestionRoute,
  '(onboarding)/rate/[sport]': TakeUpSportRoute,
  '(onboarding)/review/[assessmentId]': ReviewRoute,
  '(onboarding)/result/[assessmentId]': ResultRoute,
  '(onboarding)/done': DoneRoute,
  '(onboarding)/data': DataRoute,
};

/** A phone with no notch and no home indicator — every suite's default. */
const FLAT_INSETS = { top: 0, left: 0, right: 0, bottom: 0 } as const;

/**
 * The insets the next launch renders under.
 *
 * Module state rather than an argument threaded through `renderRouter`, because the
 * provider is inside the route tree the router builds and there is nothing to pass it
 * through. `launchSignedIn` resets it, so a suite that sets it cannot leak into one that
 * does not.
 */
let launchInsets: { top: number; left: number; right: number; bottom: number } = FLAT_INSETS;

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
        insets: launchInsets,
      }}
    >
      <QueryClientProvider client={queryClient}>
        <Slot />
      </QueryClientProvider>
    </SafeAreaProvider>
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

export interface GateStub {
  readonly ratings?: readonly Wire['RatingResponse'][];
  /**
   * The runs this player left unfinished, in the order the server sends them — sport
   * registry order. A single run is the ordinary case; two is what proves which one the
   * gate picks.
   */
  readonly runs?: readonly Wire['InProgressAssessmentResponse'][];
}

/**
 * The gate's two reads: what this player is rated at, and what they left unfinished.
 *
 * The second is **one** request covering every sport. An empty list is the answer for a
 * player with nothing outstanding — a 200, not a 204 and not a failure.
 *
 * **Now is stubbed here too, empty.** The gate's `app` outcome lands on Now, so every
 * suite that walks a player past onboarding reaches a screen that composes — and an
 * unstubbed route throws by design. A suite that cares what Now shows stubs it again
 * with a screen of its own; a later `transport.on` for the same path replaces this one.
 */
export function stubGate(transport: Transport, { ratings = [], runs = [] }: GateStub = {}) {
  transport.on('GET', '/api/v1/ratings', () =>
    json<Wire['RatingsResponse']>({ ratings: [...ratings] }),
  );

  stubRunsInProgress(transport, runs);
  stubNow(transport);
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

/**
 * A cold launch with credentials already in the keychain.
 *
 * `insets` is how a suite asks for a phone with a home indicator. It defaults to a flat
 * one, which is what every suite but the tab bar's wants — and the tab bar's wants the
 * other because the bottom inset is the one thing the bar and the screen above it can
 * both claim.
 */
export async function launchSignedIn(
  initialUrl = '/',
  insets: { top: number; left: number; right: number; bottom: number } = FLAT_INSETS,
) {
  launchInsets = insets;
  await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  renderRouter(ONBOARDING_ROUTES, { initialUrl });
}
