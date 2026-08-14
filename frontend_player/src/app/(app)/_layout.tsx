/**
 * Two boundaries, in order: is there a session, and does this player have a rating yet.
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
 * The second redirect is onboarding's. It is **not** part of `SessionStatus`: making "has
 * a rating" a session state would block every cold launch on a network request, which is
 * the opposite of what the bootstrap sequence exists to avoid.
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
