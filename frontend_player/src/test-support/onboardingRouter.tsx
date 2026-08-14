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

import { QueryClientProvider } from "@tanstack/react-query";
import { Slot } from "expo-router";
import { renderRouter } from "expo-router/testing-library";
import { SafeAreaProvider } from "react-native-safe-area-context";

import AppLayout from "@/app/(app)/_layout";
import TabsLayout from "@/app/(app)/(tabs)/_layout";
import HomeRoute from "@/app/(app)/(tabs)/index";
import AuthLayout from "@/app/(auth)/_layout";
import SignInRoute from "@/app/(auth)/sign-in";
import OnboardingLayout from "@/app/(onboarding)/_layout";
import QuestionRoute from "@/app/(onboarding)/question/[assessmentId]";
import ResultRoute from "@/app/(onboarding)/result/[assessmentId]";
import SportsRoute from "@/app/(onboarding)/sports";
import WelcomeRoute from "@/app/(onboarding)/welcome";
import { beginSession } from "@/shared/lib/auth";
import { queryClient } from "@/shared/lib/query-client";

import { json, noContent, type Transport, type Wire } from "./transport";

export const ONBOARDING_ROUTES = {
  _layout: TestRoot,
  "(app)/_layout": AppLayout,
  "(app)/(tabs)/_layout": TabsLayout,
  "(app)/(tabs)/index": HomeRoute,
  "(auth)/_layout": AuthLayout,
  "(auth)/sign-in": SignInRoute,
  "(onboarding)/_layout": OnboardingLayout,
  "(onboarding)/welcome": WelcomeRoute,
  "(onboarding)/sports": SportsRoute,
  "(onboarding)/question/[assessmentId]": QuestionRoute,
  "(onboarding)/result/[assessmentId]": ResultRoute,
};

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
        <Slot />
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

/** The four sports the backend serves, as the registry route answers. */
export const SPORTS_SERVED: Wire["SportsResponse"] = {
  sports: [
    { sport: "PADEL", players: 4, durations: [60, 90, 120] },
    { sport: "TENNIS", players: 2, durations: [60, 90] },
    { sport: "SQUASH", players: 2, durations: [45, 60, 90] },
    { sport: "BADMINTON", players: 4, durations: [60, 90] },
  ],
};

export interface GateStub {
  readonly ratings?: readonly Wire["RatingResponse"][];
  readonly run?: {
    readonly sport: string;
    readonly step: Wire["AssessmentStepResponse"];
  };
}

/** The gate's two reads: what this player is rated at, and what they left unfinished. */
export function stubGate(transport: Transport, { ratings = [], run }: GateStub = {}) {
  transport.on("GET", "/api/v1/ratings", () =>
    json<Wire["RatingsResponse"]>({ ratings: [...ratings] }),
  );

  // One request per sport, because the endpoint is scoped to one. 204 is "nothing here",
  // which is the normal state of a sport and not a failure.
  for (const sport of ["PADEL", "TENNIS", "SQUASH", "BADMINTON"]) {
    transport.on("GET", `/api/v1/assessments/in-progress?sport=${sport}`, () =>
      run?.sport === sport ? json(run.step) : noContent(),
    );
  }
}

/** A cold launch with credentials already in the keychain. */
export async function launchSignedIn(initialUrl = "/") {
  await beginSession({ accessToken: "access-1", refreshToken: "refresh-1" });
  renderRouter(ONBOARDING_ROUTES, { initialUrl });
}
