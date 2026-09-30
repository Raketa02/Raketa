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
import { Slot, router, type Href } from 'expo-router';
import { act, renderRouter, waitFor } from 'expo-router/testing-library';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { ReducedMotionProvider } from '@/shared/ui';

import AdministratorLayout from '@/app/(administrator)/_layout';
import AdministratorAreaLayout from '@/app/(administrator)/administrator/[clubId]/_layout';
import AdministratorGroupsRoute from '@/app/(administrator)/administrator/[clubId]/index';
import AdministratorYouRoute from '@/app/(administrator)/administrator/[clubId]/you/index';
import GroupSettingsRoute from '@/app/(administrator)/administrator/[clubId]/you/settings/[groupId]';
import AdministratorStartPlayingRoute from '@/app/(administrator)/administrator/[clubId]/you/start-playing';
import NewOfficialGroupRoute from '@/app/(administrator)/administrator/[clubId]/new-group';
import OfficialGroupRoute from '@/app/(administrator)/administrator/[clubId]/group/[groupId]';
import AppLayout from '@/app/(app)/_layout';
import TabsLayout from '@/app/(app)/(tabs)/_layout';
import ChallengeRoute from '@/app/(app)/(tabs)/chats/challenge/[challengeId]/index';
import ChallengeFillRoute from '@/app/(app)/(tabs)/chats/challenge/[challengeId]/fill';
import YesRoute from '@/app/(app)/(tabs)/chats/challenge/[challengeId]/yes';
import ChatsRoute from '@/app/(app)/(tabs)/chats';
import ConversationRoute from '@/app/(app)/(tabs)/chats/conversation/[conversationId]';
import ConversationGameRoute from '@/app/(app)/(tabs)/chats/conversation/[conversationId]/details';
import GameRoute from '@/app/(app)/(tabs)/games/[gameId]';
import NowRoute from '@/app/(app)/(tabs)/index';
import BuilderRoute from '@/app/(app)/(tabs)/play/builder';
import PoolRoute from '@/app/(app)/(tabs)/play/pool';
import PlayRoute from '@/app/(app)/(tabs)/play/index';
import NewGroupRoute from '@/app/(app)/(tabs)/play/new-group';
import JoinGroupRoute from '@/app/(app)/(tabs)/play/join';
import GroupRoute from '@/app/(app)/(tabs)/play/group/[groupId]/index';
import GroupFriendsRoute from '@/app/(app)/(tabs)/play/group/[groupId]/friends';
import GroupMembersRoute from '@/app/(app)/(tabs)/play/group/[groupId]/members';
import GroupEditRoute from '@/app/(app)/(tabs)/play/group/[groupId]/edit';
import GameDetailsRoute from '@/app/(app)/(tabs)/play/group/[groupId]/game/[proposalId]';
import PlayersRoute from '@/app/(app)/(tabs)/players';
import YouRoute from '@/app/(app)/(tabs)/you';
import YouAreaRoute from '@/app/(app)/(tabs)/you/area';
import YouGameSuggestionsRoute from '@/app/(app)/(tabs)/you/game-suggestions';
import YouGamesAndMoneyRoute from '@/app/(app)/(tabs)/you/games-and-money';
import YouIntroRoute from '@/app/(app)/(tabs)/you/intro';
import YouKindOfGameRoute from '@/app/(app)/(tabs)/you/kind-of-game';
import YouNameRoute from '@/app/(app)/(tabs)/you/name';
import YouPaymentsRoute from '@/app/(app)/(tabs)/you/payments';
import YouPassportRoute from '@/app/(app)/(tabs)/you/passport';
import YouPhotosRoute from '@/app/(app)/(tabs)/you/photos';
import YouRadiusRoute from '@/app/(app)/(tabs)/you/radius';
import YouReliabilityRoute from '@/app/(app)/(tabs)/you/reliability';
import YouTagsRoute from '@/app/(app)/(tabs)/you/tags';
import YouWeekRoute from '@/app/(app)/(tabs)/you/week';
import YouWhoYouPlayWithRoute from '@/app/(app)/(tabs)/you/who-you-play-with';
import AuthLayout from '@/app/(auth)/_layout';
import SignInRoute from '@/app/(auth)/sign-in';
import SignUpRoute from '@/app/(auth)/sign-up';
import ForgotPasswordRoute from '@/app/(auth)/forgot-password/index';
import ResetCodeRoute from '@/app/(auth)/forgot-password/code';
import ResetSentRoute from '@/app/(auth)/forgot-password/sent';
import ResetNewPasswordRoute from '@/app/(auth)/forgot-password/new-password';
import ResetLinkRoute from '@/app/(auth)/reset/[token]';
import InvitationCodeRoute from '@/app/(auth)/invitation/index';
import InvitationPasswordRoute from '@/app/(auth)/invitation/password';
import InvitationLinkRoute from '@/app/(auth)/invite/[token]';
import * as NativeIntent from '@/app/+native-intent';
import AvailabilityRoute from '@/app/(onboarding)/availability';
import DataRoute from '@/app/(onboarding)/data';
import DoneRoute from '@/app/(onboarding)/done';
import IntroRoute from '@/app/(onboarding)/intro';
import LocationRoute from '@/app/(onboarding)/location';
import NameRoute from '@/app/(onboarding)/name';
import StartPlayingRoute from '@/app/(onboarding)/start-playing';
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
import { featureFlagKeys } from '@/features/feature_flags/types';
import { HOME_COPY } from '@/features/shell/types';
import { beginSession, setSessionStatus } from '@/shared/lib/auth';
import {
  ClipboardProvider,
  HapticsProvider,
  ShareProvider,
  ImagePickingProvider,
  LiveStreamProvider,
  LocationProvider,
  PaymentsProvider,
  type ClipboardPort,
  type PaymentsPort,
  type HapticsPort,
  type SharePort,
  type ImagePickingPort,
  type LiveStreamPort,
  type LocationPort,
} from '@/shared/lib/platform';
import { queryClient } from '@/shared/lib/query-client';

