/**
 * Two boundaries, in order: is there a session, and is onboarding behind this player yet.
 *
 * Expo Router's declarative protected routes landed **after** SDK 52, so until this app
 * moves past it the guard is a redirect keyed on `SessionStatus` — never on
 * `user === undefined`, which conflates "still loading" with "logged out" and produces
 * the login-screen flash. See docs/architecture.md Part 2.
 *
 * The route group is the point: the boundary is visible in the file tree, so a screen
 * added under `(app)/` is guarded by where it was put rather than by remembering to
 * guard it.
 *
 * ## The entry gate
 *
 * The second redirect is onboarding's, and **onboarding is a nickname and a profile**
 * ([ADR-0200](../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §1) — so the gate
 * has three destinations rather than two: an account with no nickname goes to the naming step
 * before anything else ([ADR-0199](../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md)
 * §3), one with no Player profile goes to the profile steps from their first
 * ([ADR-0090](../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)), and only then does a
 * player reach the app. **A rating and an unfinished run route nowhere** (#730): a level is asked
 * where play begins, by a door on a group's tabs, and a run left halfway is offered there as
 * *Carry on* — never forced on a launch.
 *
 * None of it is part of `SessionStatus`: making "has a Player profile" a session state would
 * block every cold launch on a network request, which is the opposite of what the bootstrap
 * sequence exists to avoid.
 *
 * Where a player belongs is a rule, and it lives in the onboarding feature with its own
 * tests. This file only turns the decision into a route — which is the whole job of a
 * route file.
 *
 * ## An account that only runs a club's groups is sent to its area
 *
 * The gate reads the account's **profiles** ahead of all three destinations
 * ([ADR-0185](../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §3): an account that holds nothing but administrator profiles has not asked to play, so it is
 * redirected to its **administrator area** — a sibling group, `(administrator)`, with its own two
 * tabs — and never into onboarding. Which route that is belongs to the feature that owns the area.
 * An account that holds **no profile at all** is offered *Start playing* from its first step, the
 * Adult attestation, which the naming and the player setup follow through this gate.
 *
 * ## Two profiles, and an invitation to a third
 *
 * An account that holds both opens in **the profile the phone remembers** — Player by default — and
 * the gate's decision already reads it (ADR-0185 §3, ADR-0188 §2). And a club's **invitation** is
 * offered here, as a sheet over the player's app, the moment the account is in it (#518) — the
 * administrator area offers it over its own screens the same way.
 *
 * ## A link is answered once the account is in
 *
 * A link opened on the phone — a group link out of WhatsApp, an invitation's or a reset's button — is
 * **held** from the moment it arrives, through sign-in, sign-up and every destination above, and
 * answered here, where the account is in the player's app
 * ([#520](https://github.com/Rakieta02/Rakieta/issues/520)): Join a group with the link filled in, or a
 * sheet over the app. What each gets is the links feature's; this file only mounts the place.
 *
 * ## A pass ends where it began
 *
 * The gate's app branch is where every rating pass ends, and a pass has an origin
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3, amended by ADR-0200 §5): one begun on Home ends there, which is where `/` opens; one begun
 * at the Skill passport's *Add a sport* enters the app the way every pass does — *See your
 * ratings*, *continue later* and *abandon* all replace to `/` — and it is this file, told the
 * origin as the pass ends, that lays the You tab down and pushes the passport over it. The
 * shell's own move: the tab beneath, so *back* from the passport goes where it came from. Which
 * route the passport is belongs to the feature that owns the screen, not to this file — the same
 * seam `NAMING_STEP` and `SOCIAL_STEPS_ENTRY` cross.
 *
 * **A pass begun on Rankings' *Get your {sport} level* ends on Rankings** (#775), on that sport, with
 * Home laid down beneath it — the route the rankings feature names.
 *
 * **A pass that began on a group ends on it** ([ADR-0200](../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §5, #729) the same way: Play laid down, and the group's page over it on the tab the pass
 * began on, standing on the sport it rated last — the route the groups feature names.
 *
 * **Nothing of the app is drawn until it has landed.** The app's tree comes back at `/`, which is
 * Home, and a landing made after Home was drawn showed it for a frame and then slid the group in
 * over it — a blink on a device. So while a landing is due this file draws nothing, the landing is
 * made before the first frame, and it is one reset with the whole stack in it (`shell`'s
 * `useShellLanding`): the app's first frame is the group, or the passport, with its tab beneath.
 *
 * **A pass that rated a sport also re-reads Home and the bell** (#765), by whichever door it was
 * begun: a friend's ask for a level in that sport has ended on the server, and its Home card is
 * dropped before the shell is drawn (`shell`'s `useRereadAfterALevel`).
 */

import { Redirect, Stack } from 'expo-router';
import { useCallback } from 'react';

import { administratorHome, HandoverSheet, InvitationSheet } from '@/features/administrator/types';
import { NAMING_STEP, PLAYER_PROFILE, START_PLAYING_STEP } from '@/features/auth/types';
import { useFeatureDatafile } from '@/features/feature_flags/types';
import { groupReturnRoute } from '@/features/groups/types';
import {
  EntryUnavailableScreen,
  useEndOnboardingPass,
  useEntryDecision,
  type PassReturn,
} from '@/features/onboarding/types';
import { YOU_PASSPORT_ROUTE } from '@/features/player_record/types';
import { IncomingLinks } from '@/features/links/types';
import { SOCIAL_STEPS_ENTRY, useLocationRefresh } from '@/features/player_profile/types';
import { rankingsRoute } from '@/features/rankings/types';
import { useRereadAfterALevel, useShellLanding } from '@/features/shell/types';
import { useSessionStatus } from '@/shared/lib/auth';
import { useSplashHold } from '@/shared/lib/bootstrap';

