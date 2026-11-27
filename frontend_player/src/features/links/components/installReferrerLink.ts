/**
 * **The link an Android install carried, read once on the app's first launch**
 * ([#756](https://github.com/Raketa02/Raketa/issues/756), the friends mechanics §4.3).
 *
 * Zofia has no Rakieta, opens Tomek's friend link, and installs from the public site's Google Play
 * button, which carries the page's own link as the **install referrer** (#755). Opening the app
 * for the first time reads it, and **a group link or a friend link in it is held exactly as if she
 * had tapped it** — through sign-up and onboarding, then answered in the player's app: Join a group,
 * or Tomek's request on Home. An iPhone has no referrer, and is unchanged.
 *
 * Not a component, for `redirectSystemPath`'s reason: it runs before any screen exists, as a step of
 * the launch the root layout supplies (`bootstrapApp`), and **it does not hold the splash** — Play's
 * service is another app's, and the link is held whenever it answers. It is the adapter between the
 * launch and the feature, as that one is between expo-router and it.
 *
 * - **Once, on the first launch, ever** (`installReferrerRead`, a flag the phone keeps for itself):
 *   Play keeps a referrer for 90 days, and a link tapped last week is not an instruction today. The
 *   flag is raised once Play has answered, whatever it said.
 * - **Never in place of a newer link** (`receiveReferrer`): one the phone opened the app with, or
 *   opened while Play was being asked, is what the person tapped now.
 * - **It never throws**: whatever goes wrong is no link, and a launch step that threw would stop the
 *   app on its startup screen for a link nobody tapped.
 */

import { deviceInstallReferrer, type InstallReferrerPort } from '@/shared/lib/platform';
import { raisePhoneWideFlag, readPhoneWideFlag } from '@/shared/lib/preferences';

import { holdLink, linkHeldNow } from '../hooks/heldLink';
import { receiveReferrer } from '../use-cases/receiveReferrer';

export async function readTheInstallReferrerOnce(
  installReferrer: InstallReferrerPort = deviceInstallReferrer,
): Promise<void> {
  try {
    if (await readPhoneWideFlag('installReferrerRead')) return;

    const referrer = await installReferrer.readReferrer();
    await raisePhoneWideFlag('installReferrerRead');

    const link = receiveReferrer(referrer, linkHeldNow());
    if (link !== undefined) holdLink(link);
  } catch {
    // No link. The app opens as it would have.
  }
}