import { fakePayments } from './platform';
import { errorResponse, json, type Transport, type Wire } from './transport';

/**
 * The Home tab's one line — which is what *the player is in the app* looks like on screen.
 *
 * The gate's fourth destination is the shell's root, and the shell's root is the Home tab, so
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
export const HOME_TAB_LINE = HOME_COPY.empty.line;

export const ONBOARDING_ROUTES = {
  _layout: TestRoot,
  '(app)/_layout': AppLayout,
  '(app)/(tabs)/_layout': TabsLayout,
  // The five-tab shell. Play is a directory because the builder and the pool land under it,
  // and the bar reads its active column off that first segment. Players is a single-screen
  // root: the deck is the whole tab (ADR-0169 §1).
  '(app)/(tabs)/index': NowRoute,
  '(app)/(tabs)/players': PlayersRoute,
  '(app)/(tabs)/play/index': PlayRoute,
  '(app)/(tabs)/play/builder': BuilderRoute,
  '(app)/(tabs)/play/pool': PoolRoute,
  // Play › Groups' screens (#512–#514), under Play so the column stays lit and *back* is the list —
  // and Friends, Members and Edit group over a group's page, so *back* is the page.
  '(app)/(tabs)/play/new-group': NewGroupRoute,
  '(app)/(tabs)/play/join': JoinGroupRoute,
  '(app)/(tabs)/play/group/[groupId]/index': GroupRoute,
  '(app)/(tabs)/play/group/[groupId]/friends': GroupFriendsRoute,
  '(app)/(tabs)/play/group/[groupId]/members': GroupMembersRoute,
  '(app)/(tabs)/play/group/[groupId]/edit': GroupEditRoute,
  '(app)/(tabs)/play/group/[groupId]/game/[proposalId]': GameDetailsRoute,
  // A game is pushed over the Home tab and is a `games/` route rather than a `now/` one,
  // because the Home tab's root is the shell's own root and has no segment to nest under.
  '(app)/(tabs)/games/[gameId]': GameRoute,
  '(app)/(tabs)/chats': ChatsRoute,
  // A challenge is pushed over the Chats tab, and the static `challenge` above the id is the
  // decision that keeps a challenge id and a conversation id from sharing one segment.
  '(app)/(tabs)/chats/challenge/[challengeId]/index': ChallengeRoute,
  // The builder, at its **second route** — `features/play`'s own screen under the challenge it
  // is completing, so the Chats column stays lit and *back* is correct by construction.
  '(app)/(tabs)/chats/challenge/[challengeId]/fill': ChallengeFillRoute,
  // The yes screen, under the challenge it is about — pushed the instant *I'm in* is answered,
  // and the second route the bar stands down on (ADR-0167).
  '(app)/(tabs)/chats/challenge/[challengeId]/yes': YesRoute,
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
  // You is a directory since the tab was built (ADR-0179): the root, and one screen per row
  // pushed over it, each under the tab's first segment so the column stays lit. Spelled
  // `you/index` as the file tree spells it, because the shell names the pushed screens to give
  // them the push transition and `Stack.Screen` matches on the name.
  '(app)/(tabs)/you/index': YouRoute,
  '(app)/(tabs)/you/passport': YouPassportRoute,
  '(app)/(tabs)/you/reliability': YouReliabilityRoute,
  '(app)/(tabs)/you/kind-of-game': YouKindOfGameRoute,
  '(app)/(tabs)/you/week': YouWeekRoute,
  '(app)/(tabs)/you/radius': YouRadiusRoute,
  '(app)/(tabs)/you/area': YouAreaRoute,
  '(app)/(tabs)/you/who-you-play-with': YouWhoYouPlayWithRoute,
  '(app)/(tabs)/you/game-suggestions': YouGameSuggestionsRoute,
  '(app)/(tabs)/you/photos': YouPhotosRoute,
  '(app)/(tabs)/you/tags': YouTagsRoute,
  '(app)/(tabs)/you/intro': YouIntroRoute,
  '(app)/(tabs)/you/name': YouNameRoute,
  '(app)/(tabs)/you/games-and-money': YouGamesAndMoneyRoute,
  '(app)/(tabs)/you/payments': YouPaymentsRoute,
  // The administrator area (#516) — a sibling of `(app)`, one club's area per id, with its own two
  // tabs: Groups at the root, You beside it, New official group and a group's page pushed over
  // Groups, and a group's settings and Start playing's first step pushed over You (#517).
  '(administrator)/_layout': AdministratorLayout,
  '(administrator)/administrator/[clubId]/_layout': AdministratorAreaLayout,
  '(administrator)/administrator/[clubId]/index': AdministratorGroupsRoute,
  '(administrator)/administrator/[clubId]/you/index': AdministratorYouRoute,
  '(administrator)/administrator/[clubId]/you/settings/[groupId]': GroupSettingsRoute,
  '(administrator)/administrator/[clubId]/you/start-playing': AdministratorStartPlayingRoute,
  '(administrator)/administrator/[clubId]/new-group': NewOfficialGroupRoute,
  '(administrator)/administrator/[clubId]/group/[groupId]': OfficialGroupRoute,
  '(auth)/_layout': AuthLayout,
  '(auth)/sign-in': SignInRoute,
  // Sign-up is in the tree for the one walk that starts before a session exists: an account
  // created here is unnamed, and where the gate sends it next is the naming step's suite's.
  '(auth)/sign-up': SignUpRoute,
  // *Forgot password?* (#515), under the same guard as sign-in: the email form, the neutral
  // confirmation, the code, *Set a new password* by a claimed code — and by the email's link.
  '(auth)/forgot-password/index': ForgotPasswordRoute,
  '(auth)/forgot-password/sent': ResetSentRoute,
  '(auth)/forgot-password/code': ResetCodeRoute,
  '(auth)/forgot-password/new-password': ResetNewPasswordRoute,
  '(auth)/reset/[token]': ResetLinkRoute,
  // *Have an invitation code?* and *Set your password* (#518), under the same guard: the email and
  // the code, the password by a claimed code — and by the invitation email's link.
  '(auth)/invitation/index': InvitationCodeRoute,
  '(auth)/invitation/password': InvitationPasswordRoute,
  '(auth)/invite/[token]': InvitationLinkRoute,
  '(onboarding)/_layout': OnboardingLayout,
  // The naming step — the first screen after sign-up, and the gate's first destination
  // (ADR-0171 §3). Before welcome in the table as it is in the walk.
  '(onboarding)/name': NameRoute,
  // *Start playing*'s first step, the Adult attestation (#517), at the gate's own address: where it
  // sends an account that holds no profile at all. The You tab pushes the same screen inside its
  // area.
  '(onboarding)/start-playing': StartPlayingRoute,
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
  '(onboarding)/intro': IntroRoute,
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
 * The motor this tree buzzes, for the suite that counts a buzz.
 *
 * Same shape and same reasons as the photo library above. Unset means the real port over a
 * native module jest has mocked into something inert, which is right for every suite that is
 * not about a haptic — and the deck's is: *one light tick as the drag first crosses the
 * threshold, and none under reduced motion* is a claim about a count.
 */
