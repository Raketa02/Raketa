/**
 * Onboarding, driven through the real route tree and the network boundary.
 *
 * Only `fetch` is faked. The router, the http client, its timeouts, error mapping, the
 * mappers, the use-cases, the hooks, the store and the screens all run for real — so a
 * pass here means the flow works end to end minus the socket.
 *
 * The gate's four outcomes are routing behaviour, so they are asserted as routing: which
 * screen a launch lands on. These tests live outside `src/app/` and import the route
 * files, per docs/architecture.md Part 16.
 *
 * Every assertion is about what a player can see or what left the device. None reads a
 * store's internals or a hook's return shape.
 */

import { QueryClientProvider, onlineManager } from "@tanstack/react-query";
import { Slot } from "expo-router";
import { fireEvent, renderRouter, screen, waitFor } from "expo-router/testing-library";
import { SafeAreaProvider } from "react-native-safe-area-context";

import AppLayout from "@/app/(app)/_layout";
import TabsLayout from "@/app/(app)/(tabs)/_layout";
import HomeRoute from "@/app/(app)/(tabs)/index";
import AuthLayout from "@/app/(auth)/_layout";
import SignInRoute from "@/app/(auth)/sign-in";
import OnboardingLayout from "@/app/(onboarding)/_layout";
import QuestionRoute from "@/app/(onboarding)/question/[assessmentId]";
import SportsRoute from "@/app/(onboarding)/sports";
import WelcomeRoute from "@/app/(onboarding)/welcome";
import {
  beginSession,
  clearStoredTokens,
  resetSessionStatus,
  setSessionStatus,
  wireHttpCredentials,
} from "@/shared/lib/auth";
import { queryClient } from "@/shared/lib/query-client";
import { refreshTokens } from "@/features/auth/types";
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from "@/test-support/transport";

import { useSportQueue } from "../store/sportQueue.store";

const ASSESSMENT_ID = "1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6";

const SPORTS_SERVED: Wire["SportsResponse"] = {
  sports: [
    { sport: "PADEL", players: 4, durations: [60, 90, 120] },
    { sport: "TENNIS", players: 2, durations: [60, 90] },
    { sport: "SQUASH", players: 2, durations: [45, 60, 90] },
    { sport: "BADMINTON", players: 4, durations: [60, 90] },
  ],
};

const RATING: Wire["RatingResponse"] = {
  sport: "PADEL",
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: "Established", lower: 2.7, upper: 3.8 },
  status: "initial_estimate",
  engine_version: "racketskill-v3",
  updated_at: "2026-08-14T09:00:00Z",
};

const OPENING_STEP: Wire["AssessmentStepResponse"] = {
  assessment_id: ASSESSMENT_ID,
  status: "in_progress",
  question: {
    id: "q-played",
    category: "Recent activity",
    tier: null,
    situation: "Before anything else",
    text: "Have you played padel before?",
    qualifier: "Any level counts",
    options: [
      { id: "never", text: "Never played" },
      { id: "some", text: "A few times" },
    ],
  },
};

const USER: Wire["UserResponse"] = {
  id: "11111111-2222-4333-8444-555555555555",
  email: "ada@example.com",
  nickname: "ada",
  authority: "player",
  is_admin: false,
  is_active: true,
  created_at: "2026-08-13T10:00:00Z",
};

const ROUTES = {
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
};

/**
 * The providers the real root layout composes, without the bootstrap sequence — fonts,
 * the splash screen and config validation are the launch path's business and have their
 * own tests.
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

let transport: Transport;

/** The gate's two reads: what this player is rated at, and what they left unfinished. */
function stubGate({
  ratings = [],
  run,
}: {
  readonly ratings?: readonly Wire["RatingResponse"][];
  readonly run?: { readonly sport: string; readonly step: Wire["AssessmentStepResponse"] };
} = {}) {
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

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useSportQueue.getState().reset();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
});

async function launchSignedIn() {
  await beginSession({ accessToken: "access-1", refreshToken: "refresh-1" });
  renderRouter(ROUTES, { initialUrl: "/" });
}

// ---------------------------------------------------------------------------
// The entry gate — all four outcomes
// ---------------------------------------------------------------------------

