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
 *   settings app can change it, so a screen must say so and offer `openAppSettings()`
 *   rather than a control that would prompt.
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

/**
 * A capability that can be asked about and asked for — which both ports are, structurally.
 *
 * Named as the shape rather than as a union of the two ports, so a third capability obeys
 * this rule by having the two methods rather than by being added to a list somewhere.
 */
export interface AskablePermission {
  readonly getPermission: () => Promise<PermissionState>;
  readonly requestPermission: () => Promise<PermissionState>;
}

/**
 * Ask, but only where asking achieves something.
 *
 * A `granted` permission needs no prompt at all, and a `blocked` one is resolved by the OS
 * instantly and negatively without showing the player anything — so a caller that asks
 * anyway loops against a system that has already answered. What is left is the two states
 * a prompt exists for.
 *
 * Here rather than in the steps that reach a capability, because it is a rule about the
 * vocabulary above rather than about photos or about location, and because the two steps
 * that had written it themselves had written it identically — which is how the third one
 * would have come to disagree with them about what a blocked permission means.
 */
export async function ensurePermission(capability: AskablePermission): Promise<PermissionState> {
  const current = await capability.getPermission();
  if (current === 'granted' || current === 'blocked') return current;
  return capability.requestPermission();
}
