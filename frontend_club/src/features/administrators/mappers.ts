/**
 * **The club's administrators, wire to view.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the {@link Administrator} it makes.
 */

import type { components } from '@/generated/schema';

import type { Invitation } from './schemas';

type WireAdministrator = components['schemas']['AdministratorSchema'];
type WireInvitation = components['schemas']['InviteAdministratorRequest'];

const DAY_MS = 86_400_000;
/** An invitation lasts 72 hours (ADR-0184 §3), so no clock between here and the backend makes it read longer. */
const INVITATION_DAYS = 3;

/**
 * **Somebody's status, with its days**, counted when the page is drawn (ADR-0184 §1: every
 * status is derived). An invitation that has 71 hours left expires *in 3 d*, one that lapsed an
 * hour ago expired *0 d ago*, and a profile used an hour ago was used *0* days ago. `idleDays`
 * is `null` for an administrator who has not used the profile since taking it up.
 */
export type Status =
  | { readonly kind: 'active'; readonly idleDays: number | null }
  | { readonly kind: 'invited'; readonly daysLeft: number }
  | { readonly kind: 'expired'; readonly daysAgo: number };

/** An official group somebody runs. */
export interface AdministeredGroup {
  readonly id: string;
  readonly name: string;
}

/** One row of the Administrators table. */
export interface Administrator {
  readonly id: string;
  readonly name: string;
  readonly email: string;
  /** The official groups this person runs. None exist until #509. */
  readonly groups: readonly AdministeredGroup[];
  readonly status: Status;
  /** Only for an account that holds nothing but administrator profiles (ADR-0184 §6). */
  readonly canResetPassword: boolean;
}

function statusOf(wire: WireAdministrator, now: number): Status {
  const at = (instant: string | null) => (instant === null ? now : Date.parse(instant));
  switch (wire.status) {
    case 'ACTIVE':
      return {
        kind: 'active',
        idleDays:
          wire.last_used_at === null
            ? null
            : Math.max(0, Math.floor((now - at(wire.last_used_at)) / DAY_MS)),
      };
    case 'INVITED':
      return {
        kind: 'invited',
        daysLeft: Math.min(
          INVITATION_DAYS,
          Math.max(0, Math.ceil((at(wire.expires_at) - now) / DAY_MS)),
        ),
      };
    case 'EXPIRED':
      return {
        kind: 'expired',
        daysAgo: Math.max(0, Math.floor((now - at(wire.expires_at)) / DAY_MS)),
      };
  }
}

export function toAdministrator(wire: WireAdministrator, now: number): Administrator {
  return {
    id: wire.id,
    name: wire.name,
    email: wire.email,
    groups: wire.groups.map((group) => ({ id: group.id, name: group.name })),
    status: statusOf(wire, now),
    canResetPassword: wire.can_reset_password,
  };
}

/**
 * **Who an email just went to**, and why: an invitation, new or sent again, or the club's
 * *Reset password*, which sends the invitation's own link and code (ADR-0184 §6). Named as the
 * backend recorded them.
 */
export interface Sent {
  readonly kind: 'invitation' | 'reset';
  readonly name: string;
  readonly email: string;
}

export function toSent(wire: WireAdministrator, kind: Sent['kind']): Sent {
  return { kind, name: wire.name, email: wire.email };
}

export function toInvitationBody(invitation: Invitation): WireInvitation {
  return { name: invitation.name, email: invitation.email };
}