describe("where a launch lands", () => {
  it("sends a signed-out player to sign in", async () => {
    setSessionStatus("unauthenticated");

    renderRouter(ROUTES, { initialUrl: "/" });

    await waitFor(() => expect(screen).toHavePathname("/sign-in"));
    // The gate's reads are authenticated, and firing them without a session would only
    // ever produce a 401 for the rotation to chase.
    expect(transport.requests).toHaveLength(0);
  });

  it("sends a signed-in player with no ratings into onboarding", async () => {
    stubGate();

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname("/welcome"));
    expect(screen.getByText("Let's find your level")).toBeTruthy();
  });

  it("sends an already-rated player into the app, not into onboarding", async () => {
    stubGate({ ratings: [RATING] });
    transport.on("GET", "/api/v1/users/me", () => json(USER));

    await launchSignedIn();

    expect(await screen.findByText("ada")).toBeTruthy();
    expect(screen).toHavePathname("/");
  });

  it("resumes an assessment that was left unfinished", async () => {
    stubGate({ run: { sport: "TENNIS", step: OPENING_STEP } });
    transport.on("GET", `/api/v1/assessments/${ASSESSMENT_ID}`, () => json(OPENING_STEP));

    await launchSignedIn();

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));
    // The category is the heading, and the sport comes back with it — a resumed run has
    // no queue, because the queue was never persisted.
    expect(await screen.findByText("Recent activity")).toBeTruthy();
    expect(screen.getByText("Tennis · Rating 1 of 1")).toBeTruthy();
  });

  it("asks both gate questions at once rather than one after the other", async () => {
    stubGate();

    // Hold the ratings answer open. If the two reads were sequenced, nothing else would
    // reach the socket until it came back — so the second read arriving *while this is
    // still in flight* is the proof, and counting requests after both finished would
    // prove nothing.
    let answerRatings = () => {};
    const held = new Promise<void>((resolve) => {
      answerRatings = resolve;
    });
    transport.on("GET", "/api/v1/ratings", async () => {
      await held;
      return json<Wire["RatingsResponse"]>({ ratings: [] });
    });

    await launchSignedIn();

    await waitFor(() =>
      expect(
        transport.requestsTo("GET", "/api/v1/assessments/in-progress?sport=BADMINTON"),
      ).toHaveLength(1),
    );

    answerRatings();
    await waitFor(() => expect(screen).toHavePathname("/welcome"));
  });

  it("says so, and offers a retry, when the gate cannot be read", async () => {
    // A terminal failure rather than a dropped connection: a dropped connection is
    // retried automatically with backoff, and this test is about the gate's behaviour
    // rather than the retry policy's timing.
    stubGate();
    transport.on("GET", "/api/v1/ratings", () => errorResponse(403, "forbidden"));

    await launchSignedIn();

    expect(
      await screen.findByText("We couldn't pick up where you left off"),
    ).toBeTruthy();
    // No guess in either direction: sending an unrated player into the app skips
    // onboarding, and sending a rated one into onboarding re-rates them.
    expect(screen).not.toHavePathname("/welcome");

    stubGate();
    fireEvent.press(screen.getByLabelText("Try again"));

    await waitFor(() => expect(screen).toHavePathname("/welcome"));
  });

  it("says the connection is out rather than rendering nothing, when launched offline", async () => {
    stubGate();
    // `networkMode: 'online'` *pauses* a query instead of failing it, so the gate's two
    // reads never resolve and never error. Without a branch for that, the app renders a
    // blank screen for as long as the connection stays dead.
    onlineManager.setOnline(false);

    await launchSignedIn();

    expect(
      await screen.findByText(
        "We couldn't reach Rakieta. Check your connection and try again.",
      ),
    ).toBeTruthy();
    expect(transport.requests).toHaveLength(0);

    onlineManager.setOnline(true);

    await waitFor(() => expect(screen).toHavePathname("/welcome"));
  });
});

// ---------------------------------------------------------------------------
// Welcome, the picker, and the first question
// ---------------------------------------------------------------------------

