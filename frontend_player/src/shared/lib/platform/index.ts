/**
 * The platform module: everything this app knows about the device it is running on.
 *
 * App lifecycle and connectivity are *wirings* — called once by the bootstrap sequence,
 * after which nothing consults them again. The four ports below are the other kind: an
 * interface a feature depends on, with one implementation that talks to the device and one
 * fake that a test drives (`src/test-support/platform.ts`).
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
 * **The fifth is the clipboard** (#512), read-only and one verb wide, for the same reason: *Join a
 * group*'s **Paste** is a native read, and a suite has to be able to put a link on it.
 *
 * `appBuild` is the one plain *reading*: which platform and which version of the app this is,
 * the two device facts a feature flag's rules may target (ADR-0180 §8). Nothing to decide and
 * nothing a test would drive, so no port.
 *
 * `permissionStateOf` is deliberately *not* re-exported. Reading a native response is the
 * ports' own work, and a caller with a use for it is a caller that got hold of a native
 * response — which is the thing the boundary exists to prevent.
 */

export { useOnForeground, wireFocusManager } from './appState';
export { useHardwareBack } from './hardwareBack';
export { useOnReturn } from './screenReturn';
export { openAppSettings } from './appSettings';
export { appBuild } from './appBuild';
export { KEYBOARD_AVOIDANCE } from './keyboard';
export { useIsOnline, wireOnlineManager } from './networkState';

export { ensurePermission, type AskablePermission, type PermissionState } from './permission';

export { deviceLocation, type LocationFix, type LocationPort } from './location';
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
