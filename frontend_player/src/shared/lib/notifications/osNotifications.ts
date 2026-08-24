/**
 * The one module in this app that imports `expo-notifications`, and the only
 * place anything asks the OS about notifications.
 *
 * It is the shape `shared/lib/auth` has over the keychain: one module owns a
 * native capability, holds **no rule of its own**, and every decision about when
 * to call it lives above. ESLint bans `expo-notifications` everywhere else, so
 * *the app asks the OS in one place* is enforced rather than remembered — which
 * is what keeps `ADR-0061`'s promise reachable in both directions: refusing
 * notifications must cost a player the message and never a card, and a second
 * module reaching for the OS is how that would quietly stop being true.
 *
 * **Nothing here decides anything.** It answers four questions and performs two
 * acts; whether to ask, when to ask, and what to say are the notifications
 * feature's, and what to do with a refusal is nobody's — see `ADR-0065`.
 *
 * ## Two things this cannot do, and both are facts about the world
 *
 * **`timeSensitiveSetting` is not readable through this SDK.** See
 * {@link timeSensitive} — `expo-notifications`' iOS requester serialises ten
 * fields of `UNNotificationSettings` and that is not one of them.
 *
 * **There is no push token to read yet.** {@link pushToken} needs an Expo
 * project id, which is `Raketa02/Raketa#26`'s and a human's: an agent may not
 * create a credential file. Absent one the SDK throws, and this answers
 * *nothing to register* rather than turning a missing credential into an error a
 * player sees.
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

/**
 * Whether the OS prompt is still worth spending.
 *
 * `ADR-0061` spends the system dialog **only on a yes**, so the question this
 * app actually asks the OS is not *what did she answer* but *may we still ask* —
 * iOS grants exactly one prompt per install, and two denials on Android are
 * permanent. `canAskAgain` is that question, which is why it is read rather than
 * the raw status: after one Android denial the platform will still show the
 * dialog, and a status-only reading would have written that phone off.
 */
export type NotificationStanding =
  /** She said yes. There is nothing left to explain and nothing left to ask. */
  | 'granted'
  /** The prompt has not been spent. An explainer can still buy something. */
  | 'askable'
  /** Asked and refused. The OS will not show the dialog again. */
  | 'spent';

/** What `UNNotificationSettings.timeSensitiveSetting` reports, as reported. */
export type TimeSensitiveReading = 'enabled' | 'disabled' | 'notSupported';

/** The two stores this app ships to. Anything else cannot be registered. */
export type DeviceKind = 'ios' | 'android';

/**
 * The one Android channel, at `IMPORTANCE_HIGH` — **not two** (`ADR-0065`).
 *
 * *Seats you asked for* and *seats we found you* as separate channels reads as a
 * kindness and is a mute switch on the rungs that never asked, who are the
 * likeliest to throw it and whom the open call depends on. One channel means
 * muting standby costs a player the seats she actually wants, which is the
 * honest price of the switch.
 *
 * The id is the string the backend puts on every Android message
 * (`ANDROID_CHANNEL` in `app/modules/now/domain/push.py`). It is **not on the
 * contract**, so the two spellings are agreed and checked by nothing — filed as
 * `Raketa02/Raketa#130`.
 */
export const OFFERS_CHANNEL = 'offers';

/** Whether this build can be sent a message at all. */
export async function standing(): Promise<NotificationStanding> {
  return standingOf(await Notifications.getPermissionsAsync());
}

/**
 * Fire the OS prompt. **The only call in this app that spends it.**
 *
 * The defaults are what `ADR-0062`'s one line needs — an alert, a sound, and the
 * badge iOS asks for alongside them. No provisional authorisation: a quiet
 * trial delivery that never reaches a lock screen is the opposite of a channel
 * whose whole value is the Monday-morning interruption.
 */
export async function ask(): Promise<NotificationStanding> {
  return standingOf(await Notifications.requestPermissionsAsync());
}

