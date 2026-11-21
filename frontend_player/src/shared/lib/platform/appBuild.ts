/**
 * **Which build this is, on which platform** — the two facts about the device a feature flag's
 * rules may be written against
 * ([ADR-0206](../../../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)
 * §8: `platform` and `appVersion`).
 *
 * Here rather than in the flag feature for Part 13's reason — what the app knows about the device
 * it is running on lives in one directory — and like `appSettings` it is a *reading* rather than a
 * port: there is nothing to decide and nothing a test would want to drive differently.
 *
 * Each is absent when the build cannot say. A platform that is neither of the two this app ships
 * on, or a manifest with no version, is not guessed at: a rule that targets it then does not
 * match, which is the honest answer for a device that did not identify itself.
 */

import Constants from 'expo-constants';
import { Platform } from 'react-native';

export interface AppBuild {
  readonly platform?: 'ios' | 'android';
  /** The app's own version from `app.config.ts` — the one a store listing shows. Semver. */
  readonly appVersion?: string;
}

export function appBuild(): AppBuild {
  const platform = Platform.OS === 'ios' || Platform.OS === 'android' ? Platform.OS : undefined;
  const appVersion = Constants.expoConfig?.version;

  return {
    ...(platform === undefined ? {} : { platform }),
    ...(appVersion === undefined ? {} : { appVersion }),
  };
}
