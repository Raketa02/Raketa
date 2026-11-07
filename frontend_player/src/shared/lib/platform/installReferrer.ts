/**
 * The install referrer, behind a port. **The only module that imports `expo-application`**
 * ([#756](https://github.com/Raketa02/Raketa/issues/756), the friends mechanics §4.3).
 *
 * Somebody without the app opens a friend link or a group link, lands on the public site's page, and
 * installs from its Google Play button — which carries the page's own link as the **install
 * referrer** (#755). Google Play keeps it for 90 days and hands it to the app through its Install
 * Referrer service, which `expo-application` reads. **An iPhone has no such thing**: its install
 * forgets the link, and the person taps the site's *Open in Raketa* once more. So the platform's
 * difference stays here, as push's does, and the port answers `null` there.
 *
 * It is a port and not a line in the links feature on the other ports' argument: a native module has
 * no JS implementation underneath it, and *read once, on first launch* is a rule a fake can count.
 *
 * **It never rejects.** Play not answering — no Play Store, a service that is down, an install that
 * did not come from Play — is no referrer, which is what the app does with a referrer that is no
 * link anyway. The fake in `src/test-support/platform.ts` keeps the same promise.
 */

import * as Application from 'expo-application';
import { Platform } from 'react-native';

/**
 * What the app may ask of the install referrer.
 *
 * The links feature depends on this interface; `deviceInstallReferrer` is the one implementation
 * that talks to the OS, and a test substitutes `fakeInstallReferrer()` from
 * `src/test-support/platform.ts`.
 */
export interface InstallReferrerPort {
  /**
   * The text Google Play kept from the store page that installed the app — anybody's text, read by
   * the caller as such — or `null`: on an iPhone, and whenever there is none to read.
   */
  readonly readReferrer: () => Promise<string | null>;
}

export const deviceInstallReferrer: InstallReferrerPort = {
  async readReferrer() {
    if (Platform.OS !== 'android') return null;
    try {
      const referrer = await Application.getInstallReferrerAsync();
      return referrer === '' ? null : referrer;
    } catch {
      return null;
    }
  },
};
