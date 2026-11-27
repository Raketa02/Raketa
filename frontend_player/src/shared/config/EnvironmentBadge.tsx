/**
 * The badge that says which environment the running app is pointed at — or nothing at
 * all, in production.
 *
 * It lives beside `appIdentity.ts` rather than in `shared/ui/`, the same way
 * `LaunchGate` lives beside the sequence it runs: `shared/ui/` holds design-system
 * primitives, and a component that knows what an environment is is not one. It *draws*
 * with a primitive — `Tag`, the status pill — so there is no second implementation of a
 * pill in the app.
 *
 * **The environment defaults to the validated config and is overridable**, and the
 * default is written in the signature rather than at the call site on purpose. The
 * composition root's JSX is *created* while the app is still bootstrapping — the gate has
 * not resolved, so `loadEnv()` has not run — and `<EnvironmentBadge environment={getEnv()
 * .environment} />` would therefore evaluate `getEnv()` one render too early and throw on
 * the first frame. A default parameter is evaluated when the component runs, which is
 * only ever behind the gate. So the ordering bug is unwritable rather than avoided.
 *
 * The override is what lets a test render all four environments without mocking the
 * resolver or defeating its memoization.
 *
 * The overlay never intercepts a touch (`pointerEvents="none"`), because a developer
 * aid that eats a tap in the corner of every screen is worse than no aid.
 */

import { StyleSheet, View } from 'react-native';

import { Tag } from '@/shared/ui/Tag';
import { theme } from '@/shared/ui/theme';

import { appIdentity } from './appIdentity';
import { getEnv, type AppEnvironment } from './env';

export interface EnvironmentBadgeProps {
  /** Defaults to the validated config. Set it only in a test. */
  readonly environment?: AppEnvironment;
}

export function EnvironmentBadge({
  environment = getEnv().environment,
}: EnvironmentBadgeProps = {}) {
  const { badge } = appIdentity(environment);

  // Production is unbadged, and renders nothing rather than an invisible view: an empty
  // absolutely-positioned overlay is still a node in the tree of every screen.
  if (badge === null) return null;

  return (
    <View style={s.anchor} pointerEvents="none" testID="environment-badge">
      {/*
       * `warn` — amber, which this design system reads as *reversible*. The badge is not
       * an error and not a settled state; it says the thing in front of you is not the
       * real one. Deliberately NOT hidden from a screen reader: this never reaches a
       * player, and a developer using VoiceOver needs the same fact a sighted one gets.
       */}
      <Tag label={badge} variant="warn" accessibilityLabel={`Environment: ${environment}`} />
    </View>
  );
}

const s = StyleSheet.create({
  anchor: {
    position: 'absolute',
    right: theme.space.xs,
    bottom: theme.space.xs,
  },
});