/**
 * Where this phone can be reached, or `undefined` when it cannot be.
 *
 * The **Expo** token rather than the bare APNs/FCM one, and the choice is not
 * arbitrary: a device token needs a `google-services.json` and an APNs
 * entitlement on the phone — credential files an agent may not create — where an
 * Expo token needs only a project id. Everything `ADR-0062` and `ADR-0065`
 * decide is expressible through either service, so this decides the client half
 * and leaves the server's transport exactly where `LoggingPushSender` left it.
 *
 * **A failure is not an error.** Expo's own documentation says to `try`/`catch`
 * this call — it makes a network request, and it throws outright with no project
 * id, which is every build today (`Raketa02/Raketa#26`). Either way there is
 * nothing to register and nothing a player could do about it, so the answer is
 * *nothing* rather than a sentence on a screen.
 */
export async function pushToken(): Promise<string | undefined> {
  try {
    const token = await Notifications.getExpoPushTokenAsync();
    return token.data;
  } catch {
    return undefined;
  }
}

/**
 * What Time Sensitive is set to. **`notSupported`, and that is the truth today.**
 *
 * `ADR-0065` rests its whole observability argument on this being readable —
 * *"it is invisible to the server, but not to the client"* — and through this SDK
 * it is not. `expo-notifications`' iOS requester serialises ten fields of
 * `UNNotificationSettings` (`alertSetting`, `soundSetting`, `announcementSetting`
 * and seven more) and `timeSensitiveSetting` is not among them, on any platform,
 * in any version. There is no JS reader to call.
 *
 * What is returned is nevertheless **not a stand-in**. Apple reports
 * `.notSupported` for an app that holds no Time Sensitive entitlement, and this
 * build holds none — the entitlement is part of the Apple Developer membership
 * that is `Raketa02/Raketa#26` — and Android has no such setting at all, which is
 * the iPad case `ADR-0065` names in as many words: *a player who was never going
 * to get a Focus-piercing alert has refused nothing*.
 *
 * So this is correct until the entitlement ships, and **wrong the moment it
 * does**: from then on every iPhone would report `notSupported` while some of
 * them had genuinely revoked, which is the one failure that makes the signal
 * worse than no signal. That is `Raketa02/Raketa#131`, and it is a native
 * reader rather than a call somebody forgot to make.
 *
 * It is `async` because the day it is real it is an OS read, and because a
 * caller shaped around a synchronous constant is a caller that has to change.
 */
export async function timeSensitive(): Promise<TimeSensitiveReading> {
  return 'notSupported';
}

/** Which of the two stores this build came from, or neither. */
export function platform(): DeviceKind | undefined {
  if (Platform.OS === 'ios') return 'ios';
  if (Platform.OS === 'android') return 'android';
  return undefined;
}

/**
 * Create the one Android channel, so a message naming it has somewhere to land.
 *
 * A no-op on iOS, where loudness is per message (`interruptionLevel`) rather
 * than a switch the player can see and throw. On Android there is no per-message
 * lever at all, so the channel **is** the loudness — and a message naming a
 * channel that was never created falls back to the app's default one, which is
 * the Monday-morning interruption silently downgraded.
 *
 * `bypassDnd` is deliberately not set: Do Not Disturb bypass needs a second
 * runtime permission, and `ADR-0065` declines to ask for it by name.
 */
export async function ensureChannel(): Promise<void> {
  if (Platform.OS !== 'android') return;
  await Notifications.setNotificationChannelAsync(OFFERS_CHANNEL, {
    name: 'Seats that open up',
    importance: Notifications.AndroidImportance.HIGH,
  });
}

/**
 * The four questions and the two acts, as one object to inject.
 *
 * One identifier at the call site rather than six, so the port a use-case
 * declares is checked against this in **one** place: a fifth value on the wire's
 * `TimeSensitiveSetting`, or a third platform, fails `pnpm typecheck` there
 * rather than passing silently through six separate assignments.
 */
export const osNotifications = {
  standing,
  ask,
  pushToken,
  timeSensitive,
  platform,
  ensureChannel,
} as const;

/**
 * Three standings out of what the SDK reports.
 *
 * `granted` first, because it is the only one of the three that is a statement
 * about permission rather than about the dialog.
 */
function standingOf(status: Notifications.NotificationPermissionsStatus): NotificationStanding {
  if (status.granted) return 'granted';
  return status.canAskAgain ? 'askable' : 'spent';
}
