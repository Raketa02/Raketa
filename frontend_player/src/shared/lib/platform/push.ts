/**
 * The phone's push notifications, behind a port. **The only module that imports
 * `expo-notifications`** ([#559](https://github.com/Raketa02/Raketa/issues/559); the screens A7.2,
 * A9; the mechanics §17.2).
 *
 * A notice reaches a phone through Expo's push service, which addresses the phone by a **token** it
 * mints — and the token, the permission to show anything, a push arriving while the app is open and
 * the player tapping one are all native. A screen that imported the library would be a screen no
 * suite could put in front of a refusal or a tap, so this is a port like the seven beside it, with a
 * fake in `src/test-support/platform.ts`.
 *
 * ## Six verbs
 *
 * - **`getPermission` / `requestPermission`** — the platform's permission vocabulary, as location
 *   speaks it. Android 13 and up asks through a notification channel, so the channel is made before
 *   the question.
 * - **`readToken`** — this phone's Expo push token, or `null` when it has none to give: no Expo
 *   project yet, an iPhone build without the push entitlement (`shared/config/push.ts`), a phone
 *   Expo could not be reached from, a simulator. One `null` for all of them, because to a caller
 *   they are one fact — *this phone cannot be pushed to now* — and a token is read again on the
 *   next foreground anyway. **It never rejects, and it is bounded**: minting one asks Expo's
 *   servers, so an answer that has not come within the app's request timeout is `null` — the
 *   sign-out waits on it, and a train is no reason to be held in an account. **A token minted is
 *   kept for the process**, until the system says it changed.
 * - **`onTokenChange`** — the system handed the phone a new token; read it again and register it.
 * - **`onNotice`** — a push arrived **while the app is open**. The system draws nothing then — no
 *   foreground handler is set, and a notification nobody handles in the foreground is not
 *   presented — so the app draws its own banner (the screens A9's *in-app banner*).
 * - **`onOpen`** — the player opened the app **by tapping a push**, whether it was running, in the
 *   background, or not running at all. The cold start's tap is read once, when the first listener
 *   subscribes, and every tap is handed over once whichever way it arrived.
 *
 * What a push carries is handed up **as it came**: `data` is untrusted input, and the feature that
 * reads it checks it with Zod before anything is opened (`docs/architecture.md` Part 13).
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import { EXPO_PROJECT_ID, IPHONE_PUSH } from '@/shared/config/push';
import { TIMEOUT_MS } from '@/shared/lib/http';

import { permissionStateOf, type PermissionState } from './permission';

/** A push the phone received while the app was open — its words, and what it carried. */
export interface PushNotice {
  readonly title: string;
  readonly body: string;
  /** What the push carried, unread. The caller validates it. */
  readonly data: unknown;
}

export interface PushPort {
  /** The current permission, without prompting anybody. */
  readonly getPermission: () => Promise<PermissionState>;
  /** Ask the player. A `blocked` permission answers `blocked` at once, as the OS does. */
  readonly requestPermission: () => Promise<PermissionState>;
  /** This phone's push token, or `null` when it has none to give — see the module note. */
  readonly readToken: () => Promise<string | null>;
  /** Called when the system replaces the phone's token. Answers the unsubscribe. */
  readonly onTokenChange: (listener: () => void) => () => void;
  /** Called with every push that arrives while the app is open. Answers the unsubscribe. */
  readonly onNotice: (listener: (notice: PushNotice) => void) => () => void;
  /** Called with what a tapped push carried — once per tap. Answers the unsubscribe. */
  readonly onOpen: (listener: (data: unknown) => void) => () => void;
}

/**
 * The channel every push lands in on Android — Expo's service sends to `default` when a message
 * names none. Its name is what Android's settings list for the app.
 */
const ANDROID_CHANNEL = 'default';
const ANDROID_CHANNEL_NAME = 'Your games';

/** Whether this build may ask for a token at all — see `shared/config/push.ts`. */
function canBePushed(): boolean {
  if (EXPO_PROJECT_ID === null) return false;
  return Platform.OS !== 'ios' || IPHONE_PUSH;
}

/** The token minted this process, kept until the system says it changed. */
let minted: string | undefined;

/** Every tap handed over, by the notification's identifier — a cold start's included. */
const opened = new Set<string>();

async function mint(): Promise<string | null> {
  if (!canBePushed() || EXPO_PROJECT_ID === null) return null;
  if (minted !== undefined) return minted;
  let gaveUp: ReturnType<typeof setTimeout> | undefined;
  try {
    const token = await Promise.race([
      Notifications.getExpoPushTokenAsync({ projectId: EXPO_PROJECT_ID }),
      new Promise<null>((resolve) => {
        gaveUp = setTimeout(() => resolve(null), TIMEOUT_MS.request);
      }),
    ]);
    if (token === null) return null;
    minted = token.data;
    return minted;
  } catch {
    // Expo unreachable, no FCM key on Android, a simulator: no token now, and the next foreground
    // asks again. Never logged with what it would have been.
    return null;
  } finally {
    clearTimeout(gaveUp);
  }
}

function tapped(
  response: Notifications.NotificationResponse | null,
  listener: (data: unknown) => void,
): void {
  if (response === null) return;
  // A button on the notification is an action of its own; only the tap on its body opens it.
  if (response.actionIdentifier !== Notifications.DEFAULT_ACTION_IDENTIFIER) return;
  const id = response.notification.request.identifier;
  if (opened.has(id)) return;
  opened.add(id);
  listener(response.notification.request.content.data);
}

export const devicePush: PushPort = {
  async getPermission() {
    return permissionStateOf(await Notifications.getPermissionsAsync());
  },

  async requestPermission() {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync(ANDROID_CHANNEL, {
        name: ANDROID_CHANNEL_NAME,
        importance: Notifications.AndroidImportance.HIGH,
      });
    }
    return permissionStateOf(await Notifications.requestPermissionsAsync());
  },

  readToken: mint,

  onTokenChange(listener) {
    const subscription = Notifications.addPushTokenListener(() => {
      minted = undefined;
      listener();
    });
    return () => subscription.remove();
  },

  onNotice(listener) {
    const subscription = Notifications.addNotificationReceivedListener((notification) => {
      const { title, body, data } = notification.request.content;
      listener({ title: title ?? '', body: body ?? '', data });
    });
    return () => subscription.remove();
  },

  onOpen(listener) {
    let live = true;
    const subscription = Notifications.addNotificationResponseReceivedListener((response) =>
      tapped(response, listener),
    );
    // The tap that started the app came before anybody was listening.
    void Notifications.getLastNotificationResponseAsync().then((response) => {
      if (live) tapped(response, listener);
    });
    return () => {
      live = false;
      subscription.remove();
    };
  },
};
