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
 * The second redirect is onboarding's, and onboarding is **two parts** — so the gate has
 * five destinations rather than two: an unnamed account goes to the naming step before
 * anything else ([ADR-0171](../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §3), an unfinished run resumes, no ratings goes to welcome, a rating with no Player profile
 * goes to the second part's first step, and only then does a player reach the app
 * ([ADR-0090](../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 *
 * None of it is part of `SessionStatus`: making "has a rating" a session state would block
 * every cold launch on a network request, which is the opposite of what the bootstrap
 * sequence exists to avoid.
 *
 * Where a player belongs is a rule, and it lives in the onboarding feature with its own
 * tests. This file only turns the decision into a route — which is the whole job of a
 * route file.
 *
 * ## An account that only runs a club's groups is sent to its area
 *
 * The gate reads the account's **profiles** ahead of all five destinations
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
 * ## A pass that began at the passport ends on it
 *
 * The gate's app branch is where every onboarding pass ends, and a pass has an origin
 * ([ADR-0179](../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §3): one begun at the Skill passport's *Add a sport* enters the app the way every pass
 * does — *See your ratings*, *continue later* and *abandon* all replace to `/` — and it is
 * this file, told the origin as the pass ends, that lays the You tab down and pushes the
 * passport over it. The shell's own move, as the yes screen lands a room: the tab beneath,
 * so *back* from the passport goes where it came from. Which route the passport is belongs to
 * the feature that owns the screen, not to this file — the same seam `NAMING_STEP` and
 * `SOCIAL_STEPS_ENTRY` cross.
 */

import { Redirect, Stack, router, usePathname } from 'expo-router';
import { useCallback } from 'react';

import { administratorHome, InvitationSheet } from '@/features/administrator/types';
import { NAMING_STEP, PLAYER_PROFILE, START_PLAYING_STEP } from '@/features/auth/types';
import { useFeatureDatafile } from '@/features/feature_flags/types';
import {
  EntryUnavailableScreen,
  useEndOnboardingPass,
  useEntryDecision,
  type PassOrigin,
} from '@/features/onboarding/types';
import { YOU_PASSPORT_ROUTE } from '@/features/player_record/types';
import { SOCIAL_STEPS_ENTRY, useLocationRefresh } from '@/features/player_profile/types';
import { openTab } from '@/features/shell/types';
import { useSessionStatus } from '@/shared/lib/auth';

export default function AppLayout() {
  const status = useSessionStatus();
  const entry = useEntryDecision();
  const pathname = usePathname();

  // Where a pass that has just ended lands, by where it began. A welcome pass is already
  // where the gate put it; a passport pass goes back to the passport, with the You tab laid
  // down beneath it.
  const land = useCallback(
    (origin: PassOrigin) => {
      if (origin !== 'passport') return;
      openTab('you', pathname);
      router.push(YOU_PASSPORT_ROUTE);
    },
    [pathname],
  );

  // A walk through onboarding is over when the player is in the app. Declared here because
  // this is the branch that knows it — one site, and the definition rather than a line
  // someone has to remember on each of the several ways out of the flow. Called before the
  // returns below, because a hook may not be conditional.
  useEndOnboardingPass(entry.kind === 'app', land);
  // And the location moves on a cold start, for the same branch and the same reason: this is
  // the one site that knows a player is signed in and past onboarding. The feature owns what
  // happens; this file owns the moment (ADR-0174 §6).
  useLocationRefresh(entry.kind === 'app');
  // And the feature flags are fetched, for the same branch: only a player in the app can reach a
  // gated screen, and this is the site that knows one is. From here on the datafile is fetched
  // again at every return to the foreground; nothing waits for it (ADR-0180 §6).
  useFeatureDatafile(entry.kind === 'app');

  // Can't happen in practice — `BootstrapGate` renders nothing until the sequence
  // resolves, so no route tree exists while the status is still `bootstrapping`. It is
  // handled anyway because the alternative is falling through to the redirect, which
  // would turn any future change to the gate into a login-screen flash.
  if (status === 'bootstrapping') return null;

  if (status === 'unauthenticated') return <Redirect href="/sign-in" />;

  switch (entry.kind) {
    case 'pending':
      // Nothing, not a spinner: the same rule as bootstrap. A route tree rendered before
      // the gate resolves is the authenticated-tree flash, one frame before a redirect.
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
      // Before anything else: every destination after this one says the player's name. Which
      // route that is belongs to the feature that owns the naming, not to this file.
      return <Redirect href={NAMING_STEP} />;
    case 'welcome':
      return <Redirect href="/welcome" />;
    case 'social-steps':
      // The first step, always — never the one they were on when they closed the app. The
      // draft is client-held and starts empty, so the middle of the part is not a place a
      // player can be resumed to. Which route that is belongs to the feature that owns the
      // part, not to this file.
      return <Redirect href={SOCIAL_STEPS_ENTRY} />;
    case 'resume':
      return (
        <Redirect
          href={{
            pathname: '/question/[assessmentId]',
            params: { assessmentId: entry.run.assessmentId, sport: entry.run.sport },
          }}
        />
      );
    case 'app':
      return (
        <>
          <Stack screenOptions={{ headerShown: false }} />
          {/* A club's invitation, offered on launch over the player's app and never inside
              onboarding: it waits until the account is in (#518). */}
          <InvitationSheet worn={PLAYER_PROFILE} />
        </>
      );
  }
}
