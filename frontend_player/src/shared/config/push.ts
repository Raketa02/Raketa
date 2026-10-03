/**
 * **Push, switched on per platform by what exists — and nothing exists yet** (#559; the screens A9;
 * open items O6, O7 and #533's accounts).
 *
 * Two values, each read in two places that must agree, `applePay.ts`'s shape and for its reason:
 *
 * - **`EXPO_PROJECT_ID`** — the Expo project a phone's push token is minted for. Expo's push service
 *   addresses a phone by a token it issues per project, so without a project there is no token to
 *   ask for: `shared/lib/platform/push.ts` answers *no token* and the phone registers nothing.
 *   `app.config.ts` hands it to the build as `extra.eas.projectId`, where Expo's own tooling looks.
 *   #533 creates the project (and gives it Android's FCM key); its id goes here.
 * - **`IPHONE_PUSH`** — whether an iPhone build carries the push entitlement. Apple's push service
 *   needs the Apple Developer membership (O6), and **a personal team cannot sign the entitlement at
 *   all** — a development build of this app on a real iPhone would stop building the moment
 *   `expo-notifications` added it, which its config plugin does on its own. So `app.config.ts` takes
 *   it back out while this is false (`plugins/push.ts`), and an iPhone asks for no
 *   token. The permission is still asked and the list is still read: only the push is missing.
 *
 * **This module imports nothing**, for `appIdentity.ts`'s reason: Node loads it while Expo evaluates
 * `app.config.ts`, before Metro exists.
 */

export const EXPO_PROJECT_ID: string | null = null;

export const IPHONE_PUSH = false;

/** What `app.config.ts` spreads into `extra` — the project where Expo looks for it, or nothing. */
export const PUSH_PROJECT: { readonly eas?: { readonly projectId: string } } =
  EXPO_PROJECT_ID === null ? {} : { eas: { projectId: EXPO_PROJECT_ID } };