let haptics: HapticsPort | undefined;

/** Run the tree against this motor. Call before `launchSignedIn`. */
export function stubHaptics(port: HapticsPort): void {
  haptics = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetHaptics(): void {
  haptics = undefined;
}

/**
 * The clipboard this tree reads, for the suite whose screen has a Paste — Join a group's (#512).
 * Same shape and reasons as the motor above; unset is the real port over a native module jest
 * has mocked, which answers nothing.
 */
let clipboard: ClipboardPort | undefined;

/** Run the tree against this clipboard. Call before `launchSignedIn`. */
export function stubClipboard(port: ClipboardPort): void {
  clipboard = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetClipboard(): void {
  clipboard = undefined;
}

/**
 * The share sheet this tree opens, for the suite whose screen has a Share the link — a group
 * page's (#513). Same shape and reasons as the clipboard above; unset is React Native's own
 * module, which jest's setup has made answer nothing.
 */
let share: SharePort | undefined;

/** Run the tree against this share sheet. Call before `launchSignedIn`. */
export function stubShare(port: SharePort): void {
  share = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetShare(): void {
  share = undefined;
}

/**
 * The payment provider this tree saves a card through, for the suite whose screen is You ›
 * Payments (#552). **Like the live channel, it always has a fake**: the device's port would reach
 * Stripe's SDK, which jest's setup has made answer *no error* to everything — a card saved without a
 * bank anybody described. A suite that says nothing gets a phone with no wallet whose fields hold
 * nothing; a suite that walks a setup says so with `stubPayments(fakePayments())` and keeps it.
 */
let payments: PaymentsPort | undefined;

/** Run the tree against this payment provider. Call before `launchSignedIn`. */
export function stubPayments(port: PaymentsPort): void {
  payments = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetPayments(): void {
  payments = undefined;
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
        {/* The real root's one subscription to the OS motion switch, so a suite that spies
            `AccessibilityInfo.isReduceMotionEnabled` reaches every surface the way a device
            would — rather than the context's `false`, which is what a tree with no provider
            answers whatever the OS says. */}
        <ReducedMotionProvider>
          <WithPorts>
            <Slot />
          </WithPorts>
        </ReducedMotionProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

/**
 * The ports, wrapped where a suite said what they are — and the live channel and the payment
 * provider always.
 *
 * Composed here rather than in `TestRoot` so adding a port is one entry rather than another
 * level of nesting and another conditional. The live channel's default is a fake rather than
 * the device, for the reason `stubLiveStream` states; the payment provider's, for the reason
 * `stubPayments` states.
 */
function WithPorts({ children }: { readonly children: ReactNode }) {
  const withPayments = (
    <PaymentsProvider port={payments ?? NO_PAYMENTS}>{children}</PaymentsProvider>
  );

  const withShare =
    share === undefined ? withPayments : <ShareProvider port={share}>{withPayments}</ShareProvider>;

  const withClipboard =
    clipboard === undefined ? (
      withShare
    ) : (
      <ClipboardProvider port={clipboard}>{withShare}</ClipboardProvider>
    );

  const withHaptics =
    haptics === undefined ? (
      withClipboard
    ) : (
      <HapticsProvider port={haptics}>{withClipboard}</HapticsProvider>
    );

  const withLive = (
    <LiveStreamProvider port={liveStream ?? SILENT_CHANNEL}>{withHaptics}</LiveStreamProvider>
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

/**
 * The payment provider a suite that said nothing gets — one instance for the process, for
 * `SILENT_CHANNEL`'s reason: a fake holds what was typed, and shared across suites it would carry
 * one suite's card into the next. This one is a fresh fake per process that no suite types into.
 */
const NO_PAYMENTS: PaymentsPort = fakePayments();

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
 * The profile as `GET /players/me/profile` serves it: the three facts Play's search screen
 * opens on — a week, a radius and one declaration — and the facts the read grew for the You
 * tab ([#466](https://github.com/Raketa02/Raketa/issues/466)): the tags, the photos with their
 * verdicts, the intro, the opt-in and the owner's own gender and preference.
 *
 * A padel declaration is in it because *rated and undeclared* is a **different screen** —
 * ADR-0094's one-tap interstitial — so a suite that wants the ordinary case has to say a
 * declaration exists, and a suite that wants the interstitial passes a surface without one
 * (`profileSurface`). Two photos, the first passed and the second flagged, because the row on
 * You is the one screen whose question is *what did the check conclude about mine*.
 */
export const PROFILE_SURFACE_SERVED: Wire['PlayerProfileReadResponse'] = {
  weekly_hours: [
    { day: 2, hour: 19 },
    { day: 6, hour: 9 },
  ],
  search_radius_km: 12,
  play_intents: { PADEL: 'FOR_FUN' },
  social_tags: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'WARMS_UP_PROPERLY', 'HERE_TO_IMPROVE'],
  photos: [
    { photo_id: 'photo-held-1', review: 'allowed' },
    { photo_id: 'photo-held-2', review: 'flagged' },
  ],
  intro: 'Will travel for a hard game.',
  proposals_opt_in: {
    accepted: true,
    copy_version: 'proposals-opt-in.v3',
    surface: 'ONBOARDING',
    answered_at: '2026-08-12T10:00:00Z',
  },
  gender: 'MAN',
  gender_preference: 'ANY',
};

/**
 * The served surface with some facts replaced — for the suites about the week, the radius or
 * the declaration, which vary those three and have nothing to say about the rest.
 */
export function profileSurface(
  overrides: Partial<Wire['PlayerProfileReadResponse']>,
): Wire['PlayerProfileReadResponse'] {
  return { ...PROFILE_SURFACE_SERVED, ...overrides };
}

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

/**
 * One yes of the reader's own, as `GET /interest` lists it under `outgoing` — the row *You said
 * yes* and the challenge screen's invitee's line are drawn from (ADR-0169 §8).
 *
 * The two dates are the server's and no suite reads them, so they are fixed here rather than
 * spelled per test.
 */
export function outgoingYes(
  playerId: string,
  sport: Wire['Sport'],
): Wire['OutgoingInterestSchema'] {
  return {
    player_id: playerId,
    sport,
    at: '2026-08-30T18:00:00Z',
    expires_at: '2026-09-20T18:00:00Z',
  };
}

/** The reader's own yeses, as the server would list them — who, per sport. Nothing else served. */
export function stubOutgoingYeses(
  transport: Transport,
  ...yeses: readonly (readonly [playerId: string, sport: Wire['Sport']])[]
) {
  stubInterest(transport, {
    outgoing: yeses.map(([playerId, sport]) => outgoingYes(playerId, sport)),
    mutual: [],
    outstanding: [],
  });
}

export const GAMES_PATH = '/api/v1/games';

/**
 * Your games, as `GET /games` answers — **arranged, played and finished in one list.**
 *
 * `read_at` is the instant every standing and deadline in it was folded against, so a suite that
 * wants a countdown to say a particular thing sets it here rather than mocking a clock: the
 * screens measure from this field and never from the device.
 *
 * Defaulted to nothing, because every launch now draws the Home tab and almost no suite is about
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

export const pairingPath = (gameId: string) => `/api/v1/games/${gameId}/pairing`;

/**
 * One game's pairing, as `GET /games/{game_id}/pairing` answers — **or the refusal it gives by
 * name**, `pairing_is_history` once the game has happened.
 *
 * Not stubbed on every launch: the read is made on the game screen's plan lead and nowhere else,
 * and a suite about that screen says what the court is worth. A suite that reaches the plan lead
 * without stubbing it gets the transport's *no stub* failure folded to nothing drawn, which is the
 * block's own answer to an outage — so nothing breaks, and a suite asserting the block is present
 * has to say so.
 */
export function stubPairing(
  transport: Transport,
  gameId: string,
  answer:
    Wire['GamePairingResponse'] | { readonly refused: 409 | 404 | 403; readonly code: string },
) {
  transport.on('GET', pairingPath(gameId), () =>
    'refused' in answer ? errorResponse(answer.refused, answer.code) : json(answer),
  );
}

export const PLANS_PATH = '/api/v1/plans';

/**
 * Your plans, as `GET /plans` answers — **one row per court you hold an accepted seat on, written
 * or not**, keyed by `challenge_id` and carrying the anchor its day row runs from (ADR-0164).
 *
 * There is **no `read_at` on this envelope**, deliberately: a plan folds nothing against the clock,
 * so a suite that wants *today* to be a particular day sets the surface's own instant instead —
 * the room's `read_at` in the chat, `stubGames`' on the game screen — which is what keeps every
 * clock on a surface the same one. The row's `anchor` is not a clock: it is where the day row's
 * horizon runs from.
 *
 * Stubbed on every launch beside the games and the rooms, for the reason those two are: the plan
 * card is pinned in every room from its opening, so a suite that opens one would otherwise fail at
 * the socket with a name that points at `fetch` rather than at the card
 * ([#366](https://github.com/Raketa02/Raketa/issues/366)).
 *
 * **Defaulted to no rows, and the two surfaces read that differently.** The room draws nothing
 * until its row lands — the row is what says there is a plan to draw, and carries the anchor to
 * draw it with — so a suite that wants the card in a room stubs the court's row. The game screen
 * draws the card off the game's own `planned_at` meanwhile, which is what the row's anchor is once
 * a game exists (ADR-0164 §4), so its suites get three empty slots with nothing stubbed.
 */
export function stubPlans(transport: Transport, plans: readonly Wire['PlanSchema'][] = []) {
  transport.on('GET', PLANS_PATH, () => json<Wire['PlanListResponse']>({ plans: [...plans] }));
}

/** The path one court's slot answers on — addressed by its challenge — for a suite that records one. */
export const planSlotPath = (challengeId: string, slot: 'place' | 'day' | 'hour') =>
  `${PLANS_PATH}/${challengeId}/${slot}`;

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
 *
 * `people` is the page's own authors and actors, which the wire says is *not the roster*. It
 * defaults to nobody because the client merges a page's people into the ones it already holds,
 * so a page whose authors are all members names them off the room's first read — a suite whose
 * page names somebody that read did not supplies them here, as the wire would.
 */
export function stubEntries(
  transport: Transport,
  conversationId: string,
  entries: readonly (Wire['MessageSchema'] | Wire['SystemLineSchema'])[] = [],
  people: readonly Wire['ConversationPersonSchema'][] = [],
) {
  transport.on('GET', `${conversationPath(conversationId)}/entries`, () =>
    json<Wire['EntryPageResponse']>({ entries: [...entries], people: [...people] }),
  );
}

/** The path `GET /sportsmanship` answers on, for a suite that wants to say which cards are open. */
export const SPORTSMANSHIP_PATH = '/api/v1/sportsmanship';

/**
 * The courts still waiting for this player's stars, as `GET /sportsmanship` answers — **ids
 * and nothing else**, soonest to expire first.
 *
 * Defaulted to nothing, because an empty list is the ordinary answer and almost no suite is
 * about one: a card appears the day after a game and stays a week, so most launches have none
 * and the section renders nothing at all.
 *
 * A suite with cards calls this after `stubGate`, and has to `stubGames` the evenings behind
 * them: the route carries ids, and everything a card *says* comes from the games list it is
 * drawn beside.
 */
export function stubSportsmanship(
  transport: Transport,
  cards: readonly Wire['OpenCardSchema'][] = [],
) {
  transport.on('GET', SPORTSMANSHIP_PATH, () =>
    json<Wire['OpenCardsResponse']>({ cards: [...cards] }),
  );
}

/**
 * Where the feature-flag datafile is fetched from, as the fake socket sees it: the features host
 * is stripped from the URL exactly as the API's is, and `development` is the environment
 * `jest.config.js` sets (ADR-0180 §3, §4).
 */
export const DATAFILE_PATH = '/development/featurevisor-player.json';

/**
 * **The datafile the flags host serves — or none.**
 *
 * Not a wire type: the file is the flags repo's, not the API's, and the app checks its envelope
 * rather than generating one. So it is described as the object it is, and a suite about a flag
 * builds the one it needs.
 *
 * `'none'` is a 404 — what the flags repo's serve script answers for a file it has not built, and
 * a failure the app does not retry, so a suite that says nothing about flags is not left with a
 * read going round underneath it.
 */
export function stubDatafile(
  transport: Transport,
  served: Readonly<Record<string, unknown>> | 'none' = 'none',
) {
  transport.on('GET', DATAFILE_PATH, () =>
    served === 'none' ? new Response('Not Found', { status: 404 }) : json(served),
  );
}

/**
 * **A datafile as the flags repo builds one** — each named feature on or off for everybody, which
 * is `percentage: 100` or `0` on one `everyone` rule in the repo's YAML. Enough for every walk
 * about a gate; a walk about *who* a rule reaches spells its own traffic.
 *
 * The rest is what CLI 3.11.0 emits today. `schemaVersion` is the one fact the app refuses a
 * datafile on, so a walk about that refusal overrides it.
 */
export function datafileFor(
  features: Readonly<Record<string, 'on' | 'off'>>,
  overrides: Readonly<Record<string, unknown>> = {},
): Readonly<Record<string, unknown>> {
  return {
    schemaVersion: '2',
    featurevisorVersion: '3.11.0',
    revision: '1',
    segments: {},
    features: Object.fromEntries(
      Object.entries(features).map(([key, state]) => [
        key,
        {
          bucketBy: 'playerId',
          traffic: [{ key: 'everyone', segments: '*', percentage: state === 'on' ? 100000 : 0 }],
        },
      ]),
    ),
    variables: {},
    ...overrides,
  };
}

/**
 * **The datafile has been answered, and the answer is in hand** — the moment a toggle has
 * *reached the app* (ADR-0180 §6).
 *
 * Nothing on screen says so, by design: a gate reads its flag once, when it mounts, so a datafile
 * landing under a mounted screen changes nothing a player could see. A walk about a gate therefore
 * waits on the read itself — `count` requests made, and no flag read still running — before it
 * mounts the screen it is asking about.
 */
export async function datafileSettled(transport: Transport, count = 1) {
  await waitFor(() =>
    expect(transport.requestsTo('GET', DATAFILE_PATH).length).toBeGreaterThanOrEqual(count),
  );
  await waitFor(() => expect(queryClient.isFetching({ queryKey: featureFlagKeys.all })).toBe(0));
}

/**
 * **Classic play, switched on** — for every suite about the old loop: Find a game, the Players
 * deck, Chats. Since [#512](https://github.com/Raketa02/Raketa/issues/512) the Play tab opens on
 * Groups without a datafile, and since [#550](https://github.com/Raketa02/Raketa/issues/550) the
 * bar is Home · Play · You without one; `classic_play` brings all of it back at once.
 *
 * Served, launched, and **waited on before anything presses Play**: a gate reads its flag once, when
 * its screen mounts, so a Play press that raced the datafile would land on Groups — correctly, and
 * not what the suite is about. The bar follows the flag, so once the datafile has settled Players
 * and Chats are there to press. Call it where the suite would have called `launchSignedIn`, after
 * `stubGate` (which serves no datafile).
 */
export async function launchIntoClassicPlay(transport: Transport, initialUrl = '/') {
  stubDatafile(transport, datafileFor({ classic_play: 'on' }));
  await launchSignedIn(initialUrl);
  await datafileSettled(transport);
}

export const MY_GROUPS_PATH = '/api/v1/groups';

/**
 * **The player's Groups list** — `GET /groups`, newest joined first. Defaulted to none by
 * `stubGate`, because the Play tab opens on Groups since #512 and every suite that presses Play
 * reads it; a suite about the list calls this again to serve one.
 */
export function stubMyGroups(transport: Transport, groups: readonly Wire['MyGroupSchema'][] = []) {
  transport.on('GET', MY_GROUPS_PATH, () =>
    json<Wire['MyGroupsResponse']>({ groups: [...groups] }),
  );
}

export const OWN_RECORD_PATH = '/api/v1/players/me/record';

/** What the signed-in player is called — on `GET /users/me` and on their own record alike. */
const GATE_USER_NAME = 'Ada Lovelace';
const GATE_USER_NICKNAME = 'ada';

/**
 * Your own record, as `GET /players/me/record` answers — a player rated in one sport with a
 * record behind them, and the sportsmanship figure with its count, which the route serves its
 * subject as it serves any reader (ADR-0179 §5, #468).
 *
 * The You tab draws it three times over: the header card's face, intro and score, the
 * reliability row's line, and — with `?sport=` — the passport's blocks under each card. The
 * transport drops the query string, so one stub answers all three.
 */
export const OWN_RECORD_SERVED: Wire['PlayerRecordResponse'] = {
  is_self: true,
  name: GATE_USER_NAME,
  nickname: GATE_USER_NICKNAME,
  area_code: 'A+050612+0019938',
  social_tags: ['PLAYS_TO_WIN', 'STAYS_FOR_A_DRINK'],
  intro: 'Will travel for a hard game.',
  sports: [{ sport: 'PADEL', level: 2.71, band: 'Established' }],
  skill: {
    sport: 'PADEL',
    level: 2.71,
    band: 'Established',
    confidence: 28,
    counted_games: 9,
    likely_range: { low: 2.09, high: 3.33 },
    last_five: ['WIN', 'LOSS', 'WIN', 'WIN', 'LOSS'],
  },
  reliability: {
    player_score: 92,
    strands: [
      { strand: 'SHOWS_UP', good: 11, opportunities: 12, pct: 92 },
      { strand: 'ANSWERS_CHALLENGES', good: 6, opportunities: 7, pct: 86 },
      { strand: 'ANSWERS_RESULTS', good: 5, opportunities: 5, pct: 100 },
    ],
  },
  variety: { distinct_opponents: 14, times_on_court: 20 },
  // The figure and its count, to the subject as to anybody (#468, ADR-0179 §5).
  sportsmanship: { average: 4.3, raters: 12 },
};

/**
 * Your own record, for any suite that opens the You tab.
 *
 * Separate from `stubGate` because the gate does not read it — the tab does, on arrival, and a
 * suite that never presses the column never asks for it.
 */
export function stubOwnRecord(
  transport: Transport,
  served: Wire['PlayerRecordResponse'] = OWN_RECORD_SERVED,
) {
  transport.on('GET', OWN_RECORD_PATH, () => json(served));
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
   * The address the account signs in with. Defaulted for `id`'s reason; the suites about an
   * invitation's link state it, because whose invitation a link is is decided by it (#520).
   */
  readonly email?: string;
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
  /**
   * What this player is called — the gate's **first** branch
   * ([ADR-0171](../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
   * §3). `null` is an account that has not named itself yet, which the gate sends to the naming
   * step before anything else.
   *
   * Defaults to **named**, because almost no suite is about the step: every launch that lands
   * on welcome, in the app or in the middle of a run is a launch by somebody the app can already
   * call by name. The nickname rides with it and is not a parameter — nothing the gate reads
   * depends on it, and a suite about the You tab reads it off `GATE_USER`.
   */
  readonly name?: string | null;
  /**
   * The handle — **with the name by default**, since the two are one act: an account with no name
   * has no handle, and a named one has `ada`. An account an Invitation opened is the one shape that
   * holds a name and no handle (ADR-0185 §4), so its suites pass `null`.
   */
  readonly nickname?: string | null;
  /**
   * Whether the account carries the **tester mark** (ADR-0180 §9) — the one thing on this read the
   * flag seam sends on. Defaults to **false**, which is every account until an admin marks it.
   */
  readonly isTester?: boolean;
  /**
   * **Which profiles the account holds** — the gate's first read (ADR-0185 §3). Defaults to a
   * player's: every sign-up acts as a player and administers nothing. A suite about the
   * administrator area passes `ADMINISTRATOR_ONLY` or its own.
   */
  readonly profiles?: Wire['AccountProfilesSchema'];
}

/** What every signed-up account holds: it acts as a player, runs no club's groups, and is invited to none. */
export const PLAYER_ONLY: Wire['AccountProfilesSchema'] = {
  acts_as_player: true,
  administers: [],
  pending_invitations: [],
};

/**
 * The signed-in player, as `GET /users/me` answers. Identity is filler; the flag is not, and
 * neither is the name: it is what every screen says about her, and its absence is where a
 * launch is sent first.
 */
export const GATE_USER: Wire['MeResponse'] = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  name: GATE_USER_NAME,
  nickname: GATE_USER_NICKNAME,
  authority: 'player',
  is_admin: false,
  is_active: true,
  is_tester: false,
  has_player_profile: false,
  created_at: '2026-08-13T10:00:00Z',
  adult_attested: true,
  profiles: PLAYER_ONLY,
};

/**
 * The gate's three reads: what this player is rated at, what they left unfinished, and who
 * they are — which is where *does a Player profile exist* is served from.
 *
 * The unfinished-run read is **one** request covering every sport. An empty list is the
 * answer for a player with nothing outstanding — a 200, not a 204 and not a failure.
 *
 * **`stubGames`, `stubPlans`, `stubConversations` and `stubSportsmanship` are in here and none
 * of them is a gate read.** The gate's fourth destination is the shell's root, the shell's root is
 * the Home tab, and the Home tab draws a games list
 * ([#314](https://github.com/Raketa02/Raketa/issues/314)) — so every suite that lands in the app
 * makes that request whether or not it is about one. The rooms are one step further out: only the
 * Chats screen reads them, but a suite that walks to that tab for any reason would otherwise fail
 * at the socket, and the plan card pinned in every room with a game reads a third list on the way.
 * All three are defaulted to nothing, and a suite with any of them calls the stub again afterwards
 * to replace it.
 *
 * **So is the Groups list** ([#512](https://github.com/Raketa02/Raketa/issues/512)): the Play tab
 * opens on Groups with the code defaults, so a suite that presses Play for any reason reads it.
 *
 * **So is the feature-flag datafile**, and for the same reason: the signed-in app fetches it the
 * moment it opens, whatever the suite is about (ADR-0180 §6). It is defaulted to **none**, which
 * is every flag at its code default — the app as it ships. A suite about a flag calls
 * `stubDatafile` again afterwards to serve one.
 *
 * **The cards read is not made on that tab at all**, and it is still stubbed here. The card
 * asking how the other players were is drawn at the end of the **game screen**, one push in,
 * so landing in the app never asks for the list — but a suite that opens a game does, and
 * every one of those lands through here first. Defaulted to nothing for the reason the games
 * list is: a suite that is not about a card should not have to know one exists.
 */
export function stubGate(
  transport: Transport,
  {
    ratings = [],
    runs = [],
    hasPlayerProfile = false,
    id = GATE_USER.id,
    email = GATE_USER.email,
    name = GATE_USER.name ?? null,
    nickname = name === null ? null : (GATE_USER.nickname ?? null),
    isTester = false,
    profiles = PLAYER_ONLY,
  }: GateStub = {},
) {
  transport.on('GET', '/api/v1/ratings', () =>
    json<Wire['RatingsResponse']>({ ratings: [...ratings] }),
  );

  transport.on('GET', '/api/v1/users/me', () =>
    json<Wire['MeResponse']>({
      ...GATE_USER,
      id,
      email,
      name,
      nickname,
      has_player_profile: hasPlayerProfile,
      is_tester: isTester,
      adult_attested: profiles.acts_as_player,
      profiles,
    }),
  );

  stubRunsInProgress(transport, runs);
  stubGames(transport);
  stubPlans(transport);
  stubChallenges(transport);
  stubConversations(transport);
  stubSportsmanship(transport);
  stubDatafile(transport);
  stubMyGroups(transport);
  stubPaymentMethod(transport);
  stubGamesAndMoney(transport);
  stubLiveYeses(transport);
}

export const PAYMENT_METHOD_PATH = '/api/v1/players/me/payment-methods/current';

export const GAMES_AND_MONEY_PATH = '/api/v1/players/me/games-and-money';

/** The two limits a suite may set — the rest of the answer is the form's offer. */
export type LimitsStub = Partial<
  Pick<Wire['GamesAndMoneyResponse'], 'games_per_week' | 'most_ill_pay_grosze'>
>;

/**
 * Games & money, as `GET …/games-and-money` answers — **two games a week and no ceiling**, the
 * backend's own defaults, unless the suite says otherwise. The gate stubs it, because the You tab's
 * *Games & money* row reads it on every visit to the tab (#554).
 */
export function stubGamesAndMoney(transport: Transport, limits: LimitsStub = {}) {
  transport.on('GET', GAMES_AND_MONEY_PATH, () =>
    json<Wire['GamesAndMoneyResponse']>(gamesAndMoney(limits)),
  );
}

/** The whole answer, the form's offer included — the backend's range and ceilings. */
export function gamesAndMoney(limits: LimitsStub = {}): Wire['GamesAndMoneyResponse'] {
  return {
    games_per_week: 2,
    most_ill_pay_grosze: null,
    games_per_week_range: { least: 1, most: 7 },
    most_ill_pay_choices_grosze: [3500, 4500, 6000],
    ...limits,
  };
}

export const LIVE_YESES_PATH = '/api/v1/players/me/live-yeses';

/**
 * The live yeses, as `GET …/live-yeses` answers — **none** unless the suite says otherwise. The gate
 * stubs it, because Payments' state B reads it whenever a method is saved, and a game's details
 * read it when the deck no longer deals the game (#554).
 */
export function stubLiveYeses(transport: Transport, yeses: readonly Wire['LiveYesSchema'][] = []) {
  transport.on('GET', LIVE_YESES_PATH, () =>
    json<Wire['LiveYesesResponse']>({ yeses: [...yeses], cap_per_sport: 10 }),
  );
}

/** The version of the payment terms the backend holds in force (#536). */
export const PAYMENT_TERMS_IN_FORCE = '2026-09-29';

/**
 * The saved payment method, as `GET …/payment-methods/current` answers — **nothing saved** unless
 * the suite says otherwise. The gate stubs it, because the You tab's Payments row reads it on every
 * visit to the tab (#552).
 */
export function stubPaymentMethod(
  transport: Transport,
  method: Wire['SavedMethodSchema'] | null = null,
  { termsNeeded = false }: { readonly termsNeeded?: boolean } = {},
) {
  transport.on('GET', PAYMENT_METHOD_PATH, () =>
    json<Wire['PaymentMethodResponse']>({
      method,
      terms_needed: termsNeeded,
      terms_version: PAYMENT_TERMS_IN_FORCE,
    }),
  );
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

/**
 * **The tree with the app's link reader in front of it** (#520) — `src/app/+native-intent`, which
 * expo-router hands every address the operating system opens the app with before it routes one.
 *
 * Its own table rather than an entry in `ONBOARDING_ROUTES`, because the reader is the gate a link
 * passes and nothing else: every other suite's `initialUrl` is a route the suite put the player on,
 * and the reader would — rightly — refuse every one of them that is not one of the three links.
 */
export const ROUTES_WITH_LINKS = { ...ONBOARDING_ROUTES, '+native-intent': NativeIntent };

/**
 * **A cold start by a link.** The address is what expo-router hands the reader for a launch — the
 * harness takes a path, so `/join/<code>` stands for `raketa://join/<code>`; the scheme's own
 * spelling is walked by `openLink` and read in `incomingLinkUrl.test.ts`.
 */
export async function launchByLink(path: string, { signedIn }: { readonly signedIn: boolean }) {
  if (signedIn) await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  else setSessionStatus('unauthenticated');
  renderRouter(ROUTES_WITH_LINKS, { initialUrl: path });
}

/**
 * **A link opened while the app is running** — what expo-router's listener does with one: the
 * reader's answer is navigated to, and an empty answer is no navigation at all. The full address,
 * scheme and all, because that is what the operating system hands a running app.
 */
export function openLink(url: string): void {
  act(() => {
    const to = NativeIntent.redirectSystemPath({ path: url, initial: false });
    // The reader answers with one of its own screens' paths, or nothing; the router's typed hrefs
    // cannot know which path a string is.
    if (to !== '') router.navigate(to as Href);
  });
}
