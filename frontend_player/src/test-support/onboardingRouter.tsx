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
import ChallengeRoute from '@/app/(app)/(tabs)/chats/challenge/[challengeId]/index';
import ChallengeFillRoute from '@/app/(app)/(tabs)/chats/challenge/[challengeId]/fill';
import ChatsRoute from '@/app/(app)/(tabs)/chats';
import ConversationRoute from '@/app/(app)/(tabs)/chats/conversation/[conversationId]';
import ConversationGameRoute from '@/app/(app)/(tabs)/chats/conversation/[conversationId]/details';
import GameRoute from '@/app/(app)/(tabs)/games/[gameId]';
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
import { NOW_COPY } from '@/features/shell/types';
import { beginSession } from '@/shared/lib/auth';
import {
  ImagePickingProvider,
  LiveStreamProvider,
  LocationProvider,
  type ImagePickingPort,
  type LiveStreamPort,
  type LocationPort,
} from '@/shared/lib/platform';
import { queryClient } from '@/shared/lib/query-client';

import { json, type Transport, type Wire } from './transport';

/**
 * The Now tab's one line — which is what *the player is in the app* looks like on screen.
 *
 * The gate's fourth destination is the shell's root, and the shell's root is the Now tab, so
 * every suite that asserts a launch, a finish or a commit landed in the app is asserting this
 * sentence. Taken from the shell's own copy rather than spelled here, because this is exactly the
 * kind of sentence that gets reworded and eight suites holding a string literal is eight red tests
 * for a wording change.
 *
 * It was the tab's **placeholder** line until [#367](https://github.com/Raketa02/Raketa/issues/367)
 * built the rail, and it is now the tab's **empty** line — which every one of these suites draws,
 * because `stubGate` stubs the games list to nothing and a launch that arrives with no games is
 * the state they are all asserting.
 */
export const NOW_TAB_LINE = NOW_COPY.empty.line;

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
  // A game is pushed over the Now tab and is a `games/` route rather than a `now/` one,
  // because the Now tab's root is the shell's own root and has no segment to nest under.
  '(app)/(tabs)/games/[gameId]': GameRoute,
  '(app)/(tabs)/chats': ChatsRoute,
  // A challenge is pushed over the Chats tab, and the static `challenge` above the id is the
  // decision that keeps a challenge id and a conversation id from sharing one segment.
  '(app)/(tabs)/chats/challenge/[challengeId]/index': ChallengeRoute,
  // The builder, at its **second route** — `features/play`'s own screen under the challenge it
  // is completing, so the Chats column stays lit and *back* is correct by construction.
  '(app)/(tabs)/chats/challenge/[challengeId]/fill': ChallengeFillRoute,
  // And a conversation beside it, under its own static segment for the same reason: two ids of
  // two different things cannot share one `/chats/[id]`. Spelled `…/index` exactly as the file
  // tree spells it, because the shell names this route to give it the push transition and
  // `Stack.Screen` matches on the name: a table that shortened it would leave the option on a
  // route that does not exist, and the warning saying so on every suite that walks the shell.
  '(app)/(tabs)/chats/conversation/[conversationId]/index': ConversationRoute,
  // The game screen, at its **second route** — one component and two addresses, so the Chats
  // column stays lit behind the room's *Details* and *back* is correct in both directions
  // ([#368](https://github.com/Raketa02/Raketa/issues/368), ADR-0149 §5).
  '(app)/(tabs)/chats/conversation/[conversationId]/details': ConversationGameRoute,
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
 * The live channel this tree follows a room over — and **the one port whose default is a fake.**
 *
 * The other two stand in front of native modules jest has already mocked into something inert, so
 * leaving them unset costs a suite nothing but a device it did not describe. This one stands in
 * front of a **socket**: unset, the real port would mint an `Authorization` header and open an
 * `XMLHttpRequest` at the API host in every suite that lands on a room, which is a connection no
 * test asked for and the one edge `installTransport` does not cover.
 *
 * So `WithPorts` always provides one. A suite that says nothing gets a channel that reports
 * `connecting` and stays there, which is *not live is never drawn on a cold open* — the right
 * default, and the state every room test that is about something else wants.
 */
let liveStream: LiveStreamPort | undefined;