describe("walking into the questionnaire", () => {
  async function reachThePicker() {
    stubGate();
    transport.on("GET", "/api/v1/sports", () => json(SPORTS_SERVED));

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname("/welcome"));

    fireEvent.press(screen.getByLabelText("Get started"));
    await waitFor(() => expect(screen).toHavePathname("/sports"));
  }

  it("sets expectations before the first question", async () => {
    stubGate();
    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname("/welcome"));

    expect(screen.getByText("You get a starting level for each sport")).toBeTruthy();
    expect(screen.getByText("It takes about a minute per sport")).toBeTruthy();
    expect(screen.getByText("Nothing here is permanent")).toBeTruthy();
  });

  it("counts the sports chosen on the control that continues", async () => {
    await reachThePicker();

    expect(await screen.findByLabelText("Padel")).toBeTruthy();
    expect(screen.getByLabelText("Choose a sport to continue")).toBeTruthy();

    fireEvent.press(screen.getByLabelText("Padel"));
    expect(screen.getByLabelText("Rate 1 sport")).toBeTruthy();

    fireEvent.press(screen.getByLabelText("Tennis"));
    expect(screen.getByLabelText("Rate 2 sports")).toBeTruthy();

    // Tapping a chosen sport again removes it, and the count follows.
    fireEvent.press(screen.getByLabelText("Tennis"));
    expect(screen.getByLabelText("Rate 1 sport")).toBeTruthy();
  });

  it("says which sports are selected in words, not only by their border", async () => {
    await reachThePicker();

    expect(await screen.findByLabelText("Padel")).toBeTruthy();
    expect(screen.queryByText("Selected")).toBeNull();

    fireEvent.press(screen.getByLabelText("Padel"));

    expect(screen.getByText("Selected")).toBeTruthy();
    // And as state to a screen reader, which is the half a border cannot carry.
    expect(screen.getByRole("button", { name: "Padel", selected: true })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tennis", selected: true })).toBeNull();
  });

  it("starts the first chosen sport and lands on its opening question", async () => {
    await reachThePicker();

    transport.on("POST", "/api/v1/assessments", () => json(OPENING_STEP, 201));

    expect(await screen.findByLabelText("Tennis")).toBeTruthy();
    // Chosen second, so tennis is second in the queue — order is the only thing the
    // selection carries.
    fireEvent.press(screen.getByLabelText("Padel"));
    fireEvent.press(screen.getByLabelText("Tennis"));
    fireEvent.press(screen.getByLabelText("Rate 2 sports"));

    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));

    const [started] = transport.requestsTo("POST", "/api/v1/assessments");
    expect(started?.body).toEqual({ sport: "PADEL" });

    expect(await screen.findByText("Recent activity")).toBeTruthy();
    expect(screen.getByText("Padel · Rating 1 of 2")).toBeTruthy();
    // The bar measures sports — the one denominator the player actually chose — and says
    // so in words as well, because a filled rectangle is unreadable at any font size.
    expect(screen.getByLabelText("Rating 1 of 2")).toBeTruthy();

    // The response *is* the next question, so it is written into the cache rather than
    // asked for a second time.
    expect(transport.requestsTo("GET", `/api/v1/assessments/${ASSESSMENT_ID}`)).toEqual(
      [],
    );
  });

  it("sends one start, however many times the control is pressed", async () => {
    await reachThePicker();

    // Held open, so the second press lands while the first is still in flight.
    let answer = () => {};
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on("POST", "/api/v1/assessments", async () => {
      await held;
      return json(OPENING_STEP, 201);
    });

    expect(await screen.findByLabelText("Padel")).toBeTruthy();
    fireEvent.press(screen.getByLabelText("Padel"));
    fireEvent.press(screen.getByLabelText("Rate 1 sport"));

    await waitFor(() =>
      expect(transport.requestsTo("POST", "/api/v1/assessments")).toHaveLength(1),
    );
    fireEvent.press(screen.getByLabelText("Starting…"));

    answer();
    await waitFor(() => expect(screen).toHavePathname(`/question/${ASSESSMENT_ID}`));

    // The blocked button is **UX, not correctness**: `POST /assessments` has no
    // in-progress guard, so two starts that did reach the server would open two runs for
    // one sport and strand one of them. The real defence is backend-side — see the
    // follow-up issue.
    expect(transport.requestsTo("POST", "/api/v1/assessments")).toHaveLength(1);
  });

  it("never writes the sport selection to the server", async () => {
    await reachThePicker();

    expect(await screen.findByLabelText("Squash")).toBeTruthy();
    fireEvent.press(screen.getByLabelText("Squash"));
    fireEvent.press(screen.getByLabelText("Badminton"));

    // The queue orders the next few assessments and is nothing else. Choosing sports is
    // not a write, and there is no endpoint it could be one against.
    const writes = transport.requests.filter((request) => request.method !== "GET");
    expect(writes).toEqual([]);
  });
});
