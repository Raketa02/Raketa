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
import OfficialGroupRoute from '@/app/(administrator)/administrator/[clubId]/group/[groupId]/index';
import OfficialGroupMembersRoute from '@/app/(administrator)/administrator/[clubId]/group/[groupId]/members';
import AppLayout from '@/app/(app)/_layout';
import TabsLayout from '@/app/(app)/(tabs)/_layout';
import BookedGameRoute from '@/app/(app)/(tabs)/booking/[bookingId]/index';
import BookedGameChatRoute from '@/app/(app)/(tabs)/booking/[bookingId]/chat';
import BookedGameResultRoute from '@/app/(app)/(tabs)/booking/[bookingId]/result';
import SeatInviteRoute from '@/app/(app)/(tabs)/booking/[bookingId]/invite';
import NoticesRoute from '@/app/(app)/(tabs)/notices';
import NewInRakietaRoute from '@/app/(app)/(tabs)/new-in-rakieta';
import RankingsRoute from '@/app/(app)/(tabs)/rankings';
import SameLevelRoute from '@/app/(app)/(tabs)/same-level';
import SameVibeRoute from '@/app/(app)/(tabs)/same-vibe';
import HottestGroupsRoute from '@/app/(app)/(tabs)/hottest-groups';
import HomeRoute from '@/app/(app)/(tabs)/index';
import PlayRoute from '@/app/(app)/(tabs)/play/index';
import NewGroupRoute from '@/app/(app)/(tabs)/play/new-group';
import JoinGroupRoute from '@/app/(app)/(tabs)/play/join';
import GroupRoute from '@/app/(app)/(tabs)/play/group/[groupId]/index';
import GroupFriendsRoute from '@/app/(app)/(tabs)/play/group/[groupId]/friends';
import GroupInfoRoute from '@/app/(app)/(tabs)/play/group/[groupId]/info';
import GroupMembersRoute from '@/app/(app)/(tabs)/play/group/[groupId]/members';
import GroupEditRoute from '@/app/(app)/(tabs)/play/group/[groupId]/edit';
import GameDetailsRoute from '@/app/(app)/(tabs)/play/group/[groupId]/game/[proposalId]';
import RescueRoute from '@/app/(app)/(tabs)/play/group/[groupId]/rescue/[bookingId]';
import PostAGameRoute from '@/app/(app)/(tabs)/play/group/[groupId]/post';
import YouRoute from '@/app/(app)/(tabs)/you';
import YouAreaRoute from '@/app/(app)/(tabs)/you/area';
import YouBlockedPlayersRoute from '@/app/(app)/(tabs)/you/blocked-players';
import YouFriendsRoute from '@/app/(app)/(tabs)/you/friends';
import YouGamesAndMoneyRoute from '@/app/(app)/(tabs)/you/games-and-money';
import YouIntroRoute from '@/app/(app)/(tabs)/you/intro';
import YouKindOfGameRoute from '@/app/(app)/(tabs)/you/kind-of-game';
import YouNameRoute from '@/app/(app)/(tabs)/you/name';
import YouNotificationsRoute from '@/app/(app)/(tabs)/you/notifications';
import YouPaymentsRoute from '@/app/(app)/(tabs)/you/payments';
import YouPassportRoute from '@/app/(app)/(tabs)/you/passport';
import YouPhotosRoute from '@/app/(app)/(tabs)/you/photos';
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
import IntroRoute from '@/app/(onboarding)/intro';
import LocationRoute from '@/app/(onboarding)/location';
import NameRoute from '@/app/(onboarding)/name';
import StartPlayingRoute from '@/app/(onboarding)/start-playing';
import OnboardingLayout from '@/app/(onboarding)/_layout';
import PhotosRoute from '@/app/(onboarding)/photos';
import QuestionRoute from '@/app/(onboarding)/question/[assessmentId]';
import GenderRoute from '@/app/(onboarding)/gender';
import ResultRoute from '@/app/(onboarding)/result/[assessmentId]';
import ReviewRoute from '@/app/(onboarding)/review/[assessmentId]';
import SportsRoute from '@/app/(onboarding)/sports';
import TagsRoute from '@/app/(onboarding)/tags';
import { fetchCurrentUserAtLaunch, restoreSession } from '@/features/auth/types';
import { featureFlagKeys } from '@/features/feature_flags/types';
import { HOME_COPY, warmHome } from '@/features/shell/types';
import { beginSession, setSessionStatus } from '@/shared/lib/auth';
import { SplashHoldsProvider, type SplashHolds } from '@/shared/lib/bootstrap';
import {
  ClipboardProvider,
  HapticsProvider,
  KeyboardProvider,
  ShareProvider,
  ImagePickingProvider,
  LiveStreamProvider,
  LocationProvider,
  PaymentsProvider,
  PushProvider,
  type ClipboardPort,
  type PaymentsPort,
  type PushPort,
  type HapticsPort,
  type KeyboardPort,
  type SharePort,
  type ImagePickingPort,
  type LiveStreamPort,
  type LocationPort,
  type Reachability,
} from '@/shared/lib/platform';
import { raisePhoneFlag } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';

