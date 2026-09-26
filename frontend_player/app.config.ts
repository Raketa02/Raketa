/**
 * The native configuration document — a **function of the environment**, not a static
 * file. Replaces the `app.json` that used to sit here.
 *
 * Expo evaluates this in Node, before Metro exists, after it has loaded `.env*`. So the
 * environment is read straight off `process.env` — `src/shared/config/env.ts` is the
 * *runtime* resolver and cannot help here, and reaching for it would drag zod and Babel's
 * `EXPO_PUBLIC_*` substitution into a document that runs before either.
 *
 * **It contains no logic.** The two decisions — what the app is called and whether it is
 * badged, and which web domain's links are the app's — live in `src/shared/config/appIdentity.ts`
 * and `src/shared/config/appLinks.ts`, where they are pure and unit-tested without booting
 * anything. This file is a caller.
 *
 * **One installable variant.** One `bundleIdentifier`, one `package`, one `scheme`, and no
 * build-profile configuration: per-environment identifiers wait until a second backend
 * exists to point them at. What changes with the environment is the *name* and the badge.
 *
 * A missing or misspelled `EXPO_PUBLIC_ENV` refuses here rather than resolving to a
 * default, for the same reason the runtime refuses it: the wrong default is the one that
 * looks right. `expo start` stops with the variable's name; the value is never echoed,
 * because a config failure lands in logs and CI output.
 */

import type { ExpoConfig } from 'expo/config';

// Expo transpiles THIS file and then `require`s the result as CommonJS — so a relative
// `./src/…` import is resolved by plain Node, which cannot load a `.ts` file. Measured,
// not assumed: without this line `npx expo config` fails with
// `Cannot find module './src/shared/config/appIdentity'`. The hook is sucrase's, which is
// the transpiler `@expo/config` used on this file one line earlier — it is present
// exactly when this document is evaluated at all, and `.npmrc`'s `node-linker=hoisted`
// is what makes it resolvable by name from here.
import 'sucrase/register/ts';

import {
  appIdentity,
  isAppEnvironment,
  IDENTIFIED_ENVIRONMENTS,
} from './src/shared/config/appIdentity';
import { APP_SCHEME, nativeLinkConfig, readLinkDomain } from './src/shared/config/appLinks';

export default (): ExpoConfig => {
  const environment = process.env.EXPO_PUBLIC_ENV;

  if (!isAppEnvironment(environment)) {
    throw new Error(
      `EXPO_PUBLIC_ENV must be one of ${IDENTIFIED_ENVIRONMENTS.join(', ')}. ` +
        'Copy .env.example to .env.local and set it.',
    );
  }

  // The web domain's links — iOS's associated domain, Android's verified intent filter — and none
  // while the setting is empty, which is every environment today (#520). A malformed value refuses
  // here, naming the variable, for the reason the environment's does.
  const links = nativeLinkConfig(readLinkDomain(process.env.EXPO_PUBLIC_LINK_DOMAIN));

  return {
    name: appIdentity(environment).displayName,
    slug: 'raketa-player',
    version: '0.1.0',
    orientation: 'portrait',
    // One scheme, at every environment. A per-environment scheme would need
    // per-environment identifiers to be installable side by side, and those are deferred.
    scheme: APP_SCHEME,
    userInterfaceStyle: 'automatic',
    newArchEnabled: true,
    ios: {
      supportsTablet: true,
      bundleIdentifier: 'com.raketa.player',
      ...links.ios,
    },
    android: {
      package: 'com.raketa.player',
      adaptiveIcon: {
        backgroundColor: '#ffffff',
      },
      ...links.android,
    },
    plugins: [
      'expo-router',
      'expo-secure-store',
      [
        'expo-location',
        {
          // The one sentence the OS shows above the prompt. It says what is taken —
          // one position — and what for, because a player who cannot tell why is a
          // player who says no. Both background flags are spelled out although both
          // are already the default: a background location is a movement trail, which
          // is a different privacy class from the one this asks about, and a default
          // is a thing somebody flips without noticing.
          locationWhenInUsePermission:
            'Raketa uses your location once, to set the area you play in.',
          isIosBackgroundLocationEnabled: false,
          isAndroidBackgroundLocationEnabled: false,
          isAndroidForegroundServiceEnabled: false,
        },
      ],
      [
        'expo-image-picker',
        {
          photosPermission:
            'Raketa uses your photos so you can put a picture of yourself on your profile.',
        },
      ],
    ],
    experiments: {
      typedRoutes: true,
    },
    extra: {
      '//':
        'Non-secret config surfaced via expo-constants. Anything in the shipped bundle is ' +
        'PUBLIC — never put a secret here. See CLAUDE.md Safety. Runtime config lives in ' +
        'EXPO_PUBLIC_* and is validated by src/shared/config/env.ts; do not add a second ' +
        'copy of a value here — including the environment name, which the badge reads from ' +
        'the validated config rather than from a mirror that can drift.',
    },
  };
};
