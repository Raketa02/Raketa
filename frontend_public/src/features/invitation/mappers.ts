/**
 * **An invitation's link, wire to view.** The only file in this feature that imports a generated
 * type (ADR-0187 §6).
 */

import { toLinkState, type LinkState } from '@/features/set-password/mappers';
import type { components } from '@/generated/schema';

type WireInvitation = components['schemas']['InvitationPageResponse'];

/** What the invitation page greets with: **the least it needs** (ADR-0187 §5), and no email. */
export interface Invitation {
  /** The name the club typed, whole (ADR-0171 §4). */
  readonly name: string;
  readonly club: string;
  readonly state: LinkState;
  /** The code the email carries, for the app: only while the link is valid. */
  readonly code: string | null;
}

export function toInvitation(wire: WireInvitation): Invitation {
  const state = toLinkState(wire.state);
  return {
    name: wire.name,
    club: wire.club_name,
    state,
    code: state === 'valid' ? wire.code : null,
  };
}