/** Run the tree against this live channel. Call before `launchSignedIn`. */
export function stubLiveStream(port: LiveStreamPort): void {
  liveStream = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetLiveStream(): void {
  liveStream = undefined;
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
 * The three ports, wrapped where a suite said what they are — and the live channel always.
 *
 * Composed here rather than in `TestRoot` so adding a port is one entry rather than another
 * level of nesting and another conditional. The live channel's default is a fake rather than
 * the device, for the reason `stubLiveStream` states.
 */
function WithPorts({ children }: { readonly children: ReactNode }) {
  const withLive = (
    <LiveStreamProvider port={liveStream ?? SILENT_CHANNEL}>{children}</LiveStreamProvider>
  );

  const withLocation =
    location === undefined ? (
      withLive
    ) : (
      <LocationProvider port={location}>{withLive}</LocationProvider>
    );

  return imagePicking === undefined ? (
    withLocation
  ) : (
    <ImagePickingProvider port={imagePicking}>{withLocation}</ImagePickingProvider>
  );
}

/**
 * The channel a suite that said nothing gets: it opens, reports `connecting`, and never moves.
 *
 * **Not `fakeLiveStream()`**, deliberately. It is one instance for the whole process — a fresh
 * port per render would be a fresh subscription, so the effect that follows a room would tear
 * down and re-open on every re-render — and a fake holds state, which shared across the process
 * would mean one suite reading another's follows out of `opened`. This holds none: a suite that
 * wants to drive a channel says so with `stubLiveStream(fakeLiveStream())` and gets its own.
 */
const SILENT_CHANNEL: LiveStreamPort = {
  follow: ({ onStatus }) => {
    // Synchronously, exactly as the device port does: a room that has just opened is connecting,
    // and *not live* is never drawn about one.
    onStatus('connecting');
    return () => {};
  },
};

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
 * Your own *Let's play* yeses — the read behind the count in the deck's ending sentence.
 *
 * Separate from the three above and defaulted to nothing outstanding, because almost no suite
 * is about the number: `outgoingYeses` has a sentence for nought as well as for a count, so a
 * read that has not landed still draws something true.
 */
export function stubInterest(
  transport: Transport,
  served: Wire['InterestListResponse'] = { outgoing: [], mutual: [], outstanding: [] },
) {
  transport.on('GET', '/api/v1/interest', () => json(served));
}

export const GAMES_PATH = '/api/v1/games';

/**
 * Your games, as `GET /games` answers — **arranged, played and finished in one list.**
 *
 * `read_at` is the instant every standing and deadline in it was folded against, so a suite that
 * wants a countdown to say a particular thing sets it here rather than mocking a clock: the
 * screens measure from this field and never from the device.
 *
 * Defaulted to nothing, because every launch now draws the Now tab and almost no suite is about
 * what is on it — an empty list renders no section at all, which is what the tab shipped with.
 */
export function stubGames(
  transport: Transport,
  games: readonly Wire['GameSchema'][] = [],
  readAt = '2026-09-05T09:00:00Z',
) {
  transport.on('GET', GAMES_PATH, () =>
    json<Wire['GameListResponse']>({ read_at: readAt, games: [...games] }),
  );
}

export const PLANS_PATH = '/api/v1/plans';

/**
 * Your plans, as `GET /plans` answers — **one row per game somebody has agreed something about.**
 *
 * There is **no `read_at` on this envelope**, deliberately: a plan folds nothing against the clock,
 * so a suite that wants *today* to be a particular day sets `stubGames`' instant instead — the card
 * is folded against the game list's, which is what keeps every clock on a surface the same one.
 *
 * Stubbed on every launch beside the games and the rooms, for the reason those two are: the plan
 * card is pinned in every room that has a game, so a suite that opens one would otherwise fail at
 * the socket with a name that points at `fetch` rather than at the card
 * ([#366](https://github.com/Raketa02/Raketa/issues/366)).
 *
 * Defaulted to nothing, which is not an empty plan but **no plan** — *a plan is born by being
 * used*, so a game nobody has arranged anything on has no row here at all and the card draws three
 * empty slots.
 */
export function stubPlans(transport: Transport, plans: readonly Wire['PlanSchema'][] = []) {
  transport.on('GET', PLANS_PATH, () => json<Wire['PlanListResponse']>({ plans: [...plans] }));
}

/** The path one game's slot answers on, for a suite that wants to record one. */
export const planSlotPath = (gameId: string, slot: 'place' | 'day' | 'hour') =>
  `${PLANS_PATH}/${gameId}/${slot}`;

/** The path `GET /challenges` answers on, for a suite that wants to say what is in the list. */
export const CHALLENGES_PATH = '/api/v1/challenges';

/**
 * Your challenges, as `GET /challenges` answers — **sent and received in one list.**
 *
 * Stubbed on every launch because the **shell** reads it now: the tab bar carries a count of
 * unanswered challenges addressed to you, so a route left unstubbed is a failure at the socket
 * on every app-level suite, named after `fetch` rather than after the bar
 * ([#360](https://github.com/Raketa02/Raketa/issues/360)).
 *
 * `read_at` is the instant every standing and deadline in it was folded against — a suite that
 * wants a countdown to say a particular thing sets it here rather than mocking a clock.
 *
 * Defaulted to nothing, exactly as the games list is: an empty list draws no badge and a section
 * with one line in it, which is what a player with nothing outstanding should see.
 */
export function stubChallenges(
  transport: Transport,
  challenges: readonly Wire['ChallengeSchema'][] = [],
  readAt = '2026-09-05T09:00:00Z',
) {
  transport.on('GET', CHALLENGES_PATH, () =>
    json<Wire['ChallengeListResponse']>({ read_at: readAt, challenges: [...challenges] }),
  );
}

/** The path `GET /conversations` answers on, for a suite that wants to say what rooms exist. */
export const CONVERSATIONS_PATH = '/api/v1/conversations';

/**
 * Your rooms, as `GET /conversations` answers — **every one you are a member of, newest first.**
 *
 * Stubbed on every launch beside the challenge list, though for a weaker reason than that one's:
 * the shell does not read this, the **Chats screen** does, and a suite that walks to the tab for
 * any reason at all would otherwise fail at the socket with a name that points at `fetch` rather
 * than at the section ([#363](https://github.com/Raketa02/Raketa/issues/363)).
 *
 * `read_at` is on the envelope and is deliberately not mapped — no row here draws a clock — so it
 * is a constant rather than a parameter.
 *
 * Defaulted to nothing, exactly as the other two lists are: an empty list draws a section with one
 * line in it, which is what a player who has agreed to play nothing yet should see.
 */
export function stubConversations(
  transport: Transport,
  conversations: readonly Wire['ConversationRowSchema'][] = [],
) {
  transport.on('GET', CONVERSATIONS_PATH, () =>
    json<Wire['ConversationListResponse']>({
      read_at: '2026-09-05T09:00:00Z',
      conversations: [...conversations],
    }),
  );
}

/** The path one room answers on, for a suite that wants to open it. */
export const conversationPath = (conversationId: string) =>
  `${CONVERSATIONS_PATH}/${conversationId}`;

/**
 * **One room and its newest page**, as `GET /conversations/{id}` answers.
 *
 * `read_at` is one instant for the header and the page both, which is what the room's own clock
 * questions are asked of — a suite that wants *the agreed day is today* to be true sets it here
 * rather than mocking a clock.
 */
export function stubConversation(transport: Transport, room: Wire['ConversationResponse']) {
  transport.on('GET', conversationPath(room.conversation_id), () => json(room));
}

/**
 * **A page backward**, as `GET /conversations/{id}/entries` answers.
 *
 * The route is addressed without its query — the cursor is an argument to a route rather than a
 * second route — so a suite asserting *which* cursor was asked for reads `transport.requests`.
 */
export function stubEntries(
  transport: Transport,
  conversationId: string,
  entries: readonly (Wire['MessageSchema'] | Wire['SystemLineSchema'])[] = [],
) {
  transport.on('GET', `${conversationPath(conversationId)}/entries`, () =>
    json<Wire['EntryPageResponse']>({ entries: [...entries] }),
  );
}

export interface GateStub {
  readonly ratings?: readonly Wire['RatingResponse'][];
  /**
   * Who this player **is** — the id `GET /users/me` answers with, which is the same id every
   * route reads off the bearer token and the one a court draws your own seat from.
   *
   * Defaulted, because almost no suite is about identity. A suite that seats you beside
   * candidates has to state it: the poster in your seat is a function of this id, and so is
   * the court a challenge is sent with.
   */
  readonly id?: string;
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
 *
 * **`stubGames`, `stubPlans` and `stubConversations` are in here and none of them is a gate read.**
 * The gate's fourth destination is the shell's root, the shell's root is the Now tab, and the Now
 * tab draws a games list ([#314](https://github.com/Raketa02/Raketa/issues/314)) — so every suite
 * that lands in the app makes that request whether or not it is about one. The rooms are one step
 * further out: only the Chats screen reads them, but a suite that walks to that tab for any reason
 * would otherwise fail at the socket, and the plan card pinned in every room with a game reads a
 * third list on the way. All three are defaulted to nothing, and a suite with any of them calls the
 * stub again afterwards to replace it.
 */
export function stubGate(
  transport: Transport,
  { ratings = [], runs = [], hasPlayerProfile = false, id = GATE_USER.id }: GateStub = {},
) {
  transport.on('GET', '/api/v1/ratings', () =>
    json<Wire['RatingsResponse']>({ ratings: [...ratings] }),
  );

  transport.on('GET', '/api/v1/users/me', () =>
    json<Wire['UserResponse']>({ ...GATE_USER, id, has_player_profile: hasPlayerProfile }),
  );

  stubRunsInProgress(transport, runs);
  stubGames(transport);
  stubPlans(transport);
  stubChallenges(transport);
  stubConversations(transport);
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
