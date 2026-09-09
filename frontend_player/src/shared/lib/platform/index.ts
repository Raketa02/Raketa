/**
 * The platform module: everything this app knows about the device it is running on.
 *
 * App lifecycle and connectivity are *wirings* — called once by the bootstrap sequence,
 * after which nothing consults them again. The three ports below are the other kind: an
 * interface a feature depends on, with one implementation that talks to the device and one
 * fake that a test drives (`src/test-support/platform.ts`).
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
 * `permissionStateOf` is deliberately *not* re-exported. Reading a native response is the
 * ports' own work, and a caller with a use for it is a caller that got hold of a native
 * response — which is the thing the boundary exists to prevent.
 */

export { useOnForeground, wireFocusManager } from './appState';
export { openAppSettings } from './appSettings';
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
  type LiveStreamPort,
  type LiveStreamStatus,
} from './liveStream';
export {
  LiveStreamProvider,
  useLiveStream,
  type LiveStreamProviderProps,
} from './LiveStreamProvider';
