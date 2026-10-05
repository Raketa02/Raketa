/**
 * The feature-flag feature's only public surface
 * ([ADR-0180](../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)).
 *
 * Three hooks and a name. `src/app/` and other features may import from here and from nowhere else
 * inside this folder — ESLint blocks the deep paths, and a second, narrower fence keeps the SDK
 * and AsyncStorage inside `api/`.
 */

/**
 * The feature keys, declared once beside their code defaults. A gate names one; a key the client
 * has not declared does not compile.
 */
export type { FeatureKey } from './domain/featureFlags';

/**
 * Keep the datafile current: at launch, and at every return to the foreground. The signed-in
 * app's layout calls it once, because that is the one site that knows the app is open.
 */
export { useFeatureDatafile } from './hooks/useFeatureDatafile';

/** A gate: whether a feature is enabled, read once, when the screen that asks mounts. */
export { useFeatureOnMount } from './hooks/useFeatureOnMount';

/**
 * A flag **followed**, for chrome mounted before any datafile is read and kept for the session —
 * the tab bar's Classic play columns (#550). A screen never uses it: a screen reads once.
 */
export { useFollowedFeature } from './hooks/useFollowedFeature';

/**
 * The feature's query keys — for the router harness alone, which waits on the datafile read
 * because nothing on screen can say it has landed (a gate reads once, and ignores what arrives
 * after). No screen or feature reads them.
 */
export { featureFlagKeys } from './hooks/featureFlagKeys';