import { fakePayments } from './platform';
import { FILTER_OFF, SERGIO_RELIABILITY } from './playerRecord';
import {
  errorResponse,
  json,
  noContent,
  servedBody,
  type RecordedRequest,
  type Transport,
  type Wire,
} from './transport';

/**
 * The Home tab's one line — which is what *the player is in the app* looks like on screen.
 *
 * The gate's *app* destination is the shell's root, and the shell's root is the Home tab, so
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
  // The three-tab shell. Play is a directory because its groups screens land under it, and the bar
  // reads its active column off that first segment.
  '(app)/(tabs)/index': HomeRoute,
  '(app)/(tabs)/play/index': PlayRoute,
  // Play › Groups' screens (#512–#514), under Play so the column stays lit and *back* is the list —
  // and Friends, Members and Edit group over a group's page, so *back* is the page.
  '(app)/(tabs)/play/new-group': NewGroupRoute,
  '(app)/(tabs)/play/join': JoinGroupRoute,
  '(app)/(tabs)/play/group/[groupId]/index': GroupRoute,
  '(app)/(tabs)/play/group/[groupId]/friends': GroupFriendsRoute,
  '(app)/(tabs)/play/group/[groupId]/info': GroupInfoRoute,
  '(app)/(tabs)/play/group/[groupId]/members': GroupMembersRoute,
  '(app)/(tabs)/play/group/[groupId]/edit': GroupEditRoute,
  '(app)/(tabs)/play/group/[groupId]/game/[proposalId]': GameDetailsRoute,
  // A rescue seen from outside (#557) — a Seat open card's or a Seats to fill row's details.
  '(app)/(tabs)/play/group/[groupId]/rescue/[bookingId]': RescueRoute,
  '(app)/(tabs)/play/group/[groupId]/post': PostAGameRoute,
  // A booked game (#556) — its details pushed over Home, its chat and its result over the details,
  // under a `booking` segment: the Home tab's root is the shell's own root and has no segment to
  // nest under. Spelled `…/index` as the file tree spells it,
  // because the shell names the details to give them the push transition.
  '(app)/(tabs)/booking/[bookingId]/index': BookedGameRoute,
  '(app)/(tabs)/booking/[bookingId]/chat': BookedGameChatRoute,
  '(app)/(tabs)/booking/[bookingId]/result': BookedGameResultRoute,
  '(app)/(tabs)/booking/[bookingId]/invite': SeatInviteRoute,
  // The recent notices behind Home's bell (#559), under a `notices` segment the shell counts as Home's.
  '(app)/(tabs)/notices': NoticesRoute,
  // Rankings, behind the trophy left of Home's bell (#775).
  '(app)/(tabs)/rankings': RankingsRoute,
  '(app)/(tabs)/new-in-rakieta': NewInRakietaRoute,
  '(app)/(tabs)/same-level': SameLevelRoute,
  '(app)/(tabs)/same-vibe': SameVibeRoute,
  // The Groups heating up page, behind its line's *All groups ›* (#823).
  '(app)/(tabs)/hottest-groups': HottestGroupsRoute,
  // You is a directory since the tab was built (ADR-0179): the root, and one screen per row
  // pushed over it, each under the tab's first segment so the column stays lit. Spelled
  // `you/index` as the file tree spells it, because the shell names the pushed screens to give
  // them the push transition and `Stack.Screen` matches on the name.
  '(app)/(tabs)/you/index': YouRoute,
  '(app)/(tabs)/you/passport': YouPassportRoute,
  '(app)/(tabs)/you/reliability': YouReliabilityRoute,
  '(app)/(tabs)/you/kind-of-game': YouKindOfGameRoute,
  '(app)/(tabs)/you/week': YouWeekRoute,
  '(app)/(tabs)/you/area': YouAreaRoute,
  '(app)/(tabs)/you/who-you-play-with': YouWhoYouPlayWithRoute,
  '(app)/(tabs)/you/photos': YouPhotosRoute,
  '(app)/(tabs)/you/tags': YouTagsRoute,
  '(app)/(tabs)/you/intro': YouIntroRoute,
  '(app)/(tabs)/you/name': YouNameRoute,
  '(app)/(tabs)/you/games-and-money': YouGamesAndMoneyRoute,
  '(app)/(tabs)/you/payments': YouPaymentsRoute,
  '(app)/(tabs)/you/notifications': YouNotificationsRoute,
  '(app)/(tabs)/you/blocked-players': YouBlockedPlayersRoute,
  '(app)/(tabs)/you/friends': YouFriendsRoute,
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
  '(administrator)/administrator/[clubId]/group/[groupId]/index': OfficialGroupRoute,
  '(administrator)/administrator/[clubId]/group/[groupId]/members': OfficialGroupMembersRoute,
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
  // (ADR-0199 §3).
  '(onboarding)/name': NameRoute,
  // *Start playing*'s first step, the Adult attestation (#517), at the gate's own address: where it
  // sends an account that holds no profile at all. The You tab pushes the same screen inside its
  // area.
  '(onboarding)/start-playing': StartPlayingRoute,
  '(onboarding)/sports': SportsRoute,
  '(onboarding)/question/[assessmentId]': QuestionRoute,
  '(onboarding)/review/[assessmentId]': ReviewRoute,
  '(onboarding)/result/[assessmentId]': ResultRoute,
  // The profile steps, in order — the rest of onboarding since #730. They are routes rather than
  // one route with a param so the sequence is visible in the file tree, the way the
  // authorization boundary is.
  '(onboarding)/tags': TagsRoute,
  '(onboarding)/intro': IntroRoute,
  '(onboarding)/photos': PhotosRoute,
  '(onboarding)/availability': AvailabilityRoute,
  '(onboarding)/location': LocationRoute,
  '(onboarding)/gender': GenderRoute,
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
 * The soft keyboard this tree types under, for the suites about the bar standing down while it is up
 * on Android (#882). Same shape and reasons as the share sheet above; unset is the device's port over
 * React Native's own `Keyboard`, which nothing in jest ever brings up.
 */
