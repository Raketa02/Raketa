/**
 * The platform module: everything this app knows about the device it is running on.
 *
 * App lifecycle and connectivity are *wirings* — called once by the bootstrap sequence,
 * after which nothing consults them again but through Query's managers. Connectivity keeps one
 * reading beside its wiring: `readReachability`, what the online manager believes once it has its
 * first answer, which the launch reads before its session check and skips the check on when the
 * phone knows it is offline (ADR-0209 §4). The ports below are the other kind: an interface a
 * feature depends on, with one implementation that talks to the device and one fake that a test
 * drives (`src/test-support/platform.ts`).
 *
 * `useHardwareBack` is a third kind and small enough to say so here: a **hook over a device
 * gesture**, with no port under it because `BackHandler` is React Native's own and not an
 * Expo native module — nothing below it needs replacing for a test, only pressing
 * (`src/test-support/hardwareBack.ts`). It lives here for the reason `useOnForeground` does:
 * *what the device does* is one directory, and a screen reaching for `BackHandler` itself is
 * the second answer to a question this module already has one of. `useOnReturn` sits beside
 * the two of them as the third answer to *did we just come back* — the navigator's focus
 * after a blur, where `useOnForeground` is the app's — so a screen never has to decide for
 * itself what a pop means.
 *
 * Each of those modules is importable **only from inside its own file**, which is what
 * makes their behaviour readable in one sitting and their callers testable at all. The
 * linter enforces it; `scripts/test-import-boundaries.sh` proves the linter still does.
 *
 * **The third port's far side is a socket rather than a native module**, and it is here for the
 * second of the two reasons the other two are: a transport cannot be driven from a test either,
 * and one file owning the app's only long-lived connection is what keeps *close it on background*
 * and *reconnect with a fresh credential* in one place instead of in a screen.
 *
 * **The fourth is the motor**, one verb wide, and it is here for the first reason: a buzz is a
 * native module with nothing under it in a test, and *exactly one, and none under reduced
 * motion* is a rule a fake can count where a mock could only record.
 *
 * **The fifth is the clipboard** (#512), for the same reason: *Join a group*'s **Paste** is a
 * native read, and a suite has to be able to put a link on it. It learned to write with a group
 * page's **Copy link** (#513).
 *
 * **The sixth is the share sheet** (#513), one verb wide: a group page's **Share the link** opens
 * a native sheet no suite can open, so a fake records what it was handed. It is React Native's
 * own module rather than an Expo one — `useHardwareBack`'s `BackHandler` is too, and has no port —
 * and the difference is what a test needs: a back press is something a suite presses, a sheet is
 * something it has to see opened.
 *
 * **The seventh is the payment provider's phone half** (#552): Stripe's card fields and the bank's
 * check. Both are native, and a card saved is the one walk no suite could otherwise finish — so a
 * port, with a fake that behaves as Stripe's test cards do. It is the one port that carries a
 * **component** beside its verbs, because what is typed stays inside the fields and is read out of
 * them there.
 *
 * **The eighth is the phone's push notifications** (#559): the permission, the token Expo's push
 * service addresses the phone by, a push arriving while the app is open, and the tap that opens
 * one. All native, and the walks a suite has to finish — a refusal, a token registered, a banner
 * tapped — are none it could otherwise reach.
 *
 * **The ninth is the install referrer** (#756): the link Google Play carried through an Android
 * install, read once on the app's first launch. Native, and *once* is a rule a fake can count. It is
 * read before any screen exists — by a bootstrap step the root layout supplies — so it is a value
 * handed to its caller rather than a provider's.
 *
 * **The tenth is the system bars** (#857): the status bar and Android's navigation bar, painted the
 * drawn splash's edge colour while it is up and given back as its fade starts (ADR-0209). The
 * navigation bar is native, and *painted until the fade, not after* is a rule a fake can follow. The
 * platforms differ, so the port is two files: `systemBars.ts` for an iPhone and
 * `systemBars.android.ts`, the only importer of `expo-navigation-bar`. Its one caller is the launch
 * gate, which is handed it as it is handed the launch window, so it has no provider either.
 *
 * **The eleventh is the soft keyboard** (#882, ADR-0210 §9): whether it is up, and a way to follow
 * it. It joined `keyboard.ts` — the keyboard's module already, the avoidance value and the dismissal —
 * rather than a second module, so that file is the only importer of React Native's `Keyboard`, the
 * share sheet's kind of fence, and the app's one listener for its show and hide. Both shells read it
 * through `useKeyboardShrinksTheWindow`, to stand the tab bar down while an Android window is shrunk
 * for it; a suite raises and drops `fakeKeyboard()` through `KeyboardProvider`.
 *
 * `appBuild` is the one plain *reading* of what the device is: which platform and which version
 * of the app this is, the two device facts a feature flag's rules may target (ADR-0206 §8).
 * Nothing to decide and nothing a test would drive, so no port.
 *
 * `permissionStateOf` is deliberately *not* re-exported. Reading a native response is the
 * ports' own work, and a caller with a use for it is a caller that got hold of a native
 * response — which is the thing the boundary exists to prevent.
 */

