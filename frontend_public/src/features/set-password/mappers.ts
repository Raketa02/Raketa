/**
 * **A link's state, wire to view**, for the invitation's and the reset's alike: the wire names the
 * two enums apart, and the site draws them the same.
 */

import type { components } from '@/generated/schema';

type WireState =
  components['schemas']['InvitationLinkState'] | components['schemas']['ResetLinkState'];

/** Whether a link can still set a password. */
export type LinkState = 'valid' | 'expired' | 'used' | 'locked';

/** A `Record` over the wire's enums: a fifth state fails to compile until it is mapped. */
const STATES: Readonly<Record<WireState, LinkState>> = {
  valid: 'valid',
  expired: 'expired',
  used: 'used',
  locked: 'locked',
};

export function toLinkState(wire: WireState): LinkState {
  return STATES[wire];
}