let keyboard: KeyboardPort | undefined;

/** Run the tree against this keyboard. Call before `launchSignedIn`. */
export function stubKeyboard(port: KeyboardPort): void {
  keyboard = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetKeyboard(): void {
  keyboard = undefined;
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
 * The phone this tree is pushed on, for the suites about the notices (#559). **Like the live channel
 * and the payment provider, it always has one**: the device's port would reach `expo-notifications`,
 * which jest's setup mocks into a phone nobody described. A suite that says nothing gets a phone that
 * was never asked, says nothing when asked and has no token — `NO_PUSH`, which no suite can change;
 * a suite about the notices says so with `stubPush(fakePush())` and keeps it.
 */
let push: PushPort | undefined;

/** Run the tree against this phone. Call before `launchSignedIn`. */
export function stubPush(port: PushPort): void {
  push = port;
}

/** Forget it again. Called from `afterEach`, beside `transport.restore()`. */
export function resetPush(): void {
  push = undefined;
}

/**
 * **The splash's holds, counted as the launch gate counts them** (ADR-0209 §3). The harness mounts no
 * launch gate — no suite waits out a splash — so a screen that says it is blank says it here, and the
 * entry gate's suite reads how many such declarations stand. Every tree withdraws its own as it
 * unmounts, so the count is back to nought between tests.
 */
let holdsStanding = 0;

const SPLASH_HOLDS: SplashHolds = {
  place: () => {
    holdsStanding += 1;
    let withdrawn = false;
    return () => {
      if (withdrawn) return;
      withdrawn = true;
      holdsStanding -= 1;
    };
  },
};

/** How many screens of the tree say, right now, that they are blank and the splash must wait. */
export function splashHoldsStanding(): number {
  return holdsStanding;
}

/**
 * The providers the real root layout composes, without the launch gate — the drawn splash, the
 * startup sequence, fonts and config validation are the launch path's business and have their own
 * tests (`LaunchGate.test.tsx`). Its one interface with the tree, the hold, is recorded instead.
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
          <SplashHoldsProvider holds={SPLASH_HOLDS}>
            <WithPorts>
              <Slot />
            </WithPorts>
          </SplashHoldsProvider>
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
  const withPush = <PushProvider port={push ?? NO_PUSH}>{children}</PushProvider>;

  const withPayments = (
    <PaymentsProvider port={payments ?? NO_PAYMENTS}>{withPush}</PaymentsProvider>
  );

  const withShare =
    share === undefined ? withPayments : <ShareProvider port={share}>{withPayments}</ShareProvider>;

  const withKeyboard =
    keyboard === undefined ? (
      withShare
    ) : (
      <KeyboardProvider port={keyboard}>{withShare}</KeyboardProvider>
    );

  const withClipboard =
    clipboard === undefined ? (
      withKeyboard
    ) : (
      <ClipboardProvider port={clipboard}>{withKeyboard}</ClipboardProvider>
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

/**
 * The phone a suite that said nothing gets — `SILENT_CHANNEL`'s shape, for its reason: one instance
 * for the process, and **inert**, because a fake holds a permission a suite can change by pressing
 * *Allow notifications* and shared across suites it would carry one suite's answer into the next.
 * Never asked, and asking changes nothing; no token; nothing ever arrives.
 */
const NO_PUSH: PushPort = {
  getPermission: async () => 'undetermined',
  requestPermission: async () => 'undetermined',
  readToken: async () => null,
  onTokenChange: () => () => {},
  onNotice: () => () => {},
  onOpen: () => () => {},
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

/**
 * **This account has been shown the guide on _Your rating_ on this phone already**
 * ([ADR-0200](../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8) — for a suite that
 * lands on *Your rating* and is about something else. The device's storage is emptied after every
 * test, so every test begins on a phone that has never shown it, and the guide would stand over
 * every rating it walks to. The account is the gate's player unless a suite signs in somebody
 * else. `theGuideOnYourRating.test` is the suite about the guide.
 */
export function ratingGuideAlreadyShown(account: string = GATE_USER.id): Promise<void> {
  return raisePhoneFlag(account, 'ratingGuideShown');
}

export const RUNS_IN_PROGRESS_PATH = '/api/v1/assessments/in-progress';

export const PROFILE_OPTIONS_PATH = '/api/v1/player-profile/options';

/**
 * The twenty-seven Social tags in their three groups and the selection bounds, 2 to 8 — as
 * `GET /player-profile/options` answers since ADR-0207 §7 (#829): the eight new ones at the end
 * of their groups.
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
        { id: 'STAYS_FOR_A_COFFEE' },
        { id: 'UP_FOR_A_BITE_AFTER' },
        { id: 'KEEPS_IN_TOUCH' },
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
        { id: 'HAPPY_TO_SWAP_PARTNERS' },
        { id: 'PATIENT_WITH_BEGINNERS' },
        { id: 'HAPPY_TO_SHARE_TIPS' },
        { id: 'BRINGS_THE_ENERGY' },
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
        { id: 'NEW_IN_TOWN' },
      ],
    },
  ],
  social_tag_selection: { minimum_tags: 2, maximum_tags: 8 },
};

export const PROFILE_SURFACE_PATH = '/api/v1/players/me/profile';

/**
 * The profile as `GET /players/me/profile` serves it: a week and one declaration, and the
 * facts the read grew for the You tab ([#466](https://github.com/Raketa02/Raketa/issues/466)):
 * the tags, the photos with their verdicts, the intro and the owner's own gender and
 * preference.
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
  play_intents: { PADEL: 'FOR_FUN' },
  social_tags: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'WARMS_UP_PROPERLY', 'HERE_TO_IMPROVE'],
  photos: [
    { photo_id: 'photo-held-1', review: 'allowed' },
    { photo_id: 'photo-held-2', review: 'flagged' },
  ],
  intro: 'Will travel for a hard game.',
  gender: 'MAN',
  gender_preference: 'ANY',
  show_me_to_new_people: true,
};

/**
 * The served surface with some facts replaced — for the suites about the week or the
 * declaration, which vary those and have nothing to say about the rest.
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

export const GAMES_PATH = '/api/v1/games';

/**
 * Your games, as `GET /games` answers — **arranged, played and finished in one list.**
 *
 * `read_at` is the instant every standing and deadline in it was folded against, so a suite that
 * wants a countdown to say a particular thing sets it here rather than mocking a clock: the
 * screens measure from this field and never from the device.
 *
 * Read by a booked game's result screen and the stars card at its foot — never by Home, which is
 * booked games only (#576). Defaulted to nothing; a suite about one of those screens serves its
 * game.
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
 * Not stubbed on every launch: the read is made by a booked game's forecast and nowhere else, and
 * a suite about that block says what the court is worth. A suite that reaches it without stubbing
 * it gets the transport's *no stub* failure folded to nothing drawn, which is the block's own
 * answer to an outage — so nothing breaks, and a suite asserting the block is present has to say
 * so.
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

/** The path `GET /conversations` answers on, for a suite that wants to say what rooms exist. */
export const CONVERSATIONS_PATH = '/api/v1/conversations';

/**
 * Your rooms, as `GET /conversations` answers — **every one you are a member of, newest first.**
 *
 * Stubbed on every launch: Home reads it to say whether a booked game's chat is open, and a booked
 * game's details and chat find their room through it.
 *
 * `read_at` is on the envelope and is deliberately not mapped — nothing drawn from the list is a
 * clock — so it is a constant rather than a parameter. Defaulted to nothing.
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
 * `jest.config.js` sets (ADR-0206 §3, §4).
 */
export const DATAFILE_PATH = '/development/featurevisor-player.json';

/**
 * **The datafile the flags host serves — or none.**
 *
 * Not a wire type: the file is the flags repo's, not the API's, and the app checks its envelope
 * rather than generating one. So it is described as the object it is, and a suite about a feature
 * flag builds the one it needs.
 *
 * `'none'` is a 404 — what the flags repo's serve script answers for a file it has not built, and
 * a failure the app does not retry, so a suite that says nothing about feature flags is not left
 * with a read going round underneath it.
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
 * *reached the app* (ADR-0206 §6).
 *
 * Nothing on screen says so, by design: a gate reads its feature flag once, when it mounts, so a
 * datafile landing under a mounted screen changes nothing a player could see. A walk about a gate
 * therefore waits on the read itself — `count` requests made, and no datafile read still running —
 * before it mounts the screen it is asking about.
 */
export async function datafileSettled(transport: Transport, count = 1) {
  await waitFor(() =>
    expect(transport.requestsTo('GET', DATAFILE_PATH).length).toBeGreaterThanOrEqual(count),
  );
  await waitFor(() => expect(queryClient.isFetching({ queryKey: featureFlagKeys.all })).toBe(0));
}

/**
 * **Explore, switched on** — for every suite that walks Play's *Groups | Explore* switcher. Since
 * [#826](https://github.com/Raketa02/Raketa/issues/826) Play is Groups under a Groups title without
 * a datafile; `explore` brings the switcher back.
 *
 * Served, launched, and **waited on before anything presses Play**: a gate reads its feature flag
 * once, when its screen mounts, so a Play press that raced the datafile would land on the Groups
 * title — correctly, and not what the suite is about. Call it where the suite would have called
 * `launchSignedIn`, after `stubGate` (which serves no datafile) — and again for a relaunch: it
 * waits on one read more than the walk had made before it.
 */
export async function launchWithExplore(transport: Transport, initialUrl = '/') {
  const asked = transport.requestsTo('GET', DATAFILE_PATH).length;
  stubDatafile(transport, datafileFor({ explore: 'on' }));
  await launchSignedIn(initialUrl);
  await datafileSettled(transport, asked + 1);
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

/**
 * Home's Hottest groups (#800) — none unless the suite says, so the row is hidden. **Its total is the
 * groups served unless the suite says** (#822): the server's counts a pool the row only samples.
 */
export const HOTTEST_GROUPS_PATH = '/api/v1/hottest-groups';

export function stubHottestGroups(
  transport: Transport,
  groups: readonly Wire['HottestGroupSchema'][] = [],
  total: number = groups.length,
) {
  transport.on('GET', HOTTEST_GROUPS_PATH, () =>
    json<Wire['HottestGroupsResponse']>({ groups: [...groups], total }),
  );
}

/**
 * The Groups heating up page (#823) — the transport drops `?after`, so one responder answers each
 * page.
 */
export const HOTTEST_GROUPS_ALL_PATH = '/api/v1/hottest-groups/all';

/** Home's New in Rakieta (#801) — nobody unless the suite says, so the row is hidden. */
export const NEW_IN_RAKIETA_PATH = '/api/v1/new-in-rakieta';
/** New in Rakieta's See all — the transport drops `?sport&after`, so one responder answers each page. */
export const NEW_IN_RAKIETA_ALL_PATH = '/api/v1/new-in-rakieta/all';

/** Its total is the players served unless the suite says (#822). */
export function stubNewInRakieta(
  transport: Transport,
  players: readonly Wire['NewInRakietaPlayerSchema'][] = [],
  total: number = players.length,
) {
  transport.on('GET', NEW_IN_RAKIETA_PATH, () =>
    json<Wire['NewInRakietaResponse']>({ players: [...players], total }),
  );
}

/** Home's Same competitive level (#802) — nobody unless the suite says, so the row is hidden. */
export const SAME_LEVEL_PATH = '/api/v1/same-level';
/** Same level's See all — the transport drops `?sport&after`, so one responder answers each page. */
export const SAME_LEVEL_ALL_PATH = '/api/v1/same-level/all';

/** Its total is the players served unless the suite says (#822). */
export function stubSameLevel(
  transport: Transport,
  players: readonly Wire['SameLevelPlayerSchema'][] = [],
  total: number = players.length,
) {
  transport.on('GET', SAME_LEVEL_PATH, () =>
    json<Wire['SameLevelResponse']>({ players: [...players], total }),
  );
}

/** Home's Same vibe (#803) — nobody unless the suite says, so the row is hidden. */
export const SAME_VIBE_PATH = '/api/v1/same-vibe';
/** Same vibe's See all — the transport drops `?sport&after`, so one responder answers each page. */
export const SAME_VIBE_ALL_PATH = '/api/v1/same-vibe/all';

/** Its total is the players served unless the suite says (#822). */
export function stubSameVibe(
  transport: Transport,
  players: readonly Wire['SameVibePlayerSchema'][] = [],
  total: number = players.length,
) {
  transport.on('GET', SAME_VIBE_PATH, () =>
    json<Wire['SameVibeResponse']>({ players: [...players], total }),
  );
}

/** Home's Top 10 (#805) — the transport drops `?sport|prefer`, so one responder answers each read. */
export const TOP_TEN_PATH = '/api/v1/top-10';

/**
 * **Home's Top 10** (#805) — nobody ranked anywhere unless the suite says, so the row is hidden. A
 * suite about the row answers by the sport asked (`topTen.test.tsx`).
 */
export function stubTopTen(
  transport: Transport,
  read: Wire['TopTenResponse'] = { sport: 'PADEL', anyone_listed: false, players: [] },
) {
  transport.on('GET', TOP_TEN_PATH, () => json<Wire['TopTenResponse']>(read));
}

export const OWN_RECORD_PATH = '/api/v1/players/me/record';

/** What the signed-in player is called — on `GET /users/me` and on their own record alike. */
const GATE_USER_NICKNAME = 'ada';

/**
 * Your own record, as `GET /players/me/record` answers — a player rated in one sport with a
 * record behind them, and the sportsmanship figure with its count, which the route serves its
 * subject as it serves any reader (ADR-0179 §5, #468).
 *
 * The You tab draws it three times over: the header card's face, intro and figure, the
 * reliability row's line, and — with `?sport=` — the passport's blocks under each card. The
 * transport drops the query string, so one stub answers all three.
 */
export const OWN_RECORD_SERVED: Wire['PlayerRecordResponse'] = {
  is_self: true,
  // Nothing stands between a player and themself: the route answers `NONE` on your own record.
  relation: 'NONE',
  // Nobody asks themself: the route answers `false` on your own record.
  can_add_friend: false,
  nickname: GATE_USER_NICKNAME,
  photos: [],
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
  // Sergio's six months — 75 · High, turned up 12 of 13, kept 13 of 14, late once (#660) — and
  // the filter the own record always carries, off (#662).
  reliability: { ...SERGIO_RELIABILITY, filter: FILTER_OFF },
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
   * Defaulted, because almost no suite is about identity. A suite that seats you on a court has
   * to state it: the face in your seat is a function of this id.
   */
  readonly id?: string;
  /**
   * The address the account signs in with. Defaulted for `id`'s reason; the suites about an
   * invitation's link state it, because whose invitation a link is is decided by it (#520).
   */
  readonly email?: string;
  /**
   * The runs this player left unfinished, in the order the server sends them — sport
   * registry order. Read by the door where play begins, never by the gate (#730): a run left
   * halfway is offered as *Carry on*, and a launch opens the app whatever this says.
   */
  readonly runs?: readonly Wire['InProgressAssessmentResponse'][];
  /**
   * Whether the profile steps have been committed — the gate's branch after the nickname
   * (ADR-0200 §1).
   *
   * Defaults to **false**: an account sign-up and the naming leave behind, which the gate sends to
   * the profile steps. A suite about anything inside the app states `true`.
   */
  readonly hasPlayerProfile?: boolean;
  /**
   * What this player is called — their nickname, and the gate's **first** branch
   * ([ADR-0199](../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). `null` is an
   * account that has not named itself yet — one sign-up created, or one an Invitation opened —
   * which the gate sends to the naming step before anything else.
   *
   * Defaults to **named**, as `ada`, because almost no suite is about the step: every launch that
   * lands on the profile steps or in the app is a launch by somebody the app can already call by
   * their nickname.
   */
  readonly nickname?: string | null;
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
  handovers: [],
};

/**
 * The signed-in player, as `GET /users/me` answers. Identity is filler; the nickname is not: it
 * is what every screen says about her, and its absence is where a launch is sent first.
 */
export const GATE_USER: Wire['MeResponse'] = {
  id: '11111111-2222-4333-8444-555555555555',
  email: 'ada@example.com',
  nickname: GATE_USER_NICKNAME,
  authority: 'player',
  is_admin: false,
  is_active: true,
  has_player_profile: false,
  created_at: '2026-08-13T10:00:00Z',
  adult_attested: true,
  profiles: PLAYER_ONLY,
};

/**
 * The gate's one read — who the player is, which is where the nickname and *does a Player
 * profile exist* are served from (#730) — and the two reads a level is asked from where play
 * begins: what this player is rated at, and what they left unfinished. Neither of those two
 * routes a launch any more; they are here because a group's tabs, the passport and the door
 * read them, and almost every suite reaches one.
 *
 * The unfinished-run read is **one** request covering every sport. An empty list is the
 * answer for a player with nothing outstanding — a 200, not a 204 and not a failure.
 *
 * **`stubGames`, `stubConversations` and `stubSportsmanship` are in here and none of them is a gate
 * read.** The gate's *app* destination is the shell's root, the shell's root is the Home tab, and
 * Home reads the rooms to say whether a booked game's chat is open; the games list and the stars
 * are read one push in, by a booked game's result screen, and every suite that opens one lands
 * through here first. All three are defaulted to nothing, and a suite with any of them calls the
 * stub again afterwards to replace it.
 *
 * **So is the Groups list** ([#512](https://github.com/Raketa02/Raketa/issues/512)): the Play tab
 * opens on Groups, so a suite that presses Play for any reason reads it.
 *
 * **So is the feature-flag datafile**, and for the same reason: the signed-in app fetches it the
 * moment it opens, whatever the suite is about (ADR-0206 §6). It is defaulted to **none**, which
 * is every feature flag at its code default — the app as it ships. A suite about a feature flag
 * calls `stubDatafile` again afterwards to serve one.
 *
 * **So is Home's booked-games read** (#556): the bar's Home badge is its count, so the shell makes it
 * the moment the tabs are up. Defaulted to no games.
 *
 */
export function stubGate(
  transport: Transport,
  {
    ratings = [],
    runs = [],
    hasPlayerProfile = false,
    id = GATE_USER.id,
    email = GATE_USER.email,
    nickname = GATE_USER.nickname ?? null,
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
      nickname,
      has_player_profile: hasPlayerProfile,
      adult_attested: profiles.acts_as_player,
      profiles,
    }),
  );

  stubRunsInProgress(transport, runs);
  stubGames(transport);
  stubConversations(transport);
  stubSportsmanship(transport);
  stubDatafile(transport);
  stubMyGroups(transport);
  stubHottestGroups(transport);
  stubNewInRakieta(transport);
  stubSameLevel(transport);
  stubSameVibe(transport);
  stubTopTen(transport);
  stubPaymentMethod(transport);
  stubGamesAndMoney(transport);
  stubLiveYeses(transport);
  stubPaymentsToConfirm(transport);
  stubReceipts(transport);
  stubHome(transport);
  stubNotificationChoices(transport);
  stubNotices(transport);
  // Opening the list behind the bell records the visit (#627).
  transport.on('POST', NOTICES_VISIT_PATH, () => noContent());
  // Needs your answer going for good records its visit (#819).
  transport.on('POST', NEEDS_YOUR_ANSWER_VISIT_PATH, () => noContent());
  stubBlockedPlayers(transport);
  stubFriends(transport);
}

export const FRIENDS_PATH = '/api/v1/friends';
export const FRIEND_REQUESTS_PATH = '/api/v1/friends/requests';
/** Your friend link — the Add friends sheet's card reads it (#756). */
export const FRIEND_LINK_PATH = '/api/v1/friends/link';

/**
 * **Your friends and the requests each way**, as `GET /friends` and `GET /friends/requests` answer
 * — **nobody** unless the suite says otherwise — and your friend link, `tk4m9q2z`. The gate
 * stubs them, because the You tab's *Friends* row reads your friends and *Asked you* on every
 * visit (#754). One responder answers both
 * directions, reading the one the request asked for.
 */
export function stubFriends(
  transport: Transport,
  {
    friends = [],
    askedYou = [],
    youAsked = [],
  }: {
    readonly friends?: readonly Wire['FriendSchema'][];
    readonly askedYou?: readonly Wire['FriendRequestSchema'][];
    readonly youAsked?: readonly Wire['FriendRequestSchema'][];
  } = {},
) {
  transport.on('GET', FRIENDS_PATH, () =>
    json<Wire['FriendsResponse']>({ sport: null, friends: [...friends] }),
  );
  // Your link, for a suite that opens the Add friends sheet without saying (#756).
  transport.on('GET', FRIEND_LINK_PATH, () =>
    json<Wire['FriendLinkResponse']>({ code: 'tk4m9q2z', link: 'https://raketa.app/f/tk4m9q2z' }),
  );
  transport.on('GET', FRIEND_REQUESTS_PATH, (request) => {
    const direction: Wire['Direction'] = request.path.includes('direction=YOU_ASKED')
      ? 'YOU_ASKED'
      : 'ASKED_YOU';
    return json<Wire['FriendRequestsResponse']>({
      direction,
      requests: [...(direction === 'ASKED_YOU' ? askedYou : youAsked)],
    });
  });
}

export const BLOCKED_PLAYERS_PATH = '/api/v1/blocks';

/**
 * *Blocked players*, as `GET /blocks` answers — **nobody** unless the suite says otherwise. The
 * gate stubs it, because the You tab's *Blocked players* row reads it on every visit (#587).
 */
export function stubBlockedPlayers(
  transport: Transport,
  players: readonly Wire['BlockedPlayerSchema'][] = [],
) {
  transport.on('GET', BLOCKED_PLAYERS_PATH, () =>
    json<Wire['BlockedPlayersResponse']>({ players: [...players] }),
  );
}

export const NOTIFICATION_CHOICES_PATH = '/api/v1/players/me/notifications';
export const NOTICES_PATH = '/api/v1/players/me/notices';
export const NOTICES_VISIT_PATH = '/api/v1/players/me/notices/visit';
export const DEVICES_PATH = '/api/v1/players/me/devices';
export const DEVICE_REMOVAL_PATH = '/api/v1/players/me/devices/removal';

/**
 * The three choices, as `GET /players/me/notifications` answers — **the backend's defaults**, *You
 * complete it* and *Challenges for you* on and *Fill in alerts* off, unless the suite says otherwise.
 * The gate stubs it, because the You tab's *Notifications* row reads it on every visit (#559).
 */
export function stubNotificationChoices(
  transport: Transport,
  choices: Partial<Wire['NotificationChoicesSchema']> = {},
) {
  transport.on('GET', NOTIFICATION_CHOICES_PATH, () =>
    json<Wire['NotificationChoicesSchema']>({
      you_complete_it: true,
      challenges_for_you: true,
      fill_in_alerts: false,
      ...choices,
    }),
  );
}

/**
 * The recent notices, as `GET /players/me/notices` answers — **none** unless the suite says
 * otherwise. The gate stubs it, because a push arriving re-reads the list wherever the player is
 * (#559); the query string is the transport's to drop. **The bell's number is the rows marked
 * `new`** unless the suite names one (#627) — the server's count is exact however few rows it
 * answers, so a suite drawing *99+* says so.
 */
export function stubNotices(
  transport: Transport,
  notices: readonly Wire['NoticeSchema'][] = [],
  { newCount }: { readonly newCount?: number } = {},
) {
  transport.on('GET', NOTICES_PATH, () =>
    json<Wire['RecentNoticesResponse']>({
      notices: [...notices],
      new_count: newCount ?? notices.filter((notice) => notice.new).length,
      last_opened_at: null,
    }),
  );
}

export const HOME_PATH = '/api/v1/home';

/** Needs your answer went for good — its visit, naming the watermark of the read it showed (#815). */
export const NEEDS_YOUR_ANSWER_VISIT_PATH = '/api/v1/players/me/needs-your-answer/visit';

/** One booked game's details — `GET /bookings/{id}` (#556). */
export const bookingPath = (bookingId: string) => `/api/v1/bookings/${bookingId}`;

/**
 * **Home's booked games** (#542, #556) — none by default, at a fixed read: the shell holds the read
 * all session for the bar's badge, so every suite that lands in the app makes it. A suite about
 * Home serves its own, and `test-support/home.ts` builds them.
 *
 * **Its *TO CONFIRM* rows are the payments to confirm'** unless the suite names them (#815, #819):
 * the server serves *the same rows as `GET /players/me/payments-to-confirm`* on Home's read, so a
 * suite that stubs that read — with `stubPaymentsToConfirm` or by hand — finds them in Needs your
 * answer too, read at the moment Home is. A refused or broken read of them is none. **Nothing is
 * new** (`needs_your_answer`) unless the suite says so, and the watermark is `null`: a suite about
 * the envelope's badge and its visit serves both.
 */
export function stubHome(transport: Transport, home: Partial<Wire['HomeResponse']> = {}) {
  transport.on('GET', HOME_PATH, () =>
    json<Wire['HomeResponse']>({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [],
      friend_requests: [],
      friends_games: [],
      level_asks: [],
      payments_to_confirm: paymentsToConfirmServed(transport),
      needs_your_answer: { new_count: 0, watermark: null },
      ...home,
    }),
  );
}

/**
 * What `GET /players/me/payments-to-confirm` answers right now — none when it refuses, fails or
 * never answers (`answerNow`). **Its responder runs once more for every Home read**, so a suite whose
 * payments responder counts its calls or steps through answers, or answers asynchronously, serves
 * Home's `payments_to_confirm` by name instead.
 */
export function paymentsToConfirmServed(
  transport: Transport,
): Wire['PaymentsToConfirmResponse']['payments'] {
  let answer: ReturnType<Transport['answerNow']>;
  try {
    answer = transport.answerNow('GET', PAYMENTS_TO_CONFIRM_PATH);
  } catch {
    return [];
  }
  if (answer === undefined) return [];
  if (answer instanceof Promise) {
    // A failure or a socket that never answers: nothing served, and nothing left unhandled.
    answer.catch(() => undefined);
    return [];
  }
  if (!answer.ok) return [];
  const served = servedBody(answer) as Wire['PaymentsToConfirmResponse'] | undefined;
  return served?.payments ?? [];
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
    json<Wire['LiveYesesResponse']>({ yeses: [...yeses] }),
  );
}

export const PAYMENTS_TO_CONFIRM_PATH = '/api/v1/players/me/payments-to-confirm';

/**
 * The refused shares waiting for the player, as `GET …/payments-to-confirm` answers — **none**
 * unless the suite says otherwise. The gate stubs it, because Payments' state B reads it (#555).
 */
export function stubPaymentsToConfirm(
  transport: Transport,
  payments: readonly Wire['app__modules__proposals__presentation__schemas__PaymentToConfirmSchema'][] = [],
) {
  transport.on('GET', PAYMENTS_TO_CONFIRM_PATH, () =>
    json<Wire['PaymentsToConfirmResponse']>({ payments: [...payments] }),
  );
}

export const RECEIPTS_PATH = '/api/v1/players/me/receipts';

/**
 * The receipts, as `GET …/receipts` answers — **none** unless the suite says otherwise. The gate
 * stubs it, because Payments' state B reads it whenever a method is saved (#555).
 */
export function stubReceipts(
  transport: Transport,
  receipts: readonly Wire['ReceiptSchema'][] = [],
) {
  transport.on('GET', RECEIPTS_PATH, () =>
    json<Wire['ReceiptsResponse']>({ receipts: [...receipts] }),
  );
}

/** The version of the payment terms the backend holds in force (#536; Q113's words since #637). */
export const PAYMENT_TERMS_IN_FORCE = '2026-10-10';

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

/** What a warmed launch hands back: the requests its warm-up sent before the tree existed. */
export interface WarmedLaunch {
  readonly early: readonly RecordedRequest[];
}

/**
 * **A cold launch with Home warmed while the splash played** (#874; ADR-0209 §2, amended 2026-11-24)
 * — the root layout's sequence from session restore on, against this harness's query client, before
 * the tree is rendered: the session restored as the launch restores it (its check sent, so the
 * account is cached), then **the very step the root layout starts**, the shell's `warmHome`.
 *
 * - **The warm-up hears the phone's reachability the suite says** — `reachable` unless it says
 *   otherwise — while the session check is always sent: a phone known to be offline skips the check
 *   too, and then there is no account to decide from, which would hide whether the warm-up's own rule
 *   holds.
 * - **It is awaited here**, which a launch never does: the harness mounts no splash, and every read
 *   landing before the tree is what a normal connection does under one.
 * - **`early` is every request the warm-up sent**, the account's own read excluded.
 */
export async function launchWarmed(
  transport: Transport,
  {
    initialUrl = '/',
    reachability = 'reachable',
  }: { readonly initialUrl?: string; readonly reachability?: Reachability } = {},
): Promise<WarmedLaunch> {
  await beginSession({ accessToken: 'access-1', refreshToken: 'refresh-1' });
  await restoreSession(
    () => fetchCurrentUserAtLaunch(queryClient),
    async () => 'reachable',
  );
  const from = transport.requests.length;
  await warmHome(queryClient, async () => reachability);
  const early = transport.requests.slice(from);
  renderRouter(ONBOARDING_ROUTES, { initialUrl });
  return { early };
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
 * harness takes a path, so `/join/<code>` stands for `rakieta://join/<code>`; the scheme's own
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
