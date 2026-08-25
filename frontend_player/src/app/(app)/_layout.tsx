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
 * four destinations rather than two: an unfinished run resumes, no ratings goes to welcome,
 * a rating with no Player profile goes to the second part's first step, and only then does
 * a player reach the app ([ADR-0090](../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 *
 * None of it is part of `SessionStatus`: making "has a rating" a session state would block
 * every cold launch on a network request, which is the opposite of what the bootstrap
 * sequence exists to avoid.
 *
 * Where a player belongs is a rule, and it lives in the onboarding feature with its own
 * tests. This file only turns the decision into a route — which is the whole job of a
 * route file.
 */

import { Redirect, Stack } from 'expo-router';

import {
  EntryUnavailableScreen,
  useEndOnboardingPass,
  useEntryDecision,
} from '@/features/onboarding/types';
import { SOCIAL_STEPS_ENTRY } from '@/features/player_profile/types';
import { useSessionStatus } from '@/shared/lib/auth';

export default function AppLayout() {
  const status = useSessionStatus();
  const entry = useEntryDecision();

  // A walk through onboarding is over when the player is in the app. Declared here because
  // this is the branch that knows it — one site, and the definition rather than a line
  // someone has to remember on each of the several ways out of the flow. Called before the
  // returns below, because a hook may not be conditional.
  useEndOnboardingPass(entry.kind === 'app');

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
      return <EntryUnavailableScreen error={entry.error} onRetry={entry.retry} />;
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
      return <Stack screenOptions={{ headerShown: false }} />;
  }
}