export { useAppInBackground, useOnForeground, wireFocusManager } from './appState';
export { useHardwareBack } from './hardwareBack';
export { useOnReturn } from './screenReturn';
export { openAppSettings } from './appSettings';
export { appBuild } from './appBuild';
export { useCopyAndSay, type CopyWords } from './copyAndSay';
export {
  KEYBOARD_AVOIDANCE,
  deviceKeyboard,
  dismissKeyboard,
  windowResizesForKeyboard,
  type KeyboardPort,
} from './keyboard';
export {
  KeyboardProvider,
  useKeyboardShrinksTheWindow,
  type KeyboardProviderProps,
} from './KeyboardProvider';
export {
  REACHABILITY_ANSWER_WITHIN_MS,
  readReachability,
  useIsOnline,
  wireOnlineManager,
  type Reachability,
} from './networkState';

export { ensurePermission, type AskablePermission, type PermissionState } from './permission';

export { deviceLocation, type LocationFix, type LocationPort } from './location';
export { deviceInstallReferrer, type InstallReferrerPort } from './installReferrer';
export { LocationProvider, useLocation, type LocationProviderProps } from './LocationProvider';
export {
  deviceImagePicking,
  type ImagePickingPort,
  type PickedImage,
  type PickImagesOptions,
} from './imagePicking';
export {
  ImagePickingProvider,
  useImagePicking,
  type ImagePickingProviderProps,
} from './ImagePickingProvider';
export {
  deviceLiveStream,
  type FollowLive,
  type LiveNudge,
  type LiveTyping,
  type LiveStreamPort,
  type LiveStreamStatus,
} from './liveStream';
export {
  LiveStreamProvider,
  useLiveStream,
  type LiveStreamProviderProps,
} from './LiveStreamProvider';
export { deviceHaptics, type HapticsPort } from './haptics';
export { HapticsProvider, useHaptics, type HapticsProviderProps } from './HapticsProvider';
export { deviceClipboard, type ClipboardPort } from './clipboard';
export { ClipboardProvider, useClipboard, type ClipboardProviderProps } from './ClipboardProvider';
export { deviceShare, type SharePort } from './share';
export { ShareProvider, useShare, type ShareProviderProps } from './ShareProvider';
export {
  devicePayments,
  type BankAnswer,
  type CardEntry,
  type CardFieldsProps,
  type CardTaking,
  type ConfirmPayment,
  type ConfirmSetup,
  type ConfirmWith,
  type PaymentAnswer,
  type PaymentsPort,
  type PhoneWallet,
  type TakenCard,
} from './payments';
export { PaymentsProvider, usePayments, type PaymentsProviderProps } from './PaymentsProvider';
export { devicePush, type PushNotice, type PushPort } from './push';
export { PushProvider, usePush, type PushProviderProps } from './PushProvider';
export { deviceSystemBars, type SystemBarsPort } from './systemBars';
