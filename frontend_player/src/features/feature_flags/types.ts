/**
 * The feature-flag feature's only public surface
 * ([ADR-0206](../../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)).
 *
 * Two hooks, a name and the query keys. `src/app/` and other features may import from here and
 * from nowhere else inside this folder — ESLint blocks the deep paths, and a second, narrower fence
 * keeps the SDK and AsyncStorage inside `api/`.
 *
 * **One gate reads it today**: Play, on `explore` (#826). `useFollowedFeature`, which followed a
 * feature flag for the tab bar, left with the Classic play columns it served (#576) and did not
 * come back — a screen reads once, when it mounts.
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
 * The feature's query keys — for the router harness alone, which waits on the datafile read
 * because nothing on screen can say it has landed (a gate reads once, and ignores what arrives
 * after). No screen or feature reads them.
 */
export { featureFlagKeys } from './hooks/featureFlagKeys';
