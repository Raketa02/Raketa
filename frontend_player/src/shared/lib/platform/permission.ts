/**
 * The permission vocabulary the ports in this module speak.
 *
 * Every native capability behind a port — location today, the photo library today, the
 * camera and notifications when something needs them — answers the same three questions:
 * may we, ask the player, and what did they say. Naming the answer once means a screen
 * learns one set of states rather than one per capability, and means the *interesting*
 * distinction is made in one place rather than re-derived at each call site.
 *
 * See docs/architecture.md Part 13: permissions are requested just in time, through one
 * central module that distinguishes not-requested / granted / denied / permanently
 * denied.
 */

/**
 * What the app is currently allowed to do, and what asking again would achieve.
 *
 * - `undetermined` — the player has not been asked. Asking will show the OS prompt.
 * - `granted` — allowed. On iOS a *limited* photo selection lands here too: the player
 *   chose which pictures we may see, and that is a yes.
 * - `denied` — refused, and the OS will show the prompt again. Ask at the moment the
 *   player understands why, never before.
 * - `blocked` — refused permanently. Asking resolves instantly and negatively; only the
 *   settings app can change it, so a screen must offer the manual path instead.
 */
export type PermissionState = 'undetermined' | 'granted' | 'denied' | 'blocked';

/**
 * The shape every Expo permission response has, narrowed to the three fields that decide
 * the state.
 *
 * `status` is typed as a plain string rather than as the native module's enum on purpose:
 * this file is beneath both ports and must not import either native module — the linter
 * says so — and the enum's values are these strings anyway.
 */
export interface NativePermissionResponse {
  readonly granted: boolean;
  readonly canAskAgain: boolean;
  readonly status: string;
}

/** Read a native permission response as one of the four states. */
export function permissionStateOf(response: NativePermissionResponse): PermissionState {
  // Granted is read first: iOS reports `canAskAgain: false` beside a granted permission,
  // because there is nothing left to ask.
  if (response.granted) return 'granted';
  if (response.status === 'undetermined') return 'undetermined';
  return response.canAskAgain ? 'denied' : 'blocked';
}