export default function AppLayout() {
  const status = useSessionStatus();
  const entry = useEntryDecision();
  const landInTheApp = useShellLanding();
  // What a level got changes outside the questionnaire — Home's ask card for its sport, and the
  // bell (#765) — told here because every pass ends here, whichever door began it.
  const afterALevel = useRereadAfterALevel();

  // Where a pass that has just ended lands, by where it began. A Home pass is already where
  // `/` opens, and is never handed here; a passport pass goes back to the passport,
  // with the You tab laid down beneath it; a group's goes back to the group, on the tab it began
  // on and the sport it rated last, with Play beneath it; Rankings' *Get your {sport} level* goes
  // back to Rankings on that sport, with Home beneath it (#775).
  const land = useCallback(
    (back: PassReturn) => {
      switch (back.kind) {
        case 'passport':
          landInTheApp('you', { pathname: YOU_PASSPORT_ROUTE });
          return;
        case 'rankings':
          landInTheApp('home', rankingsRoute(back.sport));
          return;
        case 'group':
          landInTheApp('play', groupReturnRoute(back.groupId, back.tab, back.sport));
          return;
      }
    },
    [landInTheApp],
  );

  // A rating pass is over when the player is in the app. Declared here because
  // this is the branch that knows it — one site, and the definition rather than a line
  // someone has to remember on each of the several ways out of the flow. Called before the
  // returns below, because a hook may not be conditional.
  const landingDue = useEndOnboardingPass(entry.kind === 'app', land, afterALevel);
  // And the location moves on a cold start, for the same branch and the same reason: this is
  // the one site that knows a player is signed in and past onboarding. The feature owns what
  // happens; this file owns the moment (ADR-0174 §6).
  useLocationRefresh(entry.kind === 'app');
  // And the feature flags' datafile is read, for the same branch: only a player in the app can
  // reach a gated screen, and this is the site that knows one is. From here on it is fetched again
  // at every return to the foreground; nothing waits for it (ADR-0206 §6).
  useFeatureDatafile(entry.kind === 'app');
  // **The splash waits while the gate is still asking** (ADR-0209 §3): *pending* draws nothing, and
  // a cold launch's drawn splash fading into it would be the blank frame the brief forbids. Any
  // answer lets go — a destination, or either screen saying the gate could not be read. Only an
  // authenticated launch asks; a signed-out one is redirected and holds nothing.
  useSplashHold(status === 'authenticated' && entry.kind === 'pending');

  // Can't happen in practice — the launch gate mounts no route tree until the sequence
  // resolves, so none exists while the status is still `bootstrapping`. It is
  // handled anyway because the alternative is falling through to the redirect, which
  // would turn any future change to the gate into a login-screen flash.
  if (status === 'bootstrapping') return null;

  if (status === 'unauthenticated') return <Redirect href="/sign-in" />;

  switch (entry.kind) {
    case 'pending':
      // Nothing, not a spinner: the same rule as bootstrap. A route tree rendered before
      // the gate resolves is the authenticated-tree flash, one frame before a redirect. On a
      // cold launch the splash is still up over it, held by the line above.
      return null;
    case 'unavailable':
      return <EntryUnavailableScreen reason={entry.reason} onRetry={entry.retry} />;
    case 'administrator':
      // Ahead of everything a player is asked: this account runs a club's groups and has not asked
      // to play (ADR-0185 §3).
      return <Redirect href={administratorHome(entry.clubId)} />;
    case 'start-playing':
      // An account that holds no profile at all — an administrator-only account its club removed —
      // takes Start playing's steps from here, the Adult attestation first (ADR-0185 §3).
      return <Redirect href={START_PLAYING_STEP} />;
    case 'naming':
      // Before anything else: every destination after this one says the player's nickname.
      // Which route that is belongs to the feature that owns the naming, not to this file.
      return <Redirect href={NAMING_STEP} />;
    case 'social-steps':
      // The first step, always — never the one they were on when they closed the app. The
      // draft is client-held and starts empty, so the middle of the steps is not a place a
      // player can be resumed to. Which route that is belongs to the feature that owns the
      // steps, not to this file.
      return <Redirect href={SOCIAL_STEPS_ENTRY} />;
    case 'app':
      // Nothing until a pass coming back has landed — made before the first frame, so this draws
      // no frame of its own: the app's first is the screen the pass returns to.
      if (landingDue) return null;
      return (
        <>
          <Stack screenOptions={{ headerShown: false }} />
          {/* A club's invitation, offered on launch over the player's app and never inside
              onboarding: it waits until the account is in (#518). */}
          <InvitationSheet worn={PLAYER_PROFILE} />
          {/* A club handing this account a group, told over the player's app too (ADR-0192). */}
          <HandoverSheet worn={PLAYER_PROFILE} />
          {/* A link held since it arrived — a group link through sign-up and onboarding, an
              invitation through a sign-in — is answered here once the account is in (#520). */}
          <IncomingLinks over="player" />
        </>
      );
  }
}
